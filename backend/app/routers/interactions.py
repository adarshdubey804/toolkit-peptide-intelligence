import json
from typing import Annotated, Literal
from urllib.parse import urlsplit
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, HttpUrl
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..db import get_db
from .auth import get_current_user

router = APIRouter(prefix="/api/v1/interactions", tags=["molecular interaction intelligence"])
SUBMIT_ROLES = {"organization_admin", "curator", "researcher"}
REVIEW_ROLES = {"organization_admin", "curator", "reviewer"}


class SourceInput(BaseModel):
    source_name: str = Field(min_length=2, max_length=120)
    source_identifier: str = Field(min_length=1, max_length=200)
    source_url: HttpUrl


class InteractionSubmission(BaseModel):
    peptide_id: UUID
    target_id: UUID
    structure_identifier: str | None = Field(default=None, max_length=80)
    structure_source_url: HttpUrl | None = None
    interaction_method: Literal["experimental_complex", "computational_docking", "molecular_dynamics", "interface_analysis", "literature_report", "other"]
    evidence_type: Literal["regulatory", "clinical", "preclinical_animal", "in_vitro", "computational", "review", "unknown"]
    analysis_tool: str | None = Field(default=None, max_length=120)
    analysis_version: str | None = Field(default=None, max_length=80)
    interface_summary: str = Field(min_length=20, max_length=3000)
    interacting_residues: list[dict] = Field(default_factory=list, max_length=100)
    interaction_features: list[dict] = Field(default_factory=list, max_length=100)
    score_name: str | None = Field(default=None, max_length=100)
    score_value: float | None = Field(default=None, ge=-1e9, le=1e9)
    score_unit: str | None = Field(default=None, max_length=60)
    score_interpretation: str | None = Field(default=None, max_length=1000)
    limitations: str = Field(min_length=20, max_length=3000)
    source: SourceInput


class InteractionDecision(BaseModel):
    decision: Literal["verified", "rejected", "needs_changes"]
    rationale: str = Field(min_length=20, max_length=4000)


def _membership(user: dict, db: Session):
    organization_id = user.get("organization_id")
    role = db.execute(text("""
        SELECT role FROM organization_memberships
        WHERE organization_id=:org AND user_id=:user_id AND membership_status='active'
    """), {"org": organization_id, "user_id": user["id"]}).scalar_one_or_none() if organization_id else None
    if not role:
        raise HTTPException(status_code=403, detail="Active organization membership required.")
    return organization_id, role


