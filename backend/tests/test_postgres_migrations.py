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
            "vendors", "vendor_sources", "vendor_review_decisions",
            "vendor_sites", "vendor_site_sources", "vendor_site_decisions",
            "vendor_certifications", "vendor_certification_decisions",
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
            "formulation_profiles",
            "formulation_components",
            "formulation_stability_observations",
            "formulation_sources",
            "formulation_review_decisions",
            "process_knowledge_profiles",
            "process_knowledge_stages",
            "process_knowledge_sources",
            "process_knowledge_decisions",
            "molecular_interaction_assessments",
            "molecular_interaction_decisions",
            "evidence_appraisals",
            "evidence_appraisal_decisions",
            "publication_duplicate_candidates",
            "publication_duplicate_decisions",
            "curation_reviews",
            "curation_decisions",
            "agent_sessions",
            "agent_session_messages",
            "regulatory_guidance_records",
            "regulatory_guidance_decisions",
            "regulatory_guidance_versions",
            "regulatory_change_events",
            "regulatory_change_decisions",
            "regulatory_source_observations",
            "regulatory_source_poll_runs",
            "claim_source_locators",
            "analytical_methods",
            "analytical_method_sources",
            "analytical_method_decisions",
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

        method_rls_tables = ("analytical_methods", "analytical_method_sources", "analytical_method_decisions")
        for table_name in method_rls_tables:
            method_rls_state = connection.execute(text("""
                SELECT relrowsecurity, relforcerowsecurity
                FROM pg_class WHERE oid=to_regclass(:table_name)
            """), {"table_name": f"public.{table_name}"}).one()
            assert tuple(method_rls_state) == (True, True), f"RLS and FORCE RLS must be enabled for {table_name}"

        method_policy_count = connection.execute(text("""
            SELECT count(*) FROM pg_policies
            WHERE schemaname='public' AND policyname IN (
                'analytical_methods_select_scope',
                'analytical_methods_insert_scope',
                'analytical_methods_update_scope',
                'analytical_method_sources_select_scope',
                'analytical_method_sources_insert_scope',
                'analytical_method_decisions_select_scope',
                'analytical_method_decisions_insert_scope'
            )
        """)).scalar_one()
        assert method_policy_count == 7, "Analytical method access paths need explicit RLS policies"

        knowledge_rls_tables = (
            "formulation_profiles", "formulation_components",
            "formulation_stability_observations", "formulation_sources",
            "formulation_review_decisions", "process_knowledge_profiles",
            "process_knowledge_stages", "process_knowledge_sources",
            "process_knowledge_decisions",
        )
        for table_name in knowledge_rls_tables:
            state = connection.execute(text("""
                SELECT relrowsecurity, relforcerowsecurity
                FROM pg_class WHERE oid=to_regclass(:table_name)
            """), {"table_name": f"public.{table_name}"}).one()
            assert tuple(state) == (True, True), f"RLS and FORCE RLS must be enabled for {table_name}"

        knowledge_policy_count = connection.execute(text("""
            SELECT count(*) FROM pg_policies
            WHERE schemaname='public' AND policyname IN (
                'formulation_profiles_select_scope','formulation_profiles_insert_scope','formulation_profiles_update_scope',
                'formulation_components_select_scope','formulation_components_insert_scope','formulation_components_update_scope',
                'formulation_stability_observations_select_scope','formulation_stability_observations_insert_scope','formulation_stability_observations_update_scope',
                'formulation_sources_select_scope','formulation_sources_insert_scope','formulation_sources_update_scope',
                'formulation_review_decisions_select_scope','formulation_review_decisions_insert_scope',
                'process_knowledge_profiles_select_scope','process_knowledge_profiles_insert_scope','process_knowledge_profiles_update_scope',
                'process_knowledge_stages_select_scope','process_knowledge_stages_insert_scope','process_knowledge_stages_update_scope',
                'process_knowledge_sources_select_scope','process_knowledge_sources_insert_scope','process_knowledge_sources_update_scope',
                'process_knowledge_decisions_select_scope','process_knowledge_decisions_insert_scope'
            )
        """)).scalar_one()
        assert knowledge_policy_count == 25, "Formulation and process knowledge access paths need explicit RLS policies"

        interaction_rls_tables = ("molecular_interaction_assessments", "molecular_interaction_decisions")
        for table_name in interaction_rls_tables:
            state = connection.execute(text("""
                SELECT relrowsecurity, relforcerowsecurity
                FROM pg_class WHERE oid=to_regclass(:table_name)
            """), {"table_name": f"public.{table_name}"}).one()
            assert tuple(state) == (True, True), f"RLS and FORCE RLS must be enabled for {table_name}"
        interaction_policy_count = connection.execute(text("""
            SELECT count(*) FROM pg_policies
            WHERE schemaname='public' AND policyname IN (
                'molecular_interaction_assessments_select_scope',
                'molecular_interaction_assessments_insert_scope',
                'molecular_interaction_assessments_update_scope',
                'molecular_interaction_decisions_select_scope',
                'molecular_interaction_decisions_insert_scope'
            )
        """)).scalar_one()
        assert interaction_policy_count == 5, "Interaction assessment and decision access paths need explicit RLS policies"

        appraisal_rls_tables = (
            "evidence_appraisals", "evidence_appraisal_decisions",
            "publication_duplicate_candidates", "publication_duplicate_decisions",
        )
        for table_name in appraisal_rls_tables:
            state = connection.execute(text("""
                SELECT relrowsecurity, relforcerowsecurity
                FROM pg_class WHERE oid=to_regclass(:table_name)
            """), {"table_name": f"public.{table_name}"}).one()
            assert tuple(state) == (True, True), f"RLS and FORCE RLS must be enabled for {table_name}"
        appraisal_policy_count = connection.execute(text("""
            SELECT count(*) FROM pg_policies
            WHERE schemaname='public' AND policyname IN (
                'evidence_appraisals_select_scope','evidence_appraisals_insert_scope','evidence_appraisals_update_scope',
                'evidence_appraisal_decisions_select_scope','evidence_appraisal_decisions_insert_scope',
                'publication_duplicate_candidates_select_scope','publication_duplicate_candidates_insert_scope','publication_duplicate_candidates_update_scope',
                'publication_duplicate_decisions_select_scope','publication_duplicate_decisions_insert_scope'
            )
        """)).scalar_one()
        assert appraisal_policy_count == 10, "Evidence appraisal and duplicate-review access paths need explicit RLS policies"

        for table_name in ("curation_reviews", "curation_decisions"):
            state = connection.execute(text("""
                SELECT relrowsecurity, relforcerowsecurity
                FROM pg_class WHERE oid=to_regclass(:table_name)
            """), {"table_name": f"public.{table_name}"}).one()
            assert tuple(state) == (True, True), f"RLS and FORCE RLS must be enabled for {table_name}"
        curation_policy_count = connection.execute(text("""
            SELECT count(*) FROM pg_policies
            WHERE schemaname='public' AND policyname IN (
                'curation_reviews_select_scope','curation_reviews_insert_scope','curation_reviews_update_scope',
                'curation_decisions_select_scope','curation_decisions_insert_scope'
            )
        """)).scalar_one()
        assert curation_policy_count == 5, "Curation review and decision access paths need explicit RLS policies"

        for table_name in ("agent_sessions", "agent_session_messages"):
            state = connection.execute(text("""
                SELECT relrowsecurity, relforcerowsecurity
                FROM pg_class WHERE oid=to_regclass(:table_name)
            """), {"table_name": f"public.{table_name}"}).one()
            assert tuple(state) == (True, True), f"RLS and FORCE RLS must be enabled for {table_name}"
        agent_policy_count = connection.execute(text("""
            SELECT count(*) FROM pg_policies
            WHERE schemaname='public' AND policyname IN (
                'agent_sessions_select_scope','agent_sessions_insert_scope','agent_sessions_update_scope',
                'agent_session_messages_select_scope','agent_session_messages_insert_scope'
            )
        """)).scalar_one()
        assert agent_policy_count == 5, "Agent sessions and messages need user-and-organization RLS policies"

        regulatory_rls_tables = (
            "regulatory_guidance_records", "regulatory_guidance_decisions",
            "regulatory_guidance_versions", "regulatory_change_events",
            "regulatory_change_decisions",
        )
        for table_name in regulatory_rls_tables:
            state = connection.execute(text("""
                SELECT relrowsecurity, relforcerowsecurity
                FROM pg_class WHERE oid=to_regclass(:table_name)
            """), {"table_name": f"public.{table_name}"}).one()
            assert tuple(state) == (True, True), f"RLS and FORCE RLS must be enabled for {table_name}"
        regulatory_policy_count = connection.execute(text("""
            SELECT count(*) FROM pg_policies
            WHERE schemaname='public' AND policyname IN (
                'regulatory_guidance_records_select_scope','regulatory_guidance_records_insert_scope','regulatory_guidance_records_update_scope',
                'regulatory_guidance_decisions_select_scope','regulatory_guidance_decisions_insert_scope',
                'regulatory_guidance_versions_select_scope','regulatory_guidance_versions_insert_scope','regulatory_guidance_versions_update_scope',
                'regulatory_change_events_select_scope','regulatory_change_events_insert_scope','regulatory_change_events_update_scope',
                'regulatory_change_decisions_select_scope','regulatory_change_decisions_insert_scope'
            )
        """)).scalar_one()
        assert regulatory_policy_count == 13, "Regulatory guidance and change-history access paths need explicit RLS policies"

        for table_name in ("regulatory_source_observations", "regulatory_source_poll_runs"):
            state = connection.execute(text("""
                SELECT relrowsecurity, relforcerowsecurity
                FROM pg_class WHERE oid=to_regclass(:table_name)
            """), {"table_name": f"public.{table_name}"}).one()
            assert tuple(state) == (True, True), f"RLS and FORCE RLS must be enabled for {table_name}"
        source_scheduler_policy_count = connection.execute(text("""
            SELECT count(*) FROM pg_policies
            WHERE schemaname='public' AND policyname IN (
                'regulatory_source_observations_select_scope','regulatory_source_observations_insert_scope','regulatory_source_observations_update_scope',
                'regulatory_source_poll_runs_select_scope','regulatory_source_poll_runs_insert_scope','regulatory_source_poll_runs_update_scope'
            )
        """)).scalar_one()
        assert source_scheduler_policy_count == 6, "Regulatory source observations and poll runs need explicit RLS policies"

        vendor_rls_tables = (
            "vendors", "vendor_sources", "vendor_review_decisions",
            "vendor_sites", "vendor_site_sources", "vendor_site_decisions",
            "vendor_certifications", "vendor_certification_decisions",
        )
        for table_name in vendor_rls_tables:
            state = connection.execute(text("""
                SELECT relrowsecurity, relforcerowsecurity
                FROM pg_class WHERE oid=to_regclass(:table_name)
            """), {"table_name": f"public.{table_name}"}).one()
            assert tuple(state) == (True, True), f"RLS and FORCE RLS must be enabled for {table_name}"
        vendor_policy_count = connection.execute(text("""
            SELECT count(*) FROM pg_policies
            WHERE schemaname='public' AND policyname IN (
                'vendors_select_scope','vendors_insert_scope','vendors_update_scope',
                'vendor_sources_select_scope','vendor_sources_insert_scope','vendor_sources_update_scope',
                'vendor_review_decisions_select_scope','vendor_review_decisions_insert_scope',
                'vendor_sites_select_scope','vendor_sites_insert_scope','vendor_sites_update_scope',
                'vendor_site_sources_select_scope','vendor_site_sources_insert_scope','vendor_site_sources_update_scope',
                'vendor_site_decisions_select_scope','vendor_site_decisions_insert_scope',
                'vendor_certifications_select_scope','vendor_certifications_insert_scope','vendor_certifications_update_scope',
                'vendor_certification_decisions_select_scope','vendor_certification_decisions_insert_scope'
            )
        """)).scalar_one()
        assert vendor_policy_count == 21, "Vendor identity, site and certification access paths need explicit RLS policies"

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

        method_a = connection.execute(text("""
            INSERT INTO analytical_methods (
                method_name, method_category, owner_organization_id, visibility_scope,
                review_status, submitted_by, limitations
            ) VALUES ('Private method A', 'other', :org, 'organization',
                      'in_review', :submitter, 'Organization-owned test method.')
            RETURNING id
        """), {"org": organization_a, "submitter": submitter_a}).scalar_one()
        method_b = connection.execute(text("""
            INSERT INTO analytical_methods (
                method_name, method_category, owner_organization_id, visibility_scope,
                review_status, submitted_by, limitations
            ) VALUES ('Private method B', 'other', :org, 'organization',
                      'in_review', :submitter, 'Organization-owned test method.')
            RETURNING id
        """), {"org": organization_b, "submitter": submitter_b}).scalar_one()
        method_public = connection.execute(text("""
            INSERT INTO analytical_methods (
                method_name, method_category, owner_organization_id, visibility_scope,
                review_status, submitted_by, limitations
            ) VALUES ('Public verified method', 'other', NULL, 'public',
                      'verified', NULL, 'Shared master test method.')
            RETURNING id
        """)).scalar_one()
        for method_id in (method_a, method_b, method_public):
            connection.execute(text("""
                INSERT INTO analytical_method_sources (method_id, source_record_id, evidence_scope)
                VALUES (:method, :source, 'Source describes the analytical method and its scope.')
            """), {"method": method_id, "source": source_id})
        connection.execute(text("""
            INSERT INTO analytical_method_decisions
                (method_id, organization_id, reviewer_id, decision, rationale)
            VALUES (:method_a, :org_a, :reviewer_a, 'verified', 'Independent method review for organization A.'),
                   (:method_b, :org_b, :reviewer_b, 'verified', 'Independent method review for organization B.')
        """), {"method_a": method_a, "org_a": organization_a, "reviewer_a": submitter_b,
               "method_b": method_b, "org_b": organization_b, "reviewer_b": submitter_a})

        with pytest.raises(Exception):
            with connection.begin_nested():
                connection.execute(text("""
                INSERT INTO analytical_method_decisions
                    (method_id, organization_id, reviewer_id, decision, rationale)
                VALUES (:method, :wrong_org, :reviewer, 'verified',
                        'This deliberately mismatched organization must be rejected.')
            """), {"method": method_a, "wrong_org": organization_b, "reviewer": submitter_b})

        role_exists = connection.execute(text(
            "SELECT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='toolkit_rls_test')"
        )).scalar_one()
        if not role_exists:
            connection.exec_driver_sql("CREATE ROLE toolkit_rls_test NOLOGIN NOBYPASSRLS")
        connection.exec_driver_sql("GRANT USAGE ON SCHEMA public TO toolkit_rls_test")
        connection.exec_driver_sql("GRANT SELECT ON vendor_material_offerings TO toolkit_rls_test")
        connection.exec_driver_sql("GRANT SELECT ON analytical_methods TO toolkit_rls_test")
        connection.exec_driver_sql("GRANT SELECT ON analytical_method_sources TO toolkit_rls_test")
        connection.exec_driver_sql("GRANT SELECT ON analytical_method_decisions TO toolkit_rls_test")

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
            connection.execute(text("""
                SELECT set_config('app.organization_id', :org, true)
            """), {"org": str(organization_a)})
            visible_methods_a = set(connection.execute(text(
                "SELECT id FROM analytical_methods"
            )).scalars().all())
            assert visible_methods_a == {method_a, method_public}
            visible_method_sources_a = set(connection.execute(text(
                "SELECT method_id FROM analytical_method_sources"
            )).scalars().all())
            assert visible_method_sources_a == {method_a, method_public}
            visible_method_decisions_a = set(connection.execute(text(
                "SELECT method_id FROM analytical_method_decisions"
            )).scalars().all())
            assert visible_method_decisions_a == {method_a}

            connection.execute(text("""
                SELECT set_config('app.organization_id', '', true)
            """))
            visible_methods_public = set(connection.execute(text(
                "SELECT id FROM analytical_methods"
            )).scalars().all())
            assert visible_methods_public == {method_public}
            visible_sources_public = set(connection.execute(text(
                "SELECT method_id FROM analytical_method_sources"
            )).scalars().all())
            assert visible_sources_public == {method_public}
            assert connection.execute(text(
                "SELECT count(*) FROM analytical_method_decisions"
            )).scalar_one() == 0
        connection.exec_driver_sql("RESET ROLE")
        connection.exec_driver_sql("REVOKE SELECT ON analytical_method_decisions FROM toolkit_rls_test")
        connection.exec_driver_sql("REVOKE SELECT ON analytical_method_sources FROM toolkit_rls_test")
        connection.exec_driver_sql("REVOKE SELECT ON analytical_methods FROM toolkit_rls_test")
        connection.exec_driver_sql("REVOKE SELECT ON vendor_material_offerings FROM toolkit_rls_test")
        connection.exec_driver_sql("REVOKE USAGE ON SCHEMA public FROM toolkit_rls_test")
        connection.exec_driver_sql("DROP ROLE toolkit_rls_test")



