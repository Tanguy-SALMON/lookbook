"""
Akeneo Export Jobs API Router

This router provides CRUD operations for Akeneo export jobs.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import structlog
import json
from datetime import datetime
import uuid

from lookbook_mpc.adapters.database import get_db_connection
from lookbook_mpc.config.settings import get_settings

logger = structlog.get_logger()
router = APIRouter(prefix="/v1/admin/akeneo/export", tags=["akeneo-export"])

# Pydantic models
class AkeneoExportJobIn(BaseModel):
    name: str
    description: Optional[str] = None
    config: Dict[str, Any]
    lookbook_ids: Optional[List[str]] = None

class AkeneoExportJob(BaseModel):
    id: str
    name: str
    description: Optional[str]
    status: str
    config: Dict[str, Any]
    lookbook_ids: Optional[List[str]]
    total_items: int
    processed_items: int
    errors: List[Dict[str, Any]]
    created_at: str
    started_at: Optional[str]
    completed_at: Optional[str]
    created_by: str

    @classmethod
    def from_db(cls, data: dict):
        """Create AkeneoExportJob from database data."""
        return cls(
            id=data['id'],
            name=data['name'],
            description=data['description'],
            status=data['status'],
            config=json.loads(data['config']) if data['config'] else {},
            lookbook_ids=json.loads(data['lookbook_ids']) if data['lookbook_ids'] else None,
            total_items=data['total_items'],
            processed_items=data['processed_items'],
            errors=json.loads(data['errors']) if data['errors'] else [],
            created_at=data['created_at'].isoformat() if data['created_at'] else None,
            started_at=data['started_at'].isoformat() if data['started_at'] else None,
            completed_at=data['completed_at'].isoformat() if data['completed_at'] else None,
            created_by=data['created_by']
        )

@router.get("/", response_model=List[AkeneoExportJob])
async def get_export_jobs(
    limit: int = 100,
    offset: int = 0,
    status: Optional[str] = None
):
    """Get all export jobs with optional filtering."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Build query
        query = "SELECT * FROM akeneo_export_jobs WHERE 1=1"
        params = []

        if status:
            query += " AND status = %s"
            params.append(status)

        query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        cursor.execute(query, params)
        jobs = cursor.fetchall()

        cursor.close()
        conn.close()

        return [AkeneoExportJob.from_db(job) for job in jobs]

    except Exception as e:
        logger.error("Error fetching export jobs", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch export jobs")

@router.post("/", response_model=AkeneoExportJob)
async def create_export_job(job_in: AkeneoExportJobIn):
    """Create a new export job."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Generate UUID
        job_id = str(uuid.uuid4())

        # Insert job
        query = """
            INSERT INTO akeneo_export_jobs (
                id, name, description, config, lookbook_ids, created_by
            ) VALUES (%s, %s, %s, %s, %s, %s)
        """
        params = [
            job_id,
            job_in.name,
            job_in.description,
            json.dumps(job_in.config),
            json.dumps(job_in.lookbook_ids) if job_in.lookbook_ids else None,
            "admin"  # TODO: Get from auth
        ]

        cursor.execute(query, params)
        conn.commit()

        # Get created job
        cursor.execute("SELECT * FROM akeneo_export_jobs WHERE id = %s", (job_id,))
        created_job = cursor.fetchone()

        cursor.close()
        conn.close()

        return AkeneoExportJob.from_db(created_job)

    except Exception as e:
        logger.error("Error creating export job", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to create export job")

@router.get("/{job_id}", response_model=AkeneoExportJob)
async def get_export_job(job_id: str):
    """Get a specific export job by ID."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM akeneo_export_jobs WHERE id = %s", (job_id,))
        job = cursor.fetchone()

        if not job:
            raise HTTPException(status_code=404, detail="Export job not found")

        cursor.close()
        conn.close()

        return AkeneoExportJob.from_db(job)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching export job", job_id=job_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch export job")

@router.put("/{job_id}", response_model=AkeneoExportJob)
async def update_export_job(job_id: str, job_in: AkeneoExportJobIn):
    """Update an existing export job."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if job exists
        cursor.execute("SELECT * FROM akeneo_export_jobs WHERE id = %s", (job_id,))
        existing_job = cursor.fetchone()

        if not existing_job:
            raise HTTPException(status_code=404, detail="Export job not found")

        # Build update query
        update_fields = []
        values = []

        update_data = job_in.dict(exclude_unset=True)

        for field, value in update_data.items():
            if field in ['config', 'lookbook_ids']:
                update_fields.append(f"{field} = %s")
                values.append(json.dumps(value))
            else:
                update_fields.append(f"{field} = %s")
                values.append(value)

        if update_fields:
            values.append(job_id)
            query = f"UPDATE akeneo_export_jobs SET {', '.join(update_fields)} WHERE id = %s"
            cursor.execute(query, values)

        conn.commit()

        # Get updated job
        cursor.execute("SELECT * FROM akeneo_export_jobs WHERE id = %s", (job_id,))
        updated_job = cursor.fetchone()

        cursor.close()
        conn.close()

        return AkeneoExportJob.from_db(updated_job)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error updating export job", job_id=job_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to update export job")

@router.delete("/{job_id}")
async def delete_export_job(job_id: str):
    """Delete an export job."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if job exists
        cursor.execute("SELECT * FROM akeneo_export_jobs WHERE id = %s", (job_id,))
        existing_job = cursor.fetchone()

        if not existing_job:
            raise HTTPException(status_code=404, detail="Export job not found")

        # Delete job
        cursor.execute("DELETE FROM akeneo_export_jobs WHERE id = %s", (job_id,))
        conn.commit()

        cursor.close()
        conn.close()

        return {"message": "Export job deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error deleting export job", job_id=job_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to delete export job")

@router.post("/{job_id}/execute")
async def execute_export_job(job_id: str):
    """Execute an export job (stub implementation)."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if job exists
        cursor.execute("SELECT * FROM akeneo_export_jobs WHERE id = %s", (job_id,))
        job = cursor.fetchone()

        if not job:
            raise HTTPException(status_code=404, detail="Export job not found")

        # Update status to running
        cursor.execute("""
            UPDATE akeneo_export_jobs SET
                status = 'running',
                started_at = NOW()
            WHERE id = %s
        """, (job_id,))

        # Simulate processing (in real implementation, this would be async)
        # For now, just mark as completed
        cursor.execute("""
            UPDATE akeneo_export_jobs SET
                status = 'completed',
                completed_at = NOW(),
                processed_items = total_items
            WHERE id = %s
        """, (job_id,))

        conn.commit()

        cursor.close()
        conn.close()

        return {"message": "Export job executed successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error executing export job", job_id=job_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to execute export job")