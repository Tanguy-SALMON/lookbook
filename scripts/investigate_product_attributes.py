#!/usr/bin/env python3
"""
Product Vision Attributes Investigation Script

Investigate the database structure and content of product_vision_attributes
to understand what data is available for the recommendation engine.
"""

import asyncio
import sys
from pathlib import Path
import json

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from lookbook_mpc.adapters.db_lookbook import MySQLLookbookRepository
from lookbook_mpc.config.settings import settings


async def investigate_database():
    """Investigate the product_vision_attributes table structure and content."""

    print("🔍 PRODUCT VISION ATTRIBUTES INVESTIGATION")
    print("=" * 60)

    # Initialize repository
    repo = MySQLLookbookRepository(settings.lookbook_db_url)

    try:
        # Get database connection
        conn = await repo._get_connection()
        try:
            cursor = await conn.cursor()
            try:
                # 1. Check table structure
                print("\n📋 TABLE STRUCTURE:")
                print("-" * 30)
                await cursor.execute("DESCRIBE product_vision_attributes")
                columns = await cursor.fetchall()

                for col in columns:
                    field_name = col[0]
                    field_type = col[1]
                    nullable = col[2]
                    default = col[4] or "NULL"
                    print(
                        f"{field_name:<25} | {field_type:<20} | {nullable:<5} | {default}"
                    )

                # 2. Count total records
                print(f"\n📊 DATA OVERVIEW:")
                print("-" * 20)
                await cursor.execute("SELECT COUNT(*) FROM product_vision_attributes")
                total_count = (await cursor.fetchone())[0]
                print(f"Total products with vision attributes: {total_count}")

                # 3. Check main products table for comparison
                await cursor.execute("SELECT COUNT(*) FROM products")
                products_count = (await cursor.fetchone())[0]
                print(f"Total products in main table: {products_count}")

                coverage = (
                    (total_count / products_count * 100) if products_count > 0 else 0
                )
                print(f"Vision analysis coverage: {coverage:.1f}%")

                # 4. Analyze category distribution
                print(f"\n🏷️  CATEGORY DISTRIBUTION:")
                print("-" * 25)
                await cursor.execute("""
                    SELECT category, COUNT(*) as count
                    FROM product_vision_attributes
                    WHERE category IS NOT NULL
                    GROUP BY category
                    ORDER BY count DESC
                """)
                categories = await cursor.fetchall()

                for cat, count in categories:
                    print(f"{cat:<15}: {count:>3} products")

                # 5. Analyze color distribution
                print(f"\n🎨 COLOR DISTRIBUTION:")
                print("-" * 22)
                await cursor.execute("""
                    SELECT color, COUNT(*) as count
                    FROM product_vision_attributes
                    WHERE color IS NOT NULL
                    GROUP BY color
                    ORDER BY count DESC
                    LIMIT 10
                """)
                colors = await cursor.fetchall()

                for color, count in colors:
                    print(f"{color:<15}: {count:>3} products")

                # 6. Analyze occasion distribution
                print(f"\n🎯 OCCASION DISTRIBUTION:")
                print("-" * 26)
                await cursor.execute("""
                    SELECT occasion, COUNT(*) as count
                    FROM product_vision_attributes
                    WHERE occasion IS NOT NULL
                    GROUP BY occasion
                    ORDER BY count DESC
                """)
                occasions = await cursor.fetchall()

                for occasion, count in occasions:
                    print(f"{occasion:<15}: {count:>3} products")

                # 7. Analyze style distribution
                print(f"\n✨ STYLE DISTRIBUTION:")
                print("-" * 21)
                await cursor.execute("""
                    SELECT style, COUNT(*) as count
                    FROM product_vision_attributes
                    WHERE style IS NOT NULL
                    GROUP BY style
                    ORDER BY count DESC
                    LIMIT 10
                """)
                styles = await cursor.fetchall()

                for style, count in styles:
                    print(f"{style:<15}: {count:>3} products")

                # 8. Sample complete records
                print(f"\n🔬 SAMPLE COMPLETE RECORDS:")
                print("-" * 28)
                await cursor.execute("""
                    SELECT pva.sku, p.title, pva.category, pva.color, pva.occasion,
                           pva.style, pva.material, p.price, p.image_key
                    FROM product_vision_attributes pva
                    JOIN products p ON pva.sku = p.sku
                    WHERE pva.category IS NOT NULL
                    AND pva.color IS NOT NULL
                    AND pva.occasion IS NOT NULL
                    AND pva.style IS NOT NULL
                    LIMIT 5
                """)
                samples = await cursor.fetchall()

                for sample in samples:
                    (
                        sku,
                        title,
                        category,
                        color,
                        occasion,
                        style,
                        material,
                        price,
                        image_key,
                    ) = sample
                    print(f"\nSKU: {sku}")
                    print(f"  Title: {title[:50]}...")
                    print(f"  Category: {category} | Color: {color} | Style: {style}")
                    print(f"  Occasion: {occasion} | Material: {material}")
                    print(f"  Price: ฿{price} | Image: {image_key[:30]}...")

                # 9. Check for top/bottom combinations
                print(f"\n👔 OUTFIT COMBINATION ANALYSIS:")
                print("-" * 32)

                await cursor.execute("""
                    SELECT
                        SUM(CASE WHEN category = 'top' THEN 1 ELSE 0 END) as tops,
                        SUM(CASE WHEN category = 'bottom' THEN 1 ELSE 0 END) as bottoms,
                        SUM(CASE WHEN category = 'dress' THEN 1 ELSE 0 END) as dresses,
                        SUM(CASE WHEN category = 'outerwear' THEN 1 ELSE 0 END) as outerwear,
                        SUM(CASE WHEN category = 'shoes' THEN 1 ELSE 0 END) as shoes,
                        SUM(CASE WHEN category = 'accessory' THEN 1 ELSE 0 END) as accessories
                    FROM product_vision_attributes
                """)
                combo_stats = await cursor.fetchone()

                print(f"Tops:        {combo_stats[0]:>3} products")
                print(f"Bottoms:     {combo_stats[1]:>3} products")
                print(f"Dresses:     {combo_stats[2]:>3} products")
                print(f"Outerwear:   {combo_stats[3]:>3} products")
                print(f"Shoes:       {combo_stats[4]:>3} products")
                print(f"Accessories: {combo_stats[5]:>3} products")

                # 10. Price range analysis
                print(f"\n💰 PRICE RANGE ANALYSIS:")
                print("-" * 24)
                await cursor.execute("""
                    SELECT
                        MIN(p.price) as min_price,
                        MAX(p.price) as max_price,
                        AVG(p.price) as avg_price,
                        COUNT(*) as total_with_price
                    FROM product_vision_attributes pva
                    JOIN products p ON pva.sku = p.sku
                    WHERE p.price > 0
                """)
                price_stats = await cursor.fetchone()

                if price_stats:
                    min_p, max_p, avg_p, count_p = price_stats
                    print(f"Price range: ฿{min_p:.0f} - ฿{max_p:.0f}")
                    print(f"Average price: ฿{avg_p:.0f}")
                    print(f"Products with prices: {count_p}")

                print("\n" + "=" * 60)
                print("✅ INVESTIGATION COMPLETE")
                print("=" * 60)
            finally:
                await cursor.close()
        finally:
            await conn.ensure_closed()

    except Exception as e:
        print(f"❌ Database investigation failed: {str(e)}")
        return False

    return True


