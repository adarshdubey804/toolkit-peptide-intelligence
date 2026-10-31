import httpx
from fastapi import APIRouter, HTTPException, Query

from ..config import settings
from ..integrations.clinicaltrials import ClinicalTrialsProvider
from ..integrations.pubmed import PubMedProvider

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
