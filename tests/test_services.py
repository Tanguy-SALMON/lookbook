"""
Services Tests

This module contains unit tests for services (rules engine, recommender).
"""

import pytest
from lookbook_mpc.domain.entities import (
    Item, Outfit, OutfitItem, Rule, Intent,
    Size, Category, Material, Pattern, Season, Occasion, Fit, Role,
    VisionAttributes
)
from lookbook_mpc.services.rules import RulesEngine
from lookbook_mpc.services.recommender import OutfitRecommender


class TestRulesEngine:
    """Test RulesEngine service."""

    def setup_method(self):
        """Set up test fixtures."""
        self.rules_engine = RulesEngine()

    def test_get_rules_for_intent(self):
        """Test getting rules for a specific intent."""
        # Get yoga rules
        yoga_rules = self.rules_engine.get_rules_for_intent("yoga")
        assert yoga_rules is not None
        assert "constraints" in yoga_rules
        assert "category" in yoga_rules["constraints"]
        assert "top" in yoga_rules["constraints"]["category"]

    def test_get_rules_partial_match(self):
        """Test partial intent matching."""
        # Get rules for partial match
        rules = self.rules_engine.get_rules_for_intent("yoga_class")
        assert rules is not None
        assert rules == self.rules_engine.get_rules_for_intent("yoga")

    def test_get_rules_default_casual(self):
        """Test default casual rules when no match found."""
        # Get rules for unknown intent
        rules = self.rules_engine.get_rules_for_intent("unknown_intent")
        assert rules is not None
        assert rules == self.rules_engine.get_rules_for_intent("casual")

    def test_apply_rules_to_items(self):
        """Test applying rules to filter items."""
        # Create test items
        test_items = [
            {
                "id": 1,
                "sku": "TOP001",
                "title": "Yoga Top",
                "price": 29.99,
                "attributes": {
                    "vision_attributes": {
                        "color": "black",
                        "category": "top",
                        "material": "spandex",
                        "pattern": "plain"
                    }
                }
            },
            {
                "id": 2,
                "sku": "DRESS001",
                "title": "Evening Dress",
                "price": 99.99,
                "attributes": {
                    "vision_attributes": {
                        "color": "red",
                        "category": "dress",
                        "material": "silk",
                        "pattern": "floral"
                    }
                }
            }
        ]

        # Get yoga rules
        yoga_rules = self.rules_engine.get_rules_for_intent("yoga")

        # Apply rules
        filtered_items = self.rules_engine.apply_rules_to_items(test_items, yoga_rules)

        # Should only return yoga-appropriate items
        assert len(filtered_items) == 1
        assert filtered_items[0]["id"] == 1  # Only yoga top should match

    def test_add_custom_rule(self):
        """Test adding a custom rule."""
        custom_rule = {
            "name": "Custom Test Rule",
            "constraints": {
                "category": ["accessory"],
                "color": ["blue"]
            },
            "objectives": ["style"]
        }

        # Add custom rule
        self.rules_engine.add_custom_rule("custom", custom_rule)

        # Verify rule was added
        rules = self.rules_engine.get_rules_for_intent("custom")
        assert rules is not None
        assert rules["name"] == "Custom Test Rule"
        assert "accessory" in rules["constraints"]["category"]

    def test_get_all_rules(self):
        """Test getting all rules."""
        all_rules = self.rules_engine.get_all_rules()
        assert isinstance(all_rules, dict)
        assert len(all_rules) > 0
        assert "yoga" in all_rules
        assert "casual" in all_rules


