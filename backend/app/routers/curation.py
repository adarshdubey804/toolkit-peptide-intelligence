from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from .auth import get_current_user
from ..db import get_db

router = APIRouter(prefix="/api/v1/curation", tags=["scientific curation"])


class ReviewSubmission(BaseModel):
    entity_type: Literal["peptide", "evidence_claim"]
    entity_id: UUID
    source_record_id: UUID | None = None
    priority: Literal["low", "normal", "high"] = "normal"


class ReviewAssignment(BaseModel):
    assigned_to: UUID | None = None


class CurationDecision(BaseModel):
    decision: Literal["verified", "rejected", "needs_changes", "archived"]
    rationale: str = Field(min_length=20, max_length=4000)


def _membership(user: dict, db: Session):
    organization_id = user.get("organization_id")
    if not organization_id:
        raise HTTPException(status_code=403, detail="Organization membership required.")
    membership = db.execute(text("""
        SELECT role FROM organization_memberships
        WHERE organization_id = :organization_id AND user_id = :user_id
          AND membership_status = 'active'
    """), {"organization_id": organization_id, "user_id": user["id"]}).scalar_one_or_none()
    if not membership:
        raise HTTPException(status_code=403, detail="Active organization membership required.")
    return UUID(organization_id), membership


def _require_submitter_role(role: str):
    if role not in ("organization_admin", "researcher", "curator"):
        raise HTTPException(status_code=403, detail="Your role cannot submit scientific records for review.")


def _require_reviewer_role(role: str):
    if role not in ("organization_admin", "curator", "reviewer"):
        raise HTTPException(status_code=403, detail="Curator or reviewer permission is required.")


def _entity_exists(db: Session, entity_type: str, entity_id: UUID) -> bool:
    table = {"peptide": "peptides", "evidence_claim": "evidence_claims"}[entity_type]
    return db.execute(text(f"SELECT 1 FROM {table} WHERE id = :entity_id"), {"entity_id": entity_id}).first() is not None


