
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

        Returns:
            Full image URL
        """
        try:
            # Clean image key (remove any path components)
            clean_key = image_key.split('/')[-1]

            # Construct full URL
            url = f"{self.base_url}/{clean_key}"

            self.logger.debug("Generated image URL", image_key=clean_key, url=url)

            return url

        except Exception as e:
            self.logger.error("Error generating image URL", image_key=image_key, error=str(e))
            raise

    def get_proxy_url(self, image_key: str) -> str:
        """
        Generate proxy URL for image (for CORS control).

        Args:
            image_key: S3 image key

        Returns:
            Proxy URL that will redirect to S3
        """
        try:
            # In a real implementation, this would be a route like:
            # /v1/images/{image_key}
            # Which would handle CORS and redirect to S3

            proxy_url = f"/v1/images/{image_key}"

            self.logger.debug("Generated proxy URL", image_key=image_key, proxy_url=proxy_url)

            return proxy_url

        except Exception as e:
            self.logger.error("Error generating proxy URL", image_key=image_key, error=str(e))
            raise


class MockImageLocator(ImageLocator):
    """Mock image locator for testing purposes."""

    def __init__(self, base_url: str = "https://mock-cdn.example.com"):
        self.base_url = base_url
        self.logger = logger.bind(locator="mock")

    def get_image_url(self, image_key: str) -> str:
        """Generate mock image URL."""
        try:
            # Clean image key
            clean_key = image_key.split('/')[-1]

            # Generate mock URL
            url = f"{self.base_url}/{clean_key}"

            self.logger.debug("Mock image URL generated", image_key=clean_key, url=url)

            return url

        except Exception as e:
            self.logger.error("Error in mock image URL generation", error=str(e))
            return f"{self.base_url}/default.jpg"

    def get_proxy_url(self, image_key: str) -> str:
        """Generate mock proxy URL."""
        try:
            clean_key = image_key.split('/')[-1]
            proxy_url = f"/v1/images/{clean_key}"

            self.logger.debug("Mock proxy URL generated", image_key=clean_key, proxy_url=proxy_url)

            return proxy_url

        except Exception as e:
            self.logger.error("Error in mock proxy URL generation", error=str(e))
            return "/v1/images/default.jpg"


class ImageProcessor:
    """Utility class for image processing operations."""

    def __init__(self, max_size: int = 200):
        self.max_size = max_size
        self.logger = logger.bind(processor="image")

    def process_image_for_llm(self, image_data: bytes) -> bytes:
        """
        Process image for LLM analysis (resize, format, etc.).

        Args:
            image_data: Raw image bytes

        Returns:
            Processed image bytes
