"""
Domain Entities Tests

This module contains unit tests for domain entities and validation.
"""

import pytest
from datetime import datetime
from pathlib import Path
import sys

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from lookbook_mpc.domain.entities import (
    Item,
    Outfit,
    OutfitItem,
    Rule,
    Intent,
    Size,
    Category,
    Material,
    Pattern,
    Season,
    Occasion,
    Fit,
    Role,
    VisionAttributes,
    RecommendationRequest,
    RecommendationResponse,
    IngestRequest,
    IngestResponse,
    ChatRequest,
    ChatResponse,
)


class TestSize:
    """Test Size enum."""

    def test_size_values(self):
        """Test that all expected size values exist."""
        assert Size.XS == "XS"
        assert Size.S == "S"
        assert Size.M == "M"
        assert Size.L == "L"
        assert Size.XL == "XL"
        assert Size.XXL == "XXL"
        assert Size.XXXL == "XXXL"
        assert Size.PLUS == "PLUS"
        assert Size.ONE_SIZE == "ONE_SIZE"
        assert Size.PETITE == "PETITE"
        assert Size.TALL == "TALL"
        assert Size.CUSTOM == "CUSTOM"


class TestCategory:
    """Test Category enum."""

    def test_category_values(self):
        """Test that all expected category values exist."""
        assert Category.TOP == "top"
        assert Category.BOTTOM == "bottom"
        assert Category.DRESS == "dress"
        assert Category.OUTERWEAR == "outerwear"
        assert Category.SHOES == "shoes"
        assert Category.ACCESSORY == "accessory"


class TestItem:
    """Test Item entity."""

    def test_item_creation(self):
        """Test creating a valid item."""
        item = Item(
            sku="TEST001",
            title="Test Item",
            price=29.99,
            size_range=[Size.S, Size.M, Size.L],
            image_key="test-image.jpg",
            attributes={"color": "blue", "material": "cotton"},
            in_stock=True,
        )

        assert item.sku == "TEST001"
        assert item.title == "Test Item"
        assert item.price == 29.99
        assert item.size_range == [Size.S, Size.M, Size.L]
        assert item.image_key == "test-image.jpg"
        assert item.attributes == {"color": "blue", "material": "cotton"}
        assert item.in_stock is True

    def test_item_validation(self):
        """Test item validation."""
        # Test negative price
        with pytest.raises(ValueError, match="price cannot be negative"):
            Item(
                sku="TEST001",
                title="Test",
                price=-10.0,
                size_range=[],
                image_key="test.jpg",
            )

        # Test empty SKU
        with pytest.raises(ValueError):
            Item(sku="", title="Test", price=10.0, size_range=[], image_key="test.jpg")

        # Test invalid size range
        with pytest.raises(ValueError):
            Item(
                sku="TEST001",
                title="Test",
                price=10.0,
                size_range="invalid",
                image_key="test.jpg",
            )

        # Test too many sizes
        with pytest.raises(
            ValueError, match="size_range cannot have more than 20 sizes"
        ):
            Item(
                sku="TEST001",
                title="Test",
                price=10.0,
                size_range=[Size.S] * 25,
                image_key="test.jpg",
            )


class TestOutfit:
    """Test Outfit entity."""

    def test_outfit_creation(self):
        """Test creating a valid outfit."""
        outfit = Outfit(
            title="Summer Casual",
            intent_tags={"occasion": "casual", "season": "summer"},
            rationale="Perfect for warm weather",
            score=0.85,
        )

        assert outfit.title == "Summer Casual"
        assert outfit.intent_tags == {"occasion": "casual", "season": "summer"}
        assert outfit.rationale == "Perfect for warm weather"
        assert outfit.score == 0.85

    def test_outfit_validation(self):
        """Test outfit validation."""
        # Test empty title
        with pytest.raises(ValueError):
            Outfit(title="", intent_tags={}, rationale="test")

        # Test invalid intent_tags
        with pytest.raises(ValueError):
            Outfit(title="Test", intent_tags="invalid", rationale="test")


class TestOutfitItem:
    """Test OutfitItem entity."""

    def test_outfit_item_creation(self):
        """Test creating a valid outfit item."""
        outfit_item = OutfitItem(outfit_id=1, item_id=2, role=Role.TOP)

        assert outfit_item.outfit_id == 1
        assert outfit_item.item_id == 2
        assert outfit_item.role == Role.TOP

    def test_outfit_item_validation(self):
        """Test outfit item validation."""
        # Test negative outfit_id
        with pytest.raises(ValueError):
            OutfitItem(outfit_id=-1, item_id=2, role=Role.TOP)

        # Test negative item_id
        with pytest.raises(ValueError):
            OutfitItem(outfit_id=1, item_id=-2, role=Role.TOP)

        # Test same outfit and item ID
        with pytest.raises(
            ValueError, match="outfit_id and item_id cannot be the same"
        ):
            OutfitItem(outfit_id=1, item_id=1, role=Role.TOP)


