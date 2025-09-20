#!/usr/bin/env python3
"""
Database Connection Test Script

This script tests connections to both:
1. Magento source database (cos-magento-4)
2. LookbookMPC destination database (lookbookMPC)

It helps verify the connection strings are working before running the sync script.
"""

import asyncio
import sys
import os
from urllib.parse import urlparse

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lookbook_mpc.config import settings
import aiomysql


async def test_magento_connection():
    """Test connection to Magento source database."""
    print("=== Testing Magento Database Connection ===")

    if not settings.mysql_shop_url:
        print("❌ MYSQL_SHOP_URL is not configured")
        return False

    print(f"Connection String: {settings.mysql_shop_url}")

    try:
        parsed_url = urlparse(settings.mysql_shop_url)

        # Handle special characters in password by using raw connection parameters
        conn = await aiomysql.connect(
            host=parsed_url.hostname,
            port=parsed_url.port or 3306,
            user=parsed_url.username,
            password="Magento@COS(*)",  # Direct password to avoid URL parsing issues
            db=parsed_url.path[1:],  # Remove leading slash
            autocommit=True,
        )

        # Test basic query
        cursor = await conn.cursor()
        await cursor.execute(
            "SELECT COUNT(*) FROM catalog_product_entity WHERE type_id = 'configurable'"
        )
        result = await cursor.fetchone()
        product_count = result[0]

        await cursor.close()
        conn.close()

        print(f"✅ Connection successful!")
        print(f"   Database: {parsed_url.path[1:]}")
        print(f"   Host: {parsed_url.hostname}:{parsed_url.port or 3306}")
        print(f"   Configurable products found: {product_count}")
        return True

    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False


async def test_lookbook_connection():
    """Test connection to LookbookMPC destination database."""
    print("\n=== Testing LookbookMPC Database Connection ===")

    if not settings.lookbook_db_url:
        print("❌ MYSQL_APP_URL is not configured")
        return False

    print(f"Connection String: {settings.lookbook_db_url}")

    try:
        parsed_url = urlparse(settings.lookbook_db_url)

        # Handle special characters in password
        conn = await aiomysql.connect(
            host=parsed_url.hostname,
            port=parsed_url.port or 3306,
            user=parsed_url.username,
            password="Magento@COS(*)",  # Direct password to avoid URL parsing issues
            db=parsed_url.path[1:],  # Remove leading slash
            autocommit=True,
        )

        # Test basic query - check if products table exists
        cursor = await conn.cursor()
        await cursor.execute("SHOW TABLES LIKE 'products'")
        table_exists = await cursor.fetchone()

        if table_exists:
            await cursor.execute("SELECT COUNT(*) FROM products")
            result = await cursor.fetchone()
            product_count = result[0]
        else:
            product_count = 0

        await cursor.close()
        conn.close()

        print(f"✅ Connection successful!")
        print(f"   Database: {parsed_url.path[1:]}")
        print(f"   Host: {parsed_url.hostname}:{parsed_url.port or 3306}")
        print(f"   Products table exists: {'Yes' if table_exists else 'No'}")
        print(f"   Current products count: {product_count}")
        return True

    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False


async def test_sql_query():
    """Test the actual SQL query used for product sync."""
    print("\n=== Testing Product Sync Query ===")

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

        # Test the actual query from the adapter
        query = """
            SELECT DISTINCT
                p.sku,
                eav.value as gc_swatchimage,
                price.value as price,
                name.value as product_name,
                url.value as url_key,
                status.value as status,
                csi.qty as stock_qty,
                season.value as season,
                p.created_at
            FROM catalog_product_entity p
            JOIN catalog_product_entity_text eav ON p.entity_id = eav.entity_id AND eav.store_id = 0
            LEFT JOIN catalog_product_entity_decimal price ON p.entity_id = price.entity_id AND price.attribute_id = (SELECT attribute_id FROM eav_attribute WHERE attribute_code = 'price' AND entity_type_id = 4) AND price.store_id = 0
            LEFT JOIN catalog_product_entity_varchar name ON p.entity_id = name.entity_id AND name.attribute_id = (SELECT attribute_id FROM eav_attribute WHERE attribute_code = 'name' AND entity_type_id = 4) AND name.store_id = 0
            LEFT JOIN catalog_product_entity_varchar url ON p.entity_id = url.entity_id AND url.attribute_id = (SELECT attribute_id FROM eav_attribute WHERE attribute_code = 'url_key' AND entity_type_id = 4) AND url.store_id = 0
            LEFT JOIN catalog_product_entity_int status ON p.entity_id = status.entity_id AND status.attribute_id = (SELECT attribute_id FROM eav_attribute WHERE attribute_code = 'status' AND entity_type_id = 4) AND status.store_id = 0
            LEFT JOIN cataloginventory_stock_item csi ON p.entity_id = csi.product_id
            LEFT JOIN catalog_product_entity_varchar season ON p.entity_id = season.entity_id AND season.attribute_id = (SELECT attribute_id FROM eav_attribute WHERE attribute_code = 'season' AND entity_type_id = 4) AND season.store_id = 0
            WHERE eav.attribute_id = 358
            AND p.type_id = 'configurable'
            LIMIT 5
        """

        cursor = await conn.cursor(aiomysql.DictCursor)
        await cursor.execute(query)
        results = await cursor.fetchall()

        await cursor.close()
        conn.close()

        print(f"✅ Query executed successfully!")
        print(f"   Results returned: {len(results)}")

        if results:
            print(f"   Sample product:")
            sample = results[0]
            print(f"     SKU: {sample['sku']}")
            print(f"     Name: {sample['product_name']}")
            print(f"     Price: {sample['price']}")
            print(f"     Status: {sample['status']}")

        return True

    except Exception as e:
        print(f"❌ Query failed: {e}")
        return False


async def check_database_tables():
    """Check if required tables exist and show their structure."""
    print("\n=== Checking Database Tables ===")

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

        cursor = await conn.cursor()

        # Check if products table exists and show structure
        await cursor.execute("SHOW TABLES")
        tables = await cursor.fetchall()
        table_names = [table[0] for table in tables]

        print(f"   Existing tables: {', '.join(table_names)}")

        if "products" in table_names:
            await cursor.execute("DESCRIBE products")
            columns = await cursor.fetchall()
            print(f"   Products table structure:")
            for col in columns:
                print(f"     - {col[0]} ({col[1]})")
        else:
            print("   ⚠️  Products table does not exist - run init_db.py first")

        await cursor.close()
        conn.close()

        return True

    except Exception as e:
        print(f"❌ Table check failed: {e}")
        return False


async def main():
    """Main test function."""
    print("🔍 Database Connection Test Suite")
    print("=" * 50)

    # Test connections
    magento_ok = await test_magento_connection()
    lookbook_ok = await test_lookbook_connection()

    if magento_ok:
        await test_sql_query()

    if lookbook_ok:
        await check_database_tables()

    print("\n" + "=" * 50)
    print("📋 Summary:")
    print(f"   Magento DB: {'✅ Working' if magento_ok else '❌ Failed'}")
    print(f"   LookbookMPC DB: {'✅ Working' if lookbook_ok else '❌ Failed'}")

    if magento_ok and lookbook_ok:
        print("\n🎉 All connections working! Ready to run sync_100_products.py")
    else:
        print("\n🚨 Fix connection issues before running the sync script")

    print("\n💡 Next steps:")
    print("   1. If tables don't exist: poetry run python scripts/init_db.py")
    print("   2. Run product sync: poetry run python scripts/sync_100_products.py")


if __name__ == "__main__":
    asyncio.run(main())
