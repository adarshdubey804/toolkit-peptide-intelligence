import os
from uuid import uuid4

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
            "peptide_chemical_forms",
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
            "laboratory_capability_claims",
            "laboratory_capability_decisions",
            "analytical_test_catalogue",
            "analytical_test_catalogue_sources",
            "analytical_test_catalogue_decisions",
            "peptide_test_applicability",
            "peptide_test_applicability_decisions",
            "analytical_reference_frameworks",
            "analytical_test_framework_links",
            "api_rate_limit_buckets",
            "api_rate_limit_maintenance",
            "audit_chain_heads",\n            "vendor_material_offerings",\n            "vendor_material_batches",\n            "batch_analytical_test_results",\n            "batch_analytical_test_result_decisions",
        )
        for table_name in required_tables:
            exists = connection.execute(
                text("SELECT to_regclass(:table_name) IS NOT NULL"),
                {"table_name": f"public.{table_name}"},
            ).scalar_one()
            assert exists, f"Expected migration-created table {table_name!r}"


        chemical_form_columns = connection.execute(text("""
            SELECT count(*) FROM information_schema.columns
            WHERE table_schema='public' AND table_name='peptide_chemical_forms'
              AND column_name IN ('stereochemistry','noncanonical_residues','terminal_chemistry',
                                  'cyclization','conjugation','salt_and_counterions',
                                  'identity_fingerprint','canonicalization_version')
        """)).scalar_one()
        assert chemical_form_columns == 8, "Chemical-form identity dimensions and versioning must be present"

        chemical_form_link_columns = connection.execute(text("""
            SELECT count(*) FROM information_schema.columns
            WHERE table_schema='public'
              AND (table_name, column_name) IN (
                ('peptide_method_applicability', 'chemical_form_id'),
                ('peptide_test_applicability', 'chemical_form_id'),
                ('laboratory_capability_claims', 'chemical_form_id')
              )
        """)).scalar_one()
        assert chemical_form_link_columns == 3, "All applicability and capability records need optional chemical-form links"

        chemical_form_parent_triggers = connection.execute(text("""
            SELECT count(*) FROM pg_trigger
            WHERE NOT tgisinternal AND tgname IN (
                'trg_peptide_method_applicability_form_parent',
                'trg_peptide_test_applicability_form_parent',
                'trg_laboratory_capability_form_parent'
            )
        """)).scalar_one()
        assert chemical_form_parent_triggers == 3, "Chemical-form links must enforce parent peptide consistency"

        fingerprint_is_unique = connection.execute(text("""
            SELECT EXISTS (
                SELECT 1 FROM pg_indexes
                WHERE schemaname='public' AND tablename='peptide_chemical_forms'
                  AND indexdef ILIKE '%UNIQUE%' AND indexdef ILIKE '%identity_fingerprint%'
            )
        """)).scalar_one()
        assert not fingerprint_is_unique, "Fingerprints must not imply chemical equivalence before collision validation"

        audit_trigger_exists = connection.execute(text("""
            SELECT EXISTS (
                SELECT 1 FROM pg_trigger
                WHERE tgname = 'trg_audit_events_immutable'
                  AND NOT tgisinternal
            )
        """)).scalar_one()
        assert audit_trigger_exists, "Audit event UPDATE/DELETE protection trigger must exist"

        audit_chain_columns = connection.execute(text("""
            SELECT count(*) FROM information_schema.columns
            WHERE table_schema='public' AND table_name='audit_events'
              AND column_name IN ('chain_scope','chain_sequence','previous_hash','event_hash')
        """)).scalar_one()
        assert audit_chain_columns == 4, "Audit event chain columns must be present"

        applicability_table_exists = connection.execute(text("""
            SELECT to_regclass('public.peptide_test_applicability') IS NOT NULL
        """)).scalar_one()
        assert applicability_table_exists, "Peptide-specific test applicability table must exist"

        seeded_test_count = connection.execute(text("SELECT count(*) FROM analytical_test_catalogue")).scalar_one()
        assert seeded_test_count == 12, "The initial reference catalogue must contain twelve draft test entries"
        draft_test_count = connection.execute(text("SELECT count(*) FROM analytical_test_catalogue WHERE review_status='draft'")).scalar_one()
        assert draft_test_count == 12, "Seeded test definitions must remain explicitly unreviewed"

        site_column_exists = connection.execute(text("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema='public' AND table_name='vendor_services'
                  AND column_name='site_id' AND is_nullable='YES'
            )
        """)).scalar_one()
        assert site_column_exists, "Legacy vendor services must remain nullable while new submissions require a verified site"

        certification_submitter_exists = connection.execute(text("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema='public' AND table_name='vendor_certifications'
                  AND column_name='submitted_by'
            )
        """)).scalar_one()
        assert certification_submitter_exists, "Certification submitter attribution is required for self-review prevention"


        applicability_indexes = connection.execute(text("""
            SELECT count(*) FROM pg_indexes
            WHERE schemaname='public' AND tablename='peptide_test_applicability'
        """)).scalar_one()
        assert applicability_indexes >= 2, "Peptide test applicability needs organization and peptide/test lookup indexes"


