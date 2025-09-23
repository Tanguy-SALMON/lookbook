"""
Chat Integration Tests

Comprehensive testing of chat functionality using FastAPI TestClient.
Converted from scripts/archive/test_chat_direct.py for formal test suite integration.
"""

import pytest
import json
import uuid
from typing import Dict, Any, List
from fastapi.testclient import TestClient

from main import app
from lookbook_mpc.domain.entities import ChatRequest, ChatResponse


@pytest.mark.integration
@pytest.mark.chat
class TestChatIntegration:
    """Test suite for chat integration testing."""

    @pytest.fixture
    def client(self):
        """FastAPI test client fixture."""
        return TestClient(app)

    @pytest.fixture
    def session_ids(self):
        """Fixture to track created session IDs for cleanup."""
        return []

    def test_server_health(self, client):
        """Test if the app is healthy."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data
        assert "version" in data

    def test_basic_chat(self, client, session_ids):
        """Test basic chat functionality."""
        # Test simple chat message
        chat_data = {"message": "I want to do yoga"}

        response = client.post("/v1/chat", json=chat_data)
        assert response.status_code == 200

        data = response.json()

        # Validate response structure
        assert "session_id" in data
        assert "replies" in data
        assert "request_id" in data
        assert len(data.get("replies", [])) > 0

        # Check reply structure
        reply = data["replies"][0]
        assert "type" in reply
        assert "message" in reply

        session_id = data.get("session_id")
        assert session_id
        session_ids.append(session_id)

        # Check for outfit recommendations
        if data.get("outfits"):
            outfit = data["outfits"][0]
            assert "title" in outfit
            assert "score" in outfit

        return session_id

    def test_chat_with_session_id(self, client, session_ids):
        """Test chat with existing session ID."""
        if not session_ids:
            pytest.skip("No session ID available from previous test")

        session_id = session_ids[0]
        chat_data = {
            "session_id": session_id,
            "message": "What about business meeting outfit?",
        }

        response = client.post("/v1/chat", json=chat_data)
        assert response.status_code == 200

        data = response.json()
        assert data.get("session_id") == session_id

        if data.get("replies"):
            assert len(data["replies"]) > 0

    def test_chat_validation_errors(self, client):
        """Test chat input validation."""
        test_cases = [
            {"name": "Empty message", "data": {"message": ""}, "expected_status": 422},
            {
                "name": "Missing message",
                "data": {"session_id": "test"},
                "expected_status": 422,
            },
            {
                "name": "Empty session_id string",
                "data": {"session_id": "", "message": "test"},
                "expected_status": 422,
            },
            {
                "name": "Whitespace only message",
                "data": {"message": "   "},
                "expected_status": 422,
            },
        ]

        for test_case in test_cases:
            response = client.post("/v1/chat", json=test_case["data"])
            assert response.status_code == test_case["expected_status"], \
                f"Failed for case: {test_case['name']}"

    def test_chat_suggestions(self, client):
        """Test chat suggestions endpoint."""
        response = client.get("/v1/chat/suggestions")
        assert response.status_code == 200

        data = response.json()
        assert "suggestions" in data
        assert "categories" in data

        suggestions = data.get("suggestions", [])
        assert len(suggestions) > 0

        # Check suggestion structure
        if suggestions:
            suggestion = suggestions[0]
            required_fields = ["id", "prompt", "category", "description"]
            for field in required_fields:
                assert field in suggestion, f"Suggestion missing {field} field"

    def test_session_management(self, client, session_ids):
        """Test session management endpoints."""
        if not session_ids:
            pytest.skip("No session ID available")

        session_id = session_ids[0]

        # Test list sessions
        response = client.get("/v1/chat/sessions")
        assert response.status_code == 200

        data = response.json()
        assert "sessions" in data
        assert "pagination" in data

        # Test get specific session
        response = client.get(f"/v1/chat/sessions/{session_id}")
        assert response.status_code == 200

        data = response.json()
        required_fields = [
            "session_id",
            "created_at",
            "messages",
            "context",
            "message_count",
        ]
        for field in required_fields:
            assert field in data, f"Session details missing {field} field"

        # Test clear session context
        response = client.post(f"/v1/chat/sessions/{session_id}/clear")
        assert response.status_code == 200

    def test_conversation_flow(self, client, session_ids):
        """Test a complete conversation flow."""
        conversation_steps = [
            "I need an outfit for yoga",
            "What about something for a business meeting?",
            "Show me casual outfits under ฿2000",
            "I prefer black and white colors",
            "Any recommendations for summer season?",
        ]

        session_id = None

        for i, message in enumerate(conversation_steps):
            chat_data = {"message": message}
            if session_id:
                chat_data["session_id"] = session_id

            response = client.post("/v1/chat", json=chat_data)
            assert response.status_code == 200, f"Failed at conversation step {i + 1}"

            data = response.json()
            if not session_id:
                session_id = data.get("session_id")
                if session_id:
                    session_ids.append(session_id)

            # Check for meaningful responses
            has_replies = len(data.get("replies", [])) > 0
            has_outfits = data.get("outfits") is not None

            assert has_replies or has_outfits, f"No content in response for step {i + 1}"

    def test_fashion_specific_queries(self, client, session_ids):
        """Test fashion-specific chat queries."""
        fashion_queries = [
            "I want to look slim",
            "Beach vacation outfits",
            "Party dress for Saturday night",
            "Professional work clothes",
            "Comfortable sportswear",
            "Elegant formal wear",
            "Casual weekend outfits",
        ]

        for query in fashion_queries:
            chat_data = {"message": query}
            response = client.post("/v1/chat", json=chat_data)
            assert response.status_code == 200, f"Failed for query: {query}"

            data = response.json()
            session_id = data.get("session_id")
            if session_id and session_id not in session_ids:
                session_ids.append(session_id)

            # Check if we got meaningful responses
            has_replies = len(data.get("replies", [])) > 0
            has_outfits = data.get("outfits") is not None

            assert has_replies or has_outfits, f"No content for fashion query: {query}"

    def test_error_handling(self, client):
        """Test error handling scenarios."""
        # Test non-existent session
        fake_session_id = str(uuid.uuid4())
        response = client.get(f"/v1/chat/sessions/{fake_session_id}")
        assert response.status_code == 404

        # Test invalid session ID for deletion
        response = client.delete(f"/v1/chat/sessions/{fake_session_id}")
        assert response.status_code == 404

        # Test malformed data
        response = client.post("/v1/chat", json={"invalid": "data"})
        assert response.status_code == 422

    def test_session_cleanup(self, client, session_ids):
        """Test session cleanup (delete created sessions)."""
        for session_id in session_ids:
            response = client.delete(f"/v1/chat/sessions/{session_id}")
            assert response.status_code == 200, f"Failed to delete session {session_id}"

    def test_chat_entity_validation(self, client):
        """Test ChatRequest and ChatResponse entity validation."""
        # Test valid ChatRequest
        try:
            ChatRequest(session_id="test-123", message="Hello")
        except Exception as e:
            pytest.fail(f"Valid ChatRequest creation failed: {e}")

        # Test invalid ChatRequest (empty message)
        with pytest.raises(ValueError):
            ChatRequest(session_id="test", message="")

    @pytest.mark.parametrize("query", [
        "Red dress for date night",
        "Black suit for interview",
        "Summer tops under ฿1000",
    ])
    def test_parametrized_fashion_queries(self, client, query):
        """Test additional fashion queries using parametrization."""
        chat_data = {"message": query}
        response = client.post("/v1/chat", json=chat_data)
        assert response.status_code == 200

        data = response.json()
        has_replies = len(data.get("replies", [])) > 0
        has_outfits = data.get("outfits") is not None

        assert has_replies or has_outfits, f"No content for parametrized query: {query}"