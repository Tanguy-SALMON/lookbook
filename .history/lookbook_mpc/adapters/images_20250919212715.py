
"""
Image Handling Adapter

This adapter handles image URL generation, S3 integration,
and optional proxy endpoints for CORS control.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging
import structlog

logger = structlog.get_logger()


class ImageLocator(ABC):
    """Abstract base class for image locators."""

    @abstractmethod
    def get_image_url(self, image_key: str) -> str:
        """Get full image URL from image key."""
        pass

    @abstractmethod
    def get_proxy_url(self, image_key: str) -> str:
        """Get proxy URL for image (for CORS control)."""
        pass


class S3ImageLocator(ImageLocator):
    """S3-based image locator."""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.logger = logger.bind(locator="s3", base_url=base_url)

    def get_image_url(self, image_key: str) -> str:
        """
        Generate full S3 image URL from image key.

        Args:
            image_key: S3 image key (filename)

