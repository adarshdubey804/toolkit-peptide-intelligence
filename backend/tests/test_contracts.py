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
    assert migrations == ["001_initial_schema.sql", "002_provenance_curation.sql"]
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
