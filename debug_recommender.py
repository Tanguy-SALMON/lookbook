#!/usr/bin/env python3
"""
Debug script to test recommendation engine and product categorization.
Helps identify why only tops are being returned without bottoms.
"""

import asyncio
import os
import sys
import json
from typing import Dict, Any, List

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lookbook_mpc.services.smart_recommender import SmartRecommender
from lookbook_mpc.adapters.db_lookbook import MySQLLookbookRepository
from lookbook_mpc.config.settings import get_settings


async def debug_product_categories():
    """Check what product categories exist in the database."""
    print("=== DEBUGGING PRODUCT CATEGORIES ===\n")

    try:
        settings = get_settings()
        repository = MySQLLookbookRepository(settings.get_database_url())
        conn = await repository._get_connection()
        cursor = await conn.cursor()

        # Get category distribution
        query = """
        SELECT category, COUNT(*) as count
        FROM products
        WHERE in_stock = 1
        GROUP BY category
        ORDER BY count DESC
        """

        await cursor.execute(query)
        categories = await cursor.fetchall()

        print("Product Categories in Database:")
        for category, count in categories:
            print(f"  {category or 'NULL'}: {count} products")

        print("\n" + "="*50)

        # Get some sample products from each category
        print("\nSample Products by Category:")
        for category, _ in categories[:5]:  # Top 5 categories
            query = """
            SELECT sku, title, category, color, price
            FROM products
            WHERE category = %s AND in_stock = 1
            LIMIT 3
            """

            await cursor.execute(query, (category,))
            samples = await cursor.fetchall()

            print(f"\n{category or 'NULL'} samples:")
            for sku, title, cat, color, price in samples:
                print(f"  - {sku}: {title} | {color} | ${price}")

        await cursor.close()
        conn.close()

    except Exception as e:
        print(f"Database error: {e}")


async def debug_keyword_generation():
    """Test keyword generation for dance request."""
    print("\n=== DEBUGGING KEYWORD GENERATION ===\n")

    try:
        settings = get_settings()
        repository = MySQLLookbookRepository(settings.get_database_url())
        recommender = SmartRecommender(repository)

        test_message = "I go to dance"
        print(f"Test message: '{test_message}'")

        keywords = await recommender._generate_keywords_from_message(test_message)

        print("\nGenerated Keywords:")
        print(json.dumps(keywords, indent=2))

        return keywords

    except Exception as e:
        print(f"Keyword generation error: {e}")
        return None


async def debug_product_search(keywords: Dict[str, Any]):
    """Test product search with generated keywords."""
    print("\n=== DEBUGGING PRODUCT SEARCH ===\n")

    if not keywords:
        print("No keywords to search with")
        return []

    try:
        settings = get_settings()
        repository = MySQLLookbookRepository(settings.get_database_url())
        recommender = SmartRecommender(repository)

        products = await recommender._search_products_by_keywords(keywords, limit=15)

        print(f"Found {len(products)} products:")

        # Group by category to see distribution
        by_category = {}
        for product in products:
            cat = product.get('category', 'unknown')
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(product)

        for category, items in by_category.items():
            print(f"\n{category.upper()} ({len(items)} items):")
            for item in items[:3]:  # Show first 3
                score = item.get('relevance_score', 0)
                print(f"  - {item.get('sku')}: {item.get('title')} | Score: {score:.2f}")

        return products

    except Exception as e:
        print(f"Product search error: {e}")
        return []


async def debug_outfit_creation(products: List[Dict[str, Any]], keywords: Dict[str, Any]):
    """Test outfit creation logic."""
    print("\n=== DEBUGGING OUTFIT CREATION ===\n")

    if not products:
        print("No products to create outfits with")
        return

    try:
        settings = get_settings()
        repository = MySQLLookbookRepository(settings.get_database_url())
        recommender = SmartRecommender(repository)

        # Test the grouping logic
        grouped = recommender._group_products_by_category(products)

        print("Products grouped by category:")
        for category, items in grouped.items():
            if items:
                print(f"  {category}: {len(items)} items")
                for item in items[:2]:  # Show first 2
                    print(f"    - {item.get('title')}")

        # Test outfit creation
        outfits = await recommender._create_outfit_combinations(products, keywords, limit=5)

        print(f"\nCreated {len(outfits)} outfits:")
        for i, outfit in enumerate(outfits, 1):
            print(f"\nOutfit {i}: {outfit.get('title')}")
            print(f"  Type: {outfit.get('outfit_type')}")
            print(f"  Items: {len(outfit.get('items', []))}")
            for item in outfit.get('items', []):
                print(f"    - {item.get('title')} ({item.get('category', 'unknown')})")
            print(f"  Total: ${outfit.get('total_price', 0)}")

    except Exception as e:
        print(f"Outfit creation error: {e}")


async def debug_full_recommendation():
    """Test the complete recommendation flow."""
    print("\n=== DEBUGGING FULL RECOMMENDATION FLOW ===\n")

    try:
        settings = get_settings()
        repository = MySQLLookbookRepository(settings.get_database_url())
        recommender = SmartRecommender(repository)

        test_message = "I need something for a business meeting"
        print(f"Test message: '{test_message}'")

        outfits = await recommender.recommend_outfits(test_message, limit=3)

        print(f"\nFinal recommendation returned {len(outfits)} outfits:")

        for i, outfit in enumerate(outfits, 1):
            print(f"\nOutfit {i}:")
            print(f"  Title: {outfit.get('title')}")
            print(f"  Type: {outfit.get('outfit_type')}")
            print(f"  Items: {len(outfit.get('items', []))}")

            categories_in_outfit = set()
            for item in outfit.get('items', []):
                category = item.get('category', 'unknown')
                categories_in_outfit.add(category)
                print(f"    - {item.get('title')} ({category})")

            print(f"  Categories represented: {', '.join(sorted(categories_in_outfit))}")
            print(f"  Total: ${outfit.get('total_price', 0)}")

            # Check if we have both top and bottom
            has_top = 'top' in categories_in_outfit
            has_bottom = 'bottom' in categories_in_outfit
            has_dress = 'dress' in categories_in_outfit

            if not has_dress and not (has_top and has_bottom):
                print(f"  ⚠️  INCOMPLETE OUTFIT: Missing {'bottom' if has_top else 'top and bottom'}")

    except Exception as e:
        print(f"Full recommendation error: {e}")


async def main():
    """Run all debug tests."""
    print("LOOKBOOK-MPC RECOMMENDATION ENGINE DEBUGGER")
    print("=" * 50)

    # Step 1: Check database categories
    await debug_product_categories()

    # Step 2: Test keyword generation
    keywords = await debug_keyword_generation()

    # Step 3: Test product search
    products = await debug_product_search(keywords)

    # Step 4: Test outfit creation
    await debug_outfit_creation(products, keywords or {})

    # Step 5: Test full flow
    await debug_full_recommendation()

    print("\n" + "=" * 50)
    print("DEBUG COMPLETE")


if __name__ == "__main__":
    asyncio.run(main())
