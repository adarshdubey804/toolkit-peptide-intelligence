from pathlib import Path

from app.integrations.clinicaltrials import normalize_study
from app.main import MIGRATIONS_DIR, app


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
    assert migrations == ["001_initial_schema.sql", "002_provenance_curation.sql", "003_authentication.sql", "004_organization_workspaces.sql", "005_curation_workflow.sql", "006_enrichment_candidates.sql", "007_vendor_directory.sql", "008_analytical_method_intelligence.sql", "009_formulation_stability_intelligence.sql", "010_process_development_intelligence.sql"]
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
    assert len(SOURCE_HOSTS) == 4


def test_vendor_directory_routes_and_migration_are_registered():
    paths = app.openapi()["paths"]
    assert "/api/v1/vendors" in paths
    assert "get" in paths["/api/v1/vendors"]
    assert "post" in paths["/api/v1/vendors"]
    assert "/api/v1/vendors/{vendor_id}/services" in paths
    assert "/api/v1/vendors/{vendor_id}/certifications" in paths
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