def _source(db: Session, source: SourceInput):
    url = str(source.source_url)
    parsed = urlsplit(url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise HTTPException(status_code=422, detail="Evidence source must use HTTPS without embedded credentials.")
    return db.execute(text("""
        INSERT INTO source_records (source_name, source_identifier, source_url, retrieved_at, raw_metadata)
        VALUES (:name, :identifier, :url, now(), '{}'::jsonb)
        ON CONFLICT (source_name, source_identifier)
        DO UPDATE SET source_url=EXCLUDED.source_url, last_seen_at=now()
        RETURNING id
    """), {"name": source.source_name, "identifier": source.source_identifier, "url": url}).scalar_one()


@router.get("")
def list_interactions(
    db: Annotated[Session, Depends(get_db)],
    peptide_id: UUID | None = None,
    target_id: UUID | None = None,
    method: str | None = Query(default=None, max_length=40),
    limit: int = Query(default=50, ge=1, le=100),
):
    rows = db.execute(text("""
        SELECT a.id, a.peptide_id, p.preferred_name AS peptide_name,
               a.target_id, t.preferred_name AS target_name, t.gene_symbol, t.organism,
               a.structure_identifier, a.structure_source_url, a.interaction_method,
               a.evidence_type, a.analysis_tool, a.analysis_version, a.interface_summary,
               a.interacting_residues, a.interaction_features, a.score_name, a.score_value,
               a.score_unit, a.score_interpretation, a.limitations,
               sr.source_name, sr.source_identifier, sr.source_url, a.created_at
        FROM molecular_interaction_assessments a
        JOIN peptides p ON p.id=a.peptide_id
        JOIN targets t ON t.id=a.target_id
        JOIN source_records sr ON sr.id=a.source_id
        WHERE a.review_status='verified' AND p.review_status='verified'
          AND (:peptide IS NULL OR a.peptide_id=:peptide)
          AND (:target IS NULL OR a.target_id=:target)
          AND (:method IS NULL OR a.interaction_method=:method)
        ORDER BY a.created_at DESC LIMIT :limit
    """), {"peptide": peptide_id, "target": target_id, "method": method, "limit": limit}).mappings().all()
    return {"items": [dict(row) for row in rows], "count": len(rows),
            "notice": "Verified curation describes the source and analysis record; computational scores are not measured binding affinities."}


@router.post("", status_code=201)
def submit_interaction(
    payload: InteractionSubmission,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    organization_id, role = _membership(current_user, db)
    if role not in SUBMIT_ROLES:
        raise HTTPException(status_code=403, detail="Your role cannot submit interaction records.")
    peptide = db.execute(text("SELECT id FROM peptides WHERE id=:id AND review_status='verified'"),
                         {"id": payload.peptide_id}).scalar_one_or_none()
    if not peptide:
        raise HTTPException(status_code=409, detail="Peptide must be curator-verified.")
    target = db.execute(text("SELECT id FROM targets WHERE id=:id"), {"id": payload.target_id}).scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="Target record not found.")
    structure_url = str(payload.structure_source_url) if payload.structure_source_url else None
    if structure_url and (urlsplit(structure_url).scheme != "https" or not urlsplit(structure_url).hostname):
        raise HTTPException(status_code=422, detail="Structure URL must use HTTPS.")
    source_id = _source(db, payload.source)
    row = db.execute(text("""
        INSERT INTO molecular_interaction_assessments (
            peptide_id, target_id, structure_identifier, structure_source_url,
            interaction_method, evidence_type, analysis_tool, analysis_version,
            interface_summary, interacting_residues, interaction_features,
            score_name, score_value, score_unit, score_interpretation, limitations,
            source_id, review_status, submitted_by
        ) VALUES (
            :peptide, :target, :structure_id, :structure_url, :method, CAST(:evidence AS evidence_type),
            :tool, :version, :summary, CAST(:residues AS jsonb), CAST(:features AS jsonb),
            :score_name, :score_value, :score_unit, :score_interpretation, :limitations,
            :source, 'in_review', :submitter
        ) RETURNING id, review_status
    """), {
        "peptide": payload.peptide_id, "target": payload.target_id,
        "structure_id": payload.structure_identifier, "structure_url": structure_url,
        "method": payload.interaction_method, "evidence": payload.evidence_type,
        "tool": payload.analysis_tool, "version": payload.analysis_version,
        "summary": payload.interface_summary,
        "residues": json.dumps(payload.interacting_residues),
        "features": json.dumps(payload.interaction_features),
        "score_name": payload.score_name, "score_value": payload.score_value,
        "score_unit": payload.score_unit, "score_interpretation": payload.score_interpretation,
        "limitations": payload.limitations, "source": source_id, "submitter": current_user["id"],
    }).mappings().one()
    db.execute(text("""
        INSERT INTO audit_events (actor_user_id, organization_id, action, entity_type, entity_id, event_metadata)
        VALUES (:actor, :org, 'molecular_interaction_submitted', 'molecular_interaction_assessment', :id,
                jsonb_build_object('method', :method, 'evidence_type', :evidence))
    """), {"actor": current_user["id"], "org": organization_id, "id": row["id"],
           "method": payload.interaction_method, "evidence": payload.evidence_type})
    db.commit()
    return {"id": str(row["id"]), "review_status": row["review_status"],
            "note": "Submitted for review; computational scores remain method-specific and are not experimental affinity measurements."}


@router.get("/reviews")
def interaction_review_queue(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    limit: int = Query(default=50, ge=1, le=100),
):
    organization_id, role = _membership(current_user, db)
    if role not in REVIEW_ROLES:
        raise HTTPException(status_code=403, detail="Curator or reviewer permission is required.")
    rows = db.execute(text("""
        SELECT a.id, a.peptide_id, p.preferred_name AS peptide_name,
               a.target_id, t.preferred_name AS target_name, t.gene_symbol,
               a.structure_identifier, a.structure_source_url, a.interaction_method,
               a.evidence_type, a.analysis_tool, a.analysis_version, a.interface_summary,
               a.interacting_residues, a.interaction_features, a.score_name, a.score_value,
               a.score_unit, a.score_interpretation, a.limitations,
               sr.source_name, sr.source_identifier, sr.source_url
        FROM molecular_interaction_assessments a
        JOIN peptides p ON p.id=a.peptide_id JOIN targets t ON t.id=a.target_id
        JOIN source_records sr ON sr.id=a.source_id
        WHERE a.review_status='in_review' AND EXISTS (
            SELECT 1 FROM organization_memberships om
            WHERE om.user_id=a.submitted_by AND om.organization_id=:org
              AND om.membership_status='active'
        )
        ORDER BY a.created_at LIMIT :limit
    """), {"org": organization_id, "limit": limit}).mappings().all()
    return {"items": [dict(row) for row in rows], "count": len(rows)}


@router.post("/{assessment_id}/decisions", status_code=201)
def decide_interaction(
    assessment_id: UUID,
    payload: InteractionDecision,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    organization_id, role = _membership(current_user, db)
    if role not in REVIEW_ROLES:
        raise HTTPException(status_code=403, detail="Curator or reviewer permission is required.")
    row = db.execute(text("""
        SELECT a.* FROM molecular_interaction_assessments a
        JOIN organization_memberships om ON om.user_id=a.submitted_by
        WHERE a.id=:id AND a.review_status='in_review'
          AND om.organization_id=:org AND om.membership_status='active'
        FOR UPDATE OF a
    """), {"id": assessment_id, "org": organization_id}).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Interaction review not found in this organization.")
    if str(row["submitted_by"]) == current_user["id"]:
        raise HTTPException(status_code=409, detail="A submitter cannot review their own record.")
    db.execute(text("""
        INSERT INTO molecular_interaction_decisions (assessment_id, organization_id, reviewer_id, decision, rationale)
        VALUES (:id, :org, :reviewer, :decision, :rationale)
    """), {"id": assessment_id, "org": organization_id, "reviewer": current_user["id"],
           "decision": payload.decision, "rationale": payload.rationale.strip()})
    status = "verified" if payload.decision == "verified" else ("rejected" if payload.decision == "rejected" else "draft")
    db.execute(text("""
        UPDATE molecular_interaction_assessments
        SET review_status=:status, reviewed_by=:reviewer, reviewed_at=now() WHERE id=:id
    """), {"status": status, "reviewer": current_user["id"], "id": assessment_id})
    db.execute(text("""
        INSERT INTO audit_events (actor_user_id, organization_id, action, entity_type, entity_id, event_metadata)
        VALUES (:actor, :org, 'molecular_interaction_review_decided', 'molecular_interaction_assessment', :id,
                jsonb_build_object('decision', :decision))
    """), {"actor": current_user["id"], "org": organization_id, "id": assessment_id,
           "decision": payload.decision})
    db.commit()
    return {"assessment_id": str(assessment_id), "review_status": status, "decision": payload.decision,
            "note": "Curation validates record provenance and description, not physical binding or docking accuracy."}
