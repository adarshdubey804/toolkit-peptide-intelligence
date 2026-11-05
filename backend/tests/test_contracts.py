from pathlib import Path
import asyncio

from app.integrations.clinicaltrials import normalize_study
from app.integrations.chembl import normalize_peptide_biotherapeutic
from app.integrations.dailymed import extract_mechanism_of_action, normalize_spl
from app.integrations.dbaasp import DbaaspProvider, normalize_peptide
from app.integrations.fda_drugsfda import normalize_application
from app.integrations.fda_purple_book import discover_latest_csv_url, normalize_product as normalize_purple_book_product, parse_purple_book_csv
from app.integrations.ema_article57 import parse_article57_workbook
from app.integrations.gtopdb import GtoPdbProvider, normalize_ligand
from app.integrations.dramp import discover_fasta_downloads, merge_records, parse_fasta_records
from app.integrations.health_canada_dpd import normalize_product
from app.main import MIGRATIONS_DIR, app


def test_vendor_material_traceability_routes_are_registered_and_bounded():
    paths = app.openapi()["paths"]
    assert "/api/v1/vendor-materials/offerings" in paths
    assert "/api/v1/vendor-materials/mine/offerings" in paths
    assert "get" in paths["/api/v1/vendor-materials/mine/offerings"]
    assert "get" in paths["/api/v1/vendor-materials/offerings"]
    assert "post" in paths["/api/v1/vendor-materials/offerings"]
    assert "/api/v1/vendor-materials/offerings/{offering_id}/batches" in paths
    assert "post" in paths["/api/v1/vendor-materials/offerings/{offering_id}/batches"]
    assert "/api/v1/vendor-materials/batches/{batch_id}/test-results" in paths
    assert "post" in paths["/api/v1/vendor-materials/batches/{batch_id}/test-results"]
    assert "/api/v1/vendor-materials/reviews/{record_type}/{record_id}/decisions" in paths
    decision = paths["/api/v1/vendor-materials/reviews/{record_type}/{record_id}/decisions"]["post"]
    assert decision["requestBody"]["required"] is True


def test_batch_result_request_requires_reported_observation():
    from app.routers.vendor_materials import BatchTestResultSubmission
    import pytest
    base = {
        "test_id": "00000000-0000-0000-0000-000000000001",
        "method_id": "00000000-0000-0000-0000-000000000002",
        "source_name": "Vendor report",
        "source_identifier": "REPORT-1",
        "source_url": "https://example.org/report/1",
        "evidence_scope": "Certificate of analysis for a specific supplier lot.",
    }
    with pytest.raises(Exception):
        BatchTestResultSubmission(**base)
    valid = BatchTestResultSubmission(**base, observed_text="Reported purity: 98.2%")
    assert valid.observed_text == "Reported purity: 98.2%"


def test_vendor_material_review_scope_is_explicit():
    from app.routers.vendor_materials import MaterialDecision
    decision = MaterialDecision(
        decision="verified",
        rationale="Reviewed against the source report and verified the identity and provenance.",
        visibility_scope="public",
    )
    assert decision.visibility_scope == "public"


def test_health_and_readiness_routes_are_registered():
    paths = app.openapi()["paths"]
    assert "/health" in paths
    assert "/ready" in paths


def test_peptide_catalogue_contract_is_registered():
    paths = app.openapi()["paths"]
    assert "/api/v1/peptides" in paths
    assert "get" in paths["/api/v1/peptides"]
    assert "/api/v1/peptides/{peptide_id}" in paths


def test_search_pagination_constraints_are_documented():
    operation = app.openapi()["paths"]["/api/v1/peptides"]["get"]
    params = {item["name"]: item for item in operation["parameters"]}
    assert params["limit"]["schema"]["maximum"] == 100
    assert params["limit"]["schema"]["minimum"] == 1
    assert params["offset"]["schema"]["minimum"] == 0


def test_pubmed_discovery_is_registered_and_bounded():
    operation = app.openapi()["paths"]["/api/v1/research/pubmed"]["get"]
    params = {item["name"]: item for item in operation["parameters"]}
    assert params["limit"]["schema"]["maximum"] == 20
    assert params["limit"]["schema"]["minimum"] == 1


def test_clinical_trials_discovery_is_registered_and_bounded():
    operation = app.openapi()["paths"]["/api/v1/research/clinicaltrials"]["get"]
    params = {item["name"]: item for item in operation["parameters"]}
    assert params["limit"]["schema"]["maximum"] == 20
    assert params["limit"]["schema"]["minimum"] == 1
    assert "page_token" in params


def test_uniprot_rcsb_pubchem_routes_are_registered_and_bounded():
    paths = app.openapi()["paths"]
    for route in (
        "/api/v1/research/uniprot",
        "/api/v1/research/rcsb",
        "/api/v1/research/pubchem",
    ):
        assert "get" in paths[route]
    for route in ("/api/v1/research/uniprot", "/api/v1/research/rcsb"):
        params = {item["name"]: item for item in paths[route]["get"]["parameters"]}
        assert params["limit"]["schema"]["maximum"] == 20
        assert params["limit"]["schema"]["minimum"] == 1


def test_peptide_profile_requires_uuid_path_parameter():
    operation = app.openapi()["paths"]["/api/v1/peptides/{peptide_id}"]["get"]
    parameter = next(item for item in operation["parameters"] if item["name"] == "peptide_id")
    assert parameter["schema"]["format"] == "uuid"


def test_clinical_trials_normalization_preserves_source_and_evidence_state():
    sample = {
        "protocolSection": {
            "identificationModule": {"nctId": "NCT01234567", "briefTitle": "Example study"},
            "statusModule": {"overallStatus": "RECRUITING", "startDateStruct": {"date": "2025-01"}},
            "designModule": {"studyType": "INTERVENTIONAL", "phases": ["PHASE2"]},
            "sponsorCollaboratorsModule": {"leadSponsor": {"name": "Example sponsor"}},
            "descriptionModule": {"briefSummary": "Example summary"},
            "conditionsModule": {"conditions": ["Condition A"]},
            "armsInterventionsModule": {"interventions": [{"name": "Peptide X", "type": "DRUG"}]},
        }
    }
    result = normalize_study(sample)
    assert result["nct_id"] == "NCT01234567"
    assert result["overall_status"] == "RECRUITING"
    assert result["interventions"] == [{"name": "Peptide X", "type": "DRUG"}]
    assert result["curation_status"] == "not_reviewed"


def test_provenance_migration_is_present_and_applied_in_development_order():
    migrations = sorted(path.name for path in MIGRATIONS_DIR.glob("*.sql"))
    assert migrations == ["001_initial_schema.sql", "002_provenance_curation.sql", "003_authentication.sql", "004_organization_workspaces.sql", "005_curation_workflow.sql", "006_enrichment_candidates.sql", "007_vendor_directory.sql", "008_analytical_method_intelligence.sql", "009_formulation_stability_intelligence.sql", "010_process_development_intelligence.sql", "011_molecular_interaction_intelligence.sql", "012_agent_sessions.sql", "013_evidence_intelligence.sql", "014_regulatory_guidance_intelligence.sql", "015_regulatory_change_monitoring.sql", "016_regulatory_observation_integrity.sql", "017_regulatory_source_registry.sql", "018_enrichment_ingestion_runs.sql", "019_regulatory_source_observations.sql", "020_regulatory_poll_scheduler.sql", "021_evidence_review_decisions.sql", "022_structured_evidence_extraction.sql", "023_extracted_evidence_field_review.sql", "024_peptide_analytical_method_applicability.sql", "025_vendor_certification_verification.sql", "026_vendor_service_review.sql", "027_vendor_service_evidence_links.sql", "028_vendor_facility_verification.sql", "029_vendor_service_facility_link.sql", "030_vendor_certification_submitter.sql", "031_laboratory_capability_claims.sql", "032_analytical_test_catalogue.sql", "033_analytical_test_catalogue_curation.sql", "034_peptide_test_applicability.sql", "035_analytical_reference_framework_crosswalk.sql", "036_shared_api_rate_limiting.sql", "037_tamper_evident_audit_trail.sql", "038_explicit_record_ownership.sql", "039_canonical_peptide_chemical_forms.sql", "040_chemical_form_applicability_links.sql", "041_interaction_and_decision_ownership.sql", "042_vendor_material_batch_traceability.sql", "043_vendor_material_visibility_review.sql", "044_vendor_material_row_level_security.sql", "045_analytical_method_row_level_security.sql", "046_claim_source_citation_locators.sql", "047_formulation_process_row_level_security.sql", "048_molecular_interaction_row_level_security.sql", "049_evidence_appraisal_row_level_security.sql", "050_curation_workflow_row_level_security.sql", "051_agent_session_user_row_level_security.sql", "052_regulatory_guidance_row_level_security.sql", "053_regulatory_source_scheduler_row_level_security.sql", "054_vendor_identity_site_certification_row_level_security.sql", "055_evidence_claim_revision_history.sql", "056_extraction_source_record_provenance.sql", "057_extraction_artifact_row_level_security.sql", "058_enrichment_artifact_row_level_security.sql", "059_vendor_service_evidence_row_level_security.sql", "060_laboratory_capability_row_level_security.sql", "061_peptide_applicability_row_level_security.sql", "062_analytical_test_catalogue_decision_row_level_security.sql", "063_audit_event_row_level_security.sql", "064_regulatory_source_registry_row_level_security.sql", "065_peptide_chemical_form_revision_history.sql", "066_product_level_regulatory_authorizations.sql", "067_peptide_mechanism_of_action.sql", "068_global_peptide_discovery_registry.sql", "069_bpc157_fda_source_candidate_seed.sql", "070_bpc157_pubmed_mechanism_evidence.sql", "071_peptide_workbook_imports.sql", "072_editable_dossier_sections_and_media.sql"]
    sql = (MIGRATIONS_DIR / "002_provenance_curation.sql").read_text(encoding="utf-8")
    assert "source_record_versions" in sql
    assert "external_entity_links" in sql
    assert "curation_reviews" in sql
    assert "curation_decisions" in sql


from datetime import datetime, timezone

import pytest

from app.services.provenance import (
    build_source_envelope,
    canonicalize_source_url,
    stable_content_hash,
)


def test_source_url_canonicalization_removes_fragment_and_default_port():
    assert canonicalize_source_url("HTTPS://Example.ORG:443/a?b=1#section") == "https://example.org/a?b=1"


def test_source_url_rejects_relative_urls_and_embedded_credentials():
    with pytest.raises(ValueError):
        canonicalize_source_url("/relative/path")
    with pytest.raises(ValueError):
        canonicalize_source_url("https://user:secret@example.org/record")


def test_content_hash_is_stable_across_mapping_key_order():
    assert stable_content_hash({"a": 1, "b": 2}) == stable_content_hash({"b": 2, "a": 1})
    assert len(stable_content_hash({"a": 1})) == 64


def test_source_envelope_preserves_provenance_and_unreviewed_state():
    timestamp = datetime(2026, 10, 31, 12, 0, tzinfo=timezone.utc)
    payload = {"accession": "P12345", "sequence_length": 42}
    envelope = build_source_envelope(
        source_name="UniProtKB",
        source_identifier="P12345",
        source_url="https://www.uniprot.org/uniprotkb/P12345/entry#sequence",
        payload=payload,
        retrieved_at=timestamp,
        source_version="release-2026_04",
    )
    assert envelope["source_url"] == "https://www.uniprot.org/uniprotkb/P12345/entry"
    assert envelope["retrieved_at"] == "2026-10-31T12:00:00+00:00"
    assert envelope["content_hash"] == stable_content_hash(payload)
    assert envelope["raw_payload"] == payload
    assert envelope["curation_status"] == "not_reviewed"


def test_source_envelope_requires_timezone_aware_timestamp_and_identifiers():
    with pytest.raises(ValueError):
        build_source_envelope(
            source_name="PubMed",
            source_identifier="123",
            source_url="https://pubmed.ncbi.nlm.nih.gov/123/",
            payload={},
            retrieved_at=datetime(2026, 10, 31),
        )
    with pytest.raises(ValueError):
        build_source_envelope(
            source_name=" ",
            source_identifier="",
            source_url="https://example.org/record",
            payload={},
        )


def test_verified_peptide_knowledge_graph_route_is_registered():
    paths = app.openapi()["paths"]
    route = "/api/v1/peptides/{peptide_id}/graph"
    assert route in paths
    assert "get" in paths[route]
    parameter = next(item for item in paths[route]["get"]["parameters"] if item["name"] == "peptide_id")
    assert parameter["schema"]["format"] == "uuid"


def test_unified_research_workspace_route_is_registered_and_bounded():
    operation = app.openapi()["paths"]["/api/v1/research/workspace"]["get"]
    params = {item["name"]: item for item in operation["parameters"]}
    assert params["q"]["schema"]["minLength"] == 3
    assert params["q"]["schema"]["maxLength"] == 200
    assert params["limit"]["schema"]["minimum"] == 1
    assert params["limit"]["schema"]["maximum"] == 10


def test_research_assistant_brief_route_is_registered_and_bounded():
    operation = app.openapi()["paths"]["/api/v1/research/assistant/brief"]["get"]
    params = {item["name"]: item for item in operation["parameters"]}
    assert params["question"]["schema"]["minLength"] == 8
    assert params["question"]["schema"]["maxLength"] == 500
    assert params["limit"]["schema"]["minimum"] == 1
    assert params["limit"]["schema"]["maximum"] == 10



def test_ai_synthesis_is_opt_in_and_development_guarded():
    operation = app.openapi()["paths"]["/api/v1/research/assistant/synthesize"]["post"]
    assert operation["requestBody"]["required"] is True
    schema = operation["requestBody"]["content"]["application/json"]["schema"]
    assert schema["$ref"].endswith("AssistantSynthesisRequest")
    assert "citations" not in schema.get("properties", {})
    from app.config import settings
    assert settings.ai_synthesis_enabled is False


