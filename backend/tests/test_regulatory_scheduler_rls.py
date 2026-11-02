from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_regulatory_scheduler_binds_org_context_after_each_transaction_boundary():
    source = (ROOT / "backend" / "app" / "services" / "regulatory_scheduler.py").read_text(encoding="utf-8")
    assert "set_config('app.organization_id', :organization_id, true)" in source
    assert source.count('_set_organization_context(db, source["organization_id"])') >= 3
    assert source.index('_set_organization_context(db, source["organization_id"])') < source.index("INSERT INTO regulatory_source_poll_runs")
    assert "reservation commit ended the previous transaction; rebind before tenant-owned writes" in source


def test_regulatory_source_scheduler_rls_migration_scopes_observations_and_poll_runs_only():
    sql = (ROOT / "database" / "migrations" / "053_regulatory_source_scheduler_row_level_security.sql").read_text(encoding="utf-8")
    for table in ("regulatory_source_observations", "regulatory_source_poll_runs"):
        assert f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY" in sql
        assert f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY" in sql
    assert "ALTER TABLE regulatory_source_registry ENABLE ROW LEVEL SECURITY" not in sql
    assert "scheduler control plane" in sql