@pytest.mark.skipif(
    os.getenv("RUN_POSTGRES_MIGRATION_TESTS") != "1",
    reason="PostgreSQL citation-locator integrity test is enabled in CI only.",
)
def test_claim_source_locator_binds_exact_source_version_and_is_append_only():
    with engine.begin() as connection:
        connection.execute(text("SELECT pg_advisory_xact_lock(731904221067)"))
        apply_development_migrations(connection)

        source_a = connection.execute(text("""
            INSERT INTO source_records (source_name, source_identifier, source_url, raw_metadata)
            VALUES ('Locator test source A', :identifier, 'https://example.org/a', '{}'::jsonb)
            RETURNING id
        """), {"identifier": str(uuid4())}).scalar_one()
        source_b = connection.execute(text("""
            INSERT INTO source_records (source_name, source_identifier, source_url, raw_metadata)
            VALUES ('Locator test source B', :identifier, 'https://example.org/b', '{}'::jsonb)
            RETURNING id
        """), {"identifier": str(uuid4())}).scalar_one()
        version_a = connection.execute(text("""
            INSERT INTO source_record_versions (source_record_id, content_hash, raw_payload)
            VALUES (:source, :hash, CAST(:payload AS jsonb)) RETURNING id
        """), {"source": source_a, "hash": "a" * 64, "payload": '{"release":"A"}'}).scalar_one()
        version_b = connection.execute(text("""
            INSERT INTO source_record_versions (source_record_id, content_hash, raw_payload)
            VALUES (:source, :hash, CAST(:payload AS jsonb)) RETURNING id
        """), {"source": source_b, "hash": "b" * 64, "payload": '{"release":"B"}'}).scalar_one()
        peptide_id = connection.execute(text("""
            INSERT INTO peptides (preferred_name, review_status)
            VALUES (:name, 'in_review') RETURNING id
        """), {"name": "Locator test peptide " + str(uuid4())}).scalar_one()
        claim_id = connection.execute(text("""
            INSERT INTO evidence_claims (peptide_id, claim_text, claim_domain)
            VALUES (:peptide, 'A source-backed test claim.', 'mechanism') RETURNING id
        """), {"peptide": peptide_id}).scalar_one()
        claim_source_id = connection.execute(text("""
            INSERT INTO claim_sources (claim_id, source_record_id, supporting_excerpt, relationship)
            VALUES (:claim, :source, 'Permitted short excerpt.', 'supports') RETURNING id
        """), {"claim": claim_id, "source": source_a}).scalar_one()

        locator_id = connection.execute(text("""
            INSERT INTO claim_source_locators (
                claim_source_id, source_record_version_id, locator_type,
                locator_value, quoted_text_hash
            ) VALUES (:claim_source, :version, 'figure', 'Figure 2',
                      :quoted_hash) RETURNING id
        """), {"claim_source": claim_source_id, "version": version_a,
               "quoted_hash": "c" * 64}).scalar_one()

        with pytest.raises(Exception):
            with connection.begin_nested():
                connection.execute(text("""
                    INSERT INTO claim_source_locators (
                        claim_source_id, source_record_version_id, locator_type, locator_value
                    ) VALUES (:claim_source, :version, 'page', 'Page 4')
                """), {"claim_source": claim_source_id, "version": version_b})

        with pytest.raises(Exception):
            with connection.begin_nested():
                connection.execute(text("""
                    UPDATE claim_source_locators SET locator_value='Page 9'
                    WHERE id=:locator
                """), {"locator": locator_id})

        with pytest.raises(Exception):
            with connection.begin_nested():
                connection.execute(text("""
                    DELETE FROM claim_source_locators WHERE id=:locator
                """), {"locator": locator_id})


@pytest.mark.skipif(
    os.getenv("RUN_POSTGRES_MIGRATION_TESTS") != "1",
    reason="PostgreSQL formulation/process RLS integration test is enabled in CI only.",
)
def test_formulation_and_process_rls_inherit_parent_visibility():
    with engine.begin() as connection:
        connection.execute(text("SELECT pg_advisory_xact_lock(731904221067)"))
        apply_development_migrations(connection)

        org_a = connection.execute(text("""
            INSERT INTO organizations (name, organization_type)
            VALUES (:name, 'research_team') RETURNING id
        """), {"name": "knowledge-rls-a-" + str(uuid4())}).scalar_one()
        org_b = connection.execute(text("""
            INSERT INTO organizations (name, organization_type)
            VALUES (:name, 'research_team') RETURNING id
        """), {"name": "knowledge-rls-b-" + str(uuid4())}).scalar_one()
        user_a = connection.execute(text("""
            INSERT INTO user_profiles (display_name, role) VALUES ('Knowledge A', 'researcher') RETURNING id
        """)).scalar_one()
        user_b = connection.execute(text("""
            INSERT INTO user_profiles (display_name, role) VALUES ('Knowledge B', 'researcher') RETURNING id
        """)).scalar_one()
        source_id = connection.execute(text("""
            INSERT INTO source_records (source_name, source_identifier, source_url, raw_metadata)
            VALUES ('Knowledge RLS source', :identifier, 'https://example.org/knowledge-rls', '{}'::jsonb)
            RETURNING id
        """), {"identifier": str(uuid4())}).scalar_one()

        def formulation(name, owner, visibility, status, submitter):
            return connection.execute(text("""
                INSERT INTO formulation_profiles (
                    formulation_name, formulation_type, intended_research_context,
                    formulation_rationale, limitations, review_status, submitted_by,
                    owner_organization_id, visibility_scope
                ) VALUES (:name, 'research', 'literature review', 'Test rationale',
                          'Not a validated recipe.', :status, :submitter, :owner, :visibility)
                RETURNING id
            """), {"name": name, "owner": owner, "visibility": visibility,
                   "status": status, "submitter": submitter}).scalar_one()

        form_a = formulation("Private formulation A " + str(uuid4()), org_a, "organization", "in_review", user_a)
        form_b = formulation("Private formulation B " + str(uuid4()), org_b, "organization", "in_review", user_b)
        form_public = formulation("Public formulation " + str(uuid4()), None, "public", "verified", None)

        def form_children(form_id, prefix):
            connection.execute(text("""
                INSERT INTO formulation_components (formulation_id, component_name, component_role, review_status)
                VALUES (:id, :name, 'buffer', 'verified')
            """), {"id": form_id, "name": prefix + " component"})
            connection.execute(text("""
                INSERT INTO formulation_stability_observations (
                    formulation_id, study_context, observed_change, limitations, review_status
                ) VALUES (:id, 'accelerated study context', 'Observed change', 'Study-specific only', 'verified')
            """), {"id": form_id})
            connection.execute(text("""
                INSERT INTO formulation_sources (formulation_id, source_record_id, evidence_scope)
                VALUES (:id, :source, 'Source describes this formulation record.')
            """), {"id": form_id, "source": source_id})

        for form_id, label in ((form_a, "A"), (form_b, "B"), (form_public, "Public")):
            form_children(form_id, label)
        connection.execute(text("""
            INSERT INTO formulation_review_decisions (formulation_id, organization_id, reviewer_id, decision, rationale)
            VALUES (:form, :org, :reviewer, 'verified', 'Organization-specific review decision.')
        """), {"form": form_a, "org": org_a, "reviewer": user_b})
        connection.execute(text("""
            INSERT INTO formulation_review_decisions (formulation_id, organization_id, reviewer_id, decision, rationale)
            VALUES (:form, :org, :reviewer, 'verified', 'Organization-specific review decision.')
        """), {"form": form_b, "org": org_b, "reviewer": user_a})

        def process(name, owner, visibility, status, submitter):
            return connection.execute(text("""
                INSERT INTO process_knowledge_profiles (
                    profile_title, process_platform, development_context, process_overview,
                    limitations, review_status, submitted_by, owner_organization_id, visibility_scope
                ) VALUES (:name, 'research literature', 'non-operational research', 'Descriptive overview',
                          'Not a manufacturing instruction.', :status, :submitter, :owner, :visibility)
                RETURNING id
            """), {"name": name, "owner": owner, "visibility": visibility,
                   "status": status, "submitter": submitter}).scalar_one()

        process_a = process("Private process A " + str(uuid4()), org_a, "organization", "in_review", user_a)
        process_b = process("Private process B " + str(uuid4()), org_b, "organization", "in_review", user_b)
        process_public = process("Public process " + str(uuid4()), None, "public", "verified", None)

        def process_children(profile_id, prefix):
            connection.execute(text("""
                INSERT INTO process_knowledge_stages (
                    profile_id, stage_name, stage_category, scientific_purpose, review_status
                ) VALUES (:id, :name, 'analytical', 'Descriptive research purpose', 'verified')
            """), {"id": profile_id, "name": prefix + " stage"})
            connection.execute(text("""
                INSERT INTO process_knowledge_sources (profile_id, source_record_id, evidence_scope)
                VALUES (:id, :source, 'Source describes this process record.')
            """), {"id": profile_id, "source": source_id})

        for profile_id, label in ((process_a, "A"), (process_b, "B"), (process_public, "Public")):
            process_children(profile_id, label)
        connection.execute(text("""
            INSERT INTO process_knowledge_decisions (profile_id, organization_id, reviewer_id, decision, rationale)
            VALUES (:profile, :org, :reviewer, 'verified', 'Organization-specific review decision.')
        """), {"profile": process_a, "org": org_a, "reviewer": user_b})
        connection.execute(text("""
            INSERT INTO process_knowledge_decisions (profile_id, organization_id, reviewer_id, decision, rationale)
            VALUES (:profile, :org, :reviewer, 'verified', 'Organization-specific review decision.')
        """), {"profile": process_b, "org": org_b, "reviewer": user_a})

        role = "toolkit_knowledge_rls_test"
        exists = connection.execute(text("SELECT EXISTS (SELECT 1 FROM pg_roles WHERE rolname=:role)"), {"role": role}).scalar_one()
        if not exists:
            connection.exec_driver_sql(f"CREATE ROLE {role} NOLOGIN NOBYPASSRLS")
        connection.exec_driver_sql("GRANT USAGE ON SCHEMA public TO toolkit_knowledge_rls_test")
        for table in (
            "formulation_profiles", "formulation_components", "formulation_stability_observations",
            "formulation_sources", "formulation_review_decisions", "process_knowledge_profiles",
            "process_knowledge_stages", "process_knowledge_sources", "process_knowledge_decisions",
        ):
            connection.exec_driver_sql(f"GRANT SELECT, INSERT, UPDATE ON {table} TO toolkit_knowledge_rls_test")

        with connection.begin_nested():
            connection.exec_driver_sql("SET LOCAL ROLE toolkit_knowledge_rls_test")
            connection.execute(text("SELECT set_config('app.organization_id', :org, true)"), {"org": str(org_a)})
            assert set(connection.execute(text("SELECT id FROM formulation_profiles")).scalars()) == {form_a, form_public}
            assert set(connection.execute(text("SELECT formulation_id FROM formulation_components")).scalars()) == {form_a, form_public}
            assert set(connection.execute(text("SELECT formulation_id FROM formulation_stability_observations")).scalars()) == {form_a, form_public}
            assert set(connection.execute(text("SELECT formulation_id FROM formulation_sources")).scalars()) == {form_a, form_public}
            assert set(connection.execute(text("SELECT formulation_id FROM formulation_review_decisions")).scalars()) == {form_a}

            assert set(connection.execute(text("SELECT id FROM process_knowledge_profiles")).scalars()) == {process_a, process_public}
            assert set(connection.execute(text("SELECT profile_id FROM process_knowledge_stages")).scalars()) == {process_a, process_public}
            assert set(connection.execute(text("SELECT profile_id FROM process_knowledge_sources")).scalars()) == {process_a, process_public}
            assert set(connection.execute(text("SELECT profile_id FROM process_knowledge_decisions")).scalars()) == {process_a}

            # Direct-ID writes against another organization's parent or children must fail.
            with pytest.raises(Exception):
                with connection.begin_nested():
                    connection.execute(text("""
                        INSERT INTO formulation_profiles (
                            formulation_name, formulation_type, intended_research_context,
                            formulation_rationale, limitations, submitted_by,
                            owner_organization_id, visibility_scope
                        ) VALUES ('Cross-tenant formulation', 'research', 'test',
                                  'must fail', 'must fail', :submitter, :owner, 'organization')
                    """), {"submitter": user_a, "owner": org_b})
            with pytest.raises(Exception):
                with connection.begin_nested():
                    connection.execute(text("""
                        INSERT INTO formulation_components (formulation_id, component_name, component_role)
                        VALUES (:form, 'Cross-tenant component', 'buffer')
                    """), {"form": form_b})
            with pytest.raises(Exception):
                with connection.begin_nested():
                    connection.execute(text("""
                        INSERT INTO formulation_review_decisions (
                            formulation_id, organization_id, reviewer_id, decision, rationale
                        ) VALUES (:form, :org, :reviewer, 'verified', 'must fail')
                    """), {"form": form_b, "org": org_a, "reviewer": user_a})

            with pytest.raises(Exception):
                with connection.begin_nested():
                    connection.execute(text("""
                        INSERT INTO process_knowledge_profiles (
                            profile_title, process_platform, development_context, process_overview,
                            limitations, submitted_by, owner_organization_id, visibility_scope
                        ) VALUES ('Cross-tenant process', 'research', 'test', 'must fail',
                                  'must fail', :submitter, :owner, 'organization')
                    """), {"submitter": user_a, "owner": org_b})
            with pytest.raises(Exception):
                with connection.begin_nested():
                    connection.execute(text("""
                        INSERT INTO process_knowledge_stages (
                            profile_id, stage_name, stage_category, scientific_purpose
                        ) VALUES (:profile, 'Cross-tenant stage', 'analytical', 'must fail')
                    """), {"profile": process_b})
            with pytest.raises(Exception):
                with connection.begin_nested():
                    connection.execute(text("""
                        INSERT INTO process_knowledge_decisions (
                            profile_id, organization_id, reviewer_id, decision, rationale
                        ) VALUES (:profile, :org, :reviewer, 'verified', 'must fail')
                    """), {"profile": process_b, "org": org_a, "reviewer": user_a})

            connection.execute(text("UPDATE formulation_components SET review_status='verified' WHERE formulation_id=:id"), {"id": form_a})
            connection.execute(text("UPDATE formulation_stability_observations SET review_status='verified' WHERE formulation_id=:id"), {"id": form_a})
            connection.execute(text("UPDATE process_knowledge_stages SET review_status='verified' WHERE profile_id=:id"), {"id": process_a})

            connection.execute(text("SELECT set_config('app.organization_id', '', true)"))
            assert set(connection.execute(text("SELECT id FROM formulation_profiles")).scalars()) == {form_public}
            assert set(connection.execute(text("SELECT formulation_id FROM formulation_components")).scalars()) == {form_public}
            assert set(connection.execute(text("SELECT formulation_id FROM formulation_stability_observations")).scalars()) == {form_public}
            assert set(connection.execute(text("SELECT formulation_id FROM formulation_sources")).scalars()) == {form_public}
            assert connection.execute(text("SELECT count(*) FROM formulation_review_decisions")).scalar_one() == 0

            assert set(connection.execute(text("SELECT id FROM process_knowledge_profiles")).scalars()) == {process_public}
            assert set(connection.execute(text("SELECT profile_id FROM process_knowledge_stages")).scalars()) == {process_public}
            assert set(connection.execute(text("SELECT profile_id FROM process_knowledge_sources")).scalars()) == {process_public}
            assert connection.execute(text("SELECT count(*) FROM process_knowledge_decisions")).scalar_one() == 0

        connection.exec_driver_sql("RESET ROLE")
        for table in (
            "formulation_profiles", "formulation_components", "formulation_stability_observations",
            "formulation_sources", "formulation_review_decisions", "process_knowledge_profiles",
            "process_knowledge_stages", "process_knowledge_sources", "process_knowledge_decisions",
        ):
            connection.exec_driver_sql(f"REVOKE SELECT, INSERT, UPDATE ON {table} FROM toolkit_knowledge_rls_test")
        connection.exec_driver_sql("REVOKE USAGE ON SCHEMA public FROM toolkit_knowledge_rls_test")
        connection.exec_driver_sql("DROP ROLE toolkit_knowledge_rls_test")


