#!/usr/bin/env python3
"""
Recommender Test Script

This script tests the rules engine and outfit recommender functionality.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from lookbook_mpc.services.rules import RulesEngine
from lookbook_mpc.services.recommender import OutfitRecommender
from lookbook_mpc.adapters.intent import MockIntentParser
from lookbook_mpc.adapters.vision import MockVisionProvider
from lookbook_mpc.adapters.db_lookbook import MockLookbookRepository
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_rules_engine():
    """Test the rules engine functionality."""
    try:
        print("Testing rules engine...")

        # Initialize rules engine
        rules_engine = RulesEngine()

        # Test 1: Get rules for different intents
        print("\nTest 1: Testing rule retrieval...")
        test_intents = ["yoga", "dinner", "slimming", "casual", "business", "party", "beach", "sport"]

        for intent in test_intents:
            rules = rules_engine.get_rules_for_intent(intent)
            if rules:
                print(f"  ✓ {intent}: {rules['name']}")
                print(f"    Constraints: {list(rules.get('constraints', {}).keys())}")
                print(f"    Objectives: {rules.get('objectives', [])}")
            else:
                print(f"  ❌ {intent}: No rules found")

        # Test 2: Test rule application to items
        print("\nTest 2: Testing rule application...")

        # Create test items
        test_items = [
            {
                "id": 1,
                "sku": "TOP001",
                "title": "Yoga Top",
                "price": 35.99,
                "attributes": {
                    "vision_attributes": {
                        "color": "black",
                        "category": "top",
                        "material": "cotton",
                        "pattern": "plain",
                        "stretch": True
                    }
                }
            },
            {
                "id": 2,
                "sku": "BOTTOM001",
                "title": "Yoga Pants",
                "price": 45.99,
                "attributes": {
                    "vision_attributes": {
                        "color": "navy",
                        "category": "bottom",
                        "material": "spandex",
                        "pattern": "plain",
                        "stretch": True
                    }
                }
            },
            {
                "id": 3,
                "sku": "DRESS001",
                "title": "Evening Dress",
                "price": 120.00,
                "attributes": {
                    "vision_attributes": {
                        "color": "red",
                        "category": "dress",
                        "material": "silk",
                        "pattern": "plain",
                        "formality": "elevated"
                    }
                }
            },
            {
                "id": 4,
                "sku": "JEANS001",
                "title": "Casual Jeans",
                "price": 79.99,
                "attributes": {
                    "vision_attributes": {
                        "color": "blue",
                        "category": "bottom",
                        "material": "denim",
                        "pattern": "plain",
                        "formality": "casual"
                    }
                }
            }
        ]

        # Test yoga rules
        yoga_rules = rules_engine.get_rules_for_intent("yoga")
        yoga_filtered = rules_engine.apply_rules_to_items(test_items, yoga_rules)
        print(f"  Yoga rules: {len(yoga_filtered)} items match (expected: 2)")

        # Test dinner rules
        dinner_rules = rules_engine.get_rules_for_intent("dinner")
        dinner_filtered = rules_engine.apply_rules_to_items(test_items, dinner_rules)
        print(f"  Dinner rules: {len(dinner_filtered)} items match (expected: 1)")

        # Test slimming rules
        slimming_rules = rules_engine.get_rules_for_intent("slimming")
        slimming_filtered = rules_engine.apply_rules_to_items(test_items, slimming_rules)
        print(f"  Slimming rules: {len(slimming_filtered)} items match (expected: varies)")

        # Test 3: Test custom rule addition
        print("\nTest 3: Testing custom rule addition...")
        custom_rule = {
            "name": "Custom Test Rule",
            "constraints": {
                "category": ["top"],
                "color": ["red"]
            },
            "objectives": ["test"],
            "palette": ["red"]
        }

        rules_engine.add_custom_rule("test", custom_rule)
        test_rules = rules_engine.get_rules_for_intent("test")
        if test_rules:
            print(f"  ✓ Custom rule added: {test_rules['name']}")
        else:
            print(f"  ❌ Custom rule failed")

        # Test 4: Test all rules retrieval
        print("\nTest 4: Testing all rules retrieval...")
        all_rules = rules_engine.get_all_rules()
        print(f"  Total rules loaded: {len(all_rules)}")

        return True

    except Exception as e:
        print(f"❌ Rules engine test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_outfit_recommender():
    """Test the outfit recommender functionality."""
    try:
        print("\n\nTesting outfit recommender...")

        # Initialize services
        rules_engine = RulesEngine()
        recommender = OutfitRecommender(rules_engine)

        # Create test items
        test_items = [
            {
                "id": 1,
                "sku": "TOP001",
                "title": "Yoga Top",
                "price": 35.99,
                "image_url": "https://example.com/yoga-top.jpg",
                "attributes": {
                    "vision_attributes": {
                        "color": "black",
                        "category": "top",
                        "material": "cotton",
                        "pattern": "plain",
                        "stretch": True
                    }
                }
            },
            {
                "id": 2,
                "sku": "BOTTOM001",
                "title": "Yoga Pants",
                "price": 45.99,
                "image_url": "https://example.com/yoga-pants.jpg",
                "attributes": {
                    "vision_attributes": {
                        "color": "navy",
                        "category": "bottom",
                        "material": "spandex",
                        "pattern": "plain",
                        "stretch": True
                    }
                }
            },
            {
                "id": 3,
                "sku": "DRESS001",
                "title": "Evening Dress",
                "price": 120.00,
                "image_url": "https://example.com/evening-dress.jpg",
                "attributes": {
                    "vision_attributes": {
                        "color": "red",
                        "category": "dress",
                        "material": "silk",
                        "pattern": "plain",
                        "formality": "elevated"
                    }
                }
            },
            {
                "id": 4,
                "sku": "JEANS001",
                "title": "Casual Jeans",
                "price": 79.99,
                "image_url": "https://example.com/casual-jeans.jpg",
                "attributes": {
                    "vision_attributes": {
                        "color": "blue",
                        "category": "bottom",
                        "material": "denim",
                        "pattern": "plain",
                        "formality": "casual"
                    }
                }
            },
            {
                "id": 5,
                "sku": "JACKET001",
                "title": "Casual Jacket",
                "price": 89.99,
                "image_url": "https://example.com/casual-jacket.jpg",
                "attributes": {
                    "vision_attributes": {
                        "color": "black",
                        "category": "outerwear",
                        "material": "cotton",
                        "pattern": "plain",
                        "formality": "casual"
                    }
                }
            }
        ]

        # Test 1: Generate yoga outfit recommendations
        print("\nTest 1: Testing yoga outfit recommendations...")
        yoga_intent = {
            "intent": "recommend_outfits",
            "activity": "yoga",
            "occasion": "casual",
            "objectives": ["comfort"],
            "formality": "athleisure"
        }

        yoga_outfits = await recommender.generate_recommendations(
            intent=yoga_intent,
            candidate_items=test_items,
            max_outfits=3
        )

        print(f"  Generated {len(yoga_outfits)} yoga outfits")
        for i, outfit in enumerate(yoga_outfits):
            print(f"    Outfit {i+1}: {outfit['item_count']} items, score: {outfit['score']:.2f}")
            for item in outfit.get("items", []):
                print(f"      - {item['role']}: {item['title']} (${item['price']:.2f})")

        # Test 2: Generate dinner outfit recommendations
        print("\nTest 2: Testing dinner outfit recommendations...")
        dinner_intent = {
            "intent": "recommend_outfits",
            "occasion": "dinner",
            "budget_max": 150,
            "formality": "elevated"
        }

        dinner_outfits = await recommender.generate_recommendations(
            intent=dinner_intent,
            candidate_items=test_items,
            max_outfits=3
        )

        print(f"  Generated {len(dinner_outfits)} dinner outfits")
        for i, outfit in enumerate(dinner_outfits):
            print(f"    Outfit {i+1}: {outfit['item_count']} items, score: {outfit['score']:.2f}")
            if outfit.get("rationale"):
                print(f"      Rationale: {outfit['rationale']}")

        # Test 3: Generate theme-based outfit
        print("\nTest 3: Testing theme-based outfit generation...")
        theme_outfit = await recommender.generate_outfit_for_theme(
            theme="summer",
            items=test_items,
            constraints={"palette": ["light", "bright"]}
        )

        if theme_outfit:
            print(f"  Generated summer outfit: {theme_outfit['item_count']} items, score: {theme_outfit['score']:.2f}")
            print(f"  Rationale: {theme_outfit.get('rationale', 'No rationale')}")
        else:
            print("  ❌ Failed to generate theme outfit")

        # Test 4: Test with insufficient items
        print("\nTest 4: Testing with insufficient items...")
        insufficient_items = [test_items[0]]  # Only one item
        insufficient_outfits = await recommender.generate_recommendations(
            intent=yoga_intent,
            candidate_items=insufficient_items,
            max_outfits=3
        )

        print(f"  Generated {len(insufficient_outfits)} outfits with insufficient items (expected: 0)")

        return True

    except Exception as e:
        print(f"❌ Outfit recommender test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_integration():
    """Test integration between all components."""
    try:
        print("\n\nTesting integration...")

        # Initialize all components
        rules_engine = RulesEngine()
        recommender = OutfitRecommender(rules_engine)
        intent_parser = MockIntentParser()
        vision_provider = MockVisionProvider()
        lookbook_repo = MockLookbookRepository()

        # Test 1: Parse intent -> Get rules -> Generate recommendations
        print("\nTest 1: Full integration test...")

        # Parse user intent
        user_query = "I want to do yoga"
        parsed_intent = await intent_parser.parse_intent(user_query)
        print(f"  User query: '{user_query}'")
        print(f"  Parsed intent: {parsed_intent}")

        # Get rules for intent
        rules = rules_engine.get_rules_for_intent(parsed_intent.get("intent", "casual"))
        print(f"  Applied rules: {rules['name']}")

        # Get items from repository
        all_items = await lookbook_repo.get_all_items()
        print(f"  Available items: {len(all_items)}")

        # Filter items by rules
        filtered_items = rules_engine.apply_rules_to_items(all_items, rules)
        print(f"  Items matching rules: {len(filtered_items)}")

        # Generate recommendations
        recommendations = await recommender.generate_recommendations(
            intent=parsed_intent,
            candidate_items=filtered_items,
            max_outfits=3
        )

        print(f"  Final recommendations: {len(recommendations)}")
        for i, outfit in enumerate(recommendations):
            print(f"    Recommendation {i+1}: {outfit['item_count']} items, score: {outfit['score']:.2f}")
            if outfit.get("rationale"):
                print(f"      Rationale: {outfit['rationale']}")

        # Test 2: Test different scenarios
        print("\nTest 2: Testing different scenarios...")
        scenarios = [
            "Restaurant this weekend, attractive for $50",
            "I am fat, I want something to look slim",
            "Business meeting outfit for office"
        ]

        for scenario in scenarios:
            print(f"\n  Scenario: '{scenario}'")
            intent = await intent_parser.parse_intent(scenario)
            rules = rules_engine.get_rules_for_intent(intent.get("intent", "casual"))
            filtered_items = rules_engine.apply_rules_to_items(all_items, rules)

            if filtered_items:
                recommendations = await recommender.generate_recommendations(
                    intent=intent,
                    candidate_items=filtered_items,
                    max_outfits=2
                )
                print(f"    Generated {len(recommendations)} recommendations")
            else:
                print(f"    No items match this scenario")

        return True

    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all tests."""
    try:
        print("Starting recommender system tests...")

        # Run individual tests
        rules_success = await test_rules_engine()
        recommender_success = await test_outfit_recommender()
        integration_success = await test_integration()

        # Summary
        print("\n\n" + "="*50)
        print("TEST SUMMARY")
        print("="*50)
        print(f"Rules Engine: {'✓ PASSED' if rules_success else '❌ FAILED'}")
        print(f"Outfit Recommender: {'✓ PASSED' if recommender_success else '❌ FAILED'}")
        print(f"Integration: {'✓ PASSED' if integration_success else '❌ FAILED'}")

        if rules_success and recommender_success and integration_success:
            print("\n🎉 All tests passed!")
            return True
        else:
            print("\n❌ Some tests failed!")
            return False

    except Exception as e:
        print(f"❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)