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
    Sync products from shop catalog to database with efficient upsert logic.

    Args:
        limit: Maximum number of products to sync

    Returns:
        Dictionary with sync results
    """
    try:
        logger.info(f"Starting product sync with limit: {limit}")

        # Initialize adapters
        shop_adapter = MySQLShopCatalogAdapter(connection_string=settings.mysql_shop_url)
        lookbook_repo = SQLiteLookbookRepository(database_url=settings.lookbook_db_url)

        # Step 1: Fetch products from shop catalog
        logger.info("Fetching products from shop catalog...")
        shop_items = await shop_adapter.fetch_items(limit=limit)

        if not shop_items:
            logger.warning("No products found in shop catalog")
            return {"status": "no_products", "message": "No products found in catalog"}

        logger.info(f"Found {len(shop_items)} products in catalog")

        # Step 2: Convert to domain entities with enhanced attributes
        logger.info("Converting products to domain entities...")
        products_to_save = []
        existing_skus = set()

        # First, get existing SKUs from database to avoid duplicates
        try:
            existing_items = await lookbook_repo.get_all_items()
            existing_skus = {item.sku for item in existing_items}
            logger.info(f"Found {len(existing_skus)} existing products in database")
        except Exception as e:
            logger.warning(f"Could not fetch existing products: {e}")

        for item in shop_items:
            try:
                # Handle both Item objects and dict responses
                if hasattr(item, 'sku'):
                    # Item object - convert to enhanced dict
                    item_dict = {
                        "sku": item.sku,
                        "title": item.title,
                        "price": item.price,
                        "size_range": getattr(item, 'size_range', []),
                        "image_key": getattr(item, 'image_key', f"{item.sku}.jpg"),
                        "attributes": getattr(item, 'attributes', {}),
                        "in_stock": getattr(item, 'in_stock', True),
                        # Extract attributes from nested structure if available
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
                    # Dict response - extract enhanced attributes
                    attributes = item.get('attributes', {})
                    item_dict = {
                        "sku": item.get('sku', f"product_{len(products_to_save)}"),
                        "title": item.get('title', f"Product {len(products_to_save)}"),
                        "price": item.get('price', 29.99),
                        "size_range": item.get('size_range', []),
                        "image_key": item.get('image_key', f"{item.get('sku', f'product_{len(products_to_save)}')}.jpg"),
                        "attributes": attributes,
                        "in_stock": item.get('in_stock', True),
                        # Extract from attributes or use direct values
                        "season": item.get('season') or attributes.get('season'),
                        "url_key": item.get('url_key') or attributes.get('url_key'),
                        "product_created_at": item.get('product_created_at') or attributes.get('created_at'),
                        "stock_qty": item.get('stock_qty', 0) or attributes.get('stock_qty', 0),
                        "category": item.get('category') or attributes.get('category'),
                        "color": item.get('color') or attributes.get('color'),
                        "material": item.get('material') or attributes.get('material'),
                        "pattern": item.get('pattern') or attributes.get('pattern'),
                        "occasion": item.get('occasion') or attributes.get('occasion')
                    }

                products_to_save.append(item_dict)

            except Exception as e:
                logger.error(f"Error converting product to domain entity: {e}")
                continue

        logger.info(f"Converted {len(products_to_save)} products to domain entities")

        # Step 3: Efficient batch save with upsert logic
        logger.info("Saving products to database with upsert logic...")
        results = await lookbook_repo.batch_upsert_products(products_to_save)

        logger.info(f"Sync completed: {results}")

        return {
            "status": "success",
            "products_synced": results.get("upserted", 0),
            "products_updated": results.get("updated", 0),
            "total_found": len(shop_items),
            "skus_processed": results.get("skus", []),
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