#!/usr/bin/env python3
"""
API Test Script

This script tests the API endpoints to ensure they work correctly.
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
API_TIMEOUT = 30.0

async def test_health_endpoints():
    """Test health and readiness endpoints."""
    try:
        print("Testing health endpoints...")

        async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
            # Test health endpoint
            response = await client.get(f"{BASE_URL}/health")
            if response.status_code == 200:
                health_data = response.json()
                print(f"  ✓ Health check: {health_data['status']}")
            else:
                print(f"  ❌ Health check failed: {response.status_code}")
                return False

            # Test readiness endpoint
            response = await client.get(f"{BASE_URL}/ready")
            if response.status_code == 200:
                ready_data = response.json()
                print(f"  ✓ Readiness check: {ready_data['status']}")
                print(f"    Checks: {ready_data['checks']}")
            else:
                print(f"  ❌ Readiness check failed: {response.status_code}")
                return False

            return True

    except Exception as e:
        print(f"  ❌ Health endpoints test failed: {e}")
        return False

async def test_ingest_api():
    """Test ingest API endpoints."""
    try:
        print("\nTesting ingest API...")

        async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
            # Test item ingestion
            ingest_data = {
                "limit": 10,
                "since": None
            }

            response = await client.post(
                f"{BASE_URL}/v1/ingest/items",
                json=ingest_data,
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 202:
                ingest_response = response.json()
                print(f"  ✓ Item ingestion: {ingest_response['status']}, processed {ingest_response['items_processed']} items")

                # Test listing items
                response = await client.get(f"{BASE_URL}/v1/ingest/items?limit=5")
                if response.status_code == 200:
                    items_data = response.json()
                    print(f"  ✓ List items: {len(items_data['items'])} items returned")
                    print(f"    Pagination: {items_data['pagination']}")
                else:
                    print(f"  ❌ List items failed: {response.status_code}")
                    return False

                # Test ingestion stats
                response = await client.get(f"{BASE_URL}/v1/ingest/stats")
                if response.status_code == 200:
                    stats_data = response.json()
                    print(f"  ✓ Ingest stats: {stats_data['total_items']} total items")
                else:
                    print(f"  ❌ Ingest stats failed: {response.status_code}")
                    return False

                return True
            else:
                print(f"  ❌ Item ingestion failed: {response.status_code}")
                print(f"    Response: {response.text}")
                return False

    except Exception as e:
        print(f"  ❌ Ingest API test failed: {e}")
        return False

async def test_recommendation_api():
    """Test recommendation API endpoints."""
    try:
        print("\nTesting recommendation API...")

        async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
            # Test outfit recommendations
            reco_data = {
                "text_query": "I want to do yoga",
                "budget": 80,
                "size": "L",
                "week": "2025-W40",
                "preferences": {
                    "palette": ["dark"]
                }
            }

            response = await client.post(
                f"{BASE_URL}/v1/recommendations",
                json=reco_data,
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 200:
                reco_response = response.json()
                print(f"  ✓ Outfit recommendations: {len(reco_response['outfits'])} outfits returned")
                print(f"    Constraints used: {list(reco_response['constraints_used'].keys())}")

                if reco_response['outfits']:
                    for i, outfit in enumerate(reco_response['outfits'][:2]):  # Show first 2
                        print(f"    Outfit {i+1}: {outfit['item_count']} items, score: {outfit['score']:.2f}")
                        if outfit.get('rationale'):
                            print(f"      Rationale: {outfit['rationale']}")

                # Test preview endpoint
                response = await client.get(
                    f"{BASE_URL}/v1/recommendations/preview?text_query=yoga&budget=50"
                )
                if response.status_code == 200:
                    preview_data = response.json()
                    print(f"  ✓ Preview endpoint: {preview_data['total_available']} total outfits available")
                else:
                    print(f"  ❌ Preview endpoint failed: {response.status_code}")
                    return False

                # Test constraints endpoint
                response = await client.get(f"{BASE_URL}/v1/recommendations/constraints")
                if response.status_code == 200:
                    constraints_data = response.json()
                    print(f"  ✓ Constraints: {len(constraints_data['sizes'])} sizes, {len(constraints_data['categories'])} categories")
                else:
                    print(f"  ❌ Constraints endpoint failed: {response.status_code}")
                    return False

                # Test popular recommendations
                response = await client.get(f"{BASE_URL}/v1/recommendations/popular?limit=3")
                if response.status_code == 200:
                    popular_data = response.json()
                    print(f"  ✓ Popular: {len(popular_data['recommendations'])} popular recommendations")
                else:
                    print(f"  ❌ Popular endpoint failed: {response.status_code}")
                    return False

                return True
            else:
                print(f"  ❌ Outfit recommendations failed: {response.status_code}")
                print(f"    Response: {response.text}")
                return False

    except Exception as e:
        print(f"  ❌ Recommendation API test failed: {e}")
        return False

async def test_chat_api():
    """Test chat API endpoints."""
    try:
        print("\nTesting chat API...")

        async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
            # Test chat turn
            chat_data = {
                "message": "I want to do yoga"
            }

            response = await client.post(
                f"{BASE_URL}/v1/chat",
                json=chat_data,
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 200:
                chat_response = response.json()
                print(f"  ✓ Chat turn: {len(chat_response['replies'])} replies")
                print(f"    Session ID: {chat_response['session_id']}")

                if chat_response.get('outfits'):
                    print(f"    Outfits: {len(chat_response['outfits'])} outfit recommendations")

                # Test session listing
                response = await client.get(f"{BASE_URL}/v1/chat/sessions?limit=5")
                if response.status_code == 200:
                    sessions_data = response.json()
                    print(f"  ✓ Session list: {len(sessions_data['sessions'])} sessions")
                else:
                    print(f"  ❌ Session list failed: {response.status_code}")
                    return False

                # Test chat suggestions
                response = await client.get(f"{BASE_URL}/v1/chat/suggestions")
                if response.status_code == 200:
                    suggestions_data = response.json()
                    print(f"  ✓ Chat suggestions: {len(suggestions_data['suggestions'])} suggestions available")
                else:
                    print(f"  ❌ Chat suggestions failed: {response.status_code}")
                    return False

                return True
            else:
                print(f"  ❌ Chat turn failed: {response.status_code}")
                print(f"    Response: {response.text}")
                return False

    except Exception as e:
        print(f"  ❌ Chat API test failed: {e}")
        return False

async def test_images_api():
    """Test images API endpoints."""
    try:
        print("\nTesting images API...")

        async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
            # Test image info (mock image)
            image_key = "test-image.jpg"

            response = await client.get(f"{BASE_URL}/v1/images/info/{image_key}")
            if response.status_code == 200:
                image_info = response.json()
                print(f"  ✓ Image info: {image_info['image_key']}")
                print(f"    Available: {image_info['available']}")
                if image_info['available']:
                    print(f"    Content type: {image_info['content_type']}")
            else:
                print(f"  ❌ Image info failed: {response.status_code}")
                return False

            # Test image redirect
            response = await client.get(f"{BASE_URL}/v1/images/{image_key}/redirect")
            if response.status_code == 302:
                print(f"  ✓ Image redirect: {response.headers['location']}")
            else:
                print(f"  ❌ Image redirect failed: {response.status_code}")
                return False

            # Test batch images
            response = await client.get(f"{BASE_URL}/v1/images/batch?image_keys=test1.jpg,test2.jpg")
            if response.status_code == 200:
                batch_data = response.json()
                print(f"  ✓ Batch images: {batch_data['total_requested']} requested, {batch_data['successful']} successful")
            else:
                print(f"  ❌ Batch images failed: {response.status_code}")
                return False

            # Test CORS preflight
            response = await client.options(f"{BASE_URL}/v1/images/{image_key}")
            if response.status_code == 200:
                print(f"  ✓ CORS preflight: {response.json()['status']}")
            else:
                print(f"  ❌ CORS preflight failed: {response.status_code}")
                return False

            return True

    except Exception as e:
        print(f"  ❌ Images API test failed: {e}")
        return False

async def test_openapi_docs():
    """Test OpenAPI documentation endpoints."""
    try:
        print("\nTesting OpenAPI documentation...")

        async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
            # Test OpenAPI JSON
            response = await client.get(f"{BASE_URL}/openapi.json")
            if response.status_code == 200:
                openapi_data = response.json()
                print(f"  ✓ OpenAPI JSON: {len(openapi_data['paths'])} paths, {len(openapi_data['components']['schemas'])} schemas")
            else:
                print(f"  ❌ OpenAPI JSON failed: {response.status_code}")
                return False

            # Test Swagger UI
            response = await client.get(f"{BASE_URL}/docs")
            if response.status_code == 200:
                print(f"  ✓ Swagger UI: Available at /docs")
            else:
                print(f"  ❌ Swagger UI failed: {response.status_code}")
                return False

            # Test ReDoc
            response = await client.get(f"{BASE_URL}/redoc")
            if response.status_code == 200:
                print(f"  ✓ ReDoc: Available at /redoc")
            else:
                print(f"  ❌ ReDoc failed: {response.status_code}")
                return False

            return True

    except Exception as e:
        print(f"  ❌ OpenAPI docs test failed: {e}")
        return False

async def test_root_endpoint():
    """Test root endpoint."""
    try:
        print("\nTesting root endpoint...")

        async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
            response = await client.get(f"{BASE_URL}/")
            if response.status_code == 200:
                root_data = response.json()
                print(f"  ✓ Root endpoint: {root_data['service']} v{root_data['version']}")
                print(f"    Docs: {root_data['docs']}")
                print(f"    Health: {root_data['health']}")
                return True
            else:
                print(f"  ❌ Root endpoint failed: {response.status_code}")
                return False

    except Exception as e:
        print(f"  ❌ Root endpoint test failed: {e}")
        return False

async def main():
    """Run all API tests."""
    try:
        print("Starting API tests...")
        print(f"Base URL: {BASE_URL}")
        print(f"Timeout: {API_TIMEOUT}s")

        # Run individual tests
        health_success = await test_health_endpoints()
        ingest_success = await test_ingest_api()
        reco_success = await test_recommendation_api()
        chat_success = await test_chat_api()
        images_success = await test_images_api()
        docs_success = await test_openapi_docs()
        root_success = await test_root_endpoint()

        # Summary
        print("\n" + "="*50)
        print("API TEST SUMMARY")
        print("="*50)
        print(f"Health Endpoints: {'✓ PASSED' if health_success else '❌ FAILED'}")
        print(f"Ingest API: {'✓ PASSED' if ingest_success else '❌ FAILED'}")
        print(f"Recommendation API: {'✓ PASSED' if reco_success else '❌ FAILED'}")
        print(f"Chat API: {'✓ PASSED' if chat_success else '❌ FAILED'}")
        print(f"Images API: {'✓ PASSED' if images_success else '❌ FAILED'}")
        print(f"OpenAPI Docs: {'✓ PASSED' if docs_success else '❌ FAILED'}")
        print(f"Root Endpoint: {'✓ PASSED' if root_success else '❌ FAILED'}")

        all_passed = all([
            health_success, ingest_success, reco_success,
            chat_success, images_success, docs_success, root_success
        ])

        if all_passed:
            print("\n🎉 All API tests passed!")
            return True
        else:
            print("\n❌ Some API tests failed!")
            return False

    except Exception as e:
        print(f"❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)