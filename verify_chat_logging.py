#!/usr/bin/env python3
"""
Chat Logging Verification Script

This script verifies that the chat logging system is working correctly
by testing both the API endpoint and direct database logging.

Usage:
    poetry run python verify_chat_logging.py

Features:
- Tests API endpoint connectivity
- Verifies database logging functionality
- Checks recent chat logs
- Provides troubleshooting information
"""

import sys
import os
import json
import time
import requests
from datetime import datetime, timedelta

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from lookbook_mpc.services.chat_logger import ChatLogger
    import pymysql
except ImportError as e:
    print(f"❌ Import error: {e}")
    print(
        "Make sure you're running this from the project root with: poetry run python verify_chat_logging.py"
    )
    sys.exit(1)


class ChatLoggingVerifier:
    """Verifies chat logging functionality."""

    def __init__(self):
        self.api_url = "http://localhost:8000"
        self.db_config = {
            "host": "127.0.0.1",
            "port": 3306,
            "user": "magento",
            "password": "Magento@COS(*)",
            "database": "lookbookMPC",
            "charset": "utf8mb4",
        }

    def print_header(self, title):
        """Print formatted section header."""
        print(f"\n{'=' * 60}")
        print(f"🔍 {title}")
        print("=" * 60)

    def test_api_connectivity(self):
        """Test if the FastAPI server is running and accessible."""
        self.print_header("API Connectivity Test")

        try:
            response = requests.get(f"{self.api_url}/health", timeout=5)
            if response.status_code == 200:
                print("✅ FastAPI server is running")
                health_data = response.json()
                print(f"   Status: {health_data.get('status', 'Unknown')}")
                return True
            else:
                print(f"❌ Server responded with status code: {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            print("❌ Cannot connect to FastAPI server")
            print(
                "   Make sure the server is running with: poetry run uvicorn main:app --reload"
            )
            return False
        except Exception as e:
            print(f"❌ API connectivity error: {e}")
            return False

    def test_database_connection(self):
        """Test database connectivity."""
        self.print_header("Database Connection Test")

        try:
            conn = pymysql.connect(**self.db_config)
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1 as test")
                result = cursor.fetchone()
                print("✅ Database connection successful")

                # Check chat_logs table exists
                cursor.execute("SHOW TABLES LIKE 'chat_logs'")
                if cursor.fetchone():
                    print("✅ chat_logs table exists")

                    # Check table structure
                    cursor.execute("SELECT COUNT(*) FROM chat_logs")
                    count = cursor.fetchone()[0]
                    print(f"✅ Total chat logs in database: {count}")
                    return True
                else:
                    print("❌ chat_logs table not found")
                    return False
            conn.close()
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False

    def test_recent_logs(self):
        """Check recent chat logs."""
        self.print_header("Recent Chat Logs")

        try:
            conn = pymysql.connect(**self.db_config)
            with conn.cursor() as cursor:
                # Get logs from last 24 hours
                cursor.execute(
                    """
                    SELECT id, session_id, user_message, ai_response, created_at
                    FROM chat_logs
                    WHERE created_at >= %s
                    ORDER BY created_at DESC
                    LIMIT 10
                """,
                    (datetime.now() - timedelta(hours=24),),
                )

                recent_logs = cursor.fetchall()

                if recent_logs:
                    print(f"✅ Found {len(recent_logs)} recent chat logs:")
                    for i, log in enumerate(recent_logs[:5], 1):
                        log_id, session_id, user_msg, ai_resp, created = log
                        user_msg_short = (
                            (user_msg[:40] + "...") if len(user_msg) > 40 else user_msg
                        )
                        ai_resp_short = (
                            (ai_resp[:40] + "...")
                            if ai_resp and len(ai_resp) > 40
                            else (ai_resp or "None")
                        )
                        print(
                            f"   {i}. ID:{log_id} | {created} | U: {user_msg_short} | A: {ai_resp_short}"
                        )

                    if len(recent_logs) > 5:
                        print(f"   ... and {len(recent_logs) - 5} more")
                    return True
                else:
                    print("⚠️  No recent chat logs found (last 24 hours)")
                    print("   This could mean:")
                    print("   - No chat conversations have happened recently")
                    print("   - Chat logging is not working")
                    print("   - Database clock is incorrect")
                    return False
            conn.close()
        except Exception as e:
            print(f"❌ Error checking recent logs: {e}")
            return False

    def test_live_chat_api(self):
        """Test live chat API with logging verification."""
        self.print_header("Live Chat API Test")

        test_session = f"verify_test_{int(time.time())}"
        test_message = "This is a logging verification test"

        print(f"Testing session: {test_session}")
        print(f"Test message: {test_message}")

        try:
            # Make API request
            response = requests.post(
                f"{self.api_url}/v1/chat",
                json={"session_id": test_session, "message": test_message},
                timeout=30,
            )

            if response.status_code != 200:
                print(f"❌ API request failed with status: {response.status_code}")
                print(f"Response: {response.text}")
                return False

            response_data = response.json()
            print("✅ API request successful")
            print(f"   Response session: {response_data.get('session_id')}")
            print(f"   Replies count: {len(response_data.get('replies', []))}")
            print(f"   Outfits count: {len(response_data.get('outfits', []))}")

            # Wait a moment for logging to complete
            time.sleep(2)

            # Check if it was logged
            conn = pymysql.connect(**self.db_config)
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT id, user_message, ai_response, created_at FROM chat_logs WHERE session_id = %s",
                    (test_session,),
                )
                log_result = cursor.fetchone()

                if log_result:
                    log_id, logged_user_msg, logged_ai_resp, logged_time = log_result
                    print("✅ Chat interaction successfully logged to database")
                    print(f"   Log ID: {log_id}")
                    print(f"   Logged user message: {logged_user_msg}")
                    print(
                        f"   Logged AI response: {(logged_ai_resp[:50] + '...') if logged_ai_resp and len(logged_ai_resp) > 50 else logged_ai_resp}"
                    )
                    print(f"   Logged time: {logged_time}")
                    return True
                else:
                    print("❌ Chat interaction was NOT logged to database")
                    print("   API worked but logging failed")
                    return False

            conn.close()

        except requests.exceptions.Timeout:
            print("❌ API request timed out (30 seconds)")
            return False
        except Exception as e:
            print(f"❌ Live chat API test failed: {e}")
            return False

    def test_chat_logger_service(self):
        """Test ChatLogger service directly."""
        self.print_header("ChatLogger Service Test")

        try:
            from lookbook_mpc.services.chat_logger import ChatLogEntry

            logger = ChatLogger()

            # Create test log entry
            test_entry = ChatLogEntry(
                session_id=f"service_test_{int(time.time())}",
                request_id=f"req_{int(time.time())}",
                user_message="Direct service test message",
                ai_response="Direct service test response",
                ai_response_type="general",
                intent_parser_type="hybrid",
                conversation_turn_number=1,
                is_follow_up=False,
                response_time_ms=100,
            )

            # Log the entry
            log_id = logger.log_chat_interaction(test_entry)

            if log_id:
                print("✅ ChatLogger service working correctly")
                print(f"   Logged entry ID: {log_id}")
                return True
            else:
                print("❌ ChatLogger service returned None")
                return False

        except Exception as e:
            print(f"❌ ChatLogger service test failed: {e}")
            return False

    def run_all_tests(self):
        """Run all verification tests."""
        print("🚀 Chat Logging Verification Script")
        print(f"Timestamp: {datetime.now().isoformat()}")

        tests = [
            ("API Connectivity", self.test_api_connectivity),
            ("Database Connection", self.test_database_connection),
            ("Recent Logs Check", self.test_recent_logs),
            ("ChatLogger Service", self.test_chat_logger_service),
            ("Live Chat API", self.test_live_chat_api),
        ]

        results = []

        for test_name, test_func in tests:
            try:
                result = test_func()
                results.append((test_name, result))
            except Exception as e:
                print(f"❌ {test_name} test crashed: {e}")
                results.append((test_name, False))

        # Print summary
        self.print_header("Test Results Summary")
        passed = sum(1 for _, result in results if result)
        total = len(results)

        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {test_name}")

        print(f"\nOverall: {passed}/{total} tests passed")

        if passed == total:
            print("🎉 All tests passed! Chat logging is working correctly.")
            return True
        else:
            print("⚠️  Some tests failed. Chat logging may not be working properly.")
            self.print_troubleshooting()
            return False

    def print_troubleshooting(self):
        """Print troubleshooting information."""
        self.print_header("Troubleshooting Guide")

        print("If tests are failing, try these steps:")
        print("")
        print("1. 🔄 Restart FastAPI server:")
        print("   poetry run uvicorn main:app --host 0.0.0.0 --port 8000 --reload")
        print("")
        print("2. 🗄️  Check database connection:")
        print("   mysql -u magento -p'Magento@COS(*)' -h 127.0.0.1 -D lookbookMPC")
        print("")
        print("3. 📊 Check recent logs manually:")
        print("   SELECT * FROM chat_logs ORDER BY created_at DESC LIMIT 5;")
        print("")
        print("4. 🧪 Test API manually:")
        print("   curl -X POST http://localhost:8000/v1/chat \\")
        print("     -H 'Content-Type: application/json' \\")
        print('     -d \'{"session_id": "test", "message": "hello"}\'')
        print("")
        print("5. 📋 Check server logs for errors")
        print("")
        print("6. 🔍 Verify environment variables are set correctly")


def main():
    """Main function."""
    verifier = ChatLoggingVerifier()
    success = verifier.run_all_tests()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
