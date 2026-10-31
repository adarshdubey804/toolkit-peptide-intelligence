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
        params["category"] = category
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
def peptide_profile(peptide_id: str, db: Session = Depends(get_db)):
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
        SELECT c.id, c.claim_text, c.claim_domain, c.evidence_type, c.confidence_label,
               c.limitations, p.doi, p.pmid, p.title AS publication_title, p.url AS publication_url
        FROM evidence_claims c
        LEFT JOIN claim_sources cs ON cs.claim_id=c.id
        LEFT JOIN publications p ON p.id=cs.publication_id
        WHERE c.peptide_id=:id AND c.review_status='verified'
        ORDER BY c.created_at DESC
    """)
    return {
        "peptide": dict(peptide),
        "aliases": aliases,
        "sequences": sequences,
        "chemical_properties": chemistry,
        "structures": structures,
        "evidence_claims": claims,
    }
