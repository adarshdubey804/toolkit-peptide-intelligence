import asyncio
from typing import Annotated
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..config import settings
from ..db import get_db
from ..integrations.clinicaltrials import ClinicalTrialsProvider
from ..integrations.pubmed import PubMedProvider
from ..integrations.rcsb import RCSBProvider
from ..integrations.uniprot import UniProtProvider
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
    """), {"peptide_id": peptide_id}).mappings().first()
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
