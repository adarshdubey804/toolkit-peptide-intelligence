from typing import Annotated, Literal
from uuid import UUID
from urllib.parse import urlsplit

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, HttpUrl
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..db import get_db
from .auth import get_current_user

router = APIRouter(prefix="/api/v1/formulations", tags=["formulation and stability intelligence"])
SUBMIT_ROLES = {"organization_admin", "curator", "researcher"}
REVIEW_ROLES = {"organization_admin", "curator", "reviewer"}


class SourceInput(BaseModel):
    source_name: str = Field(min_length=2, max_length=120)
    source_identifier: str = Field(min_length=1, max_length=200)
    source_url: HttpUrl
    evidence_scope: str = Field(min_length=5, max_length=1000)


class ComponentInput(BaseModel):
    component_name: str = Field(min_length=1, max_length=200)
    component_role: Literal["buffer", "tonicity_agent", "stabilizer", "surfactant", "preservative", "bulking_agent", "delivery_material", "container_contact", "other"]
    scientific_rationale: str | None = Field(default=None, max_length=2000)
    concentration_context: str | None = Field(default=None, max_length=500)
    source: SourceInput | None = None


class StabilityInput(BaseModel):
    study_context: str = Field(min_length=5, max_length=1000)
    condition_description: str | None = Field(default=None, max_length=1000)
    duration_description: str | None = Field(default=None, max_length=300)
    analytical_method_id: UUID | None = None
    observed_change: str = Field(min_length=5, max_length=2000)
    measurement_type: str | None = Field(default=None, max_length=300)
    result_interpretation: str | None = Field(default=None, max_length=2000)
    limitations: str = Field(min_length=10, max_length=2000)
    source: SourceInput


class FormulationSubmission(BaseModel):
    peptide_id: UUID | None = None
    formulation_name: str = Field(min_length=2, max_length=200)
    formulation_type: Literal["aqueous_solution", "lyophilized", "suspension", "emulsion", "hydrogel", "lipid_based", "polymer_based", "other"]
    delivery_system: str | None = Field(default=None, max_length=500)
    intended_research_context: str = Field(min_length=10, max_length=2000)
    formulation_rationale: str = Field(min_length=20, max_length=4000)
    physical_state: str | None = Field(default=None, max_length=300)
    container_closure_context: str | None = Field(default=None, max_length=1000)
    storage_context: str | None = Field(default=None, max_length=1000)
    development_stage: Literal["research", "preclinical", "clinical_investigational", "commercial_reference", "unknown"] = "research"
    limitations: str = Field(min_length=10, max_length=3000)
    components: list[ComponentInput] = Field(default_factory=list, max_length=30)
    stability_observations: list[StabilityInput] = Field(default_factory=list, max_length=30)
    sources: list[SourceInput] = Field(min_length=1, max_length=20)


class FormulationDecision(BaseModel):
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


