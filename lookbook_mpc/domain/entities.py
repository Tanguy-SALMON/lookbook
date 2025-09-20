"""
Domain Entities

This module defines the core domain entities for the lookbook-MPC system.
These entities represent the business objects and their relationships.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from pydantic import BaseModel, Field, validator, root_validator, model_validator


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
    ONE_SIZE = "ONE_SIZE"
    PETITE = "PETITE"
    TALL = "TALL"
    CUSTOM = "CUSTOM"


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
    HAT = "hat"
    BAG = "bag"
    JEWELRY = "jewelry"
    BELT = "belt"
    SCARF = "scarf"
    SOCKS = "socks"
    GLOVES = "gloves"
    WATCH = "watch"
    GLASSES = "glasses"
    FRAGRANCE = "fragrance"
    LOUNGEWEAR = "loungewear"
    SLEEPWEAR = "sleepwear"
    ACTIVEWEAR = "activewear"


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
    RAYON = "rayon"
    ACRYLIC = "acrylic"
    SPANDEX = "spandex"
    ELASTANE = "elastane"
    CASHMERE = "cashmere"
    ALPACA = "alpaca"
    BAMBOO = "bamboo"
    TENCEL = "tencel"
    MODAL = "modal"
    POLYAMIDE = "polyamide"
    POLYURETHANE = "polyurethane"


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
    SOLID = "solid"
    MARBLE = "marble"
    CAMOUFLAGE = "camouflage"
    FAUX = "faux"
    KNIT = "knit"
    RIBBED = "ribbed"
    WOVEN = "woven"
    EMBOSSED = "embossed"
    QUILTED = "quilted"
    SEQUINED = "sequined"
    BEADED = "beaded"


class Season(str, Enum):
    """Season enumeration."""
    SPRING = "spring"
    SUMMER = "summer"
    AUTUMN = "autumn"
    WINTER = "winter"
    ALL_SEASON = "all_season"
    TRANSITIONAL = "transitional"
    RESORT = "resort"
    PRE_FALL = "pre_fall"
    PRE_SPRING = "pre_spring"


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
    DATE = "date"
    INTERVIEW = "interview"
    TRAVEL = "travel"
    GYM = "gym"
    YOGA = "yoga"
    RUNNING = "running"
    HIKING = "hiking"
    FESTIVAL = "festival"
    CONCERT = "concert"
    THEATER = "theater"
    GALA = "gala"
    COCKTAIL = "cocktail"
    BRUNCH = "brunch"
    BBQ = "bbq"
    PICNIC = "picnic"


class Fit(str, Enum):
    """Fit enumeration."""
    SLIM = "slim"
    REGULAR = "regular"
    RELAXED = "relaxed"
    LOOSE = "loose"
    TIGHT = "tight"
    BAGGY = "baggy"
    ATHLETIC = "athletic"
    SKINNY = "skinny"
    BOOTCUT = "bootcut"
    FLARE = "flare"
    STRAIGHT = "straight"
    CROPPED = "cropped"
    OVERSIZED = "oversized"
    RELAXED_FIT = "relaxed_fit"
    TAPERED = "tapered"
    SLIM_FIT = "slim_fit"
    REGULAR_FIT = "regular_fit"
    LOOSE_FIT = "loose_fit"


class Role(str, Enum):
    """Role enumeration for outfit items."""
    TOP = "top"
    BOTTOM = "bottom"
    SHOES = "shoes"
    OUTER = "outer"
    ACCESSORY = "accessory"
    DRESS = "dress"
    UNDERGARMENT = "undergarment"
    SOCKS = "socks"
    HAT = "hat"
    BAG = "bag"
    JEWELRY = "jewelry"
    BELT = "belt"
    SCARF = "scarf"
    GLOVES = "gloves"
    WATCH = "watch"
    GLASSES = "glasses"
    FRAGRANCE = "fragrance"
    LOUNGEWEAR = "loungewear"
    SLEEPWEAR = "sleepwear"


class Item(BaseModel):
    """Domain entity representing a fashion item."""

    id: Optional[int] = None
    sku: str = Field(..., min_length=1, max_length=100, description="Stock Keeping Unit")
    title: str = Field(..., min_length=1, max_length=500, description="Product title")
    price: float = Field(..., ge=0, description="Product price")
    size_range: List[Size] = Field(default_factory=list, description="Available sizes")
    image_key: str = Field(..., min_length=1, max_length=255, description="S3 image key")
    attributes: Dict[str, Any] = Field(default_factory=dict, description="Product attributes")
    in_stock: bool = Field(default=True, description="Item availability")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @validator('size_range')
    def validate_size_range(cls, v):
        if not isinstance(v, list):
            raise ValueError('size_range must be a list')
        if len(v) > 20:  # Reasonable limit
            raise ValueError('size_range cannot have more than 20 sizes')
        return v

    @validator('attributes')
    def validate_attributes(cls, v):
        if not isinstance(v, dict):
            raise ValueError('attributes must be a dictionary')
        return v

    @model_validator(mode='before')
    @classmethod
    def validate_item(cls, values):
        if values.get('price') is not None and values.get('price') < 0:
            raise ValueError('price cannot be negative')
        return values

    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class Outfit(BaseModel):
    """Domain entity representing an outfit."""

    id: Optional[int] = None
    title: str = Field(..., min_length=1, max_length=255, description="Outfit title")
    intent_tags: Dict[str, Any] = Field(default_factory=dict, description="Intent tags")
    rationale: Optional[str] = Field(None, description="Rationale for outfit")
    score: Optional[float] = Field(None, description="Outfit score")
    created_at: Optional[datetime] = None

    @validator('title')
    def validate_title(cls, v):
        if not v or not v.strip():
            raise ValueError('title cannot be empty')
        return v.strip()

    @validator('intent_tags')
    def validate_intent_tags(cls, v):
        if not isinstance(v, dict):
            raise ValueError('intent_tags must be a dictionary')
        return v

    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class OutfitItem(BaseModel):
    """Domain entity representing the relationship between outfits and items."""

    outfit_id: int = Field(..., ge=1, description="Foreign key to outfit")
    item_id: int = Field(..., ge=1, description="Foreign key to item")
    role: Role = Field(..., description="Role of item in outfit")

    @validator('outfit_id')
    def validate_outfit_id(cls, v):
        if v < 1:
            raise ValueError('outfit_id must be positive')
        return v

    @validator('item_id')
    def validate_item_id(cls, v):
        if v < 1:
            raise ValueError('item_id must be positive')
        return v

    @model_validator(mode='before')
    @classmethod
    def validate_relationship(cls, values):
        outfit_id = values.get('outfit_id')
        item_id = values.get('item_id')
        if outfit_id and item_id:
            # Basic validation - in real app might check if relationship exists
            if outfit_id == item_id:
                raise ValueError('outfit_id and item_id cannot be the same')
        return values

    class Config:
        use_enum_values = True


class Rule(BaseModel):
    """Domain entity representing recommendation rules."""

    id: Optional[int] = None
    name: str = Field(..., min_length=1, max_length=100, description="Rule name")
    intent: str = Field(..., min_length=1, max_length=100, description="Intent this rule applies to")
    constraints: Dict[str, Any] = Field(default_factory=dict, description="Rule constraints")
    priority: int = Field(default=1, ge=1, le=10, description="Rule priority")
    is_active: bool = Field(default=True, description="Whether rule is active")
    created_at: Optional[datetime] = None

    @validator('name')
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('name cannot be empty')
        return v.strip()

    @validator('intent')
    def validate_intent(cls, v):
        if not v or not v.strip():
            raise ValueError('intent cannot be empty')
        return v.strip()

    @validator('constraints')
    def validate_constraints(cls, v):
        if not isinstance(v, dict):
            raise ValueError('constraints must be a dictionary')
        return v

    @model_validator(mode='before')
    @classmethod
    def validate_rule(cls, values):
        name = values.get('name')
        intent = values.get('intent')
        if name and intent and name == intent:
            raise ValueError('name and intent cannot be the same')
        return values

    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class Intent(BaseModel):
    """Domain entity representing user intent."""

    budget_max: Optional[float] = Field(None, ge=0, description="Maximum budget")
    size: Optional[Size] = Field(None, description="Preferred size")
    category: Optional[Category] = Field(None, description="Preferred category")
    color: Optional[str] = Field(None, description="Preferred color")
    material: Optional[Material] = Field(None, description="Preferred material")
    pattern: Optional[Pattern] = Field(None, description="Preferred pattern")
    season: Optional[Season] = Field(None, description="Preferred season")
    occasion: Optional[Occasion] = Field(None, description="Preferred occasion")
    fit: Optional[Fit] = Field(None, description="Preferred fit")

    class Config:
        use_enum_values = True


class VisionAttributes(BaseModel):
    """Domain entity representing vision analysis attributes."""

    color: Optional[str] = Field(None, description="Detected color")
    category: Optional[Category] = Field(None, description="Detected category")
    material: Optional[Material] = Field(None, description="Detected material")
    pattern: Optional[Pattern] = Field(None, description="Detected pattern")
    fit: Optional[Fit] = Field(None, description="Detected fit")
    occasion: Optional[Occasion] = Field(None, description="Detected occasion")
    season: Optional[Season] = Field(None, description="Detected season")

    class Config:
        use_enum_values = True


# Request/Response models
class RecommendationRequest(BaseModel):
    """Request model for outfit recommendations."""

    text_query: str = Field(..., description="User's text query")
    budget: Optional[float] = Field(None, ge=0, description="Maximum budget")
    size: Optional[Size] = Field(None, description="Preferred size")
    week: Optional[str] = Field(None, description="Timeframe/week")
    preferences: Optional[Dict[str, Any]] = Field(None, description="Additional preferences")

    class Config:
        use_enum_values = True


class RecommendationResponse(BaseModel):
    """Response model for outfit recommendations."""

    constraints_used: Dict[str, Any] = Field(default_factory=dict, description="Constraints used for recommendations")
    outfits: List[Outfit] = Field(default_factory=list, description="Recommended outfits")
    request_id: str = Field(..., description="Request identifier")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class IngestRequest(BaseModel):
    """Request model for item ingestion."""

    limit: Optional[int] = Field(None, ge=1, le=1000, description="Maximum number of items to ingest")
    since: Optional[datetime] = Field(None, description="Ingest items updated since this timestamp")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class IngestResponse(BaseModel):
    """Response model for item ingestion."""

    status: str = Field(..., description="Processing status")
    items_processed: int = Field(..., ge=0, description="Number of items processed")
    request_id: str = Field(..., description="Request identifier")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class ChatRequest(BaseModel):
    """Request model for chat interactions."""

    session_id: Optional[str] = Field(None, description="Session identifier")
    message: str = Field(..., description="User message")
    context: Optional[Dict[str, Any]] = Field(None, description="Chat context")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class ChatResponse(BaseModel):
    """Response model for chat interactions."""

    session_id: str = Field(..., description="Session identifier")
    replies: List[Dict[str, Any]] = Field(default_factory=list, description="Response messages")
    outfits: Optional[List[Outfit]] = Field(None, description="Recommended outfits")
    request_id: str = Field(..., description="Request identifier")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }