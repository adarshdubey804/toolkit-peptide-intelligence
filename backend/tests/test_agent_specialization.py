import asyncio

from app.routers import agents


def test_all_research_agents_have_distinct_specialized_plans():
    plans = {
        agent_id: agents.build_agent_search_plan(agent_id, "Review this peptide")
        for agent_id in agents.AGENT_RETRIEVAL_PLANS
    }

    assert len(plans) == 9
    assert len({plan["query"] for plan in plans.values()}) == 9
    assert plans["analytical"]["sources"] == ["pubmed"]
    assert "HPLC" in plans["analytical"]["query"]
    assert plans["structure"]["sources"] == ["rcsb", "uniprot"]
    assert "PDB" in plans["structure"]["query"]
    assert "binding" in plans["target-interaction"]["query"]


def test_agent_run_uses_specialized_query_and_source_scope(monkeypatch):
    captured = {}

    async def fake_research_brief(question, limit, source_scope=None):
        captured["question"] = question
        captured["limit"] = limit
        captured["source_scope"] = source_scope
        return {
            "mode": "retrieval_only",
            "citations": [],
            "retrieval_summary": {"sources_requested": source_scope},
        }

    monkeypatch.setattr(agents, "research_assistant_brief", fake_research_brief)
    request = agents.AgentRunRequest(question="How is peptide purity evaluated?", limit=3)
    response = asyncio.run(agents.run_agent("analytical", request))

    assert captured["limit"] == 3
    assert captured["source_scope"] == ["pubmed"]
    assert "HPLC" in captured["question"]
    assert response["mode"] == "specialized_source_grounded_workflow"
    assert response["retrieval_plan"]["sources_requested"] == ["pubmed"]
    assert len(response["agent_output"]["recommended_review"]) == 4
