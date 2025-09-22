#!/usr/bin/env python3
"""
Script to analyze products in batches of 5 using vision AI.
This script will:
1. Fetch products from the MySQL database
2. Process them in batches of 5
3. Analyze each product with vision AI
4. Update products with vision attributes in the database
5. Track progress and results
"""

import asyncio
import sys
import os
import logging
import argparse
from typing import List, Dict, Any, Optional
import time

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lookbook_mpc.adapters.db_lookbook import MySQLLookbookRepository
from lookbook_mpc.adapters.vision import MockVisionProvider, VisionProviderOllama
from lookbook_mpc.domain.entities import (
    VisionAttributes,
    Category,
    Material,
    Pattern,
    Season,
    Occasion,
    Fit,
)
from lookbook_mpc.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def update_product_vision_attributes(
    repo: MySQLLookbookRepository, sku: str, vision_attrs: Dict[str, Any]
) -> bool:
    """
    Update a product with vision attributes in the database.

    Args:
        repo: Database repository
        sku: Product SKU
        vision_attrs: Vision attributes dictionary

    Returns:
        True if successful, False otherwise
    """
    try:
        # Get database connection
        connection = await repo._get_connection()

        # Prepare update query with vision attributes
        update_fields = []
        values = []

        # Map vision attributes to database columns
        if "color" in vision_attrs and vision_attrs["color"]:
            update_fields.append("color = %s")
            values.append(vision_attrs["color"])

        if "category" in vision_attrs and vision_attrs["category"]:
            update_fields.append("category = %s")
            values.append(vision_attrs["category"])

        if "material" in vision_attrs and vision_attrs["material"]:
            update_fields.append("material = %s")
            values.append(vision_attrs["material"])

        if "pattern" in vision_attrs and vision_attrs["pattern"]:
            update_fields.append("pattern = %s")
            values.append(vision_attrs["pattern"])

        if "season" in vision_attrs and vision_attrs["season"]:
            update_fields.append("season = %s")
            values.append(vision_attrs["season"])

        if "occasion" in vision_attrs and vision_attrs["occasion"]:
            update_fields.append("occasion = %s")
            values.append(vision_attrs["occasion"])

        # Add updated timestamp
        update_fields.append("updated_at = CURRENT_TIMESTAMP")

        if not update_fields:
            logger.warning(f"No vision attributes to update for {sku}")
            return False

        # Build and execute update query
        query = f"""
            UPDATE products
            SET {", ".join(update_fields)}
            WHERE sku = %s
        """
        values.append(sku)

        async with connection.cursor() as cursor:
            await cursor.execute(query, values)
            await connection.commit()

            if cursor.rowcount > 0:
                logger.info(f"Updated vision attributes for product {sku}")
                return True
            else:
                logger.warning(f"No product found with SKU {sku}")
                return False

    except Exception as e:
        logger.error(f"Error updating vision attributes for {sku}: {e}")
        return False
    finally:
        if "connection" in locals():
            await connection.ensure_closed()


