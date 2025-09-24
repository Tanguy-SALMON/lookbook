#!/usr/bin/env python3
"""
Test Product Import Script

Quick test to validate database connections and basic import functionality
before running the full 5000 product import.

Usage:
    poetry run python scripts/test_product_import.py
"""

import asyncio
import sys
import os
import logging
from typing import Dict, Any

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lookbook_mpc.adapters.db_shop import MySQLShopCatalogAdapter
from lookbook_mpc.adapters.db_lookbook import MySQLLookbookRepository
from lookbook_mpc.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_connections():
    """Test database connections."""
    print("=== Testing Database Connections ===")

    # Check environment variables
    print(f"MYSQL_SHOP_URL configured: {'Yes' if settings.mysql_shop_url else 'No'}")
    print(f"LOOKBOOK_DB_URL configured: {'Yes' if settings.lookbook_db_url else 'No'}")

    if not settings.mysql_shop_url:
        raise ValueError("MYSQL_SHOP_URL not configured. Please set in .env file.")

    if not settings.lookbook_db_url:
        raise ValueError("LOOKBOOK_DB_URL not configured. Please set in .env file.")

    # Test Magento connection
    try:
        shop_adapter = MySQLShopCatalogAdapter(
            connection_string=settings.mysql_shop_url
        )
        print("✅ Magento database connection: OK")
    except Exception as e:
        print(f"❌ Magento database connection failed: {e}")
        raise

    # Test Lookbook connection
    try:
        lookbook_repo = MySQLLookbookRepository(database_url=settings.lookbook_db_url)
        print("✅ Lookbook database connection: OK")
    except Exception as e:
        print(f"❌ Lookbook database connection failed: {e}")
        raise

    return shop_adapter, lookbook_repo


async def test_magento_query(shop_adapter):
    """Test querying products from Magento."""
    print("\n=== Testing Magento Product Query ===")

    try:
        # Test with small limit first
        products = await shop_adapter.get_enabled_products_with_stock(
            start_after_id=0, limit=5
        )

        print(f"✅ Found {len(products)} enabled products with stock")

        if products:
            sample = products[0]
            print(
                f"Sample product: {sample.get('sku')} - {sample.get('title')} - ฿{sample.get('price')}"
            )
            print(
                f"Source ID range: {min(p.get('source_id', 0) for p in products)} to {max(p.get('source_id', 0) for p in products)}"
            )

        return products

    except Exception as e:
        print(f"❌ Magento query failed: {e}")
        raise


async def test_lookbook_upsert(lookbook_repo, products):
    """Test upserting products to Lookbook database."""
    print("\n=== Testing Lookbook Database Upsert ===")

    if not products:
        print("⚠️ No products to test upsert with")
        return

    try:
        # Transform first product for testing
        sample_product = products[0]

        test_product = {
            "sku": sample_product.get("sku"),
            "title": sample_product.get("title", "Test Product"),
            "price": float(sample_product.get("price", 29.99)),
            "size_range": sample_product.get("size_range", ["S", "M", "L"]),
            "image_key": sample_product.get(
                "image_key", f"{sample_product.get('sku')}.jpg"
            ),
            "attributes": sample_product.get("attributes", {}),
            "in_stock": sample_product.get("in_stock", True),
            "season": sample_product.get("season"),
            "url_key": sample_product.get("url_key"),
            "product_created_at": sample_product.get("product_created_at"),
            "stock_qty": int(sample_product.get("stock_qty", 0)),
            "category": sample_product.get("category", "fashion"),
            "color": sample_product.get("color"),
            "material": sample_product.get("material"),
            "pattern": sample_product.get("pattern"),
            "occasion": sample_product.get("occasion"),
        }

        # Test batch upsert with single product
        result = await lookbook_repo.batch_upsert_products([test_product])

        print(f"✅ Upsert test successful:")
        print(f"   - Inserted: {result.get('upserted', 0)}")
        print(f"   - Updated: {result.get('updated', 0)}")
        print(f"   - Product: {test_product['sku']}")

        return result

    except Exception as e:
        print(f"❌ Lookbook upsert failed: {e}")
        raise


async def test_large_batch(shop_adapter, lookbook_repo):
    """Test with a larger batch to verify performance."""
    print("\n=== Testing Larger Batch (50 products) ===")

    try:
        # Fetch 50 products
        products = await shop_adapter.get_enabled_products_with_stock(
            start_after_id=0, limit=50
        )

        print(f"Fetched {len(products)} products for batch test")

        if not products:
            print("⚠️ No products available for batch test")
            return

        # Transform all products
        transformed_products = []
        for product in products:
            try:
                transformed = {
                    "sku": product.get("sku"),
                    "title": product.get("title", f"Product {product.get('sku')}"),
                    "price": float(product.get("price", 29.99)),
                    "size_range": product.get("size_range", ["S", "M", "L"]),
                    "image_key": product.get("image_key", f"{product.get('sku')}.jpg"),
                    "attributes": product.get("attributes", {}),
                    "in_stock": product.get("in_stock", True),
                    "season": product.get("season"),
                    "url_key": product.get("url_key"),
                    "product_created_at": product.get("product_created_at"),
                    "stock_qty": int(product.get("stock_qty", 0)),
                    "category": product.get("category", "fashion"),
                    "color": product.get("color"),
                    "material": product.get("material"),
                    "pattern": product.get("pattern"),
                    "occasion": product.get("occasion"),
                }
                transformed_products.append(transformed)
            except Exception as e:
                print(f"⚠️ Failed to transform product {product.get('sku')}: {e}")

        print(f"Successfully transformed {len(transformed_products)} products")

        # Batch upsert
        import time

        start_time = time.time()
        result = await lookbook_repo.batch_upsert_products(transformed_products)
        elapsed = time.time() - start_time

        print(f"✅ Batch upsert completed:")
        print(f"   - Products processed: {len(transformed_products)}")
        print(f"   - New products: {result.get('upserted', 0)}")
        print(f"   - Updated products: {result.get('updated', 0)}")
        print(f"   - Time taken: {elapsed:.2f} seconds")
        print(f"   - Rate: {len(transformed_products) / elapsed:.1f} products/sec")

        return result

    except Exception as e:
        print(f"❌ Batch test failed: {e}")
        raise


async def main():
    """Main test function."""
    print("Product Import Test Suite")
    print("=" * 50)

    try:
        # Test 1: Database connections
        shop_adapter, lookbook_repo = await test_connections()

        # Test 2: Magento query
        products = await test_magento_query(shop_adapter)

        # Test 3: Lookbook upsert
        await test_lookbook_upsert(lookbook_repo, products)

        # Test 4: Larger batch
        await test_large_batch(shop_adapter, lookbook_repo)

        print("\n" + "=" * 50)
        print("✅ ALL TESTS PASSED!")
        print("=" * 50)
        print("\nThe system is ready for the full 5000 product import.")
        print("Run: poetry run python scripts/sync_5000_products.py")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        print("=" * 50)
        print("\nPlease fix the issues above before running the full import.")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
