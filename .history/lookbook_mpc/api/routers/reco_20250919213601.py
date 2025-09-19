
"""
Recommendation API Router

This module handles endpoints for generating outfit recommendations
based on user intent and preferences.
"""

from fastapi import APIRouter, HTTPException, status, Query
from typing import Dict, Any, Optional, List
import logging
import structlog

from ...domain.entities import (
    RecommendationRequest,
    RecommendationResponse,
    Size
)
from ...domain.use_cases import RecommendOutfits
from ...adapters.intent import MockIntentParser
from ...adapters.db_lookbook import MockLookbookRepository
from ...services.rules import RulesEngine
from ...services.recommender import OutfitRecommender

router = APIRouter(prefix="/v1/recommendations", tags=["recommendations"])
logger = structlog.get_logger()


# Initialize dependencies (will be replaced with proper DI in later milestones)
intent_parser = MockIntentParser()
lookbook_repo = MockLookbookRepository()
rules_engine = RulesEngine()
recommender = OutfitRecommender(rules_engine)
recommend_use_case = RecommendOutfits(intent_parser, recommender, lookbook_repo)


@router.post("", response_model=RecommendationResponse)
async def get_recommendations(request: RecommendationRequest) -> RecommendationResponse:
    """
    Generate outfit recommendations based on user query.

    This endpoint analyzes the user's natural language request and
    generates 3-7 outfit recommendations that match the specified criteria.

    Args:
        request: Recommendation request with text query and constraints

    Returns:
        RecommendationResponse with outfits and constraints used

    Raises:
        HTTPException: If recommendation generation fails
    """
    try:
        logger.info("Generating outfit recommendations", request=request.dict())

        # Execute recommendation use case
        response = await recommend_use_case.execute(request)

        # Log completion
        logger.info("Recommendations generated",
                   outfits_count=len(response.outfits),
                   constraints_used=response.constraints_used)

        return response

    except Exception as e:
        logger.error("Recommendation generation failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Recommendation generation failed: {str(e)}"
        )


@router.get("/preview")
async def preview_recommendations(
    text_query: str = Query(..., description="Natural language query"),
    budget: Optional[float] = Query(None, ge=0, description="Maximum budget"),
    size: Optional[Size] = Query(None, description="Size preference"),
    week: Optional[str] = Query(None, description="Week identifier"),
    preferences: Optional[str] = Query(None, description="JSON preferences string")
) -> Dict[str, Any]:
    """
    Preview recommendations with query parameters (alternative to POST).

    Args:
        text_query: Natural language query
        budget: Maximum budget
        size: Size preference
        week: Week identifier
        preferences: JSON string with additional preferences

    Returns:
        Preview of recommendations
    """
    try:
        logger.info("Previewing recommendations", text_query=text_query)

        # Parse preferences if provided
        parsed_preferences = None
        if preferences:
            import json
            try:
                parsed_preferences = json.loads(preferences)
            except json.JSONDecodeError:
                logger.warning("Invalid preferences JSON", preferences=preferences)

        # Create request
        request = RecommendationRequest(
            text_query=text_query,
            budget=budget,
            size=size,
            week=week,
            preferences=parsed_preferences
        )

        # Execute recommendation use case
        response = await recommend_use_case.execute(request)

        return {
            "preview": True,
            "constraints_used": response.constraints_used,
            "outfits": response.outfits[:3],  # Limit preview to 3 outfits
            "total_available": len(response.outfits)
        }

    except Exception as e:
        logger.error("Preview generation failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Preview generation failed: {str(e)}"
        )


