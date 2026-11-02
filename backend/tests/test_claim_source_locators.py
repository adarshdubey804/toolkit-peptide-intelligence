from pathlib import Path


MIGRATIONS = Path(__file__).resolve().parents[2] / "database" / "migrations"


def test_claim_source_locator_migration_is_source_version_aware_and_append_only():
    sql = (MIGRATIONS / "045_claim_source_citation_locators.sql").read_text(encoding="utf-8")
    assert "claim_source_id UUID NOT NULL REFERENCES claim_sources(id) ON DELETE RESTRICT" in sql
    assert "source_record_version_id UUID REFERENCES source_record_versions(id) ON DELETE RESTRICT" in sql
    assert "enforce_claim_source_locator_version" in sql
    assert "version_source_id IS DISTINCT FROM linked_source_id" in sql
    assert "BEFORE UPDATE OR DELETE ON claim_source_locators" in sql
    assert "quoted_text_hash" in sql
    assert "UNIQUE" not in sql


def test_claim_source_locator_migration_does_not_store_restricted_quoted_full_text():
    sql = (MIGRATIONS / "045_claim_source_citation_locators.sql").read_text(encoding="utf-8")
    assert "quoted_text_hash CHAR(64)" in sql
    assert "quoted full text" in sql
