"""
Domain Entities

This module defines the core domain entities for the lookbook-MPC system.
These entities represent the business objects and their relationships.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, JSON, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Session
from sqlalchemy.dialects.mysql import VARCHAR, TEXT
from pydantic import BaseModel, Field, validator, root_validator, model_validator
from sqlalchemy.sql import func

Base = declarative_base()


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


class ItemDB(Base):
    """SQLAlchemy model for Item entity."""

    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String(100), unique=True, nullable=False, index=True)
    title = Column(String(500), nullable=False)
    price = Column(Float, nullable=False)
    size_range = Column(JSON, default=[])
    image_key = Column(String(255), nullable=False)
    attributes = Column(JSON, default={})
    in_stock = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Indexes for performance
    __table_args__ = (
        Index('idx_items_price', 'price'),
        Index('idx_items_in_stock', 'in_stock'),
        Index('idx_items_created_at', 'created_at'),
        Index('idx_items_attributes_category', 'attributes', postgresql_using='gin'),
        Index('idx_items_attributes_color', 'attributes', postgresql_using='gin'),
    )

    # Relationships
    outfit_items = relationship("OutfitItemDB", back_populates="item")

    def to_domain(self) -> Item:
        """Convert SQLAlchemy model to domain entity."""
        return Item(
            id=self.id,
            sku=self.sku,
            title=self.title,
            price=self.price,
            size_range=self.size_range,
            image_key=self.image_key,
            attributes=self.attributes,
            in_stock=self.in_stock,
            created_at=self.created_at,
            updated_at=self.updated_at
        )

    @classmethod
    def from_domain(cls, item: Item) -> 'ItemDB':
        """Create SQLAlchemy model from domain entity."""
        return cls(
            sku=item.sku,
            title=item.title,
            price=item.price,
            size_range=item.size_range,
            image_key=item.image_key,
            attributes=item.attributes,
            in_stock=item.in_stock,
            created_at=item.created_at,
            updated_at=item.updated_at
        )


class Outfit(BaseModel):
    """Domain entity representing a complete outfit."""

    id: Optional[int] = None
    title: str = Field(..., min_length=1, max_length=255, description="Outfit title")
    intent_tags: Dict[str, Any] = Field(default_factory=dict, description="Intent constraints")
    rationale: Optional[str] = Field(None, max_length=2000, description="Rationale for outfit recommendation")
    score: Optional[float] = Field(None, ge=0, le=1, description="Recommendation score")
    created_at: Optional[datetime] = None

    @validator('intent_tags')
    def validate_intent_tags(cls, v):
        if not isinstance(v, dict):
            raise ValueError('intent_tags must be a dictionary')
        return v

    @validator('title')
    def validate_title(cls, v):
        if not v or not v.strip():
            raise ValueError('title cannot be empty')
        return v.strip()

    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class OutfitDB(Base):
    """SQLAlchemy model for Outfit entity."""

    __tablename__ = "outfits"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    intent_tags = Column(JSON, default={})
    rationale = Column(Text)
    score = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Indexes for performance
    __table_args__ = (
        Index('idx_outfits_score', 'score'),
        Index('idx_outfits_created_at', 'created_at'),
        Index('idx_outfits_intent_tags', 'intent_tags', postgresql_using='gin'),
    )

    # Relationships
    outfit_items = relationship("OutfitItemDB", back_populates="outfit")

    def to_domain(self) -> Outfit:
        """Convert SQLAlchemy model to domain entity."""
        return Outfit(
            id=self.id,
            title=self.title,
            intent_tags=self.intent_tags,
            rationale=self.rationale,
            score=self.score,
            created_at=self.created_at
        )

    @classmethod
    def from_domain(cls, outfit: Outfit) -> 'OutfitDB':
        """Create SQLAlchemy model from domain entity."""
        return cls(
            title=outfit.title,
            intent_tags=outfit.intent_tags,
            rationale=outfit.rationale,
            score=outfit.score,
            created_at=outfit.created_at
        )


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


class OutfitItemDB(Base):
    """SQLAlchemy model for OutfitItem entity."""

    __tablename__ = "outfit_items"

    outfit_id = Column(Integer, ForeignKey("outfits.id"), primary_key=True)
    item_id = Column(Integer, ForeignKey("items.id"), primary_key=True)
    role = Column(String(50), nullable=False)

    # Indexes for performance
    __table_args__ = (
        Index('idx_outfit_items_outfit_id', 'outfit_id'),
        Index('idx_outfit_items_item_id', 'item_id'),
        Index('idx_outfit_items_role', 'role'),
    )

    # Relationships
    outfit = relationship("OutfitDB", back_populates="outfit_items")
    item = relationship("ItemDB", back_populates="outfit_items")

    def to_domain(self) -> OutfitItem:
        """Convert SQLAlchemy model to domain entity."""
        return OutfitItem(
            outfit_id=self.outfit_id,
            item_id=self.item_id,
            role=self.role
        )

    @classmethod
    def from_domain(cls, outfit_item: OutfitItem) -> 'OutfitItemDB':
        """Create SQLAlchemy model from domain entity."""
        return cls(
            outfit_id=outfit_item.outfit_id,
            item_id=outfit_item.item_id,
            role=outfit_item.role
        )


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


class RuleDB(Base):
    """SQLAlchemy model for Rule entity."""

    __tablename__ = "rules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    intent = Column(String(100), nullable=False)
    constraints = Column(JSON, default={})
    priority = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Indexes for performance
    __table_args__ = (
        Index('idx_rules_priority', 'priority'),
        Index('idx_rules_intent', 'intent'),
        Index('idx_rules_is_active', 'is_active'),
        Index('idx_rules_name', 'name'),
        Index('idx_rules_constraints', 'constraints', postgresql_using='gin'),
    )

    def to_domain(self) -> Rule:
        """Convert SQLAlchemy model to domain entity."""
        return Rule(
            id=self.id,
            name=self.name,
            intent=self.intent,
            constraints=self.constraints,
            priority=self.priority,
            is_active=self.is_active,
            created_at=self.created_at
        )

    @classmethod
    def from_domain(cls, rule: Rule) -> 'RuleDB':
        """Create SQLAlchemy model from domain entity."""
        return cls(
            name=rule.name,
            intent=rule.intent,
            constraints=rule.constraints,
            priority=rule.priority,
            is_active=rule.is_active,
            created_at=rule.created_at
        )


class Intent(BaseModel):
    """Domain entity representing user intent."""

    intent: str = Field(..., min_length=1, max_length=100, description="Primary intent")
    activity: Optional[str] = Field(None, max_length=100, description="Activity type")
    occasion: Optional[Occasion] = Field(None, description="Occasion")
    budget_max: Optional[float] = Field(None, ge=0, description="Maximum budget")
    objectives: List[str] = Field(default_factory=list, description="Objectives like 'slimming'")
    palette: Optional[List[str]] = Field(None, description="Color palette preferences")
    formality: Optional[str] = Field(None, max_length=50, description="Formality level")
    timeframe: Optional[str] = Field(None, max_length=50, description="Timeframe (e.g., 'this_weekend')")
    size: Optional[Size] = Field(None, description="Size preference")
    created_at: Optional[datetime] = None

    @validator('intent')
    def validate_intent(cls, v):
        if not v or not v.strip():
            raise ValueError('intent cannot be empty')
        return v.strip()

    @validator('activity')
    def validate_activity(cls, v):
        if v is not None:
            if not v.strip():
                raise ValueError('activity cannot be empty string')
            v = v.strip()
        return v

    @validator('objectives')
    def validate_objectives(cls, v):
        if not isinstance(v, list):
            raise ValueError('objectives must be a list')
        if len(v) > 10:  # Reasonable limit
            raise ValueError('objectives cannot have more than 10 items')
        return v

    @validator('palette')
    def validate_palette(cls, v):
        if v is not None:
            if not isinstance(v, list):
                raise ValueError('palette must be a list')
            if len(v) > 5:  # Reasonable limit for color palettes
                raise ValueError('palette cannot have more than 5 colors')
        return v

    @model_validator(mode='before')
    @classmethod
    def validate_intent(cls, values):
        intent = values.get('intent')
        budget_max = values.get('budget_max')

        if intent and budget_max is not None and budget_max <= 0:
            raise ValueError('budget_max must be positive when specified')

        return values

    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class VisionAttributes(BaseModel):
    """Vision analysis attributes for items."""

    color: str = Field(..., min_length=1, max_length=50, description="Primary color")
    category: Optional[Category] = Field(None, description="Product category")
    material: Optional[Material] = Field(None, description="Material")
    pattern: Optional[Pattern] = Field(None, description="Pattern")
    style: Optional[str] = Field(None, max_length=100, description="Style")
    season: Optional[Season] = Field(None, description="Season")
    occasion: Optional[Occasion] = Field(None, description="Occasion")
    fit: Optional[Fit] = Field(None, description="Fit")
    plus_size: bool = Field(default=False, description="Plus size indicator")
    description: Optional[str] = Field(None, max_length=1000, description="Product description")

    @validator('color')
    def validate_color(cls, v):
        if not v or not v.strip():
            raise ValueError('color cannot be empty')
        return v.strip().lower()

    @validator('style')
    def validate_style(cls, v):
        if v is not None:
            if not v.strip():
                raise ValueError('style cannot be empty string')
            v = v.strip()
        return v

    @validator('description')
    def validate_description(cls, v):
        if v is not None:
            v = v.strip()
        return v

    class Config:
        use_enum_values = True


class RecommendationRequest(BaseModel):
    """Request model for outfit recommendations."""

    text_query: str = Field(..., min_length=1, max_length=1000, description="Natural language query")
    budget: Optional[float] = Field(None, ge=0, description="Budget constraint")
    size: Optional[Size] = Field(None, description="Size preference")
    week: Optional[str] = Field(None, max_length=10, description="Week identifier")
    preferences: Optional[Dict[str, Any]] = Field(None, description="Additional preferences")

    @validator('text_query')
    def validate_text_query(cls, v):
        if not v or not v.strip():
            raise ValueError('text_query cannot be empty')
        return v.strip()

    @validator('week')
    def validate_week(cls, v):
        if v is not None:
            if not v.strip():
                raise ValueError('week cannot be empty string')
            v = v.strip()
        return v

    @validator('preferences')
    def validate_preferences(cls, v):
        if v is not None:
            if not isinstance(v, dict):
                raise ValueError('preferences must be a dictionary')
        return v


class RecommendationResponse(BaseModel):
    """Response model for outfit recommendations."""

    constraints_used: Dict[str, Any] = Field(..., description="Constraints applied")
    outfits: List[Dict[str, Any]] = Field(..., description="Recommended outfits")
    request_id: Optional[str] = Field(None, max_length=100, description="Request identifier")

    @validator('constraints_used')
    def validate_constraints_used(cls, v):
        if not isinstance(v, dict):
            raise ValueError('constraints_used must be a dictionary')
        return v

    @validator('outfits')
    def validate_outfits(cls, v):
        if not isinstance(v, list):
            raise ValueError('outfits must be a list')
        if len(v) > 20:  # Reasonable limit
            raise ValueError('cannot return more than 20 outfits')
        return v


class IngestRequest(BaseModel):
    """Request model for item ingestion."""

    limit: Optional[int] = Field(None, ge=1, le=1000, description="Maximum items to ingest")
    since: Optional[datetime] = Field(None, description="Ingest items updated since this time")

    @validator('limit')
    def validate_limit(cls, v):
        if v is not None and (v < 1 or v > 1000):
            raise ValueError('limit must be between 1 and 1000')
        return v


class IngestResponse(BaseModel):
    """Response model for item ingestion."""

    status: str = Field(..., min_length=1, max_length=50, description="Ingestion status")
    items_processed: int = Field(..., ge=0, description="Number of items processed")
    request_id: Optional[str] = Field(None, max_length=100, description="Request identifier")

    @validator('status')
    def validate_status(cls, v):
        if not v or not v.strip():
            raise ValueError('status cannot be empty')
        return v.strip()

    @validator('items_processed')
    def validate_items_processed(cls, v):
        if v < 0:
            raise ValueError('items_processed cannot be negative')
        return v


class ChatRequest(BaseModel):
    """Request model for chat functionality."""

    session_id: Optional[str] = Field(None, max_length=100, description="Chat session identifier")
    message: str = Field(..., min_length=1, max_length=2000, description="User message")

    @validator('message')
    def validate_message(cls, v):
        if not v or not v.strip():
            raise ValueError('message cannot be empty')
        return v.strip()

    @validator('session_id')
    def validate_session_id(cls, v):
        if v is not None:
            if not v.strip():
                raise ValueError('session_id cannot be empty string')
            v = v.strip()
        return v


class ChatResponse(BaseModel):
    """Response model for chat functionality."""

    session_id: str = Field(..., min_length=1, max_length=100, description="Chat session identifier")
    replies: List[Dict[str, Any]] = Field(..., description="Chat responses")
    outfits: Optional[List[Dict[str, Any]]] = Field(None, description="Recommended outfits")
    request_id: Optional[str] = Field(None, max_length=100, description="Request identifier")

    @validator('session_id')
    def validate_session_id(cls, v):
        if not v or not v.strip():
            raise ValueError('session_id cannot be empty')
        return v.strip()

    @validator('replies')
    def validate_replies(cls, v):
        if not isinstance(v, list):
            raise ValueError('replies must be a list')
        if len(v) > 10:  # Reasonable limit
            raise ValueError('cannot return more than 10 replies')
        return v

    @validator('outfits')
    def validate_outfits(cls, v):
        if v is not None:
            if not isinstance(v, list):
                raise ValueError('outfits must be a list')
            if len(v) > 5:  # Reasonable limit for chat responses
                raise ValueError('cannot return more than 5 outfits in chat response')
        return v