def test_ai_synthesis_service_rejects_untrusted_or_invalid_source_urls():
    from app.services.ai_synthesis import _safe_citations
    records = _safe_citations([
        {"citation_id": "pubmed:1", "url": "https://pubmed.ncbi.nlm.nih.gov/1/", "title": "Valid"},
        {"citation_id": "fake:2", "url": "http://example.org/2", "title": "Insecure"},
        {"citation_id": "fake:3", "url": "javascript:alert(1)", "title": "Invalid"},
    ])
    assert len(records) == 1
    assert records[0]["citation_id"] == "pubmed:1"


def test_pubmed_abstract_parser_handles_structured_sections():
    from app.integrations.pubmed import parse_pubmed_abstracts
    xml = """<PubmedArticleSet><PubmedArticle><MedlineCitation><PMID>12345</PMID><Article><Abstract><AbstractText Label="BACKGROUND">Context.</AbstractText><AbstractText Label="METHODS">Approach.</AbstractText></Abstract></Article></MedlineCitation></PubmedArticle></PubmedArticleSet>"""
    parsed = parse_pubmed_abstracts(xml)
    assert parsed["12345"] == "BACKGROUND: Context.\nMETHODS: Approach."


def test_pubmed_abstract_parser_allows_records_without_abstracts():
    from app.integrations.pubmed import parse_pubmed_abstracts
    assert parse_pubmed_abstracts("<PubmedArticleSet><PubmedArticle><MedlineCitation><PMID>9</PMID></MedlineCitation></PubmedArticle></PubmedArticleSet>") == {}


def test_authentication_routes_and_password_schema_are_registered():
    paths = app.openapi()["paths"]
    assert "/api/v1/auth/register" in paths
    assert "/api/v1/auth/login" in paths
    assert "/api/v1/auth/me" in paths
    assert "post" in paths["/api/v1/auth/register"]
    auth_sql = (MIGRATIONS_DIR / "003_authentication.sql").read_text(encoding="utf-8")
    assert "password_hash" in auth_sql
    assert "uq_user_profiles_email_lower" in auth_sql
    assert "is_active" in auth_sql


def test_auth_registration_requires_long_password_and_valid_email():
    from app.routers.auth import RegisterRequest
    import pytest
    with pytest.raises(Exception):
        RegisterRequest(email="not-an-email", password="short", display_name="Test User", organization_name="Test Lab")
    with pytest.raises(Exception):
        RegisterRequest(email="test@example.org", password="short", display_name="Test User", organization_name="Test Lab")


def test_organization_workspace_routes_and_membership_migration_are_registered():
    paths = app.openapi()["paths"]
    assert "/api/v1/organizations/me" in paths
    assert "/api/v1/organizations/members" in paths
    assert "/api/v1/organizations/members/{user_id}/role" in paths
    assert "/api/v1/organizations/projects" in paths
    sql = (MIGRATIONS_DIR / "004_organization_workspaces.sql").read_text(encoding="utf-8")
    assert "organization_memberships" in sql
    assert "research_projects" in sql
    assert "project_memberships" in sql


def test_project_visibility_and_role_update_are_constrained():
    from app.routers.organizations import ProjectCreate, RoleUpdate
    import pytest
    with pytest.raises(Exception):
        ProjectCreate(name="Valid project", visibility="public")
    with pytest.raises(Exception):
        RoleUpdate(role="superadmin")


def test_curation_review_and_decision_routes_are_registered():
    paths = app.openapi()["paths"]
    assert "/api/v1/curation/reviews" in paths
    assert "post" in paths["/api/v1/curation/reviews"]
    assert "get" in paths["/api/v1/curation/reviews"]
    assert "/api/v1/curation/reviews/{review_id}/assignment" in paths
    assert "/api/v1/curation/reviews/{review_id}/decisions" in paths


def test_curation_workflow_enforces_role_and_decision_contracts():
    from app.routers.curation import CurationDecision, ReviewSubmission
    import pytest
    with pytest.raises(Exception):
        ReviewSubmission(entity_type="vendor", entity_id="00000000-0000-0000-0000-000000000001")
    with pytest.raises(Exception):
        CurationDecision(decision="approved", rationale="This is a sufficiently long rationale.")
    with pytest.raises(Exception):
        CurationDecision(decision="verified", rationale="too short")


def test_curation_decision_history_is_database_append_only():
    sql = (MIGRATIONS_DIR / "005_curation_workflow.sql").read_text(encoding="utf-8")
    assert "BEFORE UPDATE OR DELETE ON curation_decisions" in sql
    assert "append-only" in sql


def test_curation_verification_requires_original_source_url():
    from app.routers import curation
    source = Path(curation.__file__).read_text(encoding="utf-8")
    assert "Verification requires at least one linked source" in source
    assert "source_url IS NOT NULL" in source


def test_peptide_dossier_submission_contract_is_registered():
    operation = app.openapi()["paths"]["/api/v1/dossiers"]["post"]
    assert operation["responses"]["201"]
    schema = operation["requestBody"]["content"]["application/json"]["schema"]
    assert schema["$ref"].endswith("PeptideDossierCreate")


def test_peptide_dossier_input_bounds_and_scientific_enums():
    from app.routers.dossiers import PeptideDossierCreate, ChemistryInput
    import pytest
    base = {
        "preferred_name": "Example peptide",
        "source_name": "PubMed",
        "source_url": "https://pubmed.ncbi.nlm.nih.gov/123456/",
    }
    record = PeptideDossierCreate(**base)
    assert record.intended_use_class == "unspecified"
    with pytest.raises(Exception):
        PeptideDossierCreate(**{**base, "intended_use_class": "clinical_prescription"})
    with pytest.raises(Exception):
        ChemistryInput(average_molecular_mass=-1)
    with pytest.raises(Exception):
        PeptideDossierCreate(**{**base, "source_url": "javascript:alert(1)"})


def test_dossier_submission_creates_review_queue_record_and_keeps_children_unverified():
    from app.routers import dossiers
    source = Path(dossiers.__file__).read_text(encoding="utf-8")
    assert "'in_review'" in source
    assert "INSERT INTO curation_reviews" in source
    assert "INSERT INTO claim_sources" in source
    assert "publicly visible until verified" in source


def test_curation_queue_includes_source_context_for_reviewer_inspection():
    from app.routers import curation
    source = Path(curation.__file__).read_text(encoding="utf-8")
    assert "record_label" in source
    assert "source_url" in source
    assert "LEFT JOIN source_records sr" in source


def test_peptide_enrichment_route_is_authenticated_and_registered():
    operation = app.openapi()["paths"]["/api/v1/enrichment/peptides/{peptide_id}"]["get"]
    assert operation["security"]
    parameter = next(item for item in operation["parameters"] if item["name"] == "peptide_id")
    assert parameter["schema"]["format"] == "uuid"


def test_enrichment_discovery_is_read_only_and_source_governed():
    from app.routers.enrichment import ALLOWED_ROLES
    from pathlib import Path

    source = (Path(__file__).parents[1] / "app" / "routers" / "enrichment.py").read_text(encoding="utf-8")
    assert ALLOWED_ROLES == {"organization_admin", "curator", "reviewer", "researcher"}
    assert "curation_status\": \"not_reviewed\"" in source
    assert "No peptide, sequence, target, pathway, structure or evidence record was created or modified." in source
    discovery_source = source.split("import hashlib", 1)[0]
    assert "INSERT INTO" not in discovery_source
    assert "UPDATE " not in discovery_source


def test_enrichment_candidate_review_routes_and_migration_are_registered():
    paths = app.openapi()["paths"]
    assert "/api/v1/enrichment/peptides/{peptide_id}/candidates" in paths
    assert "post" in paths["/api/v1/enrichment/peptides/{peptide_id}/candidates"]
    assert "/api/v1/enrichment/candidates" in paths
    assert "get" in paths["/api/v1/enrichment/candidates"]
    assert "/api/v1/enrichment/candidates/{candidate_id}/decisions" in paths
    assert "post" in paths["/api/v1/enrichment/candidates/{candidate_id}/decisions"]
    sql = (MIGRATIONS_DIR / "006_enrichment_candidates.sql").read_text(encoding="utf-8")
    assert "enrichment_candidates" in sql
    assert "enrichment_candidate_decisions" in sql
    assert "prevent_enrichment_decision_mutation" in sql


def test_enrichment_candidate_submission_restricts_official_source_domains():
    from app.routers.enrichment import SOURCE_HOSTS, _validated_source_url
    assert _validated_source_url("PubMed", "https://pubmed.ncbi.nlm.nih.gov/123/").startswith("https://")
    with pytest.raises(Exception):
        _validated_source_url("PubMed", "https://fake-pubmed.example/123")
    with pytest.raises(Exception):
        _validated_source_url("PubMed", "http://pubmed.ncbi.nlm.nih.gov/123/")
    assert {"PubMed", "ClinicalTrials.gov", "UniProtKB", "RCSB PDB", "PubChem"} <= set(SOURCE_HOSTS)


def test_vendor_directory_routes_and_migration_are_registered():
    paths = app.openapi()["paths"]
    assert "/api/v1/vendors" in paths
    assert "get" in paths["/api/v1/vendors"]
    assert "post" in paths["/api/v1/vendors"]
    assert "/api/v1/vendors/{vendor_id}/services" in paths
    assert "/api/v1/vendors/{vendor_id}/certifications" in paths
    assert "/api/v1/vendors/my-submissions" in paths
    assert "get" in paths["/api/v1/vendors/my-submissions"]
    assert "/api/v1/vendors/reviews" in paths
    assert "/api/v1/vendors/{vendor_id}/decisions" in paths
    sql = (MIGRATIONS_DIR / "007_vendor_directory.sql").read_text(encoding="utf-8")
    assert "vendor_sources" in sql
    assert "vendor_review_decisions" in sql
    assert "prevent_vendor_review_decision_mutation" in sql


def test_vendor_source_requires_https_and_credentials_are_rejected():
    from app.routers.vendors import _source_host
    assert _source_host("https://example.org/vendor") == "https://example.org/vendor"
    with pytest.raises(Exception):
        _source_host("http://example.org/vendor")
    with pytest.raises(Exception):
        _source_host("https://user:password@example.org/vendor")


def test_analytical_method_routes_and_review_migration_are_registered():
    paths = app.openapi()["paths"]
    assert "/api/v1/analytical-methods" in paths
    assert "get" in paths["/api/v1/analytical-methods"]
    assert "post" in paths["/api/v1/analytical-methods"]
    assert "/api/v1/analytical-methods/reviews" in paths
    assert "/api/v1/analytical-methods/{method_id}/decisions" in paths
    sql = (MIGRATIONS_DIR / "008_analytical_method_intelligence.sql").read_text(encoding="utf-8")
    assert "analytical_method_sources" in sql
    assert "analytical_method_decisions" in sql
    assert "prevent_analytical_method_decision_mutation" in sql


def test_method_curation_is_separate_from_validation_status():
    from app.routers.analytical_methods import MethodSubmission
    payload = MethodSubmission(
        method_name="Example peptide identity method",
        method_category="mass_spectrometry",
        scientific_principle="Mass-to-charge ratio measurement supports molecular characterization.",
        intended_purpose="Research identity characterization of peptide samples.",
        applicable_materials=["synthetic peptide"],
        method_classification="published",
        validation_status="not_assessed",
        limitations="Matrix effects and instrument configuration may affect interpretation.",
        source_name="Example Journal",
        source_identifier="doi:10.example/method",
        source_url="https://example.org/method",
        evidence_scope="Describes the analytical principle and research application.",
    )
    assert payload.validation_status == "not_assessed"


def test_formulation_routes_and_migration_are_registered():
    paths = app.openapi()["paths"]
    assert "/api/v1/formulations" in paths
    assert "get" in paths["/api/v1/formulations"]
    assert "post" in paths["/api/v1/formulations"]
    assert "/api/v1/formulations/reviews" in paths
    assert "/api/v1/formulations/{formulation_id}/decisions" in paths
    sql = (MIGRATIONS_DIR / "009_formulation_stability_intelligence.sql").read_text(encoding="utf-8")
    assert "formulation_profiles" in sql
    assert "formulation_components" in sql
    assert "formulation_stability_observations" in sql
    assert "formulation_review_decisions" in sql
    assert "prevent_formulation_review_decision_mutation" in sql


def test_formulation_submission_keeps_evidence_and_validation_boundaries():
    from app.routers.formulations import FormulationSubmission
    payload = FormulationSubmission(
        formulation_name="Published research formulation context",
        formulation_type="aqueous_solution",
        intended_research_context="Literature-described formulation research context.",
        formulation_rationale="A source-linked description of the formulation rationale and relevant scientific evidence.",
        limitations="Published results may not generalize across peptide sequences or container systems.",
        sources=[{
            "source_name": "Example Journal",
            "source_identifier": "doi:10.example/formulation",
            "source_url": "https://example.org/formulation",
            "evidence_scope": "Supports the formulation context described."
        }],
    )
    assert payload.development_stage == "research"
    assert payload.stability_observations == []


def test_process_knowledge_routes_and_schema_contract():
    paths = app.openapi()["paths"]
    assert "/api/v1/process-knowledge" in paths
    assert "get" in paths["/api/v1/process-knowledge"]
    assert "post" in paths["/api/v1/process-knowledge"]
    assert "/api/v1/process-knowledge/reviews" in paths
    assert "/api/v1/process-knowledge/{profile_id}/decisions" in paths
    sql = (MIGRATIONS_DIR / "010_process_development_intelligence.sql").read_text(encoding="utf-8")
    for table in ("process_knowledge_profiles", "process_knowledge_stages", "process_knowledge_sources", "process_knowledge_decisions"):
        assert table in sql
    assert "prevent_process_knowledge_decision_mutation" in sql


