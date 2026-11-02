from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..db import get_db
from .auth import get_current_user

router = APIRouter(prefix="/api/v1/data-quality", tags=["data quality"])


def _percentage(numerator: int, denominator: int) -> float | None:
    return round(100 * numerator / denominator, 1) if denominator else None


def build_completeness_report(db: Session, organization_id: UUID) -> dict:
    """Return separate coverage dimensions; deliberately no misleading composite score."""
    peptide = db.execute(text("""
        SELECT COUNT(*) AS total,
               COUNT(*) FILTER (WHERE review_status='verified') AS verified,
               COUNT(*) FILTER (WHERE primary_source_id IS NOT NULL) AS with_primary_source
        FROM peptides
    """)).mappings().one()
    sequences = db.execute(text("""
        SELECT COUNT(*) AS total,
               COUNT(*) FILTER (WHERE sequence IS NOT NULL AND btrim(sequence)<>'') AS with_sequence,
               COUNT(*) FILTER (
                   WHERE notation_format='one_letter_amino_acid_sequence'
                     AND identity_fingerprint IS NOT NULL
                     AND canonicalization_version IS NOT NULL
               ) AS standard_sequence_fingerprinted,
               COUNT(*) FILTER (WHERE notation_format='one_letter_amino_acid_sequence') AS standard_sequence_candidates
        FROM peptide_sequences
    """)).mappings().one()
    forms = db.execute(text("""
        SELECT COUNT(*) AS total,
               COUNT(*) FILTER (WHERE review_status='verified') AS verified,
               COUNT(*) FILTER (WHERE source_id IS NOT NULL) AS with_source,
               COUNT(*) FILTER (WHERE identity_fingerprint IS NOT NULL AND canonicalization_version IS NOT NULL) AS versioned_identity
        FROM peptide_chemical_forms
    """)).mappings().one()
    claims = db.execute(text("""
        SELECT COUNT(DISTINCT claim.id) AS total,
               COUNT(DISTINCT claim.id) FILTER (
                   WHERE EXISTS (
                       SELECT 1 FROM claim_sources source
                       WHERE source.claim_id=claim.id
                         AND (source.source_record_id IS NOT NULL OR source.publication_id IS NOT NULL)
                   )
               ) AS with_source,
               COUNT(DISTINCT claim.id) FILTER (
                   WHERE EXISTS (
                       SELECT 1 FROM evidence_claim_revisions revision
                       WHERE revision.claim_id=claim.id
                   )
               ) AS with_revision,
               COUNT(DISTINCT claim.id) FILTER (WHERE claim.review_status='verified') AS verified
        FROM evidence_claims claim
        WHERE EXISTS (
            SELECT 1 FROM curation_reviews review
            WHERE review.entity_type='evidence_claim'
              AND review.entity_id=claim.id
              AND review.owner_organization_id=:org
        )
    """), {"org": organization_id}).mappings().one()
    sources = db.execute(text("""
        SELECT COUNT(*) AS total,
               COUNT(*) FILTER (
                   WHERE EXISTS (
                       SELECT 1 FROM source_record_versions version
                       WHERE version.source_record_id=source.id
                   )
               ) AS with_version
        FROM source_records source
    """)).mappings().one()
    extraction = db.execute(text("""
        SELECT COUNT(*) AS total,
               COUNT(*) FILTER (WHERE source_record_id IS NOT NULL) AS with_source_record,
               COUNT(*) FILTER (WHERE source_record_version_id IS NOT NULL) AS with_source_version
        FROM extracted_evidence_records
        WHERE organization_id=:org
    """), {"org": organization_id}).mappings().one()
    workflow = db.execute(text("""
        SELECT COUNT(*) FILTER (WHERE review_status IN ('draft','in_review')) AS open_reviews,
               COUNT(*) AS total_reviews
        FROM curation_reviews
        WHERE owner_organization_id=:org
    """), {"org": organization_id}).mappings().one()
    decisions = db.execute(text("""
        SELECT COUNT(*) AS total,
               COUNT(*) FILTER (WHERE evidence_claim_revision_id IS NOT NULL) AS claim_revision_bound
        FROM curation_decisions
        WHERE owner_organization_id=:org
    """), {"org": organization_id}).mappings().one()

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scope": {
            "shared_catalogue": "Shared scientific catalogue counts are global.",
            "organization": str(organization_id),
            "notice": "Coverage measures describe record completeness and workflow traceability, not scientific validity or evidence quality.",
        },
        "shared_catalogue": {
            "peptides": {
                "total": peptide["total"],
                "verified": peptide["verified"],
                "with_primary_source": peptide["with_primary_source"],
                "source_coverage_percent": _percentage(peptide["with_primary_source"], peptide["total"]),
            },
            "sequences": {
                "total": sequences["total"],
                "with_sequence": sequences["with_sequence"],
                "standard_sequence_candidates": sequences["standard_sequence_candidates"],
                "standard_sequence_fingerprinted": sequences["standard_sequence_fingerprinted"],
                "standard_sequence_fingerprint_coverage_percent": _percentage(
                    sequences["standard_sequence_fingerprinted"], sequences["standard_sequence_candidates"]
                ),
            },
            "chemical_forms": {
                "total": forms["total"],
                "verified": forms["verified"],
                "with_source": forms["with_source"],
                "versioned_identity": forms["versioned_identity"],
                "source_coverage_percent": _percentage(forms["with_source"], forms["total"]),
            },
        },
        "organization_evidence": {
            "claims": {
                "total": claims["total"],
                "verified": claims["verified"],
                "with_source": claims["with_source"],
                "with_revision": claims["with_revision"],
                "source_coverage_percent": _percentage(claims["with_source"], claims["total"]),
                "revision_coverage_percent": _percentage(claims["with_revision"], claims["total"]),
            },
            "extractions": {
                "total": extraction["total"],
                "with_source_record": extraction["with_source_record"],
                "with_source_version": extraction["with_source_version"],
                "source_version_coverage_percent": _percentage(
                    extraction["with_source_version"], extraction["total"]
                ),
            },
            "curation": {
                "open_reviews": workflow["open_reviews"],
                "total_reviews": workflow["total_reviews"],
                "decisions": decisions["total"],
                "claim_revision_bound_decisions": decisions["claim_revision_bound"],
                "claim_revision_binding_percent": _percentage(
                    decisions["claim_revision_bound"], decisions["total"]
                ),
            },
        },
        "shared_provenance": {
            "source_records": sources["total"],
            "source_records_with_versions": sources["with_version"],
            "version_coverage_percent": _percentage(sources["with_version"], sources["total"]),
        },
    }


@router.get("/completeness")
def get_data_completeness(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    organization_id = current_user.get("organization_id")
    if not organization_id:
        raise HTTPException(status_code=403, detail="Active organization membership required.")
    membership = db.execute(text("""
        SELECT role FROM organization_memberships
        WHERE organization_id=:org AND user_id=:user_id AND membership_status='active'
    """), {"org": organization_id, "user_id": current_user["id"]}).scalar_one_or_none()
    if membership not in ("organization_admin", "curator", "reviewer"):
        raise HTTPException(status_code=403, detail="Curator or reviewer permissions are required.")
    return build_completeness_report(db, UUID(str(organization_id)))
