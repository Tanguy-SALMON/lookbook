"""
Lookbook-MPC API Routers Package

This package contains individual route handlers for different API endpoints.
"""

from .ingest import router as ingest_router
from .reco import router as reco_router
from .chat import router as chat_router
from .images import router as images_router

__all__ = [
    "ingest_router",
    "reco_router",
    "chat_router",
    "images_router"
]