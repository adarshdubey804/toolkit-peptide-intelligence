from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..db import get_db

router = APIRouter(prefix="/api/v1/peptides", tags=["peptides"])

PUBLIC_FIELDS = """
id, preferred_name, peptide_category, description, development_status,
intended_use_class, review_status, created_at, updated_at
"""


@router.get("")
def search_peptides(
    q: str | None = Query(default=None, min_length=1, max_length=120),
    category: str | None = Query(default=None, max_length=80),
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0, le=100000),
    db: Session = Depends(get_db),
):
    """Search only curator-verified peptide records."""
    filters = ["review_status = 'verified'"]
    params: dict[str, object] = {"limit": limit, "offset": offset}
    if q:
        filters.append("(preferred_name ILIKE :query OR description ILIKE :query OR EXISTS (SELECT 1 FROM peptide_aliases a WHERE a.peptide_id=peptides.id AND a.alias ILIKE :query))")
        params["query"] = f"%{q.strip()}%"
    if category:
        filters.append("peptide_category = :category")
        params["category"] = category.strip()
    where = " AND ".join(filters)
    rows = db.execute(
        text(f"SELECT {PUBLIC_FIELDS} FROM peptides WHERE {where} ORDER BY preferred_name LIMIT :limit OFFSET :offset"),
        params,
    ).mappings().all()
    total = db.execute(
        text(f"SELECT count(*) FROM peptides WHERE {where}"),
        {k: v for k, v in params.items() if k not in ("limit", "offset")},
    ).scalar_one()
    return {"items": [dict(row) for row in rows], "total": total, "limit": limit, "offset": offset}


@router.get("/{peptide_id}")
def peptide_profile(peptide_id: UUID, db: Session = Depends(get_db)):
    """Return a verified profile and its reviewed, source-linked evidence."""
    peptide = db.execute(
        text(f"SELECT {PUBLIC_FIELDS} FROM peptides WHERE id = :id AND review_status = 'verified'"),
        {"id": peptide_id},
    ).mappings().first()
    if peptide is None:
        raise HTTPException(status_code=404, detail="Verified peptide record not found")

    def rows(sql: str) -> list[dict]:
        return [dict(row) for row in db.execute(text(sql), {"id": peptide_id}).mappings().all()]

    aliases = rows("SELECT alias FROM peptide_aliases WHERE peptide_id=:id ORDER BY alias")
    sequences = rows("SELECT sequence, sequence_type, n_terminus, c_terminus, modifications, stereochemistry_notes FROM peptide_sequences WHERE peptide_id=:id AND review_status='verified'")
    chemistry = rows("SELECT chemical_form, molecular_formula, average_molecular_mass, monoisotopic_mass, canonical_smiles, inchi, inchikey, property_origin, method_or_tool FROM chemical_properties WHERE peptide_id=:id AND review_status='verified'")
    structures = rows("SELECT structure_type, file_format, external_identifier, method_or_prediction_tool FROM structures WHERE peptide_id=:id AND review_status='verified'")
    claims = rows("""
        SELECT DISTINCT c.id, c.claim_text, c.claim_domain, c.evidence_type, c.confidence_label,
               c.limitations, p.doi, p.pmid, p.title AS publication_title, p.url AS publication_url
        FROM evidence_claims c
        LEFT JOIN claim_sources cs ON cs.claim_id=c.id
        LEFT JOIN publications p ON p.id=cs.publication_id
        WHERE c.peptide_id=:id AND c.review_status='verified'
        ORDER BY c.id
    """)
    return {
        "peptide": dict(peptide),
        "aliases": aliases,
        "sequences": sequences,
        "chemical_properties": chemistry,
        "structures": structures,
        "evidence_claims": claims,
    }


@router.get("/{peptide_id}/graph")
def peptide_knowledge_graph(peptide_id: UUID, db: Session = Depends(get_db)):
    """Return a graph of curator-verified relationships for one verified peptide."""
    peptide = db.execute(
        text("SELECT id, preferred_name FROM peptides WHERE id=:id AND review_status='verified'"),
        {"id": peptide_id},
    ).mappings().first()
    if peptide is None:
        raise HTTPException(status_code=404, detail="Verified peptide record not found")

    nodes: dict[str, dict] = {
        str(peptide["id"]): {
            "id": str(peptide["id"]),
            "label": peptide["preferred_name"],
            "type": "peptide",
            "review_status": "verified",
        }
    }
    edges: list[dict] = []

    def add_node(identifier, label, node_type, review_status="verified", metadata=None):
        key = str(identifier)
        nodes.setdefault(key, {
            "id": key,
            "label": str(label or node_type),
            "type": node_type,
            "review_status": review_status,
            "metadata": metadata or {},
        })
        return key

    def add_edge(source, target, relationship, evidence_type="unknown", source_id=None):
        edges.append({
            "source": str(source),
            "target": str(target),
            "relationship": relationship,
            "evidence_type": evidence_type,
            "source_record_id": str(source_id) if source_id else None,
            "review_status": "verified",
        })

    sequences = db.execute(text("""
        SELECT id, sequence, sequence_type FROM peptide_sequences
        WHERE peptide_id=:id AND review_status='verified' ORDER BY id
    """), {"id": peptide_id}).mappings().all()
    for item in sequences:
        node_id = add_node(item["id"], f"{item['sequence_type']}: {item['sequence'][:32]}{'…' if len(item['sequence']) > 32 else ''}", "sequence", metadata={"sequence": item["sequence"], "sequence_type": item["sequence_type"]})
        add_edge(peptide_id, node_id, "has_sequence")

    structures = db.execute(text("""
        SELECT id, structure_type, external_identifier, method_or_prediction_tool
        FROM structures WHERE peptide_id=:id AND review_status='verified' ORDER BY id
    """), {"id": peptide_id}).mappings().all()
    for item in structures:
        label = item["external_identifier"] or item["structure_type"]
        node_id = add_node(item["id"], label, "structure", metadata={"structure_type": item["structure_type"], "method": item["method_or_prediction_tool"]})
        add_edge(peptide_id, node_id, "has_structure")

    targets = db.execute(text("""
        SELECT t.id, t.preferred_name, t.gene_symbol, t.organism,
               e.evidence_type, e.source_id
        FROM peptide_target_evidence e
        JOIN targets t ON t.id=e.target_id
        WHERE e.peptide_id=:id AND e.review_status='verified'
        ORDER BY t.preferred_name
    """), {"id": peptide_id}).mappings().all()
    for item in targets:
        node_id = add_node(item["id"], item["preferred_name"], "target", metadata={"gene_symbol": item["gene_symbol"], "organism": item["organism"]})
        add_edge(peptide_id, node_id, "targets_or_interacts_with", item["evidence_type"], item["source_id"])

    pathways = db.execute(text("""
        SELECT p.id, p.preferred_name, p.database_name, p.organism,
               e.evidence_type, e.source_id
        FROM peptide_pathway_evidence e
        JOIN pathways p ON p.id=e.pathway_id
        WHERE e.peptide_id=:id AND e.review_status='verified'
        ORDER BY p.preferred_name
    """), {"id": peptide_id}).mappings().all()
    for item in pathways:
        node_id = add_node(item["id"], item["preferred_name"], "pathway", metadata={"database": item["database_name"], "organism": item["organism"]})
        add_edge(peptide_id, node_id, "associated_with_pathway", item["evidence_type"], item["source_id"])

    claims = db.execute(text("""
        SELECT c.id, c.claim_text, c.claim_domain, c.evidence_type,
               cs.publication_id, cs.source_record_id,
               p.title AS publication_title, p.url AS publication_url
        FROM evidence_claims c
        LEFT JOIN claim_sources cs ON cs.claim_id=c.id
        LEFT JOIN publications p ON p.id=cs.publication_id
        WHERE c.peptide_id=:id AND c.review_status='verified'
        ORDER BY c.id
    """), {"id": peptide_id}).mappings().all()
    seen_claim_edges = set()
    for item in claims:
        claim_id = add_node(item["id"], item["claim_text"][:90], "evidence_claim", metadata={"claim_text": item["claim_text"], "domain": item["claim_domain"], "evidence_type": item["evidence_type"]})
        add_edge(peptide_id, claim_id, "supported_by_claim", item["evidence_type"], item["source_record_id"])
        if item["publication_id"]:
            publication_id = add_node(item["publication_id"], item["publication_title"], "publication", metadata={"url": item["publication_url"]})
            pair = (claim_id, publication_id)
            if pair not in seen_claim_edges:
                add_edge(claim_id, publication_id, "cited_by")
                seen_claim_edges.add(pair)


    # Verified analytical methods linked through source-backed method references.
    methods = db.execute(text("""
        SELECT DISTINCT m.id, m.method_name, m.method_category, m.validation_status,
               m.method_classification, m.instrument_platform, m.method_version,
               ms.source_record_id
        FROM formulation_profiles fp
        JOIN formulation_stability_observations so ON so.formulation_id=fp.id
        JOIN analytical_methods m ON m.id=so.analytical_method_id
        LEFT JOIN analytical_method_sources ms ON ms.method_id=m.id
        WHERE fp.peptide_id=:id AND fp.review_status='verified'
          AND so.review_status='verified' AND m.review_status='verified'
        ORDER BY m.method_name
    """), {"id": peptide_id}).mappings().all()
    for item in methods:
        method_node=add_node(item["id"],item["method_name"],"analytical_method",
            metadata={"category":item["method_category"],"validation_status":item["validation_status"],
                      "classification":item["method_classification"],"platform":item["instrument_platform"],
                      "version":item["method_version"]})
        add_edge(peptide_id,method_node,"characterized_by_method","unknown",item["source_record_id"])

    formulations=db.execute(text("""
        SELECT id,formulation_name,formulation_type,delivery_system,development_stage
        FROM formulation_profiles WHERE peptide_id=:id AND review_status='verified'
        ORDER BY formulation_name
    """),{"id":peptide_id}).mappings().all()
    for item in formulations:
        formulation_node=add_node(item["id"],item["formulation_name"],"formulation",
            metadata={"formulation_type":item["formulation_type"],"delivery_system":item["delivery_system"],
                      "development_stage":item["development_stage"]})
        add_edge(peptide_id,formulation_node,"has_researched_formulation")
        observations=db.execute(text("""
            SELECT id,study_context,condition_description,duration_description,observed_change,
                   measurement_type,limitations,source_id
            FROM formulation_stability_observations
            WHERE formulation_id=:id AND review_status='verified' ORDER BY created_at
        """),{"id":item["id"]}).mappings().all()
        for obs in observations:
            obs_node=add_node(obs["id"],obs["study_context"],"stability_observation",
                metadata={"condition":obs["condition_description"],"duration":obs["duration_description"],
                          "observed_change":obs["observed_change"],"measurement_type":obs["measurement_type"],
                          "limitations":obs["limitations"]})
            add_edge(formulation_node,obs_node,"has_stability_observation","unknown",obs["source_id"])
            if obs["source_id"]:
                src=db.execute(text("SELECT id,source_name,source_identifier,source_url FROM source_records WHERE id=:id"),{"id":obs["source_id"]}).mappings().first()
                if src:
                    sn=add_node(src["id"],f"{src['source_name']}: {src['source_identifier']}","source",
                        metadata={"url":src["source_url"]})
                    add_edge(obs_node,sn,"supported_by_source")

    processes=db.execute(text("""
        SELECT id,profile_title,process_platform,development_context,process_overview
        FROM process_knowledge_profiles WHERE peptide_id=:id AND review_status='verified'
        ORDER BY profile_title
    """),{"id":peptide_id}).mappings().all()
    for item in processes:
        process_node=add_node(item["id"],item["profile_title"],"process_knowledge",
            metadata={"platform":item["process_platform"],"context":item["development_context"],
                      "overview":item["process_overview"][:500]})
        add_edge(peptide_id,process_node,"has_process_development_literature")
        stages=db.execute(text("""
            SELECT id,stage_name,stage_category,scientific_purpose,source_id
            FROM process_knowledge_stages WHERE profile_id=:id AND review_status='verified'
            ORDER BY stage_name
        """),{"id":item["id"]}).mappings().all()
        for stage in stages:
            stage_node=add_node(stage["id"],stage["stage_name"],"process_stage",
                metadata={"category":stage["stage_category"],"purpose":stage["scientific_purpose"]})
            add_edge(process_node,stage_node,"describes_process_stage","unknown",stage["source_id"])

    interactions=db.execute(text("""
        SELECT a.id,t.id AS target_id,t.preferred_name,t.gene_symbol,a.interaction_method,
               a.evidence_type,a.analysis_tool,a.analysis_version,a.score_name,a.score_value,
               a.score_unit,a.score_interpretation,a.limitations,a.source_id
        FROM molecular_interaction_assessments a JOIN targets t ON t.id=a.target_id
        WHERE a.peptide_id=:id AND a.review_status='verified'
        ORDER BY t.preferred_name
    """),{"id":peptide_id}).mappings().all()
    for item in interactions:
        target_node=add_node(item["target_id"],item["preferred_name"],"target",
            metadata={"gene_symbol":item["gene_symbol"]})
        interaction_node=add_node(item["id"],f"{item['interaction_method']} assessment","interaction_assessment",
            metadata={"method":item["interaction_method"],"tool":item["analysis_tool"],
                      "version":item["analysis_version"],"score_name":item["score_name"],
                      "score_value":float(item["score_value"]) if item["score_value"] is not None else None,
                      "score_unit":item["score_unit"],"score_interpretation":item["score_interpretation"],
                      "limitations":item["limitations"]})
        add_edge(peptide_id,interaction_node,"has_interaction_assessment",item["evidence_type"],item["source_id"])
        add_edge(interaction_node,target_node,"assesses_interaction_with",item["evidence_type"],item["source_id"])

    appraisals=db.execute(text("""
        SELECT ea.id,ea.claim_id,ea.study_design,ea.evidence_level,ea.risk_of_bias,
               ea.replication_status,ea.limitations,ea.appraisal_status
        FROM evidence_appraisals ea JOIN evidence_claims ec ON ec.id=ea.claim_id
        WHERE ec.peptide_id=:id AND ec.review_status='verified'
          AND ea.appraisal_status='accepted'
        ORDER BY ea.created_at DESC
    """),{"id":peptide_id}).mappings().all()
    for item in appraisals:
        appraisal_node=add_node(item["id"],f"Appraisal: {item['study_design']}","evidence_appraisal",
            metadata={"study_design":item["study_design"],"evidence_level":item["evidence_level"],
                      "risk_of_bias":item["risk_of_bias"],"replication":item["replication_status"],
                      "limitations":item["limitations"]})
        add_edge(item["claim_id"],appraisal_node,"has_accepted_appraisal")

    return {
        "peptide_id": str(peptide_id),
        "nodes": list(nodes.values()),
        "edges": edges,
        "counts": {
            "nodes": len(nodes),
            "edges": len(edges),
            "targets": sum(node["type"] == "target" for node in nodes.values()),
            "pathways": sum(node["type"] == "pathway" for node in nodes.values()),
            "publications": sum(node["type"] == "publication" for node in nodes.values()),
        },
        "scope": "Curator-verified relationships only. Missing edges mean no verified relationship is currently recorded.",
    }


