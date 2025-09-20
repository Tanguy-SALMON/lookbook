#!/usr/bin/env python3
"""
Chat Testing Summary Script

This script provides a comprehensive summary of all chat functionality
and runs quick validation tests to ensure everything is working properly.
It serves as both a test runner and a documentation of chat features.
"""

import json
import time
from datetime import datetime
from typing import Dict, Any, List
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from main import app


class ChatSummaryTester:
    """Chat functionality summary and quick tests."""

    def __init__(self):
        self.client = TestClient(app)
        self.results = {"features": [], "tests": {"passed": 0, "failed": 0}}

    def log(self, message: str, level: str = "INFO"):
        """Log messages with timestamp."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")

    def test_feature(self, name: str, test_func, description: str = ""):
        """Test a specific feature and record results."""
        try:
            result = test_func()
            status = "✅ WORKING" if result else "❌ FAILED"
            self.results["features"].append(
                {
                    "name": name,
                    "status": "working" if result else "failed",
                    "description": description,
                }
            )
            if result:
                self.results["tests"]["passed"] += 1
            else:
                self.results["tests"]["failed"] += 1

            self.log(f"{status} {name}")
            return result
        except Exception as e:
            self.results["features"].append(
                {
                    "name": name,
                    "status": "error",
                    "description": f"{description} - Error: {str(e)}",
                }
            )
            self.results["tests"]["failed"] += 1
            self.log(f"❌ ERROR {name}: {e}")
            return False

    def quick_chat_test(self) -> bool:
        """Quick chat functionality test."""
        response = self.client.post("/v1/chat", json={"message": "Hello"})
        return response.status_code == 200 and "replies" in response.json()

    def session_management_test(self) -> bool:
        """Test session management endpoints."""
        # Create a session
        response = self.client.post("/v1/chat", json={"message": "Test"})
        if response.status_code != 200:
            return False

        session_id = response.json().get("session_id")
        if not session_id:
            return False

        # Test session retrieval
        response = self.client.get(f"/v1/chat/sessions/{session_id}")
        if response.status_code != 200:
            return False

        # Cleanup
        self.client.delete(f"/v1/chat/sessions/{session_id}")
        return True

    def suggestions_test(self) -> bool:
        """Test chat suggestions endpoint."""
        response = self.client.get("/v1/chat/suggestions")
        if response.status_code != 200:
            return False

        data = response.json()
        return "suggestions" in data and len(data["suggestions"]) > 0

    def validation_test(self) -> bool:
        """Test input validation."""
        # Test empty message
        response = self.client.post("/v1/chat", json={"message": ""})
        return response.status_code == 422

    def conversation_flow_test(self) -> bool:
        """Test multi-turn conversation."""
        # First message
        response1 = self.client.post("/v1/chat", json={"message": "I need yoga outfit"})
        if response1.status_code != 200:
            return False

        session_id = response1.json().get("session_id")

        # Second message with same session
        response2 = self.client.post(
            "/v1/chat",
            json={"session_id": session_id, "message": "What about business outfit?"},
        )

        success = (
            response2.status_code == 200
            and response2.json().get("session_id") == session_id
        )

        # Cleanup
        if session_id:
            self.client.delete(f"/v1/chat/sessions/{session_id}")

        return success

    def error_handling_test(self) -> bool:
        """Test error handling."""
        # Test non-existent session
        response = self.client.get("/v1/chat/sessions/non-existent")
        return response.status_code == 404

    def health_check_test(self) -> bool:
        """Test application health."""
        response = self.client.get("/health")
        return response.status_code == 200

    def run_summary_tests(self) -> Dict[str, Any]:
        """Run all summary tests and return results."""
        self.log("🧪 CHAT FUNCTIONALITY SUMMARY & TESTS")
        self.log("=" * 60)

        # Test core features
        features_to_test = [
            ("Health Check", self.health_check_test, "Basic application health"),
            ("Basic Chat", self.quick_chat_test, "Send message and receive reply"),
            (
                "Session Management",
                self.session_management_test,
                "Create, retrieve, and delete sessions",
            ),
            ("Chat Suggestions", self.suggestions_test, "Pre-defined chat prompts"),
            ("Input Validation", self.validation_test, "Reject invalid inputs"),
            (
                "Conversation Flow",
                self.conversation_flow_test,
                "Multi-turn conversations",
            ),
            ("Error Handling", self.error_handling_test, "Proper error responses"),
        ]

        for name, test_func, description in features_to_test:
            self.test_feature(name, test_func, description)

        return self.results

    def print_detailed_summary(self):
        """Print detailed feature summary."""
        self.log("\n📋 CHAT FEATURES OVERVIEW")
        self.log("=" * 60)

        chat_features = [
            {
                "name": "💬 Basic Chat Interface",
                "description": "Send messages and receive AI-powered responses",
                "endpoints": ["POST /v1/chat"],
                "example": '{"message": "I want to do yoga"}',
            },
            {
                "name": "🔗 Session Management",
                "description": "Maintain conversation context across multiple messages",
                "endpoints": [
                    "GET /v1/chat/sessions",
                    "GET /v1/chat/sessions/{id}",
                    "DELETE /v1/chat/sessions/{id}",
                    "POST /v1/chat/sessions/{id}/clear",
                ],
                "example": "Sessions auto-created with UUID identifiers",
            },
            {
                "name": "💡 Smart Suggestions",
                "description": "Pre-defined prompts for common fashion queries",
                "endpoints": ["GET /v1/chat/suggestions"],
                "example": "Yoga outfit, business meeting, party dress suggestions",
            },
            {
                "name": "👗 Fashion-Specific AI",
                "description": "Understands fashion terminology and context",
                "endpoints": ["POST /v1/chat"],
                "example": "Colors, styles, occasions, budget constraints",
            },
            {
                "name": "🛡️ Input Validation",
                "description": "Robust validation of chat inputs",
                "endpoints": ["POST /v1/chat"],
                "example": "Rejects empty messages, invalid session IDs",
            },
            {
                "name": "🔄 Conversation Context",
                "description": "Remembers previous messages within a session",
                "endpoints": ["POST /v1/chat"],
                "example": "Follow-up questions reference earlier messages",
            },
            {
                "name": "🎯 Outfit Recommendations",
                "description": "AI can suggest specific clothing items and outfits",
                "endpoints": ["POST /v1/chat"],
                "example": "Returns structured outfit data with items and scores",
            },
            {
                "name": "🌐 Multi-format Responses",
                "description": "Supports text replies and structured data",
                "endpoints": ["POST /v1/chat"],
                "example": "Text messages + outfit recommendations + context",
            },
        ]

        for feature in chat_features:
            self.log(f"\n{feature['name']}")
            self.log(f"  📝 {feature['description']}")
            self.log(f"  🔗 Endpoints: {', '.join(feature['endpoints'])}")
            self.log(f"  💡 Example: {feature['example']}")

    def print_test_commands(self):
        """Print useful test commands."""
        self.log("\n🛠️ TESTING COMMANDS")
        self.log("=" * 60)

        commands = [
            {
                "name": "Run All Tests",
                "command": "poetry run pytest tests/ -v",
                "description": "Complete test suite (117 tests)",
            },
            {
                "name": "Chat-Specific Tests",
                "command": "poetry run pytest tests/test_api_integration.py::TestChatEndpoints -v",
                "description": "Only chat endpoint tests",
            },
            {
                "name": "Comprehensive Chat Test",
                "command": "poetry run python scripts/test_chat_direct.py",
                "description": "Detailed chat functionality testing",
            },
            {
                "name": "Start Server",
                "command": "./start_server.sh",
                "description": "Start server with demo interface",
            },
            {
                "name": "Test with Curl",
                "command": 'curl -X POST http://localhost:8000/v1/chat -H "Content-Type: application/json" -d \'{"message":"Hello"}\'',
                "description": "Direct API testing",
            },
        ]

        for cmd in commands:
            self.log(f"\n{cmd['name']}:")
            self.log(f"  Command: {cmd['command']}")
            self.log(f"  Purpose: {cmd['description']}")

    def print_demo_info(self):
        """Print demo interface information."""
        self.log("\n🌐 DEMO INTERFACE")
        self.log("=" * 60)
        self.log("After starting the server, you can test the chat in multiple ways:")
        self.log("")
        self.log("1. 💻 Web Demo Interface:")
        self.log("   URL: http://localhost:8000/demo")
        self.log("   Features: Interactive chat UI with suggestions")
        self.log("")
        self.log("2. 📚 API Documentation:")
        self.log("   URL: http://localhost:8000/docs")
        self.log("   Features: Interactive API testing interface")
        self.log("")
        self.log("3. 🔍 Health Check:")
        self.log("   URL: http://localhost:8000/health")
        self.log("   Features: Server status and version info")

    def print_sample_requests(self):
        """Print sample chat requests."""
        self.log("\n💬 SAMPLE CHAT REQUESTS")
        self.log("=" * 60)

        samples = [
            {
                "query": "I want to do yoga",
                "category": "Activity-based",
                "expected": "Comfortable sportswear suggestions",
            },
            {
                "query": "Business meeting outfit for tomorrow",
                "category": "Occasion-based",
                "expected": "Professional business attire",
            },
            {
                "query": "Red dress under ฿2000",
                "category": "Color + Budget",
                "expected": "Red dresses within budget",
            },
            {
                "query": "I want to look slim",
                "category": "Style objective",
                "expected": "Slimming outfit recommendations",
            },
            {
                "query": "Beach vacation outfits",
                "category": "Seasonal/Location",
                "expected": "Summer and beach appropriate clothing",
            },
            {
                "query": "Black and white casual style",
                "category": "Color + Style",
                "expected": "Monochrome casual outfits",
            },
        ]

        for sample in samples:
            self.log(f"\n📝 {sample['category']}:")
            self.log(f'   Query: "{sample["query"]}"')
            self.log(f"   Expected: {sample['expected']}")


def main():
    """Main execution function."""
    import argparse

    parser = argparse.ArgumentParser(description="Chat Testing Summary")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    parser.add_argument("--quick", action="store_true", help="Quick test only")

    args = parser.parse_args()

    tester = ChatSummaryTester()

    # Run tests
    start_time = time.time()
    results = tester.run_summary_tests()
    duration = time.time() - start_time

    # Add summary info
    results["summary"] = {
        "total_features": len(results["features"]),
        "working_features": len(
            [f for f in results["features"] if f["status"] == "working"]
        ),
        "success_rate": round(
            results["tests"]["passed"]
            / (results["tests"]["passed"] + results["tests"]["failed"])
            * 100,
            1,
        ),
        "duration_seconds": round(duration, 2),
    }

    if args.json:
        print(json.dumps(results, indent=2))
        return

    # Print results
    tester.log(f"\n📊 TEST RESULTS")
    tester.log("=" * 60)
    tester.log(
        f"✅ Features Working: {results['summary']['working_features']}/{results['summary']['total_features']}"
    )
    tester.log(f"🎯 Success Rate: {results['summary']['success_rate']}%")
    tester.log(f"⏱️  Duration: {results['summary']['duration_seconds']}s")

    if not args.quick:
        tester.print_detailed_summary()
        tester.print_sample_requests()
        tester.print_test_commands()
        tester.print_demo_info()

    # Final status
    tester.log("\n" + "=" * 60)
    if results["tests"]["failed"] == 0:
        tester.log("🎉 ALL CHAT FEATURES ARE WORKING PERFECTLY!")
        tester.log("✅ Ready for chat interface testing")
    else:
        tester.log(f"⚠️  {results['tests']['failed']} features have issues")
        tester.log("🔧 Please review failed tests above")

    # Exit code
    sys.exit(0 if results["tests"]["failed"] == 0 else 1)


if __name__ == "__main__":
    main()
