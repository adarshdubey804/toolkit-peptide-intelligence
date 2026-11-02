from pathlib import Path


MIGRATIONS = Path(__file__).resolve().parents[2] / "database" / "migrations"


def test_formulation_and_process_rls_migration_covers_all_parent_and_child_tables():
    sql = (MIGRATIONS / "047_formulation_process_row_level_security.sql").read_text(encoding="utf-8")
    for table in (
        "formulation_profiles", "formulation_components", "formulation_stability_observations",
        "formulation_sources", "formulation_review_decisions", "process_knowledge_profiles",
        "process_knowledge_stages", "process_knowledge_sources", "process_knowledge_decisions",
    ):
        assert f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY" in sql
        assert f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY" in sql
    assert "fp.owner_organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid" in sql
    assert "pk.owner_organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid" in sql
    assert "AND review_status='verified'" in sql
