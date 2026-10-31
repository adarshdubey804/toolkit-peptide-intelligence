from app.integrations.clinicaltrials import normalize_study
from app.main import app


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
