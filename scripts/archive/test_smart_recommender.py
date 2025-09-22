#!/usr/bin/env python3
"""
Test Smart Recommender Service

Test the LLM-powered smart recommender that uses keyword generation
to find and rank products for outfit recommendations.
"""

import asyncio
import sys
from pathlib import Path
import json

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from lookbook_mpc.services.smart_recommender import SmartRecommender
from lookbook_mpc.adapters.db_lookbook import MySQLLookbookRepository
from lookbook_mpc.config.settings import settings


async def test_keyword_generation():
    """Test LLM keyword generation from user messages."""

    print("🧠 TESTING LLM KEYWORD GENERATION")
    print("=" * 45)

    repo = MySQLLookbookRepository(settings.lookbook_db_url)
    recommender = SmartRecommender(repo)

    test_messages = [
        "I go to dance",
        "I like drive",
        "Hello",
        "I need something for work meeting",
        "What about casual wear for weekend?",
        "I want to look good for a date",
    ]

    for message in test_messages:
        print(f"\n💬 Message: '{message}'")
        print("-" * 30)

        try:
            keywords = await recommender._generate_keywords_from_message(message)

            print(f"Keywords: {', '.join(keywords.get('keywords', [])[:5])}")
            print(f"Colors: {', '.join(keywords.get('colors', []))}")
            print(f"Occasions: {', '.join(keywords.get('occasions', []))}")
            print(f"Styles: {', '.join(keywords.get('styles', []))}")
            print(f"Categories: {', '.join(keywords.get('categories', []))}")
            print(f"Mood: {keywords.get('mood', 'N/A')}")
            print(f"Explanation: {keywords.get('explanation', 'N/A')[:80]}...")

        except Exception as e:
            print(f"❌ Error: {str(e)}")


async def test_product_search():
    """Test product search using generated keywords."""

    print("\n\n🔍 TESTING PRODUCT SEARCH BY KEYWORDS")
    print("=" * 45)

    repo = MySQLLookbookRepository(settings.lookbook_db_url)
    recommender = SmartRecommender(repo)

    # Test with dance keywords
    test_keywords = {
        "keywords": ["party", "dance", "stylish", "trendy"],
        "colors": ["black", "navy"],
        "occasions": ["party", "festival"],
        "styles": ["trendy", "chic"],
        "categories": ["dress", "top"],
        "materials": ["comfortable"],
        "mood": "confident and ready to dance",
    }

    print("Test Keywords:", test_keywords)
    print("\nSearching products...")

    try:
        products = await recommender._search_products_by_keywords(test_keywords, 8)

        print(f"Found {len(products)} products:")
        print("Score | Price  | Color | Category | Title")
        print("-" * 70)

        for product in products:
            score = product.get("relevance_score", 0)
            price = product["price"]
            color = product.get("color", "N/A")[:8]
            category = product.get("category", "N/A")[:10]
            title = product["title"][:30]
            matches = product.get("match_count", 0)

            print(
                f"{score:5.1f} | ฿{price:<5} | {color:<8} | {category:<10} | {title}... ({matches} matches)"
            )

    except Exception as e:
        print(f"❌ Product search failed: {str(e)}")


async def test_outfit_creation():
    """Test complete outfit recommendation process."""

    print("\n\n👔 TESTING COMPLETE OUTFIT RECOMMENDATIONS")
    print("=" * 50)

    repo = MySQLLookbookRepository(settings.lookbook_db_url)
    recommender = SmartRecommender(repo)

    test_messages = [
        "I go to dance",
        "I need something for business meeting",
        "Casual outfit for weekend",
    ]

    for message in test_messages:
        print(f"\n💬 Request: '{message}'")
        print("-" * 40)

        try:
            outfits = await recommender.recommend_outfits(message, limit=3)

            print(f"Generated {len(outfits)} outfit recommendations:")

            for i, outfit in enumerate(outfits, 1):
                print(f"\n  {i}. {outfit['title']} (฿{outfit['total_price']:.0f})")
                print(f"     Type: {outfit['outfit_type']}")
                print(f"     Items: {len(outfit['items'])} piece(s)")

                for item in outfit["items"]:
                    print(f"       • {item['title'][:35]}... (฿{item['price']:.0f})")
                    print(
                        f"         Color: {item['color']}, Category: {item['category']}"
                    )
                    print(f"         Score: {item['relevance_score']:.1f}")

                print(f"     Why: {outfit['style_explanation'][:80]}...")

        except Exception as e:
            print(f"❌ Outfit creation failed: {str(e)}")


