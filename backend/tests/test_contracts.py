from app.main import app


def test_health_route_is_registered():
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
