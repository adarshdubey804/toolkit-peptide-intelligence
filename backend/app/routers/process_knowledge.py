from typing import Annotated, Literal
from uuid import UUID
from urllib.parse import urlsplit

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, HttpUrl
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..db import get_db
from .auth import get_current_user

router = APIRouter(prefix="/api/v1/process-knowledge", tags=["process development intelligence"])
SUBMIT_ROLES = {"organization_admin", "curator", "researcher"}
REVIEW_ROLES = {"organization_admin", "curator", "reviewer"}


class SourceInput(BaseModel):
    source_name: str = Field(min_length=2, max_length=120)
    source_identifier: str = Field(min_length=1, max_length=200)
    source_url: HttpUrl
    evidence_scope: str = Field(min_length=5, max_length=1000)


class StageInput(BaseModel):
    stage_name: str = Field(min_length=2, max_length=160)
    stage_category: Literal["starting_materials", "synthesis_or_expression", "cleavage_or_recovery", "purification", "characterization", "impurity_control", "formulation_interface", "scale_up", "quality_system", "other"]
    scientific_purpose: str = Field(min_length=10, max_length=2000)
    analytical_readouts: list[str] = Field(default_factory=list, max_length=20)
    process_risks: str | None = Field(default=None, max_length=2000)
    source: SourceInput | None = None


class ProcessSubmission(BaseModel):
    peptide_id: UUID | None = None
    profile_title: str = Field(min_length=3, max_length=200)
    process_platform: Literal["solid_phase_peptide_synthesis", "liquid_phase_peptide_synthesis", "recombinant_expression", "hybrid_synthesis", "other"]
    development_context: str = Field(min_length=10, max_length=2000)
    process_overview: str = Field(min_length=30, max_length=5000)
    critical_quality_attributes: list[str] = Field(default_factory=list, max_length=30)
    process_impurity_context: list[str] = Field(default_factory=list, max_length=30)
    scale_up_considerations: str | None = Field(default=None, max_length=3000)
    limitations: str = Field(min_length=10, max_length=3000)
    stages: list[StageInput] = Field(default_factory=list, max_length=30)
    sources: list[SourceInput] = Field(min_length=1, max_length=20)


class ProcessDecision(BaseModel):
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
def list_process_knowledge(
    db: Annotated[Session, Depends(get_db)],
    q: str | None = Query(default=None, min_length=2, max_length=100),
    process_platform: str | None = None,
    peptide_id: UUID | None = None,
    limit: int = Query(default=50, ge=1, le=100),
):
    rows = db.execute(text("""
        SELECT pk.id, pk.peptide_id, p.preferred_name AS peptide_name, pk.profile_title,
               pk.process_platform, pk.development_context, pk.process_overview,
               pk.critical_quality_attributes, pk.process_impurity_context,
               pk.scale_up_considerations, pk.limitations,
               COALESCE((SELECT jsonb_agg(jsonb_build_object(
                   'stage_name', ps.stage_name, 'stage_category', ps.stage_category,
                   'scientific_purpose', ps.scientific_purpose,
                   'analytical_readouts', ps.analytical_readouts,
                   'process_risks', ps.process_risks,
                   'source_url', sr2.source_url
               )) FROM process_knowledge_stages ps LEFT JOIN source_records sr2 ON sr2.id=ps.source_id
               WHERE ps.profile_id=pk.id AND ps.review_status='verified'), '[]'::jsonb) AS stages,
               COALESCE((SELECT jsonb_agg(jsonb_build_object(
                   'source_name', sr.source_name, 'source_identifier', sr.source_identifier,
                   'source_url', sr.source_url, 'evidence_scope', pks.evidence_scope
               )) FROM process_knowledge_sources pks JOIN source_records sr ON sr.id=pks.source_record_id
               WHERE pks.profile_id=pk.id), '[]'::jsonb) AS sources
        FROM process_knowledge_profiles pk LEFT JOIN peptides p ON p.id=pk.peptide_id
        WHERE pk.review_status='verified'
          AND (:q IS NULL OR pk.profile_title ILIKE '%' || :q || '%' OR pk.development_context ILIKE '%' || :q || '%')
          AND (:platform IS NULL OR pk.process_platform=:platform)
          AND (:peptide IS NULL OR pk.peptide_id=:peptide)
        ORDER BY pk.profile_title LIMIT :limit
    """), {"q": q, "platform": process_platform, "peptide": peptide_id, "limit": limit}).mappings().all()
    return {"items": [dict(row) for row in rows], "count": len(rows),
            "scope": "Curator-reviewed descriptive process-development literature only; no executable synthesis parameters, batch instructions or release criteria."}


