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
