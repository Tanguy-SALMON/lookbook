#!/usr/bin/env python3
"""
Debug script to check JOIN issue between products and product_vision_attributes.
This will help identify why the search query returns 0 results.
"""

import asyncio
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lookbook_mpc.adapters.db_lookbook import MySQLLookbookRepository
from lookbook_mpc.config.settings import get_settings


async def debug_join_issue():
    """Check JOIN compatibility between products and product_vision_attributes."""
    print("=== DEBUGGING JOIN ISSUE ===\n")

    try:
        settings = get_settings()
        repository = MySQLLookbookRepository(settings.get_database_url())
        conn = await repository._get_connection()
        cursor = await conn.cursor()

        # Check SKU formats in both tables
        print("1. Checking SKU formats in products table:")
        await cursor.execute("""
            SELECT sku, title
            FROM products
            WHERE in_stock = 1
            LIMIT 5
        """)
        product_skus = await cursor.fetchall()

        for sku, title in product_skus:
            print(f"   {sku} - {title[:50]}...")

        print("\n2. Checking SKU formats in product_vision_attributes table:")
        await cursor.execute("""
            SELECT sku, category, color
            FROM product_vision_attributes
            LIMIT 5
        """)
        pva_skus = await cursor.fetchall()

        for sku, category, color in pva_skus:
            print(f"   {sku} - {category} - {color}")

        # Check for matching SKUs
        print("\n3. Checking SKU overlap between tables:")
        await cursor.execute("""
            SELECT COUNT(*) as overlap_count
            FROM products p
            INNER JOIN product_vision_attributes pva ON p.sku = pva.sku
            WHERE p.in_stock = 1
        """)
        overlap = await cursor.fetchone()
        print(f"   Products with vision attributes: {overlap[0]}")

        await cursor.execute("SELECT COUNT(*) FROM products WHERE in_stock = 1")
        total_products = await cursor.fetchone()
        print(f"   Total in-stock products: {total_products[0]}")

        await cursor.execute("SELECT COUNT(*) FROM product_vision_attributes")
        total_pva = await cursor.fetchone()
        print(f"   Total vision attributes: {total_pva[0]}")

        # Test the actual search query that's failing
        print("\n4. Testing the failing search query:")

        # Simplified version of the search
        search_terms = [
            "pva.occasion LIKE %s",
            "pva.color = %s",
            "p.title LIKE %s"
        ]
        params = ["%dance%", "black", "%top%"]
        search_clause = " OR ".join(search_terms)

        query = f"""
            SELECT p.sku, p.title, p.price, p.image_key,
                   pva.color, pva.category, pva.occasion, pva.style,
                   pva.material, pva.description,
                   COUNT(*) as match_count
            FROM products p
            JOIN product_vision_attributes pva ON p.sku = pva.sku
            WHERE p.in_stock = 1 AND ({search_clause})
            GROUP BY p.sku, p.title, p.price, p.image_key,
                     pva.color, pva.category, pva.occasion, pva.style,
                     pva.material, pva.description
            ORDER BY match_count DESC, p.price ASC
            LIMIT 10
        """

        print(f"   Query: {query}")
        print(f"   Params: {params}")

        await cursor.execute(query, params)
        results = await cursor.fetchall()

        print(f"   Results: {len(results)} products found")

        for result in results:
            sku, title, price, image_key, color, category, occasion, style, material, desc, match_count = result
            print(f"     {sku}: {title} - {category} - {color} - matches: {match_count}")

        # Try a simpler query without complex search terms
        print("\n5. Testing simpler query:")
        simple_query = """
            SELECT p.sku, p.title, pva.category, pva.color
            FROM products p
            JOIN product_vision_attributes pva ON p.sku = pva.sku
            WHERE p.in_stock = 1
              AND pva.category IN ('top', 'bottom', 'dress')
            LIMIT 10
        """

        await cursor.execute(simple_query)
        simple_results = await cursor.fetchall()

        print(f"   Simple query results: {len(simple_results)} products")
        for sku, title, category, color in simple_results:
            print(f"     {sku}: {title} - {category} - {color}")

        await cursor.close()
        conn.close()

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


async def test_fixed_search():
    """Test a working search approach."""
    print("\n=== TESTING FIXED SEARCH APPROACH ===\n")

    try:
        settings = get_settings()
        repository = MySQLLookbookRepository(settings.get_database_url())
        conn = await repository._get_connection()
        cursor = await conn.cursor()

        # Use LEFT JOIN instead of INNER JOIN to include products without vision attributes
        query = """
            SELECT p.sku, p.title, p.price, p.image_key, p.category as p_category,
                   COALESCE(pva.category, 'unknown') as pva_category,
                   COALESCE(pva.color, 'unknown') as color,
                   COALESCE(pva.style, 'unknown') as style,
                   COALESCE(pva.material, 'unknown') as material,
                   COALESCE(pva.occasion, 'unknown') as occasion
            FROM products p
            LEFT JOIN product_vision_attributes pva ON p.sku = pva.sku
            WHERE p.in_stock = 1
              AND (p.title LIKE %s OR p.title LIKE %s OR pva.occasion LIKE %s)
            LIMIT 15
        """

        await cursor.execute(query, ("%dance%", "%party%", "%party%"))
        results = await cursor.fetchall()

        print(f"Fixed search found {len(results)} products:")

        # Group by category for analysis
        by_category = {}
        for result in results:
            sku, title, price, image_key, p_cat, pva_cat, color, style, material, occasion = result
            category = pva_cat if pva_cat != 'unknown' else p_cat

            if category not in by_category:
                by_category[category] = []
            by_category[category].append({
                'sku': sku,
                'title': title,
                'price': price,
                'color': color
            })

        for category, items in by_category.items():
            print(f"\n{category.upper()} ({len(items)} items):")
            for item in items[:3]:  # Show first 3
                print(f"  - {item['sku']}: {item['title']} - {item['color']} - ${item['price']}")

        await cursor.close()
        conn.close()

    except Exception as e:
        print(f"Fixed search error: {e}")


async def main():
    """Run all debug checks."""
    await debug_join_issue()
    await test_fixed_search()

    print("\n=== SUMMARY ===")
    print("If the JOIN is working but returning 0 results, the issue is likely:")
    print("1. Search terms are too restrictive")
    print("2. No products match the specific keyword combinations")
    print("3. Case sensitivity issues in the search")
    print("\nRecommended fix: Use LEFT JOIN and improve keyword matching logic")


if __name__ == "__main__":
    asyncio.run(main())
