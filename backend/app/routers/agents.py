from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from .research import research_assistant_brief

router = APIRouter(prefix="/api/v1/agents", tags=["research agents"])

AGENTS = [
    {"id":"peptide-research","name":"Peptide Research Agent","domain":"literature","description":"Discovers peptide-related publications and clinical research records.","focus":["PubMed","ClinicalTrials.gov"],"workflow":"literature discovery and source triage"},
    {"id":"sequence","name":"Sequence Intelligence Agent","domain":"sequence","description":"Guides sequence analysis and links to Toolkit sequence-property tools.","focus":["sequence composition","molecular properties","modifications"],"workflow":"sequence analysis planning"},
    {"id":"structure","name":"Structure Intelligence Agent","domain":"structure","description":"Finds protein structures and AlphaFold predictions for a supplied protein or accession.","focus":["RCSB PDB","AlphaFold DB","UniProtKB"],"workflow":"structure discovery and confidence interpretation"},
    {"id":"target-interaction","name":"Target Interaction Agent","domain":"interaction","description":"Organizes evidence about peptide–target interactions and distinguishes experiments from computational predictions.","focus":["experimental complexes","docking","interface evidence"],"workflow":"interaction evidence classification"},
    {"id":"analytical","name":"Analytical Methods Agent","domain":"analytical","description":"Helps locate analytical method literature and structure a method-validation review.","focus":["chromatography","mass spectrometry","identity and purity","endotoxin"],"workflow":"analytical method research"},
    {"id":"formulation","name":"Formulation & Stability Agent","domain":"formulation","description":"Organizes published formulation and stability evidence without generating executable recipes.","focus":["formulation literature","stability observations","delivery systems"],"workflow":"formulation evidence review"},
    {"id":"process-development","name":"Process Development Agent","domain":"process","description":"Maps peptide process-development literature and process stages at a non-operational level.","focus":["SPPS","recombinant production","purification","process development"],"workflow":"process literature mapping"},
    {"id":"regulatory-quality","name":"Regulatory & Quality Agent","domain":"regulatory","description":"Helps frame research into regulatory and quality sources; does not determine product compliance.","focus":["regulatory guidance","quality systems","official source verification"],"workflow":"regulatory source checklist"},
    {"id":"scientific-review","name":"Scientific Review Assistant","domain":"review","description":"Builds a source review checklist and highlights evidence gaps for expert assessment.","focus":["study design","evidence class","limitations","conflicting findings"],"workflow":"evidence appraisal planning"},
]


class AgentRunRequest(BaseModel):
    question: str = Field(min_length=8, max_length=500)
    limit: int = Field(default=5, ge=1, le=10)


@router.get("")
def list_agents():
    return {"agents": AGENTS, "count": len(AGENTS),
            "notice": "These are bounded research workflows. They retrieve source records and provide review plans; they do not autonomously validate scientific claims."}


@router.post("/{agent_id}/run")
async def run_agent(agent_id: str, request: AgentRunRequest):
    agent = next((item for item in AGENTS if item["id"] == agent_id), None)
    if agent is None:
        raise HTTPException(status_code=404, detail="Research agent not found.")
    brief = await research_assistant_brief(request.question, request.limit)
    return {
        "agent": agent,
        "question": request.question.strip(),
        "mode": "source_grounded_workflow",
        "retrieval": brief,
        "agent_output": {
            "task": agent["workflow"],
            "focus_areas": agent["focus"],
            "recommended_review": [
                "Confirm that each source refers to the intended peptide, target or material.",
                "Open the original source and verify the methods, model, endpoints and reported results.",
                "Record evidence class, provenance, limitations and any conflicting findings.",
                "Submit only source-backed records to the appropriate Toolkit curator workflow."
            ],
            "interpretation": "This agent has not independently verified the scientific claims. Retrieved records remain unreviewed until qualified human curation."
        }
    }


from typing import Annotated
from uuid import UUID

from fastapi import Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..db import get_db
from .auth import get_current_user


class AgentSessionCreate(BaseModel):
    agent_id: str = Field(min_length=3, max_length=60)
    title: str = Field(min_length=2, max_length=160)
    project_id: UUID | None = None


class AgentMessageCreate(BaseModel):
    message: str = Field(min_length=8, max_length=500)
    limit: int = Field(default=5, ge=1, le=10)
    peptide_id: UUID | None = None


def _session_access(db: Session, session_id: UUID, user: dict):
    row = db.execute(text("""
        SELECT id, organization_id, user_id, agent_id, title, status, created_at, updated_at
        FROM agent_sessions
        WHERE id=:id AND organization_id=:org AND user_id=:user_id
    """), {"id": session_id, "org": user["organization_id"], "user_id": user["id"]}).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Research session not found.")
    return row


def _verified_peptide_context(db: Session, question: str, peptide_id: UUID | None):
    if peptide_id:
        peptide = db.execute(text("""
            SELECT id, preferred_name, peptide_category, description, development_status
            FROM peptides WHERE id=:id AND review_status='verified'
        """), {"id": peptide_id}).mappings().first()
    else:
        term = f"%{question.strip()[:100]}%"
        peptide = db.execute(text("""
            SELECT DISTINCT p.id, p.preferred_name, p.peptide_category, p.description, p.development_status
            FROM peptides p
            LEFT JOIN peptide_aliases a ON a.peptide_id=p.id
            WHERE p.review_status='verified'
              AND (p.preferred_name ILIKE :term OR a.alias ILIKE :term)
            ORDER BY p.preferred_name LIMIT 1
        """), {"term": term}).mappings().first()
    if not peptide:
        return []
    claims = db.execute(text("""
        SELECT id, claim_text, claim_domain, evidence_type, confidence_label, limitations
        FROM evidence_claims
        WHERE peptide_id=:id AND review_status='verified'
        ORDER BY created_at DESC LIMIT 20
    """), {"id": peptide["id"]}).mappings().all()
    return [{
        "peptide": dict(peptide),
        "verified_evidence_claims": [dict(claim) for claim in claims],
        "notice": "Toolkit-curated records marked verified; each claim still requires interpretation within its stated evidence class and limitations."
    }]


