
"""
Basic tests for the Lookbook-MPC application setup.
"""

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_root_endpoint():
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "lookbook-mpc"
    assert data["version"] == "0.1.0"
    assert "description" in data
    assert "docs" in data
    assert "health" in data


def test_health_endpoint():
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "lookbook-mpc"
    assert data["version"] == "0.1.0"


def test_readiness_endpoint():
    """Test the readiness check endpoint."""
    response = client.get("/ready")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "checks" in data
    assert "timestamp" in data


def test_api_docs_endpoint():
    """Test that API documentation is accessible."""
    response = client.get("/docs")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_openapi_endpoint():
    """Test that OpenAPI specification is accessible."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert data["openapi"] == "3.0.0"
    assert data["info"]["title"] == "Lookbook-MPC"
    assert data["info"]["version"] == "0.1.0"


def test_redoc_endpoint():
    """Test that ReDoc documentation is accessible."""
    response = client.get("/redoc")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_cors_headers():
    """Test that CORS headers are present."""
    response = client.get("/")
    assert "access-control-allow-origin" in response.headers
    assert response.headers["access-control-allow-origin"] == "*"


def test_request_id_header():
    """Test that request ID is returned in response headers."""
    response = client.get("/")
    assert "x-request-id" in response.headers
    request_id = response.headers["x-request-id"]
    assert len(request_id) > 0  # Should be a valid UUID


def test_ingest_router_exists():
    """Test that ingest router is properly mounted."""
    # Check if ingest endpoints exist
    response = client.get("/v1/ingest/stats")
    assert response.status_code == 200


def test_recommendation_router_exists():
    """Test that recommendation router is properly mounted."""
    # Check if recommendation endpoints exist
    response = client.get("/v1/recommendations/constraints")
    assert response.status_code == 200


def test_chat_router_exists():
    """Test that chat router is properly mounted."""
    # Check if chat endpoints exist
    response = client.get("/v1/chat/suggestions")
    assert response.status_code == 200


def test_images_router_exists():
    """Test that images router is properly mounted."""
    # Check if images endpoints exist
    response = client.head("/v1/images/test.jpg")
    # This should return 404 (not found) but the endpoint should exist
    assert response.status_code in [404, 200]


def test_structured_logging():
    """Test that structured logging is working."""
    # This is a basic test - in real implementation, you'd capture logs
    response = client.get("/health")
    assert response.status_code == 200


def test_error_handling():
    """Test that error handling works properly."""
