
#!/usr/bin/env python3
"""
Intent Parser Test Script

This script tests the intent parsing functionality.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from lookbook_mpc.adapters.intent import MockIntentParser, LLMIntentParser
from lookbook_mpc.domain.entities import Intent
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_intent_parsing():
    """Test intent parsing functionality."""
    try:
        print("Testing intent parsing...")

        # Test 1: Mock intent parser
        print("\nTest 1: Testing mock intent parser...")
        mock_parser = MockIntentParser()

        # Test with different user queries
        test_queries = [
            "I want to do yoga",
            "Restaurant this weekend, attractive for $50",
            "I am fat, I want something to look slim",
            "I need something casual for everyday wear",
            "Business meeting outfit for office",
            "Party outfit for Saturday night",
            "Beach vacation clothes for summer",
            "Athletic wear for gym sessions"
        ]

        for query in test_queries:
            print(f"\n  Query: '{query}'")
            result = await mock_parser.parse_intent(query)
            print(f"    Intent: {result['intent']}")
            print(f"    Activity: {result['activity']}")
            print(f"    Occasion: {result['occasion']}")
            print(f"    Budget: {result['budget_max']}")
            print(f"    Objectives: {result['objectives']}")
            print(f"    Palette: {result['palette']}")
            print(f"    Formality: {result['formality']}")

        # Test 2: Intent entity validation
        print("\nTest 2: Testing intent entity validation...")
        test_result = await mock_parser.parse_intent("Test query")

        try:
            # Create Intent object
            intent = Intent(**test_result)
            print(f"  ✓ Intent entity created successfully")
            print(f"    Intent: {intent.intent}")
            print(f"    Activity: {intent.activity}")
            print(f"    Budget: {intent.budget_max}")
        except Exception as e:
            print(f"  ❌ Intent entity validation failed: {e}")

        # Test 3: LLM intent parser (if configured)
        print("\nTest 3: Testing LLM intent parser...")
        ollama_host = "http://localhost:11434"  # Default Ollama host
        ollama_model = "qwen3"  # Default text model

        try:
            llm_parser = LLMIntentParser(ollama_host, ollama_model)
            print(f"  LLM parser initialized with host: {ollama_host}, model: {ollama_model}")

            # Test with a simple query
            test_query = "I need a casual outfit for weekend"
            print(f"  Testing query: '{test_query}'")

            # Note: This would require a running Ollama service
            # For now, just test initialization
            print(f"  ✓ LLM parser initialized successfully")

        except Exception as e:
            print(f"  ⚠️  LLM parser initialization failed (expected if Ollama not running): {e}")

        # Test 4: Edge cases
        print("\nTest 4: Testing edge cases...")
        edge_cases = [
            "",  # Empty string
            "   ",  # Whitespace only
            "Hello",  # Greeting only
            "I need help finding an outfit",
            "12345",  # Numbers only
            "What should I wear tomorrow?"  # Question format
        ]

        for case in edge_cases:
            print(f"\n  Edge case: '{case}'")
            try:
                result = await mock_parser.parse_intent(case)
                print(f"    ✓ Parsed successfully: {result['intent']}")
            except Exception as e:
                print(f"    ❌ Error: {e}")

        print("\n🎉 Intent parsing tests completed!")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(test_intent_parsing())