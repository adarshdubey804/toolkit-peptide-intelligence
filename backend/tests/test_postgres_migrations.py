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
            "audit_chain_heads",
            "vendor_material_offerings",
            "vendor_material_batches",
            "batch_analytical_test_results",
            "batch_analytical_test_result_decisions",
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


        owner_columns = connection.execute(text("""
            SELECT table_name, column_name
            FROM information_schema.columns
            WHERE table_schema='public'
              AND (table_name, column_name) IN (
                ('curation_reviews','owner_organization_id'),
                ('curation_decisions','owner_organization_id'),
                ('analytical_methods','owner_organization_id'),
                ('formulation_profiles','owner_organization_id'),
                ('process_knowledge_profiles','owner_organization_id'),
                ('molecular_interaction_assessments','owner_organization_id')
              )
        """)).fetchall()
        assert len(owner_columns) == 6, "All standalone organization submissions and review decisions must retain explicit owner IDs"

        interaction_visibility = connection.execute(text("""
            SELECT count(*) FROM information_schema.columns
            WHERE table_schema='public' AND table_name='molecular_interaction_assessments'
              AND column_name='visibility_scope'
        """)).scalar_one()
        assert interaction_visibility == 1, "Interaction submissions need explicit public/organization/restricted visibility"

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

        batch_traceability_triggers = connection.execute(text("""
            SELECT count(*) FROM pg_trigger
            WHERE NOT tgisinternal AND tgname IN (
                'trg_vendor_material_offering_scope',
                'trg_vendor_material_batch_scope',
                'trg_batch_test_result_scope',
                'trg_batch_test_result_decision_scope',
                'trg_vendor_material_offerings_immutable_evidence',
                'trg_vendor_material_batches_immutable_evidence',
                'trg_batch_analytical_test_results_immutable_evidence',
                'trg_batch_test_result_decisions_no_update'
            )
        """)).scalar_one()
        assert batch_traceability_triggers == 8, "Vendor material, lot and batch-result integrity/audit triggers must exist"

        batch_form_required = connection.execute(text("""
            SELECT is_nullable FROM information_schema.columns
            WHERE table_schema='public' AND table_name='vendor_material_offerings'
              AND column_name='chemical_form_id'
        """)).scalar_one()
        assert batch_form_required == "NO", "A vendor offering must identify its exact chemical form"

        rls_tables = (
            "vendor_material_offerings",
            "vendor_material_batches",
            "batch_analytical_test_results",
            "batch_analytical_test_result_decisions",
        )
        for table_name in rls_tables:
            rls_state = connection.execute(text("""
                SELECT relrowsecurity, relforcerowsecurity
                FROM pg_class WHERE oid=to_regclass(:table_name)
            """), {"table_name": f"public.{table_name}"}).one()
            assert tuple(rls_state) == (True, True), f"RLS and FORCE RLS must be enabled for {table_name}"

        required_policies = connection.execute(text("""
            SELECT count(*) FROM pg_policies
            WHERE schemaname='public' AND policyname IN (
                'vendor_material_offerings_select_scope',
                'vendor_material_offerings_insert_scope',
                'vendor_material_offerings_update_scope',
                'vendor_material_batches_select_scope',
                'vendor_material_batches_insert_scope',
                'vendor_material_batches_update_scope',
                'batch_analytical_test_results_select_scope',
                'batch_analytical_test_results_insert_scope',
                'batch_analytical_test_results_update_scope',
                'batch_analytical_test_result_decisions_select_scope',
                'batch_analytical_test_result_decisions_insert_scope'
            )
        """)).scalar_one()
        assert required_policies == 11, "All vendor material traceability access paths need explicit RLS policies"

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

@pytest.mark.skipif(
    os.getenv("RUN_POSTGRES_MIGRATION_TESTS") != "1",
    reason="PostgreSQL transaction-local tenant context test is enabled in CI only.",
)
def test_organization_context_is_transaction_local_and_clears_on_commit():
    organization_id = str(uuid4())
    with engine.connect() as connection:
        with connection.begin():
            bound = connection.execute(text("""
                SELECT set_config('app.organization_id', :organization_id, true)
            """), {"organization_id": organization_id}).scalar_one()
            assert bound == organization_id
            current = connection.execute(text(
                "SELECT current_setting('app.organization_id', true)"
            )).scalar_one()
            assert current == organization_id

        with connection.begin():
            current = connection.execute(text(
                "SELECT current_setting('app.organization_id', true)"
            )).scalar_one_or_none()
            assert current in (None, ""), "Transaction-local organization context must not leak through the connection pool"



