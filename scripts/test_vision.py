#!/usr/bin/env python3
"""
Vision Test Script

This script tests the vision analysis functionality.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from lookbook_mpc.adapters.vision import MockVisionProvider, VisionProviderOllama
from lookbook_mpc.domain.entities import VisionAttributes
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_vision_analysis():
    """Test vision analysis functionality."""
    try:
        print("Testing vision analysis...")

        # Test 1: Mock vision provider
        print("\nTest 1: Testing mock vision provider...")
        mock_provider = MockVisionProvider()

        # Test with different image keys
        test_keys = [
            "tshirt_white_cotton.jpg",
            "jeans_blue_denim.jpg",
            "dress_red_silk.jpg",
            "jacket_black_leather.jpg",
            "unknown_item.jpg"
        ]

        for image_key in test_keys:
            print(f"  Analyzing: {image_key}")
            result = await mock_provider.analyze_image(image_key)
            print(f"    Color: {result['color']}")
            print(f"    Category: {result['category']}")
            print(f"    Material: {result['material']}")
            print(f"    Plus Size: {result['plus_size']}")
            print(f"    Description: {result['description'][:50]}...")

        # Test 2: Vision attributes validation
        print("\nTest 2: Testing vision attributes validation...")
        test_result = await mock_provider.analyze_image("test_tshirt.jpg")

        try:
            # Create VisionAttributes object
            attrs = VisionAttributes(**test_result)
            print(f"  ✓ VisionAttributes created successfully")
            print(f"    Color: {attrs.color}")
            print(f"    Category: {attrs.category}")
            print(f"    Plus Size: {attrs.plus_size}")
        except Exception as e:
            print(f"  ❌ VisionAttributes validation failed: {e}")

        # Test 3: Ollama vision provider (if configured)
        print("\nTest 3: Testing Ollama vision provider...")
        ollama_url = "http://localhost:11434"  # Default Ollama host

        try:
            ollama_provider = VisionProviderOllama(f"{ollama_url}/api")
            print(f"  Ollama provider initialized with URL: {ollama_url}")

            # Note: This would require a running vision sidecar
            # For now, just test initialization
            print(f"  ✓ Ollama provider initialized successfully")

        except Exception as e:
            print(f"  ⚠️  Ollama provider initialization failed (expected if sidecar not running): {e}")

        print("\n🎉 Vision analysis tests completed!")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(test_vision_analysis())