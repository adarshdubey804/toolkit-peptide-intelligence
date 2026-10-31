import httpx
from pydantic import BaseModel, Field
from typing import Annotated\nfrom uuid import UUID\nimport json\n\nimport httpx\nfrom fastapi import APIRouter, HTTPException, Query, Depends\nfrom pydantic import BaseModel, Field\nfrom sqlalchemy import text\nfrom sqlalchemy.orm import Session\n\nfrom ..db import get_db\nfrom .auth import get_current_user

from ..config import settings
from ..integrations.alphafold import AlphaFoldProvider
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



@router.get("/alphafold")
async def get_alphafold_prediction(accession: str = Query(min_length=3, max_length=20)):
    """Retrieve AlphaFold DB prediction metadata by UniProt accession; predictions are not curated."""
    try:
        return await AlphaFoldProvider().get_prediction(accession)
    except (httpx.HTTPError, ValueError, KeyError, TypeError) as exc:
        raise HTTPException(status_code=502, detail="AlphaFold DB could not be reached or returned an invalid response.") from exc


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


@router.get("/assistant/brief")
async def research_assistant_brief(
    question: str = Query(min_length=8, max_length=500),
    limit: int = Query(default=5, ge=1, le=10),
):
    """Build a source-grounded research brief from live records; no generative claims."""
    query = question.strip()
    providers = {
        "clinicaltrials": ClinicalTrialsProvider().search(query, limit),
        "uniprot": UniProtProvider().search(query, limit),
        "rcsb": RCSBProvider().search(query, limit),
    }
    if settings.ncbi_email:
        providers["pubmed"] = PubMedProvider(settings.ncbi_email, settings.ncbi_api_key).search(query, limit)

    async def retrieve(name: str, operation):
        try:
            payload = await operation
            return name, payload.get("items", [])
        except Exception:
            return name, []

    retrieved = await asyncio.gather(
        *(retrieve(name, operation) for name, operation in providers.items())
    )
    source_items = dict(retrieved)
    citations = []
    for source_name in ("pubmed", "clinicaltrials", "uniprot", "rcsb"):
        for item in source_items.get(source_name, []):
            identifier = (
                item.get("pmid") or item.get("nct_id") or
                item.get("accession") or item.get("pdb_id")
            )
            url = item.get("url")
            if not identifier or not url:
                continue
            citations.append({
                "citation_id": f"{source_name}:{identifier}",
                "source": item.get("source", source_name),
                "identifier": identifier,
                "title": item.get("title") or item.get("protein_name") or item.get("entry_name") or item.get("pdb_id") or identifier,
                "url": url,
                "publication_date": item.get("publication_date"),
                "study_type": item.get("study_type"),
                "overall_status": item.get("overall_status"),
                "organism": item.get("organism"),
                "experimental_methods": item.get("experimental_methods"),
                "evidence_summary": item.get("brief_summary") or item.get("abstract") or item.get("summary") or item.get("description"),
                "curation_status": "not_reviewed",
            })

    available_sources = [
        name for name, records in source_items.items() if records
    ]
    if citations:
        answer = (
            f"I retrieved {len(citations)} source records relevant to your question from "
            f"{', '.join(available_sources)}. These records are discovery evidence, not a "
            "validated scientific conclusion. Review the original sources and assess their "
            "study models, methods, limitations and consistency before drawing conclusions."
        )
    else:
        answer = (
            "I could not retrieve source records for this question. This is not evidence that "
            "the topic has no published research. Try a shorter peptide name, target, accession, "
            "or a more specific scientific search phrase."
        )

    return {
        "mode": "retrieval_only",
        "question": query,
        "answer": answer,
        "citations": citations,
        "retrieval_summary": {
            "sources_queried": len(providers),
            "sources_with_records": len(available_sources),
            "records_retrieved": len(citations),
            "sources": available_sources,
        },
        "limitations": [
            "No generative language model was used to infer or synthesize scientific conclusions.",
            "External records are unreviewed and may be incomplete, duplicated or irrelevant.",
            "A search result is not evidence of efficacy, safety, causality or regulatory approval.",
            "Absence of retrieved records does not establish absence of evidence.",
        ],
        "next_review_steps": [
            "Open each original source and confirm the record identity.",
            "Classify the evidence as clinical, preclinical, in-vitro or computational.",
            "Extract study design, model, endpoints, results and limitations.",
            "Compare independent sources and preserve conflicting findings.",
        ],
    }



class AssistantSynthesisRequest(BaseModel):
    question: str = Field(min_length=8, max_length=500)
    limit: int = Field(default=5, ge=1, le=10)