@pytest.mark.skipif(
    os.getenv("RUN_POSTGRES_MIGRATION_TESTS") != "1",
    reason="PostgreSQL row-level-security integration test is enabled in CI only.",
)
def test_vendor_material_offering_rls_enforces_organization_and_public_scope():
    with engine.begin() as connection:
        connection.execute(text("SELECT pg_advisory_xact_lock(731904221067)"))
        apply_development_migrations(connection)

        organization_a = connection.execute(text("""
            INSERT INTO organizations (name, organization_type)
            VALUES (:name, 'research_team') RETURNING id
        """), {"name": "rls-org-a-" + str(uuid4())}).scalar_one()
        organization_b = connection.execute(text("""
            INSERT INTO organizations (name, organization_type)
            VALUES (:name, 'research_team') RETURNING id
        """), {"name": "rls-org-b-" + str(uuid4())}).scalar_one()
        submitter_a = connection.execute(text("""
            INSERT INTO user_profiles (display_name, role)
            VALUES ('RLS submitter A', 'researcher') RETURNING id
        """)).scalar_one()
        submitter_b = connection.execute(text("""
            INSERT INTO user_profiles (display_name, role)
            VALUES ('RLS submitter B', 'researcher') RETURNING id
        """)).scalar_one()

        vendor_a = connection.execute(text("""
            INSERT INTO vendors (
                legal_name, vendor_type, organization_id, review_status,
                verification_status, submitted_by
            ) VALUES (:name, 'other', :org, 'verified', 'verified', :submitter)
            RETURNING id
        """), {"name": "RLS vendor A " + str(uuid4()), "org": organization_a,
               "submitter": submitter_a}).scalar_one()
        vendor_b = connection.execute(text("""
            INSERT INTO vendors (
                legal_name, vendor_type, organization_id, review_status,
                verification_status, submitted_by
            ) VALUES (:name, 'other', :org, 'verified', 'verified', :submitter)
            RETURNING id
        """), {"name": "RLS vendor B " + str(uuid4()), "org": organization_b,
               "submitter": submitter_b}).scalar_one()

        peptide_a = connection.execute(text("""
            INSERT INTO peptides (preferred_name, review_status)
            VALUES (:name, 'verified') RETURNING id
        """), {"name": "RLS peptide A " + str(uuid4())}).scalar_one()
        peptide_b = connection.execute(text("""
            INSERT INTO peptides (preferred_name, review_status)
            VALUES (:name, 'verified') RETURNING id
        """), {"name": "RLS peptide B " + str(uuid4())}).scalar_one()
        form_a = connection.execute(text("""
            INSERT INTO peptide_chemical_forms (peptide_id, form_name, form_type, review_status)
            VALUES (:peptide, 'RLS form A', 'linear_peptide', 'verified') RETURNING id
        """), {"peptide": peptide_a}).scalar_one()
        form_b = connection.execute(text("""
            INSERT INTO peptide_chemical_forms (peptide_id, form_name, form_type, review_status)
            VALUES (:peptide, 'RLS form B', 'linear_peptide', 'verified') RETURNING id
        """), {"peptide": peptide_b}).scalar_one()
        source_id = connection.execute(text("""
            INSERT INTO source_records (source_name, source_identifier, source_url, retrieved_at, raw_metadata)
            VALUES ('RLS test source', :identifier, 'https://example.org/rls-test', now(), '{}'::jsonb)
            RETURNING id
        """), {"identifier": str(uuid4())}).scalar_one()

        own_a = connection.execute(text("""
            INSERT INTO vendor_material_offerings (
                organization_id, vendor_id, peptide_id, chemical_form_id, product_name,
                source_id, review_status, submitted_by, visibility_scope
            ) VALUES (:org, :vendor, :peptide, :form, 'Private offering A',
                      :source, 'in_review', :submitter, 'restricted')
            RETURNING id
        """), {"org": organization_a, "vendor": vendor_a, "peptide": peptide_a,
               "form": form_a, "source": source_id, "submitter": submitter_a}).scalar_one()
        own_b = connection.execute(text("""
            INSERT INTO vendor_material_offerings (
                organization_id, vendor_id, peptide_id, chemical_form_id, product_name,
                source_id, review_status, submitted_by, visibility_scope
            ) VALUES (:org, :vendor, :peptide, :form, 'Private offering B',
                      :source, 'in_review', :submitter, 'restricted')
            RETURNING id
        """), {"org": organization_b, "vendor": vendor_b, "peptide": peptide_b,
               "form": form_b, "source": source_id, "submitter": submitter_b}).scalar_one()
        public_b = connection.execute(text("""
            INSERT INTO vendor_material_offerings (
                organization_id, vendor_id, peptide_id, chemical_form_id, product_name,
                source_id, review_status, submitted_by, visibility_scope
            ) VALUES (:org, :vendor, :peptide, :form, 'Public verified offering B',
                      :source, 'verified', :submitter, 'public')
            RETURNING id
        """), {"org": organization_b, "vendor": vendor_b, "peptide": peptide_b,
               "form": form_b, "source": source_id, "submitter": submitter_b}).scalar_one()

        connection.exec_driver_sql("""
            DO $$ BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='toolkit_rls_test') THEN
                    CREATE ROLE toolkit_rls_test NOLOGIN NOBYPASSRLS;
                END IF;
            END $$;
        """)
        connection.exec_driver_sql("GRANT USAGE ON SCHEMA public TO toolkit_rls_test")
        connection.exec_driver_sql("GRANT SELECT ON vendor_material_offerings TO toolkit_rls_test")

        with connection.begin_nested():
            connection.exec_driver_sql("SET LOCAL ROLE toolkit_rls_test")
            connection.execute(text("""
                SELECT set_config('app.organization_id', :org, true)
            """), {"org": str(organization_a)})
            visible_a = set(connection.execute(text(
                "SELECT id FROM vendor_material_offerings"
            )).scalars().all())
            assert visible_a == {own_a, public_b}

            connection.execute(text("""
                SELECT set_config('app.organization_id', '', true)
            """))
            visible_public = set(connection.execute(text(
                "SELECT id FROM vendor_material_offerings"
            )).scalars().all())
            assert visible_public == {public_b}
        connection.exec_driver_sql("RESET ROLE")
        connection.exec_driver_sql("REVOKE SELECT ON vendor_material_offerings FROM toolkit_rls_test")
        connection.exec_driver_sql("REVOKE USAGE ON SCHEMA public FROM toolkit_rls_test")
        connection.exec_driver_sql("DROP ROLE toolkit_rls_test")
