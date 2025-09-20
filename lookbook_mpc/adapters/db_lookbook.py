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
    Item, ItemDB, Outfit, OutfitDB, OutfitItem, OutfitItemDB,
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
        Save items to SQLite database.

        Args:
            items: List of item dictionaries to save

        Returns:
            Number of items saved
        """
        try:
            self.logger.info("Saving items to lookbook repository", count=len(items))

            async with self._get_session() as session:
                saved_count = 0
                for item in items:
                    # Check if item already exists
                    existing_result = await session.execute(
                        select(ItemDB).where(ItemDB.sku == item["sku"])
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
                    else:
                        # Create new item
                        new_item = ItemDB(
                            sku=item["sku"],
                            title=item["title"],
                            price=item["price"],
                            size_range=item["size_range"],
                            image_key=item["image_key"],
                            attributes=item["attributes"],
                            in_stock=item["in_stock"]
                        )
                        session.add(new_item)

                    saved_count += 1

                await session.commit()
                self.logger.info("Successfully saved items", count=saved_count)
                return saved_count

        except Exception as e:
            self.logger.error("Error saving items to repository", error=str(e))
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
                query = select(ItemDB).where(ItemDB.in_stock == True)

                # Apply filters based on intent
                if intent.budget_max:
                    query = query.where(ItemDB.price <= intent.budget_max)

                if intent.size:
                    # This is a simplified size filter - in production you'd want more sophisticated logic
                    query = query.where(
                        or_(
                            ItemDB.size_range.contains([intent.size]),
                            ItemDB.size_range == ["ONE_SIZE"]
                        )
                    )

                # Filter by category if specified in attributes
                if hasattr(intent, 'category') and intent.category:
                    query = query.where(
                        ItemDB.attributes.op('->>')('category').astext == intent.category
                    )

                # Filter by color if specified in attributes
                if hasattr(intent, 'color') and intent.color:
                    query = query.where(
                        ItemDB.attributes.op('->>')('color').astext == intent.color
                    )

                # Filter by material if specified in attributes
                if hasattr(intent, 'material') and intent.material:
                    query = query.where(
                        ItemDB.attributes.op('->>')('material').astext == intent.material
                    )

                # Filter by occasion if specified in attributes
                if intent.occasion:
                    query = query.where(
                        ItemDB.attributes.op('->>')('occasion').astext == intent.occasion
                    )

                # Filter by season if specified in attributes
                if hasattr(intent, 'season') and intent.season:
                    query = query.where(
                        ItemDB.attributes.op('->>')('season').astext == intent.season
                    )

                # Filter by objectives (e.g., slimming)
                if intent.objectives:
                    for objective in intent.objectives:
                        query = query.where(
                            ItemDB.attributes.op('->>')('objectives').astext.contains(objective)
                        )

                # Filter by palette if specified
                if intent.palette:
                    for color in intent.palette:
                        query = query.where(
                            ItemDB.attributes.op('->>')('color').astext.in_(intent.palette)
                        )

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
                result = await session.execute(select(ItemDB).where(ItemDB.in_stock == True))
                items_db = result.scalars().all()

                self.logger.info("Retrieved all items", count=len(items_db))
                return [item.to_domain() for item in items_db]

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
                query = select(ItemDB).where(ItemDB.in_stock == True)

                # Apply filters
                if 'category' in filters:
                    # SQLite JSON path syntax
                    query = query.where(
                        text(f"json_extract(attributes, '$.category') = '{filters['category']}'")
                    )

                if 'color' in filters:
                    # SQLite JSON path syntax
                    query = query.where(
                        text(f"json_extract(attributes, '$.color') = '{filters['color']}'")
                    )

                if 'material' in filters:
                    # SQLite JSON path syntax
                    query = query.where(
                        text(f"json_extract(attributes, '$.material') = '{filters['material']}'")
                    )

                if 'size' in filters:
                    query = query.where(
                        or_(
                            ItemDB.size_range.contains([filters['size']]),
                            ItemDB.size_range == ["ONE_SIZE"]
                        )
                    )

                if 'max_price' in filters:
                    query = query.where(ItemDB.price <= filters['max_price'])

                if 'min_price' in filters:
                    query = query.where(ItemDB.price >= filters['min_price'])

                if 'pattern' in filters:
                    query = query.where(
                        ItemDB.attributes.op('->>')('pattern').astext == filters['pattern']
                    )

                if 'season' in filters:
                    query = query.where(
                        ItemDB.attributes.op('->>')('season').astext == filters['season']
                    )

                if 'occasion' in filters:
                    query = query.where(
                        ItemDB.attributes.op('->>')('occasion').astext == filters['occasion']
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
                    select(ItemDB).where(ItemDB.id == item_id)
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