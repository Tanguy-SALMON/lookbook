"""
Shop Catalog Adapter

This adapter handles communication with the Magento shop database
for fetching product catalog information.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
import structlog
import asyncio
import aiomysql
from urllib.parse import urlparse

logger = structlog.get_logger()


class ShopCatalogAdapter(ABC):
    """Abstract base class for shop catalog adapters."""

    @abstractmethod
    async def fetch_items(
        self, limit: Optional[int] = None, since: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Fetch items from shop catalog."""
        pass

    @abstractmethod
    async def get_item_by_sku(self, sku: str) -> Optional[Dict[str, Any]]:
        """Get specific item by SKU."""
        pass


class MySQLShopCatalogAdapter(ShopCatalogAdapter):
    """MySQL-based shop catalog adapter for Magento."""

    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.logger = logger.bind(adapter="mysql_shop")
        self._parsed_url = urlparse(connection_string)

    async def _get_connection(self):
        """Create and return a database connection."""
        return await aiomysql.connect(
            host=self._parsed_url.hostname,
            port=self._parsed_url.port or 3306,
            user=self._parsed_url.username,
            password=self._parsed_url.password,
            db=self._parsed_url.path[1:],  # Remove leading slash
            autocommit=True,
        )

    async def fetch_items(
        self, limit: Optional[int] = None, since: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch in-stock items from Magento catalog.

        Args:
            limit: Maximum number of items to fetch
            since: Fetch items updated since this timestamp

        Returns:
            List of item dictionaries with basic information
        """
        try:
            self.logger.info(
                "Fetching items from shop catalog", limit=limit, since=since
            )

            query = """
                SELECT DISTINCT
                    p.sku,
                    eav.value as gc_swatchimage,
                    COALESCE(
                        price.value,
                        (SELECT MIN(child_price.value)
                         FROM catalog_product_super_link super_link
                         JOIN catalog_product_entity child ON super_link.product_id = child.entity_id
                         JOIN catalog_product_entity_decimal child_price ON child.entity_id = child_price.entity_id
                         WHERE super_link.parent_id = p.entity_id
                         AND child_price.attribute_id = 77
                         AND child_price.store_id = 0
                         AND child_price.value > 0)
                    ) as price,
                    name.value as product_name,
                    url.value as url_key,
                    status.value as status,
                    COALESCE(csi.qty, 0) as stock_qty,
                    season.value as season,
                    color_option.value as color,
                    material.value as material,
                    p.created_at,
                    p.type_id
                FROM catalog_product_entity p
                JOIN catalog_product_entity_text eav ON p.entity_id = eav.entity_id AND eav.store_id = 0
                LEFT JOIN catalog_product_entity_decimal price ON p.entity_id = price.entity_id AND price.attribute_id = 77 AND price.store_id = 0
                LEFT JOIN catalog_product_entity_varchar name ON p.entity_id = name.entity_id AND name.attribute_id = 73 AND name.store_id = 0
                LEFT JOIN catalog_product_entity_varchar url ON p.entity_id = url.entity_id AND url.attribute_id = (SELECT attribute_id FROM eav_attribute WHERE attribute_code = 'url_key' AND entity_type_id = 4) AND url.store_id = 0
                LEFT JOIN catalog_product_entity_int status ON p.entity_id = status.entity_id AND status.attribute_id = 97 AND status.store_id = 0
                LEFT JOIN cataloginventory_stock_item csi ON p.entity_id = csi.product_id
                LEFT JOIN catalog_product_entity_varchar season ON p.entity_id = season.entity_id AND season.attribute_id = (SELECT attribute_id FROM eav_attribute WHERE attribute_code = 'season' AND entity_type_id = 4) AND season.store_id = 0
                LEFT JOIN eav_attribute_option_value color_option ON EXISTS (
                    SELECT 1 FROM catalog_product_entity_int color_attr
                    WHERE color_attr.entity_id = p.entity_id
                    AND color_attr.attribute_id = 93
                    AND color_attr.value = color_option.option_id
                    AND color_option.store_id = 0
                )
                LEFT JOIN catalog_product_entity_text material ON p.entity_id = material.entity_id AND material.attribute_id = 148 AND material.store_id = 0
                WHERE eav.attribute_id = 358
                AND p.type_id IN ('configurable', 'simple')
                AND status.value = 1
            """

            if since:
                query += f" AND p.created_at >= '{since.strftime('%Y-%m-%d %H:%M:%S')}'"

            if limit:
                query += f" LIMIT {limit}"

            items = []
            async with await self._get_connection() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    await cursor.execute(query)
                    results = await cursor.fetchall()

                    for row in results:
                        # Convert datetime to ISO format string for JSON serialization
                        created_at = (
                            row["created_at"].isoformat() if row["created_at"] else None
                        )

                        # Price is already in Thai Baht (THB)
                        price = (
                            float(row["price"])
                            if row["price"] and row["price"] > 0
                            else 29.99
                        )

                        items.append(
                            {
                                "sku": row["sku"],
                                "title": row["product_name"] or f"Product {row['sku']}",
                                "price": price,
                                "size_range": ["S", "M", "L", "XL"]
                                if row["type_id"] == "configurable"
                                else ["ONE_SIZE"],
                                "image_key": row["gc_swatchimage"]
                                or f"{row['sku']}.jpg",
                                "in_stock": bool(row["status"] == 1),
                                "season": row["season"],
                                "url_key": row["url_key"],
                                "product_created_at": created_at,
                                "stock_qty": int(row["stock_qty"])
                                if row["stock_qty"]
                                else 0,
                                "category": "fashion",  # Default category
                                "color": row["color"],
                                "material": row["material"],
                                "pattern": "solid",  # Default pattern
                                "occasion": "casual",  # Default occasion
                            }
                        )

            self.logger.info("Fetched items from shop catalog", count=len(items))
            return items

        except Exception as e:
            self.logger.error("Error fetching items from shop catalog", error=str(e))
            raise

    async def get_enabled_products_with_stock(
        self, start_after_id: int = 0, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Fetch enabled products with stock, ordered by entity_id for pagination.

        Args:
            start_after_id: Fetch products with entity_id > this value
            limit: Maximum number of products to fetch

        Returns:
            List of product dictionaries with source_id for pagination
        """
        try:
            self.logger.info("Fetching enabled products with stock",
                           start_after_id=start_after_id, limit=limit)

            query = """
                SELECT DISTINCT
                    p.entity_id as source_id,
                    p.sku,
                    COALESCE(
                        price.value,
                        (SELECT MIN(child_price.value)
                         FROM catalog_product_super_link super_link
                         JOIN catalog_product_entity child ON super_link.product_id = child.entity_id
                         JOIN catalog_product_entity_decimal child_price ON child.entity_id = child_price.entity_id
                         WHERE super_link.parent_id = p.entity_id
                         AND child_price.attribute_id = 77
                         AND child_price.store_id = 0
                         AND child_price.value > 0)
                    ) as price,
                    name.value as product_name,
                    url.value as url_key,
                    COALESCE(csi.qty, 0) as stock_qty,
                    season.value as season,
                    color_option.value as color,
                    material.value as material,
                    pattern.value as pattern,
                    occasion.value as occasion,
                    category.value as category,
                    p.created_at as product_created_at,
                    eav.value as image_key
                FROM catalog_product_entity p
                JOIN catalog_product_entity_text eav ON p.entity_id = eav.entity_id AND eav.store_id = 0 AND eav.attribute_id = 358
                LEFT JOIN catalog_product_entity_decimal price ON p.entity_id = price.entity_id AND price.attribute_id = 77 AND price.store_id = 0
                LEFT JOIN catalog_product_entity_varchar name ON p.entity_id = name.entity_id AND name.attribute_id = 73 AND name.store_id = 0
                LEFT JOIN catalog_product_entity_varchar url ON p.entity_id = url.entity_id AND url.attribute_id = (SELECT attribute_id FROM eav_attribute WHERE attribute_code = 'url_key' AND entity_type_id = 4) AND url.store_id = 0
                LEFT JOIN catalog_product_entity_int status ON p.entity_id = status.entity_id AND status.attribute_id = 97 AND status.store_id = 0
                LEFT JOIN cataloginventory_stock_item csi ON p.entity_id = csi.product_id
                LEFT JOIN catalog_product_entity_varchar season ON p.entity_id = season.entity_id AND season.attribute_id = (SELECT attribute_id FROM eav_attribute WHERE attribute_code = 'season' AND entity_type_id = 4) AND season.store_id = 0
                LEFT JOIN eav_attribute_option_value color_option ON EXISTS (
                    SELECT 1 FROM catalog_product_entity_int color_attr
                    WHERE color_attr.entity_id = p.entity_id
                    AND color_attr.attribute_id = 93
                    AND color_attr.value = color_option.option_id
                    AND color_option.store_id = 0
                )
                LEFT JOIN catalog_product_entity_text material ON p.entity_id = material.entity_id AND material.attribute_id = 148 AND material.store_id = 0
                LEFT JOIN catalog_product_entity_varchar pattern ON p.entity_id = pattern.entity_id AND pattern.attribute_id = (SELECT attribute_id FROM eav_attribute WHERE attribute_code = 'pattern' AND entity_type_id = 4) AND pattern.store_id = 0
                LEFT JOIN catalog_product_entity_varchar occasion ON p.entity_id = occasion.entity_id AND occasion.attribute_id = (SELECT attribute_id FROM eav_attribute WHERE attribute_code = 'occasion' AND entity_type_id = 4) AND occasion.store_id = 0
                LEFT JOIN catalog_product_entity_varchar category ON p.entity_id = category.entity_id AND category.attribute_id = (SELECT attribute_id FROM eav_attribute WHERE attribute_code = 'category' AND entity_type_id = 4) AND category.store_id = 0
                WHERE status.value = 1  -- enabled
                AND COALESCE(csi.qty, 0) > 0  -- in stock
                AND p.entity_id > %s  -- pagination
                ORDER BY p.entity_id ASC
                LIMIT %s
            """

            items = []
            async with await self._get_connection() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    await cursor.execute(query, (start_after_id, limit))
                    results = await cursor.fetchall()

                    for row in results:
                        # Convert datetime to ISO format string for JSON serialization
                        product_created_at = (
                            row["product_created_at"].isoformat() if row["product_created_at"] else None
                        )

                        # Price is already in Thai Baht (THB)
                        price = (
                            float(row["price"])
                            if row["price"] and row["price"] > 0
                            else 29.99
                        )

                        items.append(
                            {
                                "source_id": row["source_id"],
                                "sku": row["sku"],
                                "title": row["product_name"] or f"Product {row['sku']}",
                                "price": price,
                                "size_range": ["S", "M", "L", "XL"],  # Default for configurable
                                "image_key": row["image_key"] or f"{row['sku']}.jpg",
                                "attributes": {},  # Empty for now
                                "in_stock": True,  # Since we filter for stock_qty > 0
                                "season": row["season"],
                                "url_key": row["url_key"],
                                "product_created_at": product_created_at,
                                "stock_qty": int(row["stock_qty"]) if row["stock_qty"] else 0,
                                "category": row["category"] or "fashion",
                                "color": row["color"],
                                "material": row["material"],
                                "pattern": row["pattern"],
                                "occasion": row["occasion"],
                            }
                        )

            self.logger.info("Fetched enabled products with stock", count=len(items))
            return items

        except Exception as e:
            self.logger.error("Error fetching enabled products with stock", error=str(e))
            raise

    async def get_item_by_sku(self, sku: str) -> Optional[Dict[str, Any]]:
        """
        Get specific item by SKU.

        Args:
            sku: Stock Keeping Unit identifier

        Returns:
            Item dictionary or None if not found
        """
        try:
            self.logger.info("Fetching item by SKU", sku=sku)

            query = """
                SELECT
                    p.sku,
                    p.name as title,
                    p.price,
                    GROUP_CONCAT(DISTINCT ps.value) as size_range,
                    COALESCE(i.gc_swatchimage, '') as image_key,
                    p.status = 1 as in_stock,
                    '{}' as attributes
                FROM catalog_product_entity p
                LEFT JOIN catalog_product_entity_varchar pv ON p.entity_id = pv.entity_id AND pv.attribute_id = 80  # name
                LEFT JOIN catalog_product_entity_decimal pd ON p.entity_id = pd.entity_id AND pd.attribute_id = 75  # price
                LEFT JOIN catalog_product_entity_int pi ON p.entity_id = pi.entity_id AND pi.attribute_id = 96  # status
                LEFT JOIN catalog_product_entity_text i ON p.entity_id = i.entity_id AND i.attribute_id = 87  # image
                LEFT JOIN catalog_product_entity_varchar ps ON p.entity_id = ps.entity_id AND ps.attribute_id = 132  # size
                WHERE p.sku = %s
                AND p.type_id = 'simple'
                AND pi.value = 1  # enabled
                AND p.status = 1  # visible
                AND p.has_options = 0  # simple products
                GROUP BY p.sku, p.name, p.price, i.gc_swatchimage, p.status
            """

            async with await self._get_connection() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    await cursor.execute(query, (sku,))
                    row = await cursor.fetchone()

                    if row:
                        # Convert datetime to ISO format string for JSON serialization
                        created_at = (
                            row["created_at"].isoformat() if row["created_at"] else None
                        )

                        return {
                            "sku": row["sku"],
                            "title": row["product_name"],
                            "price": float(row["price"]) if row["price"] else 0.0,
                            "size_range": [
                                "M",
                                "L",
                                "XL",
                            ],  # Default sizes for configurable products
                            "image_key": row["gc_swatchimage"] or f"{row['sku']}.jpg",
                            "in_stock": bool(row["status"] == 1),
                            "attributes": {
                                "season": row["season"],
                                "url_key": row["url_key"],
                                "created_at": created_at,
                                "stock_qty": float(row["stock_qty"])
                                if row["stock_qty"]
                                else 0,
                            },
                        }

            self.logger.info("Item not found by SKU", sku=sku)
            return None

        except Exception as e:
            self.logger.error("Error fetching item by SKU", sku=sku, error=str(e))
            raise


class MockShopCatalogAdapter(ShopCatalogAdapter):
    """Mock adapter for testing purposes."""

    def __init__(self):
        self.mock_items = [
            {
                "sku": "1295990003",
                "title": "Classic Cotton T-Shirt",
                "price": 29.99,
                "size_range": ["S", "M", "L", "XL"],
                "image_key": "e341e2f3a4b5c6d7e8f9.jpg",
                "in_stock": True,
                "attributes": {},
            },
            {
                "sku": "1295990011",
                "title": "Slim Fit Jeans",
                "price": 79.99,
                "size_range": ["M", "L", "XL"],
                "image_key": "f567g8h9i0j1k2l3m4n5.jpg",
                "in_stock": True,
                "attributes": {},
            },
        ]

    async def fetch_items(
        self, limit: Optional[int] = None, since: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Fetch mock items."""
        items = self.mock_items
        if limit:
            items = items[:limit]
        return items

    async def get_item_by_sku(self, sku: str) -> Optional[Dict[str, Any]]:
        """Get mock item by SKU."""
        for item in self.mock_items:
            if item["sku"] == sku:
                return item
        return None
