from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_regulatory_scheduler_binds_org_context_after_each_transaction_boundary():
    source = (ROOT / "backend" / "app" / "services" / "regulatory_scheduler.py").read_text(encoding="utf-8")
    assert "set_config('app.organization_id', :organization_id, true)" in source
    assert source.count('_set_organization_context(db, source["organization_id"])') >= 3
    assert source.index('_set_organization_context(db, source["organization_id"])') < source.index("INSERT INTO regulatory_source_poll_runs")
    assert "reservation commit ended the previous transaction; rebind before tenant-owned writes" in source


def test_regulatory_source_registry_and_scheduler_rls_are_separated():
    scheduler_sql = (ROOT / "database" / "migrations" / "053_regulatory_source_scheduler_row_level_security.sql").read_text(encoding="utf-8")
    registry_sql = (ROOT / "database" / "migrations" / "064_regulatory_source_registry_row_level_security.sql").read_text(encoding="utf-8")
    for table in ("regulatory_source_observations", "regulatory_source_poll_runs"):
        assert f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY" in scheduler_sql
        assert f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY" in scheduler_sql
    for table in ("regulatory_source_registry", "audit_chain_heads"):
        assert f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY" in registry_sql
        assert f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY" in registry_sql
    assert "CREATE ROLE toolkit_regulatory_scheduler NOLOGIN NOBYPASSRLS" in registry_sql
    assert "current_user = 'toolkit_regulatory_scheduler'" in registry_sql
    assert "GRANT UPDATE (last_polled_at, next_poll_at, last_poll_status)" in registry_sql


def test_scheduler_uses_dedicated_database_role_and_fails_closed_without_it():
    db_source = (ROOT / "backend" / "app" / "db.py").read_text(encoding="utf-8")
    worker = (ROOT / "backend" / "app" / "services" / "regulatory_scheduler.py").read_text(encoding="utf-8")
    config = (ROOT / "backend" / "app" / "config.py").read_text(encoding="utf-8")
    assert "scheduler_database_url" in config
    assert "SET ROLE toolkit_regulatory_scheduler" in db_source
    assert "SchedulerSessionLocal" in worker
    assert "SCHEDULER_DATABASE_URL must use" in worker
