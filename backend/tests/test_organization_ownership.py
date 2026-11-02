from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
ROUTERS = BACKEND_ROOT / "app" / "routers"


def _source(name: str) -> str:
    return (ROUTERS / name).read_text(encoding="utf-8")


def test_curation_reviews_are_scoped_by_stored_owner_not_submitter_membership():
    source = _source("curation.py")
    assert "cr.organization_id = :organization_id" in source
    assert "cr.organization_id = :org" in source
    assert "JOIN organization_memberships om ON om.user_id = cr.submitted_by" not in source
    assert "cr.submitted_by IN (" not in source
    assert "(organization_id, entity_type, entity_id, source_record_id" in source
    assert "(review_id, organization_id, decision, rationale" in source


def test_dossier_and_enrichment_access_use_review_owner_organization():
    dossiers = _source("dossiers.py")
    enrichment = _source("enrichment.py")
    evidence = _source("evidence_intelligence.py")
    assert "(organization_id, entity_type, entity_id, source_record_id" in dossiers
    assert "cr.organization_id = :organization_id" in enrichment
    assert "cr.organization_id=:org" in enrichment
    assert "JOIN organization_memberships om ON om.user_id=cr.submitted_by" not in enrichment
    assert "cr.organization_id=:org" in evidence
    assert "JOIN organization_memberships om ON om.user_id=cr.submitted_by" not in evidence


def test_scientific_submission_tables_store_and_filter_owner_organization():
    expectations = {
        "analytical_methods.py": ("organization_id, method_name", "am.organization_id=:org"),
        "formulations.py": ("organization_id, peptide_id, formulation_name", "fp.organization_id=:org"),
        "process_knowledge.py": ("organization_id, peptide_id, profile_title", "pk.organization_id=:org"),
        "interactions.py": ("organization_id, peptide_id, target_id", "a.organization_id=:org"),
    }
    for filename, (insert_marker, filter_marker) in expectations.items():
        source = _source(filename)
        assert insert_marker in source, filename
        assert filter_marker in source, filename
        assert "JOIN organization_memberships om ON om.user_id=" not in source, filename


def test_organization_ownership_migration_uses_audit_provenance_and_conservative_fallback():
    migration = (
        BACKEND_ROOT.parent / "database" / "migrations" / "038_explicit_organization_ownership.sql"
    ).read_text(encoding="utf-8")
    assert "FROM audit_events ae" in migration
    assert "HAVING count(DISTINCT organization_id) = 1" in migration
    assert "organization_id UUID REFERENCES organizations(id)" in migration