@pytest.mark.skipif(
    os.getenv("RUN_POSTGRES_MIGRATION_TESTS") != "1",
    reason="PostgreSQL molecular interaction RLS integration test is enabled in CI only.",
)
def test_molecular_interaction_rls_enforces_owner_and_public_verified_scope():
    with engine.begin() as connection:
        connection.execute(text("SELECT pg_advisory_xact_lock(731904221067)"))
        apply_development_migrations(connection)

        org_a = connection.execute(text("""
            INSERT INTO organizations (name, organization_type)
            VALUES (:name, 'research_team') RETURNING id
        """), {"name": "interaction-rls-a-" + str(uuid4())}).scalar_one()
        org_b = connection.execute(text("""
            INSERT INTO organizations (name, organization_type)
            VALUES (:name, 'research_team') RETURNING id
        """), {"name": "interaction-rls-b-" + str(uuid4())}).scalar_one()
        user_a = connection.execute(text("""
            INSERT INTO user_profiles (display_name, role) VALUES ('Interaction A', 'researcher') RETURNING id
        """)).scalar_one()
        user_b = connection.execute(text("""
            INSERT INTO user_profiles (display_name, role) VALUES ('Interaction B', 'researcher') RETURNING id
        """)).scalar_one()
        peptide_id = connection.execute(text("""
            INSERT INTO peptides (preferred_name, review_status)
            VALUES (:name, 'verified') RETURNING id
        """), {"name": "Interaction RLS peptide " + str(uuid4())}).scalar_one()
        target_id = connection.execute(text("""
            INSERT INTO targets (preferred_name) VALUES (:name) RETURNING id
        """), {"name": "Interaction RLS target " + str(uuid4())}).scalar_one()
        source_id = connection.execute(text("""
            INSERT INTO source_records (source_name, source_identifier, source_url, raw_metadata)
            VALUES ('Interaction RLS source', :identifier, 'https://example.org/interaction-rls', '{}'::jsonb)
            RETURNING id
        """), {"identifier": str(uuid4())}).scalar_one()

        def assessment(name, owner, visibility, status, submitter):
            return connection.execute(text("""
                INSERT INTO molecular_interaction_assessments (
                    peptide_id, target_id, interaction_method, evidence_type,
                    interface_summary, limitations, source_id, review_status,
                    submitted_by, owner_organization_id, visibility_scope
                ) VALUES (
                    :peptide, :target, 'literature_report', 'computational',
                    :summary, 'Not a measured binding affinity.', :source, :status,
                    :submitter, :owner, :visibility
                ) RETURNING id
            """), {"name": name, "peptide": peptide_id, "target": target_id,
                   "summary": name + " source-linked interaction summary.",
                   "source": source_id, "status": status, "submitter": submitter,
                   "owner": owner, "visibility": visibility}).scalar_one()

        assessment_a = assessment("Private interaction A " + str(uuid4()), org_a, "organization", "in_review", user_a)
        assessment_b = assessment("Private interaction B " + str(uuid4()), org_b, "organization", "in_review", user_b)
        assessment_public = assessment("Public interaction " + str(uuid4()), None, "public", "verified", None)
        connection.execute(text("""
            INSERT INTO molecular_interaction_decisions (assessment_id, organization_id, reviewer_id, decision, rationale)
            VALUES (:assessment, :org, :reviewer, 'verified', 'Organization-scoped independent review.')
        """), {"assessment": assessment_a, "org": org_a, "reviewer": user_b})
        connection.execute(text("""
            INSERT INTO molecular_interaction_decisions (assessment_id, organization_id, reviewer_id, decision, rationale)
            VALUES (:assessment, :org, :reviewer, 'verified', 'Organization-scoped independent review.')
        """), {"assessment": assessment_b, "org": org_b, "reviewer": user_a})

        role = "toolkit_interaction_rls_test"
        exists = connection.execute(text("SELECT EXISTS (SELECT 1 FROM pg_roles WHERE rolname=:role)"), {"role": role}).scalar_one()
        if not exists:
            connection.exec_driver_sql(f"CREATE ROLE {role} NOLOGIN NOBYPASSRLS")
        connection.exec_driver_sql("GRANT USAGE ON SCHEMA public TO toolkit_interaction_rls_test")
        connection.exec_driver_sql("GRANT SELECT, INSERT, UPDATE ON molecular_interaction_assessments TO toolkit_interaction_rls_test")
        connection.exec_driver_sql("GRANT SELECT, INSERT, UPDATE ON molecular_interaction_decisions TO toolkit_interaction_rls_test")

        with connection.begin_nested():
            connection.exec_driver_sql("SET LOCAL ROLE toolkit_interaction_rls_test")
            connection.execute(text("SELECT set_config('app.organization_id', :org, true)"), {"org": str(org_a)})
            assert set(connection.execute(text("SELECT id FROM molecular_interaction_assessments")).scalars()) == {assessment_a, assessment_public}
            assert set(connection.execute(text("SELECT assessment_id FROM molecular_interaction_decisions")).scalars()) == {assessment_a}

            with pytest.raises(Exception):
                with connection.begin_nested():
                    connection.execute(text("""
                        INSERT INTO molecular_interaction_assessments (
                            peptide_id, target_id, interaction_method, evidence_type,
                            interface_summary, limitations, source_id, review_status,
                            submitted_by, owner_organization_id, visibility_scope
                        ) VALUES (
                            :peptide, :target, 'literature_report', 'computational',
                            'Cross-tenant submission must fail.', 'Must fail.', :source,
                            'in_review', :submitter, :owner, 'organization'
                        )
                    """), {"peptide": peptide_id, "target": target_id, "source": source_id,
                           "submitter": user_a, "owner": org_b})

            with pytest.raises(Exception):
                with connection.begin_nested():
                    connection.execute(text("""
                        INSERT INTO molecular_interaction_decisions (
                            assessment_id, organization_id, reviewer_id, decision, rationale
                        ) VALUES (:assessment, :org, :reviewer, 'verified', 'Cross-tenant decision must fail.')
                    """), {"assessment": assessment_b, "org": org_a, "reviewer": user_a})

            connection.execute(text("""
                UPDATE molecular_interaction_assessments
                SET review_status='verified', reviewed_by=:reviewer, reviewed_at=now()
                WHERE id=:id
            """), {"reviewer": user_b, "id": assessment_a})

            connection.execute(text("SELECT set_config('app.organization_id', '', true)"))
            assert set(connection.execute(text("SELECT id FROM molecular_interaction_assessments")).scalars()) == {assessment_public}
            assert connection.execute(text("SELECT count(*) FROM molecular_interaction_decisions")).scalar_one() == 0

        connection.exec_driver_sql("RESET ROLE")
        connection.exec_driver_sql("REVOKE SELECT, INSERT, UPDATE ON molecular_interaction_decisions FROM toolkit_interaction_rls_test")
        connection.exec_driver_sql("REVOKE SELECT, INSERT, UPDATE ON molecular_interaction_assessments FROM toolkit_interaction_rls_test")
        connection.exec_driver_sql("REVOKE USAGE ON SCHEMA public FROM toolkit_interaction_rls_test")
        connection.exec_driver_sql("DROP ROLE toolkit_interaction_rls_test")


