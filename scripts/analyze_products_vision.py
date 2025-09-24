#!/usr/bin/env python3
"""
Product Vision Analysis Script

This script analyzes products using Ollama vision model (qwen2.5vl:latest) to extract:
- Color, category, material, pattern, style
- Season, occasion, fit information
- Plus size detection
- Detailed product descriptions

Usage:
    python scripts/analyze_products_vision.py --limit 50 --batch-size 5
    python scripts/analyze_products_vision.py --auto --all
    python scripts/analyze_products_vision.py --sku "specific-sku"
"""

import asyncio
import sys
import os
import logging
import argparse
import json
import time
from typing import List, Dict, Any, Optional
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from lookbook_mpc.adapters.db_lookbook import MySQLLookbookRepository
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
from image.vision_analyzer import VisionAnalyzer
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("vision_analysis.log")],
)
logger = logging.getLogger(__name__)


class ProductVisionAnalyzer:
    """Enhanced product vision analyzer using Ollama with qwen2.5vl:latest"""

    def __init__(self):
        self.vision_analyzer = VisionAnalyzer(
            model="qwen2.5vl:latest", save_processed=False
        )
        self.db_repo = MySQLLookbookRepository(database_url=settings.lookbook_db_url)
        self.s3_base_url = os.getenv("S3_BASE_URL", "https://d29c1z66frfv6c.cloudfront.net/pub/media/catalog/product/large/")

        # Statistics tracking
        self.stats = {
            "processed": 0,
            "successful": 0,
            "failed": 0,
            "start_time": None,
            "results": [],
        }

    async def get_products_for_analysis(
        self,
        limit: Optional[int] = None,
        sku: Optional[str] = None,
        missing_vision_only: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Get products from the database that need vision analysis.

        Args:
            limit: Maximum number of products to fetch
            sku: Specific SKU to analyze (overrides other filters)
            missing_vision_only: Only get products without vision analysis

        Returns:
            List of product dictionaries
        """
        try:
            connection = await self.db_repo._get_connection()

            if sku:
                query = """
                    SELECT p.sku, p.title, p.image_key, p.price,
                           COALESCE(p.color, pva.color) as color,
                           COALESCE(p.category, pva.category) as category,
                           COALESCE(p.material, pva.material) as material,
                           COALESCE(p.pattern, pva.pattern) as pattern,
                           COALESCE(p.season, pva.season) as season,
                           COALESCE(p.occasion, pva.occasion) as occasion,
                           pva.description, p.created_at
                    FROM products p
                    LEFT JOIN product_vision_attributes pva ON p.sku = pva.sku
                    WHERE p.sku = %s AND p.in_stock = 1
                """
                params = [sku]
            else:
                if missing_vision_only:
                    # Get products that don't have detailed vision attributes
                    query = """
                        SELECT p.sku, p.title, p.image_key, p.price,
                               COALESCE(p.color, pva.color) as color,
                               COALESCE(p.category, pva.category) as category,
                               COALESCE(p.material, pva.material) as material,
                               COALESCE(p.pattern, pva.pattern) as pattern,
                               COALESCE(p.season, pva.season) as season,
                               COALESCE(p.occasion, pva.occasion) as occasion,
                               pva.description, p.created_at
                        FROM products p
                        LEFT JOIN product_vision_attributes pva ON p.sku = pva.sku
                        WHERE p.in_stock = 1
                        AND (
                            (p.color IS NULL OR p.color = '') AND (pva.color IS NULL OR pva.color = '') OR
                            (p.material IS NULL OR p.material = '') AND (pva.material IS NULL OR pva.material = '') OR
                            (p.pattern IS NULL OR p.pattern = '') AND (pva.pattern IS NULL OR pva.pattern = '') OR
                            (p.season IS NULL OR p.season = '') AND (pva.season IS NULL OR pva.season = '') OR
                            (p.occasion IS NULL OR p.occasion = '') AND (pva.occasion IS NULL OR pva.occasion = '')
                        )
                        ORDER BY p.created_at DESC
                    """
                else:
                    query = """
                        SELECT p.sku, p.title, p.image_key, p.price,
                               COALESCE(p.color, pva.color) as color,
                               COALESCE(p.category, pva.category) as category,
                               COALESCE(p.material, pva.material) as material,
                               COALESCE(p.pattern, pva.pattern) as pattern,
                               COALESCE(p.season, pva.season) as season,
                               COALESCE(p.occasion, pva.occasion) as occasion,
                               pva.description, p.created_at
                        FROM products p
                        LEFT JOIN product_vision_attributes pva ON p.sku = pva.sku
                        WHERE p.in_stock = 1
                        ORDER BY p.created_at DESC
                    """
                params = []

                if limit:
                    query += " LIMIT %s"
                    params.append(limit)

            async with connection.cursor() as cursor:
                await cursor.execute(query, params)
                rows = await cursor.fetchall()

                if not rows:
                    logger.warning("No products found matching criteria")
                    return []

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
                        "description": row[10],
                        "created_at": row[11],
                    }
                    products.append(product)

                logger.info(f"Found {len(products)} products for analysis")
                return products

        except Exception as e:
            logger.error(f"Error getting products: {e}")
            return []
        finally:
            if "connection" in locals():
                await connection.ensure_closed()

    async def analyze_single_product(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze a single product with vision AI.

        Args:
            product: Product dictionary with SKU, image_key, etc.

        Returns:
            Analysis result dictionary
        """
        sku = product["sku"]
        image_key = product["image_key"]
        title = product["title"]

        try:
            logger.info(f"Analyzing product: {sku} - {title}")

            # Validate image key
            if not image_key or image_key.strip() == "":
                raise ValueError(f"Product {sku} has no image_key")

            # Construct full image URL from S3_BASE_URL + image_key
            image_url = f"{self.s3_base_url.rstrip('/')}/{image_key.lstrip('/')}"
            logger.info(f"Processing image URL: {image_url}")

            # Analyze with Ollama vision model
            start_time = time.time()
            vision_result = self.vision_analyzer.analyze_product(image_url)
            analysis_time = time.time() - start_time

            logger.info(f"Vision analysis completed for {sku} in {analysis_time:.2f}s")

            # Validate and normalize attributes using domain entities
            try:
                # Map the vision result to our domain model
                vision_attrs = VisionAttributes(
                    color=vision_result.get("color"),
                    category=Category(vision_result.get("category"))
                    if vision_result.get("category")
                    else None,
                    material=Material(vision_result.get("material"))
                    if vision_result.get("material")
                    else None,
                    pattern=Pattern(vision_result.get("pattern"))
                    if vision_result.get("pattern")
                    else None,
                    season=Season(vision_result.get("season"))
                    if vision_result.get("season")
                    else None,
                    occasion=Occasion(vision_result.get("occasion"))
                    if vision_result.get("occasion")
                    else None,
                    fit=Fit(vision_result.get("fit"))
                    if vision_result.get("fit")
                    else None,
                    style=vision_result.get("style"),
                    plus_size=vision_result.get("plus_size", False),
                    description=vision_result.get("description"),
                )

                # Convert to dict for database storage
                validated_attrs = vision_attrs.dict(exclude_none=True)

                logger.info(f"Vision attributes validated for {sku}")

            except Exception as validation_error:
                logger.warning(f"Validation failed for {sku}: {validation_error}")
                # Use raw attributes if validation fails
                validated_attrs = vision_result

            # Update product in database
            success = await self.update_product_vision_attributes(sku, validated_attrs)

            result = {
                "sku": sku,
                "title": title,
                "status": "success" if success else "failed",
                "vision_attributes": validated_attrs,
                "analysis_time": analysis_time,
                "updated_database": success,
            }

            if success:
                self.stats["successful"] += 1
                logger.info(f"Successfully analyzed and updated: {sku}")
            else:
                self.stats["failed"] += 1
                result["error"] = "Failed to update database"

            return result

        except Exception as e:
            logger.error(f"Error analyzing product {sku}: {e}")
            self.stats["failed"] += 1
            return {
                "sku": sku,
                "title": title,
                "status": "failed",
                "error": str(e),
                "analysis_time": 0,
                "updated_database": False,
            }

    async def update_product_vision_attributes(
        self, sku: str, vision_attrs: Dict[str, Any]
    ) -> bool:
        """
        Update product with vision attributes in the database.

        Args:
            sku: Product SKU
            vision_attrs: Vision attributes dictionary

        Returns:
            True if successful, False otherwise
        """
        try:
            connection = await self.db_repo._get_connection()

            # Check if vision attributes record exists
            async with connection.cursor() as cursor:
                await cursor.execute("SELECT id FROM product_vision_attributes WHERE sku = %s", [sku])
                existing = await cursor.fetchone()

                # Prepare update fields and values
                update_fields = []
                values = []

                # Map vision attributes to database columns
                attr_mapping = {
                    "color": "color",
                    "category": "category",
                    "material": "material",
                    "pattern": "pattern",
                    "season": "season",
                    "occasion": "occasion",
                    "style": "style",
                    "fit": "fit",
                    "plus_size": "plus_size",
                    "description": "description",
                }

                for attr_key, db_column in attr_mapping.items():
                    if attr_key in vision_attrs and vision_attrs[attr_key] is not None:
                        value = vision_attrs[attr_key]

                        # Handle enum values - get their string representation
                        if hasattr(value, "value"):
                            value = value.value

                        update_fields.append(f"{db_column} = %s")
                        values.append(value)

                if not update_fields:
                    logger.warning(f"No vision attributes to update for {sku}")
                    return False

                if existing:
                    # Update existing record
                    query = f"""
                        UPDATE product_vision_attributes
                        SET {", ".join(update_fields)}, updated_at = CURRENT_TIMESTAMP
                        WHERE sku = %s
                    """
                    values.append(sku)
                else:
                    # Insert new record
                    fields = [f for f in attr_mapping.values() if f in [field.split(' = ')[0] for field in update_fields]]
                    fields.append('sku')
                    placeholders = ['%s'] * len(fields)
                    query = f"""
                        INSERT INTO product_vision_attributes ({", ".join(fields)})
                        VALUES ({", ".join(placeholders)})
                    """
                    values.append(sku)

                await cursor.execute(query, values)
                await connection.commit()

                if cursor.rowcount > 0:
                    logger.debug(f"Updated vision attributes for {sku}")
                    return True
                else:
                    logger.warning(f"Failed to update vision attributes for {sku}")
                    return False

        except Exception as e:
            logger.error(f"Error updating vision attributes for {sku}: {e}")
            return False
        finally:
            if "connection" in locals():
                await connection.ensure_closed()

    async def batch_analyze_products(
        self,
        products: List[Dict[str, Any]],
        batch_size: int = 5,
        delay_between_batches: float = 1.0,
    ) -> Dict[str, Any]:
        """
        Analyze products in batches.

        Args:
            products: List of product dictionaries
            batch_size: Number of products to process per batch
            delay_between_batches: Delay in seconds between batches

        Returns:
            Dictionary with batch analysis results
        """
        self.stats["start_time"] = time.time()
        total_products = len(products)

        logger.info(
            f"Starting batch analysis of {total_products} products (batch size: {batch_size})"
        )

        try:
            for i in range(0, total_products, batch_size):
                batch_products = products[i : i + batch_size]
                batch_num = (i // batch_size) + 1
                total_batches = (total_products + batch_size - 1) // batch_size

                logger.info(
                    f"Processing batch {batch_num}/{total_batches}: {len(batch_products)} products"
                )

                # Process batch
                batch_results = []
                for product in batch_products:
                    result = await self.analyze_single_product(product)
                    batch_results.append(result)
                    self.stats["processed"] += 1

                self.stats["results"].extend(batch_results)

                # Progress update
                progress = (i + len(batch_products)) / total_products * 100
                elapsed = time.time() - self.stats["start_time"]
                rate = self.stats["processed"] / elapsed if elapsed > 0 else 0

                logger.info(f"Progress: {progress:.1f}% - {rate:.2f} products/sec")

                # Delay between batches (except for last batch)
                if i + batch_size < total_products:
                    logger.info(
                        f"Waiting {delay_between_batches}s before next batch..."
                    )
                    await asyncio.sleep(delay_between_batches)

            # Final statistics
            total_time = time.time() - self.stats["start_time"]
            avg_time = (
                total_time / self.stats["processed"]
                if self.stats["processed"] > 0
                else 0
            )

            return {
                "status": "completed",
                "total_products": total_products,
                "processed": self.stats["processed"],
                "successful": self.stats["successful"],
                "failed": self.stats["failed"],
                "total_time": total_time,
                "avg_time_per_product": avg_time,
                "success_rate": (self.stats["successful"] / self.stats["processed"])
                * 100
                if self.stats["processed"] > 0
                else 0,
                "results": self.stats["results"],
            }

        except Exception as e:
            logger.error(f"Error in batch analysis: {e}")
            return {
                "status": "error",
                "error": str(e),
                "processed": self.stats["processed"],
                "successful": self.stats["successful"],
                "failed": self.stats["failed"],
            }


def print_analysis_report(results: Dict[str, Any]):
    """Print a comprehensive analysis report."""
    print("\n" + "=" * 80)
    print("🔍 PRODUCT VISION ANALYSIS REPORT")
    print("=" * 80)

    # Summary
    print(f"📊 SUMMARY")
    print(f"   Status: {results['status']}")
    print(f"   Total Products: {results.get('total_products', 0)}")
    print(f"   Processed: {results.get('processed', 0)}")
    print(f"   Successful: {results.get('successful', 0)}")
    print(f"   Failed: {results.get('failed', 0)}")

    if results.get("total_time"):
        print(f"   Total Time: {results['total_time']:.2f} seconds")
        print(f"   Average Time/Product: {results.get('avg_time_per_product', 0):.2f}s")
        print(f"   Success Rate: {results.get('success_rate', 0):.1f}%")

    # Show successful analyses
    if results.get("results"):
        successful = [r for r in results["results"] if r["status"] == "success"]
        failed = [r for r in results["results"] if r["status"] == "failed"]

        if successful:
            print(f"\n✅ SUCCESSFUL ANALYSES ({len(successful)})")
            for i, result in enumerate(successful[:10]):  # Show first 10
                attrs = result.get("vision_attributes", {})
                color = attrs.get("color", "N/A")
                category = attrs.get("category", "N/A")
                material = attrs.get("material", "N/A")
                pattern = attrs.get("pattern", "N/A")
                time_taken = result.get("analysis_time", 0)

                print(
                    f"   {i + 1:2d}. {result['sku']}: {color} {category} ({material}, {pattern}) - {time_taken:.2f}s"
                )

            if len(successful) > 10:
                print(f"       ... and {len(successful) - 10} more")

        if failed:
            print(f"\n❌ FAILED ANALYSES ({len(failed)})")
            for i, result in enumerate(failed[:5]):  # Show first 5 failures
                error = result.get("error", "Unknown error")
                print(f"   {i + 1}. {result['sku']}: {error}")

            if len(failed) > 5:
                print(f"      ... and {len(failed) - 5} more")

    print("\n" + "=" * 80)


async def main():
    """Main function to run vision analysis."""
    parser = argparse.ArgumentParser(
        description="Analyze products with Ollama vision AI (qwen2.5vl:latest)"
    )
    parser.add_argument(
        "--limit", type=int, default=50, help="Maximum number of products to analyze"
    )
    parser.add_argument(
        "--batch-size", type=int, default=3, help="Number of products per batch"
    )
    parser.add_argument("--sku", type=str, help="Analyze specific SKU")
    parser.add_argument(
        "--all",
        action="store_true",
        help="Analyze all products (not just missing vision data)",
    )
    parser.add_argument(
        "--auto", action="store_true", help="Run automatically without prompts"
    )
    parser.add_argument(
        "--delay", type=float, default=1.0, help="Delay between batches in seconds"
    )

    args = parser.parse_args()

    print("🔍 Product Vision Analysis with Ollama (qwen2.5vl:latest)")
    print("=" * 60)

    # Check database connection
    if not settings.lookbook_db_url:
        print("❌ ERROR: Database URL not configured")
        print("Please set MYSQL_APP_URL environment variable")
        return

    print(f"✅ Database configured: {settings.lookbook_db_url.split('@')[-1]}")

    # Initialize analyzer
    try:
        analyzer = ProductVisionAnalyzer()
        print("✅ Vision analyzer initialized with qwen2.5vl:latest")
    except Exception as e:
        print(f"❌ Failed to initialize vision analyzer: {e}")
        print("Make sure Ollama is running with qwen2.5vl:latest model")
        return

    # Get products to analyze
    print(f"\n📦 Fetching products...")
    products = await analyzer.get_products_for_analysis(
        limit=args.limit, sku=args.sku, missing_vision_only=not args.all
    )

    if not products:
        print("❌ No products found matching criteria")
        return

    print(f"✅ Found {len(products)} products to analyze")

    # Show sample products
    print("\n📋 Sample products:")
    for i, product in enumerate(products[:5]):
        missing_attrs = []
        for attr in ["color", "material", "pattern", "season", "occasion"]:
            if not product.get(attr):
                missing_attrs.append(attr)

        missing_str = (
            f" (missing: {', '.join(missing_attrs)})"
            if missing_attrs
            else " (complete)"
        )
        print(f"   {i + 1}. {product['sku']}: {product['title'][:60]}...{missing_str}")

    if len(products) > 5:
        print(f"   ... and {len(products) - 5} more")

    # Confirmation
    if not args.auto:
        print(f"\n⚠️  This will analyze {len(products)} products using Ollama AI")
        print(f"   Batch size: {args.batch_size}")
        print(f"   Delay between batches: {args.delay}s")
        print(f"   Estimated time: {len(products) * 3 / 60:.1f} minutes")

        response = input("\n🚀 Proceed with analysis? (y/N): ").strip().lower()
        if response != "y":
            print("❌ Analysis cancelled")
            return

    print(f"\n🚀 Starting vision analysis...")
    print(f"   Model: qwen2.5vl:latest")
    print(f"   Batch size: {args.batch_size}")
    print(f"   Products: {len(products)}")

    # Run analysis
    start_time = time.time()
    results = await analyzer.batch_analyze_products(
        products, batch_size=args.batch_size, delay_between_batches=args.delay
    )

    # Print report
    print_analysis_report(results)

    # Next steps
    print("🎯 NEXT STEPS")
    print("   1. Check the database for updated vision attributes")
    print("   2. Review failed analyses and retry if needed")
    print("   3. Test product recommendations with new data")
    print("   4. Start the API server: python main.py")

    # Save detailed results
    results_file = f"vision_analysis_results_{int(time.time())}.json"
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"   📄 Detailed results saved to: {results_file}")


if __name__ == "__main__":
    asyncio.run(main())