@router.post("/assistant/synthesize")
async def synthesize_research_answer(request: AssistantSynthesisRequest):
    """Development-only, source-constrained synthesis. Production access awaits authentication and rate limiting."""
    if not settings.ai_synthesis_enabled or not settings.ai_api_key:
        raise HTTPException(status_code=503, detail="AI synthesis is disabled or not configured.")
    if settings.app_env != "development":
        raise HTTPException(
            status_code=503,
            detail="AI synthesis is not enabled outside development until authenticated access and rate limiting are deployed.",
        )

    from ..services.ai_synthesis import synthesize_with_sources

    try:
        brief = await research_assistant_brief(request.question, request.limit)
        if not brief["citations"]:
            raise HTTPException(status_code=422, detail="No source records were retrieved; synthesis was not attempted.")
        result = await synthesize_with_sources(
            question=request.question,
            citations=brief["citations"],
            api_key=settings.ai_api_key,
            api_base_url=settings.ai_api_base_url,
            model=settings.ai_model,
        )
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(status_code=502, detail="AI synthesis provider failed or returned an invalid response.") from exc
    return result


class EvidenceExtractionRequest(BaseModel):
    question: str = Field(min_length=8, max_length=500)
    limit: int = Field(default=5, ge=1, le=10)


@router.post("/assistant/extract", status_code=201)
async def extract_structured_evidence(
    request: EvidenceExtractionRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Persist machine-extracted evidence fields for human review; never creates verified claims."""
    if not settings.ai_synthesis_enabled or not settings.ai_api_key:
        raise HTTPException(status_code=503, detail="AI extraction is disabled or not configured.")
    if settings.app_env != "development":
        raise HTTPException(status_code=503, detail="AI extraction remains development-only pending production security review.")
    org = current_user.get("organization_id")
    if not org:
        raise HTTPException(status_code=403, detail="Active organization membership required.")
    from ..services.evidence_extraction import extract_evidence
    brief = await research_assistant_brief(request.question, request.limit)
    citations = brief["citations"]
    records = []
    status = "no_sources"
    if citations:
        try:
            records = await extract_evidence(
                question=request.question,
                citations=citations,
                api_key=settings.ai_api_key,
                api_base_url=settings.ai_api_base_url,
                model=settings.ai_model,
            )
            status = "completed"
        except (httpx.HTTPError, ValueError, KeyError, TypeError) as exc:
            raise HTTPException(status_code=502, detail="Evidence extraction provider failed or returned invalid structured data.") from exc
    run = db.execute(text("""
        INSERT INTO evidence_extraction_runs
          (organization_id,requested_by,question,model_name,status,source_count,record_count)
        VALUES(:org,:user,:question,:model,:status,:source_count,:record_count)
        RETURNING id,created_at
    """), {
        "org": org, "user": current_user["id"], "question": request.question.strip(),
        "model": settings.ai_model, "status": status, "source_count": len(citations),
        "record_count": len(records),
    }).mappings().one()
    citation_map = {item["citation_id"]: item for item in citations}
    persisted = []
    for record in records:
        source = citation_map[record["source_citation_id"]]
        row = db.execute(text("""
            INSERT INTO extracted_evidence_records
              (organization_id,run_id,source_citation_id,source_name,source_identifier,
               source_url,source_title,extraction,extraction_model)
            VALUES(:org,:run,:citation,:source,:identifier,:url,:title,CAST(:extraction AS jsonb),:model)
            RETURNING id,review_status,created_at
        """), {
            "org": org, "run": run["id"], "citation": record["source_citation_id"],
            "source": source["source"], "identifier": source["identifier"],
            "url": source["url"], "title": source["title"],
            "extraction": json.dumps(record), "model": settings.ai_model,
        }).mappings().one()
        persisted.append({"id": str(row["id"]), "source_citation_id": record["source_citation_id"],
                          "source_title": source["title"], "extraction": record,
                          "review_status": row["review_status"]})
    db.commit()
    return {
        "run_id": str(run["id"]), "created_at": run["created_at"],
        "status": status, "records": persisted,
        "source_count": len(citations), "record_count": len(persisted),
        "notice": "Machine-extracted fields are unverified research leads. They are not canonical claims, clinical conclusions or validated measurements. Human review against original sources is required.",
    }


@router.get("/assistant/extractions/{run_id}")
def get_structured_extraction_run(
    run_id: UUID,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    org = current_user.get("organization_id")
    if not org:
        raise HTTPException(status_code=403, detail="Active organization membership required.")
    run = db.execute(text("""
        SELECT id,question,model_name,status,source_count,record_count,created_at
        FROM evidence_extraction_runs WHERE id=:id AND organization_id=:org
    """), {"id": run_id, "org": org}).mappings().first()
    if not run:
        raise HTTPException(status_code=404, detail="Evidence extraction run not found.")
    rows = db.execute(text("""
        SELECT id,source_citation_id,source_name,source_identifier,source_url,source_title,
               extraction,review_status,created_at
        FROM extracted_evidence_records
        WHERE run_id=:run AND organization_id=:org ORDER BY created_at,id
    """), {"run": run_id, "org": org}).mappings().all()
    return {"run": dict(run), "records": [dict(row) for row in rows],
            "notice": "Extraction records remain unreviewed and are not promoted to verified evidence claims."}
