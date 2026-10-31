import os

import pytest
from sqlalchemy import text

from app.db import engine
from app.main import MIGRATIONS_DIR, apply_development_migrations


@pytest.mark.skipif(
    os.getenv("RUN_POSTGRES_MIGRATION_TESTS") != "1",
    reason="PostgreSQL migration integration test is enabled in CI only.",
)
def test_full_postgres_migration_chain_is_valid_and_idempotent():
    expected_migrations = sorted(MIGRATIONS_DIR.glob("*.sql"))

    with engine.begin() as connection:
        connection.execute(text("SELECT pg_advisory_xact_lock(731904221067)"))
        apply_development_migrations(connection)
        apply_development_migrations(connection)

        applied_count = connection.execute(
            text("SELECT count(*) FROM toolkit_schema_migrations")
        ).scalar_one()
        assert applied_count == len(expected_migrations)

        required_tables = (
            "peptides",
            "analytical_methods",
            "formulation_profiles",
            "process_knowledge_profiles",
            "regulatory_source_poll_runs",
            "extracted_evidence_field_decisions",
            "peptide_method_applicability",
            "peptide_method_applicability_decisions",
            "vendor_certification_decisions",
            "vendor_service_decisions",
            "vendor_service_evidence_links",
            "vendor_service_evidence_link_decisions",
            "vendor_site_sources",
            "vendor_site_decisions",
        )
        for table_name in required_tables:
            exists = connection.execute(
                text("SELECT to_regclass(:table_name) IS NOT NULL"),
                {"table_name": f"public.{table_name}"},
            ).scalar_one()
            assert exists, f"Expected migration-created table {table_name!r}"

        site_column_exists = connection.execute(text("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema='public' AND table_name='vendor_services'
                  AND column_name='site_id' AND is_nullable='YES'
            )
        """)).scalar_one()
        assert site_column_exists, "Legacy vendor services must remain nullable while new submissions require a verified site"
