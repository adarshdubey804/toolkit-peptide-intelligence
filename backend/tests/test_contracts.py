from fastapi.testclient import TestClient

from app.main import app


def test_health_contract():
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "toolkit-peptide-intelligence-api"


def test_peptide_search_rejects_invalid_pagination():
    with TestClient(app) as client:
        response = client.get("/api/v1/peptides?limit=500")
    assert response.status_code == 422
