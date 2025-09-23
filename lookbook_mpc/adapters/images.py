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
        self.base_url = base_url.rstrip("/")
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
            clean_key = image_key.split("/")[-1]

            # Construct full URL
            url = f"{self.base_url}/{clean_key}"

            self.logger.debug("Generated image URL", image_key=clean_key, url=url)

            return url

        except Exception as e:
            self.logger.error(
                "Error generating image URL", image_key=image_key, error=str(e)
            )
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

            self.logger.debug(
                "Generated proxy URL", image_key=image_key, proxy_url=proxy_url
            )

            return proxy_url

        except Exception as e:
            self.logger.error(
                "Error generating proxy URL", image_key=image_key, error=str(e)
            )
            raise


class MockImageLocator(ImageLocator):
    """Mock image locator for testing purposes."""

    def __init__(self, base_url: str = "https://picsum.photos"):
        self.base_url = base_url.rstrip("/")
        self.logger = logger.bind(locator="mock")

    def get_image_url(self, image_key: str) -> str:
        """Generate mock image URL using a working test image service."""
        try:
            # Clean image key
            clean_key = image_key.split("/")[-1]

            # Generate working test image URL (200x200 for testing)
            # Picsum.photos provides real test images that work reliably
            if "test-image" in clean_key:
                url = f"{self.base_url}/200/200"
            else:
                # Use a deterministic seed based on filename for consistency
                seed = hash(clean_key) % 1000
                url = f"{self.base_url}/200/200?random={seed}"

            self.logger.debug("Mock image URL generated", image_key=clean_key, url=url)

            return url

        except Exception as e:
            self.logger.error("Error in mock image URL generation", error=str(e))
            return f"{self.base_url}/200/200"

    def get_proxy_url(self, image_key: str) -> str:
        """Generate mock proxy URL."""
        try:
            clean_key = image_key.split("/")[-1]
            proxy_url = f"/v1/images/{clean_key}"

            self.logger.debug(
                "Mock proxy URL generated", image_key=clean_key, proxy_url=proxy_url
            )

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
        """
        try:
            from PIL import Image
            import io

            # Open image
            img = Image.open(io.BytesIO(image_data))

            # Convert to RGB if needed
            if img.mode != "RGB":
                img = img.convert("RGB")

            # Resize if needed
            if max(img.size) > self.max_size:
                ratio = self.max_size / max(img.size)
                new_size = tuple([int(x * ratio) for x in img.size])
                img = img.resize(new_size, Image.Resampling.LANCZOS)

            # Convert back to bytes
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=85)
            processed_data = buffer.getvalue()

            self.logger.debug(
                "Image processed for LLM",
                original_size=img.size,
                processed_size=len(processed_data),
            )

            return processed_data

        except Exception as e:
            self.logger.error("Error processing image for LLM", error=str(e))
            raise

    def validate_image_format(self, image_data: bytes) -> bool:
        """
        Validate that image data is in a supported format.

        Args:
            image_data: Raw image bytes

        Returns:
            True if valid format, False otherwise
        """
        try:
            from PIL import Image
            import io

            # Try to open with PIL
            img = Image.open(io.BytesIO(image_data))

            # Verify it's actually an image
            img.verify()

            return True

        except Exception as e:
            self.logger.warning("Invalid image format", error=str(e))
            return False


class ImageCache:
    """Simple in-memory cache for image URLs."""

    def __init__(self, max_size: int = 1000):
        self.cache = {}
        self.max_size = max_size
        self.logger = logger.bind(cache="image")

    def get(self, image_key: str) -> Optional[str]:
        """Get cached image URL."""
        return self.cache.get(image_key)

    def set(self, image_key: str, url: str) -> None:
        """Cache image URL."""
        # Simple LRU eviction
        if len(self.cache) >= self.max_size:
            # Remove oldest entry (simplified)
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]

        self.cache[image_key] = url
        self.logger.debug("Image URL cached", image_key=image_key)

    def clear(self) -> None:
        """Clear all cached URLs."""
        self.cache.clear()
        self.logger.debug("Image cache cleared")
