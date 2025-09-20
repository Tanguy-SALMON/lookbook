#!/usr/bin/env python3
"""
Database Test Script

This script tests the database functionality and repository operations.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from lookbook_mpc.adapters.db_lookbook import SQLiteLookbookRepository
from lookbook_mpc.adapters.db_shop import MockShopCatalogAdapter
from lookbook_mpc.domain.entities import Item
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_database_operations():
    """Test database operations."""
    try:
        print("Testing database operations...")

        # Initialize repository
        repo = SQLiteLookbookRepository("sqlite+aiosqlite:///lookbook.db")

        # Test 1: Get all items (should be empty initially)
        print("Test 1: Getting all items...")
        items = await repo.get_all_items()
        print(f"✓ Found {len(items)} items (expected: 0)")

        # Test 2: Save some test items
        print("\nTest 2: Saving test items...")
        test_items = [
            Item(
                sku="TEST001",
                title="Test T-Shirt",
                price=19.99,
                size_range=["S", "M", "L"],
                image_key="test1.jpg",
                attributes={"color": "blue", "category": "top"},
                in_stock=True
            ),
            Item(
                sku="TEST002",
                title="Test Jeans",
                price=49.99,
                size_range=["M", "L", "XL"],
                image_key="test2.jpg",
                attributes={"color": "blue", "category": "bottom"},
                in_stock=True
            )
        ]

        saved_count = await repo.save_items([item.model_dump() for item in test_items])
        print(f"✓ Saved {saved_count} items")

        # Test 3: Get all items again
        print("\nTest 3: Getting all items after save...")
        items = await repo.get_all_items()
        print(f"✓ Found {len(items)} items (expected: 2)")

        # Test 4: Search items
        print("\nTest 4: Searching items by color...")
        results = await repo.search_items({"color": "blue"})
        print(f"✓ Found {len(results)} blue items (expected: 2)")

        # Test 5: Search items by category
        print("\nTest 5: Searching items by category...")
        results = await repo.search_items({"category": "top"})
        print(f"✓ Found {len(results)} top items (expected: 1)")

        # Test 6: Get item by ID
        print("\nTest 6: Getting item by ID...")
        if items:
            item_id = items[0].id
            item = await repo.get_item_by_id(item_id)
            print(f"✓ Found item: {item.title if item else 'None'}")

        # Test 7: Test shop catalog adapter
        print("\nTest 7: Testing shop catalog adapter...")
        shop_adapter = MockShopCatalogAdapter()
        shop_items = await shop_adapter.fetch_items(limit=5)
        print(f"✓ Fetched {len(shop_items)} items from shop catalog")

        # Test 8: Test shop catalog get by SKU
        if shop_items:
            sku = shop_items[0]["sku"]
            item = await shop_adapter.get_item_by_sku(sku)
            print(f"✓ Found item by SKU {sku}: {item['title'] if item else 'None'}")

        print("\n🎉 All database tests passed!")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(test_database_operations())