#!/usr/bin/env python3
"""
Script to populate chat_sessions table from existing chat_logs.
This is needed when chat_logs are inserted directly into the database
without going through the chat logger.
"""

import pymysql
import logging
from datetime import datetime

# Database configuration
DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "magento",
    "password": "Magento@COS(*)",
    "database": "lookbookMPC",
    "charset": "utf8mb4",
}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get database connection."""
    return pymysql.connect(**DB_CONFIG)

def populate_sessions():
    """Populate chat_sessions table from chat_logs."""
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Get all distinct session_ids from chat_logs
            cursor.execute("""
                SELECT DISTINCT session_id
                FROM chat_logs
                ORDER BY session_id
            """)

            session_ids = [row[0] for row in cursor.fetchall()]

            logger.info(f"Found {len(session_ids)} unique sessions in chat_logs")

            for session_id in session_ids:
                # Get session statistics
                cursor.execute("""
                    SELECT
                        COUNT(*) as total_messages,
                        SUM(CASE WHEN outfits_count > 0 THEN outfits_count ELSE 0 END) as total_recommendations,
                        MIN(created_at) as first_message_time,
                        MAX(created_at) as last_message_time,
                        AVG(response_time_ms) as avg_response_time
                    FROM chat_logs
                    WHERE session_id = %s
                """, (session_id,))

                stats = cursor.fetchone()
                total_messages, total_recommendations, first_time, last_time, avg_response_time = stats

                # Insert or update session
                cursor.execute("""
                    INSERT INTO chat_sessions (
                        session_id, total_messages, total_recommendations,
                        avg_response_time_ms, last_activity, created_at, is_active
                    ) VALUES (%s, %s, %s, %s, %s, %s, 1)
                    ON DUPLICATE KEY UPDATE
                        total_messages = VALUES(total_messages),
                        total_recommendations = VALUES(total_recommendations),
                        avg_response_time_ms = VALUES(avg_response_time_ms),
                        last_activity = VALUES(last_activity)
                """, (
                    session_id,
                    total_messages,
                    total_recommendations or 0,
                    avg_response_time or 0,
                    last_time,
                    first_time
                ))

                logger.info(f"Processed session {session_id}: {total_messages} messages, {total_recommendations or 0} recommendations")

        connection.commit()
        logger.info("Successfully populated chat_sessions table")

        # Verify the results
        cursor.execute("SELECT COUNT(*) FROM chat_sessions")
        total_sessions = cursor.fetchone()[0]
        logger.info(f"Total sessions in chat_sessions table: {total_sessions}")

    except Exception as e:
        logger.error(f"Error populating sessions: {e}")
        if 'connection' in locals():
            connection.rollback()
    finally:
        if 'connection' in locals():
            connection.close()

if __name__ == "__main__":
    populate_sessions()