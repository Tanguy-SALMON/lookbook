"""
Domain Use Cases

This module defines the core use cases (application services) that orchestrate
domain operations and coordinate between adapters and services.
"""

from abc import ABC, abstractmethod
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
from .entities import (
    Item,
    Outfit,
    OutfitItem,
    Rule,
    Intent,
    RecommendationRequest,
    RecommendationResponse,
    IngestRequest,
    IngestResponse,
    ChatRequest,
    ChatResponse,
    VisionAttributes,
)
from ..services.smart_recommender import SmartRecommender


class UseCase(ABC):
    """Abstract base class for all use cases."""

    @abstractmethod
    def execute(self, *args, **kwargs) -> Any:
        """Execute the use case."""
        pass


class IngestItems(UseCase):
    """Use case for ingesting fashion items from the catalog."""

    def __init__(self, shop_adapter, vision_adapter, lookbook_repo):
        self.shop_adapter = shop_adapter
        self.vision_adapter = vision_adapter
        self.lookbook_repo = lookbook_repo

    async def execute(self, request: IngestRequest) -> IngestResponse:
        """
        Execute item ingestion process.

        Args:
            request: Ingestion request with limit and since parameters

        Returns:
            IngestResponse with processing results
        """
        try:
            # Fetch items from shop catalog
            shop_items = await self.shop_adapter.fetch_items(
                limit=request.limit, since=request.since
            )

            # Process items through vision analysis
            processed_items = []
            for item in shop_items:
                try:
                    # Analyze item image
                    vision_attrs = await self.vision_adapter.analyze_image(
                        item.image_key
                    )

                    # Create enhanced item with vision attributes
                    enhanced_item = Item(
                        sku=item.sku,
                        title=item.title,
                        price=item.price,
                        size_range=item.size_range,
                        image_key=item.image_key,
                        attributes={
                            **item.attributes,
                            "vision_attributes": vision_attrs.dict(),
                        },
                        in_stock=item.in_stock,
                    )

                    processed_items.append(enhanced_item)

                except Exception as e:
                    # Log error but continue processing other items
                    print(f"Error processing item {item.sku}: {e}")
                    processed_items.append(item)

            # Save processed items to lookbook repository
            saved_count = await self.lookbook_repo.save_items(processed_items)

            return IngestResponse(
                status="completed",
                items_processed=saved_count,
                request_id=f"ingest_{datetime.now().isoformat()}",
            )

        except Exception as e:
            return IngestResponse(
                status="failed",
                items_processed=0,
                request_id=f"ingest_{datetime.now().isoformat()}",
            )


class RecommendOutfits(UseCase):
    """Use case for generating outfit recommendations."""

    def __init__(self, intent_parser, recommender_service, lookbook_repo):
        self.intent_parser = intent_parser
        self.recommender_service = recommender_service
        self.lookbook_repo = lookbook_repo

    async def execute(self, request: RecommendationRequest) -> RecommendationResponse:
        """
        Execute outfit recommendation process.

        Args:
            request: Recommendation request with query and constraints

        Returns:
            RecommendationResponse with outfit suggestions
        """
        try:
            # Parse user intent
            intent = await self.intent_parser.parse_intent(request.text_query)

            # Apply additional constraints from request
            if request.budget:
                intent.budget_max = request.budget
            if request.size:
                intent.size = request.size
            if request.week:
                intent.timeframe = request.week
            if request.preferences:
                intent.objectives.extend(request.preferences.get("objectives", []))
                if request.preferences.get("palette"):
                    intent.palette = request.preferences.get("palette")

            # Get candidate items from repository
            candidate_items = await self.lookbook_repo.get_items_by_intent(intent)

            # Generate recommendations
            recommendations = await self.recommender_service.generate_recommendations(
                intent=intent, candidate_items=candidate_items, max_outfits=7
            )

            # Build constraints used for response
            constraints_used = {
                "intent": intent.intent,
                "activity": intent.activity,
                "occasion": intent.occasion,
                "budget_max": intent.budget_max,
                "objectives": intent.objectives,
                "palette": intent.palette,
                "formality": intent.formality,
                "timeframe": intent.timeframe,
                "size": intent.size,
            }

            return RecommendationResponse(
                constraints_used=constraints_used,
                outfits=recommendations,
                request_id=f"recommend_{datetime.now().isoformat()}",
            )

        except Exception as e:
            # Return empty response on error
            return RecommendationResponse(
                constraints_used={},
                outfits=[],
                request_id=f"recommend_{datetime.now().isoformat()}",
            )


class BuildLookbook(UseCase):
    """Use case for building a complete lookbook."""

    def __init__(self, recommender_service, lookbook_repo):
        self.recommender_service = recommender_service
        self.lookbook_repo = lookbook_repo

    async def execute(self, theme: str, constraints: Dict[str, Any]) -> List[Outfit]:
        """
        Execute lookbook building process.

        Args:
            theme: Lookbook theme (e.g., "summer", "business", "casual")
            constraints: Additional constraints for the lookbook

        Returns:
            List of Outfit entities
        """
        try:
            # Get all items from repository
            all_items = await self.lookbook_repo.get_all_items()

            # Generate multiple outfit combinations
            outfits = []
            for i in range(5):  # Generate 5 outfits per theme
                outfit = await self.recommender_service.generate_outfit_for_theme(
                    theme=theme, items=all_items, constraints=constraints
                )
                if outfit:
                    outfits.append(outfit)

            # Save lookbook to repository
            await self.lookbook_repo.save_lookbook(theme, outfits)

            return outfits

        except Exception as e:
            print(f"Error building lookbook: {e}")
            return []


