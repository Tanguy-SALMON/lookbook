#!/usr/bin/env python3
"""
Debug script to find why bottoms aren't being returned in searches.
This will help identify why only tops are found and fix the bottom matching logic.
"""

import asyncio
import os
import sys
import json

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lookbook_mpc.adapters.db_lookbook import MySQLLookbookRepository
from lookbook_mpc.config.settings import get_settings


async def analyze_bottoms_in_database():
    """Analyze what bottoms exist and their attributes."""
    print("=== ANALYZING BOTTOMS IN DATABASE ===\n")

    try:
        settings = get_settings()
        repository = MySQLLookbookRepository(settings.get_database_url())
        conn = await repository._get_connection()
        cursor = await conn.cursor()

        # Get all bottoms with their attributes
        query = """
            SELECT p.sku, p.title, p.price,
                   pva.color, pva.style, pva.material, pva.occasion
            FROM products p
            JOIN product_vision_attributes pva ON p.sku = pva.sku
            WHERE p.in_stock = 1 AND pva.category = 'bottom'
            ORDER BY p.price ASC
            LIMIT 20
        """

        await cursor.execute(query)
        bottoms = await cursor.fetchall()

        print(f"Found {len(bottoms)} bottoms in database:")
        print(f"{'SKU':<15} {'Title':<40} {'Price':<8} {'Color':<12} {'Style':<15} {'Material'}")
        print("-" * 100)

        for sku, title, price, color, style, material, occasion in bottoms:
            title_short = title[:38] + ".." if len(title) > 40 else title
            print(f"{sku:<15} {title_short:<40} ${price:<7} {color:<12} {style or 'None':<15} {material or 'None'}")

        # Check what attributes bottoms have
        print(f"\n=== BOTTOM ATTRIBUTES ANALYSIS ===")

        # Colors
        await cursor.execute("""
            SELECT pva.color, COUNT(*) as count
            FROM products p
            JOIN product_vision_attributes pva ON p.sku = pva.sku
            WHERE p.in_stock = 1 AND pva.category = 'bottom'
            GROUP BY pva.color
            ORDER BY count DESC
            LIMIT 10
        """)
        colors = await cursor.fetchall()

        print("\nBottom colors:")
        for color, count in colors:
            print(f"  {color}: {count} items")

        # Styles
        await cursor.execute("""
            SELECT pva.style, COUNT(*) as count
            FROM products p
            JOIN product_vision_attributes pva ON p.sku = pva.sku
            WHERE p.in_stock = 1 AND pva.category = 'bottom'
            GROUP BY pva.style
            ORDER BY count DESC
            LIMIT 10
        """)
        styles = await cursor.fetchall()

        print("\nBottom styles:")
        for style, count in styles:
            print(f"  {style or 'NULL'}: {count} items")

        # Materials
        await cursor.execute("""
            SELECT pva.material, COUNT(*) as count
            FROM products p
            JOIN product_vision_attributes pva ON p.sku = pva.sku
            WHERE p.in_stock = 1 AND pva.category = 'bottom'
            GROUP BY pva.material
            ORDER BY count DESC
            LIMIT 10
        """)
        materials = await cursor.fetchall()

        print("\nBottom materials:")
        for material, count in materials:
            print(f"  {material or 'NULL'}: {count} items")

        await cursor.close()
        conn.close()

    except Exception as e:
        print(f"Error analyzing bottoms: {e}")


async def test_bottom_search_keywords():
    """Test if bottoms match common search keywords."""
    print("\n=== TESTING BOTTOM SEARCH KEYWORDS ===\n")

    try:
        settings = get_settings()
        repository = MySQLLookbookRepository(settings.get_database_url())
        conn = await repository._get_connection()
        cursor = await conn.cursor()

        # Test various keyword combinations that should match bottoms
        test_keywords = [
            ("black", "color"),
            ("navy", "color"),
            ("casual", "style"),
            ("party", "occasion"),
            ("dance", "occasion"),
            ("comfortable", "material"),
            ("trousers", "title"),
            ("skirt", "title"),
            ("pants", "title")
        ]

        for keyword, field_type in test_keywords:
            print(f"\nTesting keyword: '{keyword}' ({field_type})")

            if field_type == "color":
                query = """
                    SELECT p.sku, p.title, pva.color, pva.category
                    FROM products p
                    JOIN product_vision_attributes pva ON p.sku = pva.sku
                    WHERE p.in_stock = 1 AND pva.category = 'bottom' AND pva.color = %s
                    LIMIT 5
                """
                params = [keyword]
            elif field_type == "style":
                query = """
                    SELECT p.sku, p.title, pva.style, pva.category
                    FROM products p
                    JOIN product_vision_attributes pva ON p.sku = pva.sku
                    WHERE p.in_stock = 1 AND pva.category = 'bottom' AND pva.style LIKE %s
                    LIMIT 5
                """
                params = [f"%{keyword}%"]
            elif field_type == "occasion":
                query = """
                    SELECT p.sku, p.title, pva.occasion, pva.category
                    FROM products p
                    JOIN product_vision_attributes pva ON p.sku = pva.sku
                    WHERE p.in_stock = 1 AND pva.category = 'bottom' AND pva.occasion LIKE %s
                    LIMIT 5
                """
                params = [f"%{keyword}%"]
            elif field_type == "material":
                query = """
                    SELECT p.sku, p.title, pva.material, pva.category
                    FROM products p
                    JOIN product_vision_attributes pva ON p.sku = pva.sku
                    WHERE p.in_stock = 1 AND pva.category = 'bottom' AND pva.material LIKE %s
                    LIMIT 5
                """
                params = [f"%{keyword}%"]
            elif field_type == "title":
                query = """
                    SELECT p.sku, p.title, pva.category, pva.color
                    FROM products p
                    JOIN product_vision_attributes pva ON p.sku = pva.sku
                    WHERE p.in_stock = 1 AND pva.category = 'bottom' AND p.title LIKE %s
                    LIMIT 5
                """
                params = [f"%{keyword}%"]

            await cursor.execute(query, params)
            results = await cursor.fetchall()

            if results:
                print(f"  Found {len(results)} matching bottoms:")
                for result in results:
                    sku, title, attr, category = result
                    print(f"    {sku}: {title} ({attr})")
            else:
                print(f"  No bottoms found matching '{keyword}'")

        await cursor.close()
        conn.close()

    except Exception as e:
        print(f"Error testing bottom search: {e}")


