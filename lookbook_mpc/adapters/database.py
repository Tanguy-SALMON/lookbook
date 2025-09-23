"""
Database Utilities

This module provides utilities for database initialization, connection,
and management for the lookbook system.
"""

import asyncio
import logging
from typing import Optional
import structlog
import aiomysql
import pymysql
from lookbook_mpc.config.settings import get_settings

logger = structlog.get_logger()


class DatabaseManager:
    """Database manager for handling database operations."""

    def __init__(self, database_url: str):
        self.database_url = database_url
        self.logger = logger.bind(database_url=database_url)

    async def initialize(self) -> None:
        """Initialize database and create tables."""
        try:
            self.logger.info("Initializing database")
            await self._create_mysql_tables()
            self.logger.info("Database initialized successfully")
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
                autocommit=True,
            )

            cursor = await conn.cursor()

            # Create database if it doesn't exist
            await cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
            await cursor.execute(f"USE `{db_name}`")

            # Read and execute schema SQL
            schema_path = "scripts/init_db_mysql.sql"
            with open(schema_path, "r") as f:
                schema_sql = f.read()

            # Split SQL into individual statements and execute
            statements = [
                stmt.strip() for stmt in schema_sql.split(";") if stmt.strip()
            ]

            for statement in statements:
                if statement:
                    try:
                        await cursor.execute(statement)
                    except Exception as e:
                        # Ignore errors for duplicate indexes or other non-critical issues
                        if "Duplicate key name" not in str(
                            e
                        ) and "Already exists" not in str(e):
                            self.logger.warning(f"SQL statement warning: {e}")

            await cursor.close()
            conn.close()

            self.logger.info("MySQL tables created successfully")

        except Exception as e:
            self.logger.error("Failed to create MySQL tables", error=str(e))
            raise

    async def run_migrations(self) -> None:
        """Run database migrations using direct SQL."""
        try:
            self.logger.info("Running database migrations using direct SQL schema")
            # Schema is already created in initialize(), so this is a no-op
            self.logger.info("Database migrations completed successfully")
        except Exception as e:
            self.logger.error("Failed to run migrations", error=str(e))
            raise

    async def close(self) -> None:
        """Close database connections."""
        self.logger.info("Database connections closed")

    @staticmethod
    async def create_tables(database_url: str) -> None:
        """Create database tables without running migrations."""
        try:
            logger.info("Creating database tables")
            await DatabaseManager._create_mysql_tables(database_url)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error("Failed to create database tables", error=str(e))
            raise

    @staticmethod
    async def check_connection(database_url: str) -> bool:
        """Check if database connection is working."""
        try:
            return await DatabaseManager._check_mysql_connection(database_url)
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
                autocommit=True,
            )

            cursor = await conn.cursor()

            # Create database if it doesn't exist
            await cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
            await cursor.execute(f"USE `{db_name}`")

            # Read and execute schema SQL
            schema_path = "scripts/init_db_mysql.sql"
            with open(schema_path, "r") as f:
                schema_sql = f.read()

            # Split SQL into individual statements and execute
            statements = [
                stmt.strip() for stmt in schema_sql.split(";") if stmt.strip()
            ]

            for statement in statements:
                if statement:
                    try:
                        await cursor.execute(statement)
                    except Exception as e:
                        # Ignore errors for duplicate indexes or other non-critical issues
                        if "Duplicate key name" not in str(
                            e
                        ) and "Already exists" not in str(e):
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
                autocommit=True,
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


async def init_database(database_url: str) -> None:
    """Initialize database."""
    db_manager = get_db_manager(database_url)
    await db_manager.initialize()


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


def get_db_connection():
    """Get synchronous database connection using PyMySQL."""
    from urllib.parse import urlparse

    settings = get_settings()
    db_url = settings.get_database_url()

    # Parse database URL
    parsed_url = urlparse(db_url)

    return pymysql.connect(
        host=parsed_url.hostname or "127.0.0.1",
        port=parsed_url.port or 3306,
        user=parsed_url.username or "magento",
        password=parsed_url.password or "password",
        db=parsed_url.path[1:]
        if parsed_url.path
        else "lookbook_mpc",  # Remove leading slash
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
    )
