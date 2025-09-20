#!/usr/bin/env python3
"""
Script to analyze products in batches of 5 using vision AI.
This script will:
1. Fetch products from the database
2. Process them in batches of 5
3. Analyze each product with vision AI
4. Store vision attributes in the database
5. Track progress and results
"""

import asyncio
import sys
import os
import logging
from typing import List, Dict, Any, Optional
import time

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lookbook_mpc.adapters.db_shop import MySQLShopCatalogAdapter
from lookbook_mpc.adapters.vision import MockVisionProvider
from lookbook_mpc.adapters.db_lookbook import SQLiteLookbookRepository
from lookbook_mpc.domain.entities import Item, VisionAttributes
from lookbook_mpc.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def analyze_product_batch(product_skus: List[str], batch_size: int = 5) -> Dict[str, Any]:
    """
    Analyze a batch of products using vision AI.

    Args:
        product_skus: List of product SKUs to analyze
        batch_size: Number of products to process in each batch

    Returns:
        Dictionary with analysis results
    """
    try:
        logger.info(f"Starting batch analysis for {len(product_skus)} products (batch size: {batch_size})")

        # Initialize adapters
        shop_adapter = MySQLShopCatalogAdapter(connection_string=settings.mysql_shop_url)
        vision_adapter = MockVisionProvider()
        lookbook_repo = SQLiteLookbookRepository(database_url=settings.lookbook_db_url)

        # Process products in batches
        total_products = len(product_skus)
        analyzed_count = 0
        failed_count = 0
        results = []

        for i in range(0, total_products, batch_size):
            batch_skus = product_skus[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (total_products + batch_size - 1) // batch_size

            logger.info(f"Processing batch {batch_num}/{total_batches}: {len(batch_skus)} products")

            batch_results = []

            for product_sku in batch_skus:
                try:
                    logger.info(f"Analyzing product: {product_sku}")

                    # Get product from shop catalog
                    item = await shop_adapter.get_item_by_sku(product_sku)
                    if not item:
                        logger.warning(f"Product not found: {product_sku}")
                        failed_count += 1
                        batch_results.append({
                            "product_sku": product_sku,
                            "status": "failed",
                            "error": "Product not found"
                        })
                        continue

                    # Get image key for analysis
                    if hasattr(item, 'image_key'):
                        image_key = item.image_key
                    elif isinstance(item, dict) and 'image_key' in item:
                        image_key = item['image_key']
                    else:
                        logger.error(f"Product missing image_key: {product_sku}")
                        failed_count += 1
                        batch_results.append({
                            "product_sku": product_sku,
                            "status": "failed",
                            "error": "Product missing image_key"
                        })
                        continue

                    # Analyze product image with vision AI
                    logger.info(f"Analyzing image: {image_key}")
                    vision_attrs = await vision_adapter.analyze_image(image_key)

                    # Extract product details
                    if hasattr(item, 'sku'):
                        sku = item.sku
                        title = item.title
                        price = item.price
                        size_range = item.size_range
                        attributes = item.attributes
                        in_stock = item.in_stock
                    elif isinstance(item, dict):
                        sku = item['sku']
                        title = item['title']
                        price = item['price']
                        size_range = item.get('size_range', [])
                        attributes = item.get('attributes', {})
                        in_stock = item.get('in_stock', True)
                    else:
                        logger.error(f"Invalid item format: {product_sku}")
                        failed_count += 1
                        batch_results.append({
                            "product_sku": product_sku,
                            "status": "failed",
                            "error": "Invalid item format"
                        })
                        continue

                    # Create enhanced item with vision attributes
                    enhanced_item = Item(
                        sku=sku,
                        title=title,
                        price=price,
                        size_range=size_range,
                        image_key=image_key,
                        attributes={
                            **attributes,
                            "vision_attributes": vision_attrs if isinstance(vision_attrs, dict) else vision_attrs.dict()
                        },
                        in_stock=in_stock
                    )

                    # Save enhanced item to database
                    await lookbook_repo.save_items([enhanced_item])
                    analyzed_count += 1

                    batch_results.append({
                        "product_sku": product_sku,
                        "status": "analyzed",
                        "vision_attributes": vision_attrs if isinstance(vision_attrs, dict) else vision_attrs.dict(),
                        "title": title
                    })

                    logger.info(f"Successfully analyzed product: {product_sku}")

                except Exception as e:
                    logger.error(f"Failed to analyze product {product_sku}: {e}")
                    failed_count += 1
                    batch_results.append({
                        "product_sku": product_sku,
                        "status": "failed",
                        "error": str(e)
                    })

            results.extend(batch_results)

            # Small delay between batches to avoid overwhelming the system
            if i + batch_size < total_products:
                logger.info("Waiting before next batch...")
                await asyncio.sleep(1)

        logger.info(f"Batch analysis completed: {analyzed_count} successful, {failed_count} failed")

        return {
            "status": "completed",
            "total_products": total_products,
            "analyzed_products": analyzed_count,
            "failed_products": failed_count,
            "results": results,
            "message": f"Analysis complete: {analyzed_count} successful, {failed_count} failed"
        }

    except Exception as e:
        logger.error(f"Error in batch analysis: {e}")
        return {
            "status": "error",
            "error": str(e),
            "message": f"Batch analysis failed: {str(e)}"
        }

async def get_all_product_skus() -> List[str]:
    """Get all product SKUs from the database."""
    try:
        lookbook_repo = SQLiteLookbookRepository(database_url=settings.lookbook_db_url)
        products = await lookbook_repo.get_all_items()
        return [product.sku for product in products]
    except Exception as e:
        logger.error(f"Error getting product SKUs: {e}")
        return []

async def main():
    """Main function to run batch analysis."""
    print("=== Batch Product Analysis Script ===")
    print("This script will analyze products in batches of 5 using vision AI.")
    print()

    # Get all product SKUs from database
    print("Fetching all product SKUs from database...")
    product_skus = await get_all_product_skus()

    if not product_skus:
        print("No products found in database. Please run the sync script first.")
        return

    print(f"Found {len(product_skus)} products to analyze")
    print(f"Processing in batches of 5")
    print()

    # Process products in batches of 5
    result = await analyze_product_batch(product_skus, batch_size=5)

    print("\n=== Analysis Results ===")
    print(f"Status: {result['status']}")
    print(f"Total Products: {result.get('total_products', 0)}")
    print(f"Analyzed Products: {result.get('analyzed_products', 0)}")
    print(f"Failed Products: {result.get('failed_products', 0)}")
    print(f"Message: {result.get('message', 'No message')}")

    if result['status'] == 'success' and 'results' in result:
        successful_analyses = [r for r in result['results'] if r['status'] == 'analyzed']
        print(f"\nSuccessfully analyzed products:")
        for analysis in successful_analyses[:10]:  # Show first 10
            print(f"  - {analysis['product_sku']}: {analysis['title']}")

        if len(successful_analyses) > 10:
            print(f"  ... and {len(successful_analyses) - 10} more")

    print("\n=== Next Steps ===")
    print("1. Check the database for updated products with vision attributes")
    print("2. Test recommendations with the analyzed products")
    print("3. Run the verification script to see results")

if __name__ == "__main__":
    asyncio.run(main())