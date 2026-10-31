from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, HttpUrl, field_validator
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .auth import get_current_user
from ..db import get_db

router = APIRouter(prefix="/api/v1/dossiers", tags=["peptide scientific dossiers"])


class SequenceInput(BaseModel):
    sequence: str = Field(min_length=1, max_length=10000)
    sequence_type: Literal["amino_acid", "nucleotide", "other"] = "amino_acid"
    n_terminus: str | None = Field(default=None, max_length=200)
    c_terminus: str | None = Field(default=None, max_length=200)
    modifications: list[dict] = Field(default_factory=list, max_length=100)
    stereochemistry_notes: str | None = Field(default=None, max_length=2000)


class ChemistryInput(BaseModel):
    chemical_form: str | None = Field(default=None, max_length=200)
    molecular_formula: str | None = Field(default=None, max_length=200)
    average_molecular_mass: float | None = Field(default=None, gt=0, le=1000000)
    monoisotopic_mass: float | None = Field(default=None, gt=0, le=1000000)
    canonical_smiles: str | None = Field(default=None, max_length=20000)
    inchi: str | None = Field(default=None, max_length=20000)
    inchikey: str | None = Field(default=None, max_length=100)
    property_origin: Literal["measured", "calculated", "predicted", "imported", "unknown"] = "unknown"
    method_or_tool: str | None = Field(default=None, max_length=300)


class ClaimInput(BaseModel):
    claim_text: str = Field(min_length=10, max_length=4000)
    claim_domain: Literal["identity", "chemistry", "mechanism", "target", "pathway", "safety", "clinical", "formulation", "analytical", "other"]
    evidence_type: Literal["regulatory", "clinical", "preclinical_animal", "in_vitro", "computational", "review", "unknown"] = "unknown"
    limitations: str | None = Field(default=None, max_length=4000)


class PeptideDossierCreate(BaseModel):
    preferred_name: str = Field(min_length=2, max_length=200)
    peptide_category: str | None = Field(default=None, max_length=100)
    description: str | None = Field(default=None, max_length=4000)
    development_status: str | None = Field(default=None, max_length=100)
    intended_use_class: Literal["research_only", "investigational", "approved_medicine", "endogenous_reference", "unspecified"] = "unspecified"
    aliases: list[str] = Field(default_factory=list, max_length=30)
    sequences: list[SequenceInput] = Field(default_factory=list, max_length=20)
    chemical_properties: list[ChemistryInput] = Field(default_factory=list, max_length=20)
    claims: list[ClaimInput] = Field(default_factory=list, max_length=50)
    source_name: str = Field(min_length=2, max_length=120)
    source_identifier: str | None = Field(default=None, max_length=300)
    source_url: HttpUrl
    source_license_notes: str | None = Field(default=None, max_length=1000)

    @field_validator("aliases")
    @classmethod
    def normalize_aliases(cls, values):
        normalized = list(dict.fromkeys(value.strip() for value in values if value.strip()))
        if any(len(value) > 200 for value in normalized):
            raise ValueError("Aliases must be 200 characters or fewer.")
        return normalized


def _member_role(user: dict, db: Session) -> str:
    if not user.get("organization_id"):
        raise HTTPException(status_code=403, detail="Organization membership required.")
    role = db.execute(text("""
        SELECT role FROM organization_memberships
        WHERE organization_id=:org AND user_id=:user_id AND membership_status='active'
    """), {"org": user["organization_id"], "user_id": user["id"]}).scalar_one_or_none()
    if role not in ("organization_admin", "researcher", "curator"):
        raise HTTPException(status_code=403, detail="Your role cannot create scientific dossiers.")
    return role


