#!/usr/bin/env python3
"""
Script to sync 100 products from the catalog to the database.
This script will:
1. Sync products from the shop catalog
2. Store them in the lookbook database
3. Prepare them for vision analysis

Usage:
    poetry run python scripts/sync_100_products.py
"""

import asyncio
import sys
import os
import logging
import time
from typing import List, Dict, Any

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lookbook_mpc.adapters.db_shop import MySQLShopCatalogAdapter
from lookbook_mpc.adapters.db_lookbook import MySQLLookbookRepository
from lookbook_mpc.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def sync_products_to_database(limit: int = 100) -> Dict[str, Any]:
    """
    Sync products from shop catalog to database using the optimized method.

    Args:
        limit: Maximum number of products to sync

    Returns:
        Dictionary with sync results
    """
    start_time = time.time()

    try:
        logger.info(f"Starting product sync with limit: {limit}")

        # Check environment variables
        if not settings.mysql_shop_url:
            raise ValueError(
                "MYSQL_SHOP_URL environment variable is not set. "
                "Please configure the connection string for the Magento database."
            )

        if not settings.lookbook_db_url:
            raise ValueError(
                "LOOKBOOK_DB_URL environment variable is not set. "
                "Please configure the connection string for the Lookbook database."
            )

        # Initialize adapters
        shop_adapter = MySQLShopCatalogAdapter(
            connection_string=settings.mysql_shop_url
        )
        lookbook_repo = MySQLLookbookRepository(database_url=settings.lookbook_db_url)

        # Step 1: Fetch enabled products with stock from shop catalog
        fetch_start = time.time()
        logger.info("Fetching enabled products with stock from shop catalog...")
        shop_items = await shop_adapter.get_enabled_products_with_stock(
            start_after_id=0, limit=limit
        )
        fetch_time = time.time() - fetch_start

        if not shop_items:
            logger.warning("No enabled products with stock found in catalog")
            return {
                "status": "no_products",
                "message": "No enabled products with stock found in catalog",
            }

        logger.info(
            f"Found {len(shop_items)} enabled products with stock (fetch time: {fetch_time:.2f}s)"
        )

        # Step 2: Transform products to the required format
        convert_start = time.time()
        logger.info("Transforming products for database storage...")
        products_to_save = []

        for i, item in enumerate(shop_items):
            try:
                # Transform product data (items from get_enabled_products_with_stock are dicts)
                sku = item.get("sku")
                item_dict = {
                    "sku": sku,
                    "title": item.get("title", f"Product {sku or i}"),
                    "price": float(item.get("price", 29.99)),
                    "size_range": item.get("size_range", ["S", "M", "L", "XL"]),
                    "image_key": item.get(
                        "image_key", f"{sku}.jpg" if sku else f"product_{i}.jpg"
                    ),
                    "attributes": item.get("attributes", {}),
                    "in_stock": item.get("in_stock", True),
                    "season": item.get("season"),
                    "url_key": item.get("url_key"),
                    "product_created_at": item.get("product_created_at"),
                    "stock_qty": int(item.get("stock_qty", 0)),
                    "category": item.get("category", "fashion"),
                    "color": item.get("color"),
                    "material": item.get("material"),
                    "pattern": item.get("pattern"),
                    "occasion": item.get("occasion"),
                }

                products_to_save.append(item_dict)

            except Exception as e:
                logger.error(f"Error transforming product {item.get('sku', i)}: {e}")
                continue

        convert_time = time.time() - convert_start

        logger.info(
            f"Transformed {len(products_to_save)} products (conversion time: {convert_time:.2f}s)"
        )

        # Step 3: Save products to database using batch upsert
        save_start = time.time()
        logger.info("Saving products to database...")

        if not products_to_save:
            return {
                "status": "no_valid_products",
                "message": "No valid products to save after transformation",
            }

        # Use the batch upsert method
        results = await lookbook_repo.batch_upsert_products(products_to_save)
        save_time = time.time() - save_start

        total_time = time.time() - start_time
        logger.info(
            f"Sync completed in {total_time:.2f}s (fetch: {fetch_time:.2f}s, transform: {convert_time:.2f}s, save: {save_time:.2f}s)"
        )

        return {
            "status": "success",
            "products_synced": results.get("upserted", 0),
            "products_updated": results.get("updated", 0),
            "total_found": len(shop_items),
            "total_transformed": len(products_to_save),
            "performance": {
                "total_time": total_time,
                "fetch_time": fetch_time,
                "transform_time": convert_time,
                "save_time": save_time,
                "products_per_second": len(products_to_save) / total_time
                if total_time > 0
                else 0,
            },
            "message": f"Successfully synced {results.get('upserted', 0)} new and {results.get('updated', 0)} existing products",
        }

    except Exception as e:
        logger.error(f"Error syncing products: {e}")
        return {
            "status": "error",
            "error": str(e),
            "message": f"Failed to sync products: {str(e)}",
        }


async def main():
    """Main function to sync products."""
    print("=== Product Sync Script ===")
    print(
        "This script will sync 100 enabled, in-stock products from Magento to Lookbook database."
    )
    print()

    try:
        # Sync 100 products
        result = await sync_products_to_database(limit=100)

        print("\n=== Sync Results ===")
        print(f"Status: {result['status']}")
        print(f"Products Found: {result.get('total_found', 0)}")
        print(f"Products Transformed: {result.get('total_transformed', 0)}")
        print(f"New Products: {result.get('products_synced', 0)}")
        print(f"Updated Products: {result.get('products_updated', 0)}")
        print(f"Message: {result.get('message', 'No message')}")

        if "performance" in result:
            perf = result["performance"]
            print(f"\n=== Performance ===")
            print(f"Total Time: {perf.get('total_time', 0):.2f}s")
            print(
                f"Processing Rate: {perf.get('products_per_second', 0):.1f} products/sec"
            )

        if result["status"] == "success":
            print("\n=== Next Steps ===")
            print("1. Run vision analysis on new products")
            print("2. Check the admin dashboard for imported products")
            print("3. Test AI recommendations with the expanded catalog")
            print(
                "4. For larger imports, use: poetry run python scripts/sync_5000_products.py"
            )
        else:
            print(f"\n❌ Sync failed: {result.get('message', 'Unknown error')}")
            return 1

    except Exception as e:
        print(f"\n❌ Error during sync: {e}")
        logger.exception("Sync failed with exception")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
