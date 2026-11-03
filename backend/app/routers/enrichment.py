import asyncio
import json
from datetime import datetime, timezone
from typing import Annotated, Literal
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..config import settings
from ..db import get_db
from ..rate_limit_dependencies import authenticated_write_rate_limit
from ..integrations.clinicaltrials import ClinicalTrialsProvider
from ..integrations.dailymed import DailyMedProvider
from ..integrations.dbaasp import DbaaspProvider
from ..integrations.ema_article57 import EmaArticle57Provider
from ..integrations.fda_drugsfda import FdaDrugsFdaProvider
from ..integrations.fda_purple_book import FdaPurpleBookProvider
from ..integrations.gtopdb import GtoPdbProvider
from ..integrations.dramp import DrampProvider
from ..integrations.health_canada_dpd import HealthCanadaDpdProvider
from ..integrations.pubmed import PubMedProvider
from ..integrations.rcsb import RCSBProvider
from ..integrations.uniprot import UniProtProvider
from ..services.source_persistence import persist_normalized_source_record
from .auth import get_current_user

router = APIRouter(prefix="/api/v1/enrichment", tags=["peptide knowledge enrichment"])
ALLOWED_ROLES = {"organization_admin", "curator", "reviewer", "researcher"}


async def _safe_search(name: str, operation):
    try:
        result = await operation
        items = result.get("items", [])
        return {
            "status": "success",
            "source": result.get("source", name),
            "total": result.get("total"),
            "items": items,
            "coverage_notice": result.get("coverage_notice"),
            "curation_status": result.get("curation_status", "not_reviewed"),
        }
    except Exception as exc:
        return {
            "status": "unavailable",
            "source": name,
            "total": None,
            "items": [],
            "error": "The external source could not be queried. Retry later.",
            "error_type": type(exc).__name__,
        }


