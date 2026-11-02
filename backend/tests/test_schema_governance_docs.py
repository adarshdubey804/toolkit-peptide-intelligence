from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def test_schema_governance_docs_track_current_migration_baseline():
    audit = (REPOSITORY_ROOT / "docs" / "DATABASE_ARCHITECTURE_AUDIT.md").read_text(encoding="utf-8")
    inventory = (REPOSITORY_ROOT / "docs" / "SCHEMA_OWNERSHIP_INVENTORY.md").read_text(encoding="utf-8")

    assert "migrations 001–063" in audit
    assert "migrations 001–063" in inventory
    readiness = (REPOSITORY_ROOT / "docs" / "PRODUCTION_READINESS.md").read_text(encoding="utf-8")
    assert "Migrations 044–063" in inventory
    assert "migrations 044–063" in readiness
    assert "Verification status and publication visibility are independent" in inventory
    assert "direct-ID access" in inventory
    assert "AI outputs as cited, unreviewed candidates" in inventory
