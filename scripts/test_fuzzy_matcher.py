#!/usr/bin/env python3
"""
Test Fuzzy Matcher Service

Test the fuzzy product matcher with various user intents to verify
it can find relevant products and suggest outfit combinations.
"""

import asyncio
import sys
from pathlib import Path
import json

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from lookbook_mpc.services.fuzzy_matcher import FuzzyProductMatcher
from lookbook_mpc.adapters.db_lookbook import MySQLLookbookRepository
from lookbook_mpc.config.settings import settings


async def test_fuzzy_matcher():
    """Test the fuzzy matcher with various intents."""

    print("🧪 TESTING FUZZY PRODUCT MATCHER")
    print("=" * 50)

    # Initialize services
    repo = MySQLLookbookRepository(settings.lookbook_db_url)
    matcher = FuzzyProductMatcher(repo)

    # Test cases based on user conversations
    test_intents = [
        {
            "name": "Dancing",
            "intent": {
                "activity": "dancing",
                "occasion": "party",
                "objectives": ["style", "trendy"],
                "colors": [],
                "budget_max": 5000,
            },
        },
        {
            "name": "Driving/Travel",
            "intent": {
                "activity": "driving",
                "occasion": "travel",
                "objectives": ["comfort", "style"],
                "colors": [],
                "budget_max": 3000,
            },
        },
        {
            "name": "Business Meeting",
            "intent": {
                "activity": None,
                "occasion": "business",
                "objectives": ["professional"],
                "colors": ["black", "navy"],
                "budget_max": 4000,
            },
        },
        {
            "name": "Casual Weekend",
            "intent": {
                "activity": None,
                "occasion": "casual",
                "objectives": ["comfort"],
                "colors": [],
                "budget_max": 2500,
            },
        },
        {
            "name": "Hello (General)",
            "intent": {
                "activity": None,
                "occasion": "casual",
                "objectives": ["style"],
                "colors": [],
                "budget_max": None,
            },
        },
    ]

    for test_case in test_intents:
        print(f"\n🎯 Testing: {test_case['name']}")
        print("-" * 30)
        print(f"Intent: {test_case['intent']}")

        try:
            # Test fuzzy search
            products = await matcher.search_by_intent(test_case["intent"], limit=5)

            print(f"Found {len(products)} relevant products:")

            for i, product in enumerate(products, 1):
                score = product.get("relevance_score", 0)
                corrected_cat = product.get("corrected_category", "unknown")

                print(f"  {i}. {product['title'][:45]}...")
                print(f"     Category: {product['category']} → {corrected_cat}")
                print(f"     Color: {product.get('color', 'N/A')}")
                print(f"     Occasion: {product.get('occasion', 'N/A')}")
                print(f"     Price: ฿{product['price']}")
                print(f"     Score: {score:.1f}/100")
                print()

        except Exception as e:
            print(f"  ❌ Error: {str(e)}")


async def test_outfit_combinations():
    """Test outfit combination creation."""

    print("\n👔 TESTING OUTFIT COMBINATIONS")
    print("=" * 40)

    repo = MySQLLookbookRepository(settings.lookbook_db_url)
    matcher = FuzzyProductMatcher(repo)

    # Test with party/dancing intent
    party_intent = {
        "activity": "dancing",
        "occasion": "party",
        "objectives": ["style"],
        "colors": [],
        "budget_max": 6000,
    }

    try:
        # Get products grouped by category
        outfit_products = await matcher.get_outfit_suitable_products(party_intent)

        print("Available products by category:")
        for category, products in outfit_products.items():
            print(f"  {category.capitalize()}: {len(products)} items")
            for product in products[:2]:  # Show top 2 in each category
                print(f"    • {product['title'][:40]}... (฿{product['price']})")

        # Test outfit creation logic
        print(f"\n🎨 OUTFIT CREATION POSSIBILITIES:")
        print("-" * 35)

        # Strategy 1: Dresses (complete outfits)
        dresses = outfit_products["dress"]
        if dresses:
            print(f"Complete Dress Outfits: {len(dresses)} options")
            for i, dress in enumerate(dresses[:3], 1):
                print(f"  Outfit {i}: {dress['title'][:35]}... (฿{dress['price']})")

        # Strategy 2: Top + Bottom combinations
        tops = outfit_products["top"]
        bottoms = outfit_products["bottom"]

        if tops and bottoms:
            print(f"\nTop + Bottom Combinations:")
            combinations = 0
            for top in tops[:2]:
                for bottom in bottoms[:2]:
                    if matcher.check_color_compatibility(top, bottom):
                        combinations += 1
                        total_price = top["price"] + bottom["price"]
                        print(f"  Combo {combinations}:")
                        print(f"    Top: {top['title'][:30]}... (฿{top['price']})")
                        print(
                            f"    Bottom: {bottom['title'][:30]}... (฿{bottom['price']})"
                        )
                        print(f"    Total: ฿{total_price}")
                        print()

        # Strategy 3: Add outerwear
        outerwear = outfit_products["outerwear"]
        if outerwear:
            print(f"Available Outerwear: {len(outerwear)} options")
            for outer in outerwear[:2]:
                print(f"  • {outer['title'][:35]}... (฿{outer['price']})")

    except Exception as e:
        print(f"❌ Outfit combination test failed: {str(e)}")


