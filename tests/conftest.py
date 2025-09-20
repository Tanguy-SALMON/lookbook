
"""
Pytest Configuration

This module contains pytest configuration and fixtures.
"""

import pytest
import asyncio
import os
from fastapi.testclient import TestClient


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function", autouse=True)
def test_env():
    """Set up test environment variables."""
    # Store original environment variables
    original_env = {}

    # Test environment variables
    test_vars = {
        "OLLAMA_HOST": "http://localhost:11434",
        "OLLAMA_VISION_MODEL": "qwen2.5-vl:7b",
        "OLLAMA_TEXT_MODEL": "qwen3:4b",  # Use 4B variant for faster inference
        "S3_BASE_URL": "https://test-cdn.example.com",
        "LOG_LEVEL": "DEBUG",
        "TESTING": "true"
    }

    # Store and set test environment variables
    for key, value in test_vars.items():
        original_env[key] = os.environ.get(key)
        os.environ[key] = value

    yield

    # Restore original environment variables
    for key, value in original_env.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value


@pytest.fixture
def sample_item_data():
    """Sample item data for testing."""
    return {
        "id": 1,
        "sku": "1295990003",
        "title": "Classic Cotton T-Shirt",
        "price": 29.99,
        "size_range": ["XS", "S", "M", "L", "XL", "XXL"],
        "image_key": "e341e2f3a4b5c6d7e8f9.jpg",
        "attributes": {
            "vision_attributes": {
                "color": "white",
                "material": "cotton",
                "category": "top",
                "pattern": "plain",
                "style": "basic",
                "season": "summer",
                "occasion": "casual",
                "fit": "regular",
                "plus_size": False,
                "description": "Classic cotton t-shirt"
            }
        },
        "in_stock": True
    }


@pytest.fixture
def sample_intent_data():
    """Sample intent data for testing."""
    return {
        "intent": "recommend_outfits",
        "activity": "yoga",
        "occasion": "casual",
        "budget_max": 80,
        "objectives": ["comfortable", "stretch"],
        "palette": ["dark"],
        "formality": "athleisure",
        "timeframe": "this_weekend",
        "size": "L"
    }


@pytest.fixture
def sample_outfit_data():
    """Sample outfit data for testing."""
    return {
        "items": [
            {
                "item_id": 1,
                "sku": "1295990003",
                "role": "top",
                "image_url": "https://test-cdn.example.com/e341e2f3a4b5c6d7e8f9.jpg",
                "title": "Classic Cotton T-Shirt",
                "price": 29.99
            },
            {
                "item_id": 2,
                "sku": "1295990011",
                "role": "bottom",
                "image_url": "https://test-cdn.example.com/f567g8h9i0j1k2l3m4n5.jpg",
                "title": "Slim Fit Jeans",
                "price": 79.99
            }
        ],
        "score": 0.85,
        "rationale": "Perfect yoga outfit with stretch fabrics and comfortable fit"
    }


@pytest.fixture
def sample_chat_message():
    """Sample chat message for testing."""
    return {
        "session_id": "test-session-123",
        "message": "I want to do yoga"
    }


# Configure pytest settings
def pytest_configure(config):
    """Configure pytest settings."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers."""
    for item in items:
        # Mark all tests as either unit or integration
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        else:
            item.add_marker(pytest.mark.unit)

        # Mark slow tests
        if "slow" in item.nodeid or "performance" in item.nodeid:
            item.add_marker(pytest.mark.slow)