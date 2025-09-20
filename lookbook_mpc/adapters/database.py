"""
Database Utilities

This module provides utilities for database initialization, connection,
and management for the lookbook system.
"""

import asyncio
import logging
from typing import Optional
import structlog
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from alembic import command
from alembic.config import Config
import aiomysql

from lookbook_mpc.domain.entities import Base

logger = structlog.get_logger()


class DatabaseManager:
    """Database manager for handling database operations."""

    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine: Optional[AsyncEngine] = None
        self.logger = logger.bind(database_url=database_url)

    async def initialize(self) -> AsyncEngine:
        """Initialize database engine and create tables."""
        try:
            self.logger.info("Initializing database")

            # Create async engine based on database type
            if self.database_url.startswith("mysql+pymysql://"):
                # For MySQL, use aiomysql directly
                self.engine = None  # We'll use direct aiomysql connection
                await self._create_mysql_tables()
            else:
                # For SQLite, use SQLAlchemy async engine
                self.engine = create_async_engine(
                    self.database_url,
                    echo=False,  # Set to True for SQL debugging
                    future=True
                )

                # Create all tables
                async with self.engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)

            self.logger.info("Database initialized successfully")
            return self.engine

        except Exception as e:
            self.logger.error("Failed to initialize database", error=str(e))
            raise

    async def _create_mysql_tables(self) -> None:
        """Create MySQL tables using direct SQL execution."""
        try:
            # Parse MySQL connection string
            from urllib.parse import urlparse
            parsed_url = urlparse(self.database_url)

            # Extract connection parameters
            db_name = parsed_url.path[1:]  # Remove leading slash

            # Connect to MySQL server (without specific database first)
            conn = await aiomysql.connect(
                host=parsed_url.hostname,
                port=parsed_url.port or 3306,
                user=parsed_url.username,
                password=parsed_url.password,
                autocommit=True
            )

            cursor = await conn.cursor()

            # Create database if it doesn't exist
            await cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            await cursor.execute(f"USE `{db_name}`")

            # Read and execute schema SQL
            schema_path = "scripts/init_db_mysql.sql"
            with open(schema_path, 'r') as f:
                schema_sql = f.read()

            # Split SQL into individual statements and execute
            statements = [stmt.strip() for stmt in schema_sql.split(';') if stmt.strip()]

            for statement in statements:
                if statement:
                    try:
                        await cursor.execute(statement)
                    except Exception as e:
                        # Ignore errors for duplicate indexes or other non-critical issues
                        if "Duplicate key name" not in str(e) and "Already exists" not in str(e):
                            self.logger.warning(f"SQL statement warning: {e}")

            await cursor.close()
            conn.close()

            self.logger.info("MySQL tables created successfully")

        except Exception as e:
            self.logger.error("Failed to create MySQL tables", error=str(e))
            raise

    async def run_migrations(self) -> None:
        """Run database migrations using Alembic."""
        try:
            self.logger.info("Running database migrations")

            # Create Alembic configuration
            alembic_cfg = Config("alembic.ini")

            # Set the database URL to use appropriate driver
            if alembic_cfg.get_main_option("sqlalchemy.url", "").startswith("sqlite:///"):
                alembic_cfg.set_main_option("sqlalchemy.url",
                    alembic_cfg.get_main_option("sqlalchemy.url").replace("sqlite:///", "sqlite+aiosqlite:///"))
            elif alembic_cfg.get_main_option("sqlalchemy.url", "").startswith("mysql+pymysql://"):
                # For MySQL, we'll need to handle migrations differently
                # For now, skip migrations for MySQL and use direct SQL
                self.logger.info("Skipping Alembic migrations for MySQL - using direct SQL schema")
                return

            # Run upgrade in a thread pool executor to avoid async issues
            import asyncio
            from concurrent.futures import ThreadPoolExecutor

            def run_sync_migration():
                command.upgrade(alembic_cfg, "head")

            # Run in thread pool to avoid blocking the event loop
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor() as executor:
                await loop.run_in_executor(executor, run_sync_migration)

            self.logger.info("Database migrations completed successfully")

        except Exception as e:
            self.logger.error("Failed to run migrations", error=str(e))
            raise

    async def close(self) -> None:
        """Close database engine."""
        if self.engine:
            await self.engine.dispose()
            self.logger.info("Database engine closed")

    @staticmethod
    async def create_tables(database_url: str) -> None:
        """Create database tables without running migrations."""
        try:
            logger.info("Creating database tables")

            # Ensure we're using appropriate driver
            if database_url.startswith("sqlite:///"):
                database_url = database_url.replace("sqlite:///", "sqlite+aiosqlite:///")
            elif database_url.startswith("mysql+pymysql://"):
                # For MySQL, use direct connection
                await DatabaseManager._create_mysql_tables(database_url)
                return

            engine = create_async_engine(database_url, echo=False)

            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

            await engine.dispose()

            logger.info("Database tables created successfully")

        except Exception as e:
            logger.error("Failed to create database tables", error=str(e))
            raise

    @staticmethod
    async def check_connection(database_url: str) -> bool:
        """Check if database connection is working."""
        try:
            # Ensure we're using appropriate driver
            if database_url.startswith("sqlite:///"):
                database_url = database_url.replace("sqlite:///", "sqlite+aiosqlite:///")
            elif database_url.startswith("mysql+pymysql://"):
                # For MySQL, use direct connection
                return await DatabaseManager._check_mysql_connection(database_url)

            engine = create_async_engine(database_url, echo=False)

            async with engine.begin() as conn:
                await conn.execute(text("SELECT 1"))

            await engine.dispose()
            return True

        except Exception as e:
            logger.error("Database connection check failed", error=str(e))
            return False

    @staticmethod
    async def _create_mysql_tables(database_url: str) -> None:
        """Create MySQL tables using direct SQL execution (static method)."""
        try:
            # Parse MySQL connection string
            from urllib.parse import urlparse
            parsed_url = urlparse(database_url)

            # Extract connection parameters
            db_name = parsed_url.path[1:]  # Remove leading slash

            # Connect to MySQL server (without specific database first)
            conn = await aiomysql.connect(
                host=parsed_url.hostname,
                port=parsed_url.port or 3306,
                user=parsed_url.username,
                password=parsed_url.password,
                autocommit=True
            )

            cursor = await conn.cursor()

            # Create database if it doesn't exist
            await cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            await cursor.execute(f"USE `{db_name}`")

            # Read and execute schema SQL
            schema_path = "scripts/init_db_mysql.sql"
            with open(schema_path, 'r') as f:
                schema_sql = f.read()

            # Split SQL into individual statements and execute
            statements = [stmt.strip() for stmt in schema_sql.split(';') if stmt.strip()]

            for statement in statements:
                if statement:
                    try:
                        await cursor.execute(statement)
                    except Exception as e:
                        # Ignore errors for duplicate indexes or other non-critical issues
                        if "Duplicate key name" not in str(e) and "Already exists" not in str(e):
                            logger.warning(f"SQL statement warning: {e}")

            await cursor.close()
            conn.close()

            logger.info("MySQL tables created successfully")

        except Exception as e:
            logger.error("Failed to create MySQL tables", error=str(e))
            raise

    @staticmethod
    async def _check_mysql_connection(database_url: str) -> bool:
        """Check MySQL database connection."""
        try:
            # Parse MySQL connection string
            from urllib.parse import urlparse
            parsed_url = urlparse(database_url)

            # Extract connection parameters
            db_name = parsed_url.path[1:]  # Remove leading slash

            # Connect to MySQL server
            conn = await aiomysql.connect(
                host=parsed_url.hostname,
                port=parsed_url.port or 3306,
                user=parsed_url.username,
                password=parsed_url.password,
                db=db_name,
                autocommit=True
            )

            cursor = await conn.cursor()
            await cursor.execute("SELECT 1")
            result = await cursor.fetchone()

            await cursor.close()
            conn.close()

            return result is not None

        except Exception as e:
            logger.error("MySQL connection check failed", error=str(e))
            return False


# Global database manager instance
_db_manager: Optional[DatabaseManager] = None


def get_db_manager(database_url: str) -> DatabaseManager:
    """Get or create database manager instance."""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager(database_url)
    return _db_manager


async def init_database(database_url: str) -> AsyncEngine:
    """Initialize database and return engine."""
    db_manager = get_db_manager(database_url)
    return await db_manager.initialize()


async def run_db_migrations(database_url: str) -> None:
    """Run database migrations."""
    db_manager = get_db_manager(database_url)
    await db_manager.run_migrations()


async def close_database() -> None:
    """Close database connection."""
    global _db_manager
    if _db_manager:
        await _db_manager.close()
        _db_manager = None