@pytest.mark.skipif(
    os.getenv("RUN_POSTGRES_MIGRATION_TESTS") != "1",
    reason="PostgreSQL audit-chain integration test is enabled in CI only.",
)
def test_audit_chain_appends_sequentially_and_rejects_mutation():
    with engine.begin() as connection:
        connection.execute(text("SELECT pg_advisory_xact_lock(731904221067)"))
        apply_development_migrations(connection)
        with connection.begin_nested() as fixture:
            organization_id = connection.execute(text("""
                INSERT INTO organizations (name, organization_type)
                VALUES (:name, 'research_team')
                RETURNING id
            """), {"name": "audit-chain-test-" + str(uuid4())}).scalar_one()

            first = connection.execute(text("""
                INSERT INTO audit_events (organization_id, action, entity_type)
                VALUES (:organization_id, 'audit_test_first', 'test')
                RETURNING id, chain_sequence, previous_hash, event_hash
            """), {"organization_id": organization_id}).mappings().one()
            second = connection.execute(text("""
                INSERT INTO audit_events (organization_id, action, entity_type)
                VALUES (:organization_id, 'audit_test_second', 'test')
                RETURNING id, chain_sequence, previous_hash, event_hash
            """), {"organization_id": organization_id}).mappings().one()

            assert first["chain_sequence"] == 1
            assert first["previous_hash"] == "0" * 64
            assert second["chain_sequence"] == 2
            assert second["previous_hash"] == first["event_hash"]

            head = connection.execute(text("""
                SELECT last_sequence, last_hash
                FROM audit_chain_heads
                WHERE chain_scope = :scope
            """), {"scope": str(organization_id)}).mappings().one()
            assert head["last_sequence"] == 2
            assert head["last_hash"] == second["event_hash"]

            with pytest.raises(Exception):
                with connection.begin_nested():
                    connection.execute(text("""
                        UPDATE audit_events SET action='tampered'
                        WHERE id=:event_id
                    """), {"event_id": first["id"]})

            with pytest.raises(Exception):
                with connection.begin_nested():
                    connection.execute(text("""
                        DELETE FROM audit_events WHERE id=:event_id
                    """), {"event_id": second["id"]})

            fixture.rollback()


        batch_traceability_triggers = connection.execute(text("""
            SELECT count(*) FROM pg_trigger
            WHERE NOT tgisinternal AND tgname IN (
                'trg_vendor_material_offering_scope',
                'trg_vendor_material_batch_scope',
                'trg_batch_test_result_scope',
                'trg_vendor_material_offerings_immutable_evidence',
                'trg_vendor_material_batches_immutable_evidence',
                'trg_batch_analytical_test_results_immutable_evidence',
                'trg_batch_test_result_decisions_no_update'
            )
        """)).scalar_one()
        assert batch_traceability_triggers == 7, "Vendor material, lot and batch-result integrity/audit triggers must exist"

        batch_form_required = connection.execute(text("""
            SELECT is_nullable FROM information_schema.columns
            WHERE table_schema='public' AND table_name='vendor_material_offerings'
              AND column_name='chemical_form_id'
        """)).scalar_one()
        assert batch_form_required == "NO", "A vendor offering must identify its exact chemical form"