@router.post("", status_code=201)
def create_peptide_dossier(
    payload: PeptideDossierCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Create a draft dossier and submit it to the organization's scientific review queue."""
    _member_role(current_user, db)
    try:
        with db.begin():
            source_id = db.execute(text("""
                INSERT INTO source_records
                    (source_name, source_identifier, source_url, license_notes, raw_metadata, record_status)
                VALUES (:name, :identifier, :url, :license, '{}'::jsonb, 'active')
                RETURNING id
            """), {
                "name": payload.source_name.strip(),
                "identifier": payload.source_identifier.strip() if payload.source_identifier else None,
                "url": str(payload.source_url),
                "license": payload.source_license_notes,
            }).scalar_one()

            peptide_id = db.execute(text("""
                INSERT INTO peptides
                    (preferred_name, peptide_category, description, development_status,
                     intended_use_class, review_status, primary_source_id)
                VALUES (:name, :category, :description, :development_status,
                        :intended_use, 'in_review', :source_id)
                RETURNING id
            """), {
                "name": payload.preferred_name.strip(), "category": payload.peptide_category,
                "description": payload.description, "development_status": payload.development_status,
                "intended_use": payload.intended_use_class, "source_id": source_id,
            }).scalar_one()

            for alias in payload.aliases:
                db.execute(text("""
                    INSERT INTO peptide_aliases (peptide_id, alias, source_id)
                    VALUES (:peptide_id, :alias, :source_id)
                    ON CONFLICT (peptide_id, alias) DO NOTHING
                """), {"peptide_id": peptide_id, "alias": alias, "source_id": source_id})

            for sequence in payload.sequences:
                db.execute(text("""
                    INSERT INTO peptide_sequences
                        (peptide_id, sequence, sequence_type, n_terminus, c_terminus,
                         modifications, stereochemistry_notes, source_id, review_status)
                    VALUES (:peptide_id, :sequence, :sequence_type, :n_terminus, :c_terminus,
                            CAST(:modifications AS jsonb), :stereochemistry, :source_id, 'in_review')
                """), {
                    "peptide_id": peptide_id, "sequence": sequence.sequence.strip(),
                    "sequence_type": sequence.sequence_type, "n_terminus": sequence.n_terminus,
                    "c_terminus": sequence.c_terminus,
                    "modifications": __import__("json").dumps(sequence.modifications),
                    "stereochemistry": sequence.stereochemistry_notes, "source_id": source_id,
                })

            for chemistry in payload.chemical_properties:
                db.execute(text("""
                    INSERT INTO chemical_properties
                        (peptide_id, chemical_form, molecular_formula, average_molecular_mass,
                         monoisotopic_mass, canonical_smiles, inchi, inchikey, property_origin,
                         method_or_tool, source_id, review_status)
                    VALUES (:peptide_id, :form, :formula, :average_mass, :mono_mass, :smiles,
                            :inchi, :inchikey, :origin, :method, :source_id, 'in_review')
                """), {
                    "peptide_id": peptide_id, "form": chemistry.chemical_form,
                    "formula": chemistry.molecular_formula, "average_mass": chemistry.average_molecular_mass,
                    "mono_mass": chemistry.monoisotopic_mass, "smiles": chemistry.canonical_smiles,
                    "inchi": chemistry.inchi, "inchikey": chemistry.inchikey,
                    "origin": chemistry.property_origin, "method": chemistry.method_or_tool,
                    "source_id": source_id,
                })

            claim_ids = []
            for claim in payload.claims:
                claim_id = db.execute(text("""
                    INSERT INTO evidence_claims
                        (peptide_id, claim_text, claim_domain, evidence_type, limitations, review_status)
                    VALUES (:peptide_id, :claim, :domain, CAST(:evidence_type AS evidence_type),
                            :limitations, 'in_review')
                    RETURNING id
                """), {
                    "peptide_id": peptide_id, "claim": claim.claim_text.strip(),
                    "domain": claim.claim_domain, "evidence_type": claim.evidence_type,
                    "limitations": claim.limitations,
                }).scalar_one()
                db.execute(text("""
                    INSERT INTO claim_sources (claim_id, source_record_id, relationship)
                    VALUES (:claim_id, :source_id, 'supports')
                """), {"claim_id": claim_id, "source_id": source_id})
                claim_ids.append(str(claim_id))

            review_id = db.execute(text("""
                INSERT INTO curation_reviews
                    (entity_type, entity_id, source_record_id, review_status, priority, submitted_by)
                VALUES ('peptide', :peptide_id, :source_id, 'in_review', 'normal', :submitter)
                RETURNING id
            """), {"peptide_id": peptide_id, "source_id": source_id, "submitter": current_user["id"]}).scalar_one()

            db.execute(text("""
                INSERT INTO audit_events (actor_user_id, organization_id, action, entity_type, entity_id, event_metadata)
                VALUES (:actor, :org, 'peptide_dossier_created', 'peptide', :peptide_id,
                        jsonb_build_object('source_record_id', :source_id, 'review_id', :review_id,
                                           'claim_count', :claim_count))
            """), {
                "actor": current_user["id"], "org": current_user["organization_id"],
                "peptide_id": peptide_id, "source_id": source_id, "review_id": review_id,
                "claim_count": len(claim_ids),
            })
        return {
            "peptide_id": str(peptide_id),
            "source_record_id": str(source_id),
            "review_id": str(review_id),
            "claim_ids": claim_ids,
            "review_status": "in_review",
            "message": "Draft dossier submitted to your organization's scientific review queue. It is not publicly visible until verified.",
        }
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="The dossier conflicts with an existing source or record. Check the source identifier and retry.") from exc
