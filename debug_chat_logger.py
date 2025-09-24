#!/usr/bin/env python3
"""
Debug script to test ChatLogger functionality directly.
This script will help identify issues with chat logging.
"""

import sys
import os
import json
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lookbook_mpc.services.chat_logger import ChatLogger, ChatLogEntry


def test_database_connection():
    """Test basic database connection."""
    print("=== Testing Database Connection ===")
    try:
        logger = ChatLogger()
        conn = logger._get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1 as test")
            result = cursor.fetchone()
            print(f"✅ Database connection successful: {result}")
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


def test_chat_log_entry_creation():
    """Test creating a ChatLogEntry."""
    print("\n=== Testing ChatLogEntry Creation ===")
    try:
        log_entry = ChatLogEntry(
            session_id="debug_test_session",
            request_id="debug_request_123",
            user_message="Hello, this is a test message",
            ai_response="Hello! I'm here to help you with fashion recommendations.",
            ai_response_type="general",
            strategy_config={
                "name": "friendly_assistant",
                "tone": "casual",
                "language": "english",
            },
            tone_applied="casual",
            outfits_count=0,
            response_time_ms=150,
            intent_parsing_time_ms=50,
            conversation_turn_number=1,
            is_follow_up=False,
            intent_parser_type="hybrid",
        )
        print("✅ ChatLogEntry created successfully")
        print(f"   Session ID: {log_entry.session_id}")
        print(f"   User Message: {log_entry.user_message}")
        return log_entry
    except Exception as e:
        print(f"❌ ChatLogEntry creation failed: {e}")
        return None


def test_logging_to_database(log_entry):
    """Test logging the entry to database."""
    print("\n=== Testing Database Logging ===")
    try:
        logger = ChatLogger()
        log_id = logger.log_chat_interaction(log_entry)
        if log_id:
            print(f"✅ Chat interaction logged successfully with ID: {log_id}")
            return log_id
        else:
            print("❌ Chat interaction logging returned None")
            return None
    except Exception as e:
        print(f"❌ Chat interaction logging failed: {e}")
        return None


def verify_logged_entry(log_id):
    """Verify the entry was actually saved to database."""
    print(f"\n=== Verifying Logged Entry (ID: {log_id}) ===")
    try:
        logger = ChatLogger()
        conn = logger._get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT id, session_id, user_message, ai_response, created_at "
                "FROM chat_logs WHERE id = %s",
                (log_id,),
            )
            result = cursor.fetchone()
            if result:
                print("✅ Entry found in database:")
                print(f"   ID: {result[0]}")
                print(f"   Session ID: {result[1]}")
                print(f"   User Message: {result[2]}")
                print(f"   AI Response: {result[3]}")
                print(f"   Created At: {result[4]}")
                return True
            else:
                print("❌ Entry not found in database")
                return False
        conn.close()
    except Exception as e:
        print(f"❌ Database verification failed: {e}")
        return False


def test_table_schema():
    """Check if the chat_logs table has the expected schema."""
    print("\n=== Testing Table Schema ===")
    try:
        logger = ChatLogger()
        conn = logger._get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("DESCRIBE chat_logs")
            columns = cursor.fetchall()

        print("✅ chat_logs table schema:")
        for col in columns:
            print(f"   {col[0]} - {col[1]} - {col[2]} - {col[3]}")

        # Check for required columns
        column_names = [col[0] for col in columns]
        required_columns = [
            "id",
            "session_id",
            "request_id",
            "user_message",
            "ai_response",
            "ai_response_type",
            "created_at",
        ]

        missing_columns = [col for col in required_columns if col not in column_names]
        if missing_columns:
            print(f"❌ Missing required columns: {missing_columns}")
            return False
        else:
            print("✅ All required columns present")
            return True

        conn.close()
    except Exception as e:
        print(f"❌ Schema check failed: {e}")
        return False


def main():
    """Run all debug tests."""
    print("🔍 ChatLogger Debug Script")
    print("=" * 50)

    # Test 1: Database connection
    if not test_database_connection():
        print("\n❌ Stopping tests - database connection failed")
        return False

    # Test 2: Table schema
    if not test_table_schema():
        print("\n❌ Stopping tests - table schema issues")
        return False

    # Test 3: Create log entry
    log_entry = test_chat_log_entry_creation()
    if not log_entry:
        print("\n❌ Stopping tests - log entry creation failed")
        return False

    # Test 4: Log to database
    log_id = test_logging_to_database(log_entry)
    if not log_id:
        print("\n❌ Stopping tests - database logging failed")
        return False

    # Test 5: Verify entry exists
    if not verify_logged_entry(log_id):
        print("\n❌ Tests failed - entry not found in database")
        return False

    print("\n✅ All tests passed! ChatLogger is working correctly.")
    print(f"Test entry logged with ID: {log_id}")
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
