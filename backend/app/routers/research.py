import httpx
from fastapi import APIRouter, HTTPException, Query

from ..config import settings
from ..integrations.clinicaltrials import ClinicalTrialsProvider
from ..integrations.pubchem import PubChemProvider
from ..integrations.pubmed import PubMedProvider
from ..integrations.rcsb import RCSBProvider
from ..integrations.uniprot import UniProtProvider

router = APIRouter(prefix="/api/v1/research", tags=["research"])


@router.get("/pubmed")
async def search_pubmed(q: str = Query(min_length=3, max_length=300), limit: int = Query(default=10, ge=1, le=20)):
    """Live PubMed discovery; results are external records, not automatically curated."""
    if not settings.ncbi_email:
        raise HTTPException(status_code=503, detail="PubMed integration is not configured: set NCBI_EMAIL.")
    try:
        return await PubMedProvider(settings.ncbi_email, settings.ncbi_api_key).search(q, limit)
    except (httpx.HTTPError, ValueError, KeyError, TypeError) as exc:
        raise HTTPException(status_code=502, detail="PubMed could not be reached or returned an invalid response.") from exc


@router.get("/clinicaltrials")
async def search_clinical_trials(
    q: str = Query(min_length=3, max_length=300),
    limit: int = Query(default=10, ge=1, le=20),
    page_token: str | None = Query(default=None, max_length=500),
):
    """Read-only ClinicalTrials.gov v2 discovery; results are not automatically curated."""
    try:
        return await ClinicalTrialsProvider().search(q, limit, page_token)
    except (httpx.HTTPError, ValueError, KeyError, TypeError) as exc:
        raise HTTPException(status_code=502, detail="ClinicalTrials.gov could not be reached or returned an invalid response.") from exc


@router.get("/uniprot")
async def search_uniprot(q: str = Query(min_length=3, max_length=200), limit: int = Query(default=10, ge=1, le=20)):
    """Discover UniProtKB protein records; entries are not automatically curated."""
    try:
        return await UniProtProvider().search(q, limit)
    except (httpx.HTTPError, ValueError, KeyError, TypeError) as exc:
        raise HTTPException(status_code=502, detail="UniProt could not be reached or returned an invalid response.") from exc


@router.get("/rcsb")
async def search_rcsb(q: str = Query(min_length=3, max_length=200), limit: int = Query(default=10, ge=1, le=20)):
    """Discover RCSB PDB structure records; entries are not automatically curated."""
    try:
        return await RCSBProvider().search(q, limit)
    except (httpx.HTTPError, ValueError, KeyError, TypeError) as exc:
        raise HTTPException(status_code=502, detail="RCSB PDB could not be reached or returned an invalid response.") from exc


@router.get("/pubchem")
async def search_pubchem(name: str = Query(min_length=2, max_length=200)):
    """Resolve a chemical name to PubChem properties; results are not automatically curated."""
    try:
        return await PubChemProvider().search_by_name(name)
    except (httpx.HTTPError, ValueError, KeyError, TypeError) as exc:
        raise HTTPException(status_code=502, detail="PubChem could not be reached or returned an invalid response.") from exc


import asyncio
from datetime import datetime, timezone


@router.get("/workspace")
async def unified_research_search(
    q: str = Query(min_length=3, max_length=200),
    limit: int = Query(default=5, ge=1, le=10),
):
    """Search supported research sources together; upstream records remain unreviewed."""
    providers = {
        "clinicaltrials": ClinicalTrialsProvider().search(q, limit),
        "uniprot": UniProtProvider().search(q, limit),
        "rcsb": RCSBProvider().search(q, limit),
    }
    if settings.ncbi_email:
        providers["pubmed"] = PubMedProvider(settings.ncbi_email, settings.ncbi_api_key).search(q, limit)

    async def run_provider(name: str, operation):
        try:
            result = await operation
            return name, {
                "status": "success",
                "source": result.get("source", name),
                "total": result.get("total"),
                "items": result.get("items", []),
            }
        except Exception as exc:
            # Keep one upstream failure from suppressing other discovery sources.
            return name, {
                "status": "unavailable",
                "source": name,
                "total": None,
                "items": [],
                "error": "Source unavailable; retry later.",
                "error_type": type(exc).__name__,
            }

    results = await asyncio.gather(
        *(run_provider(name, operation) for name, operation in providers.items())
    )
    sources = dict(results)
    for name in ("pubmed", "clinicaltrials", "uniprot", "rcsb"):
        if name not in sources:
            sources[name] = {
                "status": "not_configured",
                "source": name,
                "total": None,
                "items": [],
                "error": "Configure NCBI_EMAIL to enable PubMed discovery." if name == "pubmed" else None,
            }

    successful = sum(source["status"] == "success" for source in sources.values())
    return {
        "query": q,
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "sources": sources,
        "summary": {
            "sources_available": successful,
            "sources_total": len(sources),
            "records_returned": sum(len(source["items"]) for source in sources.values()),
        },
        "curation_notice": "All external discovery records are unreviewed. Search results are not verified peptide facts and must be checked against their original sources.",
    }