@router.post("/reviews", status_code=201)
def submit_review(
    payload: ReviewSubmission,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    organization_id, role = _membership(current_user, db)
    _require_submitter_role(role)
    if not _entity_exists(db, payload.entity_type, payload.entity_id):
        raise HTTPException(status_code=404, detail="Scientific record not found.")
    if payload.source_record_id:
        source_exists = db.execute(text("SELECT 1 FROM source_records WHERE id = :source_id"),
                                   {"source_id": payload.source_record_id}).first()
        if not source_exists:
            raise HTTPException(status_code=404, detail="Source record not found.")
    review = db.execute(text("""
        INSERT INTO curation_reviews
            (entity_type, entity_id, source_record_id, review_status, priority, submitted_by)
        VALUES (:entity_type, :entity_id, :source_id, 'in_review', :priority, :submitted_by)
        RETURNING id, entity_type, entity_id, source_record_id, review_status, priority, created_at
    """), {
        "entity_type": payload.entity_type, "entity_id": payload.entity_id,
        "source_id": payload.source_record_id, "priority": payload.priority,
        "submitted_by": current_user["id"],
    }).mappings().one()
    db.execute(text("""
        INSERT INTO audit_events (actor_user_id, organization_id, action, entity_type, entity_id, event_metadata)
        VALUES (:actor, :org, 'curation_review_submitted', 'curation_review', :review_id,
                jsonb_build_object('record_type', :record_type, 'record_id', :record_id))
    """), {"actor": current_user["id"], "org": organization_id, "review_id": review["id"],
           "record_type": payload.entity_type, "record_id": str(payload.entity_id)})
    db.commit()
    return dict(review)


@router.get("/reviews")
def list_reviews(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    review_status: Literal["draft", "in_review", "verified", "rejected", "archived"] | None = None,
    limit: int = Query(default=50, ge=1, le=100),
):
    organization_id, role = _membership(current_user, db)
    _require_reviewer_role(role)
    rows = db.execute(text("""
        SELECT cr.id, cr.entity_type, cr.entity_id, cr.source_record_id,
               cr.review_status, cr.priority, cr.assigned_to, cr.submitted_by,
               cr.reviewed_by, cr.reviewed_at, cr.created_at, cr.updated_at
        FROM curation_reviews cr
        WHERE (:review_status IS NULL OR cr.review_status = CAST(:review_status AS review_status))
          AND EXISTS (
              SELECT 1 FROM organization_memberships om
              WHERE om.organization_id = :organization_id
                AND om.user_id = cr.submitted_by
                AND om.membership_status = 'active'
          )
        ORDER BY CASE cr.priority WHEN 'high' THEN 0 WHEN 'normal' THEN 1 ELSE 2 END,
                 cr.created_at ASC
        LIMIT :limit
    """), {"review_status": review_status, "limit": limit, "organization_id": organization_id}).mappings().all()
    return {"reviews": [dict(row) for row in rows], "count": len(rows)}


@router.patch("/reviews/{review_id}/assignment")
def assign_review(
    review_id: UUID,
    payload: ReviewAssignment,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    organization_id, role = _membership(current_user, db)
    _require_reviewer_role(role)
    if payload.assigned_to:
        is_member = db.execute(text("""
            SELECT 1 FROM organization_memberships
            WHERE organization_id = :org AND user_id = :user_id
              AND membership_status = 'active'
              AND role IN ('organization_admin','curator','reviewer')
        """), {"org": organization_id, "user_id": payload.assigned_to}).first()
        if not is_member:
            raise HTTPException(status_code=400, detail="Assignee must be an active curator or reviewer in this organization.")
    result = db.execute(text("""
        UPDATE curation_reviews cr SET assigned_to = :assignee, updated_at = now()
        WHERE cr.id = :review_id AND cr.review_status IN ('draft','in_review')
          AND cr.submitted_by IN (
              SELECT user_id FROM organization_memberships
              WHERE organization_id = :org AND membership_status = 'active'
          )
        RETURNING cr.id, cr.assigned_to, cr.review_status
    """), {"assignee": payload.assigned_to, "review_id": review_id, "org": organization_id}).mappings().first()
    if not result:
        raise HTTPException(status_code=404, detail="Open review not found in this organization.")
    db.execute(text("""
        INSERT INTO audit_events (actor_user_id, organization_id, action, entity_type, entity_id, event_metadata)
        VALUES (:actor, :org, 'curation_review_assigned', 'curation_review', :review_id,
                jsonb_build_object('assignee_id', :assignee))
    """), {"actor": current_user["id"], "org": organization_id, "review_id": review_id,
           "assignee": str(payload.assigned_to) if payload.assigned_to else None})
    db.commit()
    return dict(result)


@router.post("/reviews/{review_id}/decisions", status_code=201)
def decide_review(
    review_id: UUID,
    payload: CurationDecision,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    organization_id, role = _membership(current_user, db)
    _require_reviewer_role(role)
    review = db.execute(text("""
        SELECT cr.* FROM curation_reviews cr
        JOIN organization_memberships om ON om.user_id = cr.submitted_by
        WHERE cr.id = :review_id AND om.organization_id = :org
          AND om.membership_status = 'active'
        FOR UPDATE OF cr
    """), {"review_id": review_id, "org": organization_id}).mappings().first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found in this organization.")
    if str(review["submitted_by"]) == current_user["id"]:
        raise HTTPException(status_code=409, detail="A submitter cannot approve or reject their own record.")
    if review["review_status"] not in ("draft", "in_review"):
        raise HTTPException(status_code=409, detail="This review has already been decided.")
    if review["assigned_to"] and str(review["assigned_to"]) != current_user["id"] and role != "organization_admin":
        raise HTTPException(status_code=403, detail="This review is assigned to another reviewer.")

    new_status = "draft" if payload.decision == "needs_changes" else payload.decision
    decision = db.execute(text("""
        INSERT INTO curation_decisions
            (review_id, decision, rationale, reviewer_id, previous_status, new_status)
        VALUES (:review_id, :decision, :rationale, :reviewer, :previous_status, :new_status)
        RETURNING id, review_id, decision, rationale, reviewer_id, decided_at, previous_status, new_status
    """), {"review_id": review_id, "decision": payload.decision, "rationale": payload.rationale.strip(),
           "reviewer": current_user["id"], "previous_status": review["review_status"], "new_status": new_status}).mappings().one()

    db.execute(text("""
        UPDATE curation_reviews
        SET review_status = CAST(:new_status AS review_status), decision_reason = :rationale,
            reviewed_by = :reviewer, reviewed_at = now(), updated_at = now()
        WHERE id = :review_id
    """), {"new_status": new_status, "rationale": payload.rationale.strip(),
           "reviewer": current_user["id"], "review_id": review_id})

    if review["entity_type"] in ("peptide", "evidence_claim"):
        table = {"peptide": "peptides", "evidence_claim": "evidence_claims"}[review["entity_type"]]
        db.execute(text(f"""
            UPDATE {table}
            SET review_status = CAST(:new_status AS review_status)
            WHERE id = :entity_id
        """), {"new_status": new_status, "entity_id": review["entity_id"]})

    db.execute(text("""
        INSERT INTO audit_events (actor_user_id, organization_id, action, entity_type, entity_id, event_metadata)
        VALUES (:actor, :org, 'curation_decision_recorded', 'curation_review', :review_id,
                jsonb_build_object('decision', :decision, 'record_type', :record_type))
    """), {"actor": current_user["id"], "org": organization_id, "review_id": review_id,
           "decision": payload.decision, "record_type": review["entity_type"]})
    db.commit()
    return dict(decision)