class TestRule:
    """Test Rule entity."""

    def test_rule_creation(self):
        """Test creating a valid rule."""
        rule = Rule(
            name="Yoga Rule",
            intent="yoga",
            constraints={"category": ["activewear"], "material": ["stretch"]},
            priority=5,
            is_active=True,
        )

        assert rule.name == "Yoga Rule"
        assert rule.intent == "yoga"
        assert rule.constraints == {"category": ["activewear"], "material": ["stretch"]}
        assert rule.priority == 5
        assert rule.is_active is True

    def test_rule_validation(self):
        """Test rule validation."""
        # Test empty name
        with pytest.raises(ValueError):
            Rule(name="", intent="test", constraints={})

        # Test empty intent
        with pytest.raises(ValueError):
            Rule(name="Test", intent="", constraints={})

        # Test name and intent same
        with pytest.raises(ValueError, match="name and intent cannot be the same"):
            Rule(name="test", intent="test", constraints={})


class TestIntent:
    """Test Intent entity."""

    def test_intent_creation(self):
        """Test creating a valid intent."""
        intent = Intent(
            intent="recommend_outfits",
            activity="yoga",
            occasion=Occasion.YOGA,
            budget_max=50.0,
            objectives=["slimming"],
            palette=["dark", "monochrome"],
            formality="casual",
            timeframe="this_weekend",
            size=Size.L,
        )

        assert intent.intent == "recommend_outfits"
        assert intent.activity == "yoga"
        assert intent.occasion == Occasion.YOGA
        assert intent.budget_max == 50.0
        assert intent.objectives == ["slimming"]
        assert intent.palette == ["dark", "monochrome"]
        assert intent.formality == "casual"
        assert intent.timeframe == "this_weekend"
        assert intent.size == Size.L

    def test_intent_validation(self):
        """Test intent validation."""
        # Test empty intent
        with pytest.raises(ValueError):
            Intent(intent="")

        # Test negative budget
        with pytest.raises(
            ValueError, match="budget_max must be positive when specified"
        ):
            Intent(intent="test", budget_max=-10.0)

        # Test invalid objectives
        with pytest.raises(ValueError):
            Intent(intent="test", objectives="invalid")

        # Test too many objectives
        with pytest.raises(
            ValueError, match="objectives cannot have more than 10 items"
        ):
            Intent(intent="test", objectives=["obj"] * 15)


class TestVisionAttributes:
    """Test VisionAttributes entity."""

    def test_vision_attributes_creation(self):
        """Test creating valid vision attributes."""
        attrs = VisionAttributes(
            color="blue",
            category=Category.TOP,
            material=Material.COTTON,
            pattern=Pattern.PLAIN,
            style="casual",
            season=Season.SUMMER,
            occasion=Occasion.CASUAL,
            fit=Fit.REGULAR,
            plus_size=False,
            description="A casual blue cotton top",
        )

        assert attrs.color == "blue"
        assert attrs.category == Category.TOP
        assert attrs.material == Material.COTTON
        assert attrs.pattern == Pattern.PLAIN
        assert attrs.style == "casual"
        assert attrs.season == Season.SUMMER
        assert attrs.occasion == Occasion.CASUAL
        assert attrs.fit == Fit.REGULAR
        assert attrs.plus_size is False
        assert attrs.description == "A casual blue cotton top"

    def test_vision_attributes_validation(self):
        """Test vision attributes validation."""
        # Test empty color
        with pytest.raises(ValueError):
            VisionAttributes(color="")

        # Test color normalization
        attrs = VisionAttributes(color="  BLUE  ")
        assert attrs.color == "blue"


class TestRecommendationRequest:
    """Test RecommendationRequest entity."""

    def test_recommendation_request_creation(self):
        """Test creating a valid recommendation request."""
        request = RecommendationRequest(
            text_query="I want to do yoga",
            budget=80.0,
            size=Size.L,
            week="2025-W40",
            preferences={"palette": ["dark"]},
        )

        assert request.text_query == "I want to do yoga"
        assert request.budget == 80.0
        assert request.size == Size.L
        assert request.week == "2025-W40"
        assert request.preferences == {"palette": ["dark"]}

    def test_recommendation_request_validation(self):
        """Test recommendation request validation."""
        # Test empty text_query
        with pytest.raises(ValueError):
            RecommendationRequest(text_query="")

        # Test invalid preferences
        with pytest.raises(ValueError):
            RecommendationRequest(text_query="test", preferences="invalid")


