#!/usr/bin/env python3
"""
Script to sync 100 products from the catalog to the database.
This script will:
1. Sync products from the shop catalog
2. Store them in the lookbook database
3. Prepare them for vision analysis
"""

import asyncio
import sys
import os
import logging
from typing import List, Dict, Any

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lookbook_mpc.adapters.db_shop import MySQLShopCatalogAdapter
from lookbook_mpc.adapters.db_lookbook import SQLiteLookbookRepository
from lookbook_mpc.domain.entities import Item
from lookbook_mpc.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def sync_products_to_database(limit: int = 100) -> Dict[str, Any]:
    """
    Sync products from shop catalog to database with optimized upsert logic.

    Args:
        limit: Maximum number of products to sync

    Returns:
        Dictionary with sync results
    """
    import time
    start_time = time.time()

    try:
        logger.info(f"Starting optimized product sync with limit: {limit}")

        # Initialize adapters
        shop_adapter = MySQLShopCatalogAdapter(connection_string=settings.mysql_shop_url)
        lookbook_repo = SQLiteLookbookRepository(database_url=settings.lookbook_db_url)

        # Step 1: Fetch products from shop catalog
        fetch_start = time.time()
        logger.info("Fetching products from shop catalog...")
        shop_items = await shop_adapter.fetch_items(limit=limit)
        fetch_time = time.time() - fetch_start

        if not shop_items:
            logger.warning("No products found in shop catalog")
            return {"status": "no_products", "message": "No products found in catalog"}

        logger.info(f"Found {len(shop_items)} products in catalog (fetch time: {fetch_time:.2f}s)")

        # Step 2: Optimized conversion to domain entities
        convert_start = time.time()
        logger.info("Converting products to domain entities...")
        products_to_save = []

        # Pre-allocate list for better performance
        products_to_save = [None] * len(shop_items)

        # Process items in batch for better performance
        for i, item in enumerate(shop_items):
            try:
                # Optimized attribute extraction - avoid repeated getattr calls
                if hasattr(item, 'sku'):
                    # Item object - direct access for better performance
                    item_dict = {
                        "sku": item.sku,
                        "title": item.title,
                        "price": item.price,
                        "size_range": getattr(item, 'size_range', []),
                        "image_key": getattr(item, 'image_key', f"{item.sku}.jpg"),
                        "attributes": getattr(item, 'attributes', {}),
                        "in_stock": getattr(item, 'in_stock', True),
                        "season": getattr(item, 'season', None),
                        "url_key": getattr(item, 'url_key', None),
                        "product_created_at": getattr(item, 'product_created_at', None),
                        "stock_qty": getattr(item, 'stock_qty', 0),
                        "category": getattr(item, 'category', None),
                        "color": getattr(item, 'color', None),
                        "material": getattr(item, 'material', None),
                        "pattern": getattr(item, 'pattern', None),
                        "occasion": getattr(item, 'occasion', None)
                    }
                else:
                    # Dict response - optimized attribute extraction
                    sku = item.get('sku')
                    item_dict = {
                        "sku": sku,
                        "title": item.get('title', f"Product {i}"),
                        "price": item.get('price', 29.99),
                        "size_range": item.get('size_range', []),
                        "image_key": item.get('image_key', f"{sku}.jpg" if sku else f"product_{i}.jpg"),
                        "attributes": item.get('attributes', {}),
                        "in_stock": item.get('in_stock', True),
                        # Optimized attribute extraction
                        "season": item.get('season'),
                        "url_key": item.get('url_key'),
                        "product_created_at": item.get('product_created_at'),
                        "stock_qty": item.get('stock_qty', 0),
                        "category": item.get('category'),
                        "color": item.get('color'),
                        "material": item.get('material'),
                        "pattern": item.get('pattern'),
                        "occasion": item.get('occasion')
                    }

                products_to_save[i] = item_dict

            except Exception as e:
                logger.error(f"Error converting product {i} to domain entity: {e}")
                products_to_save[i] = None

        # Filter out None values
        products_to_save = [p for p in products_to_save if p is not None]
        convert_time = time.time() - convert_start

        logger.info(f"Converted {len(products_to_save)} products to domain entities (conversion time: {convert_time:.2f}s)")

        # Step 3: Optimized batch save with intelligent upsert logic
        save_start = time.time()
        logger.info("Saving products to database with optimized upsert logic...")

        # Use the optimized batch upsert method
        results = await lookbook_repo.batch_upsert_products(products_to_save)
        save_time = time.time() - save_start

        total_time = time.time() - start_time
        logger.info(f"Sync completed in {total_time:.2f}s (fetch: {fetch_time:.2f}s, convert: {convert_time:.2f}s, save: {save_time:.2f}s)")

        return {
            "status": "success",
            "products_synced": results.get("upserted", 0),
            "products_updated": results.get("updated", 0),
            "total_found": len(shop_items),
            "skus_processed": results.get("skus", []),
            "performance": {
                "total_time": total_time,
                "fetch_time": fetch_time,
                "conversion_time": convert_time,
                "save_time": save_time,
                "items_per_second": len(products_to_save) / total_time if total_time > 0 else 0
            },
            "message": f"Successfully synced {results.get('upserted', 0)} new and {results.get('updated', 0)} existing products"
        }

    except Exception as e:
        logger.error(f"Error syncing products: {e}")
        return {
            "status": "error",
            "error": str(e),
            "message": f"Failed to sync products: {str(e)}"
        }

async def main():
    """Main function to sync products."""
    print("=== Product Sync Script ===")
    print("This script will sync 100 products from the catalog to the database.")
    print()

    # Sync 100 products
    result = await sync_products_to_database(limit=100)

    print("\n=== Sync Results ===")
    print(f"Status: {result['status']}")
    print(f"Products Synced: {result.get('products_synced', 0)}")
    print(f"Total Found: {result.get('total_found', 0)}")
    print(f"Message: {result.get('message', 'No message')}")

    if result['status'] == 'success' and 'product_ids' in result:
        print(f"First 10 Product IDs: {', '.join(result['product_ids'])}")

    print("\n=== Next Steps ===")
    print("1. Run the batch analysis script to analyze products")
    print("2. Check the database for updated products")
    print("3. Test recommendations with the expanded catalog")

if __name__ == "__main__":
    asyncio.run(main())