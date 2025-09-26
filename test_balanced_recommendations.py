#!/usr/bin/env python3
"""
Test script to verify balanced top and bottom recommendations.
This tests the fixed recommendation engine to ensure it returns complete outfits.
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


async def test_recommendation_examples():
    """Test various recommendation scenarios to ensure tops and bottoms are returned."""
    print("=== TESTING BALANCED RECOMMENDATIONS ===\n")

    try:
        settings = get_settings()
        repository = MySQLLookbookRepository(settings.get_database_url())
        recommender = SmartRecommender(repository)

        # Test cases that should return both tops and bottoms
        test_cases = [
            {
                "message": "I go to dance",
                "expected": "Should return tops and bottoms for dancing"
            },
            {
                "message": "I need something for a business meeting",
                "expected": "Should return professional tops and bottoms"
            },
            {
                "message": "Casual weekend outfit under ฿2000",
                "expected": "Should return casual tops and bottoms within budget"
            },
            {
                "message": "I want something comfortable for work",
                "expected": "Should return work-appropriate tops and bottoms"
            },
            {
                "message": "Going out for dinner tonight",
                "expected": "Should return dinner-appropriate tops and bottoms"
            }
        ]

        for i, test_case in enumerate(test_cases, 1):
            print(f"Test {i}: {test_case['message']}")
            print(f"Expected: {test_case['expected']}")

            # Get recommendations
            outfits = await recommender.recommend_outfits(test_case['message'], limit=3)

            print(f"Returned {len(outfits)} outfits:")

            complete_outfits = 0
            total_tops = 0
            total_bottoms = 0
            total_dresses = 0

            for j, outfit in enumerate(outfits, 1):
                print(f"\n  Outfit {j}: {outfit.get('title', 'Untitled')}")
                print(f"    Type: {outfit.get('outfit_type', 'unknown')}")
                print(f"    Items: {len(outfit.get('items', []))}")

                categories_in_outfit = set()
                for item in outfit.get('items', []):
                    category = item.get('category', 'unknown')
                    categories_in_outfit.add(category)
                    print(f"      - {item.get('title', 'Unknown')} ({category})")

                    if category == 'top':
                        total_tops += 1
                    elif category == 'bottom':
                        total_bottoms += 1
                    elif category == 'dress':
                        total_dresses += 1

                # Check if outfit is complete
                has_top = 'top' in categories_in_outfit
                has_bottom = 'bottom' in categories_in_outfit
                has_dress = 'dress' in categories_in_outfit

                if has_dress or (has_top and has_bottom):
                    complete_outfits += 1
                    print(f"      ✅ COMPLETE OUTFIT")
                else:
                    missing = []
                    if not has_dress:
                        if not has_top:
                            missing.append('top')
                        if not has_bottom:
                            missing.append('bottom')
                    print(f"      ❌ INCOMPLETE: Missing {', '.join(missing)}")

                print(f"    Total: ${outfit.get('total_price', 0)}")

            # Summary for this test
            print(f"\n  Summary:")
            print(f"    Complete outfits: {complete_outfits}/{len(outfits)}")
            print(f"    Total items found: {total_tops} tops, {total_bottoms} bottoms, {total_dresses} dresses")

            success_rate = (complete_outfits / len(outfits)) * 100 if outfits else 0
            print(f"    Success rate: {success_rate:.0f}%")

            if success_rate >= 66:  # At least 2/3 should be complete
                print(f"    ✅ PASS")
            else:
                print(f"    ❌ FAIL - Not enough complete outfits")

            print("\n" + "-" * 60)

    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()


async def test_outfit_creation_details():
    """Test the outfit creation logic specifically."""
    print("\n=== TESTING OUTFIT CREATION DETAILS ===\n")

    try:
        settings = get_settings()
        repository = MySQLLookbookRepository(settings.get_database_url())
        recommender = SmartRecommender(repository)

        # Test with a simple request
        message = "I need a casual outfit"
        print(f"Testing: '{message}'")

        # Get keywords
        keywords = await recommender._generate_keywords_from_message(message)
        print(f"\nGenerated keywords: {json.dumps(keywords, indent=2)}")

        # Get products
        products = await recommender._search_products_by_keywords(keywords, limit=15)
        print(f"\nFound {len(products)} products")

        # Group by category
        grouped = recommender._group_products_by_category(products)
        print(f"\nProducts by category:")
        for category, items in grouped.items():
            if items:
                print(f"  {category}: {len(items)} items")
                for item in items[:2]:  # Show first 2
                    print(f"    - {item.get('title')}")

        # Create outfits
        outfits = await recommender._create_outfit_combinations(products, keywords, limit=3)
        print(f"\nCreated {len(outfits)} outfit combinations:")

        for i, outfit in enumerate(outfits, 1):
            print(f"\n  Outfit {i}:")
            print(f"    Title: {outfit.get('title')}")
            print(f"    Type: {outfit.get('outfit_type')}")
            print(f"    Items: {len(outfit.get('items', []))}")

            for item in outfit.get('items', []):
                print(f"      - {item.get('title')} ({item.get('category')})")

    except Exception as e:
        print(f"Detailed test failed: {e}")


async def show_success_examples():
    """Show examples that should now work correctly."""
    print("\n=== SUCCESS EXAMPLES ===\n")

    examples = [
        "I go to dance",
        "Casual weekend outfit",
        "Business meeting attire",
        "Dinner date outfit"
    ]

    try:
        settings = get_settings()
        repository = MySQLLookbookRepository(settings.get_database_url())
        recommender = SmartRecommender(repository)

        for example in examples:
            print(f"Example: '{example}'")
            outfits = await recommender.recommend_outfits(example, limit=2)

            for outfit in outfits:
                items = outfit.get('items', [])
                categories = [item.get('category') for item in items]

                if 'dress' in categories or ('top' in categories and 'bottom' in categories):
                    print(f"  ✅ {outfit.get('title')} - Complete outfit with {len(items)} items")
                else:
                    print(f"  ❌ {outfit.get('title')} - Incomplete ({len(items)} items)")

            print()

    except Exception as e:
        print(f"Examples failed: {e}")


async def main():
    """Run all balanced recommendation tests."""
    print("BALANCED RECOMMENDATION TESTS FOR LOOKBOOK-MPC")
    print("=" * 60)

    await test_recommendation_examples()
    await test_outfit_creation_details()
    await show_success_examples()

    print("\n" + "=" * 60)
    print("TESTS COMPLETE")
    print("\nIf you see ✅ COMPLETE OUTFIT for most results,")
    print("the fix is working and you'll get both tops and bottoms!")


if __name__ == "__main__":
    asyncio.run(main())
