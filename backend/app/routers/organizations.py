from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from .auth import get_current_user
from ..db import get_db

router = APIRouter(prefix="/api/v1/organizations", tags=["organization workspaces"])


class ProjectCreate(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    description: str | None = Field(default=None, max_length=2000)
    visibility: str = Field(default="organization", pattern="^(organization|private)$")


class RoleUpdate(BaseModel):
    role: str = Field(pattern="^(curator|reviewer|researcher|viewer)$")


def _require_org(user: dict) -> UUID:
    organization_id = user.get("organization_id")
    if not organization_id:
        raise HTTPException(status_code=403, detail="An organization workspace is required.")
    return UUID(organization_id)


def _require_admin(user: dict):
    if user.get("role") != "organization_admin":
        raise HTTPException(status_code=403, detail="Organization administrator permission is required.")


@router.get("/me")
def get_organization(current_user: Annotated[dict, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)]):
    organization_id = _require_org(current_user)
    result = db.execute(text("""
        SELECT o.id, o.name, o.organization_type, o.country_code, o.created_at,
               COUNT(om.user_id) FILTER (WHERE om.membership_status = 'active') AS active_members
        FROM organizations o
        JOIN organization_memberships om ON om.organization_id = o.id
        WHERE o.id = :organization_id AND om.user_id = :user_id
          AND om.membership_status = 'active'
        GROUP BY o.id
    """), {"organization_id": organization_id, "user_id": current_user["id"]}).mappings().first()
    if not result:
        raise HTTPException(status_code=403, detail="You are not an active member of this organization.")
    return dict(result)


@router.get("/members")
def list_members(current_user: Annotated[dict, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)]):
    organization_id = _require_org(current_user)
    membership = db.execute(text("""
        SELECT 1 FROM organization_memberships
        WHERE organization_id = :organization_id AND user_id = :user_id AND membership_status = 'active'
    """), {"organization_id": organization_id, "user_id": current_user["id"]}).first()
    if not membership:
        raise HTTPException(status_code=403, detail="Active organization membership required.")
    rows = db.execute(text("""
        SELECT up.id, up.email, up.display_name, om.role, om.membership_status, om.created_at
        FROM organization_memberships om
        JOIN user_profiles up ON up.id = om.user_id
        WHERE om.organization_id = :organization_id
        ORDER BY om.created_at, up.display_name
    """), {"organization_id": organization_id}).mappings().all()
    return {"organization_id": str(organization_id), "members": [dict(row) for row in rows]}


@router.patch("/members/{user_id}/role")
def update_member_role(
    user_id: UUID,
    payload: RoleUpdate,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    _require_admin(current_user)
    organization_id = _require_org(current_user)
    if str(user_id) == current_user["id"]:
        raise HTTPException(status_code=409, detail="Administrators cannot change their own role.")
    result = db.execute(text("""
        UPDATE organization_memberships
        SET role = :role, updated_at = now()
        WHERE organization_id = :organization_id AND user_id = :user_id
          AND membership_status = 'active'
        RETURNING user_id, role
    """), {"role": payload.role, "organization_id": organization_id, "user_id": user_id}).mappings().first()
    if not result:
        raise HTTPException(status_code=404, detail="Active organization member not found.")
    db.execute(text("""
        INSERT INTO audit_events (actor_user_id, organization_id, action, entity_type, entity_id, event_metadata)
        VALUES (:actor_id, :organization_id, 'member_role_updated', 'user_profile', :target_id,
                jsonb_build_object('new_role', :role))
    """), {"actor_id": current_user["id"], "organization_id": organization_id, "target_id": user_id, "role": payload.role})
    db.commit()
    return {"user_id": str(result["user_id"]), "role": result["role"]}


@router.post("/projects", status_code=201)
def create_project(
    payload: ProjectCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    organization_id = _require_org(current_user)
    membership = db.execute(text("""
        SELECT role FROM organization_memberships
        WHERE organization_id = :organization_id AND user_id = :user_id AND membership_status = 'active'
    """), {"organization_id": organization_id, "user_id": current_user["id"]}).scalar_one_or_none()
    if not membership or membership == "viewer":
        raise HTTPException(status_code=403, detail="Your membership does not permit project creation.")
    project = db.execute(text("""
        INSERT INTO research_projects (organization_id, name, description, visibility, created_by)
        VALUES (:organization_id, :name, :description, :visibility, :created_by)
        RETURNING id, organization_id, name, description, visibility, created_by, created_at
    """), {
        "organization_id": organization_id, "name": payload.name.strip(),
        "description": payload.description, "visibility": payload.visibility,
        "created_by": current_user["id"],
    }).mappings().one()
    db.execute(text("""
        INSERT INTO project_memberships (project_id, user_id, project_role)
        VALUES (:project_id, :user_id, 'owner')
    """), {"project_id": project["id"], "user_id": current_user["id"]})
    db.commit()
    return dict(project)


@router.get("/projects")
def list_projects(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    limit: int = Query(default=20, ge=1, le=100),
):
    organization_id = _require_org(current_user)
    rows = db.execute(text("""
        SELECT DISTINCT p.id, p.name, p.description, p.visibility, p.created_by, p.created_at, p.updated_at
        FROM research_projects p
        JOIN organization_memberships om ON om.organization_id = p.organization_id
        LEFT JOIN project_memberships pm ON pm.project_id = p.id AND pm.user_id = :user_id
        WHERE p.organization_id = :organization_id
          AND om.user_id = :user_id AND om.membership_status = 'active'
          AND (p.visibility = 'organization' OR p.created_by = :user_id OR pm.user_id IS NOT NULL)
        ORDER BY p.updated_at DESC
        LIMIT :limit
    """), {"organization_id": organization_id, "user_id": current_user["id"], "limit": limit}).mappings().all()
    return {"projects": [dict(row) for row in rows], "count": len(rows)}
