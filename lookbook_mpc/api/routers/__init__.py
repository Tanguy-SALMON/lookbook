"""
Lookbook-MPC API Routers Package

This package contains individual route handlers for different API endpoints.
"""

from .ingest import router as ingest_router
from .reco import router as reco_router
from .chat import router as chat_router
from .images import router as images_router
from .agents import router as agents_router
from .personas import router as personas_router
from .settings import router as settings_router
from .products import router as products_router
from .product_import import router as product_import_router
from .vision_analysis import router as vision_analysis_router
from .lookbooks import router as lookbooks_router
from .akeneo_export import router as akeneo_export_router
from .akeneo_settings import router as akeneo_settings_router

__all__ = [
    "ingest_router",
    "reco_router",
    "chat_router",
    "images_router",
    "agents_router",
    "personas_router",
    "settings_router",
    "products_router",
    "product_import_router",
    "vision_analysis_router",
    "lookbooks_router",
    "akeneo_export_router",
    "akeneo_settings_router",
]
