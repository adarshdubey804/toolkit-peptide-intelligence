from typing import Annotated, Literal
from uuid import UUID
from urllib.parse import urlsplit

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, HttpUrl
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..db import get_db
from .auth import get_current_user

router = APIRouter(prefix="/api/v1/analytical-methods", tags=["analytical method intelligence"])
SUBMIT_ROLES = {"organization_admin", "curator", "researcher"}
REVIEW_ROLES = {"organization_admin", "curator", "reviewer"}


class MethodSubmission(BaseModel):
    method_name: str = Field(min_length=2, max_length=200)
    method_category: Literal[
        "chromatography", "mass_spectrometry", "spectroscopy", "electrophoresis",
        "amino_acid_analysis", "endotoxin", "sterility", "microbiology",
        "stability", "physical_characterization", "other"
    ]
    scientific_principle: str = Field(min_length=20, max_length=4000)
    intended_purpose: str = Field(min_length=10, max_length=2000)
    applicable_materials: list[str] = Field(min_length=1, max_length=20)
    method_classification: Literal["compendial", "published", "manufacturer_method", "in_house", "research_use", "unknown"] = "unknown"
    instrument_platform: str | None = Field(default=None, max_length=500)
    sample_requirements: str | None = Field(default=None, max_length=2000)
    method_scope: str | None = Field(default=None, max_length=2000)
    method_version: str | None = Field(default=None, max_length=100)
    reference_standard: str | None = Field(default=None, max_length=1000)
    validation_status: Literal["not_assessed", "not_validated", "development", "partially_validated", "validated"] = "not_assessed"
    acceptance_criteria_source: str | None = Field(default=None, max_length=1000)
    limitations: str = Field(min_length=10, max_length=3000)
    source_name: str = Field(min_length=2, max_length=120)
    source_identifier: str = Field(min_length=1, max_length=200)
    source_url: HttpUrl
    evidence_scope: str = Field(min_length=5, max_length=1000)


class MethodDecision(BaseModel):
    decision: Literal["verified", "rejected", "needs_changes"]
    rationale: str = Field(min_length=20, max_length=4000)


def _membership(user: dict, db: Session):
    organization_id = user.get("organization_id")
    if not organization_id:
        raise HTTPException(status_code=403, detail="Active organization membership required.")
    role = db.execute(text("""
        SELECT role FROM organization_memberships
        WHERE organization_id=:org AND user_id=:user_id AND membership_status='active'
    """), {"org": organization_id, "user_id": user["id"]}).scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=403, detail="Active organization membership required.")
    return organization_id, role


def _source_record(db: Session, name: str, identifier: str, url: str):
    parsed = urlsplit(url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise HTTPException(status_code=422, detail="Reference must use HTTPS without embedded credentials.")
    return db.execute(text("""
        INSERT INTO source_records (source_name, source_identifier, source_url, retrieved_at, raw_metadata)
        VALUES (:name, :identifier, :url, now(), '{}'::jsonb)
        ON CONFLICT (source_name, source_identifier)
        DO UPDATE SET source_url=EXCLUDED.source_url, last_seen_at=now()
        RETURNING id
    """), {"name": name, "identifier": identifier, "url": url}).scalar_one()


@router.get("")
def list_verified_methods(
    db: Annotated[Session, Depends(get_db)],
    q: str | None = Query(default=None, min_length=2, max_length=100),
    category: str | None = None,
    limit: int = Query(default=50, ge=1, le=100),
):
    rows = db.execute(text("""
        SELECT am.id, am.method_name, am.method_category, am.scientific_principle,
               am.intended_purpose, am.applicable_materials, am.method_classification,
               am.instrument_platform, am.sample_requirements, am.method_scope,
               am.method_version, am.reference_standard, am.validation_status,
               am.acceptance_criteria_source, am.limitations, am.source_id,
               COALESCE(jsonb_agg(DISTINCT jsonb_build_object(
                   'source_name', sr.source_name, 'source_identifier', sr.source_identifier,
                   'source_url', sr.source_url, 'evidence_scope', ams.evidence_scope
               )) FILTER (WHERE sr.id IS NOT NULL), '[]'::jsonb) AS sources
        FROM analytical_methods am
        LEFT JOIN analytical_method_sources ams ON ams.method_id=am.id
        LEFT JOIN source_records sr ON sr.id=ams.source_record_id
        WHERE am.review_status='verified'
          AND (:q IS NULL OR am.method_name ILIKE '%' || :q || '%' OR am.intended_purpose ILIKE '%' || :q || '%')
          AND (:category IS NULL OR am.method_category=:category)
        GROUP BY am.id
        ORDER BY am.method_category, am.method_name
        LIMIT :limit
    """), {"q": q, "category": category, "limit": limit}).mappings().all()
    return {"items": [dict(row) for row in rows], "count": len(rows),
            "scope": "Curator-reviewed method records only. Validation status is a separate field and is not implied by curation."}


@router.post("", status_code=201)
def submit_method(
    payload: MethodSubmission,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    organization_id, role = _membership(current_user, db)
    if role not in SUBMIT_ROLES:
        raise HTTPException(status_code=403, detail="Your role cannot submit analytical methods.")
    source_id = _source_record(db, payload.source_name, payload.source_identifier, str(payload.source_url))
    method = db.execute(text("""
        INSERT INTO analytical_methods (
            method_name, method_category, scientific_principle, intended_purpose,
            applicable_materials, method_classification, instrument_platform,
            sample_requirements, method_scope, method_version, reference_standard,
            validation_status, acceptance_criteria_source, limitations, source_id,
            review_status, submitted_by
        ) VALUES (
            :name, :category, :principle, :purpose, :materials, :classification,
            :platform, :sample, :scope, :version, :standard, :validation,
            :criteria, :limitations, :source, 'in_review', :submitter
        ) RETURNING id, method_name, method_category, review_status, validation_status
    """), {
        "name": payload.method_name.strip(), "category": payload.method_category,
        "principle": payload.scientific_principle.strip(), "purpose": payload.intended_purpose.strip(),
        "materials": payload.applicable_materials, "classification": payload.method_classification,
        "platform": payload.instrument_platform, "sample": payload.sample_requirements,
        "scope": payload.method_scope, "version": payload.method_version,
        "standard": payload.reference_standard, "validation": payload.validation_status,
        "criteria": payload.acceptance_criteria_source, "limitations": payload.limitations.strip(),
        "source": source_id, "submitter": current_user["id"],
    }).mappings().one()
    db.execute(text("""
        INSERT INTO analytical_method_sources (method_id, source_record_id, evidence_scope)
        VALUES (:method, :source, :scope)
    """), {"method": method["id"], "source": source_id, "scope": payload.evidence_scope})
    db.execute(text("""
        INSERT INTO audit_events (actor_user_id, organization_id, action, entity_type, entity_id, event_metadata)
        VALUES (:actor, :org, 'analytical_method_submitted', 'analytical_method', :id,
                jsonb_build_object('method_category', :category, 'source_record_id', :source))
    """), {"actor": current_user["id"], "org": organization_id, "id": method["id"],
           "category": payload.method_category, "source": str(source_id)})
    db.commit()
    return dict(method)


@router.get("/reviews")
def method_review_queue(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    limit: int = Query(default=50, ge=1, le=100),
):
    organization_id, role = _membership(current_user, db)
    if role not in REVIEW_ROLES:
        raise HTTPException(status_code=403, detail="Curator or reviewer permission is required.")
    rows = db.execute(text("""
        SELECT am.id, am.method_name, am.method_category, am.method_classification,
               am.validation_status, am.intended_purpose, am.limitations,
               am.submitted_by, am.review_status,
               COALESCE(jsonb_agg(DISTINCT jsonb_build_object(
                   'source_name', sr.source_name, 'source_identifier', sr.source_identifier,
                   'source_url', sr.source_url, 'evidence_scope', ams.evidence_scope
               )) FILTER (WHERE sr.id IS NOT NULL), '[]'::jsonb) AS sources
        FROM analytical_methods am
        LEFT JOIN analytical_method_sources ams ON ams.method_id=am.id
        LEFT JOIN source_records sr ON sr.id=ams.source_record_id
        WHERE am.review_status='in_review'
          AND EXISTS (SELECT 1 FROM organization_memberships om
                      WHERE om.organization_id=:org AND om.user_id=am.submitted_by
                        AND om.membership_status='active')
        GROUP BY am.id ORDER BY am.id LIMIT :limit
    """), {"org": organization_id, "limit": limit}).mappings().all()
    return {"items": [dict(row) for row in rows], "count": len(rows)}


@router.post("/{method_id}/decisions", status_code=201)
def decide_method(
    method_id: UUID,
    payload: MethodDecision,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    organization_id, role = _membership(current_user, db)
    if role not in REVIEW_ROLES:
        raise HTTPException(status_code=403, detail="Curator or reviewer permission is required.")
    method = db.execute(text("""
        SELECT am.* FROM analytical_methods am
        JOIN organization_memberships om ON om.user_id=am.submitted_by
        WHERE am.id=:id AND am.review_status='in_review'
          AND om.organization_id=:org AND om.membership_status='active'
        FOR UPDATE OF am
    """), {"id": method_id, "org": organization_id}).mappings().first()
    if not method:
        raise HTTPException(status_code=404, detail="Method review not found in this organization.")
    if str(method["submitted_by"]) == current_user["id"]:
        raise HTTPException(status_code=409, detail="A submitter cannot review their own method.")
    if payload.decision == "verified":
        has_source = db.execute(text("""
            SELECT EXISTS (
                SELECT 1 FROM analytical_method_sources ams
                JOIN source_records sr ON sr.id=ams.source_record_id
                WHERE ams.method_id=:method AND sr.source_url IS NOT NULL
            )
        """), {"method": method_id}).scalar_one()
        if not has_source:
            raise HTTPException(status_code=409, detail="Verification requires a linked reference URL.")
    db.execute(text("""
        INSERT INTO analytical_method_decisions (method_id, organization_id, reviewer_id, decision, rationale)
        VALUES (:method, :org, :reviewer, :decision, :rationale)
    """), {"method": method_id, "org": organization_id, "reviewer": current_user["id"],
           "decision": payload.decision, "rationale": payload.rationale.strip()})
    new_status = "verified" if payload.decision == "verified" else ("rejected" if payload.decision == "rejected" else "draft")
    db.execute(text("""
        UPDATE analytical_methods SET review_status=:status, reviewed_by=:reviewer, reviewed_at=now()
        WHERE id=:method
    """), {"status": new_status, "reviewer": current_user["id"], "method": method_id})
    db.execute(text("""
        INSERT INTO audit_events (actor_user_id, organization_id, action, entity_type, entity_id, event_metadata)
        VALUES (:actor, :org, 'analytical_method_review_decided', 'analytical_method', :id,
                jsonb_build_object('decision', :decision))
    """), {"actor": current_user["id"], "org": organization_id, "id": method_id, "decision": payload.decision})
    db.commit()
    return {"method_id": str(method_id), "review_status": new_status, "decision": payload.decision,
            "validation_status": method["validation_status"],
            "note": "Curation verification does not establish analytical method validation."}