@pytest.mark.skipif(os.getenv("RUN_POSTGRES_MIGRATION_TESTS") != "1",
                    reason="PostgreSQL evidence appraisal RLS integration test is enabled in CI only.")
def test_evidence_appraisal_and_duplicate_review_rls_are_organization_scoped():
    with engine.begin() as connection:
        connection.execute(text("SELECT pg_advisory_xact_lock(731904221067)"))
        apply_development_migrations(connection)
        org_a = connection.execute(text("INSERT INTO organizations (name, organization_type) VALUES (:n,'research_team') RETURNING id"),
                                   {"n": "appraisal-a-" + str(uuid4())}).scalar_one()
        org_b = connection.execute(text("INSERT INTO organizations (name, organization_type) VALUES (:n,'research_team') RETURNING id"),
                                   {"n": "appraisal-b-" + str(uuid4())}).scalar_one()
        user_a = connection.execute(text("INSERT INTO user_profiles (display_name, role) VALUES ('Appraisal A','researcher') RETURNING id")).scalar_one()
        user_b = connection.execute(text("INSERT INTO user_profiles (display_name, role) VALUES ('Appraisal B','researcher') RETURNING id")).scalar_one()
        peptide = connection.execute(text("INSERT INTO peptides (preferred_name, review_status) VALUES (:n,'verified') RETURNING id"),
                                     {"n": "Appraisal peptide " + str(uuid4())}).scalar_one()
        claim = connection.execute(text("INSERT INTO evidence_claims (peptide_id, claim_text, claim_domain) VALUES (:p,'Evidence appraisal RLS test claim.','mechanism') RETURNING id"),
                                   {"p": peptide}).scalar_one()

        def add_appraisal(org, reviewer):
            return connection.execute(text("""
                INSERT INTO evidence_appraisals
                (organization_id,claim_id,study_design,evidence_level,risk_of_bias,replication_status,
                 limitations,appraisal_rationale,reviewer_id)
                VALUES (:o,:c,'observational_human','clinical_human','some_concerns','single_study',
                        'Study-specific limitations.','Appraisal rationale with sufficient detail.',:u)
                RETURNING id
            """), {"o": org, "c": claim, "u": reviewer}).scalar_one()

        appraisal_a = add_appraisal(org_a, user_a)
        appraisal_b = add_appraisal(org_b, user_b)
        connection.execute(text("""
            INSERT INTO evidence_appraisal_decisions (organization_id,appraisal_id,decision,rationale,reviewer_id)
            VALUES (:o,:a,'accepted','Independent appraisal decision for organization A.',:u)
        """), {"o": org_a, "a": appraisal_a, "u": user_b})
        connection.execute(text("""
            INSERT INTO evidence_appraisal_decisions (organization_id,appraisal_id,decision,rationale,reviewer_id)
            VALUES (:o,:a,'accepted','Independent appraisal decision for organization B.',:u)
        """), {"o": org_b, "a": appraisal_b, "u": user_a})

        pubs = [connection.execute(text("INSERT INTO publications (title) VALUES (:t) RETURNING id"),
                                   {"t": "Duplicate candidate " + str(i) + " " + str(uuid4())}).scalar_one()
                for i in range(4)]
        candidate_a = connection.execute(text("""
            INSERT INTO publication_duplicate_candidates (organization_id,publication_a,publication_b,match_basis)
            VALUES (:o,:a,:b,'manual') RETURNING id
        """), {"o": org_a, "a": pubs[0], "b": pubs[1]}).scalar_one()
        candidate_b = connection.execute(text("""
            INSERT INTO publication_duplicate_candidates (organization_id,publication_a,publication_b,match_basis)
            VALUES (:o,:a,:b,'manual') RETURNING id
        """), {"o": org_b, "a": pubs[2], "b": pubs[3]}).scalar_one()
        connection.execute(text("""
            INSERT INTO publication_duplicate_decisions (organization_id,candidate_id,decision,rationale,reviewer_id)
            VALUES (:o,:c,'not_duplicate','Independent duplicate decision for organization A.',:u)
        """), {"o": org_a, "c": candidate_a, "u": user_b})
        connection.execute(text("""
            INSERT INTO publication_duplicate_decisions (organization_id,candidate_id,decision,rationale,reviewer_id)
            VALUES (:o,:c,'not_duplicate','Independent duplicate decision for organization B.',:u)
        """), {"o": org_b, "c": candidate_b, "u": user_a})

        role = "toolkit_appraisal_rls_test"
        if not connection.execute(text("SELECT EXISTS (SELECT 1 FROM pg_roles WHERE rolname=:r)"), {"r": role}).scalar_one():
            connection.exec_driver_sql(f"CREATE ROLE {role} NOLOGIN NOBYPASSRLS")
        connection.exec_driver_sql("GRANT USAGE ON SCHEMA public TO toolkit_appraisal_rls_test")
        for table in ("evidence_appraisals", "publication_duplicate_candidates"):
            connection.exec_driver_sql(f"GRANT SELECT, INSERT, UPDATE ON {table} TO toolkit_appraisal_rls_test")
        for table in ("evidence_appraisal_decisions", "publication_duplicate_decisions"):
            connection.exec_driver_sql(f"GRANT SELECT, INSERT ON {table} TO toolkit_appraisal_rls_test")

        with connection.begin_nested():
            connection.exec_driver_sql("SET LOCAL ROLE toolkit_appraisal_rls_test")
            connection.execute(text("SELECT set_config('app.organization_id',:o,true)"), {"o": str(org_a)})
            assert set(connection.execute(text("SELECT id FROM evidence_appraisals")).scalars()) == {appraisal_a}
            assert set(connection.execute(text("SELECT appraisal_id FROM evidence_appraisal_decisions")).scalars()) == {appraisal_a}
            assert set(connection.execute(text("SELECT id FROM publication_duplicate_candidates")).scalars()) == {candidate_a}
            assert set(connection.execute(text("SELECT candidate_id FROM publication_duplicate_decisions")).scalars()) == {candidate_a}
            with pytest.raises(Exception):
                with connection.begin_nested():
                    connection.execute(text("""
                        INSERT INTO evidence_appraisals
                        (organization_id,claim_id,study_design,evidence_level,risk_of_bias,replication_status,limitations,appraisal_rationale,reviewer_id)
                        VALUES (:o,:c,'observational_human','clinical_human','some_concerns','single_study','No','Cross-org write must fail.',:u)
                    """), {"o": org_b, "c": claim, "u": user_a})
            with pytest.raises(Exception):
                with connection.begin_nested():
                    connection.execute(text("""
                        INSERT INTO evidence_appraisal_decisions (organization_id,appraisal_id,decision,rationale,reviewer_id)
                        VALUES (:o,:a,'accepted','Cross-org decision must fail.',:u)
                    """), {"o": org_a, "a": appraisal_b, "u": user_a})
            with pytest.raises(Exception):
                with connection.begin_nested():
                    connection.execute(text("""
                        INSERT INTO publication_duplicate_candidates (organization_id,publication_a,publication_b,match_basis)
                        VALUES (:o,:a,:b,'manual')
                    """), {"o": org_b, "a": pubs[0], "b": pubs[1]})
            with pytest.raises(Exception):
                with connection.begin_nested():
                    connection.execute(text("""
                        INSERT INTO publication_duplicate_decisions (organization_id,candidate_id,decision,rationale,reviewer_id)
                        VALUES (:o,:c,'not_duplicate','Cross-org decision must fail.',:u)
                    """), {"o": org_a, "c": candidate_b, "u": user_a})
            connection.execute(text("UPDATE evidence_appraisals SET appraisal_status='accepted' WHERE id=:id"), {"id": appraisal_a})
            connection.execute(text("UPDATE publication_duplicate_candidates SET status='not_duplicate' WHERE id=:id"), {"id": candidate_a})
            connection.execute(text("SELECT set_config('app.organization_id','',true)"))
            assert connection.execute(text("SELECT count(*) FROM evidence_appraisals")).scalar_one() == 0
            assert connection.execute(text("SELECT count(*) FROM evidence_appraisal_decisions")).scalar_one() == 0
            assert connection.execute(text("SELECT count(*) FROM publication_duplicate_candidates")).scalar_one() == 0
            assert connection.execute(text("SELECT count(*) FROM publication_duplicate_decisions")).scalar_one() == 0

        connection.exec_driver_sql("RESET ROLE")
        for table in ("evidence_appraisals", "publication_duplicate_candidates"):
            connection.exec_driver_sql(f"REVOKE SELECT, INSERT, UPDATE ON {table} FROM toolkit_appraisal_rls_test")
        for table in ("evidence_appraisal_decisions", "publication_duplicate_decisions"):
            connection.exec_driver_sql(f"REVOKE SELECT, INSERT ON {table} FROM toolkit_appraisal_rls_test")
        connection.exec_driver_sql("REVOKE USAGE ON SCHEMA public FROM toolkit_appraisal_rls_test")
        connection.exec_driver_sql("DROP ROLE toolkit_appraisal_rls_test")


