"""
Lookbook-MPC Domain Package

This package contains domain entities and use cases that define the core
business logic of the application, independent of infrastructure concerns.
"""

from .entities import Item, Outfit, OutfitItem, Rule, Intent
from .use_cases import IngestItems, RecommendOutfits, BuildLookbook, ChatTurn

__all__ = [
    "Item",
    "Outfit",
    "OutfitItem",
    "Rule",
    "Intent",
    "IngestItems",
    "RecommendOutfits",
    "BuildLookbook",
    "ChatTurn"
]