@router.get("/{peptide_id}/graph/related")
def related_peptides(
    peptide_id: UUID,
    limit: int = Query(default=25, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Find verified peptides sharing curated targets or pathways with this peptide."""
    peptide = db.execute(text("""
        SELECT id, preferred_name FROM peptides
        WHERE id=:id AND review_status='verified'
    """), {"id": peptide_id}).mappings().first()
    if peptide is None:
        raise HTTPException(status_code=404, detail="Verified peptide record not found")

    rows = db.execute(text("""
        WITH seed_targets AS (
            SELECT target_id FROM peptide_target_evidence
            WHERE peptide_id=:id AND review_status='verified'
        ), seed_pathways AS (
            SELECT pathway_id FROM peptide_pathway_evidence
            WHERE peptide_id=:id AND review_status='verified'
        ), shared AS (
            SELECT p.id, p.preferred_name, p.peptide_category,
                   'shared_target'::text AS connection_type,
                   t.id AS shared_entity_id, t.preferred_name AS shared_entity_name,
                   COUNT(*) OVER (PARTITION BY p.id) AS shared_connection_count
            FROM peptide_target_evidence e
            JOIN seed_targets s ON s.target_id=e.target_id
            JOIN targets t ON t.id=e.target_id
            JOIN peptides p ON p.id=e.peptide_id AND p.review_status='verified'
            WHERE e.review_status='verified' AND p.id<>:id
            UNION ALL
            SELECT p.id, p.preferred_name, p.peptide_category,
                   'shared_pathway'::text AS connection_type,
                   w.id AS shared_entity_id, w.preferred_name AS shared_entity_name,
                   COUNT(*) OVER (PARTITION BY p.id) AS shared_connection_count
            FROM peptide_pathway_evidence e
            JOIN seed_pathways s ON s.pathway_id=e.pathway_id
            JOIN pathways w ON w.id=e.pathway_id
            JOIN peptides p ON p.id=e.peptide_id AND p.review_status='verified'
            WHERE e.review_status='verified' AND p.id<>:id
        )
        SELECT id, preferred_name, peptide_category, connection_type,
               shared_entity_id, shared_entity_name, shared_connection_count
        FROM shared
        ORDER BY shared_connection_count DESC, preferred_name, connection_type
        LIMIT :limit
    """), {"id": peptide_id, "limit": limit}).mappings().all()
    return {
        "peptide_id": str(peptide_id),
        "items": [dict(row) for row in rows],
        "count": len(rows),
        "scope": "Verified peptide records connected through shared curator-verified target or pathway evidence. Shared associations do not establish equivalent mechanism, efficacy or clinical interchangeability.",
    }


@router.get("/compare")
def compare_peptides(
    ids: list[UUID] = Query(min_length=2, max_length=5),
    db: Session = Depends(get_db),
):
    """Compare curator-verified peptide records without inferring equivalence."""
    if len(set(ids)) != len(ids):
        raise HTTPException(status_code=422, detail="Peptide identifiers must be unique.")
    profiles = db.execute(text("""
        SELECT id, preferred_name, peptide_category, development_status,
               intended_use_class, description
        FROM peptides
        WHERE id = ANY(:ids) AND review_status='verified'
    """), {"ids": ids}).mappings().all()
    by_id = {str(row["id"]): dict(row) for row in profiles}
    if len(by_id) != len(ids):
        raise HTTPException(status_code=404, detail="One or more verified peptide records were not found.")
    results = []
    for peptide_id in ids:
        profile = by_id[str(peptide_id)]
        params = {"id": peptide_id}
        sequences = db.execute(text("""
            SELECT sequence,sequence_type,n_terminus,c_terminus,modifications,stereochemistry_notes
            FROM peptide_sequences WHERE peptide_id=:id AND review_status='verified'
        """), params).mappings().all()
        chemistry = db.execute(text("""
            SELECT chemical_form,molecular_formula,average_molecular_mass,monoisotopic_mass,
                   property_origin,method_or_tool
            FROM chemical_properties WHERE peptide_id=:id AND review_status='verified'
        """), params).mappings().all()
        targets = db.execute(text("""
            SELECT t.id,t.preferred_name,t.gene_symbol,t.organism,e.evidence_type
            FROM peptide_target_evidence e JOIN targets t ON t.id=e.target_id
            WHERE e.peptide_id=:id AND e.review_status='verified'
        """), params).mappings().all()
        pathways = db.execute(text("""
            SELECT w.id,w.preferred_name,w.database_name,w.organism,e.evidence_type
            FROM peptide_pathway_evidence e JOIN pathways w ON w.id=e.pathway_id
            WHERE e.peptide_id=:id AND e.review_status='verified'
        """), params).mappings().all()
        claims = db.execute(text("""
            SELECT c.id,c.claim_text,c.claim_domain,c.evidence_type,c.limitations,
                   p.title AS publication_title,p.doi,p.pmid,p.url AS publication_url
            FROM evidence_claims c
            LEFT JOIN claim_sources cs ON cs.claim_id=c.id
            LEFT JOIN publications p ON p.id=cs.publication_id
            WHERE c.peptide_id=:id AND c.review_status='verified'
            ORDER BY c.id
        """), params).mappings().all()
        trials = db.execute(text("""
            SELECT DISTINCT p.id,p.title,p.doi,p.pmid,p.url
            FROM evidence_claims c
            JOIN claim_sources cs ON cs.claim_id=c.id
            JOIN publications p ON p.id=cs.publication_id
            WHERE c.peptide_id=:id AND c.review_status='verified'
              AND (p.pmid IS NOT NULL OR p.doi IS NOT NULL)
            ORDER BY p.title LIMIT 100
        """), params).mappings().all()
        results.append({
            "peptide": profile,
            "sequences": [dict(x) for x in sequences],
            "chemical_properties": [dict(x) for x in chemistry],
            "targets": [dict(x) for x in targets],
            "pathways": [dict(x) for x in pathways],
            "evidence_claims": [dict(x) for x in claims],
            "linked_publications": [dict(x) for x in trials],
        })
    return {
        "items": results,
        "comparison_count": len(results),
        "scope": "Only curator-verified records are included. Missing data means no verified record is currently available, not that the property or relationship is absent. Publication links are not a clinical-trial registry and do not establish efficacy.",
    }
