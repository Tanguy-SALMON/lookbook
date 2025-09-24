#!/usr/bin/env python3
"""
Enhanced Product Import Script

Imports 5000 enabled, in-stock products from Magento to Lookbook database.
Uses existing product import service infrastructure with progress tracking,
resume capability, and comprehensive error handling.

Usage:
    poetry run python scripts/sync_5000_products.py [--limit 5000] [--batch-size 100] [--resume]
"""

import asyncio
import sys
import os
import argparse
import time
from typing import Dict, Any, Optional
import logging

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lookbook_mpc.adapters.db_shop import MySQLShopCatalogAdapter
from lookbook_mpc.adapters.db_lookbook import MySQLLookbookRepository
from lookbook_mpc.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("product_sync.log"),
    ],
)
logger = logging.getLogger(__name__)


class EnhancedProductSync:
    """Enhanced product synchronization with progress tracking and resume capability."""

    def __init__(self):
        self.shop_adapter = None
        self.lookbook_repo = None
        self.stats = {
            "total_target": 0,
            "total_processed": 0,
            "total_inserted": 0,
            "total_updated": 0,
            "total_errors": 0,
            "batches_completed": 0,
            "start_time": None,
            "last_source_id": 0,
        }

    async def initialize(self):
        """Initialize database connections."""
        logger.info("Initializing database connections...")

        if not settings.mysql_shop_url:
            raise ValueError(
                "MYSQL_SHOP_URL environment variable not set. "
                "Please configure connection to Magento database."
            )

        if not settings.lookbook_db_url:
            raise ValueError(
                "LOOKBOOK_DB_URL environment variable not set. "
                "Please configure connection to Lookbook database."
            )

        self.shop_adapter = MySQLShopCatalogAdapter(
            connection_string=settings.mysql_shop_url
        )
        self.lookbook_repo = MySQLLookbookRepository(
            database_url=settings.lookbook_db_url
        )

        logger.info("Database connections initialized successfully")

    async def get_resume_point(self) -> int:
        """Get the last processed source ID for resume capability."""
        try:
            # Try to get from a simple file-based checkpoint
            checkpoint_file = "product_sync_checkpoint.txt"
            if os.path.exists(checkpoint_file):
                with open(checkpoint_file, "r") as f:
                    return int(f.read().strip())
            return 0
        except Exception as e:
            logger.warning(f"Could not read checkpoint file: {e}")
            return 0

    async def save_checkpoint(self, source_id: int):
        """Save current progress checkpoint."""
        try:
            checkpoint_file = "product_sync_checkpoint.txt"
            with open(checkpoint_file, "w") as f:
                f.write(str(source_id))
            self.stats["last_source_id"] = source_id
        except Exception as e:
            logger.error(f"Could not save checkpoint: {e}")

    def transform_product(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """Transform product from Magento format to Lookbook format."""
        try:
            return {
                "sku": product.get("sku"),
                "title": product.get(
                    "title", f"Product {product.get('sku', 'Unknown')}"
                ),
                "price": float(product.get("price", 0))
                if product.get("price")
                else 29.99,
                "size_range": product.get("size_range", ["S", "M", "L", "XL"]),
                "image_key": product.get(
                    "image_key", f"{product.get('sku', 'unknown')}.jpg"
                ),
                "attributes": product.get("attributes", {}),
                "in_stock": product.get("in_stock", True),
                "season": product.get("season"),
                "url_key": product.get("url_key"),
                "product_created_at": product.get("product_created_at"),
                "stock_qty": int(product.get("stock_qty", 0)),
                "category": product.get("category", "fashion"),
                "color": product.get("color"),
                "material": product.get("material"),
                "pattern": product.get("pattern"),
                "occasion": product.get("occasion"),
            }
        except Exception as e:
            logger.error(
                f"Error transforming product {product.get('sku', 'unknown')}: {e}"
            )
            raise

    async def sync_batch(self, start_after_id: int, batch_size: int) -> Dict[str, Any]:
        """Sync a single batch of products."""
        batch_start = time.time()

        try:
            logger.info(
                f"Fetching batch: start_after_id={start_after_id}, batch_size={batch_size}"
            )

            # Fetch products from Magento
            products = await self.shop_adapter.get_enabled_products_with_stock(
                start_after_id=start_after_id, limit=batch_size
            )

            if not products:
                logger.info("No more products found")
                return {"products": [], "max_source_id": start_after_id}

            logger.info(f"Found {len(products)} products in batch")

            # Transform products
            transformed_products = []
            max_source_id = start_after_id

            for product in products:
                try:
                    transformed = self.transform_product(product)
                    transformed_products.append(transformed)
                    max_source_id = max(max_source_id, product.get("source_id", 0))
                except Exception as e:
                    logger.error(
                        f"Failed to transform product {product.get('sku')}: {e}"
                    )
                    self.stats["total_errors"] += 1
                    continue

            if not transformed_products:
                logger.warning("No valid products to insert in this batch")
                return {"products": [], "max_source_id": max_source_id}

            # Batch upsert to Lookbook database
            logger.info(f"Upserting {len(transformed_products)} products to database")
            upsert_result = await self.lookbook_repo.batch_upsert_products(
                transformed_products
            )

            # Update statistics
            batch_inserted = upsert_result.get("upserted", 0)
            batch_updated = upsert_result.get("updated", 0)

            self.stats["total_processed"] += len(transformed_products)
            self.stats["total_inserted"] += batch_inserted
            self.stats["total_updated"] += batch_updated
            self.stats["batches_completed"] += 1

            batch_time = time.time() - batch_start

            logger.info(
                f"Batch completed: processed={len(transformed_products)}, "
                f"inserted={batch_inserted}, updated={batch_updated}, "
                f"time={batch_time:.2f}s"
            )

            # Save checkpoint
            await self.save_checkpoint(max_source_id)

            return {
                "products": transformed_products,
                "max_source_id": max_source_id,
                "batch_inserted": batch_inserted,
                "batch_updated": batch_updated,
                "batch_time": batch_time,
            }

        except Exception as e:
            logger.error(f"Error processing batch starting at {start_after_id}: {e}")
            raise

    async def sync_products(
        self, target_count: int = 5000, batch_size: int = 100, resume: bool = True
    ):
        """Main sync function with progress tracking."""
        self.stats["start_time"] = time.time()
        self.stats["total_target"] = target_count

        logger.info(
            f"Starting product sync: target={target_count}, batch_size={batch_size}, resume={resume}"
        )

        try:
            # Determine starting point
            if resume:
                start_after_id = await self.get_resume_point()
                logger.info(f"Resuming from source_id: {start_after_id}")
            else:
                start_after_id = 0
                logger.info("Starting fresh sync from beginning")

            current_source_id = start_after_id
            total_processed = 0

            while total_processed < target_count:
                remaining = target_count - total_processed
                current_batch_size = min(batch_size, remaining)

                logger.info(
                    f"Progress: {total_processed}/{target_count} ({(total_processed / target_count) * 100:.1f}%)"
                )

                batch_result = await self.sync_batch(
                    current_source_id, current_batch_size
                )

                if not batch_result["products"]:
                    logger.info("No more products available - sync complete")
                    break

                current_source_id = batch_result["max_source_id"]
                total_processed += len(batch_result["products"])

                # Progress update
                elapsed = time.time() - self.stats["start_time"]
                rate = total_processed / elapsed if elapsed > 0 else 0
                eta = (target_count - total_processed) / rate if rate > 0 else 0

                logger.info(
                    f"Batch {self.stats['batches_completed']} complete. "
                    f"Rate: {rate:.1f} products/sec, ETA: {eta / 60:.1f} minutes"
                )

                # Small delay to prevent overwhelming the database
                await asyncio.sleep(0.5)

            await self.print_final_summary()

        except Exception as e:
            logger.error(f"Sync failed: {e}")
            await self.print_final_summary()
            raise

    async def print_final_summary(self):
        """Print comprehensive sync summary."""
        elapsed = (
            time.time() - self.stats["start_time"] if self.stats["start_time"] else 0
        )

        print("\n" + "=" * 80)
        print("PRODUCT SYNC SUMMARY")
        print("=" * 80)
        print(f"Target Products:     {self.stats['total_target']:,}")
        print(f"Total Processed:     {self.stats['total_processed']:,}")
        print(f"New Products:        {self.stats['total_inserted']:,}")
        print(f"Updated Products:    {self.stats['total_updated']:,}")
        print(f"Errors:              {self.stats['total_errors']:,}")
        print(f"Batches Completed:   {self.stats['batches_completed']:,}")
        print(f"Last Source ID:      {self.stats['last_source_id']:,}")
        print(f"Total Time:          {elapsed / 60:.2f} minutes")
        if elapsed > 0:
            print(
                f"Processing Rate:     {self.stats['total_processed'] / elapsed:.1f} products/sec"
            )
        print(
            f"Success Rate:        {((self.stats['total_processed'] - self.stats['total_errors']) / max(1, self.stats['total_processed'])) * 100:.1f}%"
        )
        print("=" * 80)

        if self.stats["total_processed"] > 0:
            print("\nNext Steps:")
            print("1. Run vision analysis on new products")
            print("2. Verify product data in admin dashboard")
            print("3. Test AI recommendations with expanded catalog")
            print("4. Monitor system performance with larger dataset")


async def main():
    """Main function with command line argument parsing."""
    parser = argparse.ArgumentParser(
        description="Import products from Magento to Lookbook"
    )
    parser.add_argument(
        "--limit", type=int, default=5000, help="Maximum products to import"
    )
    parser.add_argument(
        "--batch-size", type=int, default=100, help="Batch size for processing"
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        default=True,
        help="Resume from last checkpoint",
    )
    parser.add_argument(
        "--fresh", action="store_true", help="Start fresh (ignore checkpoints)"
    )

    args = parser.parse_args()

    # Handle fresh start
    if args.fresh:
        args.resume = False
        # Remove checkpoint file
        checkpoint_file = "product_sync_checkpoint.txt"
        if os.path.exists(checkpoint_file):
            os.remove(checkpoint_file)
            print("Checkpoint file removed - starting fresh")

    print(f"Enhanced Product Import Script")
    print(f"Target: {args.limit:,} products")
    print(f"Batch size: {args.batch_size}")
    print(f"Resume: {'Yes' if args.resume else 'No (fresh start)'}")
    print()

    sync = EnhancedProductSync()

    try:
        await sync.initialize()
        await sync.sync_products(
            target_count=args.limit, batch_size=args.batch_size, resume=args.resume
        )
        print("\nSync completed successfully! ✅")

    except KeyboardInterrupt:
        print("\nSync interrupted by user. Progress has been saved.")
        await sync.print_final_summary()
        print("Run the script again with --resume to continue from checkpoint.")

    except Exception as e:
        print(f"\nSync failed with error: {e}")
        await sync.print_final_summary()
        print("Check the logs for detailed error information.")
        print("Run the script again with --resume to retry from last checkpoint.")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
