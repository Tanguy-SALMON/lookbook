"""
Product Import Service

Handles the business logic for importing products from Magento DB to the app DB.
Manages job lifecycle, progress tracking, and error handling.
"""

import asyncio
import time
from typing import Dict, Any, Optional
from datetime import datetime
import logging
import structlog

from ..adapters.db_product_import import MySQLProductImportRepository
from ..adapters.db_shop import ShopCatalogAdapter
from ..adapters.db_lookbook import MySQLLookbookRepository

logger = structlog.get_logger()


class ProductImportService:
    """
    Service for managing product import jobs.

    Handles job creation, execution, progress tracking, and metadata management.
    """

    def __init__(
        self,
        import_repo: MySQLProductImportRepository,
        shop_adapter: ShopCatalogAdapter,
        lookbook_repo: MySQLLookbookRepository
    ):
        self.import_repo = import_repo
        self.shop_adapter = shop_adapter
        self.lookbook_repo = lookbook_repo
        self.logger = logger.bind(service="product_import")

    async def create_job(self, params: Dict[str, Any]) -> str:
        """
        Create a new import job.

        Args:
            params: Job parameters (limit, resumeFromLast, startAfterId)

        Returns:
            Job ID (UUID)
        """
        try:
            self.logger.info("Creating product import job", params=params)

            # Validate parameters
            limit = params.get("limit", 100)
            if limit < 1 or limit > 1000:
                raise ValueError("Limit must be between 1 and 1000")

            resume_from_last = params.get("resumeFromLast", True)
            start_after_id = params.get("startAfterId")

            if not resume_from_last and start_after_id is None:
                raise ValueError("startAfterId is required when resumeFromLast is false")

            # Create job record
            job_id = await self.import_repo.create_job(params)

            self.logger.info("Product import job created", job_id=job_id)
            return job_id

        except Exception as e:
            self.logger.error("Failed to create import job", error=str(e))
            raise

    async def run_job(self, job_id: str) -> None:
        """
        Execute an import job.

        Args:
            job_id: Job identifier
        """
        start_time = time.time()
        try:
            self.logger.info("Starting product import job", job_id=job_id)

            # Get job details
            job = await self.import_repo.get_job(job_id)
            if not job:
                raise ValueError(f"Job {job_id} not found")

            if job["status"] != "queued":
                raise ValueError(f"Job {job_id} is not in queued status")

            # Update job to running
            await self.import_repo.update_job_status(
                job_id,
                "running",
                started_at=datetime.utcnow().isoformat()
            )

            # Resolve startAfterId
            params = job["params"]
            resume_from_last = params.get("resumeFromLast", True)
            start_after_id = params.get("startAfterId")

            if resume_from_last:
                # Get last successful source ID from metadata
                last_id_str = await self.import_repo.get_meta("last_successful_source_id")
                start_after_id = int(last_id_str) if last_id_str else 0
                self.logger.info("Resuming from last successful ID", start_after_id=start_after_id)
            else:
                start_after_id = int(start_after_id) if start_after_id else 0

            # Fetch products from source
            limit = params.get("limit", 100)
            self.logger.info("Fetching products from source",
                           start_after_id=start_after_id, limit=limit)

            products = await self.shop_adapter.get_enabled_products_with_stock(
                start_after_id=start_after_id,
                limit=limit
            )

            self.logger.info("Fetched products from source", count=len(products))

            # Transform products for upsert
            transformed_products = []
            max_source_id = start_after_id

            for product in products:
                try:
                    # Transform product data (similar to sync_100_products.py logic)
                    transformed = self._transform_product(product)
                    transformed_products.append(transformed)
                    max_source_id = max(max_source_id, product.get("source_id", 0))
                except Exception as e:
                    self.logger.warning("Failed to transform product",
                                      sku=product.get("sku"), error=str(e))
                    continue

            # Batch upsert products
            self.logger.info("Upserting products to lookbook DB", count=len(transformed_products))

            upsert_result = await self.lookbook_repo.batch_upsert_products(transformed_products)

            # Calculate metrics
            processed = len(products)
            inserted = upsert_result.get("upserted", 0)
            updated = upsert_result.get("updated", 0)
            elapsed_ms = int((time.time() - start_time) * 1000)

            metrics = {
                "total_found": len(products),
                "processed": processed,
                "inserted": inserted,
                "updated": updated,
                "skipped": 0,  # Not filtering during transform for this demo
                "errors_count": len(products) - len(transformed_products),
                "elapsed_ms": elapsed_ms,
                "last_processed_source_id": max_source_id if products else None
            }

            # Update job metrics
            await self.import_repo.update_job_metrics(job_id, metrics)

            # Update metadata cursor if we processed products
            if products:
                await self.import_repo.set_meta("last_successful_source_id", str(max_source_id))

            # Complete job
            await self.import_repo.update_job_status(
                job_id,
                "completed",
                finished_at=datetime.utcnow().isoformat()
            )

            self.logger.info("Product import job completed successfully",
                           job_id=job_id, metrics=metrics)

        except Exception as e:
            elapsed_ms = int((time.time() - start_time) * 1000)
            error_msg = str(e)

            self.logger.error("Product import job failed",
                            job_id=job_id, error=error_msg, elapsed_ms=elapsed_ms)

            # Update job to failed
            await self.import_repo.update_job_status(
                job_id,
                "failed",
                finished_at=datetime.utcnow().isoformat(),
                error_message=error_msg
            )
            raise

    def _transform_product(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform product data from source format to lookbook format.

        Args:
            product: Raw product data from source

        Returns:
            Transformed product data
        """
        # Handle None values safely
        def safe_str(value, default=""):
            return str(value) if value is not None else default

        def safe_int(value, default=0):
            try:
                return int(value) if value is not None else default
            except (ValueError, TypeError):
                return default

        def safe_float(value, default=0.0):
            try:
                return float(value) if value is not None else default
            except (ValueError, TypeError):
                return default

        # Transform basic fields
        transformed = {
            "sku": safe_str(product.get("sku")),
            "title": safe_str(product.get("title")),
            "price": safe_float(product.get("price")),
            "size_range": product.get("size_range") or [],
            "image_key": safe_str(product.get("image_key")),
            "attributes": product.get("attributes") or {},
            "in_stock": True,  # Since we filter for stock_qty > 0
            "season": safe_str(product.get("season")),
            "url_key": safe_str(product.get("url_key")),
            "product_created_at": product.get("product_created_at"),
            "stock_qty": safe_int(product.get("stock_qty")),
            "category": safe_str(product.get("category")),
            "color": safe_str(product.get("color")),
            "material": safe_str(product.get("material")),
            "pattern": safe_str(product.get("pattern")),
            "occasion": safe_str(product.get("occasion")),
        }

        # Ensure required fields are present
        if not transformed["sku"]:
            raise ValueError("Product missing SKU")

        if not transformed["title"]:
            raise ValueError("Product missing title")

        if not transformed["image_key"]:
            raise ValueError("Product missing image_key")

        return transformed