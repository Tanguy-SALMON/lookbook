"""
Vision Analysis API Router

API endpoints for managing product vision analysis from the admin panel.
Provides endpoints to start, monitor, and manage vision analysis tasks.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import logging

from ...services.vision_analysis_service import VisionAnalysisService
from ...core.auth import get_current_admin_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/vision-analysis", tags=["Vision Analysis"])

# Initialize service
vision_service = VisionAnalysisService()


# Request/Response Models
class BatchAnalysisRequest(BaseModel):
    """Request model for starting batch analysis."""

    limit: Optional[int] = None
    batch_size: int = 5


class AnalysisStatsResponse(BaseModel):
    """Response model for analysis statistics."""

    total_products: int
    analyzed_products: int
    missing_analysis: int
    analysis_coverage: float
    recent_analysis: int
    category_breakdown: Dict[str, int]
    color_breakdown: Dict[str, int]
    last_updated: str


class ProductNeedingAnalysis(BaseModel):
    """Model for products that need analysis."""

    sku: str
    title: str
    image_key: Optional[str]
    price: float
    color: Optional[str]
    category: Optional[str]
    material: Optional[str]
    pattern: Optional[str]
    season: Optional[str]
    occasion: Optional[str]
    created_at: Optional[str]
    missing_attributes: List[str]
    analysis_needed: bool


class RecentAnalysis(BaseModel):
    """Model for recently analyzed products."""

    sku: str
    title: str
    color: Optional[str]
    category: Optional[str]
    material: Optional[str]
    pattern: Optional[str]
    season: Optional[str]
    occasion: Optional[str]
    analyzed_at: Optional[str]


class TaskProgress(BaseModel):
    """Model for task progress information."""

    task_id: str
    status: str
    total_products: int
    processed: int
    successful: int
    failed: int
    progress_percentage: float
    current_batch: int
    batch_size: int
    start_time: str
    end_time: Optional[str]
    user_id: Optional[str]
    estimated_remaining_seconds: Optional[int]
    errors: List[Dict[str, str]]


@router.get("/stats", response_model=AnalysisStatsResponse)
async def get_analysis_statistics(current_user: Dict = Depends(get_current_admin_user)):
    """
    Get overall vision analysis statistics.

    Returns statistics about:
    - Total products vs analyzed products
    - Analysis coverage percentage
    - Recent analysis activity
    - Breakdown by category and color
    """
    try:
        stats = await vision_service.get_analysis_statistics()

        if "error" in stats:
            raise HTTPException(status_code=500, detail=stats["error"])

        return AnalysisStatsResponse(**stats)

    except Exception as e:
        logger.error(f"Error getting analysis statistics: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get statistics: {str(e)}"
        )


@router.get("/products/needing-analysis", response_model=List[ProductNeedingAnalysis])
async def get_products_needing_analysis(
    limit: int = 50, current_user: Dict = Depends(get_current_admin_user)
):
    """
    Get products that need vision analysis.

    Args:
        limit: Maximum number of products to return (default: 50)

    Returns:
        List of products missing vision attributes
    """
    try:
        products = await vision_service.get_products_needing_analysis(limit=limit)
        return [ProductNeedingAnalysis(**product) for product in products]

    except Exception as e:
        logger.error(f"Error getting products needing analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get products: {str(e)}")


@router.post("/start-batch")
async def start_batch_analysis(
    request: BatchAnalysisRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict = Depends(get_current_admin_user),
):
    """
    Start a batch vision analysis process.

    Args:
        request: Batch analysis configuration
        background_tasks: FastAPI background tasks
        current_user: Current admin user info

    Returns:
        Task information including task_id for tracking progress
    """
    try:
        # Start the batch analysis
        result = await vision_service.start_batch_analysis(
            limit=request.limit,
            batch_size=request.batch_size,
            user_id=current_user.get("id") or current_user.get("username", "unknown"),
        )

        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])

        # Schedule cleanup of old tasks
        background_tasks.add_task(vision_service.cleanup_old_tasks, hours=24)

        logger.info(
            f"Batch analysis started by {current_user.get('username', 'unknown')}: {result['task_id']}"
        )

        return {
            "success": True,
            "task_id": result["task_id"],
            "total_products": result["total_products"],
            "estimated_duration_seconds": result["estimated_duration"],
            "message": result["message"],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting batch analysis: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to start analysis: {str(e)}"
        )


@router.get("/progress/{task_id}", response_model=Dict[str, Any])
async def get_analysis_progress(
    task_id: str, current_user: Dict = Depends(get_current_admin_user)
):
    """
    Get progress information for a running analysis task.

    Args:
        task_id: The task identifier returned when starting analysis

    Returns:
        Current progress information including percentage complete, products processed, etc.
    """
    try:
        result = await vision_service.get_analysis_progress(task_id)

        if not result["success"]:
            raise HTTPException(status_code=404, detail=result["error"])

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting analysis progress: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get progress: {str(e)}")


@router.post("/cancel/{task_id}")
async def cancel_analysis(
    task_id: str, current_user: Dict = Depends(get_current_admin_user)
):
    """
    Cancel a running analysis task.

    Args:
        task_id: The task identifier to cancel

    Returns:
        Cancellation confirmation
    """
    try:
        result = await vision_service.cancel_analysis(task_id)

        if not result["success"]:
            raise HTTPException(status_code=404, detail=result["error"])

        logger.info(
            f"Analysis task {task_id} cancelled by {current_user.get('username', 'unknown')}"
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling analysis: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to cancel analysis: {str(e)}"
        )


@router.get("/recent", response_model=List[RecentAnalysis])
async def get_recent_analyses(
    limit: int = 20, current_user: Dict = Depends(get_current_admin_user)
):
    """
    Get recently analyzed products (last 7 days).

    Args:
        limit: Maximum number of products to return (default: 20)

    Returns:
        List of recently analyzed products with their vision attributes
    """
    try:
        products = await vision_service.get_recent_analyses(limit=limit)
        return [RecentAnalysis(**product) for product in products]

    except Exception as e:
        logger.error(f"Error getting recent analyses: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get recent analyses: {str(e)}"
        )


@router.get("/health")
async def vision_analysis_health():
    """
    Health check endpoint for vision analysis system.

    Returns:
        Health status information
    """
    try:
        # Check if Ollama is accessible
        from ....image.vision_analyzer import VisionAnalyzer

        # Try to initialize vision analyzer
        vision_analyzer = VisionAnalyzer(model="qwen2.5vl:latest", save_processed=False)

        # Get basic stats
        stats = await vision_service.get_analysis_statistics()

        return {
            "status": "healthy",
            "vision_model": "qwen2.5vl:latest",
            "ollama_accessible": True,  # If we get here, it's accessible
            "database_accessible": "error" not in stats,
            "total_products": stats.get("total_products", 0),
            "analyzed_products": stats.get("analyzed_products", 0),
            "last_check": "2024-01-01T00:00:00",
        }

    except Exception as e:
        logger.warning(f"Vision analysis health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "vision_model": "qwen2.5vl:latest",
            "ollama_accessible": False,
            "database_accessible": False,
            "last_check": "2024-01-01T00:00:00",
        }


# Additional utility endpoints


@router.get("/models/available")
async def get_available_models(current_user: Dict = Depends(get_current_admin_user)):
    """
    Get list of available vision models.

    Returns:
        List of available Ollama vision models
    """
    try:
        # In a real implementation, you'd query Ollama for available models
        return {
            "available_models": [
                {
                    "name": "qwen2.5vl:latest",
                    "description": "Qwen 2.5 Vision Language Model - Latest version",
                    "size": "~7GB",
                    "recommended": True,
                },
                {
                    "name": "llava:latest",
                    "description": "LLaVA Vision Language Model",
                    "size": "~4GB",
                    "recommended": False,
                },
            ],
            "current_model": "qwen2.5vl:latest",
        }

    except Exception as e:
        logger.error(f"Error getting available models: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get models: {str(e)}")


@router.get("/categories/supported")
async def get_supported_categories():
    """
    Get list of supported product categories for vision analysis.

    Returns:
        List of supported categories and their descriptions
    """
    from ...domain.entities import Category, Material, Pattern, Season, Occasion, Fit

    return {
        "categories": [{"value": cat.value, "name": cat.name} for cat in Category],
        "materials": [{"value": mat.value, "name": mat.name} for mat in Material],
        "patterns": [{"value": pat.value, "name": pat.name} for pat in Pattern],
        "seasons": [{"value": sea.value, "name": sea.name} for sea in Season],
        "occasions": [{"value": occ.value, "name": occ.name} for occ in Occasion],
        "fits": [{"value": fit.value, "name": fit.name} for fit in Fit],
    }
