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
