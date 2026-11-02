from pathlib import Path


MIGRATIONS = Path(__file__).resolve().parents[2] / "database" / "migrations"


def test_evidence_appraisal_rls_migration_scopes_all_review_tables():
    sql = (MIGRATIONS / "049_evidence_appraisal_row_level_security.sql").read_text(encoding="utf-8")
    for table in (
        "evidence_appraisals", "evidence_appraisal_decisions",
        "publication_duplicate_candidates", "publication_duplicate_decisions",
    ):
        assert f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY" in sql
        assert f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY" in sql
    assert "appraisal.organization_id=evidence_appraisal_decisions.organization_id" in sql
    assert "candidate.organization_id=publication_duplicate_decisions.organization_id" in sql