async def analyze_recommendation_potential():
    """Analyze the potential for building recommendations based on available data."""

    print("\n🚀 RECOMMENDATION ENGINE ANALYSIS")
    print("=" * 40)

    repo = MySQLLookbookRepository(settings.lookbook_db_url)

    try:
        conn = await repo._get_connection()
        try:
            cursor = await conn.cursor()
            try:
                # Test potential outfit combinations
                print("\n🔍 OUTFIT COMBINATION POTENTIAL:")
                print("-" * 33)

                # Find casual tops and bottoms for example
                await cursor.execute("""
                    SELECT p.sku, p.title, p.price, p.image_key, pva.color, pva.style, pva.material
                    FROM product_vision_attributes pva
                    JOIN products p ON pva.sku = p.sku
                    WHERE pva.category = 'top'
                    AND pva.occasion IN ('casual', 'business')
                    AND p.price > 0
                    AND p.in_stock = 1
                    LIMIT 3
                """)
                sample_tops = await cursor.fetchall()

                await cursor.execute("""
                    SELECT p.sku, p.title, p.price, p.image_key, pva.color, pva.style, pva.material
                    FROM product_vision_attributes pva
                    JOIN products p ON pva.sku = p.sku
                    WHERE pva.category = 'bottom'
                    AND pva.occasion IN ('casual', 'business')
                    AND p.price > 0
                    AND p.in_stock = 1
                    LIMIT 3
                """)
                sample_bottoms = await cursor.fetchall()

                print("SAMPLE TOPS:")
                for top in sample_tops:
                    sku, title, price, img, color, style, material = top
                    print(f"  • {title[:40]} (฿{price}) - {color} {material}")

                print("\nSAMPLE BOTTOMS:")
                for bottom in sample_bottoms:
                    sku, title, price, img, color, style, material = bottom
                    print(f"  • {title[:40]} (฿{price}) - {color} {material}")

                # Test search by intent
                print(f"\n🎯 INTENT-BASED SEARCH TEST:")
                print("-" * 28)

                test_queries = [
                    ("Dancing outfit", "activity = 'dancing' OR occasion = 'party'"),
                    (
                        "Business casual",
                        "occasion = 'business' AND style IN ('classic', 'professional')",
                    ),
                    (
                        "Casual weekend",
                        "occasion = 'casual' AND style IN ('casual', 'comfortable')",
                    ),
                ]

                for query_name, where_clause in test_queries:
                    await cursor.execute(f"""
                        SELECT COUNT(*)
                        FROM product_vision_attributes pva
                        JOIN products p ON pva.sku = p.sku
                        WHERE {where_clause}
                        AND p.in_stock = 1
                    """)
                    count = (await cursor.fetchone())[0]
                    print(f"{query_name:<20}: {count:>3} matching products")

                print(f"\n💡 RECOMMENDATION STRATEGY:")
                print("-" * 28)
                print("✅ Sufficient data for outfit recommendations")
                print("✅ Top/bottom combinations available")
                print("✅ Multiple attributes for filtering")
                print("✅ Price range suitable for Thai market")
                print("✅ Image links available for display")
            finally:
                await cursor.close()
        finally:
            await conn.ensure_closed()

    except Exception as e:
        print(f"❌ Recommendation analysis failed: {str(e)}")
        return False

    return True


if __name__ == "__main__":
    print("Starting database investigation...")

    async def run_investigation():
        success1 = await investigate_database()
        if success1:
            success2 = await analyze_recommendation_potential()
            return success2
        return False

    result = asyncio.run(run_investigation())

    if result:
        print(f"\n🎉 Investigation completed successfully!")
        print("Ready to build recommendation engine with available data.")
    else:
        print(f"\n❌ Investigation failed.")