@pytest.mark.skipif(os.getenv("RUN_POSTGRES_MIGRATION_TESTS") != "1",
                    reason="PostgreSQL curation workflow RLS integration test is enabled in CI only.")
def test_curation_reviews_and_decisions_are_organization_scoped():
    with engine.begin() as connection:
        connection.execute(text("SELECT pg_advisory_xact_lock(731904221067)"))
        apply_development_migrations(connection)
        org_a = connection.execute(text("INSERT INTO organizations (name,organization_type) VALUES (:n,'research_team') RETURNING id"),
                                   {"n": "curation-a-" + str(uuid4())}).scalar_one()
        org_b = connection.execute(text("INSERT INTO organizations (name,organization_type) VALUES (:n,'research_team') RETURNING id"),
                                   {"n": "curation-b-" + str(uuid4())}).scalar_one()
        user_a = connection.execute(text("INSERT INTO user_profiles (display_name,role) VALUES ('Curation A','researcher') RETURNING id")).scalar_one()
        user_b = connection.execute(text("INSERT INTO user_profiles (display_name,role) VALUES ('Curation B','researcher') RETURNING id")).scalar_one()

        def review(org, user):
            return connection.execute(text("""
                INSERT INTO curation_reviews (entity_type,entity_id,review_status,submitted_by,owner_organization_id)
                VALUES ('evidence_claim',:entity,'in_review',:user,:org) RETURNING id
            """), {"entity": uuid4(), "user": user, "org": org}).scalar_one()

        review_a = review(org_a, user_a)
        review_b = review(org_b, user_b)
        decision_a = connection.execute(text("""
            INSERT INTO curation_decisions
            (review_id,owner_organization_id,decision,rationale,reviewer_id,previous_status,new_status)
            VALUES (:review,:org,'verified','Independent curation decision for organization A.',:user,'in_review','verified')
            RETURNING id
        """), {"review": review_a, "org": org_a, "user": user_b}).scalar_one()
        connection.execute(text("""
            INSERT INTO curation_decisions
            (review_id,owner_organization_id,decision,rationale,reviewer_id,previous_status,new_status)
            VALUES (:review,:org,'verified','Independent curation decision for organization B.',:user,'in_review','verified')
        """), {"review": review_b, "org": org_b, "user": user_a})
        with pytest.raises(Exception):
            with connection.begin_nested():
                connection.execute(text("UPDATE curation_decisions SET rationale='attempted mutation' WHERE id=:id"), {"id": decision_a})
        with pytest.raises(Exception):
            with connection.begin_nested():
                connection.execute(text("DELETE FROM curation_decisions WHERE id=:id"), {"id": decision_a})

        role = "toolkit_curation_rls_test"
        if not connection.execute(text("SELECT EXISTS (SELECT 1 FROM pg_roles WHERE rolname=:r)"), {"r": role}).scalar_one():
            connection.exec_driver_sql(f"CREATE ROLE {role} NOLOGIN NOBYPASSRLS")
        connection.exec_driver_sql("GRANT USAGE ON SCHEMA public TO toolkit_curation_rls_test")
        connection.exec_driver_sql("GRANT SELECT, INSERT, UPDATE ON curation_reviews TO toolkit_curation_rls_test")
        connection.exec_driver_sql("GRANT SELECT, INSERT ON curation_decisions TO toolkit_curation_rls_test")

        with connection.begin_nested():
            connection.exec_driver_sql("SET LOCAL ROLE toolkit_curation_rls_test")
            connection.execute(text("SELECT set_config('app.organization_id',:o,true)"), {"o": str(org_a)})
            assert set(connection.execute(text("SELECT id FROM curation_reviews")).scalars()) == {review_a}
            assert set(connection.execute(text("SELECT review_id FROM curation_decisions")).scalars()) == {review_a}

            with pytest.raises(Exception):
                with connection.begin_nested():
                    connection.execute(text("""
                        INSERT INTO curation_reviews (entity_type,entity_id,review_status,submitted_by,owner_organization_id)
                        VALUES ('evidence_claim',:entity,'in_review',:user,:org)
                    """), {"entity": uuid4(), "user": user_a, "org": org_b})
            with pytest.raises(Exception):
                with connection.begin_nested():
                    connection.execute(text("""
                        INSERT INTO curation_decisions
                        (review_id,owner_organization_id,decision,rationale,reviewer_id,previous_status,new_status)
                        VALUES (:review,:org,'verified','Cross-organization decision must fail.',:user,'in_review','verified')
                    """), {"review": review_b, "org": org_a, "user": user_a})

            connection.execute(text("UPDATE curation_reviews SET review_status='verified' WHERE id=:id"), {"id": review_a})
            assert connection.execute(text("UPDATE curation_reviews SET review_status='verified' WHERE id=:id"), {"id": review_b}).rowcount == 0
            connection.execute(text("SELECT set_config('app.organization_id','',true)"))
            assert connection.execute(text("SELECT count(*) FROM curation_reviews")).scalar_one() == 0
            assert connection.execute(text("SELECT count(*) FROM curation_decisions")).scalar_one() == 0

        connection.exec_driver_sql("RESET ROLE")
        connection.exec_driver_sql("REVOKE SELECT, INSERT, UPDATE ON curation_reviews FROM toolkit_curation_rls_test")
        connection.exec_driver_sql("REVOKE SELECT, INSERT ON curation_decisions FROM toolkit_curation_rls_test")
        connection.exec_driver_sql("REVOKE USAGE ON SCHEMA public FROM toolkit_curation_rls_test")
        connection.exec_driver_sql("DROP ROLE toolkit_curation_rls_test")


@pytest.mark.skipif(os.getenv("RUN_POSTGRES_MIGRATION_TESTS") != "1",
                    reason="PostgreSQL agent session RLS integration test is enabled in CI only.")
def test_agent_sessions_and_messages_are_private_to_user_and_organization():
    with engine.begin() as connection:
        connection.execute(text("SELECT pg_advisory_xact_lock(731904221067)"))
        apply_development_migrations(connection)
        org_a = connection.execute(text("INSERT INTO organizations (name,organization_type) VALUES (:n,'research_team') RETURNING id"),
                                   {"n": "agent-a-" + str(uuid4())}).scalar_one()
        org_b = connection.execute(text("INSERT INTO organizations (name,organization_type) VALUES (:n,'research_team') RETURNING id"),
                                   {"n": "agent-b-" + str(uuid4())}).scalar_one()
        user_a = connection.execute(text("INSERT INTO user_profiles (display_name,role) VALUES ('Agent A','researcher') RETURNING id")).scalar_one()
        user_b = connection.execute(text("INSERT INTO user_profiles (display_name,role) VALUES ('Agent B','researcher') RETURNING id")).scalar_one()
        user_c = connection.execute(text("INSERT INTO user_profiles (display_name,role) VALUES ('Agent C','researcher') RETURNING id")).scalar_one()

        def session(org, user, title):
            return connection.execute(text("""
                INSERT INTO agent_sessions (organization_id,user_id,agent_id,title)
                VALUES (:org,:user,'research-assistant',:title) RETURNING id
            """), {"org": org, "user": user, "title": title}).scalar_one()

        session_a = session(org_a, user_a, "User A private session")
        session_b = session(org_a, user_b, "User B private session")
        session_c = session(org_b, user_c, "User C private session")
        def message(session_id, role, content):
            return connection.execute(text("""
                INSERT INTO agent_session_messages (session_id,sender_role,content)
                VALUES (:session,:role,:content) RETURNING id
            """), {"session": session_id, "role": role, "content": content}).scalar_one()

        message_a = message(session_a, "user", "Private message for user A.")
        message_b = message(session_b, "user", "Private message for user B.")
        message_c = message(session_c, "user", "Private message for user C.")

        with pytest.raises(Exception):
            with connection.begin_nested():
                connection.execute(text("UPDATE agent_session_messages SET content='mutated' WHERE id=:id"), {"id": message_a})
        with pytest.raises(Exception):
            with connection.begin_nested():
                connection.execute(text("DELETE FROM agent_session_messages WHERE id=:id"), {"id": message_a})

        role = "toolkit_agent_rls_test"
        if not connection.execute(text("SELECT EXISTS (SELECT 1 FROM pg_roles WHERE rolname=:r)"), {"r": role}).scalar_one():
            connection.exec_driver_sql(f"CREATE ROLE {role} NOLOGIN NOBYPASSRLS")
        connection.exec_driver_sql("GRANT USAGE ON SCHEMA public TO toolkit_agent_rls_test")
        connection.exec_driver_sql("GRANT SELECT, INSERT, UPDATE ON agent_sessions TO toolkit_agent_rls_test")
        connection.exec_driver_sql("GRANT SELECT, INSERT ON agent_session_messages TO toolkit_agent_rls_test")

        with connection.begin_nested():
            connection.exec_driver_sql("SET LOCAL ROLE toolkit_agent_rls_test")
            connection.execute(text("SELECT set_config('app.organization_id',:org,true), set_config('app.user_id',:user,true)"),
                               {"org": str(org_a), "user": str(user_a)})
            assert set(connection.execute(text("SELECT id FROM agent_sessions")).scalars()) == {session_a}
            assert set(connection.execute(text("SELECT session_id FROM agent_session_messages")).scalars()) == {session_a}
            own_new_session = connection.execute(text("""
                INSERT INTO agent_sessions (organization_id,user_id,agent_id,title)
                VALUES (:org,:user,'research-assistant','New session created under RLS')
                RETURNING id
            """), {"org": org_a, "user": user_a}).scalar_one()
            connection.execute(text("""
                INSERT INTO agent_session_messages (session_id,sender_role,content)
                VALUES (:session,'user','Valid user-scoped message.')
            """), {"session": own_new_session})
            assert set(connection.execute(text("SELECT id FROM agent_sessions")).scalars()) == {session_a, own_new_session}
            assert set(connection.execute(text("SELECT session_id FROM agent_session_messages")).scalars()) == {session_a, own_new_session}
            with pytest.raises(Exception):
                with connection.begin_nested():
                    connection.execute(text("""
                        INSERT INTO agent_sessions (organization_id,user_id,agent_id,title)
                        VALUES (:org,:user,'research-assistant','Impersonation attempt')
                    """), {"org": org_a, "user": user_b})
            with pytest.raises(Exception):
                with connection.begin_nested():
                    connection.execute(text("""
                        INSERT INTO agent_session_messages (session_id,sender_role,content)
                        VALUES (:session,'user','Cross-user message attempt.')
                    """), {"session": session_b})
            connection.execute(text("UPDATE agent_sessions SET status='archived' WHERE id=:id"), {"id": session_a})
            assert connection.execute(text("UPDATE agent_sessions SET status='archived' WHERE id=:id"), {"id": session_b}).rowcount == 0

            connection.execute(text("SELECT set_config('app.user_id',:user,true)"), {"user": str(user_b)})
            assert set(connection.execute(text("SELECT id FROM agent_sessions")).scalars()) == {session_b}
            assert set(connection.execute(text("SELECT session_id FROM agent_session_messages")).scalars()) == {session_b}

            connection.execute(text("SELECT set_config('app.organization_id',:org,true), set_config('app.user_id',:user,true)"),
                               {"org": str(org_b), "user": str(user_c)})
            assert set(connection.execute(text("SELECT id FROM agent_sessions")).scalars()) == {session_c}
            assert set(connection.execute(text("SELECT session_id FROM agent_session_messages")).scalars()) == {session_c}

            connection.execute(text("SELECT set_config('app.organization_id','',true), set_config('app.user_id','',true)"))
            assert connection.execute(text("SELECT count(*) FROM agent_sessions")).scalar_one() == 0
            assert connection.execute(text("SELECT count(*) FROM agent_session_messages")).scalar_one() == 0

        connection.exec_driver_sql("RESET ROLE")
        connection.exec_driver_sql("REVOKE SELECT, INSERT, UPDATE ON agent_sessions FROM toolkit_agent_rls_test")
        connection.exec_driver_sql("REVOKE SELECT, INSERT ON agent_session_messages FROM toolkit_agent_rls_test")
        connection.exec_driver_sql("REVOKE USAGE ON SCHEMA public FROM toolkit_agent_rls_test")
        connection.exec_driver_sql("DROP ROLE toolkit_agent_rls_test")