class ChatTurn(UseCase):
    """Use case for handling chat interactions."""

    def __init__(self, intent_parser, recommender_service, lookbook_repo):
        self.intent_parser = intent_parser
        self.recommender_service = recommender_service
        self.lookbook_repo = lookbook_repo
        self.smart_recommender = SmartRecommender(lookbook_repo)

    async def execute(self, request: ChatRequest) -> ChatResponse:
        """
        Execute chat turn processing with pure LLM responses.

        Args:
            request: Chat request with session and message

        Returns:
            ChatResponse with natural LLM replies and optional recommendations
        """
        try:
            # Parse user intent from message using LLM
            intent = await self.intent_parser.parse_intent(request.message)

            # Use the natural response from LLM
            natural_response = intent.get(
                "natural_response", "I'm here to help you find the perfect outfit!"
            )

            # Determine if this is a recommendation request or just conversation
            is_recommendation_request = (
                intent.get("intent") == "recommend_outfits" and
                any(keyword in request.message.lower() for keyword in [
                    "want", "need", "looking for", "find", "show me", "recommend",
                    "outfit", "clothes", "wear", "style", "fashion", "dress"
                ])
            )

            # Try to generate real outfit recommendations using smart recommender
            try:
                outfit_recommendations = await self.smart_recommender.recommend_outfits(
                    request.message, limit=3
                )

                if outfit_recommendations and is_recommendation_request:
                    # Convert smart recommender output to frontend-compatible dictionaries
                    formatted_outfits = []
                    total_outfits = len(outfit_recommendations)

                    for outfit in outfit_recommendations:
                        # Create dictionary that matches frontend expectations
                        formatted_outfit = {
                            "title": outfit["title"],
                            "items": outfit[
                                "items"
                            ],  # Frontend expects items at top level
                            "total_price": outfit["total_price"],
                            "rationale": outfit["style_explanation"],
                            "score": 0.85,  # Default score as float
                            "outfit_type": outfit["outfit_type"],
                            "item_count": len(outfit["items"]),
                        }
                        formatted_outfits.append(formatted_outfit)

                    # Enhance the natural response with actual findings
                    enhanced_response = f"{natural_response}\n\nI found {total_outfits} great outfit{'s' if total_outfits != 1 else ''} for you! Here are the details with links and prices:"

                    replies = [
                        {
                            "type": "recommendations",
                            "message": enhanced_response,
                            "outfits": total_outfits,
                        }
                    ]

                    # Return raw dictionaries for frontend compatibility
                    outfits = formatted_outfits
                else:
                    # No outfits found or not a recommendation request, use natural response
                    replies = [
                        {
                            "type": "assistant",
                            "message": natural_response,
                        }
                    ]
                    outfits = []

            except Exception as e:
                print(f"Smart recommendation error: {e}")
                # Fallback to natural response only
                replies = [
                    {
                        "type": "assistant",
                        "message": natural_response,
                    }
                ]
                outfits = []

            return ChatResponse(
                session_id=request.session_id or str(uuid.uuid4()),
                replies=replies,
                outfits=outfits if outfits else None,
                request_id=str(uuid.uuid4()),
            )

        except Exception as e:
            print(f"ChatTurn error: {e}")
            # Even on error, provide a helpful response
            return ChatResponse(
                session_id=request.session_id or str(uuid.uuid4()),
                replies=[
                    {
                        "type": "assistant",
                        "message": "I'd love to help you find the perfect outfit! Could you tell me more about what you're looking for?",
                    }
                ],
                outfits=None,
                request_id=str(uuid.uuid4()),
            )

    # Removed hardcoded message builders - now using LLM natural responses


class SearchItems(UseCase):
    """Use case for searching items by various criteria."""

    def __init__(self, lookbook_repo):
        self.lookbook_repo = lookbook_repo

    async def execute(self, filters: Dict[str, Any]) -> List[Item]:
        """
        Execute item search.

        Args:
            filters: Search filters (category, color, size, etc.)

        Returns:
            List of matching Item entities
        """
        try:
            return await self.lookbook_repo.search_items(filters)
        except Exception as e:
            print(f"Error searching items: {e}")
            return []


class GetItemDetails(UseCase):
    """Use case for getting detailed item information."""

    def __init__(self, lookbook_repo):
        self.lookbook_repo = lookbook_repo

    async def execute(self, item_id: int) -> Optional[Item]:
        """
        Execute item details retrieval.

        Args:
            item_id: Item identifier

        Returns:
            Item entity or None if not found
        """
        try:
            return await self.lookbook_repo.get_item_by_id(item_id)
        except Exception as e:
            print(f"Error getting item details: {e}")
            return None
