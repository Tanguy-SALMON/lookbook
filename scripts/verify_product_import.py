#!/usr/bin/env python3
"""
Product Import Verification Script

This script verifies that products were imported correctly from the Magento database
and shows sample data to confirm the sync worked properly.
"""

import asyncio
import sys
import os
from urllib.parse import urlparse

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lookbook_mpc.config import settings
import aiomysql


async def verify_product_import():
    """Verify the product import and show sample data."""
    print("🔍 Product Import Verification")
    print("=" * 50)

    try:
        # Connect to the lookbook database
        parsed_url = urlparse(settings.lookbook_db_url)

        conn = await aiomysql.connect(
            host=parsed_url.hostname,
            port=parsed_url.port or 3306,
            user=parsed_url.username,
            password="Magento@COS(*)",
            db=parsed_url.path[1:],
            autocommit=True,
        )

        cursor = await conn.cursor(aiomysql.DictCursor)

        # Get total count
        await cursor.execute("SELECT COUNT(*) as total FROM products")
        result = await cursor.fetchone()
        total_products = result["total"]

        print(f"📊 Total Products Imported: {total_products}")

        # Get count by stock status
        await cursor.execute("""
            SELECT
                in_stock,
                COUNT(*) as count
            FROM products
            GROUP BY in_stock
        """)
        stock_results = await cursor.fetchall()

        print("\n📦 Stock Status:")
        for row in stock_results:
            status = "In Stock" if row["in_stock"] else "Out of Stock"
            print(f"   {status}: {row['count']} products")

        # Get price range
        await cursor.execute("""
            SELECT
                MIN(price) as min_price,
                MAX(price) as max_price,
                AVG(price) as avg_price
            FROM products
            WHERE price > 0
        """)
        price_result = await cursor.fetchone()

        print("\n💰 Price Information:")
        if price_result["min_price"]:
            print(
                f"   Price Range: ${price_result['min_price']:.2f} - ${price_result['max_price']:.2f}"
            )
            print(f"   Average Price: ${price_result['avg_price']:.2f}")
        else:
            print("   No price information available")

        # Get sample products (latest ones first)
        await cursor.execute("""
            SELECT
                sku,
                title,
                price,
                size_range,
                image_key,
                in_stock,
                season,
                url_key,
                stock_qty,
                category,
                color,
                material,
                pattern,
                occasion
            FROM products
            ORDER BY id DESC
            LIMIT 10
        """)
        sample_products = await cursor.fetchall()

        print(f"\n📋 Sample Products (latest 10):")
        print("-" * 50)

        for i, product in enumerate(sample_products, 1):
            print(f"{i}. SKU: {product['sku']}")
            print(f"   Title: {product['title']}")
            print(
                f"   Price: ${product['price']:.2f}"
                if product["price"]
                else "   Price: N/A"
            )
            print(f"   In Stock: {'Yes' if product['in_stock'] else 'No'}")
            print(f"   Season: {product['season'] or 'N/A'}")
            print(f"   Category: {product['category'] or 'N/A'}")
            print(f"   Color: {product['color'] or 'N/A'}")
            print(f"   Material: {product['material'] or 'N/A'}")
            print(f"   Stock Qty: {product['stock_qty'] or 0}")
            print(f"   Image: {product['image_key']}")
            print(f"   URL Key: {product['url_key'] or 'N/A'}")
            print()

        # Get oldest products to compare
        await cursor.execute("""
            SELECT
                sku,
                title,
                price,
                color,
                material,
                season
            FROM products
            ORDER BY id ASC
            LIMIT 5
        """)
        oldest_products = await cursor.fetchall()

        print(f"📋 Oldest Products (for comparison):")
        print("-" * 50)
        for i, product in enumerate(oldest_products, 1):
            print(f"{i}. SKU: {product['sku']}")
            print(f"   Title: {product['title']}")
            print(
                f"   Price: ${product['price']:.2f}"
                if product["price"]
                else "   Price: N/A"
            )
            print(f"   Color: {product['color'] or 'N/A'}")
            print(f"   Material: {product['material'] or 'N/A'}")
            print(f"   Season: {product['season'] or 'N/A'}")
            print()

        # Check for unique attributes
        print("🔍 Attribute Analysis:")

        # Season distribution
        await cursor.execute("""
            SELECT season, COUNT(*) as count
            FROM products
            WHERE season IS NOT NULL
            GROUP BY season
            ORDER BY count DESC
        """)
        seasons = await cursor.fetchall()

        if seasons:
            print("   Seasons:")
            for season in seasons:
                print(f"     {season['season']}: {season['count']} products")
        else:
            print("   No season data found")

        # Color distribution (top 10)
        await cursor.execute("""
            SELECT color, COUNT(*) as count
            FROM products
            WHERE color IS NOT NULL
            GROUP BY color
            ORDER BY count DESC
            LIMIT 10
        """)
        colors = await cursor.fetchall()

        if colors:
            print("   Top Colors:")
            for color in colors:
                print(f"     {color['color']}: {color['count']} products")
        else:
            print("   No color data found")

        # Material distribution (top 10)
        await cursor.execute("""
            SELECT material, COUNT(*) as count
            FROM products
            WHERE material IS NOT NULL
            GROUP BY material
            ORDER BY count DESC
            LIMIT 10
        """)
        materials = await cursor.fetchall()

        if materials:
            print("   Top Materials:")
            for material in materials:
                print(f"     {material['material']}: {material['count']} products")
        else:
            print("   No material data found")

        # Check for products with complete data
        await cursor.execute("""
            SELECT COUNT(*) as complete_products
            FROM products
            WHERE title IS NOT NULL
            AND price > 0
            AND image_key IS NOT NULL
            AND sku IS NOT NULL
        """)
        complete_result = await cursor.fetchone()

        print(f"\n✅ Data Quality:")
        print(
            f"   Complete Products: {complete_result['complete_products']}/{total_products}"
        )
        print(
            f"   Completeness: {(complete_result['complete_products'] / total_products * 100):.1f}%"
        )

        await cursor.close()
        conn.close()

        print("\n🎉 Product import verification completed!")
        print(
            f"✅ Successfully imported {total_products} products from Magento database"
        )

        if total_products >= 100:
            print("\n💡 Next steps:")
            print(
                "   1. Run batch vision analysis: poetry run python scripts/batch_analyze_products.py"
            )
            print("   2. Test API endpoints: poetry run python main.py")
            print(
                "   3. Test recommendations: curl -X POST http://localhost:8000/v1/recommendations"
            )
        else:
            print(f"\n⚠️  Expected 100 products but found {total_products}")
            print("   Consider running sync_100_products.py again")

        return True

    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False


