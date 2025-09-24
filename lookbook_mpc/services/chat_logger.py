"""
Chat Logging Service

This service handles comprehensive logging of all chat interactions to the database.
It tracks messages, responses, performance metrics, and business intelligence data.
"""

import json
import time
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
import pymysql
from dataclasses import dataclass

from ..config import settings


@dataclass
class ChatLogEntry:
    """Data structure for a chat log entry."""

    session_id: str
    request_id: str
    user_message: str
    ai_response: Optional[str] = None
    ai_response_type: str = "general"
    parsed_intent: Optional[Dict] = None
    intent_confidence: Optional[float] = None
    intent_parser_type: str = "mock"
    strategy_config: Optional[Dict] = None
    tone_applied: Optional[str] = None
    system_directive: Optional[str] = None
    outfits_count: int = 0
    outfits_data: Optional[List] = None
    response_time_ms: Optional[int] = None
    intent_parsing_time_ms: Optional[int] = None
    recommendation_time_ms: Optional[int] = None
    user_ip: Optional[str] = None
    user_agent: Optional[str] = None
    language_detected: Optional[str] = None
    conversation_turn_number: int = 1
    previous_message_id: Optional[int] = None
    is_follow_up: bool = False
    error_occurred: bool = False
    error_message: Optional[str] = None
    error_stack_trace: Optional[str] = None


