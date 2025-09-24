"""
Vision Analysis Service

This service handles product vision analysis requests from the admin panel.
It provides methods to:
- Analyze single products
- Run batch analysis
- Track analysis progress
- Get analysis statistics
"""

import asyncio
import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from ..adapters.db_lookbook import MySQLLookbookRepository
from ..domain.entities import (
    VisionAttributes,
    Category,
    Material,
    Pattern,
    Season,
    Occasion,
    Fit,
)
from ..config import settings

logger = logging.getLogger(__name__)


class VisionAnalysisService:
    """Service for managing product vision analysis operations."""

    def __init__(self):
        self.db_repo = MySQLLookbookRepository(database_url=settings.lookbook_db_url)
        self._analysis_tasks = {}  # Store running analysis tasks
        self._analysis_stats = {}  # Store analysis statistics

    async def get_analysis_statistics(self) -> Dict[str, Any]:
        """
        Get overall vision analysis statistics.

        Returns:
            Dictionary with analysis statistics
        """
        try:
            connection = await self.db_repo._get_connection()

            async with connection.cursor() as cursor:
                # Total products
                await cursor.execute("SELECT COUNT(*) FROM products WHERE in_stock = 1")
                total_products = (await cursor.fetchone())[0]

                # Products with vision analysis
                await cursor.execute("""
                    SELECT COUNT(*) FROM products
                    WHERE in_stock = 1
                    AND color IS NOT NULL AND color != ''
                    AND material IS NOT NULL AND material != ''
                    AND pattern IS NOT NULL AND pattern != ''
                """)
                analyzed_products = (await cursor.fetchone())[0]

                # Products needing analysis
                missing_analysis = total_products - analyzed_products

                # Recent analysis (last 7 days)
                await cursor.execute("""
                    SELECT COUNT(*) FROM products
                    WHERE in_stock = 1
                    AND updated_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
                    AND color IS NOT NULL AND color != ''
                """)
                recent_analysis = (await cursor.fetchone())[0]

                # Category breakdown
                await cursor.execute("""
                    SELECT category, COUNT(*) as count
                    FROM products
                    WHERE in_stock = 1 AND category IS NOT NULL AND category != ''
                    GROUP BY category
                    ORDER BY count DESC
                    LIMIT 10
                """)
                category_breakdown = {row[0]: row[1] for row in await cursor.fetchall()}

                # Color breakdown
                await cursor.execute("""
                    SELECT color, COUNT(*) as count
                    FROM products
                    WHERE in_stock = 1 AND color IS NOT NULL AND color != ''
                    GROUP BY color
                    ORDER BY count DESC
                    LIMIT 10
                """)
                color_breakdown = {row[0]: row[1] for row in await cursor.fetchall()}

                return {
                    "total_products": total_products,
                    "analyzed_products": analyzed_products,
                    "missing_analysis": missing_analysis,
                    "analysis_coverage": (analyzed_products / total_products * 100)
                    if total_products > 0
                    else 0,
                    "recent_analysis": recent_analysis,
                    "category_breakdown": category_breakdown,
                    "color_breakdown": color_breakdown,
                    "last_updated": datetime.now().isoformat(),
                }

        except Exception as e:
            logger.error(f"Error getting analysis statistics: {e}")
            return {
                "error": str(e),
                "total_products": 0,
                "analyzed_products": 0,
                "missing_analysis": 0,
                "analysis_coverage": 0,
            }
        finally:
            if "connection" in locals():
                await connection.ensure_closed()

    async def get_products_needing_analysis(
        self, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get products that need vision analysis.

        Args:
            limit: Maximum number of products to return

        Returns:
            List of product dictionaries
        """
        try:
            connection = await self.db_repo._get_connection()

            query = """
                SELECT sku, title, image_key, price, color, category, material,
                       pattern, season, occasion, created_at
                FROM products
                WHERE in_stock = 1
                AND (
                    color IS NULL OR color = '' OR
                    material IS NULL OR material = '' OR
                    pattern IS NULL OR pattern = '' OR
                    season IS NULL OR season = '' OR
                    occasion IS NULL OR occasion = ''
                )
                ORDER BY created_at DESC
                LIMIT %s
            """

            async with connection.cursor() as cursor:
                await cursor.execute(query, [limit])
                rows = await cursor.fetchall()

                products = []
                for row in rows:
                    missing_attrs = []
                    attrs = {
                        "color": row[4],
                        "material": row[6],
                        "pattern": row[7],
                        "season": row[8],
                        "occasion": row[9],
                    }

                    for attr_name, attr_value in attrs.items():
                        if not attr_value or attr_value.strip() == "":
                            missing_attrs.append(attr_name)

                    products.append(
                        {
                            "sku": row[0],
                            "title": row[1],
                            "image_key": row[2],
                            "price": float(row[3]) if row[3] else 0,
                            "color": row[4],
                            "category": row[5],
                            "material": row[6],
                            "pattern": row[7],
                            "season": row[8],
                            "occasion": row[9],
                            "created_at": row[10].isoformat() if row[10] else None,
                            "missing_attributes": missing_attrs,
                            "analysis_needed": len(missing_attrs) > 0,
                        }
                    )

                return products

        except Exception as e:
            logger.error(f"Error getting products needing analysis: {e}")
            return []
        finally:
            if "connection" in locals():
                await connection.ensure_closed()

    async def start_batch_analysis(
        self,
        limit: Optional[int] = None,
        batch_size: int = 5,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Start a batch analysis process.

        Args:
            limit: Maximum number of products to analyze
            batch_size: Number of products per batch
            user_id: ID of user who started the analysis

        Returns:
            Analysis task information
        """
        try:
            # Generate unique task ID
            task_id = f"analysis_{int(time.time())}"

            # Get products to analyze
            products = await self.get_products_needing_analysis(limit or 1000)

            if not products:
                return {
                    "success": False,
                    "error": "No products found that need analysis",
                    "task_id": None,
                }

            # Initialize task tracking
            self._analysis_stats[task_id] = {
                "task_id": task_id,
                "status": "starting",
                "total_products": len(products),
                "processed": 0,
                "successful": 0,
                "failed": 0,
                "start_time": datetime.now(),
                "user_id": user_id,
                "batch_size": batch_size,
                "estimated_duration": len(products) * 3,  # ~3 seconds per product
                "progress_percentage": 0,
                "current_batch": 0,
                "errors": [],
            }

            # Start the analysis task
            task = asyncio.create_task(
                self._run_batch_analysis(task_id, products, batch_size)
            )
            self._analysis_tasks[task_id] = task

            logger.info(
                f"Started batch analysis task {task_id} for {len(products)} products"
            )

            return {
                "success": True,
                "task_id": task_id,
                "total_products": len(products),
                "estimated_duration": len(products) * 3,
                "message": f"Analysis started for {len(products)} products",
            }

        except Exception as e:
            logger.error(f"Error starting batch analysis: {e}")
            return {
                "success": False,
                "error": str(e),
                "task_id": None,
            }

    async def _run_batch_analysis(
        self, task_id: str, products: List[Dict[str, Any]], batch_size: int
    ):
        """
        Run the actual batch analysis (internal method).

        Args:
            task_id: Unique task identifier
            products: List of products to analyze
            batch_size: Number of products per batch
        """
        try:
            # Import here to avoid circular imports
            from ...image.vision_analyzer import VisionAnalyzer

            # Update status to running
            self._analysis_stats[task_id]["status"] = "running"

            # Initialize vision analyzer
            vision_analyzer = VisionAnalyzer(
                model="qwen2.5vl:latest", save_processed=False
            )

            total_products = len(products)

            for i in range(0, total_products, batch_size):
                batch_products = products[i : i + batch_size]
                batch_num = (i // batch_size) + 1
                total_batches = (total_products + batch_size - 1) // batch_size

                # Update progress
                self._analysis_stats[task_id]["current_batch"] = batch_num
                self._analysis_stats[task_id]["progress_percentage"] = (
                    i / total_products
                ) * 100

                logger.info(
                    f"Task {task_id}: Processing batch {batch_num}/{total_batches}"
                )

                # Process each product in the batch
                for product in batch_products:
                    try:
                        sku = product["sku"]
                        image_key = product["image_key"]

                        if not image_key or image_key.strip() == "":
                            raise ValueError(f"No image_key for product {sku}")

                        # Analyze with vision model
                        vision_result = vision_analyzer.analyze_product(image_key)

                        # Update product in database
                        success = await self._update_product_vision_attributes(
                            sku, vision_result
                        )

                        if success:
                            self._analysis_stats[task_id]["successful"] += 1
                        else:
                            self._analysis_stats[task_id]["failed"] += 1
                            self._analysis_stats[task_id]["errors"].append(
                                {
                                    "sku": sku,
                                    "error": "Failed to update database",
                                }
                            )

                        self._analysis_stats[task_id]["processed"] += 1

                    except Exception as e:
                        logger.error(
                            f"Error analyzing product {product.get('sku', 'unknown')}: {e}"
                        )
                        self._analysis_stats[task_id]["failed"] += 1
                        self._analysis_stats[task_id]["processed"] += 1
                        self._analysis_stats[task_id]["errors"].append(
                            {
                                "sku": product.get("sku", "unknown"),
                                "error": str(e),
                            }
                        )

                # Small delay between batches
                if i + batch_size < total_products:
                    await asyncio.sleep(1)

            # Mark as completed
            self._analysis_stats[task_id]["status"] = "completed"
            self._analysis_stats[task_id]["end_time"] = datetime.now()
            self._analysis_stats[task_id]["progress_percentage"] = 100

            logger.info(
                f"Task {task_id} completed: {self._analysis_stats[task_id]['successful']} successful, {self._analysis_stats[task_id]['failed']} failed"
            )

        except Exception as e:
            logger.error(f"Error in batch analysis task {task_id}: {e}")
            self._analysis_stats[task_id]["status"] = "failed"
            self._analysis_stats[task_id]["error"] = str(e)
            self._analysis_stats[task_id]["end_time"] = datetime.now()

    async def get_analysis_progress(self, task_id: str) -> Dict[str, Any]:
        """
        Get progress information for an analysis task.

        Args:
            task_id: Task identifier

        Returns:
            Progress information dictionary
        """
        if task_id not in self._analysis_stats:
            return {
                "success": False,
                "error": f"Task {task_id} not found",
            }

        stats = self._analysis_stats[task_id].copy()

        # Add computed fields
        if stats["status"] == "running":
            elapsed_time = (datetime.now() - stats["start_time"]).total_seconds()
            if stats["processed"] > 0:
                avg_time_per_product = elapsed_time / stats["processed"]
                remaining_products = stats["total_products"] - stats["processed"]
                estimated_remaining = remaining_products * avg_time_per_product
                stats["estimated_remaining_seconds"] = int(estimated_remaining)
            else:
                stats["estimated_remaining_seconds"] = stats["estimated_duration"]

        # Convert datetime objects to ISO strings
        for key in ["start_time", "end_time"]:
            if key in stats and stats[key]:
                stats[key] = stats[key].isoformat()

        return {
            "success": True,
            "progress": stats,
        }

    async def cancel_analysis(self, task_id: str) -> Dict[str, Any]:
        """
        Cancel a running analysis task.

        Args:
            task_id: Task identifier

        Returns:
            Cancellation result
        """
        if task_id not in self._analysis_tasks:
            return {
                "success": False,
                "error": f"Task {task_id} not found",
            }

        try:
            # Cancel the task
            task = self._analysis_tasks[task_id]
            task.cancel()

            # Update stats
            if task_id in self._analysis_stats:
                self._analysis_stats[task_id]["status"] = "cancelled"
                self._analysis_stats[task_id]["end_time"] = datetime.now()

            # Clean up
            del self._analysis_tasks[task_id]

            logger.info(f"Cancelled analysis task {task_id}")

            return {
                "success": True,
                "message": f"Task {task_id} cancelled",
            }

        except Exception as e:
            logger.error(f"Error cancelling task {task_id}: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    async def get_recent_analyses(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get recently analyzed products.

        Args:
            limit: Maximum number of products to return

        Returns:
            List of recently analyzed products
        """
        try:
            connection = await self.db_repo._get_connection()

            query = """
                SELECT sku, title, color, category, material, pattern,
                       season, occasion, updated_at
                FROM products
                WHERE in_stock = 1
                AND color IS NOT NULL AND color != ''
                AND updated_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
                ORDER BY updated_at DESC
                LIMIT %s
            """

            async with connection.cursor() as cursor:
                await cursor.execute(query, [limit])
                rows = await cursor.fetchall()

                products = []
                for row in rows:
                    products.append(
                        {
                            "sku": row[0],
                            "title": row[1],
                            "color": row[2],
                            "category": row[3],
                            "material": row[4],
                            "pattern": row[5],
                            "season": row[6],
                            "occasion": row[7],
                            "analyzed_at": row[8].isoformat() if row[8] else None,
                        }
                    )

                return products

        except Exception as e:
            logger.error(f"Error getting recent analyses: {e}")
            return []
        finally:
            if "connection" in locals():
                await connection.ensure_closed()

    async def _update_product_vision_attributes(
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

                    # Handle enum values
                    if hasattr(value, "value"):
                        value = value.value

                    update_fields.append(f"{db_column} = %s")
                    values.append(value)

            if not update_fields:
                return False

            # Add updated timestamp
            update_fields.append("updated_at = CURRENT_TIMESTAMP")

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
                return cursor.rowcount > 0

        except Exception as e:
            logger.error(f"Error updating vision attributes for {sku}: {e}")
            return False
        finally:
            if "connection" in locals():
                await connection.ensure_closed()

    def cleanup_old_tasks(self, hours: int = 24):
        """
        Clean up old completed/failed tasks.

        Args:
            hours: Remove tasks older than this many hours
        """
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)

            tasks_to_remove = []
            for task_id, stats in self._analysis_stats.items():
                if stats.get("end_time") and stats["end_time"] < cutoff_time:
                    tasks_to_remove.append(task_id)

            for task_id in tasks_to_remove:
                if task_id in self._analysis_stats:
                    del self._analysis_stats[task_id]
                if task_id in self._analysis_tasks:
                    del self._analysis_tasks[task_id]

            if tasks_to_remove:
                logger.info(f"Cleaned up {len(tasks_to_remove)} old analysis tasks")

        except Exception as e:
            logger.error(f"Error cleaning up old tasks: {e}")
