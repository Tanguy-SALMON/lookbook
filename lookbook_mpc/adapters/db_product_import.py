"""
Product Import Repository Adapter

This adapter handles database operations for product import jobs and metadata.
"""

import json
import uuid
from typing import Dict, Any, Optional
from datetime import datetime
import logging
import structlog
import sqlite3
import asyncio
import aiomysql
from urllib.parse import urlparse

logger = structlog.get_logger()


class ProductImportRepository:
    """Repository for product import jobs and metadata using SQLite."""

    def __init__(self, database_url: str):
        # Extract database path from URL
        if database_url.startswith("sqlite:///"):
            self.db_path = database_url[10:]  # Remove "sqlite:///"
        else:
            self.db_path = database_url

        self.logger = logger.bind(adapter="product_import_sqlite")
        self._lock = asyncio.Lock()


class MySQLProductImportRepository:
    """Repository for product import jobs and metadata using MySQL."""

    def __init__(self, database_url: str):
        self.database_url = database_url
        self.logger = logger.bind(adapter="product_import_mysql")
        self._lock = asyncio.Lock()
        self._parsed_url = urlparse(database_url)

        # Handle special characters in password
        if self._parsed_url.password and "@COS(*)" in self._parsed_url.password:
            self.password = self._parsed_url.password.replace("@COS(*)", "@COS(*)")
        else:
            self.password = self._parsed_url.password

    async def _get_connection(self):
        """Get database connection."""
        return await aiomysql.connect(
            host=self._parsed_url.hostname,
            port=self._parsed_url.port or 3306,
            user=self._parsed_url.username,
            password=self.password,
            db=self._parsed_url.path[1:],  # Remove leading slash
            autocommit=True,
        )

    async def _get_connection(self):
        """Get database connection."""
        return await aiomysql.connect(
            host=self._parsed_url.hostname,
            port=self._parsed_url.port or 3306,
            user=self._parsed_url.username,
            password=self.password,
            db=self._parsed_url.path[1:],  # Remove leading slash
            autocommit=True,
        )

    async def get_meta(self, key: str) -> Optional[str]:
        """
        Get metadata value by key.

        Args:
            key: Metadata key

        Returns:
            Value string or None if not found
        """
        try:
            self.logger.debug("Getting metadata", key=key)

            async with self._lock:
                conn = await self._get_connection()
                cursor = await conn.cursor()

                await cursor.execute(
                    "SELECT value FROM product_import_meta WHERE `key` = %s",
                    (key,)
                )
                row = await cursor.fetchone()

                conn.close()

                if row:
                    self.logger.debug("Found metadata", key=key, value=row[0])
                    return row[0]
                else:
                    self.logger.debug("Metadata not found", key=key)
                    return None

        except Exception as e:
            self.logger.error("Error getting metadata", key=key, error=str(e))
            raise

    async def set_meta(self, key: str, value: str) -> None:
        """
        Set metadata value by key.

        Args:
            key: Metadata key
            value: Value to store
        """
        try:
            self.logger.debug("Setting metadata", key=key, value=value)

            async with self._lock:
                conn = await self._get_connection()
                cursor = await conn.cursor()

                # Use INSERT ... ON DUPLICATE KEY UPDATE for MySQL upsert
                await cursor.execute(
                    """
                    INSERT INTO product_import_meta (`key`, value, updated_at)
                    VALUES (%s, %s, %s)
                    ON DUPLICATE KEY UPDATE value = VALUES(value), updated_at = VALUES(updated_at)
                    """,
                    (key, value, datetime.utcnow().isoformat())
                )

                conn.close()

                self.logger.debug("Set metadata successfully", key=key)

        except Exception as e:
            self.logger.error("Error setting metadata", key=key, error=str(e))
            raise

    async def create_job(self, params: Dict[str, Any]) -> str:
        """
        Create a new import job.

        Args:
            params: Job parameters

        Returns:
            Job ID (UUID)
        """
        try:
            job_id = str(uuid.uuid4())
            self.logger.info("Creating import job", job_id=job_id, params=params)

            async with self._lock:
                conn = await self._get_connection()
                cursor = await conn.cursor()

                await cursor.execute(
                    """
                    INSERT INTO product_import_jobs (id, status, params, metrics)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (
                        job_id,
                        'queued',
                        json.dumps(params),
                        json.dumps({
                            'total_found': 0,
                            'processed': 0,
                            'inserted': 0,
                            'updated': 0,
                            'skipped': 0,
                            'errors_count': 0,
                            'elapsed_ms': 0,
                            'last_processed_source_id': None
                        })
                    )
                )

                conn.close()

                self.logger.info("Created import job", job_id=job_id)
                return job_id

        except Exception as e:
            self.logger.error("Error creating import job", error=str(e))
            raise

    async def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get job by ID.

        Args:
            job_id: Job identifier

        Returns:
            Job data or None if not found
        """
        try:
            self.logger.debug("Getting import job", job_id=job_id)

            async with self._lock:
                conn = await self._get_connection()
                cursor = await conn.cursor(aiomysql.DictCursor)

                await cursor.execute(
                    "SELECT * FROM product_import_jobs WHERE id = %s",
                    (job_id,)
                )
                row = await cursor.fetchone()

                conn.close()

                if row:
                    job_data = {
                        'id': row['id'],
                        'status': row['status'],
                        'params': json.loads(row['params']) if row['params'] else {},
                        'metrics': json.loads(row['metrics']) if row['metrics'] else {},
                        'created_at': row['created_at'].isoformat() if row['created_at'] else None,
                        'started_at': row['started_at'].isoformat() if row['started_at'] else None,
                        'finished_at': row['finished_at'].isoformat() if row['finished_at'] else None,
                        'error_message': row['error_message']
                    }
                    self.logger.debug("Found import job", job_id=job_id, status=job_data['status'])
                    return job_data
                else:
                    self.logger.warning("Import job not found", job_id=job_id)
                    return None

        except Exception as e:
            self.logger.error("Error getting import job", job_id=job_id, error=str(e))
            raise

    async def update_job_status(self, job_id: str, status: str, started_at: Optional[str] = None,
                               finished_at: Optional[str] = None, error_message: Optional[str] = None) -> None:
        """
        Update job status and timestamps.

        Args:
            job_id: Job identifier
            status: New status
            started_at: Started timestamp (ISO format)
            finished_at: Finished timestamp (ISO format)
            error_message: Error message if failed
        """
        try:
            self.logger.info("Updating job status", job_id=job_id, status=status)

            async with self._lock:
                conn = await self._get_connection()
                cursor = await conn.cursor()

                update_fields = ["status = %s"]
                params = [status]

                if started_at is not None:
                    update_fields.append("started_at = %s")
                    params.append(started_at)

                if finished_at is not None:
                    update_fields.append("finished_at = %s")
                    params.append(finished_at)

                if error_message is not None:
                    update_fields.append("error_message = %s")
                    params.append(error_message)

                params.append(job_id)  # WHERE clause

                query = f"UPDATE product_import_jobs SET {', '.join(update_fields)} WHERE id = %s"
                await cursor.execute(query, params)

                conn.close()

                self.logger.debug("Updated job status", job_id=job_id, status=status)

        except Exception as e:
            self.logger.error("Error updating job status", job_id=job_id, status=status, error=str(e))
            raise

    async def update_job_metrics(self, job_id: str, metrics: Dict[str, Any]) -> None:
        """
        Update job metrics.

        Args:
            job_id: Job identifier
            metrics: Metrics dictionary
        """
        try:
            self.logger.debug("Updating job metrics", job_id=job_id, metrics=metrics)

            async with self._lock:
                conn = await self._get_connection()
                cursor = await conn.cursor()

                await cursor.execute(
                    "UPDATE product_import_jobs SET metrics = %s WHERE id = %s",
                    (json.dumps(metrics), job_id)
                )

                conn.close()

                self.logger.debug("Updated job metrics", job_id=job_id)

        except Exception as e:
            self.logger.error("Error updating job metrics", job_id=job_id, error=str(e))
            raise