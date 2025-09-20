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
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import selectinload
from sqlalchemy import select, and_, or_, text, JSON

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
    """SQLite-based lookbook repository."""

    def __init__(self, database_url: str):
        # Ensure we're using async SQLite driver
        if database_url.startswith("sqlite:///"):
            database_url = database_url.replace("sqlite:///", "sqlite+aiosqlite:///")

        self.database_url = database_url
        self.engine = create_async_engine(database_url, echo=False)
        self.async_session = async_sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
        self.logger = logger.bind(adapter="sqlite_lookbook")

    def _get_session(self) -> AsyncSession:
        """Get database session."""
        return self.async_session()

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

            async with self._get_session() as session:
                async with session.no_autoflush:
                    saved_count = 0
                    for item in items:
                        # Check if item already exists
                        existing_result = await session.execute(
                            select(ProductDB).where(ProductDB.sku == item["sku"])
                        )
                        existing_item = existing_result.scalar_one_or_none()

                        if existing_item:
                            # Update existing item
                            existing_item.title = item["title"]
                            existing_item.price = item["price"]
                            existing_item.size_range = item["size_range"]
                            existing_item.image_key = item["image_key"]
                            existing_item.attributes = item["attributes"]
                            existing_item.in_stock = item["in_stock"]
                            existing_item.updated_at = datetime.utcnow()

                            # Update new columns
                            existing_item.season = item.get("season")
                            existing_item.url_key = item.get("url_key")
                            existing_item.product_created_at = item.get("product_created_at")
                            existing_item.stock_qty = item.get("stock_qty", 0)
                            existing_item.category = item.get("category")
                            existing_item.color = item.get("color")
                            existing_item.material = item.get("material")
                            existing_item.pattern = item.get("pattern")
                            existing_item.occasion = item.get("occasion")
                        else:
                            # Create new item
                            new_item = ProductDB(
                                sku=item["sku"],
                                title=item["title"],
                                price=item["price"],
                                size_range=item["size_range"],
                                image_key=item["image_key"],
                                attributes=item["attributes"],
                                in_stock=item["in_stock"],
                                season=item.get("season"),
                                url_key=item.get("url_key"),
                                product_created_at=item.get("product_created_at"),
                                stock_qty=item.get("stock_qty", 0),
                                category=item.get("category"),
                                color=item.get("color"),
                                material=item.get("material"),
                                pattern=item.get("pattern"),
                                occasion=item.get("occasion")
                            )
                            session.add(new_item)

                        saved_count += 1

                    await session.commit()
                    self.logger.info("Successfully saved items", count=saved_count)
                    return saved_count

        except Exception as e:
            self.logger.error("Error saving items to repository", error=str(e))
            raise

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

            # Prepare data for bulk insert
            upsert_data = []
            for item in items:
                # Ensure all required fields are present
                row_data = {
                    "sku": item.get("sku"),
                    "title": item.get("title", ""),
                    "price": item.get("price", 0.0),
                    "size_range": json.dumps(item.get("size_range", [])),
                    "image_key": item.get("image_key", ""),
                    "attributes": json.dumps(item.get("attributes", {})),
                    "in_stock": item.get("in_stock", True),
                    "season": item.get("season"),
                    "url_key": item.get("url_key"),
                    "product_created_at": item.get("product_created_at"),
                    "stock_qty": item.get("stock_qty", 0),
                    "category": item.get("category"),
                    "color": item.get("color"),
                    "material": item.get("material"),
                    "pattern": item.get("pattern"),
                    "occasion": item.get("occasion"),
                    "updated_at": datetime.utcnow()
                }
                upsert_data.append(row_data)

            async with self._get_session() as session:
                # Use SQLite's INSERT OR REPLACE for efficient upsert
                # This is much faster than individual row-by-row operations
                columns = list(upsert_data[0].keys())
                placeholders = [f":{col}" for col in columns]
                column_names = ", ".join(columns)
                placeholder_str = ", ".join(placeholders)

                # Build the INSERT OR REPLACE query
                # SQLite doesn't support INSERT OR REPLACE directly with all columns,
                # so we need to use a temporary table approach
                temp_table_name = f"temp_upsert_{int(datetime.utcnow().timestamp())}"

                # Create temporary table
                create_temp_table = f"""
                CREATE TEMPORARY TABLE {temp_table_name} (
                    sku TEXT PRIMARY KEY,
                    title TEXT,
                    price REAL,
                    size_range TEXT,
                    image_key TEXT,
                    attributes TEXT,
                    in_stock INTEGER,
                    season TEXT,
                    url_key TEXT,
                    product_created_at TEXT,
                    stock_qty INTEGER,
                    category TEXT,
                    color TEXT,
                    material TEXT,
                    pattern TEXT,
                    occasion TEXT,
                    updated_at TEXT
                )
                """

                # Insert into temporary table
                insert_temp = f"""
                INSERT INTO {temp_table_name} ({column_names})
                VALUES ({placeholder_str})
                """

                # Replace from temp to main table
                replace_query = f"""
                REPLACE INTO products ({column_names})
                SELECT {column_names} FROM {temp_table_name}
                """

                # Drop temp table
                drop_temp = f"DROP TABLE {temp_table_name}"

                try:
                    # Create temp table
                    await session.execute(create_temp_table)

                    # Bulk insert into temp table
                    for row in upsert_data:
                        await session.execute(insert_temp, row)

                    # Replace into main table
                    await session.execute(replace_query)

                    # Get counts
                    result = await session.execute(
                        "SELECT COUNT(*) FROM products WHERE sku IN (:skus)",
                        {"skus": [item["sku"] for item in items]}
                    )
                    total_count = result.scalar()

                    await session.commit()

                    self.logger.info("Successfully batch upserted products", count=len(items))
                    return {
                        "upserted": len(items),
                        "updated": len(items),  # With REPLACE, all are treated as updates
                        "skus": [item["sku"] for item in items],
                        "total_in_db": total_count
                    }

                except Exception as e:
                    await session.rollback()
                    self.logger.error("Error during batch upsert", error=str(e))
                    raise

        except Exception as e:
            self.logger.error("Error in batch upsert products", error=str(e))
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

            async with self._get_session() as session:
                query = select(ProductDB).where(ProductDB.in_stock == True)

                # Apply filters based on intent
                if intent.budget_max:
                    query = query.where(ProductDB.price <= intent.budget_max)

                if intent.size:
                    # This is a simplified size filter - in production you'd want more sophisticated logic
                    query = query.where(
                        or_(
                            ProductDB.size_range.contains([intent.size]),
                            ProductDB.size_range == ["ONE_SIZE"]
                        )
                    )

                # Filter by category using new column
                if hasattr(intent, 'category') and intent.category:
                    query = query.where(ProductDB.category == intent.category)

                # Filter by color using new column
                if hasattr(intent, 'color') and intent.color:
                    query = query.where(ProductDB.color == intent.color)

                # Filter by material using new column
                if hasattr(intent, 'material') and intent.material:
                    query = query.where(ProductDB.material == intent.material)

                # Filter by occasion using new column
                if intent.occasion:
                    query = query.where(ProductDB.occasion == intent.occasion)

                # Filter by season using new column
                if hasattr(intent, 'season') and intent.season:
                    query = query.where(ProductDB.season == intent.season)

                # Filter by objectives (e.g., slimming) - still use JSON for this
                if intent.objectives:
                    for objective in intent.objectives:
                        query = query.where(
                            ProductDB.attributes.op('->>')('objectives').astext.contains(objective)
                        )

                # Filter by palette if specified
                if intent.palette:
                    for color in intent.palette:
                        query = query.where(ProductDB.color.in_(intent.palette))

                result = await session.execute(query)
                items_db = result.scalars().all()

                self.logger.info("Found items by intent", count=len(items_db))
                return [item.to_domain() for item in items_db]

        except Exception as e:
            self.logger.error("Error getting items by intent", error=str(e))
            raise

    async def get_all_items(self) -> List[Item]:
        """Get all items from repository."""
        try:
            self.logger.info("Getting all items")

            async with self._get_session() as session:
                result = await session.execute(select(ProductDB).where(ProductDB.in_stock == True))
                items_db = result.scalars().all()

                self.logger.info("Retrieved all items", count=len(items_db))
                # Filter out None values and convert to domain objects
                valid_items = [item for item in items_db if item is not None]
                return [item.to_domain() for item in valid_items]

        except Exception as e:
            self.logger.error("Error getting all items", error=str(e))
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

            async with self._get_session() as session:
                query = select(ProductDB).where(ProductDB.in_stock == True)

                # Apply filters using new columns
                if 'category' in filters:
                    query = query.where(ProductDB.category == filters['category'])

                if 'color' in filters:
                    query = query.where(ProductDB.color == filters['color'])

                if 'material' in filters:
                    query = query.where(ProductDB.material == filters['material'])

                if 'size' in filters:
                    query = query.where(
                        or_(
                            ProductDB.size_range.contains([filters['size']]),
                            ProductDB.size_range == ["ONE_SIZE"]
                        )
                    )

                if 'max_price' in filters:
                    query = query.where(ProductDB.price <= filters['max_price'])

                if 'min_price' in filters:
                    query = query.where(ProductDB.price >= filters['min_price'])

                if 'pattern' in filters:
                    query = query.where(
                        ProductDB.attributes.op('->>')('pattern').astext == filters['pattern']
                    )

                if 'season' in filters:
                    query = query.where(
                        ProductDB.attributes.op('->>')('season').astext == filters['season']
                    )

                if 'occasion' in filters:
                    query = query.where(
                        ProductDB.attributes.op('->>')('occasion').astext == filters['occasion']
                    )

                result = await session.execute(query)
                items_db = result.scalars().all()

                self.logger.info("Found items by search", count=len(items_db))
                return [item.to_domain() for item in items_db]

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

            async with self._get_session() as session:
                result = await session.execute(
                    select(ProductDB).where(ProductDB.id == item_id)
                )
                item_db = result.scalar_one_or_none()

                if item_db:
                    self.logger.info("Found item by ID", item_id=item_id)
                    return item_db.to_domain()
                else:
                    self.logger.warning("Item not found by ID", item_id=item_id)
                    return None

        except Exception as e:
            self.logger.error("Error getting item by ID", error=str(e))
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

            async with self._get_session() as session:
                # Save each outfit
                for outfit in outfits:
                    # Check if outfit already exists
                    existing = await session.execute(
                        select(OutfitDB).where(OutfitDB.title == outfit.title)
                    )
                    outfit_db = existing.scalar_one_or_none()

                    if not outfit_db:
                        # Create new outfit
                        outfit_db = OutfitDB.from_domain(outfit)
                        session.add(outfit_db)
                        await session.flush()  # Get the ID

                    # Save outfit items
                    for item_data in outfit.get('items', []):
                        outfit_item = OutfitItem(
                            outfit_id=outfit_db.id,
                            item_id=item_data['item_id'],
                            role=item_data['role']
                        )
                        outfit_item_db = OutfitItemDB.from_domain(outfit_item)
                        session.add(outfit_item_db)

                await session.commit()
                self.logger.info("Successfully saved lookbook", theme=theme)

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