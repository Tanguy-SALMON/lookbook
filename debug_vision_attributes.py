#!/usr/bin/env python3
"""
Debug script to check product_vision_attributes table structure and data.
This will help identify why categorization is failing.
"""

import asyncio
import os
import sys
import json

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lookbook_mpc.adapters.db_lookbook import MySQLLookbookRepository
from lookbook_mpc.config.settings import get_settings


async def debug_vision_attributes_table():
    """Check if product_vision_attributes table exists and has data."""
    print("=== DEBUGGING PRODUCT VISION ATTRIBUTES TABLE ===\n")

    try:
        settings = get_settings()
        repository = MySQLLookbookRepository(settings.get_database_url())
        conn = await repository._get_connection()
        cursor = await conn.cursor()

        # Check if table exists
        await cursor.execute("SHOW TABLES LIKE 'product_vision_attributes'")
        table_exists = await cursor.fetchone()

        if not table_exists:
            print("❌ product_vision_attributes table does NOT exist")
            print("\nThis explains why the search query fails!")
            print("The recommendation engine is trying to join with a non-existent table.")
            return

        print("✅ product_vision_attributes table exists")

        # Check table structure
        await cursor.execute("DESCRIBE product_vision_attributes")
        columns = await cursor.fetchall()

        print("\nTable Structure:")
        for column in columns:
            print(f"  {column[0]} - {column[1]} - {column[2]} - {column[3]} - {column[4]}")

        # Check if table has data
        await cursor.execute("SELECT COUNT(*) FROM product_vision_attributes")
        count = await cursor.fetchone()
        print(f"\nTotal records: {count[0]}")

        if count[0] > 0:
            # Get sample data
            await cursor.execute("""
                SELECT sku, category, color, style, material, occasion
                FROM product_vision_attributes
                LIMIT 10
            """)
            samples = await cursor.fetchall()

            print("\nSample data:")
            for sku, category, color, style, material, occasion in samples:
                print(f"  {sku}: cat={category}, color={color}, style={style}")

            # Check category distribution
            await cursor.execute("""
                SELECT category, COUNT(*) as count
                FROM product_vision_attributes
                GROUP BY category
                ORDER BY count DESC
            """)
            categories = await cursor.fetchall()

            print("\nCategory distribution in vision attributes:")
            for category, count in categories:
                print(f"  {category or 'NULL'}: {count} products")

        await cursor.close()
        conn.close()

    except Exception as e:
        print(f"Error: {e}")


async def debug_product_search_fallback():
    """Test fallback search without vision attributes."""
    print("\n=== DEBUGGING FALLBACK SEARCH ===\n")

    try:
        settings = get_settings()
        repository = MySQLLookbookRepository(settings.get_database_url())
        conn = await repository._get_connection()
        cursor = await conn.cursor()

        # Simple search in products table only
        query = """
        SELECT sku, title, price, image_key, category, color, material
        FROM products
        WHERE in_stock = 1
          AND (title LIKE %s OR title LIKE %s OR title LIKE %s)
        LIMIT 15
        """

        # Search for dance-related items
        await cursor.execute(query, ('%dance%', '%party%', '%top%'))
        results = await cursor.fetchall()

        print(f"Found {len(results)} products with fallback search:")

        for sku, title, price, image_key, category, color, material in results:
            print(f"  {sku}: {title}")
            print(f"    Category: {category}, Color: {color}, Price: ${price}")

        await cursor.close()
        conn.close()

    except Exception as e:
        print(f"Fallback search error: {e}")


async def check_recommended_solution():
    """Show the recommended fix."""
    print("\n=== RECOMMENDED SOLUTION ===\n")

    print("The issue is that the recommendation engine expects:")
    print("1. product_vision_attributes table with proper categories")
    print("2. Categories like 'top', 'bottom', 'dress' instead of 'fashion'")
    print()
    print("Possible solutions:")
    print("1. Create and populate product_vision_attributes table")
    print("2. Update search logic to use products.category with better detection")
    print("3. Improve category classification in _group_products_by_category")
    print()
    print("Quick fix: Modify search to work without vision attributes table")


async def main():
    """Run all debug checks."""
    await debug_vision_attributes_table()
    await debug_product_search_fallback()
    await check_recommended_solution()


if __name__ == "__main__":
    asyncio.run(main())
