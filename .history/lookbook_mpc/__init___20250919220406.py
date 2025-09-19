"""
Lookbook-MPC - Fashion Lookbook Recommendation Microservice

A FastAPI-based service for fashion recommendations using vision analysis
and intent parsing with Ollama LLMs.
"""

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"
__description__ = "Fashion lookbook recommendation microservice with vision analysis and intent parsing"

# Core imports for easy access
from .domain.entities import (
    Item,
    Outfit,
    OutfitItem,
    Rule,
    Intent,
    Size,
    IngestRequest,
    IngestResponse,
    RecommendationRequest,
    RecommendationResponse,
    ChatRequest,
    ChatResponse
)

from .domain.use_cases import (
    IngestItems,
    RecommendOutfits,
    ChatTurn
)

from .adapters.images import (
    S3ImageLocator,
    MockImageLocator
)

from .services.rules import RulesEngine
from .services.recommender import OutfitRecommender

__all__ = [
    # Version and metadata
    "__version__",
    "__author__",
    "__email__",
    "__description__",

    # Domain entities
    "Item",
    "Outfit",
    "OutfitItem",
    "Rule",
    "Intent",
    "Size",
    "IngestRequest",
    "IngestResponse",
    "RecommendationRequest",
    "RecommendationResponse",
    "ChatRequest",
    "ChatResponse",

    # Use cases
    "IngestItems",
    "RecommendOutfits",
    "ChatTurn",

    # Adapters
    "S3ImageLocator",
    "MockImageLocator",

    # Services
    "RulesEngine",
    "OutfitRecommender"
]