async def test_color_compatibility():
    """Test color compatibility logic."""

    print("\n\n🎨 TESTING COLOR COMPATIBILITY")
    print("=" * 35)

    repo = MySQLLookbookRepository(settings.lookbook_db_url)
    recommender = SmartRecommender(repo)

    # Test color combinations
    test_combinations = [
        ({"color": "black"}, {"color": "white"}),
        ({"color": "navy"}, {"color": "beige"}),
        ({"color": "red"}, {"color": "green"}),
        ({"color": "black"}, {"color": "black"}),
        ({"color": "grey"}, {"color": "white"}),
    ]

    print("Color Compatibility Tests:")
    print("Color 1    | Color 2    | Compatible?")
    print("-" * 40)

    for item1, item2 in test_combinations:
        color1 = item1["color"]
        color2 = item2["color"]
        compatible = recommender._check_color_compatibility(item1, item2)
        status = "✅ Yes" if compatible else "❌ No"

        print(f"{color1:<10} | {color2:<10} | {status}")


async def test_category_correction():
    """Test category correction logic."""

    print("\n\n🔧 TESTING CATEGORY CORRECTION")
    print("=" * 35)

    repo = MySQLLookbookRepository(settings.lookbook_db_url)
    recommender = SmartRecommender(repo)

    # Get some real products to test
    try:
        keywords = {
            "keywords": ["casual"],
            "colors": [],
            "occasions": ["casual"],
            "styles": [],
            "categories": [],
            "materials": [],
        }
        products = await recommender._search_products_by_keywords(keywords, 10)

        if products:
            grouped = recommender._group_products_by_category(products)

            print("Products grouped by corrected category:")
            for category, items in grouped.items():
                if items:
                    print(f"\n{category.upper()}S ({len(items)} items):")
                    for item in items[:3]:
                        original_cat = item.get("category", "unknown")
                        print(f"  • {item['title'][:40]}...")
                        if category != original_cat:
                            print(
                                f"    [Corrected from '{original_cat}' to '{category}']"
                            )

    except Exception as e:
        print(f"❌ Category correction test failed: {str(e)}")


async def test_scoring_system():
    """Test relevance scoring system."""

    print("\n\n📊 TESTING RELEVANCE SCORING")
    print("=" * 35)

    repo = MySQLLookbookRepository(settings.lookbook_db_url)
    recommender = SmartRecommender(repo)

    # Create test product and keywords
    test_product = {
        "title": "BLACK PARTY DRESS",
        "color": "black",
        "occasion": "party",
        "style": "trendy",
        "material": "polyester",
        "category": "dress",
        "match_count": 5,
    }

    test_keywords = {
        "keywords": ["party", "dance", "stylish"],
        "colors": ["black"],
        "occasions": ["party", "festival"],
        "styles": ["trendy", "chic"],
        "categories": ["dress"],
        "materials": ["comfortable"],
    }

    score = recommender._calculate_keyword_score(test_product, test_keywords)

    print(f"Test Product: {test_product['title']}")
    print(f"Keywords: {test_keywords}")
    print(f"Calculated Score: {score}/100")
    print("\nScore Breakdown:")
    print("- Color match (black): +25 points")
    print("- Occasion match (party): +20 points")
    print("- Category match (dress): +20 points")
    print("- Style match (trendy): +15 points")
    print("- Database matches: +10 points")


if __name__ == "__main__":
    print("🚀 Starting Smart Recommender Tests\n")

    async def run_all_tests():
        await test_keyword_generation()
        await test_product_search()
        await test_outfit_creation()
        await test_color_compatibility()
        await test_category_correction()
        await test_scoring_system()

        print("\n" + "=" * 50)
        print("✅ ALL SMART RECOMMENDER TESTS COMPLETED")
        print("=" * 50)
        print("\n💡 Next Steps:")
        print("1. Integrate smart recommender into chat system")
        print("2. Add MCP server endpoints")
        print("3. Generate product links and images")
        print("4. Test with real user conversations")

    asyncio.run(run_all_tests())
