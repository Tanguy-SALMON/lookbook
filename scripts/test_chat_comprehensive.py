#!/usr/bin/env python3
"""
Comprehensive Chat Testing Script

This script thoroughly tests all chat functionality including:
- Basic chat interactions
- Session management
- Context handling
- Error scenarios
- Intent parsing
- Outfit recommendations
- Chat suggestions
- Multiple conversation flows
"""

import asyncio
import json
import requests
import uuid
import time
from datetime import datetime
from typing import Dict, Any, List
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lookbook_mpc.domain.entities import ChatRequest, ChatResponse


class ChatTester:
    """Comprehensive chat functionality tester."""

    def __init__(self, base_url: str = "http://0.0.0.0:8000"):
        self.base_url = base_url
        self.session_ids = []
        self.test_results = {"passed": 0, "failed": 0, "errors": []}

    def log(self, message: str, level: str = "INFO"):
        """Log test messages with timestamp."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")

    def assert_test(self, condition: bool, test_name: str, error_msg: str = ""):
        """Assert a test condition and track results."""
        if condition:
            self.test_results["passed"] += 1
            self.log(f"✅ {test_name}", "PASS")
            return True
        else:
            self.test_results["failed"] += 1
            full_error = f"{test_name}: {error_msg}" if error_msg else test_name
            self.test_results["errors"].append(full_error)
            self.log(f"❌ {test_name} - {error_msg}", "FAIL")
            return False

    def make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make HTTP request with error handling."""
        url = f"{self.base_url}{endpoint}"
        try:
            response = requests.request(method, url, **kwargs)
            return response
        except requests.RequestException as e:
            self.log(f"Request failed: {e}", "ERROR")
            raise

    def test_server_health(self) -> bool:
        """Test if the server is running and healthy."""
        self.log("Testing server health...")

        # Retry logic for server startup
        max_retries = 3
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    self.log(f"Retry attempt {attempt + 1}/{max_retries}")
                    time.sleep(2)  # Wait between retries

                response = self.make_request("GET", "/health")
                healthy = self.assert_test(
                    response.status_code == 200,
                    "Server health check",
                    f"Expected 200, got {response.status_code}",
                )
                if healthy:
                    self.log("Server is healthy and ready for testing")
                return healthy
            except Exception as e:
                if attempt == max_retries - 1:  # Last attempt
                    self.assert_test(
                        False, "Server health check", f"Server unreachable: {e}"
                    )
                    return False
                else:
                    self.log(f"Connection attempt {attempt + 1} failed: {e}", "WARN")
        return False

    def test_basic_chat(self) -> str:
        """Test basic chat functionality."""
        self.log("Testing basic chat functionality...")

        # Test simple chat message
        chat_data = {"message": "I want to do yoga"}

        response = self.make_request("POST", "/v1/chat", json=chat_data)

        self.assert_test(
            response.status_code == 200,
            "Basic chat request",
            f"Expected 200, got {response.status_code}",
        )

        if response.status_code != 200:
            return None

        data = response.json()

        # Validate response structure
        self.assert_test("session_id" in data, "Response has session_id")

        self.assert_test("replies" in data, "Response has replies")

        self.assert_test("request_id" in data, "Response has request_id")

        self.assert_test(
            len(data.get("replies", [])) > 0, "Response has at least one reply"
        )

        # Check reply structure
        if data.get("replies"):
            reply = data["replies"][0]
            self.assert_test("type" in reply, "Reply has type field")
            self.assert_test("message" in reply, "Reply has message field")

        session_id = data.get("session_id")
        if session_id:
            self.session_ids.append(session_id)

        self.log(f"Generated session ID: {session_id}")
        return session_id

    def test_chat_with_session_id(self, session_id: str) -> bool:
        """Test chat with existing session ID."""
        self.log(f"Testing chat with existing session ID: {session_id}")

        chat_data = {
            "session_id": session_id,
            "message": "What about business meeting outfit?",
        }

        response = self.make_request("POST", "/v1/chat", json=chat_data)

        success = self.assert_test(
            response.status_code == 200,
            "Chat with existing session",
            f"Expected 200, got {response.status_code}",
        )

        if success:
            data = response.json()
            self.assert_test(
                data.get("session_id") == session_id,
                "Session ID preserved",
                f"Expected {session_id}, got {data.get('session_id')}",
            )

        return success

    def test_chat_validation_errors(self) -> bool:
        """Test chat input validation."""
        self.log("Testing chat input validation...")

        test_cases = [
            {"name": "Empty message", "data": {"message": ""}, "expected_status": 422},
            {
                "name": "Missing message",
                "data": {"session_id": "test"},
                "expected_status": 422,
            },
            {
                "name": "Empty session_id string",
                "data": {"session_id": "", "message": "test"},
                "expected_status": 422,
            },
            {
                "name": "Whitespace only message",
                "data": {"message": "   "},
                "expected_status": 422,
            },
        ]

        all_passed = True

        for test_case in test_cases:
            response = self.make_request("POST", "/v1/chat", json=test_case["data"])
            passed = self.assert_test(
                response.status_code == test_case["expected_status"],
                f"Validation: {test_case['name']}",
                f"Expected {test_case['expected_status']}, got {response.status_code}",
            )
            all_passed = all_passed and passed

        return all_passed

    def test_chat_suggestions(self) -> bool:
        """Test chat suggestions endpoint."""
        self.log("Testing chat suggestions...")

        response = self.make_request("GET", "/v1/chat/suggestions")

        success = self.assert_test(
            response.status_code == 200,
            "Chat suggestions endpoint",
            f"Expected 200, got {response.status_code}",
        )

        if success:
            data = response.json()
            self.assert_test(
                "suggestions" in data, "Suggestions response has suggestions field"
            )

            self.assert_test(
                "categories" in data, "Suggestions response has categories field"
            )

            suggestions = data.get("suggestions", [])
            self.assert_test(len(suggestions) > 0, "Has at least one suggestion")

            # Check suggestion structure
            if suggestions:
                suggestion = suggestions[0]
                required_fields = ["id", "prompt", "category", "description"]
                for field in required_fields:
                    self.assert_test(
                        field in suggestion, f"Suggestion has {field} field"
                    )

        return success

    def test_session_management(self, session_id: str) -> bool:
        """Test session management endpoints."""
        self.log("Testing session management...")

        # Test list sessions
        response = self.make_request("GET", "/v1/chat/sessions")
        success = self.assert_test(
            response.status_code == 200, "List sessions endpoint"
        )

        if success:
            data = response.json()
            self.assert_test("sessions" in data, "Sessions list has sessions field")
            self.assert_test("pagination" in data, "Sessions list has pagination field")

        # Test get specific session
        response = self.make_request("GET", f"/v1/chat/sessions/{session_id}")
        success = (
            self.assert_test(response.status_code == 200, "Get specific session")
            and success
        )

        if response.status_code == 200:
            data = response.json()
            required_fields = [
                "session_id",
                "created_at",
                "messages",
                "context",
                "message_count",
            ]
            for field in required_fields:
                self.assert_test(field in data, f"Session details has {field} field")

        # Test clear session context
        response = self.make_request("POST", f"/v1/chat/sessions/{session_id}/clear")
        success = (
            self.assert_test(response.status_code == 200, "Clear session context")
            and success
        )

        return success

    def test_conversation_flow(self) -> bool:
        """Test a complete conversation flow."""
        self.log("Testing complete conversation flow...")

        conversation_steps = [
            "I need an outfit for yoga",
            "What about something for a business meeting?",
            "Show me casual outfits under ฿2000",
            "I prefer black and white colors",
            "Any recommendations for summer season?",
        ]

        session_id = None
        all_success = True

        for i, message in enumerate(conversation_steps):
            self.log(f"Conversation step {i + 1}: {message}")

            chat_data = {"message": message}
            if session_id:
                chat_data["session_id"] = session_id

            response = self.make_request("POST", "/v1/chat", json=chat_data)

            step_success = self.assert_test(
                response.status_code == 200,
                f"Conversation step {i + 1}",
                f"Expected 200, got {response.status_code}",
            )

            if step_success and response.status_code == 200:
                data = response.json()
                if not session_id:
                    session_id = data.get("session_id")
                    if session_id:
                        self.session_ids.append(session_id)

                # Check for outfit recommendations in responses
                if data.get("outfits"):
                    self.log(
                        f"  → Received {len(data['outfits'])} outfit recommendations"
                    )

                if data.get("replies"):
                    self.log(
                        f"  → Reply: {data['replies'][0].get('message', '')[:100]}..."
                    )

            all_success = all_success and step_success

        return all_success

    def test_fashion_specific_queries(self) -> bool:
        """Test fashion-specific chat queries."""
        self.log("Testing fashion-specific queries...")

        fashion_queries = [
            "I want to look slim",
            "Beach vacation outfits",
            "Party dress for Saturday night",
            "Professional work clothes",
            "Comfortable sportswear",
            "Elegant formal wear",
            "Casual weekend outfits",
        ]

        all_success = True

        for query in fashion_queries:
            self.log(f"Testing query: {query}")

            chat_data = {"message": query}
            response = self.make_request("POST", "/v1/chat", json=chat_data)

            success = self.assert_test(
                response.status_code == 200,
                f"Fashion query: {query[:30]}...",
                f"Expected 200, got {response.status_code}",
            )

            if success and response.status_code == 200:
                data = response.json()
                session_id = data.get("session_id")
                if session_id and session_id not in self.session_ids:
                    self.session_ids.append(session_id)

                # Check if we got meaningful responses
                has_replies = len(data.get("replies", [])) > 0
                has_outfits = data.get("outfits") is not None

                self.assert_test(
                    has_replies or has_outfits,
                    f"Fashion query has content: {query[:30]}...",
                    "No replies or outfits returned",
                )

            all_success = all_success and success

        return all_success

    def test_error_handling(self) -> bool:
        """Test error handling scenarios."""
        self.log("Testing error handling...")

        # Test non-existent session
        fake_session_id = str(uuid.uuid4())
        response = self.make_request("GET", f"/v1/chat/sessions/{fake_session_id}")

        success = self.assert_test(
            response.status_code == 404,
            "Non-existent session handling",
            f"Expected 404, got {response.status_code}",
        )

        # Test invalid session ID for deletion
        response = self.make_request("DELETE", f"/v1/chat/sessions/{fake_session_id}")
        success = (
            self.assert_test(
                response.status_code == 404,
                "Delete non-existent session",
                f"Expected 404, got {response.status_code}",
            )
            and success
        )

        # Test malformed JSON
        try:
            response = requests.post(f"{self.base_url}/v1/chat", data="invalid json")
            success = (
                self.assert_test(
                    response.status_code == 422,
                    "Malformed JSON handling",
                    f"Expected 422, got {response.status_code}",
                )
                and success
            )
        except Exception as e:
            self.log(f"Malformed JSON test error: {e}", "WARN")

        return success

    def test_session_cleanup(self) -> bool:
        """Test session cleanup (delete created sessions)."""
        self.log("Testing session cleanup...")

        success = True

        for session_id in self.session_ids:
            self.log(f"Deleting session: {session_id}")
            response = self.make_request("DELETE", f"/v1/chat/sessions/{session_id}")

            step_success = self.assert_test(
                response.status_code == 200,
                f"Delete session {session_id[:8]}...",
                f"Expected 200, got {response.status_code}",
            )
            success = success and step_success

        return success

    def run_all_tests(self) -> Dict[str, Any]:
        """Run all chat tests."""
        self.log("🚀 Starting comprehensive chat testing...")
        start_time = time.time()

        # Test server health first
        if not self.test_server_health():
            self.log("❌ Server health check failed. Aborting tests.", "ERROR")
            return self.get_results(time.time() - start_time)

        # Run all test suites
        test_suites = [
            ("Basic Chat", self.test_basic_chat),
            ("Chat Validation", self.test_chat_validation_errors),
            ("Chat Suggestions", self.test_chat_suggestions),
            ("Conversation Flow", self.test_conversation_flow),
            ("Fashion Queries", self.test_fashion_specific_queries),
            ("Error Handling", self.test_error_handling),
        ]

        session_id = None

        for suite_name, test_func in test_suites:
            self.log(f"\n📋 Running {suite_name} tests...")
            try:
                if suite_name == "Basic Chat":
                    session_id = test_func()  # Basic chat returns session_id
                elif suite_name == "Session Management" and session_id:
                    self.test_session_management(session_id)
                    self.test_chat_with_session_id(session_id)
                else:
                    test_func()
            except Exception as e:
                self.log(f"Test suite {suite_name} failed with error: {e}", "ERROR")
                self.assert_test(False, f"{suite_name} suite execution", str(e))

        # Test session management with any available session
        if self.session_ids:
            self.log(f"\n📋 Running Session Management tests...")
            self.test_session_management(self.session_ids[0])
            self.test_chat_with_session_id(self.session_ids[0])

        # Cleanup
        self.log(f"\n🧹 Cleaning up test sessions...")
        self.test_session_cleanup()

        return self.get_results(time.time() - start_time)

    def get_results(self, duration: float) -> Dict[str, Any]:
        """Get comprehensive test results."""
        total_tests = self.test_results["passed"] + self.test_results["failed"]
        success_rate = (
            (self.test_results["passed"] / total_tests * 100) if total_tests > 0 else 0
        )

        return {
            "summary": {
                "total_tests": total_tests,
                "passed": self.test_results["passed"],
                "failed": self.test_results["failed"],
                "success_rate": round(success_rate, 2),
                "duration_seconds": round(duration, 2),
            },
            "errors": self.test_results["errors"],
            "sessions_created": len(self.session_ids),
        }

    def print_results(self, results: Dict[str, Any]):
        """Print formatted test results."""
        summary = results["summary"]

        self.log("\n" + "=" * 60)
        self.log("📊 CHAT TESTING RESULTS")
        self.log("=" * 60)
        self.log(f"Total Tests: {summary['total_tests']}")
        self.log(f"✅ Passed: {summary['passed']}")
        self.log(f"❌ Failed: {summary['failed']}")
        self.log(f"🎯 Success Rate: {summary['success_rate']}%")
        self.log(f"⏱️  Duration: {summary['duration_seconds']}s")
        self.log(f"🔗 Sessions Created: {results['sessions_created']}")

        if results["errors"]:
            self.log(f"\n❌ FAILED TESTS ({len(results['errors'])}):")
            for i, error in enumerate(results["errors"], 1):
                self.log(f"  {i}. {error}")

        self.log("=" * 60)

        if summary["failed"] == 0:
            self.log("🎉 ALL CHAT TESTS PASSED!")
        else:
            self.log(f"⚠️  {summary['failed']} tests failed. Please review.")


def main():
    """Main execution function."""
    import argparse

    parser = argparse.ArgumentParser(description="Comprehensive Chat Testing")
    parser.add_argument(
        "--url",
        default="http://0.0.0.0:8000",
        help="Base URL for the API (default: http://0.0.0.0:8000)",
    )
    parser.add_argument("--json", action="store_true", help="Output results as JSON")

    args = parser.parse_args()

    # Create tester and run tests
    tester = ChatTester(base_url=args.url)
    results = tester.run_all_tests()

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        tester.print_results(results)

    # Exit with non-zero code if tests failed
    sys.exit(1 if results["summary"]["failed"] > 0 else 0)


if __name__ == "__main__":
    main()
