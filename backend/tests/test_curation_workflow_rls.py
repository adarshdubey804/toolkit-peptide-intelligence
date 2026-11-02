from pathlib import Path


MIGRATIONS = Path(__file__).resolve().parents[2] / "database" / "migrations"


def test_curation_workflow_rls_migration_scopes_reviews_and_decisions():
    sql = (MIGRATIONS / "050_curation_workflow_row_level_security.sql").read_text(encoding="utf-8")
    for table in ("curation_reviews", "curation_decisions"):
        assert f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY" in sql
        assert f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY" in sql
    assert "review.owner_organization_id=curation_decisions.owner_organization_id" in sql
    assert "owner_organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid" in sql


def test_curation_decisions_are_database_append_only():
    sql = (MIGRATIONS / "050_curation_workflow_row_level_security.sql").read_text(encoding="utf-8")
    assert "BEFORE UPDATE OR DELETE ON curation_decisions" in sql
    assert "Curation decisions are append-only" in sql