async def test_category_correction():
    """Test category classification correction."""

    print("\n🔧 TESTING CATEGORY CORRECTION")
    print("=" * 35)

    repo = MySQLLookbookRepository(settings.lookbook_db_url)
    matcher = FuzzyProductMatcher(repo)

    try:
        # Get all products to see classification issues
        general_intent = {
            "occasion": "casual",
            "objectives": ["style"],
            "budget_max": 10000,
        }

        products = await matcher.search_by_intent(general_intent, limit=15)

        print("Category Correction Analysis:")
        print("Original → Corrected | Product Title")
        print("-" * 60)

        corrections = 0
        for product in products:
            original = product["category"]
            corrected = product.get("corrected_category", original)

            if original != corrected:
                corrections += 1
                marker = "✅ FIXED"
            else:
                marker = "      "

            print(
                f"{original:<10} → {corrected:<10} {marker} | {product['title'][:35]}..."
            )

        print(f"\nTotal corrections applied: {corrections}/{len(products)}")

    except Exception as e:
        print(f"❌ Category correction test failed: {str(e)}")


async def test_scoring_system():
    """Test the relevance scoring system."""

    print("\n📊 TESTING SCORING SYSTEM")
    print("=" * 30)

    repo = MySQLLookbookRepository(settings.lookbook_db_url)
    matcher = FuzzyProductMatcher(repo)

    # Test with very specific intent
    specific_intent = {
        "activity": "dancing",
        "occasion": "party",
        "objectives": ["style", "trendy"],
        "colors": ["black"],
        "budget_max": 3500,
    }

    try:
        products = await matcher.search_by_intent(specific_intent, limit=8)

        print("Products ranked by relevance score:")
        print("Score | Price  | Color | Occasion | Title")
        print("-" * 65)

        for product in products:
            score = product.get("relevance_score", 0)
            color = product.get("color", "N/A")[:8]
            occasion = product.get("occasion", "N/A")[:12]
            title = product["title"][:25]
            price = product["price"]

            print(
                f"{score:5.1f} | ฿{price:<5} | {color:<8} | {occasion:<12} | {title}..."
            )

        if products:
            best = products[0]
            print(f"\n🏆 Best Match: {best['title']}")
            print(f"   Score: {best.get('relevance_score', 0):.1f}/100")
            print(
                f"   Why: {best.get('color', 'N/A')} {best.get('category', 'N/A')} for {best.get('occasion', 'N/A')}"
            )

    except Exception as e:
        print(f"❌ Scoring system test failed: {str(e)}")


if __name__ == "__main__":
    print("🚀 Starting Fuzzy Matcher Tests\n")

    async def run_all_tests():
        await test_fuzzy_matcher()
        await test_outfit_combinations()
        await test_category_correction()
        await test_scoring_system()

        print("\n" + "=" * 50)
        print("✅ ALL TESTS COMPLETED")
        print("=" * 50)
        print("\n💡 Next Steps:")
        print("1. Integrate fuzzy matcher into recommendation engine")
        print("2. Connect to chat system for real product suggestions")
        print("3. Add MCP server tools for external access")

    asyncio.run(run_all_tests())
