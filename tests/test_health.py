"""Tests for health check endpoints."""
from fastapi.testclient import TestClient


def test_get_health(client: TestClient) -> None:
    """Validate GET /health returns status ok and project HippoGrid."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "project": "HippoGrid",
    }


def test_get_health_db(client: TestClient) -> None:
    """Validate GET /health/db returns project HippoGrid and database status dictionary."""
    response = client.get("/health/db")
    assert response.status_code == 200
    data = response.json()
    assert data["project"] == "HippoGrid"
    assert "database" in data
    assert "connected" in data["database"]
    assert "latency_ms" in data["database"]
