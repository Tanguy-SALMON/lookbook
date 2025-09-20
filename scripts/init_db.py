#!/usr/bin/env python3
"""
Database Initialization Script

This script initializes the lookbook database and runs migrations.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from lookbook_mpc.adapters.database import init_database
from lookbook_mpc.adapters.db_lookbook import SQLiteLookbookRepository
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Main function to initialize database."""
    try:
        # Get database URL from environment
        database_url = "sqlite+aiosqlite:///lookbook.db"

        logger.info("Starting database initialization")
        logger.info(f"Database URL: {database_url}")

        # Initialize database
        engine = await init_database(database_url)

        # Test repository
        logger.info("Testing repository connection")
        repo = SQLiteLookbookRepository(database_url)

        # Try to get all items (should be empty initially)
        items = await repo.get_all_items()
        logger.info(f"Repository test successful, found {len(items)} items")

        # Close database connection
        await engine.dispose()

        logger.info("Database initialization completed successfully")

    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())