@pytest.mark.skipif(os.getenv("RUN_POSTGRES_MIGRATION_TESTS") != "1",
                    reason="PostgreSQL regulatory guidance RLS integration test is enabled in CI only.")
def test_regulatory_guidance_versions_and_decisions_follow_owner_and_public_verified_scope():
    with engine.begin() as connection:
        connection.execute(text("SELECT pg_advisory_xact_lock(731904221067)"))
        apply_development_migrations(connection)
        org_a = connection.execute(text("INSERT INTO organizations (name,organization_type) VALUES (:n,'research_team') RETURNING id"),
                                   {"n": "regulatory-a-" + str(uuid4())}).scalar_one()
        org_b = connection.execute(text("INSERT INTO organizations (name,organization_type) VALUES (:n,'research_team') RETURNING id"),
                                   {"n": "regulatory-b-" + str(uuid4())}).scalar_one()
        user_a = connection.execute(text("INSERT INTO user_profiles (display_name,role) VALUES ('Regulatory A','researcher') RETURNING id")).scalar_one()
        user_b = connection.execute(text("INSERT INTO user_profiles (display_name,role) VALUES ('Regulatory B','researcher') RETURNING id")).scalar_one()
        source = connection.execute(text("""
            INSERT INTO source_records (source_name,source_identifier,source_url,raw_metadata)
            VALUES ('Regulatory RLS source',:identifier,'https://example.org/regulatory-rls','{}'::jsonb) RETURNING id
        """), {"identifier": str(uuid4())}).scalar_one()

        def guidance(org, user, title, status):
            return connection.execute(text("""
                INSERT INTO regulatory_guidance_records
                (organization_id,authority,jurisdiction,document_type,document_title,scope_summary,
                 source_record_id,review_status,submitted_by)
                VALUES (:org,'Research Authority','Global','guidance',:title,
                        'This summary is a scoped research reference, not a compliance determination.',
                        :source,:status,:user) RETURNING id
            """), {"org": org, "user": user, "title": title, "status": status, "source": source}).scalar_one()

        guidance_a = guidance(org_a, user_a, "Private guidance A " + str(uuid4()), "in_review")
        guidance_b = guidance(org_b, user_b, "Private guidance B " + str(uuid4()), "in_review")
        guidance_public = guidance(org_b, user_b, "Public verified guidance " + str(uuid4()), "verified")
        connection.execute(text("""
            INSERT INTO regulatory_guidance_decisions (guidance_id,organization_id,reviewer_id,decision,rationale)
            VALUES (:guidance,:org,:user,'verified','Organization-scoped guidance review decision A.')
        """), {"guidance": guidance_a, "org": org_a, "user": user_b})
        connection.execute(text("""
            INSERT INTO regulatory_guidance_decisions (guidance_id,organization_id,reviewer_id,decision,rationale)
            VALUES (:guidance,:org,:user,'verified','Organization-scoped guidance review decision B.')
        """), {"guidance": guidance_b, "org": org_b, "user": user_a})

        def version(guidance_id, user, status, suffix):
            return connection.execute(text("""
                INSERT INTO regulatory_guidance_versions
                (guidance_id,version_or_revision,source_url,content_hash,observed_by,observation_note,review_status)
                VALUES (:guidance,:version,:url,:hash,:user,'Observed source version for RLS test.',:status)
                RETURNING id
            """), {"guidance": guidance_id, "version": suffix,
                   "url": "https://example.org/regulatory/" + suffix,
                   "hash": (("c" if suffix == "P1" else suffix[0].lower()) * 64), "user": user, "status": status}).scalar_one()

        version_a = version(guidance_a, user_a, "pending_review", "A1")
        version_b = version(guidance_b, user_b, "pending_review", "B1")
        version_public = version(guidance_public, user_b, "accepted", "P1")

        def event(guidance_id, version_id, user, status):
            return connection.execute(text("""
                INSERT INTO regulatory_change_events
                (guidance_id,new_version_id,change_type,change_summary,submitted_by,status)
                VALUES (:guidance,:version,'new_version','A sufficiently detailed regulatory source change summary.',:user,:status)
                RETURNING id
            """), {"guidance": guidance_id, "version": version_id, "user": user, "status": status}).scalar_one()

        event_a = event(guidance_a, version_a, user_a, "needs_review")
        event_b = event(guidance_b, version_b, user_b, "needs_review")
        event_public = event(guidance_public, version_public, user_b, "published")
        connection.execute(text("""
            INSERT INTO regulatory_change_decisions (event_id,organization_id,reviewer_id,decision,rationale)
            VALUES (:event,:org,:user,'published','Organization-scoped change decision A.')
        """), {"event": event_a, "org": org_a, "user": user_b})
        connection.execute(text("""
            INSERT INTO regulatory_change_decisions (event_id,organization_id,reviewer_id,decision,rationale)
            VALUES (:event,:org,:user,'published','Organization-scoped change decision B.')
        """), {"event": event_b, "org": org_b, "user": user_a})

        role = "toolkit_regulatory_rls_test"
        if not connection.execute(text("SELECT EXISTS (SELECT 1 FROM pg_roles WHERE rolname=:r)"), {"r": role}).scalar_one():
            connection.exec_driver_sql(f"CREATE ROLE {role} NOLOGIN NOBYPASSRLS")
        connection.exec_driver_sql("GRANT USAGE ON SCHEMA public TO toolkit_regulatory_rls_test")
        for table in ("regulatory_guidance_records", "regulatory_guidance_versions", "regulatory_change_events"):
            connection.exec_driver_sql(f"GRANT SELECT, INSERT, UPDATE ON {table} TO toolkit_regulatory_rls_test")
        for table in ("regulatory_guidance_decisions", "regulatory_change_decisions"):
            connection.exec_driver_sql(f"GRANT SELECT, INSERT ON {table} TO toolkit_regulatory_rls_test")

        with connection.begin_nested():
            connection.exec_driver_sql("SET LOCAL ROLE toolkit_regulatory_rls_test")
            connection.execute(text("SELECT set_config('app.organization_id',:org,true)"), {"org": str(org_a)})
            assert set(connection.execute(text("SELECT id FROM regulatory_guidance_records")).scalars()) == {guidance_a, guidance_public}
            assert set(connection.execute(text("SELECT guidance_id FROM regulatory_guidance_decisions")).scalars()) == {guidance_a}
            assert set(connection.execute(text("SELECT id FROM regulatory_guidance_versions")).scalars()) == {version_a, version_public}
            assert set(connection.execute(text("SELECT id FROM regulatory_change_events")).scalars()) == {event_a, event_public}
            assert set(connection.execute(text("SELECT event_id FROM regulatory_change_decisions")).scalars()) == {event_a}

            with pytest.raises(Exception):
                with connection.begin_nested():
                    connection.execute(text("""
                        INSERT INTO regulatory_guidance_records
                        (organization_id,authority,jurisdiction,document_type,document_title,scope_summary,source_record_id,submitted_by)
                        VALUES (:org,'Authority','Global','guidance','Cross-org record',
                                'This cross-org guidance submission must fail under the active tenant context.',:source,:user)
                    """), {"org": org_b, "source": source, "user": user_a})
            with pytest.raises(Exception):
                with connection.begin_nested():
                    connection.execute(text("""
                        INSERT INTO regulatory_guidance_versions
                        (guidance_id,source_url,observed_by,observation_note)
                        VALUES (:guidance,'https://example.org/cross-org-version',:user,'Cross-org version must fail.')
                    """), {"guidance": guidance_b, "user": user_a})
            with pytest.raises(Exception):
                with connection.begin_nested():
                    connection.execute(text("""
                        INSERT INTO regulatory_change_events
                        (guidance_id,new_version_id,change_type,change_summary,submitted_by)
                        VALUES (:guidance,:version,'new_version','Cross-org event must fail with a sufficiently long summary.',:user)
                    """), {"guidance": guidance_b, "version": version_b, "user": user_a})
            with pytest.raises(Exception):
                with connection.begin_nested():
                    connection.execute(text("""
                        INSERT INTO regulatory_guidance_decisions
                        (guidance_id,organization_id,reviewer_id,decision,rationale)
                        VALUES (:guidance,:org,:user,'verified','Cross-org guidance decision must fail.')
                    """), {"guidance": guidance_b, "org": org_a, "user": user_a})
            with pytest.raises(Exception):
                with connection.begin_nested():
                    connection.execute(text("""
                        INSERT INTO regulatory_change_decisions
                        (event_id,organization_id,reviewer_id,decision,rationale)
                        VALUES (:event,:org,:user,'published','Cross-org change decision must fail.')
                    """), {"event": event_b, "org": org_a, "user": user_a})

            connection.execute(text("UPDATE regulatory_guidance_records SET limitations='Owner-only update.' WHERE id=:id"), {"id": guidance_a})
            connection.execute(text("UPDATE regulatory_guidance_versions SET observation_note='Owner-only update.' WHERE id=:id"), {"id": version_a})
            connection.execute(text("UPDATE regulatory_change_events SET impact_assessment='Owner-only update.' WHERE id=:id"), {"id": event_a})
            connection.execute(text("SELECT set_config('app.organization_id','',true)"))
            assert set(connection.execute(text("SELECT id FROM regulatory_guidance_records")).scalars()) == {guidance_public}
            assert set(connection.execute(text("SELECT id FROM regulatory_guidance_versions")).scalars()) == {version_public}
            assert set(connection.execute(text("SELECT id FROM regulatory_change_events")).scalars()) == {event_public}
            assert connection.execute(text("SELECT count(*) FROM regulatory_guidance_decisions")).scalar_one() == 0
            assert connection.execute(text("SELECT count(*) FROM regulatory_change_decisions")).scalar_one() == 0

        connection.exec_driver_sql("RESET ROLE")
        for table in ("regulatory_guidance_records", "regulatory_guidance_versions", "regulatory_change_events"):
            connection.exec_driver_sql(f"REVOKE SELECT, INSERT, UPDATE ON {table} FROM toolkit_regulatory_rls_test")
        for table in ("regulatory_guidance_decisions", "regulatory_change_decisions"):
            connection.exec_driver_sql(f"REVOKE SELECT, INSERT ON {table} FROM toolkit_regulatory_rls_test")
        connection.exec_driver_sql("REVOKE USAGE ON SCHEMA public FROM toolkit_regulatory_rls_test")
        connection.exec_driver_sql("DROP ROLE toolkit_regulatory_rls_test")


