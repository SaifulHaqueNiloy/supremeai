from fastapi.testclient import TestClient

from core.app import app

client = TestClient(app)


def test_root_endpoint_exposes_service_metadata():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "message": "Welcome to SupremeAI Backend API",
        "status": "Active",
        "docs_url": "/docs",
    }


def test_openapi_document_is_available():
    response = client.get("/openapi.json")

    assert response.status_code == 200
    document = response.json()
    assert document["info"]["title"]
    assert "/" in document["paths"]
    assert "/health/aggregated" in document["paths"]


def test_docs_route_is_available():
    response = client.get("/docs")

    assert response.status_code == 200
    assert "swagger" in response.text.lower()
