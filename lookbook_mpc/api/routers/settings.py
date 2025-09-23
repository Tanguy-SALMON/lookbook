"""
Settings API Router

This router provides endpoints for application settings and configuration.
"""

import os
from typing import Dict, Any
from fastapi import APIRouter, HTTPException
import structlog

from lookbook_mpc.config.settings import get_settings

logger = structlog.get_logger()
router = APIRouter(prefix="/v1/settings", tags=["settings"])


@router.get("/environment")
async def get_environment_variables() -> Dict[str, Any]:
    """Get environment variables and configuration settings."""
    try:
        settings = get_settings()

        # Return a curated set of environment variables and settings
        env_vars = {
            # Ollama Settings
            "OLLAMA_HOST": settings.ollama_host,
            "OLLAMA_VISION_MODEL": settings.ollama_vision_model,
            "OLLAMA_TEXT_MODEL": settings.ollama_text_model,
            # Storage & CDN
            "S3_BASE_URL": settings.s3_base_url,
            "PRODUCT_LINK_BASE_URL": settings.product_link_base_url,
            # Database Configuration
            "LOOKBOOK_DB_URL": settings.lookbook_db_url,
            "MYSQL_SHOP_URL": settings.mysql_shop_url,
            # Application Settings
            "LOG_LEVEL": settings.log_level,
            "TZ": os.getenv("TZ", "UTC"),
            "VISION_PORT": str(
                settings.api_port + 1
            ),  # Assuming vision runs on next port
            # Optional/Runtime
            "CORS_ORIGINS": os.getenv("CORS_ORIGINS"),
            "LOG_FORMAT": settings.log_format,
            "LOG_FILE": os.getenv("LOG_FILE"),
            # Additional settings
            "LLM_PROVIDER": settings.llm_provider,
            "API_HOST": settings.api_host,
            "API_PORT": str(settings.api_port),
            "VISION_SIDECAR_HOST": settings.vision_sidecar_host,
            "FEATURE_MCP": str(settings.feature_mcp),
            "FEATURE_METRICS": str(settings.feature_metrics),
        }

        return {"success": True, "data": env_vars}

    except Exception as e:
        logger.error("Error fetching environment variables", error=str(e))
        raise HTTPException(
            status_code=500, detail="Failed to fetch environment variables"
        )


@router.post("/")
async def update_settings(settings_data: Dict[str, Any]) -> Dict[str, Any]:
    """Update application settings (placeholder implementation for testing)."""
    try:
        logger.info("Settings update requested", data=settings_data)

        # This is a placeholder implementation for testing
        # In a real application, you would validate and persist the settings

        return {
            "success": True,
            "message": "Settings updated successfully",
            "data": settings_data,
        }

    except Exception as e:
        logger.error("Error updating settings", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to update settings")