def test_process_submission_requires_sources_and_limits_stage_categories():
    from app.routers.process_knowledge import ProcessSubmission
    payload = ProcessSubmission(
        profile_title="Published SPPS process-development overview",
        process_platform="solid_phase_peptide_synthesis",
        development_context="Literature overview for research process-development context.",
        process_overview="Descriptive review of process stages, quality attributes and known development considerations.",
        limitations="Not a manufacturing instruction or validated process parameter set.",
        sources=[{"source_name":"Journal","source_identifier":"doi:10.example/peptide",
                  "source_url":"https://example.org/article","evidence_scope":"Supports the overview."}]
    )
    assert payload.stages == []
    assert payload.process_platform == "solid_phase_peptide_synthesis"


def test_bioinformatics_routes_and_sequence_validation_contract():
    paths = app.openapi()["paths"]
    assert "/api/v1/bioinformatics/analyze" in paths
    assert "/api/v1/bioinformatics/align" in paths
    analyze = paths["/api/v1/bioinformatics/analyze"]["post"]["requestBody"]["content"]["application/json"]["schema"]
    assert analyze["$ref"].endswith("/SequenceRequest")
    from app.routers.bioinformatics import SequenceRequest, AlignmentRequest, analyze_sequence, align_sequences
    with pytest.raises(Exception):
        SequenceRequest(sequence="ACD-X")
    result = analyze_sequence(SequenceRequest(sequence="ACDE"))
    assert result["sequence_length"] == 4
    assert result["calculation_status"] == "computed_estimate"
    assert result["molecular_weight_da_average"] > 400
    alignment = align_sequences(AlignmentRequest(sequence_a="ACDE", sequence_b="ACDF"))
    assert alignment["identity_percent"] == 75.0
    assert alignment["method"].startswith("Needleman-Wunsch")


def test_alphafold_structure_discovery_route_is_registered_and_bounded():
    operation = app.openapi()["paths"]["/api/v1/research/alphafold"]["get"]
    params = {item["name"]: item for item in operation["parameters"]}
    assert params["accession"]["schema"]["minLength"] == 3
    assert params["accession"]["schema"]["maxLength"] == 20


def test_structure_discovery_workspace_is_registered():
    paths = app.openapi()["paths"]
    assert "/api/v1/research/rcsb" in paths
    assert "/api/v1/research/alphafold" in paths
    assert "get" in paths["/api/v1/research/alphafold"]


def test_molecular_interaction_routes_and_migration_contract():
    paths = app.openapi()["paths"]
    assert "/api/v1/interactions" in paths
    assert "get" in paths["/api/v1/interactions"]
    assert "post" in paths["/api/v1/interactions"]
    assert "/api/v1/interactions/reviews" in paths
    assert "/api/v1/interactions/{assessment_id}/decisions" in paths
    sql = (MIGRATIONS_DIR / "011_molecular_interaction_intelligence.sql").read_text(encoding="utf-8")
    assert "molecular_interaction_assessments" in sql
    assert "molecular_interaction_decisions" in sql
    assert "prevent_molecular_interaction_decision_mutation" in sql


def test_interaction_submission_schema_keeps_methods_and_evidence_separate():
    from app.routers.interactions import InteractionSubmission
    from pydantic import ValidationError
    payload = InteractionSubmission(
        peptide_id="00000000-0000-0000-0000-000000000001",
        target_id="00000000-0000-0000-0000-000000000002",
        interaction_method="computational_docking",
        evidence_type="computational",
        interface_summary="A computational interface assessment reports candidate residue contacts.",
        limitations="Docking scores are method-dependent and do not establish experimental affinity.",
        source={"source_name":"Example repository","source_identifier":"run-123",
                "source_url":"https://example.org/run-123"}
    )
    assert payload.interaction_method == "computational_docking"
    assert payload.evidence_type == "computational"
    with pytest.raises(ValidationError):
        InteractionSubmission(
            peptide_id="00000000-0000-0000-0000-000000000001",
            target_id="00000000-0000-0000-0000-000000000002",
            interaction_method="clinical_affinity",
            evidence_type="computational",
            interface_summary="An interface assessment.",
            limitations="Not validated.",
            source={"source_name":"Example","source_identifier":"1",
                    "source_url":"https://example.org"}
        )


def test_research_agent_catalogue_and_run_routes_are_registered():
    paths = app.openapi()["paths"]
    assert "/api/v1/agents" in paths
    assert "get" in paths["/api/v1/agents"]
    assert "/api/v1/agents/{agent_id}/run" in paths
    assert "post" in paths["/api/v1/agents/{agent_id}/run"]


def test_research_agent_catalogue_has_specialized_scientific_roles():
    from app.routers.agents import AGENTS
    identifiers = {agent["id"] for agent in AGENTS}
    assert {
        "peptide-research", "sequence", "structure", "target-interaction",
        "analytical", "formulation", "process-development",
        "regulatory-quality", "scientific-review"
    }.issubset(identifiers)
    assert len(AGENTS) == 9


def test_persistent_agent_session_routes_and_migration():
    paths = app.openapi()["paths"]
    assert "/api/v1/agents/sessions" in paths
    assert "get" in paths["/api/v1/agents/sessions"]
    assert "post" in paths["/api/v1/agents/sessions"]
    assert "/api/v1/agents/sessions/{session_id}" in paths
    assert "/api/v1/agents/sessions/{session_id}/messages" in paths
    assert "/api/v1/agents/sessions/{session_id}/archive" in paths
    sql = (MIGRATIONS_DIR / "012_agent_sessions.sql").read_text(encoding="utf-8")
    assert "agent_sessions" in sql
    assert "agent_session_messages" in sql
    assert "organization_id" in sql


def test_agent_message_request_is_bounded_and_supports_exact_peptide_context():
    from app.routers.agents import AgentMessageCreate
    from pydantic import ValidationError
    payload = AgentMessageCreate(message="Review the evidence for this peptide target.", peptide_id="00000000-0000-0000-0000-000000000001")
    assert payload.peptide_id is not None
    with pytest.raises(ValidationError):
        AgentMessageCreate(message="short")


def test_evidence_intelligence_routes_and_migration_contract():
    paths = app.openapi()["paths"]
    assert "/api/v1/evidence-intelligence/claims" in paths
    assert "/api/v1/evidence-intelligence/appraisals" in paths
    assert "/api/v1/evidence-intelligence/appraisals/{claim_id}" in paths
    assert "/api/v1/evidence-intelligence/duplicate-candidates" in paths
    assert "/api/v1/evidence-intelligence/duplicate-candidates/{candidate_id}/decision" in paths
    sql = (MIGRATIONS_DIR / "013_evidence_intelligence.sql").read_text(encoding="utf-8")
    assert "evidence_appraisals" in sql
    assert "publication_duplicate_candidates" in sql
    assert "Evidence level is not a quality score" in sql


def test_evidence_appraisal_keeps_level_and_bias_orthogonal():
    from app.routers.evidence_intelligence import Appraisal
    from pydantic import ValidationError
    payload = Appraisal(
        claim_id="00000000-0000-0000-0000-000000000001",
        study_design="computational", evidence_level="computational",
        risk_of_bias="high_concern", replication_status="single_study",
        limitations="Computational prediction is not experimental validation.",
        appraisal_rationale="A single in-silico study with limited independent confirmation."
    )
    assert payload.evidence_level == "computational"
    assert payload.risk_of_bias == "high_concern"
    with pytest.raises(ValidationError):
        Appraisal(
            claim_id="00000000-0000-0000-0000-000000000001",
            study_design="computational", evidence_level="clinical_human",
            risk_of_bias="impossible", limitations="Not enough details to appraise.",
            appraisal_rationale="This is a test of schema constraints."
        )


def test_peptide_graph_includes_verified_development_relationships():
    from app.routers import peptides
    source = __import__("inspect").getsource(peptides.peptide_knowledge_graph)
    for table in (
        "formulation_profiles", "formulation_stability_observations",
        "process_knowledge_profiles", "process_knowledge_stages",
        "molecular_interaction_assessments", "evidence_appraisals",
        "analytical_methods",
    ):
        assert table in source
    assert "appraisal_status='accepted'" in source
    assert "review_status='verified'" in source


def test_related_peptide_graph_route_uses_verified_shared_evidence():
    from app.routers import peptides
    paths = {route.path for route in peptides.router.routes}
    assert "/api/v1/peptides/{peptide_id}/graph/related" in paths
    source = __import__("inspect").getsource(peptides.related_peptides)
    assert "peptide_target_evidence" in source
    assert "peptide_pathway_evidence" in source
    assert "review_status='verified'" in source
    assert "clinical interchangeability" in source


def test_peptide_comparison_route_is_verified_and_bounded():
    from app.routers import peptides
    from fastapi.routing import APIRoute
    route = next(r for r in peptides.router.routes if isinstance(r, APIRoute) and r.path == "/api/v1/peptides/compare")
    assert "GET" in route.methods
    source = __import__("inspect").getsource(peptides.compare_peptides)
    assert "review_status='verified'" in source
    assert "len(set(ids))" in source
    assert "clinical-trial registry" in source


def test_peptide_research_report_is_source_traceable_and_verified():
    from app.routers import peptides
    paths = {route.path for route in peptides.router.routes}
    assert "/api/v1/peptides/{peptide_id}/report" in paths
    source = __import__("inspect").getsource(peptides.peptide_research_report)
    assert "peptide_knowledge_graph" in source
    assert "appraisal_status='accepted'" in source
    assert "source_records" in source
    assert "not clinical advice" in source


def test_regulatory_guidance_api_is_source_backed_and_reviewed():
    from app.routers import regulatory
    paths = {route.path for route in regulatory.router.routes}
    assert "/api/v1/regulatory" in paths
    assert "/api/v1/regulatory/reviews" in paths
    assert "/api/v1/regulatory/{guidance_id}/decisions" in paths
    source = __import__("inspect").getsource(regulatory)
    assert "source_record_id" in source
    assert "review_status='verified'" in source
    assert "Submitters cannot review their own records." in source


def test_regulatory_change_monitoring_requires_human_review():
    from app.routers import regulatory
    paths = {route.path for route in regulatory.router.routes}
    assert "/api/v1/regulatory/{guidance_id}/observations" in paths
    assert "/api/v1/regulatory/{guidance_id}/history" in paths
    assert "/api/v1/regulatory/changes/reviews" in paths
    assert "/api/v1/regulatory/changes/{event_id}/decisions" in paths
    source = __import__("inspect").getsource(regulatory.observe_guidance_version)
    assert "requires curator review" in source
    assert "review_status='accepted'" in __import__("inspect").getsource(regulatory.guidance_history)


def test_regulatory_observation_integrity_migration_adds_null_safe_deduplication():
    sql = (MIGRATIONS_DIR / "016_regulatory_observation_integrity.sql").read_text(encoding="utf-8")
    assert "NULLS NOT DISTINCT" in sql
    assert "regulatory_guidance_versions" in sql


def test_regulatory_published_change_accepts_its_version_snapshot():
    source = (Path(__file__).parents[1] / "app" / "routers" / "regulatory.py").read_text(encoding="utf-8")
    assert 'payload.decision in {"confirmed_change","published"}' in source


def test_regulatory_source_registry_routes_are_registered_and_bounded():
    paths = app.openapi()["paths"]
    assert "/api/v1/regulatory/sources" in paths
    assert "get" in paths["/api/v1/regulatory/sources"]
    operation = paths["/api/v1/regulatory/sources"]["post"]
    assert operation["requestBody"]["content"]["application/json"]["schema"]["$ref"].endswith("/RegulatorySourceInput")


def test_regulatory_source_registry_migration_is_organization_scoped():
    sql = (MIGRATIONS_DIR / "017_regulatory_source_registry.sql").read_text(encoding="utf-8")
    assert "organization_id" in sql
    assert "UNIQUE(organization_id,feed_url)" in sql


def test_persistent_enrichment_ingestion_routes_and_migration():
    paths = app.openapi()["paths"]
    assert "/api/v1/enrichment/peptides/{peptide_id}/runs" in paths
    assert "post" in paths["/api/v1/enrichment/peptides/{peptide_id}/runs"]
    assert "/api/v1/enrichment/runs" in paths
    sql = (MIGRATIONS_DIR / "018_enrichment_ingestion_runs.sql").read_text(encoding="utf-8")
    assert "enrichment_ingestion_runs" in sql
    assert "organization_id" in sql
    assert "finished_at" in sql


def test_ingestion_source_request_is_bounded_and_rejects_unknown_sources():
    from app.routers.enrichment import IngestionRunRequest
    from pydantic import ValidationError
    assert IngestionRunRequest(sources=["PubMed"], limit_per_source=5).limit_per_source == 5
    with pytest.raises(ValidationError):
        IngestionRunRequest(sources=["arbitrary-url"])
    with pytest.raises(ValidationError):
        IngestionRunRequest(sources=["PubMed", "PubMed"])
    with pytest.raises(ValidationError):
        IngestionRunRequest(sources=["PubMed"], limit_per_source=1000)


def test_regulatory_rss_polling_is_bounded_and_review_gated():
    paths = app.openapi()["paths"]
    assert "/api/v1/regulatory/sources/{source_id}/poll" in paths
    assert "/api/v1/regulatory/sources/observations" in paths
    assert "/api/v1/regulatory/sources/observations/{observation_id}/decision" in paths
    from app.routers.regulatory import _parse_rss_items, APPROVED_REGULATORY_DOMAINS
    xml = b'<rss><channel><item><title>Safety update</title><link>https://www.fda.gov/news/item</link><guid>item-1</guid></item></channel></rss>'
    assert _parse_rss_items(xml)[0]["guid"] == "item-1"
    with pytest.raises(ValueError):
        _parse_rss_items(b'<!DOCTYPE rss [<!ENTITY x "bad">]><rss/>')
    assert {"fda.gov", "ema.europa.eu", "gov.uk", "cdsco.gov.in", "who.int"} <= APPROVED_REGULATORY_DOMAINS
    sql = (MIGRATIONS_DIR / "019_regulatory_source_observations.sql").read_text(encoding="utf-8")
    assert "UNIQUE(source_id,external_identifier)" in sql
    assert "pending_review" in sql