@router.post("", status_code=201)
def submit_process_knowledge(
    payload: ProcessSubmission,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    organization_id, role = _membership(current_user, db)
    if role not in SUBMIT_ROLES:
        raise HTTPException(status_code=403, detail="Your role cannot submit process knowledge.")
    if payload.peptide_id and not db.execute(text(
        "SELECT id FROM peptides WHERE id=:id AND review_status='verified'"
    ), {"id": payload.peptide_id}).scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Linked peptide must be curator-verified.")
    row = db.execute(text("""
        INSERT INTO process_knowledge_profiles (
            peptide_id, profile_title, process_platform, development_context, process_overview,
            critical_quality_attributes, process_impurity_context, scale_up_considerations,
            limitations, review_status, submitted_by
        ) VALUES (:peptide, :title, :platform, :context, :overview, CAST(:cqa AS jsonb),
                  CAST(:impurities AS jsonb), :scaleup, :limitations, 'in_review', :submitter)
        RETURNING id, profile_title, process_platform, review_status
    """), {"peptide": payload.peptide_id, "title": payload.profile_title.strip(),
           "platform": payload.process_platform, "context": payload.development_context,
           "overview": payload.process_overview, "cqa": __import__("json").dumps(payload.critical_quality_attributes),
           "impurities": __import__("json").dumps(payload.process_impurity_context),
           "scaleup": payload.scale_up_considerations, "limitations": payload.limitations,
           "submitter": current_user["id"]}).mappings().one()
    profile_id = row["id"]
    for source in payload.sources:
        source_id = _source(db, source)
        db.execute(text("""
            INSERT INTO process_knowledge_sources (profile_id, source_record_id, evidence_scope)
            VALUES (:profile, :source, :scope) ON CONFLICT DO NOTHING
        """), {"profile": profile_id, "source": source_id, "scope": source.evidence_scope})
    for stage in payload.stages:
        source_id = _source(db, stage.source) if stage.source else None
        db.execute(text("""
            INSERT INTO process_knowledge_stages (
                profile_id, stage_name, stage_category, scientific_purpose,
                analytical_readouts, process_risks, source_id, review_status
            ) VALUES (:profile, :name, :category, :purpose, CAST(:readouts AS jsonb),
                      :risks, :source, 'in_review')
        """), {"profile": profile_id, "name": stage.stage_name, "category": stage.stage_category,
               "purpose": stage.scientific_purpose,
               "readouts": __import__("json").dumps(stage.analytical_readouts),
               "risks": stage.process_risks, "source": source_id})
        if source_id:
            db.execute(text("""
                INSERT INTO process_knowledge_sources (profile_id, source_record_id, evidence_scope)
                VALUES (:profile, :source, :scope) ON CONFLICT DO NOTHING
            """), {"profile": profile_id, "source": source_id, "scope": "Stage: " + stage.stage_name})
    db.execute(text("""
        INSERT INTO audit_events (actor_user_id, organization_id, action, entity_type, entity_id, event_metadata)
        VALUES (:actor, :org, 'process_knowledge_submitted', 'process_knowledge_profile', :id,
                jsonb_build_object('platform', :platform, 'stage_count', :stages))
    """), {"actor": current_user["id"], "org": organization_id, "id": profile_id,
           "platform": payload.process_platform, "stages": len(payload.stages)})
    db.commit()
    return dict(row)


@router.get("/reviews")
def process_review_queue(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    limit: int = Query(default=50, ge=1, le=100),
):
    organization_id, role = _membership(current_user, db)
    if role not in REVIEW_ROLES:
        raise HTTPException(status_code=403, detail="Curator or reviewer permission is required.")
    rows = db.execute(text("""
        SELECT pk.id, pk.profile_title, pk.process_platform, pk.development_context,
               pk.process_overview, pk.limitations,
               COALESCE((SELECT jsonb_agg(jsonb_build_object(
                   'source_name', sr.source_name, 'source_identifier', sr.source_identifier,
                   'source_url', sr.source_url, 'evidence_scope', pks.evidence_scope
               )) FROM process_knowledge_sources pks JOIN source_records sr ON sr.id=pks.source_record_id
               WHERE pks.profile_id=pk.id), '[]'::jsonb) AS sources,
               COALESCE((SELECT jsonb_agg(jsonb_build_object(
                   'stage_name', ps.stage_name, 'stage_category', ps.stage_category,
                   'scientific_purpose', ps.scientific_purpose, 'analytical_readouts', ps.analytical_readouts,
                   'process_risks', ps.process_risks, 'source_url', sr2.source_url
               )) FROM process_knowledge_stages ps LEFT JOIN source_records sr2 ON sr2.id=ps.source_id
               WHERE ps.profile_id=pk.id), '[]'::jsonb) AS stages
        FROM process_knowledge_profiles pk
        WHERE pk.review_status='in_review'
          AND EXISTS (SELECT 1 FROM organization_memberships om
                      WHERE om.user_id=pk.submitted_by AND om.organization_id=:org
                        AND om.membership_status='active')
        ORDER BY pk.created_at LIMIT :limit
    """), {"org": organization_id, "limit": limit}).mappings().all()
    return {"items": [dict(row) for row in rows], "count": len(rows)}


@router.post("/{profile_id}/decisions", status_code=201)
def decide_process_knowledge(
    profile_id: UUID,
    payload: ProcessDecision,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    organization_id, role = _membership(current_user, db)
    if role not in REVIEW_ROLES:
        raise HTTPException(status_code=403, detail="Curator or reviewer permission is required.")
    profile = db.execute(text("""
        SELECT pk.* FROM process_knowledge_profiles pk
        JOIN organization_memberships om ON om.user_id=pk.submitted_by
        WHERE pk.id=:id AND pk.review_status='in_review'
          AND om.organization_id=:org AND om.membership_status='active'
        FOR UPDATE OF pk
    """), {"id": profile_id, "org": organization_id}).mappings().first()
    if not profile:
        raise HTTPException(status_code=404, detail="Process review not found in this organization.")
    if str(profile["submitted_by"]) == current_user["id"]:
        raise HTTPException(status_code=409, detail="A submitter cannot review their own record.")
    if payload.decision == "verified":
        count = db.execute(text("""
            SELECT count(*) FROM process_knowledge_sources pks
            JOIN source_records sr ON sr.id=pks.source_record_id
            WHERE pks.profile_id=:id AND sr.source_url IS NOT NULL
        """), {"id": profile_id}).scalar_one()
        if count < 1:
            raise HTTPException(status_code=409, detail="Verification requires linked source URLs.")
    db.execute(text("""
        INSERT INTO process_knowledge_decisions (profile_id, organization_id, reviewer_id, decision, rationale)
        VALUES (:id, :org, :reviewer, :decision, :rationale)
    """), {"id": profile_id, "org": organization_id, "reviewer": current_user["id"],
           "decision": payload.decision, "rationale": payload.rationale.strip()})
    status = "verified" if payload.decision == "verified" else ("rejected" if payload.decision == "rejected" else "draft")
    db.execute(text("""
        UPDATE process_knowledge_profiles SET review_status=:status, reviewed_by=:reviewer, reviewed_at=now()
        WHERE id=:id
    """), {"status": status, "reviewer": current_user["id"], "id": profile_id})
    if status == "verified":
        db.execute(text("UPDATE process_knowledge_stages SET review_status='verified' WHERE profile_id=:id"),
                   {"id": profile_id})
    db.execute(text("""
        INSERT INTO audit_events (actor_user_id, organization_id, action, entity_type, entity_id, event_metadata)
        VALUES (:actor, :org, 'process_knowledge_review_decided', 'process_knowledge_profile', :id,
                jsonb_build_object('decision', :decision))
    """), {"actor": current_user["id"], "org": organization_id, "id": profile_id,
           "decision": payload.decision})
    db.commit()
    return {"profile_id": str(profile_id), "review_status": status, "decision": payload.decision,
            "note": "Curation verifies the sourced description only, not process performance, manufacturing suitability or batch release."}