class ChatLogger:
    """Service for logging chat interactions to database."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def _get_db_connection(self):
        """Get database connection."""
        return pymysql.connect(
            host="127.0.0.1",
            port=3306,
            user="magento",
            password="Magento@COS(*)",
            database="lookbookMPC",
            charset="utf8mb4",
        )

    def log_chat_interaction(self, log_entry: ChatLogEntry) -> Optional[int]:
        """
        Log a complete chat interaction to the database.

        Args:
            log_entry: Chat log entry data

        Returns:
            The ID of the logged entry, or None if failed
        """
        try:
            connection = self._get_db_connection()
            with connection.cursor() as cursor:
                # Insert chat log entry
                insert_sql = """
                INSERT INTO chat_logs (
                    session_id, request_id, user_message, user_message_timestamp,
                    ai_response, ai_response_type, ai_response_timestamp,
                    parsed_intent, intent_confidence, intent_parser_type,
                    strategy_config, tone_applied, system_directive,
                    outfits_count, outfits_data, recommendation_engine_version,
                    response_time_ms, intent_parsing_time_ms, recommendation_time_ms,
                    user_ip, user_agent, language_detected,
                    conversation_turn_number, previous_message_id, is_follow_up,
                    error_occurred, error_message, error_stack_trace,
                    created_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                """

                values = (
                    log_entry.session_id,
                    log_entry.request_id,
                    log_entry.user_message,
                    datetime.now(),  # user_message_timestamp
                    log_entry.ai_response,
                    log_entry.ai_response_type,
                    datetime.now()
                    if log_entry.ai_response
                    else None,  # ai_response_timestamp
                    json.dumps(log_entry.parsed_intent)
                    if log_entry.parsed_intent
                    else None,
                    log_entry.intent_confidence,
                    log_entry.intent_parser_type,
                    json.dumps(log_entry.strategy_config)
                    if log_entry.strategy_config
                    else None,
                    log_entry.tone_applied,
                    log_entry.system_directive,
                    log_entry.outfits_count,
                    json.dumps(log_entry.outfits_data)
                    if log_entry.outfits_data
                    else None,
                    "v1",  # recommendation_engine_version
                    log_entry.response_time_ms,
                    log_entry.intent_parsing_time_ms,
                    log_entry.recommendation_time_ms,
                    log_entry.user_ip,
                    log_entry.user_agent,
                    log_entry.language_detected,
                    log_entry.conversation_turn_number,
                    log_entry.previous_message_id,
                    log_entry.is_follow_up,
                    log_entry.error_occurred,
                    log_entry.error_message,
                    log_entry.error_stack_trace,
                    datetime.now(),  # created_at
                )

                cursor.execute(insert_sql, values)
                log_id = cursor.lastrowid

            connection.commit()
            connection.close()

            # Update session statistics
            self._update_session_stats(log_entry.session_id, log_entry)

            return log_id

        except Exception as e:
            self.logger.error(f"Error logging chat interaction: {e}")
            if "connection" in locals():
                connection.rollback()
                connection.close()
            return None

    def _update_session_stats(self, session_id: str, log_entry: ChatLogEntry):
        """Update session statistics."""
        try:
            connection = self._get_db_connection()
            with connection.cursor() as cursor:
                # Update or create session record
                upsert_sql = """
                INSERT INTO chat_sessions (
                    session_id, total_messages, total_recommendations,
                    avg_response_time_ms, last_activity, created_at, name
                ) VALUES (%s, 1, %s, %s, %s, %s, NULL)
                ON DUPLICATE KEY UPDATE
                total_messages = total_messages + 1,
                total_recommendations = total_recommendations + %s,
                avg_response_time_ms = CASE
                    WHEN avg_response_time_ms IS NULL THEN %s
                    ELSE (avg_response_time_ms + %s) / 2
                END,
                last_activity = %s
                """

                now = datetime.now()
                values = (
                    session_id,
                    log_entry.outfits_count,  # total_recommendations (initial)
                    log_entry.response_time_ms,  # avg_response_time_ms (initial)
                    now,  # last_activity (initial)
                    now,  # created_at (initial)
                    log_entry.outfits_count,  # total_recommendations (update)
                    log_entry.response_time_ms,  # avg_response_time_ms (for average calc)
                    log_entry.response_time_ms,  # avg_response_time_ms (for average calc)
                    now,  # last_activity (update)
                )

                cursor.execute(upsert_sql, values)

            connection.commit()
            connection.close()

        except Exception as e:
            self.logger.error(f"Error updating session stats: {e}")

    def get_conversation_history(self, session_id: str, limit: int = 20) -> List[Dict]:
        """
        Get conversation history for a session.

        Args:
            session_id: Session identifier
            limit: Maximum number of messages to return

        Returns:
            List of conversation messages
        """
        try:
            connection = self._get_db_connection()
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT user_message, ai_response, ai_response_type, outfits_count,
                           created_at, conversation_turn_number, error_occurred
                    FROM chat_logs
                    WHERE session_id = %s
                    ORDER BY created_at DESC
                    LIMIT %s
                """,
                    (session_id, limit),
                )

                results = cursor.fetchall()

                history = []
                for row in results:
                    history.append(
                        {
                            "user_message": row[0],
                            "ai_response": row[1],
                            "ai_response_type": row[2],
                            "outfits_count": row[3],
                            "timestamp": row[4].isoformat(),
                            "turn_number": row[5],
                            "error_occurred": bool(row[6]),
                        }
                    )

            connection.close()
            return list(reversed(history))  # Return in chronological order

        except Exception as e:
            self.logger.error(f"Error getting conversation history: {e}")
            return []

    def get_session_context(self, session_id: str) -> Dict[str, Any]:
        """
        Get context information for a session.

        Args:
            session_id: Session identifier

        Returns:
            Session context data
        """
        try:
            connection = self._get_db_connection()
            with connection.cursor() as cursor:
                # Get session data
                cursor.execute(
                    """
                    SELECT total_messages, total_recommendations, context_data,
                           current_strategy, created_at, last_activity
                    FROM chat_sessions
                    WHERE session_id = %s
                """,
                    (session_id,),
                )

                session_result = cursor.fetchone()

                # Get last message for turn number
                cursor.execute(
                    """
                    SELECT conversation_turn_number, language_detected
                    FROM chat_logs
                    WHERE session_id = %s
                    ORDER BY created_at DESC
                    LIMIT 1
                """,
                    (session_id,),
                )

                last_message_result = cursor.fetchone()

            connection.close()

            context = {
                "session_id": session_id,
                "total_messages": session_result[0] if session_result else 0,
                "total_recommendations": session_result[1] if session_result else 0,
                "context_data": json.loads(session_result[2])
                if session_result and session_result[2]
                else {},
                "current_strategy": json.loads(session_result[3])
                if session_result and session_result[3]
                else None,
                "created_at": session_result[4].isoformat() if session_result else None,
                "last_activity": session_result[5].isoformat()
                if session_result
                else None,
                "next_turn_number": (last_message_result[0] + 1)
                if last_message_result
                else 1,
                "language_detected": last_message_result[1]
                if last_message_result
                else None,
            }

            return context

        except Exception as e:
            self.logger.error(f"Error getting session context: {e}")
            return {
                "session_id": session_id,
                "total_messages": 0,
                "total_recommendations": 0,
                "context_data": {},
                "next_turn_number": 1,
            }

    def log_user_action(self, session_id: str, action: str, data: Dict[str, Any]):
        """
        Log user action (clicks, purchases, etc.) for business intelligence.

        Args:
            session_id: Session identifier
            action: Action type (click, purchase, add_to_cart, etc.)
            data: Action data
        """
        try:
            # For now, update the last chat log entry with the action
            connection = self._get_db_connection()
            with connection.cursor() as cursor:
                # Get the most recent message ID for this session
                cursor.execute(
                    """
                    SELECT id FROM chat_logs
                    WHERE session_id = %s
                    ORDER BY created_at DESC
                    LIMIT 1
                """,
                    (session_id,),
                )

                result = cursor.fetchone()
                if result:
                    message_id = result[0]

                    # Update with user action
                    if action == "click_recommendation":
                        cursor.execute(
                            """
                            UPDATE chat_logs
                            SET clicked_recommendations = %s
                            WHERE id = %s
                        """,
                            (json.dumps(data), message_id),
                        )
                    elif action in ["purchase", "add_to_cart"]:
                        cursor.execute(
                            """
                            UPDATE chat_logs
                            SET conversion_events = %s
                            WHERE id = %s
                        """,
                            (json.dumps({action: data}), message_id),
                        )

            connection.commit()
            connection.close()

        except Exception as e:
            self.logger.error(f"Error logging user action: {e}")

    def get_performance_metrics(self, days: int = 7) -> Dict[str, Any]:
        """
        Get performance metrics for the chat system.

        Args:
            days: Number of days to analyze

        Returns:
            Performance metrics dictionary
        """
        try:
            connection = self._get_db_connection()
            with connection.cursor() as cursor:
                # Get metrics from the last N days
                cursor.execute(
                    """
                    SELECT
                        COUNT(*) as total_messages,
                        COUNT(DISTINCT session_id) as unique_sessions,
                        AVG(response_time_ms) as avg_response_time,
                        AVG(outfits_count) as avg_recommendations_per_message,
                        SUM(CASE WHEN error_occurred = 1 THEN 1 ELSE 0 END) as error_count,
                        SUM(outfits_count) as total_recommendations
                    FROM chat_logs
                    WHERE created_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
                """,
                    (days,),
                )

                metrics = cursor.fetchone()

                # Get response type distribution
                cursor.execute(
                    """
                    SELECT ai_response_type, COUNT(*) as count
                    FROM chat_logs
                    WHERE created_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
                    GROUP BY ai_response_type
                """,
                    (days,),
                )

                response_types = cursor.fetchall()

            connection.close()

            return {
                "period_days": days,
                "total_messages": metrics[0] or 0,
                "unique_sessions": metrics[1] or 0,
                "avg_response_time_ms": round(metrics[2] or 0, 2),
                "avg_recommendations_per_message": round(metrics[3] or 0, 2),
                "error_count": metrics[4] or 0,
                "error_rate": round(
                    (metrics[4] or 0) / max(metrics[0] or 1, 1) * 100, 2
                ),
                "total_recommendations": metrics[5] or 0,
                "response_type_distribution": {
                    row[0]: row[1] for row in response_types
                },
            }

        except Exception as e:
            self.logger.error(f"Error getting performance metrics: {e}")
            return {
                "period_days": days,
                "total_messages": 0,
                "unique_sessions": 0,
                "avg_response_time_ms": 0,
                "error_count": 0,
                "error_rate": 0,
            }

    def update_session_satisfaction(self, session_id: str, score: float):
        """
        Update satisfaction score for a session.

        Args:
            session_id: Session identifier
            score: Satisfaction score (0.0 to 5.0)
        """
        try:
            connection = self._get_db_connection()
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE chat_sessions
                    SET satisfaction_score = %s
                    WHERE session_id = %s
                """,
                    (score, session_id),
                )

            connection.commit()
            connection.close()

        except Exception as e:
            self.logger.error(f"Error updating satisfaction score: {e}")
