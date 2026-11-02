from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..db import get_db
from .auth import get_current_user

router = APIRouter(prefix="/api/v1/audit", tags=["audit trail"])


def _audit_organization(user: dict, db: Session) -> UUID:
    organization_id = user.get("organization_id")
    if not organization_id:
        raise HTTPException(status_code=403, detail="An organization workspace is required.")

    role = db.execute(text("""
        SELECT role
        FROM organization_memberships
        WHERE organization_id = :organization_id
          AND user_id = :user_id
          AND membership_status = 'active'
    """), {"organization_id": organization_id, "user_id": user["id"]}).scalar_one_or_none()

    if role != "organization_admin":
        raise HTTPException(status_code=403, detail="Organization administrator permission is required to view the audit trail.")
    return UUID(str(organization_id))


@router.get("/events")
def list_audit_events(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    before_sequence: int | None = Query(default=None, ge=1),
    action: str | None = Query(default=None, min_length=1, max_length=120),
    entity_type: str | None = Query(default=None, min_length=1, max_length=120),
    limit: int = Query(default=50, ge=1, le=100),
):
    organization_id = _audit_organization(current_user, db)
    rows = db.execute(text("""
        SELECT ae.id, ae.chain_sequence, ae.action, ae.entity_type, ae.entity_id,
               ae.event_metadata, ae.occurred_at, ae.previous_hash, ae.event_hash,
               up.display_name AS actor_display_name, ae.actor_user_id
        FROM audit_events ae
        LEFT JOIN user_profiles up ON up.id = ae.actor_user_id
        WHERE ae.organization_id = :organization_id
          AND (:before_sequence IS NULL OR ae.chain_sequence < :before_sequence)
          AND (:action IS NULL OR ae.action = :action)
          AND (:entity_type IS NULL OR ae.entity_type = :entity_type)
        ORDER BY ae.chain_sequence DESC
        LIMIT :limit
    """), {
        "organization_id": organization_id,
        "before_sequence": before_sequence,
        "action": action,
        "entity_type": entity_type,
        "limit": limit,
    }).mappings().all()

    items = [dict(row) for row in rows]
    return {
        "organization_id": str(organization_id),
        "items": items,
        "count": len(items),
        "next_before_sequence": items[-1]["chain_sequence"] if len(items) == limit else None,
    }


@router.get("/integrity")
def verify_audit_integrity(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    organization_id = _audit_organization(current_user, db)
    result = db.execute(text("""
        WITH ordered_events AS (
            SELECT ae.*,
                   lag(ae.event_hash) OVER (ORDER BY ae.chain_sequence) AS prior_hash,
                   lag(ae.chain_sequence) OVER (ORDER BY ae.chain_sequence) AS prior_sequence
            FROM audit_events ae
            WHERE ae.organization_id = :organization_id
        ),
        checked_events AS (
            SELECT *,
                   (
                       previous_hash IS DISTINCT FROM COALESCE(prior_hash, repeat('0', 64))
                       OR chain_sequence <> COALESCE(prior_sequence + 1, 1)
                       OR chain_scope IS DISTINCT FROM :chain_scope
                       OR event_hash IS DISTINCT FROM audit_event_sha256(
                           id, actor_user_id, organization_id, action, entity_type,
                           entity_id, event_metadata, occurred_at, chain_scope,
                           chain_sequence, previous_hash
                       )
                   ) AS invalid
            FROM ordered_events
        )
        SELECT count(*) AS total_events,
               count(*) FILTER (WHERE invalid) AS invalid_events
        FROM checked_events
    """), {"organization_id": organization_id}).mappings().one()

    total = int(result["total_events"])
    invalid = int(result["invalid_events"])
    return {
        "organization_id": str(organization_id),
        "total_events": total,
        "invalid_events": invalid,
        "valid": invalid == 0,
        "verification_scope": "This organization’s database audit-event chain",
        "limitation": "This detects row edits, deletions, and chain discontinuities; it does not protect against a privileged database operator who can rewrite the chain and its head.",
    }
