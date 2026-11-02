from pathlib import Path

from app.main import app, MIGRATIONS_DIR


def test_audit_trail_routes_are_authenticated_and_organization_scoped():
    paths = app.openapi()["paths"]
    assert "/api/v1/audit/events" in paths
    assert "get" in paths["/api/v1/audit/events"]
    assert "/api/v1/audit/integrity" in paths
    assert "get" in paths["/api/v1/audit/integrity"]

    for path in ("/api/v1/audit/events", "/api/v1/audit/integrity"):
        operation = paths[path]["get"]
        assert "security" in operation
        assert operation["security"]

    router = (Path(__file__).parents[1] / "app" / "routers" / "audit.py").read_text(encoding="utf-8")
    assert "membership_status = 'active'" in router
    assert 'role != "organization_admin"' in router
    assert "ae.organization_id = :organization_id" in router
    assert "audit_event_sha256" in router
    assert "invalid_events" in router


def test_audit_chain_migration_backfills_and_protects_event_history():
    migration = (MIGRATIONS_DIR / "037_tamper_evident_audit_trail.sql").read_text(encoding="utf-8")
    assert "CREATE EXTENSION IF NOT EXISTS pgcrypto" in migration
    assert "audit_chain_heads" in migration
    assert "audit_event_sha256" in migration
    assert "pg_advisory_xact_lock" in migration
    assert "BEFORE INSERT ON audit_events" in migration
    assert "BEFORE UPDATE OR DELETE ON audit_events" in migration
    assert "UPDATE audit_events" in migration
