import json
from typing import Annotated, Literal
from urllib.parse import urlsplit
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, HttpUrl
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..db import get_db
from ..rate_limit_dependencies import authenticated_write_rate_limit
from .auth import get_current_user

router = APIRouter(prefix="/api/v1/peptide-chemical-forms", tags=["peptide chemical forms"])
SUBMIT_ROLES = {"organization_admin", "curator", "researcher"}
REVIEW_ROLES = {"organization_admin", "curator", "reviewer"}


class ChemicalFormSubmission(BaseModel):
    peptide_id: UUID
    peptide_sequence_id: UUID | None = None
    form_name: str = Field(min_length=2, max_length=200)
    form_type: Literal[
        "unspecified", "linear_peptide", "cyclic_peptide", "branched_peptide",
        "conjugate", "modified_peptide", "salt_form", "other"
    ] = "unspecified"
    raw_chemical_notation: str | None = Field(default=None, max_length=20000)
    residue_encoding: list[dict] = Field(default_factory=list, max_length=500)
    stereochemistry: dict = Field(default_factory=dict)
    noncanonical_residues: list[dict] = Field(default_factory=list, max_length=200)
    terminal_chemistry: dict = Field(default_factory=dict)
    post_translational_modifications: list[dict] = Field(default_factory=list, max_length=200)
    cyclization: dict = Field(default_factory=dict)
    conjugation: dict = Field(default_factory=dict)
    salt_and_counterions: dict = Field(default_factory=dict)
    chemical_formula: str | None = Field(default=None, max_length=200)
    average_molecular_mass: float | None = Field(default=None, gt=0, le=1000000)
    monoisotopic_mass: float | None = Field(default=None, gt=0, le=1000000)
    canonical_smiles: str | None = Field(default=None, max_length=20000)
    inchi: str | None = Field(default=None, max_length=20000)
    inchikey: str | None = Field(default=None, max_length=100)
    evidence_scope: str = Field(min_length=10, max_length=2000)
    source_name: str = Field(min_length=2, max_length=120)
    source_identifier: str = Field(min_length=1, max_length=200)
    source_url: HttpUrl


class ChemicalFormDecision(BaseModel):
    decision: Literal["verified", "rejected", "needs_changes"]
    visibility_scope: Literal["organization", "public"] = "organization"
    rationale: str = Field(min_length=20, max_length=4000)


def _membership(user: dict, db: Session) -> tuple[str, str]:
    organization_id = user.get("organization_id")
    if not organization_id:
        raise HTTPException(status_code=403, detail="Active organization membership required.")
    role = db.execute(text("""
        SELECT role FROM organization_memberships
        WHERE organization_id=:org AND user_id=:user_id AND membership_status='active'
    """), {"org": organization_id, "user_id": user["id"]}).scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=403, detail="Active organization membership required.")
    return str(organization_id), role


def _source_record(db: Session, payload: ChemicalFormSubmission):
    parsed = urlsplit(str(payload.source_url))
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise HTTPException(status_code=422, detail="Evidence source must use HTTPS without embedded credentials.")
    return db.execute(text("""
        INSERT INTO source_records (source_name,source_identifier,source_url,retrieved_at,raw_metadata)
        VALUES (:name,:identifier,:url,now(),'{}'::jsonb)
        ON CONFLICT (source_name,source_identifier)
        DO UPDATE SET source_url=EXCLUDED.source_url,last_seen_at=now()
        RETURNING id
    """), {
        "name": payload.source_name,
        "identifier": payload.source_identifier,
        "url": str(payload.source_url),
    }).scalar_one()


def _json(value) -> str:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail="Chemical-form structures must contain finite JSON values.") from exc


