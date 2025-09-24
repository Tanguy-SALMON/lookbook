"""
Lookbooks API Router

This router provides CRUD operations for lookbooks and their products, with Akeneo integration.
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
router = APIRouter(prefix="/v1/lookbooks", tags=["lookbooks"])

# Pydantic models
class LookbookIn(BaseModel):
    slug: str
    title: str
    description: Optional[str] = None
    cover_image_key: Optional[str] = None
    is_active: Optional[bool] = True
    akeneo_lookbook_id: Optional[str] = None
    akeneo_score: Optional[float] = None
    akeneo_last_update: Optional[datetime] = None
    akeneo_sync_status: Optional[str] = 'never'
    akeneo_last_error: Optional[str] = None

class Lookbook(BaseModel):
    id: str
    slug: str
    title: str
    description: Optional[str]
    cover_image_key: Optional[str]
    is_active: bool
    akeneo_lookbook_id: Optional[str]
    akeneo_score: Optional[float]
    akeneo_last_update: Optional[datetime]
    akeneo_sync_status: str
    akeneo_last_error: Optional[str]
    created_at: str
    updated_at: str

    @classmethod
    def from_db(cls, data: dict):
        """Create Lookbook from database data."""
        return cls(
            id=data['id'],
            slug=data['slug'],
            title=data['title'],
            description=data['description'],
            cover_image_key=data['cover_image_key'],
            is_active=bool(data['is_active']),
            akeneo_lookbook_id=data['akeneo_lookbook_id'],
            akeneo_score=float(data['akeneo_score']) if data['akeneo_score'] is not None else None,
            akeneo_last_update=data['akeneo_last_update'],
            akeneo_sync_status=data['akeneo_sync_status'],
            akeneo_last_error=data['akeneo_last_error'],
            created_at=data['created_at'].isoformat() if data['created_at'] else None,
            updated_at=data['updated_at'].isoformat() if data['updated_at'] else None
        )

class LookbookProductIn(BaseModel):
    product_sku: str
    position: Optional[int] = 0
    note: Optional[str] = None

class LookbookProduct(BaseModel):
    lookbook_id: str
    product_sku: str
    position: int
    note: Optional[str]

    @classmethod
    def from_db(cls, data: dict):
        """Create LookbookProduct from database data."""
        return cls(
            lookbook_id=data['lookbook_id'],
            product_sku=data['product_sku'],
            position=data['position'],
            note=data['note']
        )

class LinkAkeneoIn(BaseModel):
    akeneo_lookbook_id: str

@router.get("/", response_model=List[Lookbook])
async def get_lookbooks(
    limit: int = 100,
    offset: int = 0,
    q: Optional[str] = None
):
    """Get all lookbooks with optional search."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Build query
        query = "SELECT * FROM lookbooks WHERE 1=1"
        params = []

        if q:
            query += " AND (title LIKE %s OR slug LIKE %s OR description LIKE %s)"
            search_param = f"%{q}%"
            params.extend([search_param, search_param, search_param])

        query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        cursor.execute(query, params)
        lookbooks = cursor.fetchall()

        cursor.close()
        conn.close()

        return [Lookbook.from_db(lb) for lb in lookbooks]

    except Exception as e:
        logger.error("Error fetching lookbooks", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch lookbooks")

@router.post("/", response_model=Lookbook)
async def create_lookbook(lookbook_in: LookbookIn):
    """Create a new lookbook."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Generate UUID
        lookbook_id = str(uuid.uuid4())

        # Insert lookbook
        query = """
            INSERT INTO lookbooks (
                id, slug, title, description, cover_image_key, is_active,
                akeneo_lookbook_id, akeneo_score, akeneo_last_update,
                akeneo_sync_status, akeneo_last_error
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = [
            lookbook_id,
            lookbook_in.slug,
            lookbook_in.title,
            lookbook_in.description,
            lookbook_in.cover_image_key,
            lookbook_in.is_active,
            lookbook_in.akeneo_lookbook_id,
            lookbook_in.akeneo_score,
            lookbook_in.akeneo_last_update,
            lookbook_in.akeneo_sync_status,
            lookbook_in.akeneo_last_error
        ]

        cursor.execute(query, params)
        conn.commit()

        # Get created lookbook
        cursor.execute("SELECT * FROM lookbooks WHERE id = %s", (lookbook_id,))
        created_lookbook = cursor.fetchone()

        cursor.close()
        conn.close()

        return Lookbook.from_db(created_lookbook)

    except Exception as e:
        logger.error("Error creating lookbook", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to create lookbook")

@router.get("/{lookbook_id}", response_model=Lookbook)
async def get_lookbook(lookbook_id: str):
    """Get a specific lookbook by ID."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM lookbooks WHERE id = %s", (lookbook_id,))
        lookbook = cursor.fetchone()

        if not lookbook:
            raise HTTPException(status_code=404, detail="Lookbook not found")

        cursor.close()
        conn.close()

        return Lookbook.from_db(lookbook)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching lookbook", lookbook_id=lookbook_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch lookbook")

@router.put("/{lookbook_id}", response_model=Lookbook)
async def update_lookbook(lookbook_id: str, lookbook_in: LookbookIn):
    """Update an existing lookbook."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if lookbook exists
        cursor.execute("SELECT * FROM lookbooks WHERE id = %s", (lookbook_id,))
        existing_lookbook = cursor.fetchone()

        if not existing_lookbook:
            raise HTTPException(status_code=404, detail="Lookbook not found")

        # Build update query
        update_fields = []
        values = []

        update_data = lookbook_in.dict(exclude_unset=True)

        for field, value in update_data.items():
            update_fields.append(f"{field} = %s")
            values.append(value)

        if update_fields:
            values.append(lookbook_id)
            query = f"UPDATE lookbooks SET {', '.join(update_fields)}, updated_at = NOW() WHERE id = %s"
            cursor.execute(query, values)

        conn.commit()

        # Get updated lookbook
        cursor.execute("SELECT * FROM lookbooks WHERE id = %s", (lookbook_id,))
        updated_lookbook = cursor.fetchone()

        cursor.close()
        conn.close()

        return Lookbook.from_db(updated_lookbook)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error updating lookbook", lookbook_id=lookbook_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to update lookbook")

@router.delete("/{lookbook_id}")
async def delete_lookbook(lookbook_id: str):
    """Delete a lookbook."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if lookbook exists
        cursor.execute("SELECT * FROM lookbooks WHERE id = %s", (lookbook_id,))
        existing_lookbook = cursor.fetchone()

        if not existing_lookbook:
            raise HTTPException(status_code=404, detail="Lookbook not found")

        # Delete lookbook (products will be deleted via CASCADE)
        cursor.execute("DELETE FROM lookbooks WHERE id = %s", (lookbook_id,))
        conn.commit()

        cursor.close()
        conn.close()

        return {"message": "Lookbook deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error deleting lookbook", lookbook_id=lookbook_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to delete lookbook")

@router.get("/{lookbook_id}/products", response_model=List[LookbookProduct])
async def get_lookbook_products(lookbook_id: str):
    """Get products for a specific lookbook."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if lookbook exists
        cursor.execute("SELECT id FROM lookbooks WHERE id = %s", (lookbook_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Lookbook not found")

        cursor.execute("SELECT * FROM lookbook_products WHERE lookbook_id = %s ORDER BY position", (lookbook_id,))
        products = cursor.fetchall()

        cursor.close()
        conn.close()

        return [LookbookProduct.from_db(p) for p in products]

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching lookbook products", lookbook_id=lookbook_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch lookbook products")

@router.post("/{lookbook_id}/products", response_model=LookbookProduct)
async def add_lookbook_product(lookbook_id: str, product_in: LookbookProductIn):
    """Add a product to a lookbook."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if lookbook exists
        cursor.execute("SELECT id FROM lookbooks WHERE id = %s", (lookbook_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Lookbook not found")

        # Check if product exists in products table
        cursor.execute("SELECT sku FROM products WHERE sku = %s", (product_in.product_sku,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Product not found")

        # Check if already exists
        cursor.execute("SELECT * FROM lookbook_products WHERE lookbook_id = %s AND product_sku = %s",
                      (lookbook_id, product_in.product_sku))
        if cursor.fetchone():
            raise HTTPException(status_code=409, detail="Product already in lookbook")

        # Insert product
        query = "INSERT INTO lookbook_products (lookbook_id, product_sku, position, note) VALUES (%s, %s, %s, %s)"
        cursor.execute(query, (lookbook_id, product_in.product_sku, product_in.position, product_in.note))
        conn.commit()

        # Get created product
        cursor.execute("SELECT * FROM lookbook_products WHERE lookbook_id = %s AND product_sku = %s",
                      (lookbook_id, product_in.product_sku))
        created_product = cursor.fetchone()

        cursor.close()
        conn.close()

        return LookbookProduct.from_db(created_product)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error adding lookbook product", lookbook_id=lookbook_id, product_sku=product_in.product_sku, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to add product to lookbook")

@router.delete("/{lookbook_id}/products/{product_sku}")
async def remove_lookbook_product(lookbook_id: str, product_sku: str):
    """Remove a product from a lookbook."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if exists
        cursor.execute("SELECT * FROM lookbook_products WHERE lookbook_id = %s AND product_sku = %s",
                      (lookbook_id, product_sku))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Product not found in lookbook")

        # Delete
        cursor.execute("DELETE FROM lookbook_products WHERE lookbook_id = %s AND product_sku = %s",
                      (lookbook_id, product_sku))
        conn.commit()

        cursor.close()
        conn.close()

        return {"message": "Product removed from lookbook successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error removing lookbook product", lookbook_id=lookbook_id, product_sku=product_sku, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to remove product from lookbook")

@router.post("/{lookbook_id}/link-akeneo")
async def link_akeneo(lookbook_id: str, link_in: LinkAkeneoIn):
    """Link lookbook to Akeneo."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if lookbook exists
        cursor.execute("SELECT * FROM lookbooks WHERE id = %s", (lookbook_id,))
        lookbook = cursor.fetchone()

        if not lookbook:
            raise HTTPException(status_code=404, detail="Lookbook not found")

        # Update lookbook with Akeneo link
        cursor.execute("""
            UPDATE lookbooks SET
                akeneo_lookbook_id = %s,
                akeneo_sync_status = 'linked',
                akeneo_last_update = NOW(),
                updated_at = NOW()
            WHERE id = %s
        """, (link_in.akeneo_lookbook_id, lookbook_id))

        conn.commit()

        cursor.close()
        conn.close()

        return {"message": f"Lookbook linked to Akeneo ID {link_in.akeneo_lookbook_id}"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error linking to Akeneo", lookbook_id=lookbook_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to link to Akeneo")

@router.post("/{lookbook_id}/export-akeneo")
async def export_akeneo(lookbook_id: str):
    """Export lookbook to Akeneo (stub implementation)."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if lookbook exists
        cursor.execute("SELECT * FROM lookbooks WHERE id = %s", (lookbook_id,))
        lookbook = cursor.fetchone()

        if not lookbook:
            raise HTTPException(status_code=404, detail="Lookbook not found")

        # Stub: Update status to pending then exported
        cursor.execute("""
            UPDATE lookbooks SET
                akeneo_sync_status = 'exported',
                akeneo_last_update = NOW(),
                updated_at = NOW()
            WHERE id = %s
        """, (lookbook_id,))

        conn.commit()

        cursor.close()
        conn.close()

        return {"message": "Lookbook exported to Akeneo successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error exporting to Akeneo", lookbook_id=lookbook_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to export to Akeneo")