def test_regulatory_scheduler_worker_and_run_history_contracts():
    paths = app.openapi()["paths"]
    assert "/api/v1/regulatory/sources/poll-runs" in paths
    assert "/api/v1/regulatory/sources/due" in paths
    from app.services.regulatory_scheduler import MAX_SOURCES_PER_RUN, poll_due_sources
    assert MAX_SOURCES_PER_RUN == 25
    assert asyncio.iscoroutinefunction(poll_due_sources)
    worker = (Path(__file__).parents[1] / "app" / "services" / "regulatory_scheduler.py").read_text(encoding="utf-8")
    assert "SKIP LOCKED" in worker
    assert "follow_redirects=False" in worker
    assert "next_poll_at" in worker
    migration = (MIGRATIONS_DIR / "020_regulatory_poll_scheduler.sql").read_text(encoding="utf-8")
    assert "regulatory_source_poll_runs" in migration
    assert "last_polled_at" in migration


def test_ai_synthesis_reports_sentence_level_citation_coverage():
    from app.services.ai_synthesis import _safe_citations
    records = _safe_citations([{
        "citation_id": "pubmed:123",
        "source": "PubMed",
        "identifier": "123",
        "title": "Example study",
        "url": "https://pubmed.ncbi.nlm.nih.gov/123/",
        "evidence_summary": "A bounded source summary.",
    }])
    assert len(records) == 1
    assert records[0]["citation_id"] == "pubmed:123"
    assert "sentence-level citation coverage" in (Path(__file__).parents[1] / "app" / "services" / "ai_synthesis.py").read_text(encoding="utf-8")


def test_evidence_review_decisions_are_independent_and_append_only():
    paths = app.openapi()["paths"]
    assert "/api/v1/evidence-intelligence/appraisals/{appraisal_id}/decision" in paths
    assert "/api/v1/evidence-intelligence/appraisals/{appraisal_id}/decisions" in paths
    assert "/api/v1/evidence-intelligence/duplicate-candidates/{candidate_id}/decisions" in paths
    router = (Path(__file__).parents[1] / "app" / "routers" / "evidence_intelligence.py").read_text(encoding="utf-8")
    assert "An appraisal must be independently reviewed by a different reviewer." in router
    migration = (MIGRATIONS_DIR / "021_evidence_review_decisions.sql").read_text(encoding="utf-8")
    assert "BEFORE UPDATE OR DELETE" in migration
    assert "evidence_appraisal_decisions" in migration
    assert "publication_duplicate_decisions" in migration


def test_structured_evidence_extraction_contract_and_source_allowlist():
    paths = app.openapi()["paths"]
    assert "/api/v1/research/assistant/extract" in paths
    assert "/api/v1/research/assistant/extractions/{run_id}" in paths
    from app.services.evidence_extraction import validate_extraction
    citations = [{
        "citation_id": "pubmed:123",
        "source": "PubMed",
        "identifier": "123",
        "url": "https://pubmed.ncbi.nlm.nih.gov/123/",
    }]
    valid = validate_extraction({"records": [{
        "source_citation_id": "pubmed:123",
        "study_design": "in_vitro",
        "evidence_level": "in_vitro",
        "sample_size": 4,
        "findings": ["Observed binding in vitro."],
    }]}, citations)
    assert len(valid) == 1
    assert valid[0]["sample_size"] == 4
    assert valid[0]["peptide_identity"] is None
    invalid_source = validate_extraction({"records": [{
        "source_citation_id": "fake:999",
        "study_design": "unknown",
        "evidence_level": "unknown",
    }]}, citations)
    assert invalid_source == []
    invalid_size = validate_extraction({"records": [{
        "source_citation_id": "pubmed:123",
        "study_design": "unknown",
        "evidence_level": "unknown",
        "sample_size": "many",
    }]}, citations)
    assert invalid_size[0]["sample_size"] is None
    migration = (MIGRATIONS_DIR / "022_structured_evidence_extraction.sql").read_text(encoding="utf-8")
    assert "extracted_evidence_records" in migration
    assert "not_reviewed" in migration



def test_extraction_field_review_routes_are_authenticated_and_registered():
    paths = app.openapi()["paths"]
    review = "/api/v1/research/assistant/extractions/{run_id}/records/{record_id}/fields/{field_name}/review"
    history = "/api/v1/research/assistant/extractions/{run_id}/records/{record_id}/history"
    assert "post" in paths[review]
    assert "get" in paths[history]
    operation = paths[review]["post"]
    assert operation["requestBody"]["required"] is True
    migration = (MIGRATIONS_DIR / "023_extracted_evidence_field_review.sql").read_text(encoding="utf-8")
    assert "extracted_evidence_field_decisions" in migration
    assert "BEFORE UPDATE OR DELETE" in migration
    router = (Path(__file__).parents[1] / "app" / "routers" / "research.py").read_text(encoding="utf-8")
    assert "original AI output is never overwritten" in router
    assert "Curator or reviewer permissions are required." in router


class _FakeMigrationResult:
    def __init__(self, value=None):
        self.value = value

    def scalar_one_or_none(self):
        return self.value


class _FakeMigrationConnection:
    def __init__(self):
        self.ledger = {}
        self.executed_sql = []

    def exec_driver_sql(self, statement, execution_options=None):
        self.executed_sql.append(statement)

    def execute(self, statement, params=None):
        sql = str(statement).lstrip()
        params = params or {}
        if sql.startswith("SELECT checksum"):
            return _FakeMigrationResult(self.ledger.get(params["version"]))
        if sql.startswith("INSERT INTO toolkit_schema_migrations"):
            self.ledger[params["version"]] = params["checksum"]
            return _FakeMigrationResult()
        raise AssertionError(f"Unexpected SQL in migration test: {sql}")


def test_development_migration_ledger_applies_each_file_once(tmp_path):
    from app.main import apply_development_migrations

    (tmp_path / "001_first.sql").write_text("SELECT 1;", encoding="utf-8")
    (tmp_path / "002_second.sql").write_text("SELECT 2;", encoding="utf-8")
    connection = _FakeMigrationConnection()

    apply_development_migrations(connection, tmp_path)
    first_run_count = len(connection.executed_sql)
    apply_development_migrations(connection, tmp_path)

    assert first_run_count == 3  # ledger table plus two migration files
    assert connection.executed_sql.count("SELECT 1;") == 1
    assert connection.executed_sql.count("SELECT 2;") == 1
    assert set(connection.ledger) == {"001_first.sql", "002_second.sql"}


def test_development_migration_ledger_rejects_modified_applied_file(tmp_path):
    from app.main import apply_development_migrations

    migration = tmp_path / "001_first.sql"
    migration.write_text("SELECT 1;", encoding="utf-8")
    connection = _FakeMigrationConnection()
    apply_development_migrations(connection, tmp_path)

    migration.write_text("SELECT 2;", encoding="utf-8")
    with pytest.raises(RuntimeError, match="Applied migration 001_first.sql was modified"):
        apply_development_migrations(connection, tmp_path)



def test_peptide_specific_analytical_applicability_routes_and_schema_are_registered():
    paths = app.openapi()["paths"]
    assert "/api/v1/analytical-methods/applicability" in paths
    assert "get" in paths["/api/v1/analytical-methods/applicability"]
    assert "post" in paths["/api/v1/analytical-methods/applicability"]
    assert "/api/v1/analytical-methods/applicability/reviews" in paths
    assert "/api/v1/analytical-methods/applicability/{applicability_id}/decisions" in paths
    sql = (MIGRATIONS_DIR / "024_peptide_analytical_method_applicability.sql").read_text(encoding="utf-8")
    assert "peptide_method_applicability" in sql
    assert "peptide_method_applicability_decisions" in sql
    assert "prevent_peptide_method_applicability_decision_mutation" in sql


def test_applicability_submission_requires_source_and_explicit_scope():
    from app.routers.analytical_methods import ApplicabilitySubmission

    payload = ApplicabilitySubmission(
        peptide_id="00000000-0000-0000-0000-000000000001",
        method_id="00000000-0000-0000-0000-000000000002",
        test_purpose="Peptide identity confirmation",
        material_form="lyophilized research reference",
        sample_matrix="neat reference material",
        applicability_rationale="The cited study evaluated this analytical method for the specified peptide material.",
        evidence_scope="The source supports identity assessment under the described study conditions.",
        limitations="Applicability to other matrices and modified analogues has not been established.",
        source_name="Example Journal",
        source_identifier="doi:10.example/peptide-method",
        source_url="https://example.org/peptide-method",
    )
    assert payload.test_purpose == "Peptide identity confirmation"



def test_vendor_facility_review_routes_are_registered():
    paths = app.openapi()["paths"]
    assert "/api/v1/vendors/{vendor_id}/sites" in paths
    assert "post" in paths["/api/v1/vendors/{vendor_id}/sites"]
    assert "get" in paths["/api/v1/vendors/{vendor_id}/sites"]
    assert "/api/v1/vendors/sites/reviews" in paths
    assert "get" in paths["/api/v1/vendors/sites/reviews"]
    assert "/api/v1/vendors/sites/{site_id}/decisions" in paths
    assert "post" in paths["/api/v1/vendors/sites/{site_id}/decisions"]


def test_vendor_certification_review_routes_are_registered():
    paths = app.openapi()["paths"]
    assert "/api/v1/vendors/organization-options" in paths
    assert "get" in paths["/api/v1/vendors/organization-options"]
    assert "/api/v1/vendors/certifications/reviews" in paths
    assert "get" in paths["/api/v1/vendors/certifications/reviews"]
    assert "/api/v1/vendors/certifications/{certification_id}/decisions" in paths
    assert "post" in paths["/api/v1/vendors/certifications/{certification_id}/decisions"]
    assert "/api/v1/vendors/services/reviews" in paths
    assert "get" in paths["/api/v1/vendors/services/reviews"]
    assert "/api/v1/vendors/services/{service_id}/decisions" in paths
    assert "post" in paths["/api/v1/vendors/services/{service_id}/decisions"]
    assert "/api/v1/vendors/services/{service_id}/evidence-links" in paths
    assert "post" in paths["/api/v1/vendors/services/{service_id}/evidence-links"]
    assert "/api/v1/vendors/service-evidence-links/reviews" in paths
    assert "get" in paths["/api/v1/vendors/service-evidence-links/reviews"]
    assert "/api/v1/vendors/service-evidence-links/{link_id}/decisions" in paths
    assert "post" in paths["/api/v1/vendors/service-evidence-links/{link_id}/decisions"]
    assert "/api/v1/vendors/{vendor_id}/services" in paths
    assert "get" in paths["/api/v1/vendors/{vendor_id}/services"]
    assert "/api/v1/vendors/{vendor_id}/capabilities" in paths
    assert "get" in paths["/api/v1/vendors/{vendor_id}/capabilities"]



def test_vendor_service_submission_requires_a_verified_facility_reference():
    from pydantic import ValidationError
    from app.routers.vendors import VendorServiceSubmission

    with pytest.raises(ValidationError):
        VendorServiceSubmission(
            service_name="LC-MS identity testing",
            capability_description="Source-described analytical service for peptide identity evaluation.",
            source_name="Example Laboratory",
            source_identifier="service-catalogue-001",
            source_url="https://example.org/services",
        )



def test_vendor_candidate_batch_import_contract_and_unverified_defaults():
    from pydantic import ValidationError
    from app.routers.vendors import VendorCandidateBatch

    valid = {
        "legal_name": "Example Peptide Company",
        "website_url": "https://example.org",
        "country_code": "US",
        "vendor_type": "peptide_manufacturer",
        "source_name": "Official company website",
        "source_identifier": "official-service-page:example",
        "source_url": "https://example.org/peptide-services",
        "evidence_scope": "Official service page describes custom peptide synthesis; facility and certification claims are not inferred.",
    }
    batch = VendorCandidateBatch(candidates=[valid])
    assert len(batch.candidates) == 1
    assert batch.candidates[0].identity_source is None
    with pytest.raises(ValidationError):
        VendorCandidateBatch(candidates=[])
    with pytest.raises(ValidationError):
        VendorCandidateBatch(candidates=[{**valid, "country_code": "USA"}])
    with pytest.raises(ValidationError):
        VendorCandidateBatch(candidates=[{**valid, "source_url": "http://example.org/source"}])
    with pytest.raises(ValidationError):
        VendorCandidateBatch(candidates=[{**valid, "identity_source": {
            "source_name": "Official company profile",
            "source_identifier": "identity-example",
            "source_url": "http://example.org/profile",
            "evidence_scope": "Official profile identifies the corporate reference country.",
        }}])



def test_vendor_candidate_import_route_is_registered():
    paths = app.openapi()["paths"]
    assert "/api/v1/vendors/import-candidates" in paths
    assert "post" in paths["/api/v1/vendors/import-candidates"]



def test_vendor_candidate_sources_must_match_official_company_domain():
    from fastapi import HTTPException
    from app.routers.vendors import _candidate_source_url

    assert _candidate_source_url("https://www.example.org", "https://example.org/services") == "https://example.org/services"
    assert _candidate_source_url("https://example.org", "https://labs.example.org/profile") == "https://labs.example.org/profile"
    with pytest.raises(HTTPException):
        _candidate_source_url("https://example.org", "https://unrelated.example.net/services")



