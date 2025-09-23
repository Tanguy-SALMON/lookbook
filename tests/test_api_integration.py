"""
API Integration Tests

Comprehensive testing of all API endpoints using pytest and httpx.
Converted from scripts/test_api.py for formal test suite integration.
"""

import pytest
import asyncio
from typing import Dict, Any
import httpx
from fastapi.testclient import TestClient

from main import app


@pytest.mark.integration
@pytest.mark.api
class TestAPIIntegration:
    """Test suite for API integration testing."""

    @pytest.fixture
    def client(self):
        """FastAPI test client fixture."""
        return TestClient(app)

    @pytest.fixture
    async def async_client(self):
        """Async HTTP client for external API calls."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            yield client

    @pytest.fixture
    def base_url(self):
        """Base URL for API endpoints."""
        return "http://localhost:8000"

    def test_health_endpoints(self, client):
        """Test health and readiness endpoints."""
        # Test health endpoint
        response = client.get("/health")
        assert response.status_code == 200
        health_data = response.json()
        assert "status" in health_data
        assert health_data["status"] == "healthy"

        # Test readiness endpoint (may return 503 if services are down)
        response = client.get("/ready")
        # Accept both 200 (ready) and 503 (not ready) as valid responses
        assert response.status_code in [200, 503]
        ready_data = response.json()
        assert "status" in ready_data
        assert "checks" in ready_data

    def test_ingest_api(self, client):
        """Test ingest API endpoints (may not exist in all configurations)."""
        # Test item ingestion - this endpoint may not exist
        ingest_data = {"limit": 10, "since": None}

        response = client.post(
            "/v1/ingest/items",
            json=ingest_data,
            headers={"Content-Type": "application/json"},
        )

        # Accept 404 if endpoint doesn't exist, or 200/202 if it does
        if response.status_code == 404:
            pytest.skip("Ingest API not available in this configuration")
        else:
            # Accept both 202 (async processing) and 200 (immediate response)
            assert response.status_code in [200, 202]

            if response.status_code == 202:
                ingest_response = response.json()
                assert "status" in ingest_response
                assert "items_processed" in ingest_response

                # Test listing items
                response = client.get("/v1/ingest/items?limit=5")
                assert response.status_code == 200
                items_data = response.json()
                assert "items" in items_data
                assert "pagination" in items_data

                # Test ingestion stats
                response = client.get("/v1/ingest/stats")
                assert response.status_code == 200
                stats_data = response.json()
                assert "total_items" in stats_data

    def test_recommendation_api(self, client):
        """Test recommendation API endpoints."""
        # Test outfit recommendations
        reco_data = {
            "text_query": "I want to do yoga",
            "budget": 80,
            "size": "L",
            "week": "2025-W40",
            "preferences": {"palette": ["dark"]},
        }

        response = client.post(
            "/v1/recommendations",
            json=reco_data,
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 200
        reco_response = response.json()
        assert "outfits" in reco_response
        assert "constraints_used" in reco_response

        if reco_response["outfits"]:
            outfit = reco_response["outfits"][0]
            assert "title" in outfit
            assert "score" in outfit

        # Test preview endpoint
        response = client.get("/v1/recommendations/preview?text_query=yoga&budget=50")
        assert response.status_code == 200
        preview_data = response.json()
        assert "total_available" in preview_data

        # Test constraints endpoint
        response = client.get("/v1/recommendations/constraints")
        assert response.status_code == 200
        constraints_data = response.json()
        assert "sizes" in constraints_data
        assert "categories" in constraints_data

        # Test popular recommendations
        response = client.get("/v1/recommendations/popular?limit=3")
        assert response.status_code == 200
        popular_data = response.json()
        assert "recommendations" in popular_data

    def test_chat_api(self, client):
        """Test chat API endpoints."""
        # Test chat turn
        chat_data = {"message": "I want to do yoga"}

        response = client.post(
            "/v1/chat",
            json=chat_data,
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 200
        chat_response = response.json()
        assert "replies" in chat_response
        assert "session_id" in chat_response
        assert len(chat_response["replies"]) > 0

        # Check first reply structure
        reply = chat_response["replies"][0]
        assert "type" in reply
        assert "message" in reply

        session_id = chat_response.get("session_id")
        assert session_id

        # Test session listing
        response = client.get("/v1/chat/sessions?limit=5")
        assert response.status_code == 200
        sessions_data = response.json()
        assert "sessions" in sessions_data
        assert "pagination" in sessions_data

        # Test chat suggestions
        response = client.get("/v1/chat/suggestions")
        assert response.status_code == 200
        suggestions_data = response.json()
        assert "suggestions" in suggestions_data
        assert "categories" in suggestions_data
        assert len(suggestions_data.get("suggestions", [])) > 0

    def test_images_api(self, client):
        """Test images API endpoints (may fail if vision service is down)."""
        # Test image info (mock image)
        image_key = "test-image.jpg"

        response = client.get(f"/v1/images/info/{image_key}")
        # Accept 200 (success) or 502 (vision service down)
        assert response.status_code in [200, 502]

        if response.status_code == 200:
            image_info = response.json()
            assert "image_key" in image_info
            assert "available" in image_info

            # Test image redirect (don't follow redirects to check 302 status)
            response = client.get(
                f"/v1/images/{image_key}/redirect", follow_redirects=False
            )
            assert response.status_code == 302
            assert "location" in response.headers

            # Test batch images
            response = client.get(f"/v1/images/batch?image_keys=test1.jpg,test2.jpg")
            assert response.status_code == 200
            batch_data = response.json()
            assert "total_requested" in batch_data
            assert "successful" in batch_data

            # Test CORS preflight
            response = client.options(f"/v1/images/{image_key}")
            assert response.status_code == 200
        else:
            # Vision service is down, skip remaining tests
            pytest.skip("Vision service not available")

    def test_openapi_docs(self, client):
        """Test OpenAPI documentation endpoints."""
        # Test OpenAPI JSON
        response = client.get("/openapi.json")
        assert response.status_code == 200
        openapi_data = response.json()
        assert "paths" in openapi_data
        assert "components" in openapi_data
        assert "schemas" in openapi_data["components"]

        # Test Swagger UI redirect
        response = client.get("/docs")
        assert response.status_code == 200
        # Should return HTML content
        assert "html" in response.headers.get("content-type", "").lower()

        # Test ReDoc
        response = client.get("/redoc")
        assert response.status_code == 200

    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/", headers={"Accept": "application/json"})
        assert response.status_code == 200
        root_data = response.json()
        assert "service" in root_data
        assert "version" in root_data
        assert "docs" in root_data
        assert "health" in root_data

    def test_settings_api(self, client):
        """Test settings API endpoints using TestClient."""
        # Test environment endpoint
        response = client.get("/v1/settings/environment")
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert data["success"] is True
        assert "data" in data

        # Test settings POST endpoint (may not be implemented)
        settings_data = {"test": "data"}
        response = client.post("/v1/settings", json=settings_data)
        # Accept both 200 (implemented) and 405 (not implemented)
        assert response.status_code in [200, 405]
        if response.status_code == 200:
            data = response.json()
            assert "success" in data
            assert data["success"] is True