class TestRecommendationResponse:
    """Test RecommendationResponse entity."""

    def test_recommendation_response_creation(self):
        """Test creating a valid recommendation response."""
        response = RecommendationResponse(
            constraints_used={"intent": "yoga", "budget_max": 50.0},
            outfits=[
                Outfit(title="Test Outfit", items=[], score=0.8, rationale="test")
            ],
            request_id="test123",
        )

        assert response.constraints_used == {"intent": "yoga", "budget_max": 50.0}
        assert len(response.outfits) == 1
        assert response.request_id == "test123"

    def test_recommendation_response_validation(self):
        """Test recommendation response validation."""
        # Test invalid constraints_used
        with pytest.raises(ValueError):
            RecommendationResponse(constraints_used="invalid", outfits=[])

        # Test invalid outfits
        with pytest.raises(ValueError):
            RecommendationResponse(constraints_used={}, outfits="invalid")

        # Test too many outfits
        with pytest.raises(ValueError, match="cannot return more than 20 outfits"):
            outfits = [
                Outfit(title=f"Test Outfit {i}", items=[], score=0.8, rationale="test")
                for i in range(25)
            ]
            RecommendationResponse(constraints_used={}, outfits=outfits)


class TestIngestRequest:
    """Test IngestRequest entity."""

    def test_ingest_request_creation(self):
        """Test creating a valid ingest request."""
        request = IngestRequest(limit=100, since=datetime.now())

        assert request.limit == 100
        assert isinstance(request.since, datetime)

    def test_ingest_request_validation(self):
        """Test ingest request validation."""
        # Test invalid limit
        with pytest.raises(ValueError):
            IngestRequest(limit=0)

        with pytest.raises(ValueError):
            IngestRequest(limit=1001)


class TestIngestResponse:
    """Test IngestResponse entity."""

    def test_ingest_response_creation(self):
        """Test creating a valid ingest response."""
        response = IngestResponse(
            status="completed", items_processed=50, request_id="ingest_123"
        )

        assert response.status == "completed"
        assert response.items_processed == 50
        assert response.request_id == "ingest_123"

    def test_ingest_response_validation(self):
        """Test ingest response validation."""
        # Test empty status
        with pytest.raises(ValueError):
            IngestResponse(status="", items_processed=0)

        # Test negative items_processed
        with pytest.raises(ValueError):
            IngestResponse(status="completed", items_processed=-1)


class TestChatRequest:
    """Test ChatRequest entity."""

    def test_chat_request_creation(self):
        """Test creating a valid chat request."""
        request = ChatRequest(
            session_id="session_123", message="Hello, I need help finding an outfit"
        )

        assert request.session_id == "session_123"
        assert request.message == "Hello, I need help finding an outfit"

    def test_chat_request_validation(self):
        """Test chat request validation."""
        # Test empty message
        with pytest.raises(ValueError):
            ChatRequest(message="")

        # Test empty session_id
        with pytest.raises(ValueError, match="session_id cannot be empty string"):
            ChatRequest(session_id="", message="test")


class TestChatResponse:
    """Test ChatResponse entity."""

    def test_chat_response_creation(self):
        """Test creating a valid chat response."""
        response = ChatResponse(
            session_id="session_123",
            replies=[{"type": "text", "message": "Hello!"}],
            outfits=[
                {
                    "title": "Test Outfit",
                    "items": [],
                    "total_price": 100.0,
                    "style_explanation": "test explanation",
                    "outfit_type": "coordinated_set",
                }
            ],
            request_id="chat_123",
        )

        assert response.session_id == "session_123"
        assert len(response.replies) == 1
        assert len(response.outfits) == 1
        assert response.request_id == "chat_123"

    def test_chat_response_validation(self):
        """Test chat response validation."""
        # Test empty session_id
        with pytest.raises(ValueError):
            ChatResponse(session_id="", replies=[])

        # Test invalid replies
        with pytest.raises(ValueError):
            ChatResponse(session_id="test", replies="invalid")

        # Test too many replies
        with pytest.raises(ValueError, match="cannot return more than 10 replies"):
            replies = [{"type": "text", "message": "test"}] * 15
            ChatResponse(session_id="test", replies=replies)

        # Test invalid outfits
        with pytest.raises(ValueError):
            ChatResponse(session_id="test", replies=[], outfits="invalid")