def test_vendor_facility_candidate_batch_requires_source_backed_records():
    from pydantic import ValidationError
    from app.routers.vendors import VendorSiteCandidateBatch

    valid = {
        "site_name": "Bubendorf",
        "address": "Hauptstrasse 144, 4416 Bubendorf, Switzerland",
        "country_code": "CH",
        "site_scope": "Official site page describes peptide manufacturing, process development and analytical capabilities.",
        "source_name": "Official facility page",
        "source_identifier": "official-facility:bachem-bubendorf",
        "source_url": "https://www.bachem.com/about-bachem/our-locations/bubendorf/",
    }
    batch = VendorSiteCandidateBatch(candidates=[{
        **valid,
        "additional_sources": [{
            "source_name": "Official company contact page",
            "source_identifier": "official-contact:facility-address",
            "source_url": "https://www.bachem.com/contact/",
            "evidence_scope": "Official contact page independently lists the facility postal address.",
        }],
    }])
    assert batch.candidates[0].country_code == "CH"
    assert len(batch.candidates[0].additional_sources) == 1
    with pytest.raises(ValidationError):
        VendorSiteCandidateBatch(candidates=[])
    with pytest.raises(ValidationError):
        VendorSiteCandidateBatch(candidates=[{**valid, "source_url": "http://www.bachem.com/site"}])
    with pytest.raises(ValidationError):
        VendorSiteCandidateBatch(candidates=[{**valid, "additional_sources": [{
            "source_name": "Third party directory",
            "source_identifier": "third-party-site",
            "source_url": "http://directory.example.net",
            "evidence_scope": "Address copied from an external directory.",
        }]}])



def test_vendor_facility_candidate_import_route_is_registered():
    paths = app.openapi()["paths"]
    path = "/api/v1/vendors/{vendor_id}/import-site-candidates"
    assert path in paths
    assert "post" in paths[path]


def test_facility_specific_laboratory_capability_routes_are_registered():
    paths = app.openapi()["paths"]
    assert "/api/v1/analytical-methods/laboratory-capabilities" in paths
    assert {"get", "post"} <= set(paths["/api/v1/analytical-methods/laboratory-capabilities"])
    assert "/api/v1/analytical-methods/laboratory-capabilities/reviews" in paths
    assert "get" in paths["/api/v1/analytical-methods/laboratory-capabilities/reviews"]
    assert "/api/v1/analytical-methods/laboratory-capabilities/{claim_id}/decisions" in paths
    assert "post" in paths["/api/v1/analytical-methods/laboratory-capabilities/{claim_id}/decisions"]


def test_laboratory_capability_migration_preserves_review_and_provenance_controls():
    sql = (MIGRATIONS_DIR / "031_laboratory_capability_claims.sql").read_text(encoding="utf-8")
    for expected in (
        "laboratory_capability_claims",
        "laboratory_capability_decisions",
        "organization_id",
        "service_id",
        "method_id",
        "peptide_id",
        "sample_matrix",
        "storage_shipping_requirements",
        "source_id",
        "submitted_by",
        "review_status",
        "prevent_laboratory_capability_decision_mutation",
    ):
        assert expected in sql


def test_structured_analytical_test_catalogue_route_is_registered():
    paths = app.openapi()["paths"]
    assert "/api/v1/analytical-methods/test-catalogue" in paths
    operation = paths["/api/v1/analytical-methods/test-catalogue"]["get"]
    params = {item["name"]: item for item in operation["parameters"]}
    assert params["limit"]["schema"]["maximum"] == 200
    assert "quality_attribute" in params


def test_analytical_test_catalogue_review_routes_are_registered():
    paths = app.openapi()["paths"]
    assert "/api/v1/analytical-methods/test-catalogue/reviews" in paths
    assert "get" in paths["/api/v1/analytical-methods/test-catalogue/reviews"]
    assert "/api/v1/analytical-methods/test-catalogue/{test_id}/decisions" in paths
    assert "post" in paths["/api/v1/analytical-methods/test-catalogue/{test_id}/decisions"]


def test_analytical_test_catalogue_review_routes_are_registered():
    paths = app.openapi()["paths"]
    assert "/api/v1/analytical-methods/test-catalogue/reviews" in paths
    assert "get" in paths["/api/v1/analytical-methods/test-catalogue/reviews"]
    assert "/api/v1/analytical-methods/test-catalogue/{test_id}/decisions" in paths
    assert "post" in paths["/api/v1/analytical-methods/test-catalogue/{test_id}/decisions"]


def test_peptide_test_applicability_routes_are_registered():
    paths = app.openapi()["paths"]
    base = "/api/v1/analytical-methods/test-catalogue/applicability"
    assert {"get", "post"} <= set(paths[base])
    assert "get" in paths[base + "/reviews"]
    assert "post" in paths[base + "/{applicability_id}/decisions"]


def test_peptide_test_applicability_payload_rejects_unsupported_status_and_non_https_source():
    from pydantic import ValidationError
    from uuid import uuid4
    from app.routers.analytical_methods import PeptideTestApplicabilitySubmission

    payload = {
        "peptide_id": uuid4(),
        "test_id": uuid4(),
        "applicability_status": "conditional",
        "rationale": "The cited evidence supports a conditional assessment for this material context.",
        "evidence_scope": "Published evidence concerning the stated peptide and test purpose.",
        "limitations": "The reference does not validate a procedure or define acceptance criteria.",
        "source_name": "Peer-reviewed publication",
        "source_identifier": "doi:10.example/peptide-test",
        "source_url": "https://doi.org/10.example/peptide-test",
    }
    assert PeptideTestApplicabilitySubmission(**payload).applicability_status == "conditional"
    with pytest.raises(ValidationError):
        PeptideTestApplicabilitySubmission(**{**payload, "applicability_status": "mandatory"})
    with pytest.raises(ValidationError):
        PeptideTestApplicabilitySubmission(**{**payload, "source_url": "http://example.org/reference"})


def test_analytical_reference_framework_crosswalk_route_is_registered():
    paths = app.openapi()["paths"]
    path = "/api/v1/analytical-methods/test-catalogue/frameworks"
    assert "get" in paths[path]
    params = {item["name"]: item for item in paths[path]["get"]["parameters"]}
    assert params["limit"]["schema"]["maximum"] == 250


def test_reference_framework_crosswalk_migration_keeps_review_and_limitations_fields():
    sql = (MIGRATIONS_DIR / "035_analytical_reference_framework_crosswalk.sql").read_text(encoding="utf-8")
    for expected in (
        "analytical_reference_frameworks",
        "analytical_test_framework_links",
        "framework_code",
        "jurisdiction_or_system",
        "official_status",
        "applicability_limitations",
        "review_status",
        "ICH_Q2_R2",
        "ICH_Q14",
        "USP_503_1",
    ):
        assert expected in sql

def test_authenticated_user_is_scoped_to_the_organization_in_the_jwt():
    from uuid import uuid4

    from app.routers.auth import _create_access_token, get_current_user

    user_id = uuid4()
    token_organization_id = uuid4()
    other_organization_id = uuid4()
    token = _create_access_token(str(user_id), str(token_organization_id), "researcher")

    class FakeResult:
        def mappings(self):
            return self

        def first(self):
            return {
                "id": user_id,
                "email": "researcher@example.org",
                "display_name": "Researcher",
                "organization_id": token_organization_id,
                "role": "researcher",
                "is_active": True,
                "organization_name": "Token Organization",
            }

    class FakeDatabase:
        calls = []

        def execute(self, statement, parameters):
            self.calls.append((str(statement), parameters))
            return FakeResult()

    db = FakeDatabase()
    db.calls = []
    user = get_current_user(token, db)

    assert "om.organization_id = :organization_id" in db.calls[0][0]
    assert db.calls[0][1]["organization_id"] == token_organization_id
    assert db.calls[0][1]["organization_id"] != other_organization_id
    assert "set_config('app.organization_id', :organization_id, true)" in db.calls[1][0]
    assert db.calls[1][1]["organization_id"] == str(token_organization_id)
    assert "set_config('app.user_id', :user_id, true)" in db.calls[2][0]
    assert db.calls[2][1]["user_id"] == str(user_id)
    assert user["organization_id"] == str(token_organization_id)


def test_static_peptide_compare_route_precedes_dynamic_uuid_profile_route():
    routes = [route.path for route in app.routes if getattr(route, "path", None)]
    compare_path = "/api/v1/peptides/compare"
    profile_path = "/api/v1/peptides/{peptide_id}"
    assert routes.index(compare_path) < routes.index(profile_path)


def test_unprotected_write_routes_are_explicitly_allowlisted():
    paths = app.openapi()["paths"]
    public_write_routes = {
        (method.upper(), path)
        for path, operations in paths.items()
        for method, operation in operations.items()
        if method in {"post", "put", "patch", "delete"} and not operation.get("security")
    }
    assert public_write_routes == {
        ("POST", "/api/v1/auth/register"),
        ("POST", "/api/v1/auth/login"),
        ("POST", "/api/v1/bioinformatics/analyze"),
        ("POST", "/api/v1/bioinformatics/align"),
        # This route is development-only and is blocked outside APP_ENV=development.
        ("POST", "/api/v1/research/assistant/synthesize"),
    }


def test_public_ai_synthesis_endpoint_is_blocked_outside_development(monkeypatch):
    import asyncio
    import pytest
    from fastapi import HTTPException
    from app.config import settings
    from app.routers.research import AssistantSynthesisRequest, synthesize_research_answer

    monkeypatch.setattr(settings, "ai_synthesis_enabled", True)
    monkeypatch.setattr(settings, "ai_api_key", "test-provider-key")
    monkeypatch.setattr(settings, "app_env", "production")

    with pytest.raises(HTTPException) as error:
        asyncio.run(synthesize_research_answer(
            AssistantSynthesisRequest(question="Review published peptide evidence")
        ))
    assert error.value.status_code == 503


def test_canonical_peptide_identity_schema_preserves_raw_notation_and_versioning():
    migration = (MIGRATIONS_DIR / "039_canonical_peptide_chemical_forms.sql").read_text(encoding="utf-8")
    for expected in (
        "raw_notation TEXT",
        "normalized_sequence TEXT",
        "notation_format TEXT",
        "canonicalization_version TEXT",
        "identity_fingerprint TEXT",
        "CREATE TABLE IF NOT EXISTS peptide_chemical_forms",
        "stereochemistry JSONB",
        "noncanonical_residues JSONB",
        "terminal_chemistry JSONB",
        "post_translational_modifications JSONB",
        "cyclization JSONB",
        "conjugation JSONB",
        "salt_and_counterions JSONB",
        "supersedes_form_id UUID",
        "intentionally non-unique",
    ):
        assert expected in migration
    assert "UNIQUE(identity_fingerprint)" not in migration


def test_peptide_profile_and_comparison_expose_reviewed_chemical_forms():
    source = Path(__import__("app.routers.peptides", fromlist=["__file__"]).__file__).read_text(encoding="utf-8")
    assert "FROM peptide_chemical_forms" in source
    assert "WHERE peptide_id=:id AND review_status='verified'" in source
    assert '"chemical_forms"' in source
    assert "canonicalization_version" in source



def test_chemical_form_applicability_links_enforce_parent_peptide_consistency():
    migration = (MIGRATIONS_DIR / "040_chemical_form_applicability_links.sql").read_text(encoding="utf-8")
    for table in (
        "peptide_method_applicability",
        "peptide_test_applicability",
        "laboratory_capability_claims",
    ):
        assert f"ALTER TABLE {table}" in migration
        assert f"ON {table}" in migration
        assert f"idx_{table}_form" in migration or table == "laboratory_capability_claims"
    assert "chemical_form_id UUID" in migration
    assert "REFERENCES peptide_chemical_forms(id) ON DELETE RESTRICT" in migration
    assert "enforce_peptide_chemical_form_parent" in migration
    assert "IS DISTINCT FROM v_form_peptide_id" in migration
    assert "NULL preserves legacy" in migration



def test_applicability_payloads_accept_optional_chemical_form_scope():
    from uuid import uuid4
    from app.routers.analytical_methods import (
        ApplicabilitySubmission,
        PeptideTestApplicabilitySubmission,
        LaboratoryCapabilitySubmission,
    )

    form_id = uuid4()
    method_payload = ApplicabilitySubmission(
        peptide_id=uuid4(), chemical_form_id=form_id, method_id=uuid4(),
        test_purpose="Assess identity for this specified form",
        applicability_rationale="The evidence specifically addresses the selected chemical form.",
        evidence_scope="Published characterization data for this form.",
        limitations="The source does not establish validation or acceptance criteria.",
        source_name="Peer-reviewed publication", source_identifier="doi:10.example/method",
        source_url="https://doi.org/10.example/method",
    )
    test_payload = PeptideTestApplicabilitySubmission(
        peptide_id=uuid4(), chemical_form_id=form_id, test_id=uuid4(),
        applicability_status="conditional",
        rationale="The source supports conditional applicability for the selected form.",
        evidence_scope="Evidence for the stated form and test context.",
        limitations="This does not establish a validated procedure or acceptance criteria.",
        source_name="Peer-reviewed publication", source_identifier="doi:10.example/test",
        source_url="https://doi.org/10.example/test",
    )
    lab_payload = LaboratoryCapabilitySubmission(
        service_id=uuid4(), method_id=uuid4(), peptide_id=uuid4(),
        chemical_form_id=form_id, test_purpose="Test capability for the selected form",
        sample_matrix="Aqueous sample", evidence_scope="Facility capability source evidence.",
        limitations="Does not establish current capacity or validation.",
        source_name="Laboratory source", source_identifier="facility-capability-1",
        source_url="https://example.org/capability",
    )
    assert method_payload.chemical_form_id == form_id
    assert test_payload.chemical_form_id == form_id
    assert lab_payload.chemical_form_id == form_id


