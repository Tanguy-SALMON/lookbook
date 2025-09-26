#!/usr/bin/env python3
"""
Debug why bottoms aren't being used in outfit creation despite being found.
This will trace through the outfit creation logic step by step.
"""

import asyncio
import os
import sys
import json

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lookbook_mpc.services.smart_recommender import SmartRecommender
from lookbook_mpc.adapters.db_lookbook import MySQLLookbookRepository
from lookbook_mpc.config.settings import get_settings


async def debug_outfit_creation_step_by_step():
    """Debug outfit creation logic step by step."""
    print("=== DEBUGGING OUTFIT CREATION STEP BY STEP ===\n")

    try:
        settings = get_settings()
        repository = MySQLLookbookRepository(settings.get_database_url())
        recommender = SmartRecommender(repository)

        # Test with a simple message
        message = "I need a casual outfit"
        print(f"Testing message: '{message}'")

        # Step 1: Generate keywords
        keywords = await recommender._generate_keywords_from_message(message)
        print(f"\n1. Generated keywords:")
        print(f"   Colors: {keywords.get('colors', [])}")
        print(f"   Styles: {keywords.get('styles', [])}")
        print(f"   Categories: {keywords.get('categories', [])}")

        # Step 2: Search for products
        products = await recommender._search_products_by_keywords(keywords, limit=15)
        print(f"\n2. Initial product search found {len(products)} products:")

        for i, product in enumerate(products):
            category = product.get('category', 'unknown')
            title = product.get('title', 'Unknown')
            score = product.get('relevance_score', 0)
            print(f"   {i+1}. {title} ({category}) - Score: {score}")

        # Step 3: Group products by category
        grouped = recommender._group_products_by_category(products)
        print(f"\n3. Products grouped by category:")
        for category, items in grouped.items():
            if items:
                print(f"   {category}: {len(items)} items")
                for item in items:
                    print(f"     - {item.get('title')} (Score: {item.get('relevance_score', 0)})")

        # Step 4: Check outfit creation logic manually
        print(f"\n4. Testing outfit creation logic:")

        # Check if we have the required categories
        tops = grouped.get('top', [])
        bottoms = grouped.get('bottom', [])
        dresses = grouped.get('dress', [])

        print(f"   Available for outfits:")
        print(f"   - Tops: {len(tops)}")
        print(f"   - Bottoms: {len(bottoms)}")
        print(f"   - Dresses: {len(dresses)}")

        # Test the actual outfit creation
        outfits = await recommender._create_outfit_combinations(products, keywords, limit=3)
        print(f"\n5. Created {len(outfits)} outfits:")

        for i, outfit in enumerate(outfits, 1):
            print(f"\n   Outfit {i}:")
            print(f"     Title: {outfit.get('title')}")
            print(f"     Type: {outfit.get('outfit_type')}")
            print(f"     Items: {len(outfit.get('items', []))}")

            for item in outfit.get('items', []):
                print(f"       - {item.get('title')} ({item.get('category', 'unknown')})")

        # Test color compatibility if we have tops and bottoms
        if tops and bottoms:
            print(f"\n6. Testing color compatibility:")
            for top in tops[:2]:
                for bottom in bottoms[:2]:
                    compatible = recommender._check_color_compatibility(top, bottom)
                    top_color = top.get('color', 'unknown')
                    bottom_color = bottom.get('color', 'unknown')
                    print(f"   {top.get('title')} ({top_color}) + {bottom.get('title')} ({bottom_color}): {'✅' if compatible else '❌'}")

    except Exception as e:
        print(f"Debug failed: {e}")
        import traceback
        traceback.print_exc()


