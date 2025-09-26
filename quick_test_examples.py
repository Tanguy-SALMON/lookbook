#!/usr/bin/env python3
"""
Quick test of a few examples to verify the recommendation fix works.
This tests if we can get complete outfits with both tops and bottoms.
"""

import asyncio
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lookbook_mpc.services.smart_recommender import SmartRecommender
from lookbook_mpc.adapters.db_lookbook import MySQLLookbookRepository
from lookbook_mpc.config.settings import get_settings


async def test_quick_examples():
    """Test a few examples to see if we get complete outfits."""
    print("=== QUICK TEST: COMPLETE OUTFITS ===\n")

    try:
        settings = get_settings()
        repository = MySQLLookbookRepository(settings.get_database_url())
        recommender = SmartRecommender(repository)

        examples = [
            "I go to dance",
            "Business meeting outfit",
            "Casual weekend look"
        ]

        for example in examples:
            print(f"Testing: '{example}'")
            outfits = await recommender.recommend_outfits(example, limit=2)

            if not outfits:
                print("  ❌ No outfits returned")
                continue

            complete_count = 0
            for outfit in outfits:
                items = outfit.get('items', [])
                categories = [item.get('category') for item in items]

                # Check if complete
                has_dress = 'dress' in categories
                has_top = 'top' in categories
                has_bottom = 'bottom' in categories

                is_complete = has_dress or (has_top and has_bottom)

                if is_complete:
                    complete_count += 1
                    status = "✅ COMPLETE"
                else:
                    status = "❌ INCOMPLETE"

                item_desc = ", ".join([f"{item.get('title')} ({item.get('category')})" for item in items])
                print(f"  {status}: {outfit.get('title')} - {item_desc}")

            success_rate = (complete_count / len(outfits)) * 100
            print(f"  Success rate: {complete_count}/{len(outfits)} ({success_rate:.0f}%)\n")

    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()


async def main():
    await test_quick_examples()
    print("Quick test complete!")


if __name__ == "__main__":
    asyncio.run(main())
