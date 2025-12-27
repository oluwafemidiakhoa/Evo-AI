"""Tests for FastAPI application."""

import pytest
from fastapi.testclient import TestClient

from evo_ai.api.app import create_app


@pytest.fixture
def client():
    """Create test client."""
    app = create_app()
    return TestClient(app)


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "healthy"
    assert "version" in data
    assert "timestamp" in data
    assert "services" in data


def test_openapi_docs(client):
    """Test OpenAPI documentation is available."""
    response = client.get("/api/docs")
    assert response.status_code == 200


def test_openapi_json(client):
    """Test OpenAPI JSON schema."""
    response = client.get("/api/openapi.json")

    assert response.status_code == 200
    data = response.json()

    assert data["info"]["title"] == "Evo-AI Platform API"
    assert data["info"]["version"] == "1.0.0"


def test_metrics_endpoint(client):
    """Test Prometheus metrics endpoint."""
    response = client.get("/metrics")

    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]


def test_cors_headers(client):
    """Test CORS headers are present."""
    response = client.options("/health")

    # CORS headers should be present
    assert "access-control-allow-origin" in response.headers


def test_api_routes_exist(client):
    """Test that API routes are registered."""
    response = client.get("/api/openapi.json")
    data = response.json()

    paths = data["paths"]

    # Campaign routes
    assert "/api/campaigns" in paths
    assert "/api/campaigns/{campaign_id}" in paths

    # Round routes
    assert "/api/campaigns/{campaign_id}/rounds" in paths

    # Variant routes
    assert "/api/variants" in paths
    assert "/api/variants/{variant_id}" in paths
    assert "/api/variants/{variant_id}/lineage" in paths

    # Evaluation routes
    assert "/api/evaluations" in paths

    # Report routes
    assert "/api/reports" in paths
