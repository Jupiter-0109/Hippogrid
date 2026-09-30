"""Pytest fixtures and configuration for HippoGrid test suite."""
import pytest
from fastapi.testclient import TestClient
from backend.main import app


@pytest.fixture(scope="session")
def client() -> TestClient:
    """Create a test client for the FastAPI application."""
    return TestClient(app)
