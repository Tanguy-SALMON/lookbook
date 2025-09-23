"""
Products API Router

This router provides CRUD operations for products and their vision attributes.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import structlog
import json
from datetime import datetime

from lookbook_mpc.adapters.database import get_db_connection
from lookbook_mpc.config.settings import get_settings

logger = structlog.get_logger()
router = APIRouter(prefix="/v1/products", tags=["products"])

# Pydantic models
class ProductVisionAttributes(BaseModel):
    id: Optional[int] = None
    sku: str
    color: Optional[str] = None
    category: Optional[str] = None
    material: Optional[str] = None
    pattern: Optional[str] = None
    season: Optional[str] = None
    occasion: Optional[str] = None
    style: Optional[str] = None

class ProductCreate(BaseModel):
    sku: str
    title: str
    price: float
    size_range: List[str] = []
    image_key: Optional[str] = None
    in_stock: bool = True
    season: Optional[str] = None
    url_key: Optional[str] = None
    stock_qty: int = 0
    category: Optional[str] = None
    color: Optional[str] = None
    material: Optional[str] = None
    pattern: Optional[str] = None
    occasion: Optional[str] = None
    vision_attributes: Optional[ProductVisionAttributes] = None

class ProductUpdate(BaseModel):
    sku: Optional[str] = None
    title: Optional[str] = None
    price: Optional[float] = None
    size_range: Optional[List[str]] = None
    image_key: Optional[str] = None
    in_stock: Optional[bool] = None
    season: Optional[str] = None
    url_key: Optional[str] = None
    stock_qty: Optional[int] = None
    category: Optional[str] = None
    color: Optional[str] = None
    material: Optional[str] = None
    pattern: Optional[str] = None
    occasion: Optional[str] = None
    vision_attributes: Optional[ProductVisionAttributes] = None

class ProductResponse(BaseModel):
    id: int
    sku: str
    title: str
    price: float
    size_range: List[str]
    image_key: Optional[str]
    in_stock: bool
    season: Optional[str]
    url_key: Optional[str]
    stock_qty: int
    category: Optional[str]
    color: Optional[str]
    material: Optional[str]
    pattern: Optional[str]
    occasion: Optional[str]
    vision_attributes: Optional[ProductVisionAttributes]
    created_at: str
    updated_at: str

    @classmethod
    def from_db(cls, product_data: dict, vision_data: Optional[dict] = None):
        """Create ProductResponse from database data."""
        vision_attrs = None
        if vision_data:
            vision_attrs = ProductVisionAttributes(
                id=vision_data.get('id'),
                sku=vision_data.get('sku'),
                color=vision_data.get('color'),
                category=vision_data.get('category'),
                material=vision_data.get('material'),
                pattern=vision_data.get('pattern'),
                season=vision_data.get('season'),
                occasion=vision_data.get('occasion'),
                style=vision_data.get('style')
            )

        return cls(
            id=product_data['id'],
            sku=product_data['sku'],
            title=product_data['title'],
            price=float(product_data['price']),
            size_range=json.loads(product_data['size_range']) if product_data['size_range'] else [],
            image_key=product_data['image_key'],
            in_stock=bool(product_data['in_stock']),
            season=product_data['season'],
            url_key=product_data['url_key'],
            stock_qty=product_data['stock_qty'],
            category=product_data['category'],
            color=product_data['color'],
            material=product_data['material'],
            pattern=product_data['pattern'],
            occasion=product_data['occasion'],
            vision_attributes=vision_attrs,
            created_at=product_data['created_at'].isoformat() if product_data['created_at'] else None,
            updated_at=product_data['updated_at'].isoformat() if product_data['updated_at'] else None
        )

@router.get("/", response_model=List[ProductResponse])
async def get_products(
    limit: int = 100,
    offset: int = 0,
    search: Optional[str] = None,
    category: Optional[str] = None,
    in_stock: Optional[bool] = None
):
    """Get all products with optional filtering."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Build query
        query = """
            SELECT p.* FROM products p
            LEFT JOIN product_vision_attributes pva ON p.sku = pva.sku
            WHERE 1=1
        """
        params = []

        if search:
            query += " AND (p.title LIKE %s OR p.sku LIKE %s OR p.category LIKE %s)"
            search_param = f"%{search}%"
            params.extend([search_param, search_param, search_param])

        if category:
            query += " AND p.category = %s"
            params.append(category)

        if in_stock is not None:
            query += " AND p.in_stock = %s"
            params.append(in_stock)

        query += " ORDER BY p.created_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        cursor.execute(query, params)
        products = cursor.fetchall()

        # Get vision attributes for each product
        result = []
        for product in products:
            # Get vision attributes
            cursor.execute("SELECT * FROM product_vision_attributes WHERE sku = %s", (product['sku'],))
            vision_data = cursor.fetchone()

            result.append(ProductResponse.from_db(product, vision_data))

        cursor.close()
        conn.close()

        return result

    except Exception as e:
        logger.error("Error fetching products", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch products")

@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(product_id: int):
    """Get a specific product by ID."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))
        product = cursor.fetchone()

        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        # Get vision attributes
        cursor.execute("SELECT * FROM product_vision_attributes WHERE sku = %s", (product['sku'],))
        vision_data = cursor.fetchone()

        cursor.close()
        conn.close()

        return ProductResponse.from_db(product, vision_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching product", product_id=product_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch product")

@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(product_id: int, product_update: ProductUpdate):
    """Update an existing product."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if product exists
        cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))
        existing_product = cursor.fetchone()

        if not existing_product:
            raise HTTPException(status_code=404, detail="Product not found")

        # Build update query for products table
        update_fields = []
        values = []

        update_data = product_update.dict(exclude_unset=True, exclude={'vision_attributes'})

        for field, value in update_data.items():
            if value is not None:
                if field == 'size_range':
                    update_fields.append(f"{field} = %s")
                    values.append(json.dumps(value))
                else:
                    update_fields.append(f"{field} = %s")
                    values.append(value)

        if update_fields:
            values.append(product_id)
            query = f"UPDATE products SET {', '.join(update_fields)}, updated_at = NOW() WHERE id = %s"
            cursor.execute(query, values)

        # Handle vision attributes
        if product_update.vision_attributes:
            vision_data = product_update.vision_attributes.dict(exclude_unset=True)

            # Check if vision attributes exist
            cursor.execute("SELECT id FROM product_vision_attributes WHERE sku = %s", (existing_product['sku'],))
            existing_vision = cursor.fetchone()

            if existing_vision:
                # Update existing
                update_fields = []
                values = []
                for field, value in vision_data.items():
                    if field != 'id' and field != 'sku' and value is not None:
                        update_fields.append(f"{field} = %s")
                        values.append(value)
                if update_fields:
                    values.append(existing_product['sku'])
                    query = f"UPDATE product_vision_attributes SET {', '.join(update_fields)} WHERE sku = %s"
                    cursor.execute(query, values)
            else:
                # Insert new
                if vision_data:
                    fields = []
                    placeholders = []
                    values = []
                    for field, value in vision_data.items():
                        if field not in ['id'] and value is not None:
                            fields.append(field)
                            placeholders.append("%s")
                            values.append(value)
                    if fields:
                        query = f"INSERT INTO product_vision_attributes ({', '.join(fields)}) VALUES ({', '.join(placeholders)})"
                        cursor.execute(query, values)

        conn.commit()

        # Get updated product
        cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))
        updated_product = cursor.fetchone()

        # Get vision attributes
        cursor.execute("SELECT * FROM product_vision_attributes WHERE sku = %s", (updated_product['sku'],))
        vision_data = cursor.fetchone()

        cursor.close()
        conn.close()

        return ProductResponse.from_db(updated_product, vision_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error updating product", product_id=product_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to update product")

@router.get("/count/total")
async def get_products_count():
    """Get total count of products."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) as count FROM products")
        result = cursor.fetchone()

        cursor.close()
        conn.close()

        return {"count": result['count']}

    except Exception as e:
        logger.error("Error fetching products count", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch products count")