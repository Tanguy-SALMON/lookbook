#!/usr/bin/env python3
"""
Demo UI Test Script

This script tests the demo UI endpoint to ensure it works correctly.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import httpx
import json
from datetime import datetime

# Test configuration
BASE_URL = "http://localhost:8000"
DEMO_URL = f"{BASE_URL}/demo"
API_TIMEOUT = 30.0

async def test_demo_endpoint():
    """Test demo UI endpoint."""
    try:
        print("Testing demo UI endpoint...")

        async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
            # Test demo page
            response = await client.get(DEMO_URL)
            if response.status_code == 200:
                content = response.text
                print(f"  ✓ Demo page: {len(content)} characters")

                # Check for key elements
                if "AI Fashion Assistant" in content:
                    print(f"  ✓ Contains title: AI Fashion Assistant")
                else:
                    print(f"  ❌ Missing title: AI Fashion Assistant")
                    return False

                if "chat" in content.lower():
                    print(f"  ✓ Contains chat interface")
                else:
                    print(f"  ❌ Missing chat interface")
                    return False

                if "demo.html" in content:
                    print(f"  ✓ References demo.html")
                else:
                    print(f"  ❌ Missing demo.html reference")
                    return False

                return True
            else:
                print(f"  ❌ Demo page failed: {response.status_code}")
                print(f"    Response: {response.text[:200]}...")
                return False

    except Exception as e:
        print(f"  ❌ Demo endpoint test failed: {e}")
        return False

async def test_demo_assets():
    """Test demo assets and styling."""
    try:
        print("\nTesting demo assets...")

        async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
            # Test Tailwind CSS CDN
            response = await client.get("https://cdn.tailwindcss.com", timeout=10)
            if response.status_code == 200:
                print(f"  ✓ Tailwind CSS CDN: accessible")
            else:
                print(f"  ❌ Tailwind CSS CDN: {response.status_code}")

            # Test Font Awesome CDN
            response = await client.get("https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css", timeout=10)
            if response.status_code == 200:
                print(f"  ✓ Font Awesome CDN: accessible")
            else:
                print(f"  ❌ Font Awesome CDN: {response.status_code}")

            # Test Google Fonts
            response = await client.get("https://fonts.googleapis.com/css2?family=Onest:wght@400;500;600;700&display=swap", timeout=10)
            if response.status_code == 200:
                print(f"  ✓ Google Fonts: accessible")
            else:
                print(f"  ❌ Google Fonts: {response.status_code}")

            return True

    except Exception as e:
        print(f"  ❌ Demo assets test failed: {e}")
        return False

async def test_demo_functionality():
    """Test demo UI functionality (mock test)."""
    try:
        print("\nTesting demo functionality...")

        # Test that the demo page has the expected JavaScript functions
        async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
            response = await client.get(DEMO_URL)
            if response.status_code == 200:
                content = response.text

                # Check for key JavaScript functions
                expected_functions = [
                    "sendMessage",
                    "sendSuggestion",
                    "handleKeyPress",
                    "addMessage",
                    "addOutfitCard",
                    "checkApiHealth"
                ]

                missing_functions = []
                for func in expected_functions:
                    if f"function {func}" in content or f"{func} =" in content:
                        print(f"  ✓ Contains function: {func}")
                    else:
                        missing_functions.append(func)
                        print(f"  ❌ Missing function: {func}")

                if missing_functions:
                    print(f"  ❌ Missing {len(missing_functions)} functions: {missing_functions}")
                    return False

                # Check for API endpoints
                if "/v1/chat" in content:
                    print(f"  ✓ References /v1/chat endpoint")
                else:
                    print(f"  ❌ Missing /v1/chat reference")
                    return False

                if "/health" in content:
                    print(f"  ✓ References /health endpoint")
                else:
                    print(f"  ❌ Missing /health reference")
                    return False

                return True
            else:
                print(f"  ❌ Demo functionality test failed: {response.status_code}")
                return False

    except Exception as e:
        print(f"  ❌ Demo functionality test failed: {e}")
        return False

async def main():
    """Run all demo tests."""
    try:
        print("Starting demo UI tests...")
        print(f"Demo URL: {DEMO_URL}")
        print(f"Timeout: {API_TIMEOUT}s")

        # Run individual tests
        demo_success = await test_demo_endpoint()
        assets_success = await test_demo_assets()
        functionality_success = await test_demo_functionality()

        # Summary
        print("\n" + "="*50)
        print("DEMO UI TEST SUMMARY")
        print("="*50)
        print(f"Demo Endpoint: {'✓ PASSED' if demo_success else '❌ FAILED'}")
        print(f"Demo Assets: {'✓ PASSED' if assets_success else '❌ FAILED'}")
        print(f"Demo Functionality: {'✓ PASSED' if functionality_success else '❌ FAILED'}")

        all_passed = all([demo_success, assets_success, functionality_success])

        if all_passed:
            print("\n🎉 All demo UI tests passed!")
            return True
        else:
            print("\n❌ Some demo UI tests failed!")
            return False

    except Exception as e:
        print(f"❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)