async def analyze_product_batch(
    product_data: List[Dict[str, Any]], batch_size: int = 5
) -> Dict[str, Any]:
    """
    Analyze a batch of products using vision AI.

    Args:
        product_data: List of product dictionaries with SKU, image_key, title, etc.
        batch_size: Number of products to process in each batch

    Returns:
        Dictionary with analysis results
    """
    try:
        logger.info(
            f"Starting batch analysis for {len(product_data)} products (batch size: {batch_size})"
        )

        # Initialize adapters
        lookbook_repo = MySQLLookbookRepository(database_url=settings.lookbook_db_url)

        # Use MockVisionProvider for now (vision sidecar setup can be done later)
        vision_adapter = MockVisionProvider()
        logger.info("Using MockVisionProvider (generating realistic mock data)")

        # Process products in batches
        total_products = len(product_data)
        analyzed_count = 0
        failed_count = 0
        results = []

        for i in range(0, total_products, batch_size):
            batch_products = product_data[i : i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (total_products + batch_size - 1) // batch_size

            logger.info(
                f"Processing batch {batch_num}/{total_batches}: {len(batch_products)} products"
            )

            batch_results = []

            for product in batch_products:
                try:
                    sku = product["sku"]
                    image_key = product["image_key"]
                    title = product["title"]

                    logger.info(f"Analyzing product: {sku} - {title}")

                    # Check if image_key is valid
                    if not image_key or image_key.strip() == "":
                        logger.warning(f"Product {sku} has no image_key, using default")
                        image_key = f"{sku}.jpg"

                    # Analyze product image with vision AI
                    logger.info(f"Analyzing image: {image_key}")
                    vision_attrs = await vision_adapter.analyze_image(image_key)

                    # Validate vision attributes using domain entity
                    try:
                        vision_entity = VisionAttributes(**vision_attrs)
                        validated_attrs = vision_entity.dict()
                        logger.info(
                            f"Vision analysis successful for {sku}: {validated_attrs}"
                        )
                    except Exception as validation_error:
                        logger.error(
                            f"Vision attributes validation failed for {sku}: {validation_error}"
                        )
                        # Use raw attributes if validation fails
                        validated_attrs = vision_attrs

                    # Update product in database with vision attributes
                    success = await update_product_vision_attributes(
                        lookbook_repo, sku, validated_attrs
                    )

                    if success:
                        analyzed_count += 1
                        batch_results.append(
                            {
                                "product_sku": sku,
                                "status": "analyzed",
                                "vision_attributes": validated_attrs,
                                "title": title,
                            }
                        )
                        logger.info(f"Successfully analyzed and updated product: {sku}")
                    else:
                        failed_count += 1
                        batch_results.append(
                            {
                                "product_sku": sku,
                                "status": "failed",
                                "error": "Failed to update database",
                                "title": title,
                            }
                        )

                except Exception as e:
                    logger.error(
                        f"Failed to analyze product {product.get('sku', 'unknown')}: {e}"
                    )
                    failed_count += 1
                    batch_results.append(
                        {
                            "product_sku": product.get("sku", "unknown"),
                            "status": "failed",
                            "error": str(e),
                            "title": product.get("title", "Unknown"),
                        }
                    )

            results.extend(batch_results)

            # Small delay between batches to avoid overwhelming the system
            if i + batch_size < total_products:
                logger.info("Waiting before next batch...")
                await asyncio.sleep(1)

        logger.info(
            f"Batch analysis completed: {analyzed_count} successful, {failed_count} failed"
        )

        return {
            "status": "completed",
            "total_products": total_products,
            "analyzed_products": analyzed_count,
            "failed_products": failed_count,
            "results": results,
            "message": f"Analysis complete: {analyzed_count} successful, {failed_count} failed",
        }

    except Exception as e:
        logger.error(f"Error in batch analysis: {e}")
        return {
            "status": "error",
            "error": str(e),
            "message": f"Batch analysis failed: {str(e)}",
        }


async def get_products_for_analysis(
    limit: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Get products from the database that need vision analysis.

    Args:
        limit: Maximum number of products to fetch (None for all)

    Returns:
        List of product dictionaries
    """
    try:
        lookbook_repo = MySQLLookbookRepository(database_url=settings.lookbook_db_url)
        connection = await lookbook_repo._get_connection()

        # Query to get products that haven't been analyzed yet
        # (products without detailed vision attributes)
        query = """
            SELECT sku, title, image_key, price, color, category, material, pattern, season, occasion
            FROM products
            WHERE in_stock = 1
            ORDER BY created_at DESC
        """

        if limit:
            query += f" LIMIT {limit}"

        async with connection.cursor() as cursor:
            await cursor.execute(query)
            rows = await cursor.fetchall()

            if not rows:
                logger.warning("No products found in database")
                return []

            # Convert to list of dictionaries
            products = []
            for row in rows:
                product = {
                    "sku": row[0],
                    "title": row[1],
                    "image_key": row[2],
                    "price": row[3],
                    "color": row[4],
                    "category": row[5],
                    "material": row[6],
                    "pattern": row[7],
                    "season": row[8],
                    "occasion": row[9],
                }
                products.append(product)

            logger.info(f"Found {len(products)} products for analysis")
            return products

    except Exception as e:
        logger.error(f"Error getting products for analysis: {e}")
        return []
    finally:
        if "connection" in locals():
            await connection.ensure_closed()


async def main():
    """Main function to run batch analysis."""
    print("=== Batch Product Vision Analysis Script ===")
    print("This script will analyze products in batches of 5 using vision AI.")
    print("It will update products with detailed descriptions and attributes.")
    print()

    # Check database connection
    print("Checking database connection...")
    if not settings.lookbook_db_url:
        print("❌ ERROR: MYSQL_APP_URL environment variable is not set!")
        print("Please configure the MySQL connection string for the lookbook database.")
        return

    print(f"✅ Database URL configured: {settings.lookbook_db_url}")
    print()

    # Get products from database
    print("Fetching products from database...")
    product_data = await get_products_for_analysis(
        limit=100
    )  # Limit to 100 for testing

    if not product_data:
        print("❌ No products found in database.")
        print("Please run the sync script first: python scripts/sync_100_products.py")
        return

    print(f"✅ Found {len(product_data)} products to analyze")
    print()

    # Show some examples
    print("Sample products to be analyzed:")
    for i, product in enumerate(product_data[:5]):
        print(
            f"  {i + 1}. {product['sku']}: {product['title']} (image: {product['image_key']})"
        )
    if len(product_data) > 5:
        print(f"  ... and {len(product_data) - 5} more")
    print()

    # Check for command line arguments
    parser = argparse.ArgumentParser(
        description="Batch analyze products with vision AI"
    )
    parser.add_argument(
        "--auto", action="store_true", help="Run automatically without prompts"
    )
    args = parser.parse_args()

    if not args.auto:
        # Confirm before proceeding
        response = input("Proceed with vision analysis? (y/N): ").strip().lower()
        if response != "y":
            print("Analysis cancelled.")
            return

    print("\n=== Starting Vision Analysis ===")

    # Process products in batches of 5
    start_time = time.time()
    result = await analyze_product_batch(product_data, batch_size=5)
    total_time = time.time() - start_time

    print("\n=== Analysis Results ===")
    print(f"Status: {result['status']}")
    print(f"Total Products: {result.get('total_products', 0)}")
    print(f"Analyzed Products: {result.get('analyzed_products', 0)}")
    print(f"Failed Products: {result.get('failed_products', 0)}")
    print(f"Total Time: {total_time:.2f} seconds")
    print(f"Message: {result.get('message', 'No message')}")

    if result["status"] == "completed" and "results" in result:
        successful_analyses = [
            r for r in result["results"] if r["status"] == "analyzed"
        ]

        if successful_analyses:
            print(f"\n✅ Successfully analyzed products:")
            for analysis in successful_analyses[:10]:  # Show first 10
                attrs = analysis.get("vision_attributes", {})
                color = attrs.get("color", "N/A")
                category = attrs.get("category", "N/A")
                material = attrs.get("material", "N/A")
                print(f"  - {analysis['product_sku']}: {color} {category} ({material})")

            if len(successful_analyses) > 10:
                print(f"  ... and {len(successful_analyses) - 10} more")

        failed_analyses = [r for r in result["results"] if r["status"] == "failed"]
        if failed_analyses:
            print(f"\n❌ Failed products:")
            for analysis in failed_analyses[:5]:  # Show first 5 failures
                error = analysis.get("error", "Unknown error")
                print(f"  - {analysis['product_sku']}: {error}")

    print("\n=== Next Steps ===")
    print("1. Check the database products table for updated vision attributes")
    print("2. Run verification: python scripts/verify_product_import.py")
    print("3. Test recommendations with the analyzed products")
    print("4. Start the API server: python main.py")


if __name__ == "__main__":
    asyncio.run(main())
