#!/usr/bin/env python3
"""
Database Schema Cleanup Script

This script removes the redundant 'attributes' JSON column from the products table
since we already have the data flattened in individual columns.
"""

import asyncio
import sys
import os
from urllib.parse import urlparse

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lookbook_mpc.config import settings
import aiomysql


async def cleanup_database_schema():
    """Remove the redundant attributes column from products table."""
    print("🔧 Database Schema Cleanup")
    print("=" * 40)

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

        # Check if attributes column exists
        await cursor.execute("DESCRIBE products")
        columns = await cursor.fetchall()
        column_names = [col[0] for col in columns]

        if "attributes" in column_names:
            print("📋 Current table structure:")
            for col in columns:
                marker = " ❌" if col[0] == "attributes" else ""
                print(f"   {col[0]} ({col[1]}){marker}")

            print("\n🗑️  Removing redundant 'attributes' column...")

            # Remove the attributes column
            await cursor.execute("ALTER TABLE products DROP COLUMN attributes")

            print("✅ Successfully removed 'attributes' column")

            # Show updated structure
            print("\n📋 Updated table structure:")
            await cursor.execute("DESCRIBE products")
            updated_columns = await cursor.fetchall()
            for col in updated_columns:
                print(f"   {col[0]} ({col[1]})")

        else:
            print("ℹ️  'attributes' column not found - already cleaned up!")

        # Show sample data to verify
        await cursor.execute(
            "SELECT sku, title, price, color, material, season FROM products LIMIT 3"
        )
        samples = await cursor.fetchall()

        if samples:
            print(f"\n📋 Sample data verification:")
            for sample in samples:
                print(f"   SKU: {sample[0]}")
                print(f"   Title: {sample[1]}")
                print(f"   Price: ฿{sample[2]:.2f}" if sample[2] else "   Price: N/A")
                print(f"   Color: {sample[3] or 'N/A'}")
                print(f"   Material: {sample[4] or 'N/A'}")
                print(f"   Season: {sample[5] or 'N/A'}")
                print()

        await cursor.close()
        conn.close()

        print("🎉 Database schema cleanup completed!")
        print("\n💡 Benefits:")
        print("   ✅ Removed redundant JSON storage")
        print("   ✅ Simplified data structure")
        print("   ✅ Better query performance")
        print("   ✅ Easier data maintenance")

        return True

    except Exception as e:
        print(f"❌ Schema cleanup failed: {e}")
        return False


async def main():
    """Main cleanup function."""
    success = await cleanup_database_schema()

    if success:
        print("\n💡 Next steps:")
        print("   1. Update the sync script to not include attributes field")
        print("   2. Re-run product sync if needed")
        print("   3. Test the API with the cleaned schema")


if __name__ == "__main__":
    asyncio.run(main())