async def test_dance_party_bottom_search():
    """Test specific search for dance/party bottoms."""
    print("\n=== TESTING DANCE/PARTY BOTTOM SEARCH ===\n")

    try:
        settings = get_settings()
        repository = MySQLLookbookRepository(settings.get_database_url())
        conn = await repository._get_connection()
        cursor = await conn.cursor()

        # Replicate the exact search logic but focus on bottoms
        dance_keywords = ['dance', 'party', 'black', 'navy', 'white', 'trendy', 'chic', 'modern']

        search_terms = []
        params = []

        # Build the same search terms but only for bottoms
        for keyword in dance_keywords[:5]:  # Limit to first 5 keywords
            search_terms.extend([
                "pva.occasion LIKE %s",
                "pva.color = %s",
                "pva.style LIKE %s",
                "pva.material LIKE %s",
                "p.title LIKE %s",
            ])
            params.extend([
                f"%{keyword}%",  # occasion
                keyword,         # color (exact match)
                f"%{keyword}%",  # style
                f"%{keyword}%",  # material
                f"%{keyword}%",  # title
            ])

        search_clause = " OR ".join(search_terms)

        query = """
            SELECT p.sku, p.title, p.price, pva.color, pva.style, pva.material,
                   COUNT(*) as match_count
            FROM products p
            JOIN product_vision_attributes pva ON p.sku = pva.sku
            WHERE p.in_stock = 1 AND pva.category = 'bottom' AND ({})
            GROUP BY p.sku, p.title, p.price, pva.color, pva.style, pva.material
            ORDER BY match_count DESC, p.price ASC
            LIMIT 10
        """.format(search_clause)

        print(f"Search query for bottoms:")
        print(f"Keywords: {dance_keywords[:5]}")
        print(f"Search terms: {len(search_terms)} conditions")

        await cursor.execute(query, params)
        results = await cursor.fetchall()

        print(f"\nFound {len(results)} dance/party bottoms:")

        if results:
            for sku, title, price, color, style, material, match_count in results:
                print(f"  {sku}: {title}")
                print(f"    Price: ${price}, Color: {color}, Style: {style}, Matches: {match_count}")
        else:
            print("  No bottoms found with dance/party keywords!")
            print("  This explains why only tops are returned in recommendations.")

        # Test a simpler bottom search
        print(f"\n=== TESTING SIMPLE BOTTOM SEARCH ===")

        simple_query = """
            SELECT p.sku, p.title, p.price, pva.color, pva.style
            FROM products p
            JOIN product_vision_attributes pva ON p.sku = pva.sku
            WHERE p.in_stock = 1 AND pva.category = 'bottom'
              AND (pva.color IN ('black', 'navy', 'white') OR pva.style LIKE '%casual%')
            ORDER BY p.price ASC
            LIMIT 10
        """

        await cursor.execute(simple_query)
        simple_results = await cursor.fetchall()

        print(f"Simple search found {len(simple_results)} bottoms:")
        for sku, title, price, color, style in simple_results:
            print(f"  {sku}: {title} - {color} - {style} - ${price}")

        await cursor.close()
        conn.close()

    except Exception as e:
        print(f"Error in dance/party bottom search: {e}")


async def suggest_fix():
    """Suggest how to fix the bottom matching issue."""
    print(f"\n=== RECOMMENDED FIX ===\n")

    print("Based on the analysis, the issue is likely:")
    print("1. Bottoms don't match the specific keywords being generated for 'dance/party'")
    print("2. Search is too restrictive - exact color matches vs. LIKE patterns")
    print("3. Bottom attributes (style, occasion) may not align with dance/party terms")
    print()
    print("Solutions:")
    print("1. **Broaden search criteria** - Use more generic terms for bottoms")
    print("2. **Category-specific keywords** - Different keywords for tops vs bottoms")
    print("3. **Fallback search** - If no bottoms found, search with basic criteria")
    print("4. **Improve search balance** - Ensure both tops and bottoms are found")
    print()
    print("Quick fix: Modify search to explicitly look for bottoms with broader criteria")


async def main():
    """Run all bottom search debugging."""
    print("BOTTOM SEARCH DEBUG FOR LOOKBOOK-MPC")
    print("=" * 50)

    await analyze_bottoms_in_database()
    await test_bottom_search_keywords()
    await test_dance_party_bottom_search()
    await suggest_fix()

    print("\n" + "=" * 50)
    print("BOTTOM SEARCH DEBUG COMPLETE")


if __name__ == "__main__":
    asyncio.run(main())