async def check_data_issues():
    """Check for common data issues that might affect recommendations."""
    print("\n🔍 Data Quality Analysis")
    print("-" * 30)

    try:
        parsed_url = urlparse(settings.lookbook_db_url)

        conn = await aiomysql.connect(
            host=parsed_url.hostname,
            port=parsed_url.port or 3306,
            user=parsed_url.username,
            password="Magento@COS(*)",
            db=parsed_url.path[1:],
            autocommit=True,
        )

        cursor = await conn.cursor(aiomysql.DictCursor)

        # Check for missing prices
        await cursor.execute(
            "SELECT COUNT(*) as count FROM products WHERE price IS NULL OR price = 0"
        )
        no_price = await cursor.fetchone()

        # Check for missing titles
        await cursor.execute(
            "SELECT COUNT(*) as count FROM products WHERE title IS NULL OR title = ''"
        )
        no_title = await cursor.fetchone()

        # Check for missing images
        await cursor.execute(
            "SELECT COUNT(*) as count FROM products WHERE image_key IS NULL OR image_key = ''"
        )
        no_image = await cursor.fetchone()

        # Check for missing SKUs
        await cursor.execute(
            "SELECT COUNT(*) as count FROM products WHERE sku IS NULL OR sku = ''"
        )
        no_sku = await cursor.fetchone()

        print("⚠️  Potential Issues:")
        print(f"   Missing/Zero Prices: {no_price['count']} products")
        print(f"   Missing Titles: {no_title['count']} products")
        print(f"   Missing Images: {no_image['count']} products")
        print(f"   Missing SKUs: {no_sku['count']} products")

        # Show products with missing critical data
        if no_price["count"] > 0:
            await cursor.execute("""
                SELECT sku, title
                FROM products
                WHERE price IS NULL OR price = 0
                LIMIT 5
            """)
            no_price_products = await cursor.fetchall()
            print(f"\n   Sample products missing prices:")
            for product in no_price_products:
                print(f"     - {product['sku']}: {product['title'][:50]}...")

        await cursor.close()
        conn.close()

    except Exception as e:
        print(f"❌ Data quality check failed: {e}")


async def main():
    """Main verification function."""
    success = await verify_product_import()

    if success:
        await check_data_issues()


if __name__ == "__main__":
    asyncio.run(main())