def _source(db: Session, source: SourceInput):
    url = str(source.source_url)
    parsed = urlsplit(url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise HTTPException(status_code=422, detail="Evidence source must use HTTPS without embedded credentials.")
    source_id = db.execute(text("""
        INSERT INTO source_records (source_name, source_identifier, source_url, retrieved_at, raw_metadata)
        VALUES (:name, :identifier, :url, now(), '{}'::jsonb)
        ON CONFLICT (source_name, source_identifier)
        DO UPDATE SET source_url=EXCLUDED.source_url, last_seen_at=now()
        RETURNING id
    """), {"name": source.source_name, "identifier": source.source_identifier, "url": url}).scalar_one()
    return source_id


@router.get("")
def list_formulations(
    db: Annotated[Session, Depends(get_db)],
    q: str | None = Query(default=None, min_length=2, max_length=100),
    formulation_type: str | None = None,
    peptide_id: UUID | None = None,
    limit: int = Query(default=50, ge=1, le=100),
):
    rows = db.execute(text("""
        SELECT fp.id, fp.peptide_id, p.preferred_name AS peptide_name, fp.formulation_name,
               fp.formulation_type, fp.delivery_system, fp.intended_research_context,
               fp.formulation_rationale, fp.physical_state, fp.container_closure_context,
               fp.storage_context, fp.development_stage, fp.limitations,
               COALESCE((SELECT jsonb_agg(jsonb_build_object(
                   'component_name', fc.component_name, 'component_role', fc.component_role,
                   'scientific_rationale', fc.scientific_rationale,
                   'concentration_context', fc.concentration_context
               )) FROM formulation_components fc
               WHERE fc.formulation_id=fp.id AND fc.review_status='verified'), '[]'::jsonb) AS components,
               COALESCE((SELECT jsonb_agg(jsonb_build_object(
                   'study_context', fo.study_context, 'condition_description', fo.condition_description,
                   'duration_description', fo.duration_description, 'observed_change', fo.observed_change,
                   'measurement_type', fo.measurement_type, 'result_interpretation', fo.result_interpretation,
                   'limitations', fo.limitations, 'analytical_method_id', fo.analytical_method_id
               )) FROM formulation_stability_observations fo
               WHERE fo.formulation_id=fp.id AND fo.review_status='verified'), '[]'::jsonb) AS stability_observations,
               COALESCE((SELECT jsonb_agg(jsonb_build_object(
                   'source_name', sr.source_name, 'source_identifier', sr.source_identifier,
                   'source_url', sr.source_url, 'evidence_scope', fs.evidence_scope
               )) FROM formulation_sources fs JOIN source_records sr ON sr.id=fs.source_record_id
               WHERE fs.formulation_id=fp.id), '[]'::jsonb) AS sources
        FROM formulation_profiles fp
        LEFT JOIN peptides p ON p.id=fp.peptide_id
        WHERE fp.review_status='verified'
          AND (:q IS NULL OR fp.formulation_name ILIKE '%' || :q || '%' OR fp.intended_research_context ILIKE '%' || :q || '%')
          AND (:type IS NULL OR fp.formulation_type=:type)
          AND (:peptide_id IS NULL OR fp.peptide_id=:peptide_id)
        ORDER BY fp.formulation_name LIMIT :limit
    """), {"q": q, "type": formulation_type, "peptide_id": peptide_id, "limit": limit}).mappings().all()
    return {"items": [dict(row) for row in rows], "count": len(rows),
            "scope": "Curator-reviewed formulation records and individually reviewed components or observations only. Research information, not executable formulation instructions."}


@router.post("", status_code=201)
def submit_formulation(
    payload: FormulationSubmission,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    organization_id, role = _membership(current_user, db)
    if role not in SUBMIT_ROLES:
        raise HTTPException(status_code=403, detail="Your role cannot submit formulation records.")
    if payload.peptide_id:
        peptide = db.execute(text("SELECT id FROM peptides WHERE id=:id AND review_status='verified'"),
                             {"id": payload.peptide_id}).scalar_one_or_none()
        if not peptide:
            raise HTTPException(status_code=409, detail="Formulation can only link to a curator-verified peptide.")
    profile = db.execute(text("""
        INSERT INTO formulation_profiles (
            peptide_id, formulation_name, formulation_type, delivery_system,
            intended_research_context, formulation_rationale, physical_state,
            container_closure_context, storage_context, development_stage,
            limitations, review_status, submitted_by
        ) VALUES (
            :peptide, :name, :type, :delivery, :context, :rationale, :physical,
            :container, :storage, :stage, :limitations, 'in_review', :submitter
        ) RETURNING id, formulation_name, formulation_type, review_status
    """), {"peptide": payload.peptide_id, "name": payload.formulation_name.strip(),
           "type": payload.formulation_type, "delivery": payload.delivery_system,
           "context": payload.intended_research_context.strip(), "rationale": payload.formulation_rationale.strip(),
           "physical": payload.physical_state, "container": payload.container_closure_context,
           "storage": payload.storage_context, "stage": payload.development_stage,
           "limitations": payload.limitations.strip(), "submitter": current_user["id"]}).mappings().one()
    profile_id = profile["id"]
    for item in payload.sources:
        source_id = _source(db, item)
        db.execute(text("""
            INSERT INTO formulation_sources (formulation_id, source_record_id, evidence_scope)
            VALUES (:profile, :source, :scope) ON CONFLICT DO NOTHING
        """), {"profile": profile_id, "source": source_id, "scope": item.evidence_scope})
    for component in payload.components:
        source_id = _source(db, component.source) if component.source else None
        db.execute(text("""
            INSERT INTO formulation_components (
                formulation_id, component_name, component_role, scientific_rationale,
                concentration_context, source_id, review_status
            ) VALUES (:profile, :name, :role, :rationale, :context, :source, 'in_review')
        """), {"profile": profile_id, "name": component.component_name.strip(),
               "role": component.component_role, "rationale": component.scientific_rationale,
               "context": component.concentration_context, "source": source_id})
        if source_id:
            db.execute(text("""
                INSERT INTO formulation_sources (formulation_id, source_record_id, evidence_scope)
                VALUES (:profile, :source, :scope) ON CONFLICT DO NOTHING
            """), {"profile": profile_id, "source": source_id,
                   "scope": "Component evidence: " + component.component_name})
    for observation in payload.stability_observations:
        source_id = _source(db, observation.source)
        if observation.analytical_method_id:
            method = db.execute(text("""
                SELECT id FROM analytical_methods WHERE id=:id AND review_status='verified'
            """), {"id": observation.analytical_method_id}).scalar_one_or_none()
            if not method:
                raise HTTPException(status_code=409, detail="Stability observation must reference a curator-verified analytical method.")
        db.execute(text("""
            INSERT INTO formulation_stability_observations (
                formulation_id, study_context, condition_description, duration_description,
                analytical_method_id, observed_change, measurement_type, result_interpretation,
                limitations, source_id, review_status
            ) VALUES (:profile, :context, :condition, :duration, :method, :change,
                      :measurement, :interpretation, :limitations, :source, 'in_review')
        """), {"profile": profile_id, "context": observation.study_context,
               "condition": observation.condition_description, "duration": observation.duration_description,
               "method": observation.analytical_method_id, "change": observation.observed_change,
               "measurement": observation.measurement_type, "interpretation": observation.result_interpretation,
               "limitations": observation.limitations, "source": source_id})
        db.execute(text("""
            INSERT INTO formulation_sources (formulation_id, source_record_id, evidence_scope)
            VALUES (:profile, :source, :scope) ON CONFLICT DO NOTHING
        """), {"profile": profile_id, "source": source_id, "scope": "Stability observation: " + observation.study_context})
    db.execute(text("""
        INSERT INTO audit_events (actor_user_id, organization_id, action, entity_type, entity_id, event_metadata)
        VALUES (:actor, :org, 'formulation_submitted', 'formulation_profile', :id,
                jsonb_build_object('formulation_type', :type, 'source_count', :source_count))
    """), {"actor": current_user["id"], "org": organization_id, "id": profile_id,
           "type": payload.formulation_type, "source_count": len(payload.sources)})
    db.commit()
    return dict(profile)


@router.get("/reviews")
def formulation_review_queue(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    limit: int = Query(default=50, ge=1, le=100),
):
    organization_id, role = _membership(current_user, db)
    if role not in REVIEW_ROLES:
        raise HTTPException(status_code=403, detail="Curator or reviewer permission is required.")
    rows = db.execute(text("""
        SELECT fp.id, fp.formulation_name, fp.formulation_type, fp.intended_research_context,
               fp.formulation_rationale, fp.limitations, fp.submitted_by, fp.review_status,
               COALESCE(jsonb_agg(DISTINCT jsonb_build_object(
                   'source_name', sr.source_name, 'source_identifier', sr.source_identifier,
                   'source_url', sr.source_url, 'evidence_scope', fs.evidence_scope
               )) FILTER (WHERE sr.id IS NOT NULL), '[]'::jsonb) AS sources,
               (SELECT count(*) FROM formulation_components fc WHERE fc.formulation_id=fp.id) AS component_count,
               (SELECT count(*) FROM formulation_stability_observations fo WHERE fo.formulation_id=fp.id) AS observation_count
        FROM formulation_profiles fp
        LEFT JOIN formulation_sources fs ON fs.formulation_id=fp.id
        LEFT JOIN source_records sr ON sr.id=fs.source_record_id
        WHERE fp.review_status='in_review'
          AND EXISTS (SELECT 1 FROM organization_memberships om
                      WHERE om.organization_id=:org AND om.user_id=fp.submitted_by
                        AND om.membership_status='active')
        GROUP BY fp.id ORDER BY fp.created_at LIMIT :limit
    """), {"org": organization_id, "limit": limit}).mappings().all()
    return {"items": [dict(row) for row in rows], "count": len(rows)}


@router.post("/{formulation_id}/decisions", status_code=201)
def decide_formulation(
    formulation_id: UUID,
    payload: FormulationDecision,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    organization_id, role = _membership(current_user, db)
    if role not in REVIEW_ROLES:
        raise HTTPException(status_code=403, detail="Curator or reviewer permission is required.")
    profile = db.execute(text("""
        SELECT fp.* FROM formulation_profiles fp
        JOIN organization_memberships om ON om.user_id=fp.submitted_by
        WHERE fp.id=:id AND fp.review_status='in_review'
          AND om.organization_id=:org AND om.membership_status='active'
        FOR UPDATE OF fp
    """), {"id": formulation_id, "org": organization_id}).mappings().first()
    if not profile:
        raise HTTPException(status_code=404, detail="Formulation review not found in this organization.")
    if str(profile["submitted_by"]) == current_user["id"]:
        raise HTTPException(status_code=409, detail="A submitter cannot review their own formulation.")
    if payload.decision == "verified":
        source_count = db.execute(text("""
            SELECT count(*) FROM formulation_sources fs
            JOIN source_records sr ON sr.id=fs.source_record_id
            WHERE fs.formulation_id=:id AND sr.source_url IS NOT NULL
        """), {"id": formulation_id}).scalar_one()
        if source_count < 1:
            raise HTTPException(status_code=409, detail="Verification requires at least one linked reference URL.")
    db.execute(text("""
        INSERT INTO formulation_review_decisions (formulation_id, organization_id, reviewer_id, decision, rationale)
        VALUES (:id, :org, :reviewer, :decision, :rationale)
    """), {"id": formulation_id, "org": organization_id, "reviewer": current_user["id"],
           "decision": payload.decision, "rationale": payload.rationale.strip()})
    new_status = "verified" if payload.decision == "verified" else ("rejected" if payload.decision == "rejected" else "draft")
    db.execute(text("""
        UPDATE formulation_profiles SET review_status=:status, reviewed_by=:reviewer, reviewed_at=now()
        WHERE id=:id
    """), {"status": new_status, "reviewer": current_user["id"], "id": formulation_id})
    if payload.decision == "verified":
        db.execute(text("UPDATE formulation_components SET review_status='verified' WHERE formulation_id=:id"),
                   {"id": formulation_id})
        db.execute(text("UPDATE formulation_stability_observations SET review_status='verified' WHERE formulation_id=:id"),
                   {"id": formulation_id})
    db.execute(text("""
        INSERT INTO audit_events (actor_user_id, organization_id, action, entity_type, entity_id, event_metadata)
        VALUES (:actor, :org, 'formulation_review_decided', 'formulation_profile', :id,
                jsonb_build_object('decision', :decision))
    """), {"actor": current_user["id"], "org": organization_id, "id": formulation_id, "decision": payload.decision})
    db.commit()
    return {"formulation_id": str(formulation_id), "review_status": new_status, "decision": payload.decision,
            "note": "Review confirms record curation only; it does not validate a formulation, stability claim, shelf life, or manufacturing procedure."}
