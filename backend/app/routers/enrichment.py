import asyncio
from datetime import datetime, timezone
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
          AND (p.review_status = 'verified' OR EXISTS (
              SELECT 1 FROM curation_reviews cr
              JOIN organization_memberships om ON om.user_id = cr.submitted_by
              WHERE cr.entity_type = 'peptide' AND cr.entity_id = p.id
                AND om.organization_id = :organization_id AND om.membership_status = 'active'
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
from pydantic import BaseModel, Field
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


@router.post("/peptides/{peptide_id}/candidates", status_code=201)
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


@router.post("/candidates/{candidate_id}/decisions", status_code=201)
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


@router.post("/peptides/{peptide_id}/runs", status_code=201)
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
            JOIN organization_memberships om ON om.user_id=cr.submitted_by
            WHERE cr.entity_type='peptide' AND cr.entity_id=p.id
              AND om.organization_id=:org AND om.membership_status='active'
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