def test_chemical_form_scope_helper_rejects_missing_or_mismatched_parent():
    from uuid import uuid4
    from fastapi import HTTPException
    from app.routers.analytical_methods import _validate_chemical_form_scope

    peptide_id, other_peptide_id, form_id = uuid4(), uuid4(), uuid4()

    class FakeResult:
        def __init__(self, value):
            self.value = value

        def scalar_one_or_none(self):
            return self.value

    class FakeDatabase:
        def __init__(self, value):
            self.value = value

        def execute(self, statement, parameters):
            assert parameters["form_id"] == form_id
            return FakeResult(self.value)

    _validate_chemical_form_scope(FakeDatabase(peptide_id), peptide_id, form_id)
    with pytest.raises(HTTPException) as mismatch:
        _validate_chemical_form_scope(FakeDatabase(other_peptide_id), peptide_id, form_id)
    assert mismatch.value.status_code == 422
    with pytest.raises(HTTPException) as missing:
        _validate_chemical_form_scope(FakeDatabase(None), peptide_id, form_id)
    assert missing.value.status_code == 404
    with pytest.raises(HTTPException) as no_parent:
        _validate_chemical_form_scope(FakeDatabase(peptide_id), None, form_id)
    assert no_parent.value.status_code == 422


def test_evidence_claim_revision_schema_and_curation_contract():
    migration = MIGRATIONS_DIR / "055_evidence_claim_revision_history.sql"
    sql = migration.read_text(encoding="utf-8")
    assert "evidence_claim_revisions" in sql
    assert "content_hash CHAR(64)" in sql
    assert "evidence_claim_revision_id" in sql
    assert "capture_evidence_claim_revision" in sql
    assert "bind_curation_decision_to_claim_revision" in sql
    assert "BEFORE UPDATE OR DELETE ON evidence_claim_revisions" in sql


def test_extraction_source_provenance_migration_is_registered_and_typed():
    sql = (MIGRATIONS_DIR / "056_extraction_source_record_provenance.sql").read_text(encoding="utf-8")
    assert "source_record_id UUID REFERENCES source_records(id)" in sql
    assert "source_record_version_id UUID REFERENCES source_record_versions(id)" in sql
    assert "normalized_provider_record" in sql
    assert "enforce_extracted_source_version_match" in sql
    assert "source_record_versions_append_only" in sql


def test_extraction_artifact_rls_migration_has_select_insert_and_parent_guards():
    sql = (MIGRATIONS_DIR / "057_extraction_artifact_row_level_security.sql").read_text(encoding="utf-8")
    for table in ("evidence_extraction_runs", "extracted_evidence_records", "extracted_evidence_field_decisions"):
        assert "ALTER TABLE " + table + " ENABLE ROW LEVEL SECURITY" in sql
        assert table + "_select_scope" in sql
        assert table + "_insert_scope" in sql
    assert "enforce_extraction_run_organization" in sql
    assert "enforce_extraction_decision_organization" in sql


def test_data_quality_completeness_route_is_registered_and_protected():
    operation = app.openapi()["paths"]["/api/v1/data-quality/completeness"]["get"]
    from inspect import getsource
    from app.routers.data_quality import get_data_completeness

    source = getsource(get_data_completeness)
    assert "organization_memberships" in source
    assert "organization_admin" in source
    assert "curator" in source
    assert "reviewer" in source


def test_laboratory_capability_rls_migration_has_tenant_and_public_evidence_guards():
    sql = (MIGRATIONS_DIR / "060_laboratory_capability_row_level_security.sql").read_text(encoding="utf-8")
    for table in ("laboratory_capability_claims", "laboratory_capability_decisions"):
        assert "ALTER TABLE " + table + " ENABLE ROW LEVEL SECURITY" in sql
        assert "ALTER TABLE " + table + " FORCE ROW LEVEL SECURITY" in sql
    assert "visibility_scope='public'" in sql
    assert "service.review_status='verified'" in sql
    assert "vendor.verification_status='verified'" in sql
    assert "site.review_status='verified'" in sql
    assert "method.visibility_scope='public'" in sql
    assert "enforce_laboratory_capability_parent_scope" in sql
    assert "enforce_laboratory_capability_decision_owner" in sql


def test_peptide_applicability_rls_migration_covers_both_assessment_families():
    sql = (MIGRATIONS_DIR / "061_peptide_applicability_row_level_security.sql").read_text(encoding="utf-8")
    for table in (
        "peptide_method_applicability", "peptide_method_applicability_decisions",
        "peptide_test_applicability", "peptide_test_applicability_decisions",
    ):
        assert "ALTER TABLE " + table + " ENABLE ROW LEVEL SECURITY" in sql
        assert "ALTER TABLE " + table + " FORCE ROW LEVEL SECURITY" in sql
    assert "visibility_scope='public'" in sql
    assert "method.visibility_scope='public'" in sql
    assert "test.review_status='verified'" in sql
    assert "enforce_peptide_method_applicability_scope" in sql
    assert "enforce_peptide_test_applicability_scope" in sql
    assert "enforce_peptide_method_applicability_decision_owner" in sql
    assert "enforce_peptide_test_applicability_decision_owner" in sql


def test_analytical_test_catalogue_decisions_rls_is_organization_scoped():
    sql = (MIGRATIONS_DIR / "062_analytical_test_catalogue_decision_row_level_security.sql").read_text(encoding="utf-8")
    table = "analytical_test_catalogue_decisions"
    assert "ALTER TABLE " + table + " ENABLE ROW LEVEL SECURITY" in sql
    assert "ALTER TABLE " + table + " FORCE ROW LEVEL SECURITY" in sql
    assert table + "_select_scope" in sql
    assert table + "_insert_scope" in sql
    assert "current_setting('app.organization_id', true)" in sql
    assert "analytical_test_catalogue test" in sql


def test_audit_event_rls_binds_organization_and_actor_context():
    sql = (MIGRATIONS_DIR / "063_audit_event_row_level_security.sql").read_text(encoding="utf-8")
    assert "ALTER TABLE audit_events ENABLE ROW LEVEL SECURITY" in sql
    assert "ALTER TABLE audit_events FORCE ROW LEVEL SECURITY" in sql
    assert "audit_events_select_scope" in sql
    assert "audit_events_insert_scope" in sql
    assert "current_setting('app.organization_id', true)" in sql
    assert "current_setting('app.user_id', true)" in sql
    auth_source = (Path(__file__).resolve().parents[1] / "app" / "routers" / "auth.py").read_text(encoding="utf-8")
    switch_source = auth_source.split("@router.post(\"/switch-organization\")", 1)[1]
    assert switch_source.index("set_config('app.organization_id'") < switch_source.index("INSERT INTO audit_events")


def test_data_quality_router_is_registered_exactly_once():
    source = (Path(__file__).resolve().parents[1] / "app" / "main.py").read_text(encoding="utf-8")
    assert source.count("from .routers.data_quality import router as data_quality_router") == 1
    assert source.count("app.include_router(data_quality_router)") == 1


def test_all_sensitive_write_routes_have_per_user_rate_limit_dependencies():
    from app.routers.analytical_methods import router as analytical_router
    from app.routers.enrichment import router as enrichment_router
    from app.routers.vendors import router as vendor_router

    expected = (
        (enrichment_router, "enrichment_write"),
        (vendor_router, "vendor_write"),
        (analytical_router, "analytical_write"),
    )
    for router, scope in expected:
        post_routes = [route for route in router.routes if "POST" in getattr(route, "methods", set())]
        assert post_routes
        for route in post_routes:
            assert any(
                getattr(dependency.call, "rate_limit_scope", None) == scope
                for dependency in route.dependant.dependencies
            ), f"{route.path} is missing its {scope} rate limit"


def test_peptide_mechanism_of_action_profile_contract_is_registered():
    paths = app.openapi()["paths"]
    assert "/api/v1/peptides/{peptide_id}" in paths
    assert "get" in paths["/api/v1/peptides/{peptide_id}"]


def test_fda_drugsfda_normalization_preserves_product_and_submission_scope():
    record = {
        "application_number": "NDA000001",
        "sponsor_name": "Example Sponsor",
        "products": [{
            "product_number": "001",
            "dosage_form": "INJECTION",
            "route": "SUBCUTANEOUS",
            "marketing_status": "Prescription",
            "active_ingredients": [{"name": "PEPTIDE X", "strength": "1 MG"}],
        }],
        "submissions": [{
            "submission_type": "ORIG",
            "submission_status": "AP",
            "submission_status_date": "20250101",
        }],
    }
    result = normalize_application(record)
    assert result["application_number"] == "NDA000001"
    assert result["products"][0]["active_ingredients"][0]["name"] == "PEPTIDE X"
    assert result["approved_submission_actions_observed"][0]["submission_status"] == "AP"
    assert result["curation_status"] == "not_reviewed"
    assert result["jurisdiction"] == "US"


def test_dailymed_normalization_does_not_claim_approval():
    result = normalize_spl({
        "setid": "00000000-0000-0000-0000-000000000001",
        "spl_version": "4",
        "title": "PEPTIDE X INJECTION",
        "published_date": "Jan 01, 2025",
    })
    assert result["set_id"] == "00000000-0000-0000-0000-000000000001"
    assert "dailymed.nlm.nih.gov" in result["source_url"]
    assert result["curation_status"] == "not_reviewed"
    assert "not necessarily identical" in result["label_notice"]


def test_fda_and_dailymed_research_routes_are_registered_and_bounded():
    paths = app.openapi()["paths"]
    for route in ("/api/v1/research/fda-drugsfda", "/api/v1/research/dailymed"):
        assert "get" in paths[route]
    fda_params = {item["name"]: item for item in paths["/api/v1/research/fda-drugsfda"]["get"]["parameters"]}
    daily_params = {item["name"]: item for item in paths["/api/v1/research/dailymed"]["get"]["parameters"]}
    assert fda_params["limit"]["schema"]["maximum"] == 99
    assert daily_params["limit"]["schema"]["maximum"] == 100


def test_global_peptide_discovery_persistence_route_is_registered_and_rate_limited():
    paths = app.openapi()["paths"]
    route = paths["/api/v1/enrichment/discover-peptides"]["post"]
    assert route["requestBody"]["required"] is True
    assert "PeptideDiscoveryRequest" in str(route["requestBody"])
    from app.routers.enrichment import router as enrichment_router
    discovery_route = next(
        item for item in enrichment_router.routes
        if item.path == "/api/v1/enrichment/discover-peptides"
    )
    assert any(
        getattr(dependency.call, "rate_limit_scope", None) == "enrichment_write"
        for dependency in discovery_route.dependant.dependencies
    )


def test_global_peptide_discovery_browser_route_is_registered():
    paths = app.openapi()["paths"]
    route = paths["/api/v1/enrichment/discovery-candidates"]["get"]
    parameters = {item["name"]: item for item in route["parameters"]}
    assert parameters["limit"]["schema"]["default"] == 50
    assert parameters["offset"]["schema"]["default"] == 0


def test_health_canada_dpd_normalization_preserves_canadian_product_status():
    result = normalize_product(
        {
            "drug_code": 12345,
            "drug_identification_number": "01234567",
            "brand_name": "Example Peptide",
            "company_name": "Example Manufacturer",
            "class_name": "Human",
        },
        [{"ingredient_name": "PEPTIDE X", "strength": "1", "strength_unit": "MG"}],
        [{"status": "Approved"}],
        [{"pharmaceutical_form_name": "Solution"}],
        [{"route_of_administration_name": "Subcutaneous"}],
    )
    assert result["drug_identification_number"] == "01234567"
    assert result["active_ingredients"][0]["ingredient_name"] == "PEPTIDE X"
    assert result["source_status_records"][0]["status"] == "Approved"
    assert result["jurisdiction"] == "CA"
    assert result["curation_status"] == "not_reviewed"


def test_health_canada_dpd_research_route_is_registered_and_bounded():
    route = app.openapi()["paths"]["/api/v1/research/health-canada-dpd"]["get"]
    params = {item["name"]: item for item in route["parameters"]}
    assert params["limit"]["schema"]["maximum"] == 50


def test_global_peptide_discovery_accepts_canada_as_a_source():
    from app.routers.enrichment import PeptideDiscoveryRequest
    request = PeptideDiscoveryRequest(query="peptide X", sources=["health_canada_dpd"])
    assert request.sources == ["health_canada_dpd"]


def test_dailymed_extracts_only_explicit_moa_section():
    xml = """<?xml version="1.0" encoding="UTF-8"?>
    <document xmlns="urn:hl7-org:v3">
      <component><structuredBody>
        <component><section>
          <code code="43679-0" displayName="MECHANISM OF ACTION SECTION"/>
          <title>12.1 Mechanism of Action</title>
          <text><paragraph>Peptide X binds receptor Y and activates intracellular signalling.</paragraph></text>
        </section></component>
        <component><section>
          <code code="43681-6" displayName="PHARMACODYNAMICS SECTION"/>
          <title>12.2 Pharmacodynamics</title>
          <text><paragraph>Biomarker Z changes after administration.</paragraph></text>
        </section></component>
      </structuredBody></component>
    </document>"""
    result = extract_mechanism_of_action(xml)
    assert result["found"] is True
    assert result["section_code"] == "43679-0"
    assert "binds receptor Y" in result["mechanism_text"]
    assert "Biomarker Z" not in result["mechanism_text"]
    assert result["evidence_level"] == "source_asserted"


def test_dailymed_title_fallback_is_explicitly_marked():
    result = extract_mechanism_of_action(
        '<document xmlns="urn:hl7-org:v3"><component><section>'
        '<title>12.1 Mechanism of Action</title>'
        '<text><paragraph>Explicit fallback mechanism text from the label.</paragraph></text>'
        '</section></component></document>'
    )
    assert result["found"] is True
    assert result["section_code"] == "title_fallback"
    assert result["extraction_status"] == "extracted_from_explicit_spl_section"


def test_dailymed_missing_moa_section_is_not_inferred():
    result = extract_mechanism_of_action(
        '<document xmlns="urn:hl7-org:v3"><component><section>'
        '<code code="43681-6"/><title>12.2 Pharmacodynamics</title>'
        '<text>Observed effect only.</text></section></component></document>'
    )
    assert result["found"] is False
    assert result["mechanism_text"] is None
    assert result["extraction_status"] == "section_not_present"


def test_dailymed_moa_extraction_route_is_registered():
    paths = app.openapi()["paths"]
    route = paths["/api/v1/research/dailymed/{set_id}/mechanism-of-action"]["get"]
    assert route["parameters"][0]["name"] == "set_id"


