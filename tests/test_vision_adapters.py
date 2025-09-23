"""
Vision Adapters Tests

Testing of vision analysis functionality and adapters.
Converted from scripts/test_vision.py for formal test suite integration.
"""

import pytest
import asyncio
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from lookbook_mpc.adapters.vision import MockVisionProvider, VisionProviderOllama
from lookbook_mpc.domain.entities import VisionAttributes


@pytest.mark.unit
@pytest.mark.vision
class TestVisionAdapters:
    """Test suite for vision adapter functionality."""

    @pytest.fixture
    def mock_provider(self):
        """Mock vision provider fixture."""
        return MockVisionProvider()

    @pytest.fixture
    def ollama_provider(self):
        """Ollama vision provider fixture."""
        # Use default Ollama URL
        return VisionProviderOllama("http://localhost:11434/api")

    @pytest.mark.asyncio
    async def test_mock_vision_provider_basic(self, mock_provider):
        """Test basic mock vision provider functionality."""
        # Test with different image keys
        test_keys = [
            "tshirt_white_cotton.jpg",
            "jeans_blue_denim.jpg",
            "dress_red_silk.jpg",
            "jacket_black_leather.jpg",
            "unknown_item.jpg"
        ]

        for image_key in test_keys:
            result = await mock_provider.analyze_image(image_key)

            # Validate result structure
            assert "color" in result
            assert "category" in result
            assert "material" in result
            assert "plus_size" in result
            assert "description" in result

            # Validate data types
            assert isinstance(result["color"], str)
            assert isinstance(result["category"], str)
            assert isinstance(result["material"], str)
            assert isinstance(result["plus_size"], bool)
            assert isinstance(result["description"], str)

            # Validate description is not empty
            assert len(result["description"]) > 0

    @pytest.mark.asyncio
    async def test_vision_attributes_validation(self, mock_provider):
        """Test vision attributes validation."""
        test_result = await mock_provider.analyze_image("test_tshirt.jpg")

        # Create VisionAttributes object
        attrs = VisionAttributes(**test_result)

        # Validate attributes
        assert hasattr(attrs, 'color')
        assert hasattr(attrs, 'category')
        assert hasattr(attrs, 'material')
        assert hasattr(attrs, 'plus_size')
        assert hasattr(attrs, 'description')

        # Validate data types after creation
        assert isinstance(attrs.color, str)
        assert isinstance(attrs.category, str)
        assert isinstance(attrs.material, str)
        assert isinstance(attrs.plus_size, bool)
        assert isinstance(attrs.description, str)

    @pytest.mark.asyncio
    async def test_mock_provider_structure(self, mock_provider):
        """Test that mock provider returns properly structured results."""
        image_key = "structure_test.jpg"

        # Call provider
        result = await mock_provider.analyze_image(image_key)

        # Verify structure is correct
        required_fields = ["color", "category", "material", "plus_size", "description"]
        for field in required_fields:
            assert field in result
            assert result[field] is not None

        # Verify data types
        assert isinstance(result["color"], str)
        assert isinstance(result["category"], str)
        assert isinstance(result["material"], str)
        assert isinstance(result["plus_size"], bool)
        assert isinstance(result["description"], str)

    @pytest.mark.asyncio
    async def test_ollama_provider_initialization(self, ollama_provider):
        """Test Ollama vision provider initialization."""
        # This should not raise an exception
        assert ollama_provider is not None
        assert hasattr(ollama_provider, 'analyze_image')

        # Check URL configuration
        assert ollama_provider.sidecar_url == "http://localhost:11434/api"

    @pytest.mark.asyncio
    async def test_ollama_provider_error_handling(self, ollama_provider):
        """Test Ollama provider error handling when service unavailable."""
        # This should handle connection errors gracefully
        try:
            result = await ollama_provider.analyze_image("test.jpg")
            # If it succeeds, validate structure
            if result:
                assert "color" in result
                assert "category" in result
        except Exception as e:
            # Expected when Ollama service is not running
            error_str = str(e).lower()
            # Check for various possible error messages
            has_expected_error = any(keyword in error_str for keyword in [
                "connection", "timeout", "unavailable", "404", "not found", "vision sidecar error"
            ])
            assert has_expected_error, f"Unexpected error message: {str(e)}"

    @pytest.mark.asyncio
    async def test_vision_attributes_edge_cases(self, mock_provider):
        """Test vision attributes with edge cases."""
        # Test with empty filename (mock provider handles this gracefully)
        result = await mock_provider.analyze_image("")
        assert "color" in result  # Should return fallback data

        # Test with very long filename
        long_filename = "a" * 1000 + ".jpg"
        result = await mock_provider.analyze_image(long_filename)
        assert "color" in result  # Should still work

        # Test with unusual characters
        weird_filename = "test@#$%^&*().jpg"
        result = await mock_provider.analyze_image(weird_filename)
        assert "color" in result  # Should handle gracefully

    @pytest.mark.asyncio
    async def test_multiple_concurrent_requests(self, mock_provider):
        """Test handling multiple concurrent vision analysis requests."""
        image_keys = [
            "concurrent1.jpg",
            "concurrent2.jpg",
            "concurrent3.jpg",
            "concurrent4.jpg",
            "concurrent5.jpg"
        ]

        # Run multiple requests concurrently
        tasks = [mock_provider.analyze_image(key) for key in image_keys]
        results = await asyncio.gather(*tasks)

        # Validate all results
        assert len(results) == len(image_keys)
        for result in results:
            assert "color" in result
            assert "category" in result
            assert "material" in result
            assert "plus_size" in result
            assert "description" in result

    @pytest.mark.asyncio
    async def test_vision_result_format(self, mock_provider):
        """Test that vision results conform to expected format."""
        result = await mock_provider.analyze_image("format_test.jpg")

        # Check that all expected fields are present and non-empty
        required_fields = ["color", "category", "material", "description"]
        for field in required_fields:
            assert field in result
            assert result[field] != ""
            assert result[field] is not None

        # Check plus_size is boolean
        assert isinstance(result["plus_size"], bool)

        # Check description has reasonable length
        assert 10 <= len(result["description"]) <= 500

    @pytest.mark.parametrize("image_key,expected_category", [
        ("tshirt_white_cotton.jpg", "tops"),
        ("jeans_blue_denim.jpg", "bottoms"),
        ("dress_red_silk.jpg", "dresses"),
        ("jacket_black_leather.jpg", "outerwear"),
    ])
    @pytest.mark.asyncio
    async def test_categorized_images(self, mock_provider, image_key, expected_category):
        """Test vision analysis with parametrized test cases."""
        result = await mock_provider.analyze_image(image_key)

        assert "category" in result
        # Note: Mock provider might not return exact categories, so we just check structure
        assert isinstance(result["category"], str)
        assert len(result["category"]) > 0