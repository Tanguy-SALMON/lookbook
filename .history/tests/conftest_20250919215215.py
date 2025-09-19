"""
Pytest configuration and fixtures for Lookbook-MPC tests.
"""

import pytest
import os
from fastapi.testclient import TestClient


@pytest.fixture(scope="session")
def test_env():
    """Set up test environment variables."""
    # Store original environment variables
    original_env = {}

    # Set test environment variables
    test_vars = {
        "OLLAMA_HOST": "http://localhost:11434",
        "OLLAMA_VISION_MODEL": "qwen2.5-vl:7b",
        "OLLAMA_TEXT_MODEL": "qwen3",
        "S3_BASE_URL": "https://test-cdn.example.com",
        "LOG_LEVEL": "DEBUG",
        "TESTING": "true"
    }

    # Store and set environment variables
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
def client(test_env):
    """Create test client with test environment."""
    from main import app
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def sample_item_data():
    """Sample item data for testing."""
    return {
        "id": 1,
        "sku": "1295990003",
        "title": "Classic Cotton T-Shirt",
        "price": 29.99,
        "size_range": "XS-XXL",
        "image_key": "e341e2f3a4b5c6d7e8f9.jpg",
        "attributes": {
            "color": "white",
            "material": "cotton",
            "category": "top",
            "vision_attributes": {
                "color": "white",
                "category": "top",
                "material": "cotton",
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
        "objectives": ["comfort", "stretch"],
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
                "price": 29.99,
                "score": 0.85
            },
            {
                "item_id": 2,
                "sku": "1295990011",
                "role": "bottom",
                "image_url": "https://test-cdn.example.com/f567g8h9i0j1k2l3m4n5.jpg",
                "title": "Yoga Leggings",
                "price": 49.99,
                "score": 0.82
            }
        ],
        "score": 0.83,
        "rationale": "Perfect yoga outfit with stretch fabrics and comfortable fit",
        "constraints_used": {
            "activity": "yoga",
            "formality": "athleisure",
            "budget_max": 80
        }
    }


@pytest.fixture
def mock_ollama_response():
    """Mock Ollama response for testing."""
    return {
        "model": "qwen2.5-vl:7b",
        "response": "COLOR: white\n\nDESCRIPTION: Classic cotton t-shirt perfect for everyday wear.\n\nATTRIBUTES:\nPlus Size: No\nMaterial: Cotton\nPattern: Plain\nStyle: Basic\nSeason: Summer\nOccasion: Casual"
    }


@pytest.fixture
def mock_image_data():
    """Mock image data for testing."""
    return b"fake_image_data_for_testing_purposes"


@pytest.fixture
def sample_rules():
    """Sample rules data for testing."""
    return [
        {
            "id": 1,
            "name": "yoga_outfit",
            "intent": "yoga",
            "constraints": {
                "category": ["top", "bottom", "dress"],
                "material": ["cotton", "nylon", "spandex"],
                "formality": "athleisure",
                "budget_max": 100
            }
        },
        {
            "id": 2,
            "name": "casual_weekend",
            "intent": "casual",
            "constraints": {
                "category": ["top", "bottom", "dress"],
                "formality": "casual",
                "budget_max": 200
            }
        }
    ]


@pytest.fixture
def sample_constraints():
    """Sample constraints data for testing."""
    return {
        "category": ["top", "bottom"],
        "material": ["cotton", "denim"],
        "max_price": 100,
        "min_price": 20,
        "color": ["blue", "black", "white"]
    }


@pytest.fixture
def sample_search_filters():
    """Sample search filters for testing."""
    return {
        "category": "top",
        "color": "blue",
        "max_price": 50,
        "limit": 10
    }


@pytest.fixture
def sample_chat_message():
    """Sample chat message for testing."""
    return {
        "session_id": "test-session-123",
        "message": "I want to do yoga"
    }


@pytest.fixture
def sample_chat_response():
    """Sample chat response for testing."""
    return {
        "session_id": "test-session-123",
        "replies": [
            {
                "message": "I'd be happy to help you find yoga outfits! Let me search for comfortable and stretchy options.",
                "type": "text"
            }
        ],
        "outfits": [
            {
                "items": [
                    {
                        "item_id": 1,
                        "sku": "1295990003",
                        "role": "top",
                        "image_url": "https://test-cdn.example.com/e341e2f3a4b5c6d7e8f9.jpg",
                        "title": "Yoga Top",
                        "price": 35.99,
                        "score": 0.88
                    }
                ],
                "score": 0.88,
                "rationale": "Perfect yoga top with stretch fabric and breathable design"
            }
        ]
    }


@pytest.fixture
def sample_image_key():
    """Sample image key for testing."""
    return "test_image_key.jpg"


@pytest.fixture
def sample_image_url():
    """Sample image URL for testing."""
    return "https://test-cdn.example.com/test_image_key.jpg"


@pytest.fixture
def sample_ingest_request():
    """Sample ingest request for testing."""
    return {
        "limit": 25,
        "since": "2025-01-19T00:00:00Z"
    }


@pytest.fixture
def sample_ingest_response():
    """Sample ingest response for testing."""
    return {
        "status": "completed",
        "items_processed": 25,
        "items_failed": 0,
        "timestamp": "2025-01-19T14:00:00Z",
        "details": {
            "total_found": 30,
            "successfully_processed": 25,
            "failed": 5
        }
    }


@pytest.fixture
def sample_recommendation_request():
    """Sample recommendation request for testing."""
    return {
        "text_query": "I want to do yoga",
        "budget": 80,
        "size": "L",
        "week": "2025-W40",
        "preferences": {
            "palette": ["dark"],
            "objectives": ["comfort", "stretch"]
        }
    }


@pytest.fixture
def sample_recommendation_response():
    """Sample recommendation response for testing."""
    return {
        "constraints_used": {
            "activity": "yoga",
            "formality": "athleisure",
            "budget_max": 80
        },
        "outfits": [
            {
                "items": [
                    {
                        "item_id": 123,
                        "sku": "1295990003",
                        "role": "top",
                        "image_url": "https://test-cdn.example.com/e341e2f3a4b5c6d7e8f9.jpg",
                        "title": "Yoga Top",
                        "price": 35.99,
                        "score": 0.88
                    },
                    {
                        "item_id": 456,
                        "sku": "1295990011",
                        "role": "bottom",
                        "image_url": "https://test-cdn.example.com/f567g8h9i0j1k2l3m4n5.jpg",
                        "title": "Yoga Leggings",
                        "price": 44.99,
                        "score": 0.85
                    }
                ],
                "score": 0.86,
                "rationale": "Perfect yoga outfit with stretch fabrics and comfortable fit"
            }
        ]
    }