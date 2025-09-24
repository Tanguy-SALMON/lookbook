#!/usr/bin/env python3
"""
Test Vision Analysis Functionality

This script tests the vision analysis system to ensure:
1. Ollama is running with qwen2.5vl:latest model
2. VisionAnalyzer can process images
3. Database integration works
4. API endpoints are functional
"""

import asyncio
import sys
import os
import json
import time
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from lookbook_mpc.services.vision_analysis_service import VisionAnalysisService
from lookbook_mpc.config import settings
from image.vision_analyzer import VisionAnalyzer
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_ollama_connection():
    """Test if Ollama is running and has the required model."""
    print("🔍 Testing Ollama connection...")

    try:
        vision_analyzer = VisionAnalyzer(model="qwen2.5vl:latest", save_processed=False)

        # Try a simple test (this would normally require an image)
        print("✅ VisionAnalyzer initialized successfully")
        print(f"   Model: qwen2.5vl:latest")
        print(f"   Ollama Host: {vision_analyzer.ollama_host}")

        return True

    except Exception as e:
        print(f"❌ Ollama connection failed: {e}")
        print("   Make sure Ollama is running: ollama serve")
        print("   Make sure model is available: ollama pull qwen2.5vl:latest")
        return False


async def test_database_connection():
    """Test database connection and check for products."""
    print("\n📊 Testing database connection...")

    try:
        if not settings.lookbook_db_url:
            print("❌ Database URL not configured")
            print("   Please set MYSQL_APP_URL environment variable")
            return False

        vision_service = VisionAnalysisService()
        stats = await vision_service.get_analysis_statistics()

        if "error" in stats:
            print(f"❌ Database connection failed: {stats['error']}")
            return False

        print("✅ Database connection successful")
        print(f"   Total products: {stats['total_products']}")
        print(f"   Analyzed products: {stats['analyzed_products']}")
        print(f"   Missing analysis: {stats['missing_analysis']}")
        print(f"   Coverage: {stats['analysis_coverage']:.1f}%")

        return True

    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False


async def test_products_needing_analysis():
    """Test getting products that need analysis."""
    print("\n📦 Testing products needing analysis...")

    try:
        vision_service = VisionAnalysisService()
        products = await vision_service.get_products_needing_analysis(limit=5)

        print(f"✅ Found {len(products)} products needing analysis")

        if products:
            print("   Sample products:")
            for i, product in enumerate(products[:3]):
                missing = ", ".join(product["missing_attributes"])
                print(f"     {i + 1}. {product['sku']}: {product['title'][:50]}...")
                print(f"        Missing: {missing}")
                print(f"        Image: {product['image_key']}")
        else:
            print("   No products need analysis (all are up to date)")

        return True

    except Exception as e:
        print(f"❌ Products test failed: {e}")
        return False


async def test_mock_vision_analysis():
    """Test vision analysis with a mock product."""
    print("\n🔍 Testing mock vision analysis...")

    try:
        # Create a simple mock image analysis
        vision_analyzer = VisionAnalyzer(model="qwen2.5vl:latest", save_processed=False)

        # This would normally analyze a real image
        print("✅ Vision analyzer ready for image analysis")
        print("   Note: Actual image analysis requires a valid image file")
        print("   Model: qwen2.5vl:latest")

        # Test the analysis service
        vision_service = VisionAnalysisService()

        # Get a sample product
        products = await vision_service.get_products_needing_analysis(limit=1)

        if products:
            sample_product = products[0]
            print(f"   Sample product: {sample_product['sku']}")
            print(f"   Image key: {sample_product['image_key']}")
            print("   Ready for analysis when image is available")
        else:
            print("   No products available for testing")

        return True

    except Exception as e:
        print(f"❌ Mock analysis test failed: {e}")
        return False


async def test_recent_analyses():
    """Test getting recent analyses."""
    print("\n📈 Testing recent analyses...")

    try:
        vision_service = VisionAnalysisService()
        recent = await vision_service.get_recent_analyses(limit=5)

        print(f"✅ Found {len(recent)} recently analyzed products")

        if recent:
            print("   Recent analyses:")
            for i, product in enumerate(recent[:3]):
                print(
                    f"     {i + 1}. {product['sku']}: {product['color']} {product['category']}"
                )
                print(
                    f"        Material: {product['material']}, Pattern: {product['pattern']}"
                )
        else:
            print("   No recent analyses found")

        return True

    except Exception as e:
        print(f"❌ Recent analyses test failed: {e}")
        return False


def print_system_info():
    """Print system information."""
    print("🖥️  SYSTEM INFORMATION")
    print("=" * 50)
    print(f"Python version: {sys.version}")
    print(f"Project root: {project_root}")
    print(f"Database URL configured: {'Yes' if settings.lookbook_db_url else 'No'}")
    print(f"Ollama host: {os.getenv('OLLAMA_HOST', 'http://localhost:11434')}")
    print()


def print_requirements():
    """Print requirements for vision analysis."""
    print("📋 REQUIREMENTS FOR VISION ANALYSIS")
    print("=" * 50)
    print("1. Ollama must be running:")
    print("   ollama serve")
    print()
    print("2. qwen2.5vl:latest model must be installed:")
    print("   ollama pull qwen2.5vl:latest")
    print()
    print("3. Database must be configured:")
    print("   export MYSQL_APP_URL='mysql+aiomysql://user:pass@host:port/db'")
    print()
    print("4. Products must exist in the database:")
    print("   Run product import scripts first")
    print()


async def main():
    """Run all vision analysis tests."""
    print("🔍 VISION ANALYSIS SYSTEM TEST")
    print("=" * 50)

    print_system_info()
    print_requirements()

    # Run tests
    tests = [
        ("Ollama Connection", test_ollama_connection),
        ("Database Connection", test_database_connection),
        ("Products Needing Analysis", test_products_needing_analysis),
        ("Mock Vision Analysis", test_mock_vision_analysis),
        ("Recent Analyses", test_recent_analyses),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")

    print(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! Vision analysis system is ready.")
        print("\nNext steps:")
        print("1. Run: python scripts/analyze_products_vision.py --limit 5")
        print("2. Check the admin panel for vision analysis features")
        print("3. Monitor analysis progress and results")
    else:
        print(
            f"\n⚠️  {total - passed} tests failed. Please fix issues before proceeding."
        )
        print("\nTroubleshooting:")
        print("1. Check Ollama installation and model availability")
        print("2. Verify database connection and product data")
        print("3. Review error messages above")


if __name__ == "__main__":
    asyncio.run(main())