@router.get("/sessions")
def list_agent_sessions(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    limit: int = Query(default=30, ge=1, le=100),
):
    rows = db.execute(text("""
        SELECT s.id, s.agent_id, s.title, s.status, s.created_at, s.updated_at,
               count(m.id) AS message_count
        FROM agent_sessions s LEFT JOIN agent_session_messages m ON m.session_id=s.id
        WHERE s.organization_id=:org AND s.user_id=:user_id
        GROUP BY s.id ORDER BY s.updated_at DESC LIMIT :limit
    """), {"org": current_user["organization_id"], "user_id": current_user["id"], "limit": limit}).mappings().all()
    return {"items": [dict(row) for row in rows], "count": len(rows)}


@router.post("/sessions", status_code=201)
def create_agent_session(
    payload: AgentSessionCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    if not any(agent["id"] == payload.agent_id for agent in AGENTS):
        raise HTTPException(status_code=404, detail="Research agent not found.")
    project_id = None
    if payload.project_id:
        project_id = db.execute(text("""
            SELECT p.id FROM research_projects p
            WHERE p.id=:project AND p.organization_id=:org
              AND (p.visibility='organization' OR p.created_by=:user_id
                   OR EXISTS (SELECT 1 FROM project_memberships pm WHERE pm.project_id=p.id AND pm.user_id=:user_id))
        """), {"project": payload.project_id, "org": current_user["organization_id"], "user_id": current_user["id"]}).scalar_one_or_none()
        if not project_id:
            raise HTTPException(status_code=404, detail="Research project not found or inaccessible.")
    row = db.execute(text("""
        INSERT INTO agent_sessions (organization_id, project_id, user_id, agent_id, title)
        VALUES (:org, :project, :user_id, :agent, :title)
        RETURNING id, agent_id, title, status, created_at, updated_at
    """), {"org": current_user["organization_id"], "project": project_id,
           "user_id": current_user["id"], "agent": payload.agent_id, "title": payload.title.strip()}).mappings().one()
    db.commit()
    return dict(row)


@router.get("/sessions/{session_id}")
def get_agent_session(
    session_id: UUID,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    session = _session_access(db, session_id, current_user)
    messages = db.execute(text("""
        SELECT id, sender_role, content, citations, metadata, created_at
        FROM agent_session_messages WHERE session_id=:id ORDER BY created_at, id
    """), {"id": session_id}).mappings().all()
    return {"session": dict(session), "messages": [dict(message) for message in messages]}


@router.post("/sessions/{session_id}/messages", status_code=201)
async def send_agent_message(
    session_id: UUID,
    payload: AgentMessageCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    session = _session_access(db, session_id, current_user)
    if session["status"] != "active":
        raise HTTPException(status_code=409, detail="Archived research sessions cannot receive messages.")
    agent = next(item for item in AGENTS if item["id"] == session["agent_id"])
    context = _verified_peptide_context(db, payload.message, payload.peptide_id)
    if payload.peptide_id and not context:
        raise HTTPException(status_code=404, detail="Verified peptide record not found.")
    brief = await research_assistant_brief(payload.message, payload.limit)
    output = {
        "agent": agent,
        "task": agent["workflow"],
        "retrieval": brief,
        "toolkit_verified_context": context,
        "review_plan": [
            "Confirm entity identity and source relevance.",
            "Check study model, methods, endpoints and limitations in original sources.",
            "Keep clinical, preclinical, in-vitro and computational evidence distinct.",
            "Preserve contradictions and submit proposed records for qualified human review."
        ],
        "interpretation": "Retrieved external records remain unreviewed. Toolkit verified context is included only when an exact verified peptide match is available. No scientific claim is automatically promoted."
    }
    db.execute(text("""
        INSERT INTO agent_session_messages (session_id, sender_role, content, metadata)
        VALUES (:session, 'user', :content, jsonb_build_object('agent_id', :agent))
    """), {"session": session_id, "content": payload.message.strip(), "agent": agent["id"]})
    db.execute(text("""
        INSERT INTO agent_session_messages (session_id, sender_role, content, citations, metadata)
        VALUES (:session, 'agent', :content, CAST(:citations AS jsonb), CAST(:metadata AS jsonb))
    """), {"session": session_id, "content": brief["answer"],
           "citations": json.dumps(brief["citations"]),
           "metadata": json.dumps(output, default=str)})
    db.execute(text("UPDATE agent_sessions SET updated_at=now() WHERE id=:id"), {"id": session_id})
    db.commit()
    return {"session_id": str(session_id), "agent": agent, "response": output}


@router.patch("/sessions/{session_id}/archive")
def archive_agent_session(
    session_id: UUID,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    _session_access(db, session_id, current_user)
    db.execute(text("""
        UPDATE agent_sessions SET status='archived', updated_at=now()
        WHERE id=:id AND organization_id=:org AND user_id=:user_id
    """), {"id": session_id, "org": current_user["organization_id"], "user_id": current_user["id"]})
    db.commit()
    return {"session_id": str(session_id), "status": "archived"}
