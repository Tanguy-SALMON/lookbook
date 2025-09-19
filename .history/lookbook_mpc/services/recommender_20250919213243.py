"""
Outfit Recommender Service

This service implements the core recommendation logic for
completing outfits based on user intent and available items.
"""

from typing import Dict, List, Any, Optional, Tuple
import random
import logging
import structlog

logger = structlog.get_logger()


class OutfitRecommender:
    """Outfit recommendation service."""

    def __init__(self, rules_engine):
        self.rules_engine = rules_engine
        self.logger = logger.bind(service="outfit_recommender")

    async def generate_recommendations(
        self,
        intent: Dict[str, Any],
        candidate_items: List[Dict[str, Any]],
        max_outfits: int = 7
    ) -> List[Dict[str, Any]]:
        """
        Generate outfit recommendations based on intent and candidate items.

        Args:
            intent: User intent dictionary
            candidate_items: List of candidate items
            max_outfits: Maximum number of outfits to generate

        Returns:
            List of outfit recommendations
        """
        try:
            self.logger.info("Generating outfit recommendations",
                           intent=intent,
                           candidate_count=len(candidate_items),
                           max_outfits=max_outfits)

            # Get rules for this intent
            rules = self.rules_engine.get_rules_for_intent(intent.get("intent", "casual"))

            if not rules:
                self.logger.warning("No rules found for intent", intent=intent)
                return []

            # Apply rules to filter and score items
            filtered_items = self.rules_engine.apply_rules_to_items(candidate_items, rules)

            if not filtered_items:
                self.logger.warning("No items match the rules", intent=intent)
                return []

            # Generate outfit combinations
            outfits = []
            for i in range(min(max_outfits, len(filtered_items) // 3)):  # Need at least 3 items per outfit
                outfit = await self._generate_single_outfit(filtered_items, rules, intent)
                if outfit:
                    outfits.append(outfit)

            # Generate rationale for each outfit
            for outfit in outfits:
                outfit["rationale"] = await self._generate_outfit_rationale(outfit, intent, rules)

            self.logger.info("Outfit recommendations generated", count=len(outfits))

            return outfits

        except Exception as e:
            self.logger.error("Error generating outfit recommendations", error=str(e))
            return []

    async def _generate_single_outfit(
        self,
        items: List[Dict[str, Any]],
        rules: Dict[str, Any],
        intent: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Generate a single outfit combination."""
        try:
            # Group items by category
            categorized_items = self._categorize_items(items)

            # Build outfit based on rules
            outfit_items = {}

            # Select top item for each required category
            required_categories = self._get_required_categories(rules)

            for category in required_categories:
                if category in categorized_items and categorized_items[category]:
                    # Select best item for this category
                    best_item = self._select_best_item_for_category(
                        categorized_items[category],
                        category,
                        rules
                    )
                    if best_item:
                        outfit_items[category] = best_item

            # Add optional items if we have space
            optional_categories = self._get_optional_categories(rules)
            for category in optional_categories:
                if category in categorized_items and categorized_items[category]:
                    # Check if we already have an item for this category
                    if category not in outfit_items:
                        best_item = self._select_best_item_for_category(
                            categorized_items[category],
                            category,
                            rules
                        )
                        if best_item:
                            outfit_items[category] = best_item

            # Ensure we have a complete outfit
            if len(outfit_items) < 2:  # At least 2 items for a basic outfit
                return None

            # Calculate overall outfit score
            outfit_score = self._calculate_outfit_score(outfit_items, rules)

            # Build outfit response
            outfit = {
                "items": [
                    {
                        "item_id": item.get("id"),
                        "sku": item.get("sku"),
                        "role": category,
                        "image_url": item.get("image_url", ""),
                        "title": item.get("title", ""),
                        "price": item.get("price", 0),
                        "score": item.get("rule_score", 0)
                    }
                    for category, item in outfit_items.items()
                ],
                "score": outfit_score,
                "item_count": len(outfit_items)
            }

            return outfit

        except Exception as e:
            self.logger.error("Error generating single outfit", error=str(e))
            return None

    def _categorize_items(self, items: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group items by their category."""
        categorized = {
            "top": [],
            "bottom": [],
            "dress": [],
            "outerwear": [],
            "shoes": [],
            "accessory": []
        }

        for item in items:
            vision_attrs = item.get("attributes", {}).get("vision_attributes", {})
            category = vision_attrs.get("category", "accessory")

            if category in categorized:
                categorized[category].append(item)
            else:
                categorized["accessory"].append(item)

        return categorized

    def _get_required_categories(self, rules: Dict[str, Any]) -> List[str]:
        """Get required categories based on rules."""
        constraints = rules.get("constraints", {})
        category_constraints = constraints.get("category", [])

        # Default required categories
        required = ["top", "bottom"]

        # Override with rule constraints
        if category_constraints:
            required = [cat for cat in category_constraints if cat in ["top", "bottom", "dress"]]

        return required

    def _get_optional_categories(self, rules: Dict[str, Any]) -> List[str]:
        """Get optional categories based on rules."""
        return ["outerwear", "shoes", "accessory"]

    def _select_best_item_for_category(
        self,
        items: List[Dict[str, Any]],
        category: str,
        rules: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Select the best item for a specific category."""
        if not items:
            return None

        # Sort by rule score first
        sorted_items = sorted(items, key=lambda x: x.get("rule_score", 0), reverse=True)

        # For dresses, we only need one item
        if category == "dress":
            return sorted_items[0]

        # For other categories, consider price diversity
        if len(sorted_items) > 1:
            # Try to get items with different price points
            prices = [item.get("price", 0) for item in sorted_items]
            avg_price = sum(prices) / len(prices)

            # Select item closest to average price but with good score
            best_item = None
            best_score = 0

            for item in sorted_items:
                score = item.get("rule_score", 0)
                price = item.get("price", 0)
                price_diff = abs(price - avg_price)

                # Balance score and price appropriateness
                combined_score = score * (1 - min(price_diff / avg_price, 0.5))

                if combined_score > best_score:
                    best_score = combined_score
                    best_item = item

            return best_item or sorted_items[0]

        return sorted_items[0]

    def _calculate_outfit_score(self, outfit_items: Dict[str, Dict[str, Any]], rules: Dict[str, Any]) -> float:
        """Calculate overall outfit score."""
        if not outfit_items:
            return 0.0

        # Average of individual item scores
        item_scores = [item.get("rule_score", 0) for item in outfit_items.values()]
        avg_score = sum(item_scores) / len(item_scores)

        # Bonus for complete outfit
        completeness_bonus = min(len(outfit_items) / 4, 0.2)  # Max 20% bonus

        # Bonus for color coordination (simplified)
        color_bonus = self._calculate_color_coordination_bonus(outfit_items)

        total_score = avg_score + completeness_bonus + color_bonus

        return min(total_score, 1.0)

    def _calculate_color_coordination_bonus(self, outfit_items: Dict[str, Dict[str, Any]]) -> float:
        """Calculate color coordination bonus (simplified)."""
        try:
            colors = []
            for item in outfit_items.values():
                vision_attrs = item.get("attributes", {}).get("vision_attributes", {})
                color = vision_attrs.get("color", "")
                if color:
                    colors.append(color.lower())

            if len(colors) < 2:
                return 0.0

            # Simple coordination check
            unique_colors = set(colors)

            # Bonus for neutral colors
            neutral_colors = {"black", "white", "navy", "grey", "beige"}
            neutral_count = sum(1 for color in unique_colors if color in neutral_colors)

            if neutral_count == len(unique_colors):
                return 0.1  # All neutral is good
            elif len(unique_colors) <= 2:
                return 0.05  # Few colors is good
            else:
                return 0.0  # Too many colors

        except Exception:
            return 0.0

    async def generate_outfit_for_theme(
        self,
        theme: str,
        items: List[Dict[str, Any]],
        constraints: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Generate an outfit for a specific theme.

        Args:
            theme: Lookbook theme
            items: Available items
            constraints: Additional constraints

        Returns:
            Outfit dictionary or None
        """
        try:
            self.logger.info("Generating outfit for theme", theme=theme)

            # Create mock intent for theme
            theme_intent = {
                "intent": theme,
                "theme": theme,
                **constraints
            }

            # Get rules for theme
            rules = self.rules_engine.get_rules_for_intent(theme)

            if not rules:
                self.logger.warning("No rules found for theme", theme=theme)
                return None

            # Apply rules to filter items
            filtered_items = self.rules_engine.apply_rules_to_items(items, rules)

            if not filtered_items:
                self.logger.warning("No items match theme rules", theme=theme)
                return None

            # Generate single outfit
            outfit = await self._generate_single_outfit(filtered_items, rules, theme_intent)

            if outfit:
                outfit["theme"] = theme
                outfit["rationale"] = await self._generate_theme_rationale(outfit, theme, rules)

            return outfit

        except Exception as e:
            self.logger.error("Error generating outfit for theme", theme=theme, error=str(e))
            return None

    async def _generate_outfit_rationale(
        self,
        outfit: Dict[str, Any],
        intent: Dict[str, Any],
        rules: Dict[str, Any]
    ) -> str:
        """Generate rationale for an outfit recommendation."""
        try:
            # Simple rationale generation based on rules and items
            item_count = outfit.get("item_count", 0)
            score = outfit.get("score", 0)

            # Get intent keywords
            intent_keywords = []
            if intent.get("activity"):
                intent_keywords.append(intent["activity"])
            if intent.get("occasion"):
                intent_keywords.append(intent["occasion"])
            if intent.get("objectives"):
                intent_keywords.extend(intent["objectives"])

            # Build rationale
            rationale_parts = []

            if intent_keywords:
                rationale_parts.append(f"Perfect for {', '.join(intent_keywords)}")

            if score > 0.8:
                rationale_parts.append("with excellent style coordination")
            elif score > 0.6:
                rationale_parts.append("with good style coordination")

            if item_count >= 4:
                rationale_parts.append("creating a complete look")
            elif item_count >= 3:
                rationale_parts.append("for a well-balanced outfit")

            rationale = " ".join(rationale_parts) + "."

            # Add specific item details
            items = outfit.get("items", [])
            if items:
                top_items = [item for item in items if item.get("role") == "top"]
                bottom_items = [item for item in items if item.get("role") == "bottom"]

                if top_items and bottom_items:
                    rationale += f" Features {top_items[0].get('title', 'a top')} and {bottom_items[0].get('title', 'bottom')}."

            return rationale

        except Exception as e:
            self.logger.error("Error generating outfit rationale", error=str(e))
            return "Stylish outfit recommendation."

    async def _generate_theme_rationale(
        self,
        outfit: Dict[str, Any],
        theme: str,
        rules: Dict[str, Any]
    ) -> str:
        """Generate rationale for a theme-based outfit."""
        try:
            item_count = outfit.get("item_count", 0)
            score = outfit.get("score", 0)

            rationale = f"Perfect {theme} look"

            if score > 0.7:
                rationale += " with excellent coordination"
            elif score > 0.5:
                rationale += " with good styling"

            rationale += f" featuring {item_count} pieces."

            return rationale

        except Exception as e:
            self.logger.error("Error generating theme rationale", error=str(e))
            return f"Stylish {theme} outfit."