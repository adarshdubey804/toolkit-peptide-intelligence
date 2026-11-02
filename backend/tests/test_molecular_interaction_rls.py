from pathlib import Path


MIGRATIONS = Path(__file__).resolve().parents[2] / "database" / "migrations"


def test_molecular_interaction_rls_migration_scopes_assessments_and_decisions():
    sql = (MIGRATIONS / "048_molecular_interaction_row_level_security.sql").read_text(encoding="utf-8")
    assert "ALTER TABLE molecular_interaction_assessments ENABLE ROW LEVEL SECURITY" in sql
    assert "ALTER TABLE molecular_interaction_assessments FORCE ROW LEVEL SECURITY" in sql
    assert "ALTER TABLE molecular_interaction_decisions ENABLE ROW LEVEL SECURITY" in sql
    assert "ALTER TABLE molecular_interaction_decisions FORCE ROW LEVEL SECURITY" in sql
    assert "visibility_scope='public' AND review_status='verified'" in sql
    assert "assessment.owner_organization_id=organization_id" in sql
    assert "molecular_interaction_decisions_insert_scope" in sql
