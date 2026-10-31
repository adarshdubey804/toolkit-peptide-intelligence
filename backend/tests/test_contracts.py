from uuid import UUID

from fastapi import FastAPI
from fastapi.testclient import TestClient

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


def test_peptide_profile_requires_uuid_path_parameter():
    operation = app.openapi()["paths"]["/api/v1/peptides/{peptide_id}"]["get"]
    parameter = next(item for item in operation["parameters"] if item["name"] == "peptide_id")
    assert parameter["schema"]["format"] == "uuid"
