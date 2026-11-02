from pathlib import Path


MIGRATIONS = Path(__file__).resolve().parents[2] / "database" / "migrations"


def test_regulatory_guidance_rls_migration_scopes_parent_versions_and_decisions():
    sql = (MIGRATIONS / "052_regulatory_guidance_row_level_security.sql").read_text(encoding="utf-8")
    tables = (
        "regulatory_guidance_records", "regulatory_guidance_decisions",
        "regulatory_guidance_versions", "regulatory_change_events",
        "regulatory_change_decisions",
    )
    for table in tables:
        assert f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY" in sql
        assert f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY" in sql
    assert "guidance.review_status='verified'" in sql
    assert "regulatory_guidance_versions.review_status='accepted'" in sql
    assert "guidance.organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid" in sql
    assert "guidance.organization_id=regulatory_guidance_decisions.organization_id" in sql
    assert "guidance.organization_id=regulatory_change_decisions.organization_id" in sql