@router.get("/constraints")
async def get_available_constraints() -> Dict[str, Any]:
    """
    Get available constraint options for recommendations.

    Returns:
        Dictionary with available constraint options
    """
    try:
        logger.info("Getting available constraints")

        constraints_response = {
            "sizes": ["XS", "S", "M", "L", "XL", "XXL", "XXXL", "PLUS"],
            "categories": ["top", "bottom", "dress", "outerwear", "shoes", "accessory"],
            "occasions": ["casual", "business", "formal", "party", "wedding", "sport", "beach"],
            "materials": ["cotton", "polyester", "nylon", "wool", "silk", "linen", "denim", "leather"],
            "colors": ["black", "white", "navy", "grey", "beige", "red", "blue", "green", "yellow", "pink"],
            "patterns": ["plain", "striped", "floral", "print", "checked", "plaid", "polka_dot"],
            "budget_ranges": {
                "budget": {"min": 0, "max": 1000, "step": 10},
                "price_points": ["under_30", "30_50", "50_100", "100_200", "over_200"]
            },
            "objectives": ["comfort", "style", "slimming", "confidence", "performance", "flexibility"],
            "palettes": ["neutral", "pastel", "bright", "dark", "monochrome", "earth_tones", "bold"]
        }

        return constraints_response

    except Exception as e:
        logger.error("Error getting constraints", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get constraints: {str(e)}"
        )


@router.get("/popular")
async def get_popular_recommendations(
    limit: int = Query(5, ge=1, le=10, description="Number of recommendations to return")
) -> Dict[str, Any]:
    """
    Get popular outfit recommendations.

    Args:
        limit: Maximum number of recommendations to return

    Returns:
        Popular outfit recommendations
    """
    try:
        logger.info("Getting popular recommendations", limit=limit)

        # Mock popular recommendations (in real implementation, this would query database)
        popular_response = {
            "popular": True,
            "recommendations": [
                {
                    "items": [
                        {
                            "item_id": 1,
                            "sku": "1295990003",
                            "role": "top",
                            "image_url": "https://example.com/images/e341e2f3a4b5c6d7e8f9.jpg",
                            "title": "Classic Cotton T-Shirt",
                            "price": 29.99,
                            "score": 0.85
                        },
                        {
                            "item_id": 2,
                            "sku": "1295990011",
                            "role": "bottom",
                            "image_url": "https://example.com/images/f567g8h9i0j1k2l3m4n5.jpg",
                            "title": "Slim Fit Jeans",
                            "price": 79.99,
                            "score": 0.82
                        }
                    ],
                    "score": 0.83,
                    "rationale": "Classic casual combination perfect for everyday wear",
                    "popularity_score": 95,
                    "constraints_used": {
                        "occasion": "casual",
                        "formality": "casual"
                    }
                }
            ],
            "limit": limit
        }

        return popular_response

    except Exception as e:
        logger.error("Error getting popular recommendations", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get popular recommendations: {str(e)}"
        )


@router.get("/trending")
async def get_trending_recommendations(
    category: Optional[str] = Query(None, description="Filter by category"),
    limit: int = Query(5, ge=1, le=10, description="Number of recommendations to return")
) -> Dict[str, Any]:
    """
    Get trending outfit recommendations.

    Args:
        category: Filter by category (optional)
        limit: Maximum number of recommendations to return

    Returns:
        Trending outfit recommendations
    """
    try:
        logger.info("Getting trending recommendations", category=category, limit=limit)

        # Mock trending recommendations
        trending_response = {
            "trending": True,
            "category": category,
            "recommendations": [
                {
                    "items": [
                        {
                            "item_id": 3,
                            "sku": "1295990022",
                            "role": "top",
                            "image_url": "https://example.com/images/g890h1i2j3k4l5m6n7o8.jpg",
                            "title": "Oversized Blouse",
                            "price": 59.99,
                            "score": 0.78
                        },
                        {
                            "item_id": 4,
                            "sku": "1295990033",
                            "role": "bottom",
                            "image_url": "https://example.com/images/p990q0r1s2t3u4v5w6x7.jpg",
                            "title": "Wide Leg Trousers",
                            "price": 89.99,
                            "score": 0.75
                        }
                    ],
                    "score": 0.76,
                    "rationale": "Modern oversized trend perfect for contemporary style",
                    "trend_score": 88,
                    "trend_reason": "Increased search volume by 150% this month",
                    "constraints_used": {
                        "style": "modern",
                        "formality": "casual"
                    }
                }
            ],
            "limit": limit
        }

        return trending_response

    except Exception as e:
