#!/usr/bin/env python3
"""
Simple LLM Chat Test Script

Tests the pure LLM chat functionality without hybrid fallback.
"""

import asyncio
import json
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from lookbook_mpc.adapters.intent import LLMIntentParser
from lookbook_mpc.domain.entities import ChatRequest, ChatResponse
from lookbook_mpc.domain.use_cases import ChatTurn
from lookbook_mpc.adapters.db_lookbook import MockLookbookRepository
from lookbook_mpc.services.rules import RulesEngine
from lookbook_mpc.services.recommender import OutfitRecommender


async def test_llm_chat():
    """Test the pure LLM chat functionality."""
    print("🚀 Testing Pure LLM Chat Functionality\n")

    # Initialize components
    intent_parser = LLMIntentParser(
        host="http://localhost:11434", model="qwen3:4b-instruct", timeout=15
    )

    lookbook_repo = MockLookbookRepository()
    rules_engine = RulesEngine()
    recommender = OutfitRecommender(rules_engine)
    chat_use_case = ChatTurn(intent_parser, recommender, lookbook_repo)

    # Test cases from user's conversation
    test_messages = [
        "Hello",
        "I go to dance",
        "I like drive",
        "I want something for yoga",
        "Show me business outfits",
        "What about casual wear for weekend?",
    ]

    print("=" * 60)
    print("TESTING PURE LLM CHAT RESPONSES")
    print("=" * 60)

    for i, message in enumerate(test_messages, 1):
        print(f"\n🗣️  Test {i}: '{message}'")
        print("-" * 40)

        try:
            # Test intent parsing first
            print("🧠 LLM Intent Parsing...")
            intent = await intent_parser.parse_intent(message)

            print(f"   Intent: {intent.get('intent', 'N/A')}")
            print(f"   Activity: {intent.get('activity', 'N/A')}")
            print(f"   Occasion: {intent.get('occasion', 'N/A')}")
            print(f"   Objectives: {intent.get('objectives', [])}")
            print(f"   Natural Response: {intent.get('natural_response', 'N/A')}")

            # Test full chat flow
            print("\n💬 Full Chat Response...")
            request = ChatRequest(message=message)
            response = await chat_use_case.execute(request)

            if response.replies:
                print(f"   Bot: {response.replies[0]['message']}")
                print(f"   Type: {response.replies[0]['type']}")
                if response.outfits:
                    print(f"   Outfits Found: {len(response.outfits)}")
            else:
                print("   No replies generated")

        except Exception as e:
            print(f"   ❌ Error: {str(e)}")

    print("\n" + "=" * 60)
    print("TESTING COMPLETE")
    print("=" * 60)


async def test_intent_only():
    """Test just the intent parsing component."""
    print("\n🎯 Testing Intent Parsing Only\n")

    intent_parser = LLMIntentParser(
        host="http://localhost:11434", model="qwen3:4b-instruct", timeout=15
    )

    test_phrases = [
        "I go to dance",
        "I like drive",
        "hello",
        "I need workout clothes",
        "Something for business meeting",
    ]

    for phrase in test_phrases:
        print(f"Input: '{phrase}'")
        try:
            result = await intent_parser.parse_intent(phrase)
            print(f"  → Natural Response: {result.get('natural_response')}")
            print(f"  → Activity: {result.get('activity')}")
            print(f"  → Occasion: {result.get('occasion')}")
            print()
        except Exception as e:
            print(f"  → Error: {str(e)}\n")


if __name__ == "__main__":
    # Run intent parsing test first, then full chat test
    print("🎯 Starting LLM-Only Chat Testing (No Interactive Input)\n")
    asyncio.run(test_intent_only())
    asyncio.run(test_llm_chat())