@router.get("")
def list_chemical_forms(
    peptide_id: UUID,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    _membership(current_user, db)
    rows = db.execute(text("""
        SELECT id,peptide_id,peptide_sequence_id,form_name,form_type,raw_chemical_notation,
               residue_encoding,stereochemistry,noncanonical_residues,terminal_chemistry,
               post_translational_modifications,cyclization,conjugation,salt_and_counterions,
               chemical_formula,average_molecular_mass,monoisotopic_mass,canonical_smiles,
               inchi,inchikey,evidence_scope,review_status,visibility_scope,created_at
        FROM peptide_chemical_forms
        WHERE peptide_id=:peptide_id
        ORDER BY form_name,id
    """), {"peptide_id": peptide_id}).mappings().all()
    return {"items": [dict(row) for row in rows], "count": len(rows)}


@router.post("", status_code=201, dependencies=[Depends(authenticated_write_rate_limit("chemical_form_write"))])
def submit_chemical_form(
    payload: ChemicalFormSubmission,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    organization_id, role = _membership(current_user, db)
    if role not in SUBMIT_ROLES:
        raise HTTPException(status_code=403, detail="Your organization role cannot submit chemical forms.")
    peptide = db.execute(text("""
        SELECT p.id FROM peptides p
        WHERE p.id=:peptide_id AND (
            p.review_status='verified'
            OR EXISTS (
                SELECT 1 FROM curation_reviews review
                WHERE review.entity_type='peptide' AND review.entity_id=p.id
                  AND review.owner_organization_id=:organization_id
            )
        )
    """), {"peptide_id": payload.peptide_id, "organization_id": organization_id}).scalar_one_or_none()
    if peptide is None:
        raise HTTPException(status_code=404, detail="Peptide record not found or inaccessible.")
    if payload.peptide_sequence_id is not None:
        sequence = db.execute(text("""
            SELECT id FROM peptide_sequences
            WHERE id=:sequence_id AND peptide_id=:peptide_id
        """), {"sequence_id": payload.peptide_sequence_id, "peptide_id": payload.peptide_id}).scalar_one_or_none()
        if sequence is None:
            raise HTTPException(status_code=422, detail="The selected sequence does not belong to this peptide.")

    source_id = _source_record(db, payload)
    form_id = db.execute(text("""
        INSERT INTO peptide_chemical_forms (
            peptide_id,peptide_sequence_id,form_name,form_type,raw_chemical_notation,
            residue_encoding,stereochemistry,noncanonical_residues,terminal_chemistry,
            post_translational_modifications,cyclization,conjugation,salt_and_counterions,
            chemical_formula,average_molecular_mass,monoisotopic_mass,canonical_smiles,
            inchi,inchikey,source_id,review_status,owner_organization_id,submitted_by,
            visibility_scope,evidence_scope
        ) VALUES (
            :peptide_id,:sequence_id,:form_name,:form_type,:notation,
            CAST(:residue_encoding AS jsonb),CAST(:stereochemistry AS jsonb),
            CAST(:noncanonical AS jsonb),CAST(:terminal AS jsonb),
            CAST(:ptms AS jsonb),CAST(:cyclization AS jsonb),CAST(:conjugation AS jsonb),
            CAST(:salts AS jsonb),:formula,:average_mass,:mono_mass,:smiles,:inchi,:inchikey,
            :source_id,'in_review',:organization_id,:submitted_by,'organization',:evidence_scope
        ) RETURNING id
    """), {
        "peptide_id": payload.peptide_id,
        "sequence_id": payload.peptide_sequence_id,
        "form_name": payload.form_name.strip(),
        "form_type": payload.form_type,
        "notation": payload.raw_chemical_notation,
        "residue_encoding": _json(payload.residue_encoding),
        "stereochemistry": _json(payload.stereochemistry),
        "noncanonical": _json(payload.noncanonical_residues),
        "terminal": _json(payload.terminal_chemistry),
        "ptms": _json(payload.post_translational_modifications),
        "cyclization": _json(payload.cyclization),
        "conjugation": _json(payload.conjugation),
        "salts": _json(payload.salt_and_counterions),
        "formula": payload.chemical_formula,
        "average_mass": payload.average_molecular_mass,
        "mono_mass": payload.monoisotopic_mass,
        "smiles": payload.canonical_smiles,
        "inchi": payload.inchi,
        "inchikey": payload.inchikey,
        "source_id": source_id,
        "organization_id": organization_id,
        "submitted_by": current_user["id"],
        "evidence_scope": payload.evidence_scope.strip(),
    }).scalar_one()
    db.execute(text("""
        INSERT INTO audit_events(actor_user_id,organization_id,action,entity_type,entity_id,event_metadata)
        VALUES(:user_id,:organization_id,'peptide_chemical_form_submitted',
               'peptide_chemical_form',:form_id,jsonb_build_object('peptide_id',:peptide_id,'source_id',:source_id))
    """), {
        "user_id": current_user["id"], "organization_id": organization_id,
        "form_id": form_id, "peptide_id": payload.peptide_id, "source_id": str(source_id),
    })
    db.commit()
    return {
        "id": str(form_id),
        "peptide_id": str(payload.peptide_id),
        "peptide_sequence_id": str(payload.peptide_sequence_id) if payload.peptide_sequence_id else None,
        "review_status": "in_review",
        "visibility_scope": "organization",
        "source_id": str(source_id),
    }


@router.post("/{form_id}/decisions", dependencies=[Depends(authenticated_write_rate_limit("chemical_form_review"))])
def decide_chemical_form(
    form_id: UUID,
    payload: ChemicalFormDecision,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    organization_id, role = _membership(current_user, db)
    if role not in REVIEW_ROLES:
        raise HTTPException(status_code=403, detail="Curator or reviewer permission is required.")
    if payload.decision != "verified" and payload.visibility_scope != "organization":
        raise HTTPException(status_code=422, detail="Only verified chemical forms may be published publicly.")
    form = db.execute(text("""
        SELECT id FROM peptide_chemical_forms
        WHERE id=:form_id AND owner_organization_id=:organization_id
          AND review_status='in_review'
        FOR UPDATE
    """), {"form_id": form_id, "organization_id": organization_id}).scalar_one_or_none()
    if form is None:
        raise HTTPException(status_code=404, detail="In-review chemical form not found.")
    db.execute(text("""
        INSERT INTO peptide_chemical_form_decisions
            (chemical_form_id,organization_id,reviewer_id,decision,visibility_scope,rationale)
        VALUES(:form_id,:organization_id,:reviewer_id,:decision,:visibility_scope,:rationale)
    """), {
        "form_id": form_id, "organization_id": organization_id,
        "reviewer_id": current_user["id"], "decision": payload.decision,
        "visibility_scope": payload.visibility_scope, "rationale": payload.rationale.strip(),
    })
    review_status = "verified" if payload.decision == "verified" else ("rejected" if payload.decision == "rejected" else "in_review")
    db.execute(text("""
        UPDATE peptide_chemical_forms
        SET review_status=:review_status,visibility_scope=:visibility_scope,updated_at=now()
        WHERE id=:form_id AND owner_organization_id=:organization_id
    """), {
        "review_status": review_status, "visibility_scope": payload.visibility_scope,
        "form_id": form_id, "organization_id": organization_id,
    })
    db.execute(text("""
        INSERT INTO audit_events(actor_user_id,organization_id,action,entity_type,entity_id,event_metadata)
        VALUES(:user_id,:organization_id,'peptide_chemical_form_decided',
               'peptide_chemical_form',:form_id,jsonb_build_object('decision',:decision,'visibility_scope',:visibility_scope))
    """), {
        "user_id": current_user["id"], "organization_id": organization_id,
        "form_id": form_id, "decision": payload.decision, "visibility_scope": payload.visibility_scope,
    })
    db.commit()
    return {
        "chemical_form_id": str(form_id),
        "decision": payload.decision,
        "review_status": review_status,
        "visibility_scope": payload.visibility_scope,
    }
