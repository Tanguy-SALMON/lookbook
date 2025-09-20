#!/usr/bin/env python3
"""
MCP Server Test Script

This script tests the MCP server endpoints to ensure they work correctly.
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
MCP_BASE_URL = f"{BASE_URL}/mcp"
API_TIMEOUT = 30.0

async def test_mcp_tools():
    """Test MCP tools endpoints."""
    try:
        print("Testing MCP tools...")

        async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
            # Test list tools
            response = await client.get(f"{MCP_BASE_URL}/tools")
            if response.status_code == 200:
                tools_data = response.json()
                print(f"  ✓ List tools: {len(tools_data)} tools available")

                for tool in tools_data:
                    print(f"    - {tool['name']}: {tool['description']}")
            else:
                print(f"  ❌ List tools failed: {response.status_code}")
                return False

            # Test call recommend_outfits tool
            tool_args = {
                "query": "I want to do yoga",
                "budget": 80,
                "size": "L",
                "preferences": {"palette": ["dark"]}
            }

            response = await client.post(
                f"{MCP_BASE_URL}/call",
                json={"name": "recommend_outfits", "arguments": tool_args},
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 200:
                result = response.json()
                print(f"  ✓ Call recommend_outfits: {len(result.get('outfits', []))} outfits returned")
            else:
                print(f"  ❌ Call recommend_outfits failed: {response.status_code}")
                print(f"    Response: {response.text}")
                return False

            # Test call search_items tool
            tool_args = {
                "category": "top",
                "color": "black",
                "limit": 5
            }

            response = await client.post(
                f"{MCP_BASE_URL}/call",
                json={"name": "search_items", "arguments": tool_args},
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 200:
                result = response.json()
                print(f"  ✓ Call search_items: {len(result.get('items', []))} items found")
                print(f"    Total count: {result.get('total_count', 0)}")
            else:
                print(f"  ❌ Call search_items failed: {response.status_code}")
                print(f"    Response: {response.text}")
                return False

            # Test call ingest_batch tool
            tool_args = {
                "limit": 10
            }

            response = await client.post(
                f"{MCP_BASE_URL}/call",
                json={"name": "ingest_batch", "arguments": tool_args},
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 200:
                result = response.json()
                print(f"  ✓ Call ingest_batch: {result.get('status')}, processed {result.get('items_processed')} items")
            else:
                print(f"  ❌ Call ingest_batch failed: {response.status_code}")
                print(f"    Response: {response.text}")
                return False

            return True

    except Exception as e:
        print(f"  ❌ MCP tools test failed: {e}")
        return False

async def test_mcp_resources():
    """Test MCP resources endpoints."""
    try:
        print("\nTesting MCP resources...")

        async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
            # Test list resources
            response = await client.get(f"{MCP_BASE_URL}/resources")
            if response.status_code == 200:
                resources_data = response.json()
                print(f"  ✓ List resources: {len(resources_data)} resources available")

                for resource in resources_data:
                    print(f"    - {resource['uri']}: {resource['name']}")
            else:
                print(f"  ❌ List resources failed: {response.status_code}")
                return False

            # Test read openapi resource
            response = await client.get(f"{MCP_BASE_URL}/resources/openapi")
            if response.status_code == 200:
                openapi_data = response.json()
                print(f"  ✓ Read openapi: {openapi_data.get('info', {}).get('title')} v{openapi_data.get('info', {}).get('version')}")
            else:
                print(f"  ❌ Read openapi failed: {response.status_code}")
                return False

            # Test read rules_catalog resource
            response = await client.get(f"{MCP_BASE_URL}/resources/rules_catalog")
            if response.status_code == 200:
                rules_data = response.json()
                print(f"  ✓ Read rules_catalog: {len(rules_data.get('rules', []))} rules available")
            else:
                print(f"  ❌ Read rules_catalog failed: {response.status_code}")
                return False

            # Test read schemas resource
            response = await client.get(f"{MCP_BASE_URL}/resources/schemas")
            if response.status_code == 200:
                schemas_data = response.json()
                print(f"  ✓ Read schemas: {len(schemas_data.get('schemas', {}))} schema definitions")
            else:
                print(f"  ❌ Read schemas failed: {response.status_code}")
                return False

            return True

    except Exception as e:
        print(f"  ❌ MCP resources test failed: {e}")
        return False

async def test_mcp_error_handling():
    """Test MCP error handling."""
    try:
        print("\nTesting MCP error handling...")

        async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
            # Test calling non-existent tool
            response = await client.post(
                f"{MCP_BASE_URL}/call",
                json={"name": "non_existent_tool", "arguments": {}},
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 200:
                result = response.json()
                if "error" in result:
                    print(f"  ✓ Error handling: {result['error']}")
                else:
                    print(f"  ❌ Error handling failed: No error in response")
                    return False
            else:
                print(f"  ❌ Error handling failed: {response.status_code}")
                return False

            # Test reading non-existent resource
            response = await client.get(f"{MCP_BASE_URL}/resources/non_existent")

            if response.status_code == 200:
                result = response.json()
                if "error" in result:
                    print(f"  ✓ Resource error handling: {result['error']}")
                else:
                    print(f"  ❌ Resource error handling failed: No error in response")
                    return False
            else:
                print(f"  ❌ Resource error handling failed: {response.status_code}")
                return False

            return True

    except Exception as e:
        print(f"  ❌ MCP error handling test failed: {e}")
        return False

async def main():
    """Run all MCP tests."""
    try:
        print("Starting MCP server tests...")
        print(f"Base URL: {MCP_BASE_URL}")
        print(f"Timeout: {API_TIMEOUT}s")

        # Run individual tests
        tools_success = await test_mcp_tools()
        resources_success = await test_mcp_resources()
        error_success = await test_mcp_error_handling()

        # Summary
        print("\n" + "="*50)
        print("MCP SERVER TEST SUMMARY")
        print("="*50)
        print(f"MCP Tools: {'✓ PASSED' if tools_success else '❌ FAILED'}")
        print(f"MCP Resources: {'✓ PASSED' if resources_success else '❌ FAILED'}")
        print(f"MCP Error Handling: {'✓ PASSED' if error_success else '❌ FAILED'}")

        all_passed = all([tools_success, resources_success, error_success])

        if all_passed:
            print("\n🎉 All MCP server tests passed!")
            return True
        else:
            print("\n❌ Some MCP server tests failed!")
            return False

    except Exception as e:
        print(f"❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)