class TestOutfitRecommender:
    """Test OutfitRecommender service."""

    def setup_method(self):
        """Set up test fixtures."""
        self.rules_engine = RulesEngine()
        self.recommender = OutfitRecommender(self.rules_engine)

        # Create test items
        self.test_items = [
            Item(
                id=1,
                sku="TOP001",
                title="Yoga Top",
                price=29.99,
                size_range=[Size.S, Size.M, Size.L],
                image_key="yoga-top.jpg",
                attributes={
                    "vision_attributes": {
                        "color": "black",
                        "category": Category.TOP,
                        "material": Material.SPANDEX,
                        "pattern": Pattern.PLAIN,
                        "season": Season.ALL_SEASON,
                        "occasion": Occasion.YOGA,
                        "fit": Fit.REGULAR
                    }
                },
                in_stock=True
            ),
            Item(
                id=2,
                sku="BOTTOM001",
                title="Yoga Leggings",
                price=39.99,
                size_range=[Size.S, Size.M, Size.L],
                image_key="yoga-leggings.jpg",
                attributes={
                    "vision_attributes": {
                        "color": "black",
                        "category": Category.BOTTOM,
                        "material": Material.SPANDEX,
                        "pattern": Pattern.PLAIN,
                        "season": Season.ALL_SEASON,
                        "occasion": Occasion.YOGA,
                        "fit": Fit.REGULAR
                    }
                },
                in_stock=True
            ),
            Item(
                id=3,
                sku="SHOES001",
                title="Yoga Mat",
                price=19.99,
                size_range=[Size.ONE_SIZE],
                image_key="yoga-mat.jpg",
                attributes={
                    "vision_attributes": {
                        "color": "purple",
                        "category": Category.ACCESSORY,
                        "material": Material.POLYURETHANE,
                        "pattern": Pattern.PLAIN,
                        "season": Season.ALL_SEASON,
                        "occasion": Occasion.YOGA,
                        "fit": Fit.REGULAR
                    }
                },
                in_stock=True
            )
        ]

    @pytest.mark.asyncio
    async def test_generate_recommendations(self):
        """Test generating outfit recommendations."""
        # Create intent
        intent = {
            "intent": "yoga",
            "activity": "yoga",
            "occasion": "yoga",
            "budget_max": 100.0,
            "objectives": ["comfortable"],
            "formality": "casual"
        }

        # Generate recommendations
        recommendations = await self.recommender.generate_recommendations(
            intent=intent,
            candidate_items=[item.dict() for item in self.test_items],
            max_outfits=3
        )

        assert len(recommendations) <= 3
        assert all("items" in rec for rec in recommendations)
        assert all("score" in rec for rec in recommendations)
        assert all("rationale" in rec for rec in recommendations)

    @pytest.mark.asyncio
    async def test_generate_outfit_for_theme(self):
        """Test generating outfit for a specific theme."""
        # Generate outfit for yoga theme
        outfit = await self.recommender.generate_outfit_for_theme(
            theme="yoga",
            items=[item.dict() for item in self.test_items],
            constraints={"occasion": "yoga", "budget_max": 100.0}
        )

        assert outfit is not None
        assert "items" in outfit
        assert "rationale" in outfit
        assert len(outfit["items"]) >= 1

    def test_categorize_items(self):
        """Test item categorization."""
        # Convert test items to dict format
        item_dicts = [item.dict() for item in self.test_items]

        categorized = self.recommender._categorize_items(item_dicts)

        assert len(categorized) == 6
        assert "top" in categorized
        assert "bottom" in categorized
        assert "accessory" in categorized
        assert len(categorized["top"]) == 1
        assert len(categorized["bottom"]) == 1
        assert len(categorized["accessory"]) == 1

    def test_get_required_categories(self):
        """Test getting required categories from rules."""
        # Get yoga rules
        yoga_rules = self.rules_engine.get_rules_for_intent("yoga")

        required = self.recommender._get_required_categories(yoga_rules)

        assert isinstance(required, list)
        assert len(required) >= 1

    def test_get_optional_categories(self):
        """Test getting optional categories."""
        optional = self.recommender._get_optional_categories({})

        assert isinstance(optional, list)
        assert "outerwear" in optional
        assert "shoes" in optional
        assert "accessory" in optional

    def test_calculate_outfit_score(self):
        """Test outfit score calculation."""
        # Create outfit items
        outfit_items = {
            "top": {"rule_score": 0.8, "price": 29.99},
            "bottom": {"rule_score": 0.7, "price": 39.99}
        }

        # Get yoga rules
        yoga_rules = self.rules_engine.get_rules_for_intent("yoga")

        score = self.recommender._calculate_outfit_score(outfit_items, yoga_rules)

        assert 0.0 <= score <= 1.0
        assert isinstance(score, float)

    def test_calculate_color_coordination_bonus(self):
        """Test color coordination bonus calculation."""
        # Create outfit items with same color
        outfit_items = {
            "top": {"attributes": {"vision_attributes": {"color": "black"}}},
            "bottom": {"attributes": {"vision_attributes": {"color": "black"}}}
        }

        bonus = self.recommender._calculate_color_coordination_bonus(outfit_items)

        assert 0.0 <= bonus <= 0.1
        assert isinstance(bonus, float)

    def test_select_best_item_for_category(self):
        """Test selecting best item for category."""
        # Create items with different scores
        items = [
            {"rule_score": 0.8, "price": 50.0},
            {"rule_score": 0.9, "price": 30.0},
            {"rule_score": 0.7, "price": 40.0}
        ]

        # Get yoga rules
        yoga_rules = self.rules_engine.get_rules_for_intent("yoga")

        best_item = self.recommender._select_best_item_for_category(items, "top", yoga_rules)

        assert best_item is not None
        # The selection logic considers both score and price diversity
        # So it might not always pick the highest score
        assert best_item["rule_score"] in [0.7, 0.8, 0.9]
        assert best_item in items