async def debug_why_no_combinations():
    """Debug why top+bottom combinations aren't being created."""
    print(f"\n=== DEBUGGING WHY NO TOP+BOTTOM COMBINATIONS ===\n")

    try:
        settings = get_settings()
        repository = MySQLLookbookRepository(settings.get_database_url())
        recommender = SmartRecommender(repository)

        # Create test data that should work
        test_top = {
            'sku': 'test-top',
            'title': 'Test Top',
            'price': 50.0,
            'category': 'top',
            'color': 'black',
            'relevance_score': 0.8
        }

        test_bottom = {
            'sku': 'test-bottom',
            'title': 'Test Bottom',
            'price': 60.0,
            'category': 'bottom',
            'color': 'black',
            'relevance_score': 0.7
        }

        test_products = [test_top, test_bottom]
        test_keywords = {
            'keywords': ['casual', 'comfortable'],
            'colors': ['black', 'white'],
            'styles': ['casual']
        }

        print("Testing with synthetic data:")
        print(f"  Top: {test_top['title']} ({test_top['color']})")
        print(f"  Bottom: {test_bottom['title']} ({test_bottom['color']})")

        # Test grouping
        grouped = recommender._group_products_by_category(test_products)
        print(f"\nGrouped categories:")
        for cat, items in grouped.items():
            if items:
                print(f"  {cat}: {len(items)} items")

        # Test color compatibility
        compatible = recommender._check_color_compatibility(test_top, test_bottom)
        print(f"\nColor compatibility: {'✅' if compatible else '❌'}")

        # Test outfit creation
        outfits = await recommender._create_outfit_combinations(test_products, test_keywords, limit=3)
        print(f"\nCreated {len(outfits)} outfits:")

        for outfit in outfits:
            items = outfit.get('items', [])
            categories = [item.get('category') for item in items]
            print(f"  - {outfit.get('title')}: {len(items)} items ({', '.join(categories)})")

        if len(outfits) == 0 or all(len(o.get('items', [])) == 1 for o in outfits):
            print("\n❌ PROBLEM: Not creating top+bottom combinations!")
            print("Need to investigate the _create_outfit_combinations logic.")
        else:
            print("\n✅ SUCCESS: Creating proper combinations!")

    except Exception as e:
        print(f"Synthetic test failed: {e}")


async def check_actual_database_products():
    """Check what actual products exist that should work together."""
    print(f"\n=== CHECKING ACTUAL DATABASE PRODUCTS ===\n")

    try:
        settings = get_settings()
        repository = MySQLLookbookRepository(settings.get_database_url())
        conn = await repository._get_connection()
        cursor = await conn.cursor()

        # Find some black tops and bottoms that should match
        await cursor.execute("""
            SELECT p.sku, p.title, p.price, pva.category, pva.color
            FROM products p
            JOIN product_vision_attributes pva ON p.sku = pva.sku
            WHERE p.in_stock = 1
              AND pva.color = 'black'
              AND pva.category IN ('top', 'bottom')
            ORDER BY pva.category, p.price ASC
            LIMIT 6
        """)

        results = await cursor.fetchall()

        if results:
            print("Found matching black items:")
            tops = []
            bottoms = []

            for sku, title, price, category, color in results:
                print(f"  {category}: {title} - ${price}")

                if category == 'top':
                    tops.append({
                        'sku': sku, 'title': title, 'price': float(price),
                        'category': category, 'color': color, 'relevance_score': 0.8
                    })
                elif category == 'bottom':
                    bottoms.append({
                        'sku': sku, 'title': title, 'price': float(price),
                        'category': category, 'color': color, 'relevance_score': 0.8
                    })

            if tops and bottoms:
                print(f"\nTesting combination with real data:")
                print(f"  {len(tops)} tops and {len(bottoms)} bottoms available")

                # Create outfit with real data
                recommender = SmartRecommender(repository)
                real_products = tops + bottoms
                real_keywords = {'colors': ['black'], 'styles': ['casual']}

                outfits = await recommender._create_outfit_combinations(real_products, real_keywords, limit=3)

                print(f"\nReal data created {len(outfits)} outfits:")
                for outfit in outfits:
                    items = outfit.get('items', [])
                    categories = [item.get('category') for item in items]
                    print(f"  - {outfit.get('title')}: {len(items)} items ({', '.join(categories)})")

                    if len(items) > 1 and 'top' in categories and 'bottom' in categories:
                        print("    ✅ SUCCESS: Complete top+bottom outfit!")
                    else:
                        print("    ❌ Still only single items")

        await cursor.close()
        conn.close()

    except Exception as e:
        print(f"Database check failed: {e}")


async def main():
    """Run all outfit creation debugging."""
    print("OUTFIT CREATION DEBUG FOR LOOKBOOK-MPC")
    print("=" * 60)

    await debug_outfit_creation_step_by_step()
    await debug_why_no_combinations()
    await check_actual_database_products()

    print(f"\n" + "=" * 60)
    print("OUTFIT CREATION DEBUG COMPLETE")
    print(f"\nIf this debug shows that products are found but combinations aren't created,")
    print(f"the issue is in the _create_outfit_combinations method logic.")


if __name__ == "__main__":
    asyncio.run(main())
