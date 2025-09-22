#!/usr/bin/env python3
"""
Test Chat Integration with Smart Recommender

Direct test to debug the chat system integration with smart recommender.
"""

import asyncio
import sys
from pathlib import Path
import json

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from lookbook_mpc.domain.entities import ChatRequest
from lookbook_mpc.domain.use_cases import ChatTurn
from lookbook_mpc.adapters.intent import LLMIntentParser
from lookbook_mpc.adapters.db_lookbook import MySQLLookbookRepository
from lookbook_mpc.services.rules import RulesEngine
from lookbook_mpc.services.recommender import OutfitRecommender
from lookbook_mpc.config.settings import settings


async def test_direct_chat_integration():
    """Test chat integration with smart recommender directly."""

    print("🧪 TESTING DIRECT CHAT INTEGRATION")
    print("=" * 45)

    # Initialize components exactly like in chat router
    intent_parser = LLMIntentParser(
        host=settings.ollama_host,
        model="qwen3:4b-instruct",
        timeout=15,
    )
    lookbook_repo = MySQLLookbookRepository(settings.lookbook_db_url)
    rules_engine = RulesEngine()
    recommender = OutfitRecommender(rules_engine)
    chat_use_case = ChatTurn(intent_parser, recommender, lookbook_repo)

    test_messages = ["I go to dance", "I need something for business meeting", "Hello"]

    for message in test_messages:
        print(f"\n💬 Testing: '{message}'")
        print("-" * 40)

        try:
            # Create chat request
            request = ChatRequest(message=message)

            # Execute chat use case
            response = await chat_use_case.execute(request)

            print(
                f"Response Type: {response.replies[0]['type'] if response.replies else 'None'}"
            )
            print(
                f"Message: {response.replies[0]['message'][:100] if response.replies else 'None'}..."
            )
            print(f"Outfits: {len(response.outfits) if response.outfits else 0}")

            if response.outfits:
                print("\nOutfit Details:")
                for i, outfit in enumerate(response.outfits, 1):
                    print(f"  {i}. {outfit['title']} (฿{outfit['total_price']:.0f})")
                    print(f"     Items: {len(outfit['items'])} pieces")
                    for item in outfit["items"]:
                        print(
                            f"       • {item['title'][:35]}... (฿{item['price']:.0f})"
                        )
                        print(f"         {item['image_url']}")
                    print(f"     Explanation: {outfit['explanation'][:80]}...")
            else:
                print("No outfits generated")

        except Exception as e:
            print(f"❌ Error: {str(e)}")
            import traceback

            traceback.print_exc()


async def test_smart_recommender_direct():
    """Test smart recommender directly to verify it works."""

    print("\n\n🔍 TESTING SMART RECOMMENDER DIRECTLY")
    print("=" * 45)

    from lookbook_mpc.services.smart_recommender import SmartRecommender

    lookbook_repo = MySQLLookbookRepository(settings.lookbook_db_url)
    smart_recommender = SmartRecommender(lookbook_repo)

    try:
        outfits = await smart_recommender.recommend_outfits("I go to dance", limit=2)

        print(f"Smart recommender found {len(outfits)} outfits:")

        for i, outfit in enumerate(outfits, 1):
            print(f"\n  {i}. {outfit['title']} (฿{outfit['total_price']:.0f})")
            print(f"     Type: {outfit['outfit_type']}")
            for item in outfit["items"]:
                print(f"       • {item['title'][:35]}... (฿{item['price']:.0f})")
                print(f"         SKU: {item['sku']}, Color: {item['color']}")
            print(f"     Why: {outfit['style_explanation'][:80]}...")

        return len(outfits) > 0

    except Exception as e:
        print(f"❌ Smart recommender error: {str(e)}")
        import traceback

        traceback.print_exc()
        return False


async def test_intent_parser_direct():
    """Test intent parser to see what it returns."""

    print("\n\n🧠 TESTING INTENT PARSER DIRECTLY")
    print("=" * 40)

    intent_parser = LLMIntentParser(
        host=settings.ollama_host,
        model="qwen3:4b-instruct",
        timeout=15,
    )

    try:
        intent = await intent_parser.parse_intent("I go to dance")

        print("Intent parser result:")
        print(json.dumps(intent, indent=2))

        return intent

    except Exception as e:
        print(f"❌ Intent parser error: {str(e)}")
        return {}


if __name__ == "__main__":
    print("🚀 Starting Chat Integration Debug Tests\n")

    async def run_debug_tests():
        # Test 1: Intent parser
        intent = await test_intent_parser_direct()

        # Test 2: Smart recommender
        smart_works = await test_smart_recommender_direct()

        # Test 3: Full integration
        await test_direct_chat_integration()

        print("\n" + "=" * 50)
        print("✅ DEBUG TESTS COMPLETED")
        print("=" * 50)

        print(f"\nResults:")
        print(f"- Intent Parser: {'✅ Working' if intent else '❌ Failed'}")
        print(f"- Smart Recommender: {'✅ Working' if smart_works else '❌ Failed'}")
        print(f"- Integration: See results above")

    asyncio.run(run_debug_tests())
