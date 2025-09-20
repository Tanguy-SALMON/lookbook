"""
Lookbook Repository Adapter

This adapter handles database operations for the lookbook system,
including item storage, outfit management, and rule storage.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
import structlog
import sqlite3
import json
import asyncio

from lookbook_mpc.domain.entities import (
    Item, ProductDB, Outfit, OutfitDB, OutfitItem, OutfitItemDB,
    Rule, RuleDB, Intent, VisionAttributes
)

logger = structlog.get_logger()


class LookbookRepository(ABC):
    """Abstract base class for lookbook repositories."""

    @abstractmethod
    async def save_items(self, items: List[Item]) -> int:
        """Save items to repository."""
        pass

    @abstractmethod
    async def get_items_by_intent(self, intent: Intent) -> List[Item]:
        """Get items matching intent criteria."""
        pass

    @abstractmethod
    async def get_all_items(self) -> List[Item]:
        """Get all items from repository."""
        pass

    @abstractmethod
    async def search_items(self, filters: Dict[str, Any]) -> List[Item]:
        """Search items by filters."""
        pass

    @abstractmethod
    async def get_item_by_id(self, item_id: int) -> Optional[Item]:
        """Get item by ID."""
        pass

    @abstractmethod
    async def save_lookbook(self, theme: str, outfits: List[Outfit]) -> None:
        """Save lookbook with theme and outfits."""
        pass


class SQLiteLookbookRepository(LookbookRepository):
    """SQLite-based lookbook repository using direct SQLite operations."""

    def __init__(self, database_url: str):
        # Extract database path from URL
        if database_url.startswith("sqlite:///"):
            self.db_path = database_url[10:]  # Remove "sqlite:///"
        else:
            self.db_path = database_url

        self.logger = logger.bind(adapter="sqlite_lookbook")
        self._lock = asyncio.Lock()

    async def _get_connection(self):
        """Get database connection."""
        return sqlite3.connect(self.db_path)

    async def batch_upsert_products(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Efficiently upsert products in batch using INSERT OR REPLACE.

        Args:
            items: List of item dictionaries to upsert

        Returns:
            Dictionary with upsert results
        """
        try:
            self.logger.info("Batch upserting products", count=len(items))

            if not items:
                return {"upserted": 0, "updated": 0, "skus": []}

            async with self._lock:
                conn = await self._get_connection()
                cursor = conn.cursor()

                upserted_count = 0
                updated_count = 0

                for item in items:
                    try:
                        # Ensure all required fields are present and properly formatted
                        if not isinstance(item, dict):
                            self.logger.error(f"Invalid item format: {item}")
                            continue

                        # Convert data to proper format
                        sku = str(item.get("sku", ""))
                        title = str(item.get("title", ""))
                        price = float(item.get("price", 0.0))
                        size_range = json.dumps(item.get("size_range", []))
                        image_key = str(item.get("image_key", ""))
                        attributes = json.dumps(item.get("attributes", {}))
                        in_stock = int(item.get("in_stock", True))
                        season = str(item.get("season")) if item.get("season") else None
                        url_key = str(item.get("url_key")) if item.get("url_key") else None
                        product_created_at = item.get("product_created_at")
                        stock_qty = int(item.get("stock_qty", 0))
                        category = str(item.get("category")) if item.get("category") else None
                        color = str(item.get("color")) if item.get("color") else None
                        material = str(item.get("material")) if item.get("material") else None
                        pattern = str(item.get("pattern")) if item.get("pattern") else None
                        occasion = str(item.get("occasion")) if item.get("occasion") else None
                        updated_at = datetime.utcnow().isoformat()

                        # Check if product exists
                        cursor.execute("SELECT id FROM products WHERE sku = ?", (sku,))
                        existing_id = cursor.fetchone()

                        if existing_id:
                            # Update existing product
                            cursor.execute("""
                                UPDATE products SET
                                    title = ?, price = ?, size_range = ?, image_key = ?,
                                    attributes = ?, in_stock = ?, season = ?, url_key = ?,
                                    product_created_at = ?, stock_qty = ?, category = ?,
                                    color = ?, material = ?, pattern = ?, occasion = ?,
                                    updated_at = ?
                                WHERE sku = ?
                            """, (
                                title, price, size_range, image_key, attributes, in_stock,
                                season, url_key, product_created_at, stock_qty, category,
                                color, material, pattern, occasion, updated_at, sku
                            ))
                            updated_count += 1
                        else:
                            # Insert new product
                            cursor.execute("""
                                INSERT INTO products (
                                    sku, title, price, size_range, image_key, attributes,
                                    in_stock, season, url_key, product_created_at, stock_qty,
                                    category, color, material, pattern, occasion, updated_at
                                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (
                                sku, title, price, size_range, image_key, attributes,
                                in_stock, season, url_key, product_created_at, stock_qty,
                                category, color, material, pattern, occasion, updated_at
                            ))
                            upserted_count += 1

                    except Exception as e:
                        self.logger.error(f"Error processing item {item.get('sku', 'unknown')}: {e}")
                        continue

                conn.commit()
                conn.close()

                self.logger.info("Successfully batch upserted products",
                               upserted=upserted_count, updated=updated_count, total=len(items))
                return {
                    "upserted": upserted_count,
                    "updated": updated_count,
                    "skus": [item["sku"] for item in items],
                    "total_in_db": upserted_count + updated_count
                }

        except Exception as e:
            self.logger.error("Error in batch upsert products", error=str(e))
            raise

    async def get_all_items(self) -> List[Item]:
        """Get all items from repository."""
        try:
            self.logger.info("Getting all items")

            async with self._lock:
                conn = await self._get_connection()
                cursor = conn.cursor()

                cursor.execute("SELECT * FROM products WHERE in_stock = 1")
                rows = cursor.fetchall()

                conn.close()

                self.logger.info("Retrieved all items", count=len(rows))

                # Convert to domain objects
                items = []
                for row in rows:
                    item = {
                        "id": row[0],
                        "sku": row[1],
                        "title": row[2],
                        "price": row[3],
                        "size_range": json.loads(row[4]) if row[4] else [],
                        "image_key": row[5],
                        "attributes": json.loads(row[6]) if row[6] else {},
                        "in_stock": bool(row[7]),
                        "created_at": row[8],
                        "updated_at": row[9],
                        "season": row[10],
                        "url_key": row[11],
                        "product_created_at": row[12],
                        "stock_qty": row[13],
                        "category": row[14],
                        "color": row[15],
                        "material": row[16],
                        "pattern": row[17],
                        "occasion": row[18]
                    }
                    items.append(item)

                return items

        except Exception as e:
            self.logger.error("Error getting all items", error=str(e))
            raise

    async def get_items_by_intent(self, intent: Intent) -> List[Item]:
        """
        Get items matching intent criteria.

        Args:
            intent: Intent entity with constraints

        Returns:
            List of matching Item entities
        """
        try:
            self.logger.info("Getting items by intent", intent=intent.dict())

            async with self._lock:
                conn = await self._get_connection()
                cursor = conn.cursor()

                query = "SELECT * FROM products WHERE in_stock = 1"
                params = []

                # Apply filters based on intent
                if intent.budget_max:
                    query += " AND price <= ?"
                    params.append(intent.budget_max)

                if intent.size:
                    # This is a simplified size filter
                    query += " AND (size_range LIKE ? OR size_range = ?)"
                    params.append(f'%"{intent.size}"%')
                    params.append('["ONE_SIZE"]')

                # Filter by category using new column
                if hasattr(intent, 'category') and intent.category:
                    query += " AND category = ?"
                    params.append(intent.category)

                # Filter by color using new column
                if hasattr(intent, 'color') and intent.color:
                    query += " AND color = ?"
                    params.append(intent.color)

                # Filter by material using new column
                if hasattr(intent, 'material') and intent.material:
                    query += " AND material = ?"
                    params.append(intent.material)

                # Filter by occasion using new column
                if intent.occasion:
                    query += " AND occasion = ?"
                    params.append(intent.occasion)

                # Filter by season using new column
                if hasattr(intent, 'season') and intent.season:
                    query += " AND season = ?"
                    params.append(intent.season)

                cursor.execute(query, params)
                rows = cursor.fetchall()

                conn.close()

                self.logger.info("Found items by intent", count=len(rows))

                # Convert to domain objects
                items = []
                for row in rows:
                    item = {
                        "id": row[0],
                        "sku": row[1],
                        "title": row[2],
                        "price": row[3],
                        "size_range": json.loads(row[4]) if row[4] else [],
                        "image_key": row[5],
                        "attributes": json.loads(row[6]) if row[6] else {},
                        "in_stock": bool(row[7]),
                        "created_at": row[8],
                        "updated_at": row[9],
                        "season": row[10],
                        "url_key": row[11],
                        "product_created_at": row[12],
                        "stock_qty": row[13],
                        "category": row[14],
                        "color": row[15],
                        "material": row[16],
                        "pattern": row[17],
                        "occasion": row[18]
                    }
                    items.append(item)

                return items

        except Exception as e:
            self.logger.error("Error getting items by intent", error=str(e))
            raise

    async def search_items(self, filters: Dict[str, Any]) -> List[Item]:
        """
        Search items by filters.

        Args:
            filters: Search filters (category, color, size, etc.)

        Returns:
            List of matching Item entities
        """
        try:
            self.logger.info("Searching items", filters=filters)

            async with self._lock:
                conn = await self._get_connection()
                cursor = conn.cursor()

                query = "SELECT * FROM products WHERE in_stock = 1"
                params = []

                # Apply filters using new columns
                if 'category' in filters:
                    query += " AND category = ?"
                    params.append(filters['category'])

                if 'color' in filters:
                    query += " AND color = ?"
                    params.append(filters['color'])

                if 'material' in filters:
                    query += " AND material = ?"
                    params.append(filters['material'])

                if 'size' in filters:
                    query += " AND (size_range LIKE ? OR size_range = ?)"
                    params.append(f'%"{filters["size"]}%')
                    params.append('["ONE_SIZE"]')

                if 'max_price' in filters:
                    query += " AND price <= ?"
                    params.append(filters['max_price'])

                if 'min_price' in filters:
                    query += " AND price >= ?"
                    params.append(filters['min_price'])

                if 'pattern' in filters:
                    query += " AND pattern = ?"
                    params.append(filters['pattern'])

                if 'season' in filters:
                    query += " AND season = ?"
                    params.append(filters['season'])

                if 'occasion' in filters:
                    query += " AND occasion = ?"
                    params.append(filters['occasion'])

                cursor.execute(query, params)
                rows = cursor.fetchall()

                conn.close()

                self.logger.info("Found items by search", count=len(rows))

                # Convert to domain objects
                items = []
                for row in rows:
                    item = {
                        "id": row[0],
                        "sku": row[1],
                        "title": row[2],
                        "price": row[3],
                        "size_range": json.loads(row[4]) if row[4] else [],
                        "image_key": row[5],
                        "attributes": json.loads(row[6]) if row[6] else {},
                        "in_stock": bool(row[7]),
                        "created_at": row[8],
                        "updated_at": row[9],
                        "season": row[10],
                        "url_key": row[11],
                        "product_created_at": row[12],
                        "stock_qty": row[13],
                        "category": row[14],
                        "color": row[15],
                        "material": row[16],
                        "pattern": row[17],
                        "occasion": row[18]
                    }
                    items.append(item)

                return items

        except Exception as e:
            self.logger.error("Error searching items", error=str(e))
            raise

    async def get_item_by_id(self, item_id: int) -> Optional[Item]:
        """
        Get item by ID.

        Args:
            item_id: Item identifier

        Returns:
            Item entity or None if not found
        """
        try:
            self.logger.info("Getting item by ID", item_id=item_id)

            async with self._lock:
                conn = await self._get_connection()
                cursor = conn.cursor()

                cursor.execute("SELECT * FROM products WHERE id = ?", (item_id,))
                row = cursor.fetchone()

                conn.close()

                if row:
                    self.logger.info("Found item by ID", item_id=item_id)
                    item = {
                        "id": row[0],
                        "sku": row[1],
                        "title": row[2],
                        "price": row[3],
                        "size_range": json.loads(row[4]) if row[4] else [],
                        "image_key": row[5],
                        "attributes": json.loads(row[6]) if row[6] else {},
                        "in_stock": bool(row[7]),
                        "created_at": row[8],
                        "updated_at": row[9],
                        "season": row[10],
                        "url_key": row[11],
                        "product_created_at": row[12],
                        "stock_qty": row[13],
                        "category": row[14],
                        "color": row[15],
                        "material": row[16],
                        "pattern": row[17],
                        "occasion": row[18]
                    }
                    return item
                else:
                    self.logger.warning("Item not found by ID", item_id=item_id)
                    return None

        except Exception as e:
            self.logger.error("Error getting item by ID", error=str(e))
            raise

    async def save_items(self, items: List[Dict[str, Any]]) -> int:
        """
        Save items to SQLite database (legacy method - use batch_upsert_products for better performance).

        Args:
            items: List of item dictionaries to save

        Returns:
            Number of items saved
        """
        try:
            self.logger.info("Saving items to lookbook repository", count=len(items))

            # Use batch_upsert_products for better performance
            result = await self.batch_upsert_products(items)
            return result.get("upserted", 0) + result.get("updated", 0)

        except Exception as e:
            self.logger.error("Error saving items to repository", error=str(e))
            raise

    async def save_lookbook(self, theme: str, outfits: List[Outfit]) -> None:
        """
        Save lookbook with theme and outfits.

        Args:
            theme: Lookbook theme
            outfits: List of Outfit entities
        """
        try:
            self.logger.info("Saving lookbook", theme=theme, outfit_count=len(outfits))

            # For now, just log the action - this would need proper implementation
            self.logger.info("Lookbook save not implemented yet", theme=theme)

        except Exception as e:
            self.logger.error("Error saving lookbook", error=str(e))
            raise


class MockLookbookRepository(LookbookRepository):
    """Mock repository for testing purposes."""

    def __init__(self):
        self.mock_items = [
            {
                "id": 1,
                "sku": "1295990003",
                "title": "Classic Cotton T-Shirt",
                "price": 29.99,
                "size_range": ["S", "M", "L", "XL"],
                "image_key": "e341e2f3a4b5c6d7e8f9.jpg",
                "attributes": {
                    "vision_attributes": {
                        "color": "white",
                        "category": "top",
                        "material": "cotton",
                        "pattern": "plain"
                    }
                },
                "in_stock": True
            },
            {
                "id": 2,
                "sku": "1295990011",
                "title": "Slim Fit Jeans",
                "price": 79.99,
                "size_range": ["M", "L", "XL"],
                "image_key": "f567g8h9i0j1k2l3m4n5.jpg",
                "attributes": {
                    "vision_attributes": {
                        "color": "blue",
                        "category": "bottom",
                        "material": "denim",
                        "pattern": "plain"
                    }
                },
                "in_stock": True
            }
        ]

    async def save_items(self, items: List[Dict[str, Any]]) -> int:
        """Save mock items."""
        self.mock_items.extend(items)
        return len(items)

    async def get_items_by_intent(self, intent: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get mock items by intent."""
        # Simple mock filtering
        if intent.get("occasion") == "casual":
            return [item for item in self.mock_items if item["attributes"].get("vision_attributes", {}).get("category") in ["top", "bottom"]]
        return self.mock_items

    async def get_all_items(self) -> List[Dict[str, Any]]:
        """Get all mock items."""
        return self.mock_items

    async def search_items(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search mock items."""
        # Simple mock search
        results = self.mock_items
        if filters.get("category"):
            category = filters["category"]
            results = [item for item in results if item["attributes"].get("vision_attributes", {}).get("category") == category]
        return results

    async def get_item_by_id(self, item_id: int) -> Optional[Dict[str, Any]]:
        """Get mock item by ID."""
        for item in self.mock_items:
            if item["id"] == item_id:
                return item
        return None

    async def save_lookbook(self, theme: str, outfits: List[Dict[str, Any]]) -> None:
        """Save mock lookbook."""
        # Mock implementation - just log the action
        logger.info(f"Mock save lookbook: {theme}", outfit_count=len(outfits))