def test_purple_book_discovers_latest_monthly_csv_from_fda_download_page():
    html = """
    <a href="https://www.accessdata.fda.gov/drugsatfda_docs/PurpleBook/2025/purplebook-search-December-data-download.csv">Dec</a>
    <a href="https://www.accessdata.fda.gov/drugsatfda_docs/PurpleBook/2026/purplebook-search-October-data-download.csv">Oct</a>
    """
    assert discover_latest_csv_url(html).endswith("2026/purplebook-search-October-data-download.csv")


def test_purple_book_parser_uses_full_snapshot_table_not_monthly_change_table():
    csv_text = (
        "Change Type,BLA Number,Proper Name,Product Number,License Type\n"
        "N,123,Temporary row,001,351(a)\n"
        "\n"
        "BLA Number,Proper Name,Product Number,License Type,Applicant,Strength,Route of Administration,Licensure\n"
        "123,Peptide biologic A,001,351(a),Example Sponsor,1 mg,Subcutaneous,Licensed\n"
        "456,Other biologic,002,351(a),Other Sponsor,2 mg,Intravenous,Licensed\n"
    )
    rows = parse_purple_book_csv(csv_text)
    assert len(rows) == 2
    assert rows[0]["proper_name"] == "Peptide biologic A"
    assert rows[0]["bla_number"] == "123"
    normalized = normalize_purple_book_product(rows[0], "https://example.test/purplebook.csv")
    assert normalized["source_identifier"] == "123:001"
    assert normalized["jurisdiction"] == "US"
    assert normalized["source_version"] == "purplebook.csv"
    assert normalized["curation_status"] == "not_reviewed"
    assert "not proof" in normalized["coverage_notice"]


def test_purple_book_research_and_global_discovery_contracts_are_registered():
    route = app.openapi()["paths"]["/api/v1/research/fda-purple-book"]["get"]
    params = {item["name"]: item for item in route["parameters"]}
    assert params["limit"]["schema"]["maximum"] == 100
    from app.routers.enrichment import PeptideDiscoveryRequest
    request = PeptideDiscoveryRequest(
        query="peptide biologic",
        sources=["fda_purple_book", "health_canada_dpd"],
    )
    assert len(request.sources) == 2


def test_peptide_mechanisms_can_be_submitted_to_independent_curation():
    schemas = app.openapi()["components"]["schemas"]
    entity_types = schemas["ReviewSubmission"]["properties"]["entity_type"]["enum"]
    assert "peptide_mechanism" in entity_types
    paths = app.openapi()["paths"]
    assert "/api/v1/enrichment/peptides/{peptide_id}/mechanisms/dailymed" in paths
    assert "post" in paths["/api/v1/enrichment/peptides/{peptide_id}/mechanisms/dailymed"]

def test_mechanism_review_submission_is_curation_compatible():
    schemas = app.openapi()["components"]["schemas"]
    assert "peptide_mechanism" in schemas["ReviewSubmission"]["properties"]["entity_type"]["enum"]
    assert "/api/v1/curation/reviews/{review_id}/decisions" in app.openapi()["paths"]
    assert "/api/v1/enrichment/peptides/{peptide_id}/mechanisms/dailymed" in app.openapi()["paths"]

def test_curators_can_retrieve_source_backed_mechanism_review_details():
    route = app.openapi()["paths"]["/api/v1/curation/reviews/{review_id}/mechanism"]["get"]
    assert route["parameters"][0]["name"] == "review_id"


def test_gtopdb_normalization_preserves_peptide_interaction_source_hints():
    result = normalize_ligand(
        {"ligandId": 1234, "name": "Example peptide", "type": "Peptide"},
        [{"type": "Agonist", "targetName": "GLP-1 receptor"}],
    )
    assert result["source_identifier"] == "1234"
    assert result["candidate_name"] == "Example peptide"
    assert result["reported_target"] == "GLP-1 receptor"
    assert result["reported_mechanism"] == "Agonist at GLP-1 receptor"
    assert result["curation_status"] == "not_reviewed"


def test_gtopdb_is_gracefully_not_configured_without_api_key():
    result = asyncio.run(GtoPdbProvider().search_peptides("oxytocin", api_key=None))
    assert result["status"] == "not_configured"
    assert result["items"] == []


def test_gtopdb_research_and_global_discovery_contracts_are_registered():
    route = app.openapi()["paths"]["/api/v1/research/gtopdb-peptides"]["get"]
    params = {item["name"]: item for item in route["parameters"]}
    assert params["limit"]["schema"]["maximum"] == 30
    from app.routers.enrichment import PeptideDiscoveryRequest
    request = PeptideDiscoveryRequest(query="peptide X", sources=["gtopdb"])
    assert request.sources == ["gtopdb"]


def test_dramp_download_discovery_finds_fasta_and_fasts_datasets():
    html = """
    <a href="/downloads/download.php?filename=download_data%2FDRAMP5.0%2Fgeneral_amps.fasta">General</a>
    <a href="/downloads/download.php?filename=download_data%2FDRAMP5.0%2Fgeneral_smiles.fasta">General FASTS</a>
    <a href="/downloads/download.php?filename=download_data%2FDRAMP5.0%2Fgeneral_amps.xlsx">Workbook</a>
    """
    links = discover_fasta_downloads(html)
    assert len(links) == 2
    assert any(item["contains_smiles"] for item in links)


def test_dramp_fasta_and_fasts_merge_preserves_sequence_and_smiles():
    fasta = parse_fasta_records(
        ">DRAMP00005 Epicidin 280 (Bacteriocin)\nSLGPAIKATRQVCPKATRFVTVSCKKSDCQ\n",
        "general_amps",
    )
    fasts = parse_fasta_records(
        ">DRAMP00005 CC(C)C[C@@H]1NC(=O)\nSLGPAIKATRQVCPKATRFVTVSCKKSDCQ\n",
        "general_smiles",
        contains_smiles=True,
    )
    merged = merge_records([
        (fasta[0], "https://example.test/general.fasta"),
        (fasts[0], "https://example.test/general_smiles.fasta"),
    ])
    assert len(merged) == 1
    assert merged[0]["source_identifier"] == "DRAMP00005"
    assert merged[0]["candidate_name"] == "Epicidin 280 (Bacteriocin)"
    assert merged[0]["reported_sequence"] == "SLGPAIKATRQVCPKATRFVTVSCKKSDCQ"
    assert merged[0]["reported_chemical_form"] == "CC(C)C[C@@H]1NC(=O)"
    assert merged[0]["chemical_form"] == "CC(C)C[C@@H]1NC(=O)"
    assert set(merged[0]["dataset_categories"]) == {"general_amps", "general_smiles"}


def test_dramp_download_discovery_finds_fasta_and_fasts_datasets():
    html = """
    <a href="/downloads/download.php?filename=download_data%2FDRAMP5.0%2Fgeneral_amps.fasta">General</a>
    <a href="/downloads/download.php?filename=download_data%2FDRAMP5.0%2Fgeneral_smiles.fasta">General FASTS</a>
    <a href="/downloads/download.php?filename=download_data%2FDRAMP5.0%2Fgeneral_amps.xlsx">Workbook</a>
    """
    links = discover_fasta_downloads(html)
    assert len(links) == 2
    assert any(item["contains_smiles"] for item in links)


def test_dramp_fasta_and_fasts_merge_preserves_sequence_and_smiles():
    fasta = parse_fasta_records(
        ">DRAMP00005 Epicidin 280 (Bacteriocin)\nSLGPAIKATRQVCPKATRFVTVSCKKSDCQ\n",
        "general_amps",
    )
    fasts = parse_fasta_records(
        ">DRAMP00005 CC(C)C[C@@H]1NC(=O)\nSLGPAIKATRQVCPKATRFVTVSCKKSDCQ\n",
        "general_smiles",
        contains_smiles=True,
    )
    merged = merge_records([
        (fasta[0], "https://example.test/general.fasta"),
        (fasts[0], "https://example.test/general_smiles.fasta"),
    ])
    assert len(merged) == 1
    assert merged[0]["source_identifier"] == "DRAMP00005"
    assert merged[0]["candidate_name"] == "Epicidin 280 (Bacteriocin)"
    assert merged[0]["reported_sequence"] == "SLGPAIKATRQVCPKATRFVTVSCKKSDCQ"
    assert merged[0]["reported_chemical_form"] == "CC(C)C[C@@H]1NC(=O)"
    assert set(merged[0]["dataset_categories"]) == {"general_amps", "general_smiles"}


def test_dramp_research_and_global_discovery_contracts_are_registered():
    route = app.openapi()["paths"]["/api/v1/research/dramp-peptides"]["get"]
    params = {item["name"]: item for item in route["parameters"]}
    assert params["limit"]["schema"]["maximum"] == 100
    from app.routers.enrichment import PeptideDiscoveryRequest
    request = PeptideDiscoveryRequest(query="Epicidin", sources=["dramp"])
    assert request.sources == ["dramp"]


def test_dramp_research_and_global_discovery_contracts_are_registered():
    route = app.openapi()["paths"]["/api/v1/research/dramp-peptides"]["get"]
    params = {item["name"]: item for item in route["parameters"]}
    assert params["limit"]["schema"]["maximum"] == 100
    from app.routers.enrichment import PeptideDiscoveryRequest
    request = PeptideDiscoveryRequest(query="Epicidin", sources=["dramp"])
    assert request.sources == ["dramp"]

def _article57_test_workbook() -> bytes:
    from io import BytesIO
    from openpyxl import Workbook
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Article 57"
    sheet.append(["EMA Article 57 public product data"])
    sheet.append(["Product name", "Active substance", "Route of administration", "Country of authorisation", "Marketing authorisation holder"])
    sheet.append(["Example peptide injection", "Example peptide", "Subcutaneous", "DE", "Example Pharma GmbH"])
    sheet.append(["Unrelated tablet", "Unrelated small molecule", "Oral", "FR", "Example Labs"])
    output = BytesIO()
    workbook.save(output)
    workbook.close()
    return output.getvalue()


def test_ema_article57_parser_extracts_source_fields_without_claiming_peptide_identity():
    rows = parse_article57_workbook(_article57_test_workbook(), "example peptide", 10)
    assert len(rows) == 1
    assert rows[0]["product_name"] == "Example peptide injection"
    assert rows[0]["active_substance"] == "Example peptide"
    assert rows[0]["country_of_authorisation"] == "DE"
    assert rows[0]["jurisdiction"] == "EEA"
    assert rows[0]["source_status"] == "valid_marketing_authorisation_in_article57_snapshot"
    assert rows[0]["curation_status"] == "not_reviewed"
    assert "not a peptide identity match" in rows[0]["coverage_notice"]


def test_ema_article57_parser_rejects_workbooks_without_required_headers():
    from io import BytesIO
    from openpyxl import Workbook
    import pytest
    workbook = Workbook()
    workbook.active.append(["Name", "Substance"])
    output = BytesIO()
    workbook.save(output)
    workbook.close()
    with pytest.raises(ValueError, match="schema changed"):
        parse_article57_workbook(output.getvalue(), "peptide", 10)


def test_ema_article57_research_and_discovery_contracts_are_registered():
    route = app.openapi()["paths"]["/api/v1/research/ema-article57"]["get"]
    params = {item["name"]: item for item in route["parameters"]}
    assert params["limit"]["schema"]["maximum"] == 50
    from app.routers.enrichment import PeptideDiscoveryRequest
    request = PeptideDiscoveryRequest(query="peptide X", sources=["ema_article57"])
    assert request.sources == ["ema_article57"]


def test_dbaasp_normalization_preserves_modified_sequence_and_assay_context():
    result = normalize_peptide({
        "id": 107,
        "dbaaspId": "DBAASPR_000107",
        "name": "Example antimicrobial peptide",
        "majorName": "Example AMP",
        "sequence": "KWRR-modified",
        "sequenceLength": 12,
        "synthesisType": {"name": "Synthetic"},
        "complexity": {"name": "monomer"},
        "targetObjects": [{"name": "Outer membrane protein A"}],
        "nterminus": {"name": "Acetylated"},
        "targetActivities": [{
            "targetSpecies": {"name": "Escherichia coli"},
            "activityMeasureGroup": {"name": "MIC"},
            "activityMeasureValue": "4",
            "concentration": "4",
            "unit": {"name": "µM"},
            "medium": {"name": "MHB"},
            "ph": "7.2",
            "ionicStrength": "150 mM",
            "reference": "PMID:12345678",
        }],
        "hemoliticCytotoxicActivities": [{"activity": 5, "reference": "PMID:12345678"}],
        "synergies": [{
            "antibioticId": 12,
            "antibioticName": "Example antibiotic",
            "peptideActivity": "8",
            "peptideAntibioticActivity": "2",
            "antibioticActivity": "16",
            "fici": "0.5",
            "reference": "PMID:12345678",
        }],
        "articles": [{"title": "Example article", "pubmed": {"pubmedId": "12345678"}}],
        "unusualAminoAcids": [{"position": 4, "beforeModification": "K"}],
        "smiles": [{"smiles": "CCN"}],
    })
    assert result["source_identifier"] == "DBAASPR_000107"
    assert result["sequence"] == "KWRR-modified"
    assert result["reported_target"] == "target object: Outer membrane protein A"
    assert "N-terminus: Acetylated" in result["chemical_form"]
    assert result["target_activities"][0]["activityMeasureValue"] == "4"
    assert result["hemolytic_cytotoxic_activities"][0]["activity"] == 5
    assert result["reported_combination_activity"][0]["antibioticName"] == "Example antibiotic"
    assert result["reported_combination_activity"][0]["fici"] == "0.5"
    assert result["evidence_level"] == "source_asserted"
    assert "peptide-peptide synergy" in result["evidence_notice"]
    assert result["curation_status"] == "not_reviewed_in_peptide_intelligence"


