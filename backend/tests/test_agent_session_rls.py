from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MIGRATIONS = ROOT / "database" / "migrations"


def test_agent_session_rls_migration_binds_user_and_organization():
    sql = (MIGRATIONS / "051_agent_session_user_row_level_security.sql").read_text(encoding="utf-8")
    for table in ("agent_sessions", "agent_session_messages"):
        assert f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY" in sql
        assert f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY" in sql
    assert "current_setting('app.organization_id', true)" in sql
    assert "current_setting('app.user_id', true)" in sql
    assert "session.user_id=NULLIF(current_setting('app.user_id', true), '')::uuid" in sql
    assert "BEFORE UPDATE OR DELETE ON agent_session_messages" in sql


def test_authenticated_request_sets_user_and_organization_transaction_context():
    source = (ROOT / "app" / "routers" / "auth.py").read_text(encoding="utf-8")
    assert "set_config('app.organization_id'" in source
    assert "set_config('app.user_id'" in source
