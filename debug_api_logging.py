#!/usr/bin/env python3
"""
Debug script to test the exact API flow that might be causing logging issues.
This will simulate the same data flow as the chat API endpoint.
"""

import sys
import os
import json
import uuid
import time
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lookbook_mpc.services.chat_logger import ChatLogger, ChatLogEntry
from lookbook_mpc.services.strategy import StrategyService
from lookbook_mpc.api.routers.chat import sessions


def simulate_api_request():
    """Simulate the exact flow from the chat API."""
    print("=== Simulating API Request Flow ===")

    # Simulate request data
    session_id = f"debug_api_test_{int(time.time())}"
    message = "I need help with a party outfit"

    print(f"Session ID: {session_id}")
    print(f"Message: {message}")

    try:
        # Initialize services like in the real API
        strategy_service = StrategyService()
        chat_logger = ChatLogger()

        # Get session context
        session_context = chat_logger.get_session_context(session_id)
        print(f"Session context: {session_context}")

        # Get strategy
        strategy = strategy_service.get_strategy(session_id)
        print(f"Strategy name: {strategy.name}")

        # Build system directive
        system_directive = strategy_service.build_system_directive(strategy)
        print(f"System directive length: {len(system_directive)} chars")

        # Simulate response data
        response_time_ms = 250
        intent_time = 75
        request_id = str(uuid.uuid4())

        # Simulate response structure
        response_data = {
            "session_id": session_id,
            "request_id": request_id,
            "replies": [
                {
                    "message": "I'll help you find a perfect party outfit!",
                    "type": "recommendations",
                }
            ],
            "outfits": [
                {
                    "title": "Party Look",
                    "items": [
                        {
                            "sku": "TEST123",
                            "title": "Test Item",
                            "price": 1500.0,
                            "color": "black",
                        }
                    ],
                    "total_price": 1500.0,
                }
            ],
        }

        print(f"Response outfits count: {len(response_data['outfits'])}")

        # Create log entry with exact same data as API
        print("\n=== Creating Log Entry ===")

        log_entry = ChatLogEntry(
            session_id=response_data["session_id"],
            request_id=response_data["request_id"],
            user_message=message,
            ai_response=response_data["replies"][0]["message"]
            if response_data["replies"]
            else None,
            ai_response_type=response_data["replies"][0].get("type", "general")
            if response_data["replies"]
            else "general",
            strategy_config={
                "name": strategy.name,
                "tone": strategy.tone,
                "language": strategy.language,
                "objectives": strategy.objectives,
                "guardrails": strategy.guardrails,
                "style_config": strategy.style_config,
            },
            tone_applied=strategy.tone,
            system_directive=system_directive,
            outfits_count=len(response_data["outfits"])
            if response_data["outfits"]
            else 0,
            outfits_data=response_data["outfits"] if response_data["outfits"] else None,
            response_time_ms=response_time_ms,
            intent_parsing_time_ms=intent_time,
            conversation_turn_number=session_context["next_turn_number"],
            is_follow_up=session_context["total_messages"] > 0,
            intent_parser_type="hybrid",
        )

        print("✅ Log entry created successfully")

        # Try to log it
        print("\n=== Attempting Database Log ===")
        log_id = chat_logger.log_chat_interaction(log_entry)

        if log_id:
            print(f"✅ Successfully logged with ID: {log_id}")

            # Verify it was saved
            print("\n=== Verifying Database Entry ===")
            import pymysql

            conn = pymysql.connect(
                host="127.0.0.1",
                port=3306,
                user="magento",
                password="Magento@COS(*)",
                database="lookbookMPC",
                charset="utf8mb4",
            )

            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT id, session_id, user_message, ai_response, outfits_count, created_at "
                    "FROM chat_logs WHERE id = %s",
                    (log_id,),
                )
                result = cursor.fetchone()

                if result:
                    print("✅ Entry verified in database:")
                    print(f"   ID: {result[0]}")
                    print(f"   Session: {result[1]}")
                    print(f"   User Message: {result[2][:50]}...")
                    print(f"   AI Response: {result[3][:50]}...")
                    print(f"   Outfits Count: {result[4]}")
                    print(f"   Created: {result[5]}")
                    return True
                else:
                    print("❌ Entry not found in database!")
                    return False

            conn.close()
        else:
            print("❌ Logging returned None")
            return False

    except Exception as e:
        print(f"❌ Error in simulation: {e}")
        import traceback

        traceback.print_exc()
        return False


def check_recent_logs():
    """Check the most recent log entries."""
    print("\n=== Recent Log Entries ===")
    try:
        import pymysql

        conn = pymysql.connect(
            host="127.0.0.1",
            port=3306,
            user="magento",
            password="Magento@COS(*)",
            database="lookbookMPC",
            charset="utf8mb4",
        )

        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT id, session_id, user_message, created_at "
                "FROM chat_logs ORDER BY created_at DESC LIMIT 5"
            )
            results = cursor.fetchall()

            for row in results:
                print(
                    f"ID: {row[0]}, Session: {row[1]}, Message: {row[2][:30]}..., Time: {row[3]}"
                )

        conn.close()

    except Exception as e:
        print(f"❌ Error checking recent logs: {e}")


def test_json_serialization():
    """Test JSON serialization of complex objects."""
    print("\n=== Testing JSON Serialization ===")

    try:
        strategy_service = StrategyService()
        strategy = strategy_service.get_strategy("test_session")

        # Test strategy config serialization
        strategy_config = {
            "name": strategy.name,
            "tone": strategy.tone,
            "language": strategy.language,
            "objectives": strategy.objectives,
            "guardrails": strategy.guardrails,
            "style_config": strategy.style_config,
        }

        json_str = json.dumps(strategy_config)
        print(f"✅ Strategy config JSON: {len(json_str)} chars")

        # Test outfits data serialization
        outfits_data = [
            {
                "title": "Test Outfit",
                "items": [{"sku": "TEST", "price": 100.0}],
                "total_price": 100.0,
            }
        ]

        json_str = json.dumps(outfits_data)
        print(f"✅ Outfits data JSON: {len(json_str)} chars")

        return True

    except Exception as e:
        print(f"❌ JSON serialization failed: {e}")
        return False


def main():
    """Run all debug tests."""
    print("🔍 API Logging Debug Script")
    print("=" * 50)

    # Check recent logs first
    check_recent_logs()

    # Test JSON serialization
    if not test_json_serialization():
        print("❌ JSON serialization issues detected")
        return False

    # Simulate API request
    if not simulate_api_request():
        print("❌ API simulation failed")
        return False

    print("\n✅ API logging simulation completed successfully!")
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
