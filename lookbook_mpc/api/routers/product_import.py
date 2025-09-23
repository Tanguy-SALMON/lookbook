"""
Product Import API Router

This router provides endpoints for managing product import jobs from Magento DB.
"""

import asyncio
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, validator
import structlog

from lookbook_mpc.services.product_import_service import ProductImportService
from lookbook_mpc.adapters.db_product_import import MySQLProductImportRepository
from lookbook_mpc.adapters.db_shop import MySQLShopCatalogAdapter
from lookbook_mpc.adapters.db_lookbook import MySQLLookbookRepository
from lookbook_mpc.config.settings import get_settings

logger = structlog.get_logger()
router = APIRouter(prefix="/api/admin/product-import", tags=["product-import"])

# Global service instance (should be injected properly in production)
_service_instance = None

def get_product_import_service() -> ProductImportService:
    """Get or create product import service instance."""
    global _service_instance
    if _service_instance is None:
        settings = get_settings()
        import_repo = MySQLProductImportRepository(settings.lookbook_db_url)
        shop_adapter = MySQLShopCatalogAdapter(settings.mysql_shop_url)
        lookbook_repo = MySQLLookbookRepository(settings.lookbook_db_url)
        _service_instance = ProductImportService(import_repo, shop_adapter, lookbook_repo)
    return _service_instance

# Pydantic models
class CreateImportJobRequest(BaseModel):
    limit: int = 100
    resumeFromLast: bool = True
    startAfterId: int = None

    @validator('limit')
    def validate_limit(cls, v):
        if v < 1 or v > 1000:
            raise ValueError('Limit must be between 1 and 1000')
        return v

    @validator('startAfterId')
    def validate_start_after_id(cls, v, values):
        if not values.get('resumeFromLast', True) and v is None:
            raise ValueError('startAfterId is required when resumeFromLast is false')
        return v

class CreateImportJobResponse(BaseModel):
    jobId: str

class ImportJobResponse(BaseModel):
    id: str
    status: str
    params: Dict[str, Any]
    metrics: Dict[str, Any]
    created_at: str
    started_at: str = None
    finished_at: str = None
    error_message: str = None

@router.post("/jobs", response_model=CreateImportJobResponse)
async def create_import_job(
    request: CreateImportJobRequest,
    background_tasks: BackgroundTasks
):
    """
    Create a new product import job.

    This endpoint creates a job and starts it in the background.
    """
    try:
        service = get_product_import_service()

        # Create job
        job_id = await service.create_job(request.dict())

        # Start job in background
        background_tasks.add_task(run_import_job_background, job_id)

        logger.info("Created product import job", job_id=job_id)
        return CreateImportJobResponse(jobId=job_id)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Failed to create import job", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to create import job")

@router.get("/jobs/{job_id}", response_model=ImportJobResponse)
async def get_import_job(job_id: str):
    """
    Get the status and details of an import job.
    """
    try:
        service = get_product_import_service()
        job = await service.import_repo.get_job(job_id)

        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        return ImportJobResponse(**job)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get import job", job_id=job_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get import job")

async def run_import_job_background(job_id: str):
    """
    Background task to run an import job.
    """
    try:
        service = get_product_import_service()
        await service.run_job(job_id)
        logger.info("Background import job completed", job_id=job_id)
    except Exception as e:
        logger.error("Background import job failed", job_id=job_id, error=str(e))