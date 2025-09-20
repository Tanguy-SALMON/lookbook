"""
Vision Analysis Adapter

This adapter handles vision analysis using Ollama models to extract
attributes from product images.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging
import structlog
import aiohttp
import asyncio
import random

from ..domain.entities import Category, Material, Pattern, Season, Occasion, Fit

logger = structlog.get_logger()


class VisionProvider(ABC):
    """Abstract base class for vision providers."""

    @abstractmethod
    async def analyze_image(self, image_key: str) -> Dict[str, Any]:
        """Analyze image and extract attributes."""
        pass


class VisionProviderOllama(VisionProvider):
    """Ollama-based vision provider that calls the vision sidecar."""

    def __init__(self, sidecar_url: str, timeout: int = 40):
        self.sidecar_url = sidecar_url
        self.timeout = timeout
        self.logger = logger.bind(provider="vision_sidecar", url=sidecar_url)

    async def analyze_image(self, image_key: str) -> Dict[str, Any]:
        """
        Analyze image using vision sidecar.

        Args:
            image_key: S3 image key for the product image

        Returns:
            Dictionary with extracted vision attributes
        """
        try:
            self.logger.info("Analyzing image with vision sidecar", image_key=image_key)

            # Call vision sidecar
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            ) as session:
                payload = {"image_key": image_key}

                async with session.post(
                    f"{self.sidecar_url}/analyze", json=payload
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result
                    else:
                        error_text = await response.text()
                        raise Exception(
                            f"Vision sidecar error: {response.status} - {error_text}"
                        )

        except Exception as e:
            self.logger.error(
                "Error analyzing image", image_key=image_key, error=str(e)
            )
            raise


class MockVisionProvider(VisionProvider):
    """Mock vision provider for testing purposes with realistic fashion data."""

    def __init__(self):
        self.logger = logger.bind(provider="mock_vision")

        # Realistic fashion combinations
        self.mock_data = {
            "tshirt": [
                {
                    "color": "white",
                    "category": Category.TOP.value,
                    "material": Material.COTTON.value,
                    "pattern": Pattern.PLAIN.value,
                    "style": "classic",
                    "season": Season.SUMMER.value,
                    "occasion": Occasion.CASUAL.value,
                    "fit": Fit.REGULAR.value,
                    "plus_size": False,
                    "description": "Classic white cotton t-shirt with crew neck and short sleeves. Perfect for everyday wear.",
                },
                {
                    "color": "navy",
                    "category": Category.TOP.value,
                    "material": Material.COTTON.value,
                    "pattern": Pattern.STRIPED.value,
                    "style": "casual",
                    "season": Season.SPRING.value,
                    "occasion": Occasion.CASUAL.value,
                    "fit": Fit.SLIM.value,
                    "plus_size": False,
                    "description": "Navy blue striped cotton t-shirt with modern slim fit. Versatile piece for casual styling.",
                },
            ],
            "jeans": [
                {
                    "color": "denim-blue",
                    "category": Category.BOTTOM.value,
                    "material": Material.DENIM.value,
                    "pattern": Pattern.PLAIN.value,
                    "style": "casual",
                    "season": Season.AUTUMN.value,
                    "occasion": Occasion.CASUAL.value,
                    "fit": Fit.SLIM.value,
                    "plus_size": False,
                    "description": "Classic slim-fit blue jeans with five-pocket styling. Durable denim with comfortable stretch.",
                },
                {
                    "color": "black",
                    "category": Category.BOTTOM.value,
                    "material": Material.DENIM.value,
                    "pattern": Pattern.PLAIN.value,
                    "style": "modern",
                    "season": Season.WINTER.value,
                    "occasion": Occasion.CASUAL.value,
                    "fit": Fit.REGULAR.value,
                    "plus_size": False,
                    "description": "Black denim jeans with regular fit. Versatile and sophisticated for various occasions.",
                },
            ],
            "dress": [
                {
                    "color": "red",
                    "category": Category.DRESS.value,
                    "material": Material.SILK.value,
                    "pattern": Pattern.PLAIN.value,
                    "style": "elegant",
                    "season": Season.SUMMER.value,
                    "occasion": Occasion.PARTY.value,
                    "fit": Fit.REGULAR.value,
                    "plus_size": False,
                    "description": "Elegant red silk dress with flowing silhouette. Perfect for special occasions and evening events.",
                },
                {
                    "color": "floral",
                    "category": Category.DRESS.value,
                    "material": Material.CHIFFON.value,
                    "pattern": Pattern.FLORAL.value,
                    "style": "romantic",
                    "season": Season.SPRING.value,
                    "occasion": Occasion.CASUAL.value,
                    "fit": Fit.LOOSE.value,
                    "plus_size": False,
                    "description": "Romantic floral chiffon dress with loose fit and flowing fabric. Ideal for spring outings.",
                },
            ],
            "jacket": [
                {
                    "color": "black",
                    "category": Category.OUTERWEAR.value,
                    "material": Material.LEATHER.value,
                    "pattern": Pattern.PLAIN.value,
                    "style": "edgy",
                    "season": Season.AUTUMN.value,
                    "occasion": Occasion.CASUAL.value,
                    "fit": Fit.SLIM.value,
                    "plus_size": False,
                    "description": "Classic black leather jacket with modern slim fit. Timeless piece for edgy styling.",
                },
            ],
            "sneakers": [
                {
                    "color": "white",
                    "category": Category.SHOES.value,
                    "material": Material.LEATHER.value,
                    "pattern": Pattern.PLAIN.value,
                    "style": "athletic",
                    "season": Season.SUMMER.value,
                    "occasion": Occasion.SPORT.value,
                    "fit": Fit.REGULAR.value,
                    "plus_size": False,
                    "description": "Clean white leather sneakers with classic athletic styling. Comfortable for daily activities.",
                },
            ],
        }

    async def analyze_image(self, image_key: str) -> Dict[str, Any]:
        """Return realistic mock vision attributes based on image key patterns."""
        self.logger.info("Mock image analysis", image_key=image_key)

        # Determine category from image key
        key_lower = image_key.lower()

        # Match patterns to categories
        if any(
            word in key_lower
            for word in ["tshirt", "t-shirt", "shirt", "blouse", "top"]
        ):
            category_data = self.mock_data.get("tshirt", [])
        elif any(
            word in key_lower for word in ["jeans", "pants", "trousers", "bottom"]
        ):
            category_data = self.mock_data.get("jeans", [])
        elif any(word in key_lower for word in ["dress", "gown"]):
            category_data = self.mock_data.get("dress", [])
        elif any(
            word in key_lower for word in ["jacket", "coat", "blazer", "cardigan"]
        ):
            category_data = self.mock_data.get("jacket", [])
        elif any(word in key_lower for word in ["shoe", "sneaker", "boot", "heel"]):
            category_data = self.mock_data.get("sneakers", [])
        else:
            # Default fallback with variety
            fallback_options = [
                {
                    "color": random.choice(["black", "white", "navy", "grey", "beige"]),
                    "category": random.choice(list(Category)).value,
                    "material": random.choice(list(Material)).value,
                    "pattern": random.choice(list(Pattern)).value,
                    "style": "modern",
                    "season": random.choice(list(Season)).value,
                    "occasion": random.choice(list(Occasion)).value,
                    "fit": random.choice(list(Fit)).value,
                    "plus_size": random.choice([True, False]),
                    "description": f"Stylish fashion item with modern design and quality construction.",
                }
            ]
            category_data = fallback_options

        # Return a random variation from the category
        if category_data:
            result = random.choice(category_data)
            # Add some variability for plus_size based on image key hints
            if any(word in key_lower for word in ["plus", "xl", "xxl", "3xl", "large"]):
                result = result.copy()
                result["plus_size"] = True
                result["description"] += " Available in plus sizes for comfortable fit."
            return result

        # Ultimate fallback
        return {
            "color": "black",
            "category": Category.ACCESSORY.value,
            "material": Material.POLYESTER.value,
            "pattern": Pattern.PLAIN.value,
            "style": "modern",
            "season": Season.AUTUMN.value,
            "occasion": Occasion.CASUAL.value,
            "fit": Fit.REGULAR.value,
            "plus_size": False,
            "description": "Modern fashion accessory with versatile styling options.",
        }