@pytest.mark.skipif(os.getenv("RUN_POSTGRES_MIGRATION_TESTS") != "1",
                    reason="PostgreSQL regulatory source scheduler RLS integration test is enabled in CI only.")
def test_regulatory_source_observations_and_poll_runs_are_organization_scoped():
    with engine.begin() as connection:
        connection.execute(text("SELECT pg_advisory_xact_lock(731904221067)"))
        apply_development_migrations(connection)
        org_a = connection.execute(text("INSERT INTO organizations (name,organization_type) VALUES (:n,'research_team') RETURNING id"),
                                   {"n": "reg-source-a-" + str(uuid4())}).scalar_one()
        org_b = connection.execute(text("INSERT INTO organizations (name,organization_type) VALUES (:n,'research_team') RETURNING id"),
                                   {"n": "reg-source-b-" + str(uuid4())}).scalar_one()
        user_a = connection.execute(text("INSERT INTO user_profiles (display_name,role) VALUES ('Reg Source A','researcher') RETURNING id")).scalar_one()
        user_b = connection.execute(text("INSERT INTO user_profiles (display_name,role) VALUES ('Reg Source B','researcher') RETURNING id")).scalar_one()

        def source(org, user, label):
            return connection.execute(text("""
                INSERT INTO regulatory_source_registry
                (organization_id,authority,jurisdiction,source_name,source_type,feed_url,official_domain,description,created_by)
                VALUES (:org,'Research Authority','Global',:name,'rss',:url,'example.org','Test source registry row.',:user)
                RETURNING id
            """), {"org": org, "user": user, "name": label + " source",
                   "url": "https://example.org/" + label + "/" + str(uuid4())}).scalar_one()

        source_a = source(org_a, user_a, "a")
        source_b = source(org_b, user_b, "b")
        run_a = connection.execute(text("""
            INSERT INTO regulatory_source_poll_runs (organization_id,source_id,trigger_type,status,finished_at)
            VALUES (:org,:source,'manual','success',now()) RETURNING id
        """), {"org": org_a, "source": source_a}).scalar_one()
        run_b = connection.execute(text("""
            INSERT INTO regulatory_source_poll_runs (organization_id,source_id,trigger_type,status,finished_at)
            VALUES (:org,:source,'manual','success',now()) RETURNING id
        """), {"org": org_b, "source": source_b}).scalar_one()
        observation_a = connection.execute(text("""
            INSERT INTO regulatory_source_observations
            (organization_id,source_id,external_identifier,item_title,item_url,content_hash,raw_metadata)
            VALUES (:org,:source,:external,'Source A update','https://example.org/a-update',:hash,'{}'::jsonb)
            RETURNING id
        """), {"org": org_a, "source": source_a, "external": str(uuid4()), "hash": "a" * 64}).scalar_one()
        observation_b = connection.execute(text("""
            INSERT INTO regulatory_source_observations
            (organization_id,source_id,external_identifier,item_title,item_url,content_hash,raw_metadata)
            VALUES (:org,:source,:external,'Source B update','https://example.org/b-update',:hash,'{}'::jsonb)
            RETURNING id
        """), {"org": org_b, "source": source_b, "external": str(uuid4()), "hash": "b" * 64}).scalar_one()

        role = "toolkit_reg_source_rls_test"
        if not connection.execute(text("SELECT EXISTS (SELECT 1 FROM pg_roles WHERE rolname=:r)"), {"r": role}).scalar_one():
            connection.exec_driver_sql(f"CREATE ROLE {role} NOLOGIN NOBYPASSRLS")
        connection.exec_driver_sql("GRANT USAGE ON SCHEMA public TO toolkit_reg_source_rls_test")
        for table in ("regulatory_source_observations", "regulatory_source_poll_runs"):
            connection.exec_driver_sql(f"GRANT SELECT, INSERT, UPDATE ON {table} TO toolkit_reg_source_rls_test")

        with connection.begin_nested():
            connection.exec_driver_sql("SET LOCAL ROLE toolkit_reg_source_rls_test")
            connection.execute(text("SELECT set_config('app.organization_id',:org,true)"), {"org": str(org_a)})
            assert set(connection.execute(text("SELECT id FROM regulatory_source_poll_runs")).scalars()) == {run_a}
            assert set(connection.execute(text("SELECT id FROM regulatory_source_observations")).scalars()) == {observation_a}
            with pytest.raises(Exception):
                with connection.begin_nested():
                    connection.execute(text("""
                        INSERT INTO regulatory_source_poll_runs (organization_id,source_id,trigger_type,status,finished_at)
                        VALUES (:org,:source,'manual','success',now())
                    """), {"org": org_b, "source": source_b})
            with pytest.raises(Exception):
                with connection.begin_nested():
                    connection.execute(text("""
                        INSERT INTO regulatory_source_observations
                        (organization_id,source_id,external_identifier,item_title,item_url,content_hash,raw_metadata)
                        VALUES (:org,:source,:external,'Cross-tenant item','https://example.org/cross',:hash,'{}'::jsonb)
                    """), {"org": org_b, "source": source_b, "external": str(uuid4()), "hash": "c" * 64})
            connection.execute(text("UPDATE regulatory_source_poll_runs SET status='error',finished_at=now() WHERE id=:id"), {"id": run_a})
            connection.execute(text("UPDATE regulatory_source_observations SET review_status='accepted' WHERE id=:id"), {"id": observation_a})
            connection.execute(text("SELECT set_config('app.organization_id','',true)"))
            assert connection.execute(text("SELECT count(*) FROM regulatory_source_poll_runs")).scalar_one() == 0
            assert connection.execute(text("SELECT count(*) FROM regulatory_source_observations")).scalar_one() == 0

        connection.exec_driver_sql("RESET ROLE")
        for table in ("regulatory_source_observations", "regulatory_source_poll_runs"):
            connection.exec_driver_sql(f"REVOKE SELECT, INSERT, UPDATE ON {table} FROM toolkit_reg_source_rls_test")
        connection.exec_driver_sql("REVOKE USAGE ON SCHEMA public FROM toolkit_reg_source_rls_test")
        connection.exec_driver_sql("DROP ROLE toolkit_reg_source_rls_test")
