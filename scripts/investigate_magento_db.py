#!/usr/bin/env python3
"""
Magento Database Investigation Script

This script investigates the Magento database structure to understand
how to properly extract product data with prices, attributes, etc.
"""

import asyncio
import sys
import os
from urllib.parse import urlparse

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lookbook_mpc.config import settings
import aiomysql


async def investigate_catalog_structure():
    """Investigate the Magento catalog structure."""
    print("🔍 Magento Database Structure Investigation")
    print("=" * 60)

    try:
        parsed_url = urlparse(settings.mysql_shop_url)

        conn = await aiomysql.connect(
            host=parsed_url.hostname,
            port=parsed_url.port or 3306,
            user=parsed_url.username,
            password="Magento@COS(*)",
            db=parsed_url.path[1:],
            autocommit=True,
        )

        cursor = await conn.cursor(aiomysql.DictCursor)

        # 1. Investigate main product table
        print("📋 1. CATALOG_PRODUCT_ENTITY Structure:")
        await cursor.execute("DESCRIBE catalog_product_entity")
        columns = await cursor.fetchall()
        for col in columns:
            print(f"   {col['Field']} ({col['Type']}) - {col['Null']}")

        # 2. Count products by type
        print("\n📊 2. Product Types:")
        await cursor.execute("""
            SELECT type_id, COUNT(*) as count
            FROM catalog_product_entity
            GROUP BY type_id
            ORDER BY count DESC
        """)
        types = await cursor.fetchall()
        for ptype in types:
            print(f"   {ptype['type_id']}: {ptype['count']} products")

        # 3. Investigate EAV attributes
        print("\n🏷️  3. EAV Attributes (key ones):")
        await cursor.execute("""
            SELECT attribute_id, attribute_code, backend_type, frontend_input
            FROM eav_attribute
            WHERE entity_type_id = 4
            AND attribute_code IN ('name', 'price', 'status', 'visibility', 'color', 'material', 'season', 'category_ids', 'image', 'small_image', 'thumbnail')
            ORDER BY attribute_code
        """)
        attributes = await cursor.fetchall()
        for attr in attributes:
            print(
                f"   {attr['attribute_code']} (ID: {attr['attribute_id']}, Type: {attr['backend_type']})"
            )

        # 4. Check what attribute 358 is (from the original query)
        print("\n🔍 4. Mystery Attribute 358:")
        await cursor.execute("""
            SELECT attribute_id, attribute_code, backend_type, frontend_input, frontend_label
            FROM eav_attribute
            WHERE attribute_id = 358
        """)
        attr_358 = await cursor.fetchone()
        if attr_358:
            print(
                f"   Attribute 358: {attr_358['attribute_code']} ({attr_358['frontend_label']})"
            )
        else:
            print("   Attribute 358 not found!")

        # 5. Sample product data with prices
        print("\n💰 5. Sample Products with Price Data:")
        await cursor.execute("""
            SELECT DISTINCT
                p.entity_id,
                p.sku,
                p.type_id,
                name_attr.value as product_name,
                price_attr.value as price
            FROM catalog_product_entity p
            LEFT JOIN catalog_product_entity_varchar name_attr ON p.entity_id = name_attr.entity_id
                AND name_attr.attribute_id = (SELECT attribute_id FROM eav_attribute WHERE attribute_code = 'name' AND entity_type_id = 4)
                AND name_attr.store_id = 0
            LEFT JOIN catalog_product_entity_decimal price_attr ON p.entity_id = price_attr.entity_id
                AND price_attr.attribute_id = (SELECT attribute_id FROM eav_attribute WHERE attribute_code = 'price' AND entity_type_id = 4)
                AND price_attr.store_id = 0
            WHERE p.type_id = 'configurable'
            AND price_attr.value IS NOT NULL
            AND price_attr.value > 0
            LIMIT 10
        """)

        sample_products = await cursor.fetchall()
        if sample_products:
            print("   Products with prices found:")
            for product in sample_products:
                print(
                    f"   {product['sku']}: {product['product_name']} - ${product['price']}"
                )
        else:
            print("   No configurable products with prices found!")

        # 6. Check simple products for prices
        print("\n🔍 6. Simple Products with Prices:")
        await cursor.execute("""
            SELECT DISTINCT
                p.entity_id,
                p.sku,
                p.type_id,
                name_attr.value as product_name,
                price_attr.value as price
            FROM catalog_product_entity p
            LEFT JOIN catalog_product_entity_varchar name_attr ON p.entity_id = name_attr.entity_id
                AND name_attr.attribute_id = (SELECT attribute_id FROM eav_attribute WHERE attribute_code = 'name' AND entity_type_id = 4)
                AND name_attr.store_id = 0
            LEFT JOIN catalog_product_entity_decimal price_attr ON p.entity_id = price_attr.entity_id
                AND price_attr.attribute_id = (SELECT attribute_id FROM eav_attribute WHERE attribute_code = 'price' AND entity_type_id = 4)
                AND price_attr.store_id = 0
            WHERE p.type_id = 'simple'
            AND price_attr.value IS NOT NULL
            AND price_attr.value > 0
            LIMIT 10
        """)

        simple_products = await cursor.fetchall()
        if simple_products:
            print("   Simple products with prices:")
            for product in simple_products:
                print(
                    f"   {product['sku']}: {product['product_name']} - ${product['price']}"
                )
        else:
            print("   No simple products with prices found!")

        # 7. Investigate image storage
        print("\n🖼️  7. Image Storage Investigation:")
        await cursor.execute("""
            SELECT DISTINCT backend_type, COUNT(*) as count
            FROM eav_attribute
            WHERE entity_type_id = 4
            AND attribute_code IN ('image', 'small_image', 'thumbnail', 'swatch_image', 'gc_swatchimage')
            GROUP BY backend_type
        """)
        image_types = await cursor.fetchall()
        for img_type in image_types:
            print(
                f"   Image storage type: {img_type['backend_type']} ({img_type['count']} attributes)"
            )

        # 8. Check what's in catalog_product_entity_text for attribute 358
        print("\n📝 8. Text Attribute 358 Sample Data:")
        await cursor.execute("""
            SELECT p.sku, eav.value
            FROM catalog_product_entity p
            JOIN catalog_product_entity_text eav ON p.entity_id = eav.entity_id
            WHERE eav.attribute_id = 358
            AND eav.store_id = 0
            LIMIT 5
        """)
        text_samples = await cursor.fetchall()
        for sample in text_samples:
            print(f"   {sample['sku']}: {sample['value'][:100]}...")

        # 9. Better price query investigation
        print("\n💡 9. Alternative Price Query:")
        await cursor.execute("""
            SELECT
                p.sku,
                p.type_id,
                MIN(CASE WHEN super_link.parent_id IS NOT NULL THEN parent_price.value ELSE child_price.value END) as final_price
            FROM catalog_product_entity p
            LEFT JOIN catalog_product_super_link super_link ON p.entity_id = super_link.product_id
            LEFT JOIN catalog_product_entity parent ON super_link.parent_id = parent.entity_id
            LEFT JOIN catalog_product_entity_decimal parent_price ON parent.entity_id = parent_price.entity_id
                AND parent_price.attribute_id = (SELECT attribute_id FROM eav_attribute WHERE attribute_code = 'price' AND entity_type_id = 4)
                AND parent_price.store_id = 0
            LEFT JOIN catalog_product_entity_decimal child_price ON p.entity_id = child_price.entity_id
                AND child_price.attribute_id = (SELECT attribute_id FROM eav_attribute WHERE attribute_code = 'price' AND entity_type_id = 4)
                AND child_price.store_id = 0
            WHERE (parent_price.value > 0 OR child_price.value > 0)
            GROUP BY p.sku, p.type_id
            LIMIT 10
        """)
        price_samples = await cursor.fetchall()
        if price_samples:
            print("   Products with calculated prices:")
            for sample in price_samples:
                print(
                    f"   {sample['sku']} ({sample['type_id']}): ${sample['final_price']}"
                )

        # 10. Category investigation
        print("\n📁 10. Category Data:")
        await cursor.execute("""
            SELECT
                p.sku,
                GROUP_CONCAT(cc.name) as categories
            FROM catalog_product_entity p
            JOIN catalog_category_product ccp ON p.entity_id = ccp.product_id
            JOIN catalog_category_entity cc ON ccp.category_id = cc.entity_id
            WHERE p.type_id = 'configurable'
            GROUP BY p.sku
            LIMIT 5
        """)
        category_samples = await cursor.fetchall()
        if category_samples:
            print("   Products with categories:")
            for sample in category_samples:
                print(f"   {sample['sku']}: {sample['categories']}")

        await cursor.close()
        conn.close()

        print("\n✅ Investigation completed!")
        print("\n💡 Key Findings:")
        print("   - Check if configurable products inherit prices from children")
        print("   - Attribute 358 contains image data")
        print("   - Need to join with super_link table for parent-child relationships")
        print("   - Categories are in separate junction table")

    except Exception as e:
        print(f"❌ Investigation failed: {e}")


async def main():
    """Main investigation function."""
    await investigate_catalog_structure()


if __name__ == "__main__":
    asyncio.run(main())