@router.get("/peptides/{peptide_id}")
async def discover_peptide_evidence(
    peptide_id: UUID,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Discover source-linked literature and database candidates; never writes or verifies records."""
    organization_id = current_user.get("organization_id")
    if not organization_id or current_user.get("role") not in ALLOWED_ROLES:
        raise HTTPException(status_code=403, detail="An active research, curator or reviewer organization role is required.")

    peptide = db.execute(text("""
        SELECT p.id, p.preferred_name, p.peptide_category, p.review_status
        FROM peptides p
        WHERE p.id = :peptide_id
          AND (p.review_status = 'verified' OR EXISTS (
              SELECT 1 FROM curation_reviews cr
              WHERE cr.entity_type = 'peptide' AND cr.entity_id = p.id
                AND cr.owner_organization_id = :organization_id
          ))
    """), {"peptide_id": peptide_id, "organization_id": organization_id}).mappings().first()
    if peptide is None:
        raise HTTPException(status_code=404, detail="Peptide record not found.")

    aliases = db.execute(text("""
        SELECT alias FROM peptide_aliases WHERE peptide_id = :peptide_id ORDER BY alias LIMIT 12
    """), {"peptide_id": peptide_id}).scalars().all()
    sequences = db.execute(text("""
        SELECT sequence, sequence_type FROM peptide_sequences
        WHERE peptide_id = :peptide_id ORDER BY id LIMIT 5
    """), {"peptide_id": peptide_id}).mappings().all()

    # Exact phrase terms reduce broad lexical noise; aliases are discovery hints, not identity proof.
    terms = list(dict.fromkeys([peptide["preferred_name"], *aliases]))
    query = " OR ".join(f'"{term.replace(chr(34), "")}"' for term in terms[:6])
    providers = {
        "clinicaltrials": ClinicalTrialsProvider().search(query, 10),
        "uniprot": UniProtProvider().search(query, 10),
        "rcsb": RCSBProvider().search(query, 10),
    }
    if settings.ncbi_email:
        providers["pubmed"] = PubMedProvider(settings.ncbi_email, settings.ncbi_api_key).search(query, 10)

    results = await asyncio.gather(*(
        _safe_search(name, operation) for name, operation in providers.items()
    ))
    sources = dict(zip(providers.keys(), results))
    for name in ("pubmed", "clinicaltrials", "uniprot", "rcsb"):
        if name not in sources:
            sources[name] = {
                "status": "not_configured", "source": name, "total": None, "items": [],
                "error": "Configure NCBI_EMAIL to enable PubMed discovery." if name == "pubmed" else None,
            }

    candidates = []
    for source_name, source in sources.items():
        for item in source["items"]:
            identifier = item.get("pmid") or item.get("nct_id") or item.get("accession") or item.get("pdb_id")
            url = item.get("url")
            if not identifier or not url:
                continue
            candidates.append({
                "candidate_id": f"{source_name}:{identifier}",
                "source": source.get("source", source_name),
                "source_identifier": identifier,
                "source_url": url,
                "title": item.get("title") or item.get("protein_name") or item.get("entry_name") or identifier,
                "publication_date": item.get("publication_date"),
                "study_type": item.get("study_type"),
                "overall_status": item.get("overall_status"),
                "organism": item.get("organism"),
                "sequence_length": item.get("sequence_length"),
                "experimental_methods": item.get("experimental_methods"),
                "summary": item.get("abstract") or item.get("brief_summary") or item.get("summary") or item.get("description"),
                "match_basis": "Exact-phrase name or alias search; identity not established.",
                "curation_status": "not_reviewed",
            })

    return {
        "peptide": {
            "id": str(peptide["id"]),
            "preferred_name": peptide["preferred_name"],
            "category": peptide["peptide_category"],
            "existing_review_status": peptide["review_status"],
            "aliases_searched": aliases,
            "sequence_context": [
                {"sequence_type": row["sequence_type"], "length": len(row["sequence"])}
                for row in sequences
            ],
        },
        "retrieval_query": query,
        "sources": sources,
        "candidates": candidates,
        "summary": {
            "sources_available": sum(source["status"] == "success" for source in sources.values()),
            "candidate_count": len(candidates),
        },
        "next_step": "A curator must inspect each original source, confirm entity identity and study relevance, then submit accepted evidence through the existing dossier and curation workflow.",
        "governance": "Read-only discovery. No peptide, sequence, target, pathway, structure or evidence record was created or modified. Name matches do not prove peptide identity; sequence similarity and target associations are not inferred.",
    }


import hashlib
import json
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.exc import IntegrityError

SOURCE_HOSTS = {
    "PubMed": "pubmed.ncbi.nlm.nih.gov",
    "ClinicalTrials.gov": "clinicaltrials.gov",
    "UniProtKB": "www.uniprot.org",
    "RCSB PDB": "www.rcsb.org",
    "PubChem": "pubchem.ncbi.nlm.nih.gov",
    "AlphaFold Protein Structure Database": "alphafold.ebi.ac.uk",
}


class CandidateSubmission(BaseModel):
    source: str = Field(min_length=2, max_length=80)
    source_identifier: str = Field(min_length=1, max_length=120)
    source_url: str = Field(min_length=10, max_length=1000)
    title: str = Field(min_length=2, max_length=1000)
    summary: str | None = Field(default=None, max_length=12000)
    match_basis: str = Field(min_length=5, max_length=500)
    raw_metadata: dict = Field(default_factory=dict)


class CandidateDecision(BaseModel):
    decision: str
    rationale: str = Field(min_length=20, max_length=4000)


class DailyMedMechanismSubmission(BaseModel):
    set_id: str = Field(min_length=36, max_length=36, pattern=r"^[0-9a-fA-F-]{36}$")
    chemical_form_id: UUID | None = None

class GtoPdbMechanismSubmission(BaseModel):
    ligand_id: int = Field(gt=0)
    chemical_form_id: UUID | None = None

class PeptideDiscoveryRequest(BaseModel):
    query: str = Field(min_length=2, max_length=160)
    sources: list[str] = Field(
        default_factory=lambda: ["fda_drugsfda", "fda_purple_book", "ema_article57", "dbaasp", "dailymed", "health_canada_dpd", "clinicaltrials", "pubmed"],
        min_length=1,
        max_length=10,
    )
    limit: int = Field(default=20, ge=1, le=50)


def _candidate_membership(user: dict, db: Session):
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


def _validated_source_url(source: str, url: str) -> str:
    from urllib.parse import urlsplit
    expected_host = SOURCE_HOSTS.get(source)
    parsed = urlsplit(url)
    if not expected_host or parsed.scheme != "https" or parsed.hostname != expected_host or parsed.username or parsed.password:
        raise HTTPException(status_code=422, detail="Source must be one of the supported providers and use its official HTTPS domain.")
    return url


@router.post("/peptides/{peptide_id}/mechanisms/dailymed", status_code=201, dependencies=[Depends(authenticated_write_rate_limit("enrichment_write", settings.enrichment_rate_limit_per_window))])
async def submit_dailymed_mechanism_for_review(
    peptide_id: UUID,
    payload: DailyMedMechanismSubmission,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Create a source-backed, unverified MOA record and queue it for independent curation."""
    organization_id, role = _candidate_membership(current_user, db)
    if role not in {"organization_admin", "curator", "reviewer", "researcher"}:
        raise HTTPException(status_code=403, detail="Researcher, curator or reviewer membership is required.")

    peptide = db.execute(text("""
        SELECT p.id, p.preferred_name
        FROM peptides p
        WHERE p.id=:peptide_id
          AND (p.review_status='verified' OR EXISTS (
              SELECT 1 FROM curation_reviews review
              WHERE review.entity_type='peptide' AND review.entity_id=p.id
                AND review.owner_organization_id=:organization_id
          ))
    """), {"peptide_id": peptide_id, "organization_id": organization_id}).mappings().first()
    if peptide is None:
        raise HTTPException(status_code=404, detail="Peptide dossier not found or not accessible.")
    if payload.chemical_form_id:
        form_exists = db.execute(text("""
            SELECT 1 FROM peptide_chemical_forms
            WHERE id=:form_id AND peptide_id=:peptide_id
        """), {"form_id": payload.chemical_form_id, "peptide_id": peptide_id}).first()
        if not form_exists:
            raise HTTPException(status_code=422, detail="Chemical form does not belong to this peptide dossier.")

    try:
        extracted = await DailyMedProvider().get_mechanism_of_action(payload.set_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Invalid DailyMed SPL Set ID.") from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="DailyMed SPL could not be retrieved.") from exc
    if extracted.get("found") and len((extracted.get("mechanism_text") or "").strip()) < 20:
        raise HTTPException(status_code=422, detail="The extracted MOA section is too short to create a scientific mechanism record.")
    if not extracted.get("found") or not extracted.get("mechanism_text"):
        raise HTTPException(
            status_code=422,
            detail="This DailyMed SPL does not contain an explicit 12.1 Mechanism of Action section. No mechanism record was created.",
        )

    source_payload = {
        "source": "DailyMed",
        "set_id": extracted["set_id"],
        "spl_title": extracted.get("spl_title"),
        "spl_version": extracted.get("spl_version"),
        "mechanism_section": extracted.get("mechanism_text"),
        "section_code": extracted.get("section_code"),
        "section_title": extracted.get("section_title"),
        "retrieved_at": extracted.get("retrieved_at"),
        "curation_status": "not_reviewed",
        "approval_status": extracted.get("approval_status"),
    }
    source = persist_normalized_source_record(
        db,
        source_name="DailyMed",
        source_identifier=extracted["set_id"],
        source_url=extracted["source_url"],
        title=extracted.get("spl_title") or "DailyMed SPL",
        payload=source_payload,
        source_version=str(extracted["spl_version"]) if extracted.get("spl_version") is not None else None,
    )
    source_locator = (
        f"{extracted.get('section_title') or '12.1 Mechanism of Action'} "
        f"(LOINC {extracted.get('section_code')}; SPL version {extracted.get('spl_version') or 'not stated'})"
    )
    existing = db.execute(text("""
        SELECT id, review_status FROM peptide_mechanisms
        WHERE peptide_id=:peptide_id
          AND chemical_form_id IS NOT DISTINCT FROM :chemical_form_id
          AND source_record_id=:source_id
          AND source_locator=:source_locator
        ORDER BY created_at DESC LIMIT 1
    """), {
        "peptide_id": peptide_id, "chemical_form_id": payload.chemical_form_id,
        "source_id": source["source_record_id"], "source_locator": source_locator,
    }).mappings().first()
    if existing:
        review = db.execute(text("""
            SELECT id, review_status FROM curation_reviews
            WHERE entity_type='peptide_mechanism' AND entity_id=:mechanism_id
              AND owner_organization_id=:organization_id
            ORDER BY created_at DESC LIMIT 1
        """), {"mechanism_id": existing["id"], "organization_id": organization_id}).mappings().first()
        db.commit()
        return {
            "mechanism_id": str(existing["id"]),
            "review_id": str(review["id"]) if review else None,
            "review_status": existing["review_status"],
            "already_exists": True,
            "evidence_level": "source_asserted",
            "notice": extracted.get("notice"),
        }

    mechanism = db.execute(text("""
        INSERT INTO peptide_mechanisms (
            peptide_id, chemical_form_id, mechanism_title, mechanism_statement,
            mechanism_class, target_name, evidence_level, evidence_type,
            limitations, source_record_id, source_locator, source_excerpt,
            model_or_method, review_status
        ) VALUES (
            :peptide_id, :chemical_form_id, :title, :statement,
            'unknown', 'Not separately curated from the label text',
            'source_asserted', 'unknown',
            :limitations, :source_id, :source_locator, :excerpt,
            :method, 'in_review'
        )
        RETURNING id, review_status
    """), {
        "peptide_id": peptide_id,
        "chemical_form_id": payload.chemical_form_id,
        "title": "DailyMed label: 12.1 Mechanism of Action",
        "statement": extracted["mechanism_text"],
        "limitations": (
            "Source-reported SPL text only. DailyMed presence is not proof of FDA approval; "
            "the current SPL may differ from the last FDA-approved label. Verify the exact "
            "product, active ingredient, chemical form, indication, jurisdiction and label "
            "version before treating this as a regulatory-label mechanism."
        ),
        "source_id": source["source_record_id"],
        "source_locator": source_locator,
        "excerpt": extracted["mechanism_text"],
        "method": "DailyMed SPL XML extraction; LOINC 43679-0 or explicit 12.1 title fallback; extractor v1",
    }).mappings().one()

    review = db.execute(text("""
        INSERT INTO curation_reviews (
            entity_type, entity_id, source_record_id, review_status, priority,
            submitted_by, owner_organization_id
        ) VALUES (
            'peptide_mechanism', :mechanism_id, :source_id, 'in_review',
            'normal', :submitter, :organization_id
        )
        RETURNING id, review_status
    """), {
        "mechanism_id": mechanism["id"], "source_id": source["source_record_id"],
        "submitter": current_user["id"], "organization_id": organization_id,
    }).mappings().one()

    db.execute(text("""
        INSERT INTO audit_events (actor_user_id, organization_id, action, entity_type, entity_id, event_metadata)
        VALUES (:actor, :org, 'peptide_mechanism_submitted_for_review', 'peptide_mechanism', :mechanism_id,
                jsonb_build_object('peptide_id', :peptide_id, 'source', 'DailyMed',
                                   'set_id', :set_id, 'source_version', :source_version,
                                   'evidence_level', 'source_asserted'))
    """), {
        "actor": current_user["id"], "org": organization_id, "mechanism_id": mechanism["id"],
        "peptide_id": peptide_id, "set_id": extracted["set_id"],
        "source_version": extracted.get("spl_version"),
    })
    db.commit()
    return {
        "mechanism_id": str(mechanism["id"]),
        "review_id": str(review["id"]),
        "review_status": mechanism["review_status"],
        "already_exists": False,
        "evidence_level": "source_asserted",
        "notice": extracted.get("notice"),
    }

@router.post("/peptides/{peptide_id}/mechanisms/gtopdb", status_code=201, dependencies=[Depends(authenticated_write_rate_limit("enrichment_write", settings.enrichment_rate_limit_per_window))])
async def submit_gtopdb_mechanism_for_review(
    peptide_id: UUID,
    payload: GtoPdbMechanismSubmission,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Import source-reported GtoPdb peptide/target interactions into independent review."""
    organization_id, role = _candidate_membership(current_user, db)
    if role not in {"organization_admin", "curator", "reviewer", "researcher"}:
        raise HTTPException(status_code=403, detail="Researcher, curator or reviewer membership is required.")
    if not settings.gtopdb_api_key:
        raise HTTPException(status_code=503, detail="GtoPdb is not configured. Set GTOPDB_API_KEY after registering with the source.")

    peptide = db.execute(text("""
        SELECT p.id, p.preferred_name
        FROM peptides p
        WHERE p.id=:peptide_id
          AND (p.review_status='verified' OR EXISTS (
              SELECT 1 FROM curation_reviews review
              WHERE review.entity_type='peptide' AND review.entity_id=p.id
                AND review.owner_organization_id=:organization_id
          ))
    """), {"peptide_id": peptide_id, "organization_id": organization_id}).mappings().first()
    if peptide is None:
        raise HTTPException(status_code=404, detail="Peptide dossier not found or not accessible.")
    if payload.chemical_form_id:
        form_exists = db.execute(text("""
            SELECT 1 FROM peptide_chemical_forms
            WHERE id=:form_id AND peptide_id=:peptide_id
        """), {"form_id": payload.chemical_form_id, "peptide_id": peptide_id}).first()
        if not form_exists:
            raise HTTPException(status_code=422, detail="Chemical form does not belong to this peptide dossier.")

    try:
        ligand = await GtoPdbProvider().get_peptide_ligand(payload.ligand_id, settings.gtopdb_api_key)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="GtoPdb ligand was not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Invalid GtoPdb ligand request.") from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="GtoPdb could not be reached or returned an upstream error.") from exc

    ligand_type = str(ligand.get("ligand_type") or "")
    if "peptide" not in ligand_type.casefold():
        raise HTTPException(status_code=422, detail="The selected GtoPdb ligand is not explicitly classified as a peptide.")
    interactions = ligand.get("reported_interactions") or []
    if not interactions:
        raise HTTPException(status_code=422, detail="GtoPdb has no target interaction records for this ligand; no mechanism record was created.")

    source_id = ligand.get("source_identifier")
    source_url = ligand.get("source_url")
    if not source_id or not source_url:
        raise HTTPException(status_code=502, detail="GtoPdb did not return a stable ligand identifier and source URL.")
    source_payload = {
        "source": "IUPHAR/BPS Guide to PHARMACOLOGY",
        "source_version": "GtoPdb API",
        "ligand_id": payload.ligand_id,
        "candidate_name": ligand.get("candidate_name"),
        "ligand_type": ligand_type,
        "synonyms": ligand.get("synonyms"),
        "reported_interactions": interactions,
        "reported_targets": ligand.get("reported_target"),
        "reported_mechanism": ligand.get("reported_mechanism"),
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "curation_status": "not_reviewed",
        "license_notice": "GtoPdb database ODbL and content CC BY-SA 4.0; attribution and share-alike terms require review before redistribution.",
    }
    source = persist_normalized_source_record(
        db,
        source_name="IUPHAR/BPS Guide to PHARMACOLOGY",
        source_identifier=str(source_id),
        source_url=source_url,
        title=ligand.get("candidate_name") or f"GtoPdb peptide ligand {source_id}",
        payload=source_payload,
        source_version="GtoPdb API",
    )

    created = []
    existing_ids = []
    for index, interaction in enumerate(interactions, start=1):
        target = (
            interaction.get("targetName")
            or interaction.get("target_name")
            or interaction.get("target")
        )
        if isinstance(target, dict):
            target = target.get("name") or target.get("preferredName")
        action = (
            interaction.get("type")
            or interaction.get("interactionType")
            or interaction.get("action")
        )
        if not action:
            continue
        target_name = str(target).strip() if target else "Target not specified in GtoPdb interaction"
        action_text = str(action).strip()
        statement = (
            f"GtoPdb reports {action_text} for peptide ligand "
            f"{ligand.get('candidate_name') or source_id} at {target_name}."
        )
        source_locator = (
            f"GtoPdb ligand {source_id}; interaction {index}; "
            f"target={target_name}; action={action_text}"
        )
        existing = db.execute(text("""
            SELECT id FROM peptide_mechanisms
            WHERE peptide_id=:peptide_id
              AND chemical_form_id IS NOT DISTINCT FROM :chemical_form_id
              AND source_record_id=:source_id
              AND source_locator=:source_locator
            ORDER BY created_at DESC LIMIT 1
        """), {
            "peptide_id": peptide_id, "chemical_form_id": payload.chemical_form_id,
            "source_id": source["source_record_id"], "source_locator": source_locator,
        }).scalar_one_or_none()
        if existing:
            existing_ids.append(str(existing))
            continue

        mechanism = db.execute(text("""
            INSERT INTO peptide_mechanisms (
                peptide_id, chemical_form_id, mechanism_title, mechanism_statement,
                mechanism_class, target_name, target_action, binding_or_interaction,
                evidence_level, evidence_type, limitations, source_record_id,
                source_locator, source_excerpt, model_or_method, review_status
            ) VALUES (
                :peptide_id, :chemical_form_id, :title, :statement,
                'unknown', :target_name, :target_action, :interaction,
                'source_asserted', 'unknown', :limitations, :source_id,
                :source_locator, :excerpt, :method, 'in_review'
            )
            RETURNING id, review_status
        """), {
            "peptide_id": peptide_id,
            "chemical_form_id": payload.chemical_form_id,
            "title": f"GtoPdb reported interaction: {action_text[:140]}",
            "statement": statement,
            "target_name": target_name,
            "target_action": action_text[:1000],
            "interaction": action_text[:1000],
            "limitations": (
                "This is an interaction assertion reproduced from an expert-curated GtoPdb record, "
                "not a complete mechanistic pathway or proof of clinical effect. Confirm the exact "
                "peptide/chemical-form identity, target subtype, species, assay context, interaction "
                "direction and source record before approving or expanding the mechanism."
            ),
            "source_id": source["source_record_id"],
            "source_locator": source_locator,
            "excerpt": json.dumps(interaction, ensure_ascii=False, default=str)[:4000],
            "method": "IUPHAR/BPS Guide to PHARMACOLOGY API interaction import; source-reported fields only",
        }).mappings().one()

        review = db.execute(text("""
            INSERT INTO curation_reviews (
                entity_type, entity_id, source_record_id, review_status, priority,
                submitted_by, owner_organization_id
            ) VALUES (
                'peptide_mechanism', :mechanism_id, :source_id, 'in_review',
                'normal', :submitter, :organization_id
            )
            RETURNING id, review_status
        """), {
            "mechanism_id": mechanism["id"], "source_id": source["source_record_id"],
            "submitter": current_user["id"], "organization_id": organization_id,
        }).mappings().one()

        db.execute(text("""
            INSERT INTO audit_events (actor_user_id, organization_id, action, entity_type, entity_id, event_metadata)
            VALUES (:actor, :org, 'peptide_mechanism_submitted_for_review', 'peptide_mechanism', :mechanism_id,
                    jsonb_build_object('peptide_id', :peptide_id, 'source', 'GtoPdb',
                                       'ligand_id', :ligand_id, 'interaction_index', :interaction_index,
                                       'evidence_level', 'source_asserted'))
        """), {
            "actor": current_user["id"], "org": organization_id, "mechanism_id": mechanism["id"],
            "peptide_id": peptide_id, "ligand_id": payload.ligand_id, "interaction_index": index,
        })
        created.append({"mechanism_id": str(mechanism["id"]), "review_id": str(review["id"])})

    db.commit()
    return {
        "source": "IUPHAR/BPS Guide to PHARMACOLOGY",
        "ligand_id": payload.ligand_id,
        "created": created,
        "already_exists": existing_ids,
        "created_count": len(created),
        "existing_count": len(existing_ids),
        "review_status": "in_review" if created else "already_submitted",
        "evidence_level": "source_asserted",
        "notice": (
            "GtoPdb target interactions are source-reported pharmacology evidence, not automatically "
            "a complete mechanism of action. Each imported interaction requires independent curator review."
        ),
    }


@router.post("/discover-peptides", status_code=200, dependencies=[Depends(authenticated_write_rate_limit("enrichment_write", settings.enrichment_rate_limit_per_window))])
async def discover_and_persist_peptide_candidates(
    payload: PeptideDiscoveryRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Search official/research sources and persist unverified discovery observations."""
    organization_id, role = _candidate_membership(current_user, db)
    if role not in {"organization_admin", "curator", "reviewer", "researcher"}:
        raise HTTPException(status_code=403, detail="Researcher, curator or reviewer membership is required.")

    allowed_sources = {"fda_drugsfda", "fda_purple_book", "ema_article57", "dbaasp", "dailymed", "health_canada_dpd", "clinicaltrials", "pubmed", "gtopdb", "dramp"}
    selected = list(dict.fromkeys(payload.sources))
    if not selected or not set(selected).issubset(allowed_sources):
        raise HTTPException(status_code=422, detail="Unsupported peptide discovery source.")
    query = payload.query.strip()
    if len(query) < 2:
        raise HTTPException(status_code=422, detail="Search query must contain at least two non-space characters.")

    operations = {}
    if "fda_drugsfda" in selected:
        operations["fda_drugsfda"] = FdaDrugsFdaProvider().search_by_ingredient(
            query, min(payload.limit, 50), settings.openfda_api_key
        )
    if "fda_purple_book" in selected:
        operations["fda_purple_book"] = FdaPurpleBookProvider().search(
            query, min(payload.limit, 100)
        )
    if "gtopdb" in selected and settings.gtopdb_api_key:
        operations["gtopdb"] = GtoPdbProvider().search_peptides(
            query, min(payload.limit, 30), settings.gtopdb_api_key
        )
    if "dramp" in selected:
        operations["dramp"] = DrampProvider().search(query, min(payload.limit, 100))
    if "ema_article57" in selected:
        operations["ema_article57"] = EmaArticle57Provider().search(
            query, min(payload.limit, 50)
        )
    if "dbaasp" in selected:
        operations["dbaasp"] = DbaaspProvider().search(
            query, min(payload.limit, 25)
        )
    if "dailymed" in selected:
        operations["dailymed"] = DailyMedProvider().search_by_name(query, min(payload.limit, 50), 1)
    if "health_canada_dpd" in selected:
        operations["health_canada_dpd"] = HealthCanadaDpdProvider().search_by_ingredient(
            query, min(payload.limit, 50)
        )
    if "clinicaltrials" in selected:
        operations["clinicaltrials"] = ClinicalTrialsProvider().search(query, min(payload.limit, 50))
    if "pubmed" in selected and settings.ncbi_email:
        operations["pubmed"] = PubMedProvider(settings.ncbi_email, settings.ncbi_api_key).search(query, min(payload.limit, 50))

    results = await asyncio.gather(*(
        _safe_search(name, operation) for name, operation in operations.items()
    ))
    source_results = dict(zip(operations.keys(), results))
    if "pubmed" in selected and "pubmed" not in source_results:
        source_results["pubmed"] = {
            "status": "not_configured", "source": "PubMed", "total": None, "items": [],
            "error": "Configure NCBI_EMAIL to enable PubMed discovery.",
        }
    if "gtopdb" in selected and "gtopdb" not in source_results:
        source_results["gtopdb"] = {
            "status": "not_configured", "source": "IUPHAR/BPS Guide to PHARMACOLOGY",
            "total": None, "items": [],
            "error": "Register with GtoPdb and configure GTOPDB_API_KEY to enable this source.",
        }

    dailymed_result = source_results.get("dailymed")
    if dailymed_result and dailymed_result.get("status") == "success":
        semaphore = asyncio.Semaphore(5)
        async def enrich_dailymed_moa(item: dict) -> None:
            set_id = item.get("set_id")
            if not set_id:
                item["mechanism_extraction_status"] = "missing_spl_set_id"
                return
            try:
                async with semaphore:
                    extracted = await DailyMedProvider().get_mechanism_of_action(set_id)
                item["spl_search_result_version"] = item.get("spl_version")
                if extracted.get("spl_version") is not None:
                    item["spl_version"] = extracted.get("spl_version")
                item["mechanism_extraction_status"] = extracted.get("extraction_status")
                item["mechanism_source_url"] = extracted.get("source_url")
                item["mechanism_source_locator"] = (
                    f"Section 12.1 Mechanism of Action (LOINC {extracted.get('section_code')})"
                    if extracted.get("found") else None
                )
                item["mechanism_evidence_level"] = extracted.get("evidence_level", "unknown")
                item["mechanism_extraction_notice"] = extracted.get("notice")
                if extracted.get("found"):
                    item["mechanism_of_action"] = extracted.get("mechanism_text")
            except Exception:
                item["mechanism_extraction_status"] = "source_unavailable_or_unparseable"

        await asyncio.gather(*(
            enrich_dailymed_moa(item) for item in dailymed_result.get("items", [])
        ))

    persisted = []
    failed = []
    try:
        for source_key, result in source_results.items():
            if result.get("status") != "success":
                continue
            source_name = result.get("source") or source_key
            for item in result.get("items", []):
                if source_key == "fda_drugsfda":
                    identifier = item.get("application_number")
                    source_url = item.get("source_url")
                    title = f"FDA application {identifier or 'unknown'}"
                    products = item.get("products") or []
                    ingredient_names = [
                        ingredient.get("name")
                        for product in products
                        for ingredient in (product.get("active_ingredients") or [])
                        if ingredient.get("name")
                    ]
                    candidate_name = next(
                        (name for name in ingredient_names if name.casefold() == query.casefold()),
                        query,
                    )
                    development_status = item.get("approval_state_interpretation")
                elif source_key == "fda_purple_book":
                    identifier = item.get("source_identifier")
                    source_url = item.get("source_url")
                    title = f"FDA Purple Book {item.get('bla_number') or 'BLA unknown'} · {item.get('proper_name') or query}"
                    candidate_name = item.get("proper_name") or query
                    development_status = item.get("licensure") or item.get("marketing_status") or "licensed_biologic_record_observed"
                elif source_key == "gtopdb":
                    identifier = item.get("source_identifier")
                    source_url = item.get("source_url")
                    title = f"GtoPdb ligand {identifier or 'unknown'} · {item.get('candidate_name') or query}"
                    candidate_name = item.get("candidate_name") or query
                    development_status = item.get("ligand_type") or "curated_peptide_ligand_record"
                elif source_key == "dramp":
                    identifier = item.get("source_identifier")
                    source_url = item.get("source_url")
                    title = f"DRAMP {identifier or 'unknown'} · {item.get('candidate_name') or query}"
                    candidate_name = item.get("candidate_name") or identifier or query
                    development_status = None
                elif source_key == "ema_article57":
                    identifier = item.get("source_identifier")
                    source_url = item.get("source_url")
                    title = f"EMA Article 57 product · {item.get('product_name') or query}"
                    candidate_name = item.get("active_substance") or query
                    development_status = item.get("source_status") or "source_status_not_returned"
                elif source_key == "dbaasp":
                    identifier = item.get("source_identifier")
                    source_url = item.get("source_url")
                    title = f"DBAASP peptide {identifier or 'unknown'} · {item.get('candidate_name') or query}"
                    candidate_name = item.get("candidate_name") or query
                    development_status = item.get("synthesis_type") or item.get("complexity") or "experimental_antimicrobial_peptide_record"
                elif source_key == "dailymed":
                    identifier = item.get("set_id")
                    source_url = item.get("source_url")
                    title = item.get("title") or query
                    candidate_name = query
                    development_status = "SPL_label_record_observed"
                elif source_key == "health_canada_dpd":
                    identifier = item.get("drug_code")
                    source_url = item.get("source_url")
                    din = item.get("drug_identification_number")
                    title = f"Health Canada DIN {din or identifier or 'unknown'}"
                    ingredients = item.get("active_ingredients") or []
                    candidate_name = next(
                        (entry.get("ingredient_name") for entry in ingredients
                         if entry.get("ingredient_name") and entry.get("ingredient_name").casefold() == query.casefold()),
                        query,
                    )
                    status_rows = item.get("source_status_records") or []
                    development_status = (
                        status_rows[0].get("status") or status_rows[0].get("status_name")
                        if status_rows else "source_status_not_returned"
                    )
                elif source_key == "clinicaltrials":
                    identifier = item.get("nct_id")
                    source_url = item.get("url")
                    title = item.get("title") or query
                    candidate_name = query
                    development_status = item.get("overall_status")
                else:
                    identifier = item.get("pmid")
                    source_url = item.get("url")
                    title = item.get("title") or query
                    candidate_name = query
                    development_status = "publication_record_observed"

                if not identifier or not source_url:
                    failed.append({"source": source_key, "reason": "missing_stable_source_identifier_or_url"})
                    continue
                if len(json.dumps(item, ensure_ascii=False, default=str)) > 30000:
                    failed.append({"source": source_key, "identifier": str(identifier), "reason": "source_payload_exceeds_30kb"})
                    continue

                snapshot = persist_normalized_source_record(
                    db,
                    source_name=source_name,
                    source_identifier=str(identifier),
                    source_url=source_url,
                    title=title,
                    payload=item,
                    source_version=str(item.get("source_version") or item.get("spl_version")) if (item.get("source_version") is not None or item.get("spl_version") is not None) else None,
                )
                candidate = db.execute(text("""
                    INSERT INTO peptide_discovery_candidates (
                        source_record_id, source_entity_identifier, source_entity_url,
                        candidate_name, candidate_kind, source_development_status,
                        source_jurisdiction_code, reported_sequence, reported_sequence_type,
                        reported_chemical_form, reported_target, reported_mechanism,
                        identity_match_status, candidate_status,
                        last_seen_at, last_observed_at, raw_metadata
                    ) VALUES (
                        :source_id, :identifier, :url, :name, 'unknown', :development_status,
                        :jurisdiction, :sequence, :sequence_type, :chemical_form,
                        :target, :mechanism, 'unresolved', 'discovered', now(), now(),
                        CAST(:metadata AS jsonb)
                    )
                    ON CONFLICT (source_record_id, source_entity_identifier) DO UPDATE SET
                        source_entity_url=EXCLUDED.source_entity_url,
                        source_development_status=COALESCE(EXCLUDED.source_development_status,
                                                           peptide_discovery_candidates.source_development_status),
                        last_seen_at=now(),
                        last_observed_at=now(),
                        raw_metadata=EXCLUDED.raw_metadata,
                        updated_at=now()
                    RETURNING id, candidate_status
                """), {
                    "source_id": snapshot["source_record_id"],
                    "identifier": str(identifier),
                    "url": source_url,
                    "name": candidate_name,
                    "development_status": development_status,
                    "jurisdiction": "US" if source_key in {"fda_drugsfda", "fda_purple_book", "dailymed"} else "CA" if source_key == "health_canada_dpd" else "EEA" if source_key == "ema_article57" else None,
                    "sequence": item.get("sequence"),
                    "sequence_type": item.get("sequence_type"),
                    "chemical_form": item.get("chemical_form"),
                    "target": item.get("target") or item.get("target_name"),
                    "mechanism": item.get("mechanism_of_action") or item.get("mechanism"),
                    "metadata": json.dumps({"search_query": query, "source_record": item}, ensure_ascii=False, default=str),
                }).mappings().one()

                db.execute(text("""
                    INSERT INTO peptide_discovery_observations (
                        candidate_id, source_record_id, source_version, payload, payload_hash
                    ) VALUES (
                        :candidate_id, :source_id, :source_version,
                        CAST(:payload AS jsonb), :payload_hash
                    )
                    ON CONFLICT (candidate_id, payload_hash) DO NOTHING
                """), {
                    "candidate_id": candidate["id"],
                    "source_id": snapshot["source_record_id"],
                    "source_version": str(item.get("source_version") or item.get("spl_version")) if (item.get("source_version") is not None or item.get("spl_version") is not None) else None,
                    "payload": json.dumps(item, ensure_ascii=False, default=str),
                    "payload_hash": snapshot["content_hash"],
                })
                persisted.append({
                    "candidate_id": str(candidate["id"]),
                    "source": source_name,
                    "source_identifier": str(identifier),
                    "candidate_name": candidate_name,
                    "status": candidate["candidate_status"],
                    "identity_match_status": "unresolved",
                })

        db.execute(text("""
            INSERT INTO audit_events (actor_user_id, organization_id, action, entity_type, entity_id, event_metadata)
            VALUES (:actor, :org, 'global_peptide_discovery_run', 'peptide_discovery_candidate', NULL,
                    jsonb_build_object('query', :query, 'sources', CAST(:sources AS jsonb),
                                       'persisted_count', :count, 'failed_count', :failed))
        """), {
            "actor": current_user["id"], "org": organization_id, "query": query,
            "sources": json.dumps(selected), "count": len(persisted), "failed": len(failed),
        })
        db.commit()
    except Exception:
        db.rollback()
        raise

    return {
        "query": query,
        "sources": source_results,
        "persisted_candidates": persisted,
        "persisted_count": len(persisted),
        "skipped_records": failed,
        "governance": (
            "All saved items are source observations with unresolved peptide identity. "
            "Search matches are not proof that the source record describes a peptide, "
            "not a regulatory determination, and not a curated mechanism-of-action claim. "
            "Human review is required before linking to a canonical peptide dossier."
        ),
    }


@router.get("/discovery-candidates")
def list_global_peptide_discovery_candidates(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    q: str | None = None,
    candidate_status: str = "all",
    source_name: str | None = None,
    limit: int = 50,
    offset: int = 0,
):
    """Browse source-backed discovery observations; identity remains unverified."""
    organization_id, role = _candidate_membership(current_user, db)
    if role not in {"organization_admin", "curator", "reviewer", "researcher"}:
        raise HTTPException(status_code=403, detail="Researcher, curator or reviewer membership is required.")
    if candidate_status not in {"all", "discovered", "needs_review", "accepted", "rejected", "duplicate", "superseded"}:
        raise HTTPException(status_code=422, detail="Invalid discovery candidate status.")
    if not 1 <= limit <= 100 or not 0 <= offset <= 100000:
        raise HTTPException(status_code=422, detail="Limit must be 1–100 and offset 0–100000.")
    if q is not None and (len(q.strip()) < 2 or len(q) > 160):
        raise HTTPException(status_code=422, detail="Search text must contain 2–160 characters.")
    if source_name is not None and (len(source_name) < 2 or len(source_name) > 100):
        raise HTTPException(status_code=422, detail="Source name must contain 2–100 characters.")

    filters = ["1=1"]
    params: dict[str, object] = {"limit": limit, "offset": offset}
    if candidate_status != "all":
        filters.append("candidate_status = :status")
        params["status"] = candidate_status
    if q:
        filters.append("(position(lower(:query) in lower(candidate_name)) > 0 OR position(lower(:query) in lower(source_entity_identifier)) > 0)")
        params["query"] = q.strip()
    if source_name:
        filters.append("source_name = :source_name")
        params["source_name"] = source_name
    where = " AND ".join(filters)

    items = db.execute(text(f"""
        SELECT c.id, c.candidate_name, c.candidate_kind, c.source_development_status,
               c.source_jurisdiction_code, c.reported_sequence, c.reported_chemical_form,
               c.reported_target, c.reported_mechanism, c.identity_match_status,
               c.match_confidence, c.match_rationale, c.candidate_status,
               c.canonical_peptide_id, c.first_seen_at, c.last_seen_at, c.last_observed_at,
               s.source_name, s.source_identifier, s.source_url, s.content_hash,
               (SELECT count(*) FROM peptide_discovery_observations o WHERE o.candidate_id=c.id) AS observation_count
        FROM peptide_discovery_candidates c
        JOIN source_records s ON s.id=c.source_record_id
        WHERE {where}
        ORDER BY c.last_seen_at DESC, c.candidate_name
        LIMIT :limit OFFSET :offset
    """), params).mappings().all()
    total = db.execute(text(f"""
        SELECT count(*)
        FROM peptide_discovery_candidates c
        JOIN source_records s ON s.id=c.source_record_id
        WHERE {where}
    """), {k: v for k, v in params.items() if k not in {"limit", "offset"}}).scalar_one()
    return {
        "items": [dict(item) for item in items],
        "total": total,
        "limit": limit,
        "offset": offset,
        "scope": "Source observations only. A candidate is not a verified peptide entity or regulatory status determination.",
    }


class GlobalDiscoveryDecision(BaseModel):
    decision: Literal[
        "accepted_as_existing_peptide", "accepted_as_new_peptide",
        "rejected", "duplicate", "needs_more_evidence",
    ]
    rationale: str = Field(min_length=20, max_length=4000)
    canonical_peptide_id: UUID | None = None

    @field_validator("rationale")
    @classmethod
    def validate_rationale_text(cls, value: str) -> str:
        cleaned = value.strip()
        if len(cleaned) < 20:
            raise ValueError("Rationale must contain at least 20 non-space characters.")
        return cleaned

    @field_validator("canonical_peptide_id")
    @classmethod
    def validate_canonical_link(cls, value, info):
        decision = info.data.get("decision")
        if decision == "accepted_as_existing_peptide" and value is None:
            raise ValueError("Select a verified canonical peptide when accepting as an existing peptide.")
        if decision != "accepted_as_existing_peptide" and value is not None:
            raise ValueError("A canonical peptide link is only valid for accepted_as_existing_peptide.")
        return value


@router.get("/discovery-candidates/{candidate_id}")
def get_global_peptide_discovery_candidate(
    candidate_id: UUID,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Retrieve the source-backed, versioned dossier for one unresolved peptide candidate."""
    organization_id, role = _candidate_membership(current_user, db)
    if role not in {"organization_admin", "curator", "reviewer", "researcher"}:
        raise HTTPException(status_code=403, detail="Researcher, curator or reviewer membership is required.")

    candidate = db.execute(text("""
        SELECT c.*, s.source_name, s.source_identifier, s.source_url,
               s.retrieved_at AS source_retrieved_at, s.license_notes,
               p.preferred_name AS canonical_peptide_name
        FROM peptide_discovery_candidates c
        JOIN source_records s ON s.id=c.source_record_id
        LEFT JOIN peptides p ON p.id=c.canonical_peptide_id
        WHERE c.id=:id
    """), {"id": candidate_id}).mappings().first()
    if candidate is None:
        raise HTTPException(status_code=404, detail="Peptide discovery candidate not found.")

    observations = db.execute(text("""
        SELECT id, source_version, payload_hash, observed_at, payload
        FROM peptide_discovery_observations
        WHERE candidate_id=:id
        ORDER BY observed_at DESC
        LIMIT 10
    """), {"id": candidate_id}).mappings().all()
    decisions = db.execute(text("""
        SELECT d.id, d.decision, d.canonical_peptide_id, d.rationale,
               d.evidence_source_record_ids, d.decided_at,
               reviewer.display_name AS reviewer_name
        FROM peptide_discovery_decisions d
        LEFT JOIN user_profiles reviewer ON reviewer.id=d.reviewer_id
        WHERE d.candidate_id=:id
        ORDER BY d.decided_at DESC
        LIMIT 50
    """), {"id": candidate_id}).mappings().all()

    return {
        "candidate": dict(candidate),
        "observations": [dict(row) for row in observations],
        "decisions": [dict(row) for row in decisions],
        "permissions": {
            "can_review": role in {"organization_admin", "curator", "reviewer"},
            "organization_id": str(organization_id),
        },
        "dossier_notice": (
            "This is a provisional source-observation folder, not a verified canonical peptide dossier. "
            "Source sequence, chemical form, target and mechanism fields remain unreviewed until curated."
        ),
    }


@router.post("/discovery-candidates/{candidate_id}/decisions", status_code=201,
             dependencies=[Depends(authenticated_write_rate_limit("enrichment_write", settings.enrichment_rate_limit_per_window))])
def decide_global_peptide_discovery_candidate(
    candidate_id: UUID,
    payload: GlobalDiscoveryDecision,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    organization_id, role = _candidate_membership(current_user, db)
    if role not in {"organization_admin", "curator", "reviewer"}:
        raise HTTPException(status_code=403, detail="Curator or reviewer permission is required.")

    candidate = db.execute(text("""
        SELECT id, source_record_id, candidate_status
        FROM peptide_discovery_candidates
        WHERE id=:id FOR UPDATE
    """), {"id": candidate_id}).mappings().first()
    if candidate is None:
        raise HTTPException(status_code=404, detail="Peptide discovery candidate not found.")

    decision = payload.decision
    canonical_id = payload.canonical_peptide_id
    if decision == "accepted_as_existing_peptide":
        canonical = db.execute(text("""
            SELECT id FROM peptides WHERE id=:id AND review_status='verified'
        """), {"id": canonical_id}).first()
        if canonical is None:
            raise HTTPException(status_code=422, detail="The linked canonical peptide must be curator-verified.")
        next_status, identity_status = "accepted", "matched"
    elif decision == "accepted_as_new_peptide":
        next_status, identity_status = "accepted", "new_entity"
    elif decision == "rejected":
        next_status, identity_status = "rejected", "rejected"
    elif decision == "duplicate":
        next_status, identity_status = "duplicate", "ambiguous"
    else:
        next_status, identity_status = "needs_review", "unresolved"

    rationale = payload.rationale.strip()
    db.execute(text("""
        INSERT INTO peptide_discovery_decisions
            (candidate_id, decision, canonical_peptide_id, rationale,
             evidence_source_record_ids, reviewer_id)
        VALUES (:candidate, :decision, :canonical, :rationale,
                ARRAY[CAST(:source_id AS uuid)], :reviewer)
    """), {
        "candidate": candidate_id, "decision": decision, "canonical": canonical_id,
        "rationale": rationale, "source_id": candidate["source_record_id"],
        "reviewer": current_user["id"],
    })
    db.execute(text("""
        UPDATE peptide_discovery_candidates
        SET candidate_status=:status, identity_match_status=:identity,
            canonical_peptide_id=:canonical, match_rationale=:rationale,
            updated_at=now()
        WHERE id=:candidate
    """), {
        "status": next_status, "identity": identity_status, "canonical": canonical_id,
        "rationale": rationale, "candidate": candidate_id,
    })
    db.execute(text("""
        INSERT INTO audit_events
            (actor_user_id, organization_id, action, entity_type, entity_id, event_metadata)
        VALUES (:actor, :org, 'global_peptide_discovery_decided',
                'peptide_discovery_candidate', :id,
                jsonb_build_object('decision', :decision, 'candidate_status', :status,
                                   'identity_match_status', :identity,
                                   'canonical_peptide_id', :canonical))
    """), {
        "actor": current_user["id"], "org": organization_id, "id": candidate_id,
        "decision": decision, "status": next_status, "identity": identity_status,
        "canonical": str(canonical_id) if canonical_id else None,
    })
    db.commit()
    return {
        "candidate_id": str(candidate_id),
        "decision": decision,
        "candidate_status": next_status,
        "identity_match_status": identity_status,
        "canonical_peptide_id": str(canonical_id) if canonical_id else None,
        "notice": (
            "Accepted as a new peptide identity. Canonical dossier creation remains a separate governed step."
            if decision == "accepted_as_new_peptide" else "Decision recorded with immutable history."
        ),
    }



@router.post("/peptides/{peptide_id}/candidates", status_code=201, dependencies=[Depends(authenticated_write_rate_limit("enrichment_write", settings.enrichment_rate_limit_per_window))])
def submit_enrichment_candidate(
    peptide_id: UUID,
    payload: CandidateSubmission,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    organization_id, role = _candidate_membership(current_user, db)
    if role not in ALLOWED_ROLES:
        raise HTTPException(status_code=403, detail="Your organization role cannot submit enrichment candidates.")
    if not db.execute(text("SELECT 1 FROM peptides WHERE id=:id"), {"id": peptide_id}).first():
        raise HTTPException(status_code=404, detail="Peptide record not found.")
    source_url = _validated_source_url(payload.source, payload.source_url)
    raw_metadata = payload.raw_metadata
    if len(json.dumps(raw_metadata, ensure_ascii=False)) > 20000:
        raise HTTPException(status_code=413, detail="Candidate metadata exceeds the 20 KB limit.")
    content_hash = hashlib.sha256(json.dumps(raw_metadata, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()
    try:
        row = db.execute(text("""
            INSERT INTO enrichment_candidates
                (organization_id, peptide_id, source_name, source_identifier, source_url,
                 title, summary, match_basis, raw_metadata, content_hash, submitted_by)
            VALUES (:org, :peptide, :source, :identifier, :url, :title, :summary,
                    :basis, CAST(:metadata AS jsonb), :hash, :submitter)
            RETURNING id, candidate_status, created_at
        """), {
            "org": organization_id, "peptide": peptide_id, "source": payload.source,
            "identifier": payload.source_identifier, "url": source_url, "title": payload.title,
            "summary": payload.summary, "basis": payload.match_basis,
            "metadata": json.dumps(raw_metadata), "hash": content_hash,
            "submitter": current_user["id"],
        }).mappings().one()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="This source candidate has already been submitted for this peptide in your organization.") from exc
    db.execute(text("""
        INSERT INTO audit_events (actor_user_id, organization_id, action, entity_type, entity_id, event_metadata)
        VALUES (:actor, :org, 'enrichment_candidate_submitted', 'enrichment_candidate', :id,
                jsonb_build_object('peptide_id', :peptide, 'source', :source, 'source_identifier', :identifier))
    """), {"actor": current_user["id"], "org": organization_id, "id": row["id"],
           "peptide": str(peptide_id), "source": payload.source, "identifier": payload.source_identifier})
    db.commit()
    return {"id": str(row["id"]), "status": row["candidate_status"], "created_at": row["created_at"]}


@router.get("/candidates")
def list_enrichment_candidates(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    candidate_status: str = "pending",
    limit: int = 50,
):
    organization_id, role = _candidate_membership(current_user, db)
    if role not in {"organization_admin", "curator", "reviewer"}:
        raise HTTPException(status_code=403, detail="Curator or reviewer permission is required.")
    if candidate_status not in {"pending", "accepted", "rejected", "duplicate", "needs_review", "all"}:
        raise HTTPException(status_code=422, detail="Invalid candidate status.")
    if limit < 1 or limit > 100:
        raise HTTPException(status_code=422, detail="Limit must be between 1 and 100.")
    rows = db.execute(text("""
        SELECT ec.id, ec.peptide_id, p.preferred_name, ec.source_name, ec.source_identifier,
               ec.source_url, ec.title, ec.summary, ec.match_basis, ec.candidate_status,
               ec.submitted_by, ec.reviewed_by, ec.review_rationale, ec.created_at, ec.reviewed_at
        FROM enrichment_candidates ec
        JOIN peptides p ON p.id=ec.peptide_id
        WHERE ec.organization_id=:org
          AND (:status='all' OR ec.candidate_status::text=:status)
        ORDER BY ec.created_at DESC LIMIT :limit
    """), {"org": organization_id, "status": candidate_status, "limit": limit}).mappings().all()
    return {"items": [dict(row) for row in rows], "count": len(rows)}


@router.post("/candidates/{candidate_id}/decisions", status_code=201, dependencies=[Depends(authenticated_write_rate_limit("enrichment_write"))])
def decide_enrichment_candidate(
    candidate_id: UUID,
    payload: CandidateDecision,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    organization_id, role = _candidate_membership(current_user, db)
    if role not in {"organization_admin", "curator", "reviewer"}:
        raise HTTPException(status_code=403, detail="Curator or reviewer permission is required.")
    if payload.decision not in {"accepted", "rejected", "duplicate", "needs_review"}:
        raise HTTPException(status_code=422, detail="Decision must be accepted, rejected, duplicate or needs_review.")
    candidate = db.execute(text("""
        SELECT * FROM enrichment_candidates
        WHERE id=:id AND organization_id=:org FOR UPDATE
    """), {"id": candidate_id, "org": organization_id}).mappings().first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Enrichment candidate not found in this organization.")
    if str(candidate["submitted_by"]) == current_user["id"]:
        raise HTTPException(status_code=409, detail="The submitter cannot decide their own enrichment candidate.")
    if candidate["candidate_status"] != "pending":
        raise HTTPException(status_code=409, detail="This candidate has already been reviewed.")
    db.execute(text("""
        INSERT INTO enrichment_candidate_decisions
            (candidate_id, organization_id, reviewer_id, decision, rationale)
        VALUES (:candidate, :org, :reviewer, CAST(:decision AS enrichment_candidate_status), :rationale)
    """), {"candidate": candidate_id, "org": organization_id, "reviewer": current_user["id"],
           "decision": payload.decision, "rationale": payload.rationale.strip()})
    db.execute(text("""
        UPDATE enrichment_candidates
        SET candidate_status=CAST(:decision AS enrichment_candidate_status),
            reviewed_by=:reviewer, review_rationale=:rationale, reviewed_at=now(), updated_at=now()
        WHERE id=:candidate
    """), {"decision": payload.decision, "reviewer": current_user["id"],
           "rationale": payload.rationale.strip(), "candidate": candidate_id})
    db.execute(text("""
        INSERT INTO audit_events (actor_user_id, organization_id, action, entity_type, entity_id, event_metadata)
        VALUES (:actor, :org, 'enrichment_candidate_decided', 'enrichment_candidate', :id,
                jsonb_build_object('decision', :decision, 'peptide_id', :peptide, 'source', :source))
    """), {"actor": current_user["id"], "org": organization_id, "id": candidate_id,
           "decision": payload.decision, "peptide": str(candidate["peptide_id"]), "source": candidate["source_name"]})
    db.commit()
    return {"candidate_id": str(candidate_id), "status": payload.decision, "reviewed_at": "recorded"}


from pydantic import field_validator
from ..integrations.pubchem import PubChemProvider
from ..integrations.alphafold import AlphaFoldProvider


class IngestionRunRequest(BaseModel):
    sources: list[str] = Field(default_factory=lambda: ["PubMed", "ClinicalTrials.gov", "UniProtKB", "RCSB PDB"], min_length=1, max_length=6)
    limit_per_source: int = Field(default=10, ge=1, le=20)

    @field_validator("sources")
    @classmethod
    def validate_sources(cls, values):
        allowed = {"PubMed", "ClinicalTrials.gov", "UniProtKB", "RCSB PDB", "PubChem"}
        if len(set(values)) != len(values) or any(value not in allowed for value in values):
            raise ValueError("Choose unique supported sources only. AlphaFold requires a UniProt accession and is not a text-search source.")
        return values


@router.post("/peptides/{peptide_id}/runs", status_code=201, dependencies=[Depends(authenticated_write_rate_limit("enrichment_write"))])
async def run_persistent_enrichment(
    peptide_id: UUID,
    payload: IngestionRunRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Run bounded official-source searches and persist unreviewed candidates for curator review."""
    organization_id, role = _candidate_membership(current_user, db)
    if role not in ALLOWED_ROLES:
        raise HTTPException(status_code=403, detail="Researcher, curator or reviewer role required.")
    peptide = db.execute(text("""
        SELECT p.id, p.preferred_name, p.review_status FROM peptides p
        WHERE p.id=:peptide AND (
          p.review_status='verified' OR EXISTS (
            SELECT 1 FROM curation_reviews cr
            WHERE cr.entity_type='peptide' AND cr.entity_id=p.id
              AND cr.owner_organization_id=:org
          ))
    """), {"peptide": peptide_id, "org": organization_id}).mappings().first()
    if not peptide:
        raise HTTPException(status_code=404, detail="Peptide record not found.")
    aliases = db.execute(text("SELECT alias FROM peptide_aliases WHERE peptide_id=:id ORDER BY alias LIMIT 8"), {"id": peptide_id}).scalars().all()
    terms = list(dict.fromkeys([peptide["preferred_name"], *aliases]))
    query = " OR ".join(f'"{term.replace(chr(34), "")}"' for term in terms[:5])
    run = db.execute(text("""
        INSERT INTO enrichment_ingestion_runs
          (organization_id, peptide_id, started_by, search_query, requested_sources, status)
        VALUES (:org,:peptide,:user,:query,CAST(:sources AS jsonb),'running')
        RETURNING id, started_at
    """), {"org": organization_id, "peptide": peptide_id, "user": current_user["id"],
           "query": query, "sources": json.dumps(payload.sources)}).mappings().one()
    db.commit()

    operations = {}
    for source in payload.sources:
        if source == "PubMed":
            if settings.ncbi_email:
                operations[source] = PubMedProvider(settings.ncbi_email, settings.ncbi_api_key).search(query, payload.limit_per_source)
        elif source == "ClinicalTrials.gov":
            operations[source] = ClinicalTrialsProvider().search(query, payload.limit_per_source)
        elif source == "UniProtKB":
            operations[source] = UniProtProvider().search(query, payload.limit_per_source)
        elif source == "RCSB PDB":
            operations[source] = RCSBProvider().search(query, payload.limit_per_source)
        elif source == "PubChem":
            operations[source] = PubChemProvider().search_by_name(peptide["preferred_name"])

    async def fetch_one(name, operation):
        try:
            result = await operation
            return name, result, None
        except Exception as exc:
            return name, None, type(exc).__name__

    fetched = await asyncio.gather(*(fetch_one(name, operation) for name, operation in operations.items()))
    inserted = 0
    duplicates = 0
    failed_sources = []
    source_counts = {}
    for source, result, error in fetched:
        if error:
            failed_sources.append({"source": source, "error_type": error})
            source_counts[source] = 0
            continue
        items = result.get("items", [])
        source_counts[source] = len(items)
        for item in items:
            identifier = (item.get("pmid") or item.get("nct_id") or item.get("accession")
                          or item.get("pdb_id") or item.get("cid"))
            url = item.get("url")
            if not identifier or not url:
                continue
            title = (item.get("title") or item.get("protein_name") or item.get("entry_name")
                     or item.get("molecular_formula") or str(identifier))[:1000]
            summary = (item.get("abstract") or item.get("brief_summary") or item.get("summary")
                       or item.get("description"))
            metadata = {key: value for key, value in item.items() if key not in {"abstract", "brief_summary", "summary", "description"}}
            metadata["source_query"] = query
            metadata["retrieved_at"] = datetime.now(timezone.utc).isoformat()
            metadata["curation_status"] = "not_reviewed"
            if len(json.dumps(metadata, ensure_ascii=False, default=str)) > 20000:
                metadata = {"truncated": True, "source_identifier": str(identifier), "source_query": query}
            try:
                row = db.execute(text("""
                    INSERT INTO enrichment_candidates
                      (organization_id,peptide_id,source_name,source_identifier,source_url,title,summary,
                       match_basis,raw_metadata,content_hash,submitted_by)
                    VALUES (:org,:peptide,:source,:identifier,:url,:title,:summary,:basis,
                      CAST(:metadata AS jsonb),:hash,:user)
                    ON CONFLICT (organization_id,peptide_id,source_name,source_identifier) DO NOTHING
                    RETURNING id
                """), {"org": organization_id, "peptide": peptide_id, "source": source,
                       "identifier": str(identifier)[:120], "url": url, "title": title,
                       "summary": str(summary)[:12000] if summary else None,
                       "basis": "Automated bounded name/alias search; entity identity and relevance require curator confirmation.",
                       "metadata": json.dumps(metadata, ensure_ascii=False, default=str),
                       "hash": hashlib.sha256(json.dumps(metadata, sort_keys=True, ensure_ascii=False, default=str).encode()).hexdigest(),
                       "user": current_user["id"]}).first()
                if row:
                    inserted += 1
                else:
                    duplicates += 1
            except Exception:
                db.rollback()
                failed_sources.append({"source": source, "error_type": "persistence_error"})
    final_status = "completed_with_errors" if failed_sources else "completed"
    db.execute(text("""
        UPDATE enrichment_ingestion_runs SET status=:status, finished_at=now(),
          candidate_count=:inserted, duplicate_count=:duplicates,
          source_results=CAST(:results AS jsonb), errors=CAST(:errors AS jsonb)
        WHERE id=:id AND organization_id=:org
    """), {"status": final_status, "inserted": inserted, "duplicates": duplicates,
           "results": json.dumps(source_counts), "errors": json.dumps(failed_sources),
           "id": run["id"], "org": organization_id})
    db.execute(text("""
        INSERT INTO audit_events(actor_user_id,organization_id,action,entity_type,entity_id,event_metadata)
        VALUES (:user,:org,'enrichment_ingestion_completed','enrichment_ingestion_run',:id,
          jsonb_build_object('inserted',:inserted,'duplicates',:duplicates,'status',:status))
    """), {"user": current_user["id"], "org": organization_id, "id": run["id"],
           "inserted": inserted, "duplicates": duplicates, "status": final_status})
    db.commit()
    return {"run_id": str(run["id"]), "status": final_status, "search_query": query,
            "sources": source_counts, "new_candidates": inserted, "duplicates_skipped": duplicates,
            "errors": failed_sources, "curation_status": "not_reviewed",
            "note": "Candidates are persisted for curator review only; no canonical peptide, target, structure, trial or claim records are automatically created."}


@router.get("/runs")
def list_ingestion_runs(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    limit: int = 30,
):
    organization_id, role = _candidate_membership(current_user, db)
    if role not in {"organization_admin", "curator", "reviewer", "researcher"}:
        raise HTTPException(status_code=403, detail="Research organization role required.")
    if limit < 1 or limit > 100:
        raise HTTPException(status_code=422, detail="Limit must be between 1 and 100.")
    rows = db.execute(text("""
        SELECT r.id,r.peptide_id,p.preferred_name,r.search_query,r.requested_sources,
               r.status,r.candidate_count,r.duplicate_count,r.source_results,r.errors,
               r.started_at,r.finished_at
        FROM enrichment_ingestion_runs r JOIN peptides p ON p.id=r.peptide_id
        WHERE r.organization_id=:org ORDER BY r.started_at DESC LIMIT :limit
    """), {"org": organization_id, "limit": limit}).mappings().all()
    return {"items": [dict(row) for row in rows], "count": len(rows)}
