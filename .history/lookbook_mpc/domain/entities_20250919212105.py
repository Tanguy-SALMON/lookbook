"""
Domain Entities

This module defines the core domain entities for the lookbook-MPC system.
These entities represent the business objects and their relationships.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
from pydantic import BaseModel, Field


class Size(str, Enum):
    """Size enumeration for clothing items."""
    XS = "XS"
    S = "S"
    M = "M"
    L = "L"
    XL = "XL"
    XXL = "XXL"
    XXXL = "XXXL"
    PLUS = "PLUS"


class Category(str, Enum):
    """Product category enumeration."""
    TOP = "top"
    BOTTOM = "bottom"
    DRESS = "dress"
    OUTERWEAR = "outerwear"
    SHOES = "shoes"
    ACCESSORY = "accessory"
    UNDERWEAR = "underwear"
    SWIMWEAR = "swimwear"


class Material(str, Enum):
    """Material enumeration."""
    COTTON = "cotton"
    POLYESTER = "polyester"
    NYLON = "nylon"
    WOOL = "wool"
    SILK = "silk"
    LINEN = "linen"
    DENIM = "denim"
    LEATHER = "leather"
    VELVET = "velvet"
    CHIFFON = "chiffon"
    FLEECE = "fleece"


class Pattern(str, Enum):
    """Pattern enumeration."""
    PLAIN = "plain"
    STRIPED = "striped"
    FLORAL = "floral"
    PRINT = "print"
    CHECKERED = "checked"
    PLAID = "plaid"
    POLKA_DOT = "polka_dot"
    ANIMAL_PRINT = "animal_print"
    GEOMETRIC = "geometric"


class Season(str, Enum):
    """Season enumeration."""
    SPRING = "spring"
    SUMMER = "summer"
    AUTUMN = "autumn"
    WINTER = "winter"


class Occasion(str, Enum):
    """Occasion enumeration."""
    CASUAL = "casual"
    BUSINESS = "business"
    FORMAL = "formal"
    PARTY = "party"
    WEDDING = "wedding"
    SPORT = "sport"
    BEACH = "beach"
    SLEEP = "sleep"


class Fit(str, Enum):
    """Fit enumeration."""
    SLIM = "slim"
    REGULAR = "regular"
    RELAXED = "relaxed"
    LOOSE = "loose"
    TIGHT = "tight"
    BAGGY = "baggy"


class Role(str, Enum):
    """Role enumeration for outfit items."""
    TOP = "top"
    BOTTOM = "bottom"
    SHOES = "shoes"
    OUTER = "outer"
    ACCESSORY = "accessory"
    DRESS = "dress"


class Item(BaseModel):
    """Domain entity representing a fashion item."""

    id: Optional[int] = None
    sku: str = Field(..., description="Stock Keeping Unit")
    title: str = Field(..., description="Product title")
    price: float = Field(..., ge=0, description="Product price")
    size_range: List[Size] = Field(default_factory=list, description="Available sizes")
    image_key: str = Field(..., description="S3 image key")
    attributes: Dict[str, Any] = Field(default_factory=dict, description="Product attributes")
    in_stock: bool = Field(default=True, description="Item availability")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        use_enum_values = True


class Outfit(BaseModel):
    """Domain entity representing a complete outfit."""

    id: Optional[int] = None
    title: str = Field(..., description="Outfit title")
    intent_tags: Dict[str, Any] = Field(default_factory=dict, description="Intent constraints")
    rationale: Optional[str] = Field(None, description="Rationale for outfit recommendation")
    score: Optional[float] = Field(None, ge=0, le=1, description="Recommendation score")
    created_at: Optional[datetime] = None

    class Config:
        use_enum_values = True


class OutfitItem(BaseModel):
    """Domain entity representing the relationship between outfits and items."""

    outfit_id: int = Field(..., description="Foreign key to outfit")
    item_id: int = Field(..., description="Foreign key to item")
    role: Role = Field(..., description="Role of item in outfit")

    class Config:
        use_enum_values = True


class Rule(BaseModel):
    """Domain entity representing recommendation rules."""

    id: Optional[int] = None
    name: str = Field(..., description="Rule name")
    intent: str = Field(..., description="Intent this rule applies to")
    constraints: Dict[str, Any] = Field(default_factory=dict, description="Rule constraints")
    priority: int = Field(default=1, ge=1, le=10, description="Rule priority")
    is_active: bool = Field(default=True, description="Whether rule is active")
    created_at: Optional[datetime] = None

    class Config:
        use_enum_values = True


class Intent(BaseModel):
    """Domain entity representing user intent."""

    intent: str = Field(..., description="Primary intent")
    activity: Optional[str] = Field(None, description="Activity type")
    occasion: Optional[Occasion] = Field(None, description="Occasion")
    budget_max: Optional[float] = Field(None, ge=0, description="Maximum budget")
    objectives: List[str] = Field(default_factory=list, description="Objectives like 'slimming'")
    palette: Optional[List[str]] = Field(None, description="Color palette preferences")
    formality: Optional[str] = Field(None, description="Formality level")
    timeframe: Optional[str] = Field(None, description="Timeframe (e.g., 'this_weekend')")
    size: Optional[Size] = Field(None, description="Size preference")
    created_at: Optional[datetime] = None

    class Config:
        use_enum_values = True


class VisionAttributes(BaseModel):
    """Vision analysis attributes for items."""

    color: str = Field(..., description="Primary color")
    category: Optional[Category] = Field(None, description="Product category")
    material: Optional[Material] = Field(None, description="Material")
    pattern: Optional[Pattern] = Field(None, description="Pattern")
    style: Optional[str] = Field(None, description="Style")
    season: Optional[Season] = Field(None, description="Season")
    occasion: Optional[Occasion] = Field(None, description="Occasion")
    fit: Optional[Fit] = Field(None, description="Fit")
    plus_size: bool = Field(default=False, description="Plus size indicator")
    description: Optional[str] = Field(None, description="Product description")


class RecommendationRequest(BaseModel):
    """Request model for outfit recommendations."""

    text_query: str = Field(..., description="Natural language query")
    budget: Optional[float] = Field(None, ge=0, description="Budget constraint")
    size: Optional[Size] = Field(None, description="Size preference")
    week: Optional[str] = Field(None, description="Week identifier")
    preferences: Optional[Dict[str, Any]] = Field(None, description="Additional preferences")


class RecommendationResponse(BaseModel):
    """Response model for outfit recommendations."""

    constraints_used: Dict[str, Any] = Field(..., description="Constraints applied")
    outfits: List[Dict[str, Any]] = Field(..., description="Recommended outfits")
    request_id: Optional[str] = Field(None, description="Request identifier")


class IngestRequest(BaseModel):
    """Request model for item ingestion."""

    limit: Optional[int] = Field(None, ge=1, le=1000, description="Maximum items to ingest")
    since: Optional[datetime] = Field(None, description="Ingest items updated since this time")


class IngestResponse(BaseModel):
    """Response model for item ingestion."""

    status: str = Field(..., description="Ingestion status")
    items_processed: int = Field(..., ge=0, description="Number of items processed")
    request_id: Optional[str] = Field(None, description="Request identifier")


class ChatRequest(BaseModel):
    """Request model for chat functionality."""

    session_id: Optional[str] = Field(None, description="Chat session identifier")
    message: str = Field(..., description="User message")


class ChatResponse(BaseModel):
    """Response model for chat functionality."""

    session_id: str = Field(..., description="Chat session identifier")
    replies: List[Dict[str, Any]] = Field(..., description="Chat responses")
    outfits: Optional[List[Dict[str, Any]]] = Field(None, description="Recommended outfits")
    request_id: Optional[str] = Field(None, description="Request identifier")