def test_dbaasp_requires_stable_record_identifier():
    import pytest
    with pytest.raises(ValueError, match="stable identifier"):
        normalize_peptide({"name": "Missing identifier", "sequence": "GIGKFL"})


def test_dbaasp_research_and_global_discovery_contracts_are_registered():
    route = app.openapi()["paths"]["/api/v1/research/dbaasp-peptides"]["get"]
    params = {item["name"]: item for item in route["parameters"]}
    assert params["limit"]["schema"]["maximum"] == 25
    from app.routers.enrichment import PeptideDiscoveryRequest
    request = PeptideDiscoveryRequest(query="magainin", sources=["dbaasp"])
    assert request.sources == ["dbaasp"]

def test_global_discovery_candidate_dossier_and_decision_routes_are_registered():
    paths = app.openapi()["paths"]
    assert "get" in paths["/api/v1/enrichment/discovery-candidates/{candidate_id}"]
    assert "post" in paths["/api/v1/enrichment/discovery-candidates/{candidate_id}/decisions"]


def test_global_discovery_decision_requires_canonical_link_only_for_existing_peptide():
    import pytest
    from pydantic import ValidationError
    from app.routers.enrichment import GlobalDiscoveryDecision
    from uuid import uuid4

    valid = GlobalDiscoveryDecision(
        decision="accepted_as_existing_peptide",
        canonical_peptide_id=uuid4(),
        rationale="Sequence and chemical form match the verified canonical record.",
    )
    assert valid.canonical_peptide_id is not None
    with pytest.raises(ValidationError):
        GlobalDiscoveryDecision(
            decision="rejected",
            canonical_peptide_id=uuid4(),
            rationale="This candidate is not a peptide entity and is excluded.",
        )
    with pytest.raises(ValidationError):
        GlobalDiscoveryDecision(
            decision="rejected",
            rationale="                    ",
        )


def test_gtopdb_peptide_ligand_detail_normalization_preserves_interactions():
    from app.integrations.gtopdb import normalize_ligand
    result = normalize_ligand(
        {"ligandId": 1234, "name": "Example peptide", "type": "Peptide"},
        [{"targetName": "GLP-1 receptor", "type": "Agonist", "targetId": 10}],
    )
    assert result["source_identifier"] == "1234"
    assert result["reported_target"] == "GLP-1 receptor"
    assert result["reported_mechanism"] == "Agonist at GLP-1 receptor"
    assert result["curation_status"] == "not_reviewed"


def test_gtopdb_mechanism_import_route_is_registered_and_bounded():
    route = app.openapi()["paths"]["/api/v1/enrichment/peptides/{peptide_id}/mechanisms/gtopdb"]["post"]
    assert route["requestBody"]["required"] is True
    schemas = app.openapi()["components"]["schemas"]
    ligand_id = schemas["GtoPdbMechanismSubmission"]["properties"]["ligand_id"]
    assert ligand_id["exclusiveMinimum"] == 0


def test_gtopdb_mechanism_submission_requires_exact_ligand_id():
    from app.routers.enrichment import GtoPdbMechanismSubmission
    request = GtoPdbMechanismSubmission(ligand_id=1234)
    assert request.ligand_id == 1234
    with pytest.raises(Exception):
        GtoPdbMechanismSubmission(ligand_id=0)


def test_gtopdb_mechanism_curation_route_is_registered():
    paths = app.openapi()["paths"]
    route = paths["/api/v1/enrichment/peptides/{peptide_id}/mechanisms/gtopdb"]["post"]
    assert route["requestBody"]["required"] is True
    assert "/api/v1/curation/reviews/{review_id}/mechanism" in paths


def test_chembl_peptide_helm_biotherapeutic_normalization_preserves_source_moa():
    result = normalize_peptide_biotherapeutic(
        {
            "molecule_chembl_id": "CHEMBL448105",
            "pref_name": "Example peptide",
            "molecule_type": "Protein",
            "max_phase": 4,
        },
        {
            "helm_notation": "PEPTIDE1{A.L.Y.A.S.K.L.S.[am]}$$$$",
            "description": "Synthetic peptide biotherapeutic",
        },
        [{
            "mechanism_of_action": "Agonist at GLP-1 receptor",
            "action_type": "AGONIST",
            "target_chembl_id": "CHEMBL1784",
            "target_name": "GLP-1 receptor",
        }],
        "ChEMBL_37",
    )
    assert result["source_identifier"] == "CHEMBL448105"
    assert result["reported_sequence"].startswith("PEPTIDE1{")
    assert result["reported_sequence_type"] == "HELM peptide polymer notation"
    assert result["reported_target"] == "GLP-1 receptor"
    assert "Agonist at GLP-1 receptor" in result["reported_mechanism"]
    assert result["license"] == "CC BY-SA 3.0"
    assert result["curation_status"] == "not_reviewed"


def test_chembl_adapter_excludes_non_peptide_biotherapeutic_helm():
    result = normalize_peptide_biotherapeutic(
        {"molecule_chembl_id": "CHEMBL999", "pref_name": "Example antibody"},
        {"helm_notation": "PROTEIN1{A.G.C}$$$$"},
        [],
        "ChEMBL_37",
    )
    assert result is None


def test_chembl_peptide_discovery_route_and_source_contract_are_registered():
    route = app.openapi()["paths"]["/api/v1/research/chembl-peptides"]["get"]
    params = {item["name"]: item for item in route["parameters"]}
    assert params["limit"]["schema"]["maximum"] == 30
    from app.routers.enrichment import PeptideDiscoveryRequest
    request = PeptideDiscoveryRequest(query="tirzepatide", sources=["chembl"])
    assert request.sources == ["chembl"]


def test_chembl_mechanism_import_submission_requires_canonical_molecule_id():
    from app.routers.enrichment import ChEMBLMechanismSubmission
    payload = ChEMBLMechanismSubmission(chembl_id="CHEMBL448105")
    assert payload.chembl_id == "CHEMBL448105"
    with pytest.raises(Exception):
        ChEMBLMechanismSubmission(chembl_id="CHEMBL-nope")


def test_chembl_mechanism_import_route_is_registered():
    route = app.openapi()["paths"]["/api/v1/enrichment/peptides/{peptide_id}/mechanisms/chembl"]["post"]
    assert route["requestBody"]["required"] is True
    schemas = app.openapi()["components"]["schemas"]
    assert "chembl_id" in schemas["ChEMBLMechanismSubmission"]["properties"]


def test_chembl_exact_peptide_lookup_rejects_invalid_identifier_without_network():
    from app.integrations.chembl import ChEMBLProvider
    with pytest.raises(ValueError):
        asyncio.run(ChEMBLProvider().get_peptide_molecule("not-a-chembl-id"))


def test_default_global_peptide_discovery_includes_all_configured_specialist_sources():
    from app.routers.enrichment import PeptideDiscoveryRequest
    request = PeptideDiscoveryRequest(query="peptide")
    assert "dramp" in request.sources
    assert "gtopdb" in request.sources
    assert "chembl" in request.sources
    assert len(request.sources) <= 12


def test_peptide_workbook_import_route_is_registered_and_file_upload_is_required():
    operation = app.openapi()["paths"]["/api/v1/dossiers/import-workbook"]["post"]
    assert operation["requestBody"]["required"] is True
    assert operation["requestBody"]["content"]["multipart/form-data"]
    assert "post" in app.openapi()["paths"]["/api/v1/dossiers/import-workbook"]


def test_peptide_workbook_import_migration_preserves_row_level_provenance():
    sql = (MIGRATIONS_DIR / "071_peptide_workbook_imports.sql").read_text(encoding="utf-8")
    assert "peptide_workbook_import_batches" in sql
    assert "peptide_workbook_import_rows" in sql
    assert "UNIQUE (batch_id, worksheet_name, worksheet_row_number)" in sql
    assert "source_row JSONB" in sql


def test_peptide_dossier_section_editor_routes_are_registered():
    paths = app.openapi()["paths"]
    assert "/api/v1/dossiers/candidates/{candidate_id}/sections" in paths
    assert "get" in paths["/api/v1/dossiers/candidates/{candidate_id}/sections"]
    assert "/api/v1/dossiers/candidates/{candidate_id}/sections/{section_key}" in paths
    assert "put" in paths["/api/v1/dossiers/candidates/{candidate_id}/sections/{section_key}"]


def test_dossier_sections_are_organization_scoped_and_revisioned():
    sql = (MIGRATIONS_DIR / "072_editable_dossier_sections_and_media.sql").read_text(encoding="utf-8")
    assert "ENABLE ROW LEVEL SECURITY" in sql
    assert "FORCE ROW LEVEL SECURITY" in sql
    assert "peptide_dossier_section_revisions" in sql
    assert "prevent_peptide_dossier_section_revision_mutation" in sql
    assert "citations JSONB" in sql
    assert "media JSONB" in sql


def test_dossier_editor_cors_allows_put_requests():
    from app.main import app
    cors = next(m for m in app.user_middleware if m.cls.__name__ == "CORSMiddleware")
    assert "PUT" in cors.kwargs["allow_methods"]


def test_private_workbook_discovery_records_are_tenant_scoped():
    sql = (MIGRATIONS_DIR / "071_peptide_workbook_imports.sql").read_text(encoding="utf-8")
    assert "owner_organization_id UUID REFERENCES organizations(id)" in sql
    assert "peptide_discovery_candidates FORCE ROW LEVEL SECURITY" in sql
    assert "peptide_discovery_observations FORCE ROW LEVEL SECURITY" in sql
    assert "peptide_workbook_import_batches FORCE ROW LEVEL SECURITY" in sql
    assert "peptide_workbook_import_rows FORCE ROW LEVEL SECURITY" in sql


def test_workbook_import_recognizes_common_peptide_column_header_variants():
    from app.routers.workbook_import import _first_header, _normalise_header, NAME_HEADERS
    assert _normalise_header("Peptide (generic / common name)") == "peptide generic common name"
    assert _first_header(("Brand", "Peptide Name", "FDA Status"), NAME_HEADERS) == "Peptide Name"
    assert _first_header(("Drug", "Common Name"), NAME_HEADERS) == "Common Name"


def test_workbook_import_preserves_companion_worksheet_metadata():
    sql = (MIGRATIONS_DIR / "071_peptide_workbook_imports.sql").read_text(encoding="utf-8")
    assert "workbook_metadata JSONB" in sql
    assert "source_row JSONB" in sql
    from app.routers import workbook_import
    assert "Expected 128 populated peptide rows" in __import__("inspect").getsource(workbook_import.import_peptide_workbook)


def test_dossier_references_must_map_to_claims_and_use_https():
    from pydantic import ValidationError
    from app.routers.workbook_import import DossierReferenceInput, DossierMediaInput
    valid = {
        "claim_text": "Binds the target receptor in a concentration-dependent assay.",
        "title": "Primary pharmacology study",
        "source_name": "PubMed",
        "url": "https://pubmed.ncbi.nlm.nih.gov/12345678/",
        "locator": "Figure 2",
        "evidence_type": "in_vitro",
    }
    assert DossierReferenceInput(**valid).claim_text.startswith("Binds")
    with pytest.raises(ValidationError):
        DossierReferenceInput(**{**valid, "url": "http://example.org/source"})
    with pytest.raises(ValidationError):
        DossierReferenceInput(**{key: value for key, value in valid.items() if key != "claim_text"})
    media = {
        "title": "Peptide structure",
        "image_url": "https://pubchem.ncbi.nlm.nih.gov/image.png",
        "alt_text": "2D molecular structure depiction",
        "source_name": "PubChem",
        "license_or_reuse_terms": "PubChem record image terms",
    }
    assert DossierMediaInput(**media).image_url.scheme == "https"



def test_workbook_row_extractor_accepts_128_rows_and_preserves_source_fields():
    from io import BytesIO
    from openpyxl import Workbook, load_workbook
    from app.routers.workbook_import import _extract_peptide_rows

    source = Workbook()
    sheet = source.active
    sheet.title = "Peptides"
    sheet.append(["Catalogue export"])
    sheet.append(["Peptide (generic / common name)", "FDA Status", "Source note"])
    for index in range(128):
        sheet.append([f"Peptide {index + 1}", "Not approved", f"Source row {index + 1}"])
    payload = BytesIO()
    source.save(payload)
    source.close()

    parsed_workbook = load_workbook(BytesIO(payload.getvalue()), read_only=True, data_only=True)
    try:
        rows = _extract_peptide_rows(parsed_workbook)
    finally:
        parsed_workbook.close()

    assert len(rows) == 128
    assert rows[0][0] == 4
    assert rows[0][2] == "Peptide 1"
    assert rows[0][3] == "Not approved"
    assert rows[-1][2] == "Peptide 128"
    assert rows[0][1]["Source note"] == "Source row 1"


def test_workbook_row_extractor_rejects_wrong_row_count_and_missing_headers():
    from io import BytesIO
    from openpyxl import Workbook, load_workbook
    from fastapi import HTTPException
    from app.routers.workbook_import import _extract_peptide_rows

    def parse(sheet_name, header, count):
        source = Workbook()
        sheet = source.active
        sheet.title = sheet_name
        sheet.append(header)
        for index in range(count):
            sheet.append([f"Peptide {index + 1}"])
        payload = BytesIO()
        source.save(payload)
        source.close()
        parsed = load_workbook(BytesIO(payload.getvalue()), read_only=True, data_only=True)
        try:
            return _extract_peptide_rows(parsed)
        finally:
            parsed.close()

    with pytest.raises(HTTPException) as wrong_count:
        parse("Peptides", ["Peptide Name"], 127)
    assert wrong_count.value.status_code == 422
    with pytest.raises(HTTPException) as missing_header:
        parse("Peptides", ["Drug", "Status"], 128)
    assert missing_header.value.status_code == 422
    with pytest.raises(HTTPException) as missing_sheet:
        parse("Catalogue", ["Peptide Name"], 128)
    assert missing_sheet.value.status_code == 422
