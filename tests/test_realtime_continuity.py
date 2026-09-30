"""Test suite for Phase 12 Realtime Continuity Alert Simulation and Audit Logging.
Healthcare Infrastructure & Primary-care Planning Optimization Grid
"""
import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_simulate_continuity_alert():
    """Test inserting a simulated critical alert through the protected FastAPI endpoint."""
    payload = {
        "phc_code": "PHC-DST-A1-04",
        "service_id": "diarrhoeal_care",
        "status": "CRITICAL",
        "hours_to_compromise": 8.5,
        "primary_bottleneck": "Automated Flash Flood Inundation & ORS Depletion",
    }
    response = client.post("/api/v1/continuity/simulate-alert", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "INSERTED"
    assert data["continuity_status"] == "CRITICAL"
    assert data["hours_to_compromise"] == 8.5
    assert data["primary_bottleneck"] == "Automated Flash Flood Inundation & ORS Depletion"
    assert data["realtime_broadcast"] is True
    assert "id" in data


def test_get_recent_continuity_events():
    """Test retrieving recently recorded continuity events from PostgreSQL."""
    response = client.get("/api/v1/continuity/events?limit=5")
    assert response.status_code == 200
    events = response.json()
    assert isinstance(events, list)
    assert len(events) > 0
    first_event = events[0]
    assert "id" in first_event
    assert "status" in first_event
    assert "hours_to_compromise" in first_event
