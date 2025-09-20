"""
Ingest API Router

This module handles endpoints for ingesting fashion items
from the shop catalog into the lookbook system.
"""

from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from typing import Dict, Any, Optional, List
import logging
import structlog

from ...domain.entities import IngestRequest, IngestResponse, Item
from ...domain.use_cases import IngestItems
from ...adapters.db_shop import MockShopCatalogAdapter
from ...adapters.vision import MockVisionProvider
from ...adapters.db_lookbook import MockLookbookRepository

router = APIRouter(prefix="/v1/ingest", tags=["ingest"])
logger = structlog.get_logger()


# Initialize dependencies (will be replaced with proper DI in later milestones)
shop_adapter = MockShopCatalogAdapter()
vision_adapter = MockVisionProvider()
lookbook_repo = MockLookbookRepository()
ingest_use_case = IngestItems(shop_adapter, vision_adapter, lookbook_repo)


@router.post("/sync/products", response_model=Dict[str, Any], status_code=status.HTTP_202_ACCEPTED)
async def sync_products(
    request: IngestRequest,
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """
    Sync products from Magento catalog (Step 1: Data Synchronization).

    This endpoint only syncs product data from Magento without image analysis.
    Use this first to get products into the system, then use /analyze/batch.

    Args:
        request: Sync request with limit and since parameters
        background_tasks: FastAPI background tasks for async processing

    Returns:
        Sync results with product IDs and status
    """
    try:
        logger.info("Starting product sync", request=request.dict())

        # Fetch items from shop catalog only (no vision analysis)
        shop_items = await shop_adapter.fetch_items(
            limit=request.limit,
            since=request.since
        )

        # Extract product IDs for the response (handle both dict and Item objects)
        product_ids = []
        for item in shop_items:
            if hasattr(item, 'sku'):
                product_ids.append(item.sku)
            elif isinstance(item, dict) and 'sku' in item:
                product_ids.append(item['sku'])

        logger.info("Product sync completed",
                   products_found=len(shop_items),
                   product_ids=product_ids[:5])  # Log first 5 IDs

        return {
            "status": "synced",
            "products_found": len(shop_items),
            "product_ids": product_ids,
            "message": f"Synced {len(shop_items)} products from catalog. Ready for analysis.",
            "next_step": "Use /analyze/batch to analyze specific products"
        }

    except Exception as e:
        logger.error("Product sync failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Product sync failed: {str(e)}. Check MySQL connection to Magento."
        )


@router.post("/analyze/batch", response_model=Dict[str, Any], status_code=status.HTTP_202_ACCEPTED)
async def analyze_products(
    product_ids: List[str],
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """
    Analyze specific products with Vision AI (Step 2: Image Analysis).

    This endpoint takes product IDs and analyzes their images using the
    Vision Sidecar and LLM to extract color, material, pattern attributes.

    Args:
        product_ids: List of product SKUs to analyze
        background_tasks: FastAPI background tasks for async processing

    Returns:
        Analysis results with processed items
    """
    try:
        logger.info("Starting batch analysis", product_ids=product_ids)

        analyzed_count = 0
        failed_count = 0
        results = []

        for product_id in product_ids:
            try:
                # Get product from shop catalog
                item = await shop_adapter.get_item_by_sku(product_id)
                if not item:
                    logger.warning("Product not found", product_id=product_id)
                    failed_count += 1
                    continue

                # Handle both dict and Item objects for image_key
                if hasattr(item, 'image_key'):
                    image_key = item.image_key
                elif isinstance(item, dict) and 'image_key' in item:
                    image_key = item['image_key']
                else:
                    logger.error("Product missing image_key", product_id=product_id, item=item)
                    failed_count += 1
                    results.append({
                        "product_id": product_id,
                        "status": "failed",
                        "error": "Product missing image_key"
                    })
                    continue

                # Analyze item image with Vision Sidecar
                vision_attrs = await vision_adapter.analyze_image(image_key)

                # Handle both dict and Item objects for Item creation
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
                    size_range = item.get('size_range', {})
                    attributes = item.get('attributes', {})
                    in_stock = item.get('in_stock', True)
                else:
                    logger.error("Invalid item format", product_id=product_id, item=item)
                    failed_count += 1
                    results.append({
                        "product_id": product_id,
                        "status": "failed",
                        "error": "Invalid item format"
                    })
                    continue

                # Save to lookbook database
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

                await lookbook_repo.save_items([enhanced_item])
                analyzed_count += 1

                results.append({
                    "product_id": product_id,
                    "status": "analyzed",
                    "vision_attributes": vision_attrs if isinstance(vision_attrs, dict) else vision_attrs.dict()
                })

                logger.info("Product analyzed successfully", product_id=product_id)

            except Exception as e:
                logger.error("Product analysis failed", product_id=product_id, error=str(e))
                failed_count += 1
                results.append({
                    "product_id": product_id,
                    "status": "failed",
                    "error": str(e)
                })

        logger.info("Batch analysis completed",
                   analyzed=analyzed_count,
                   failed=failed_count,
                   total=len(product_ids))

        return {
            "status": "completed",
            "analyzed_products": analyzed_count,
            "failed_products": failed_count,
            "total_products": len(product_ids),
            "results": results,
            "message": f"Analysis complete: {analyzed_count} successful, {failed_count} failed"
        }

    except Exception as e:
        logger.error("Batch analysis failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch analysis failed: {str(e)}. Check Vision Sidecar connection."
        )


@router.post("/products", response_model=IngestResponse, status_code=status.HTTP_202_ACCEPTED)
async def ingest_products(
    request: IngestRequest,
    background_tasks: BackgroundTasks
) -> IngestResponse:
    """
    Ingest fashion products from the shop catalog.

    This endpoint processes products from the Magento catalog, analyzes them
    using vision AI, and stores them in the lookbook database.

    Args:
        request: Ingestion request with optional limit and since parameters
        background_tasks: FastAPI background tasks for async processing

    Returns:
        IngestResponse with processing status and results

    Raises:
        HTTPException: If ingestion fails
    """
    try:
        logger.info("Starting product ingestion", request=request.dict())

        # Execute ingestion use case
        response = await ingest_use_case.execute(request)

        # Log completion
        logger.info("Product ingestion completed",
                   status=response.status,
                   items_processed=response.items_processed)

        return response

    except Exception as e:
        logger.error("Product ingestion failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ingestion failed: {str(e)}. Check: 1) MySQL connection, 2) Vision Sidecar, 3) Image URLs"
        )


@router.get("/status/{request_id}")
async def get_ingest_status(request_id: str) -> Dict[str, Any]:
    """
    Get the status of a previous ingestion request.

    Args:
        request_id: Unique identifier for the ingestion request

    Returns:
        Status information for the ingestion request

    Raises:
        HTTPException: If request_id is not found
    """
    try:
        logger.info("Checking ingest status", request_id=request_id)

        # Mock status response (in real implementation, this would query a job queue)
        status_response = {
            "request_id": request_id,
            "status": "completed",
            "items_processed": 25,
            "timestamp": "2025-01-19T14:00:00Z",
            "details": {
                "total_found": 30,
                "successfully_processed": 25,
                "failed": 5,
                "errors": ["Image analysis timeout", "Invalid SKU format"]
            }
        }

        return status_response

    except Exception as e:
        logger.error("Error checking ingest status", request_id=request_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Status check failed: {str(e)}"
        )


@router.get("/products")
async def list_ingested_products(
    limit: Optional[int] = 10,
    offset: Optional[int] = 0,
    category: Optional[str] = None
) -> Dict[str, Any]:
    """
    List ingested products with optional filtering.

    Args:
        limit: Maximum number of products to return (default: 10)
        offset: Number of products to skip (default: 0)
        category: Filter by category (optional)

    Returns:
        Dictionary with products and pagination info
    """
    try:
        logger.info("Listing ingested products", limit=limit, offset=offset, category=category)

        # Mock response (in real implementation, this would query the database)
        products_response = {
            "products": [
                {
                    "id": 1,
                    "sku": "1295990003",
                    "title": "Classic Cotton T-Shirt",
                    "price": 29.99,
                    "category": "top",
                    "color": "white",
                    "image_url": "https://example.com/images/e341e2f3a4b5c6d7e8f9.jpg",
                    "ingested_at": "2025-01-19T14:00:00Z"
                },
                {
                    "id": 2,
                    "sku": "1295990011",
                    "title": "Slim Fit Jeans",
                    "price": 79.99,
                    "category": "bottom",
                    "color": "blue",
                    "image_url": "https://example.com/images/f567g8h9i0j1k2l3m4n5.jpg",
                    "ingested_at": "2025-01-19T14:00:00Z"
                }
            ],
            "pagination": {
                "total": 150,
                "limit": limit,
                "offset": offset,
                "has_more": offset + limit < 150
            }
        }

        return products_response

    except Exception as e:
        logger.error("Error listing ingested products", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list products: {str(e)}"
        )


@router.delete("/products/{product_id}")
async def delete_ingested_product(product_id: int) -> Dict[str, Any]:
    """
    Delete a specific ingested product.

    Args:
        product_id: ID of the product to delete

    Returns:
        Deletion confirmation

    Raises:
        HTTPException: If product is not found or deletion fails
    """
    try:
        logger.info("Deleting ingested product", product_id=product_id)

        # Mock deletion (in real implementation, this would delete from database)
        return {
            "message": "Product deleted successfully",
            "product_id": product_id,
            "deleted_at": "2025-01-19T14:00:00Z"
        }

    except Exception as e:
        logger.error("Error deleting product", product_id=product_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete product: {str(e)}"
        )


@router.get("/stats")
async def get_ingestion_stats() -> Dict[str, Any]:
    """
    Get ingestion statistics.

    Returns:
        Statistics about ingested items
    """
    try:
        logger.info("Getting ingestion statistics")

        # Mock statistics (in real implementation, this would query database)
        stats_response = {
            "total_items": 150,
            "by_category": {
                "top": 45,
                "bottom": 38,
                "dress": 22,
                "outerwear": 18,
                "shoes": 15,
                "accessory": 12
            },
            "by_color": {
                "black": 35,
                "white": 28,
                "blue": 22,
                "grey": 18,
                "red": 15,
                "other": 32
            },
            "by_price_range": {
                "under_30": 45,
                "30_50": 38,
                "50_100": 42,
                "over_100": 25
            },
            "last_ingestion": "2025-01-19T14:00:00Z",
            "items_processed_today": 25
        }

        return stats_response

    except Exception as e:
        logger.error("Error getting ingestion statistics", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get statistics: {str(e)}"
        )