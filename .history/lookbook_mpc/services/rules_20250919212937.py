"""
Rules Engine Service

This service implements the rules engine that maps user intents
to specific constraints and outfit composition rules.
"""

from typing import Dict, List, Any, Optional
import logging
import structlog

logger = structlog.get_logger()


class RulesEngine:
    """Rules engine for fashion recommendations."""

    def __init__(self):
        self.logger = logger.bind(service="rules_engine")
        self.rules = self._load_default_rules()

    def _load_default_rules(self) -> Dict[str, Any]:
        """Load default rules for different intents."""
        return {
            "yoga": {
                "name": "Yoga Outfit Rules",
                "constraints": {
                    "category": ["top", "bottom"],
                    "material": ["cotton", "nylon", "spandex"],
                    "stretch": True,
                    "comfort": "high",
                    "formality": "athleisure"
                },
                "objectives": ["comfort", "flexibility"],
                "palette": ["neutral", "pastel"],
                "excluded_categories": ["dress", "outerwear", "shoes", "accessory"]
            },
            "dinner": {
                "name": "Dinner Outfit Rules",
                "constraints": {
                    "category": ["top", "bottom", "dress"],
                    "material": ["cotton", "silk", "polyester"],
                    "formality": "elevated",
                    "occasion": "dinner"
                },
                "objectives": ["style", "confidence"],
                "palette": ["elegant", "classic"],
                "budget_range": [30, 150],
                "excluded_categories": ["sport", "beach"]
            },
            "slimming": {
                "name": "Slimming Outfit Rules",
                "constraints": {
                    "color": ["dark", "monochrome", "navy", "black"],
                    "pattern": ["plain", "vertical"],
                    "fit": ["slim", "regular"],
                    "layers": ["structured"],
                    "rise": ["mid", "high"]
                },
                "objectives": ["slimming", "confidence"],
                "excluded_patterns": ["horizontal", "large_print"],
                "excluded_colors": ["white", "light_colors"]
            },
            "casual": {
                "name": "Casual Outfit Rules",
                "constraints": {
                    "category": ["top", "bottom", "dress"],
                    "material": ["cotton", "denim", "linen"],
                    "formality": "casual",
                    "occasion": "everyday"
                },
                "objectives": ["comfort", "style"],
                "palette": ["versatile", "neutral"],
                "excluded_categories": ["formal", "business"]
            },
            "business": {
                "name": "Business Outfit Rules",
                "constraints": {
                    "category": ["top", "bottom", "dress", "outerwear"],
                    "material": ["wool", "cotton", "polyester"],
                    "formality": "business",
                    "occasion": "work"
                },
                "objectives": ["professional", "confidence"],
                "palette": ["professional", "neutral"],
                "excluded_categories": ["sport", "beach", "party"]
            },
            "party": {
                "name": "Party Outfit Rules",
                "constraints": {
                    "category": ["top", "bottom", "dress", "outerwear"],
                    "material": ["silk", "velvet", "sequin"],
                    "formality": "elevated",
                    "occasion": "party"
                },
                "objectives": ["style", "confidence", "attention"],
                "palette": ["elegant", "bold"],
                "excluded_categories": ["sport", "beach", "business"]
            },
            "beach": {
                "name": "Beach Outfit Rules",
                "constraints": {
                    "category": ["top", "bottom", "dress"],
                    "material": ["cotton", "linen", "polyester"],
                    "formality": "casual",
                    "occasion": "beach"
                },
                "objectives": ["comfort", "breathable", "style"],
                "palette": ["light", "bright", "beachy"],
                "excluded_categories": ["business", "formal", "winter"]
            },
            "sport": {
                "name": "Sport Outfit Rules",
                "constraints": {
                    "category": ["top", "bottom", "outerwear"],
                    "material": ["polyester", "nylon", "spandex"],
                    "formality": "athleisure",
                    "occasion": "sport"
                },
                "objectives": ["performance", "comfort", "flexibility"],
                "palette": ["sporty", "bright"],
                "excluded_categories": ["formal", "business", "party"]
            }
        }

    def get_rules_for_intent(self, intent: str) -> Optional[Dict[str, Any]]:
        """
        Get rules for a specific intent.

        Args:
            intent: Intent string (e.g., "yoga", "dinner", "slimming")

        Returns:
            Rules dictionary or None if no rules found
        """
        try:
            # Normalize intent string
            normalized_intent = intent.lower().strip()

            # Try exact match first
            if normalized_intent in self.rules:
                return self.rules[normalized_intent]

            # Try partial match
            for rule_intent, rule_data in self.rules.items():
                if normalized_intent in rule_intent or rule_intent in normalized_intent:
                    return rule_data

            # Return default rules if no specific match
            return self.rules.get("casual")

        except Exception as e:
            self.logger.error("Error getting rules for intent", intent=intent, error=str(e))
            return self.rules.get("casual")

    def apply_rules_to_items(self, items: List[Dict[str, Any]], rules: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Apply rules to filter and score items.

        Args:
            items: List of item dictionaries
            rules: Rules dictionary with constraints

        Returns:
            Filtered and scored list of items
        """
        try:
            self.logger.info("Applying rules to items", item_count=len(items), rules=rules.get("name", "unknown"))

            filtered_items = []

            for item in items:
                if self._item_matches_rules(item, rules):
                    scored_item = self._score_item_for_rules(item, rules)
                    filtered_items.append(scored_item)

            # Sort by score (descending)
            filtered_items.sort(key=lambda x: x.get("rule_score", 0), reverse=True)

            self.logger.info("Rule application completed",
                           original_count=len(items),
                           filtered_count=len(filtered_items))

            return filtered_items

        except Exception as e:
            self.logger.error("Error applying rules to items", error=str(e))
            return []

    def _item_matches_rules(self, item: Dict[str, Any], rules: Dict[str, Any]) -> bool:
        """Check if an item matches the given rules."""
        try:
            vision_attrs = item.get("attributes", {}).get("vision_attributes", {})

            # Check included categories
            if "constraints" in rules and "category" in rules["constraints"]:
                allowed_categories = rules["constraints"]["category"]
                item_category = vision_attrs.get("category")
                if item_category and item_category not in allowed_categories:
                    return False

            # Check excluded categories
            if "excluded_categories" in rules:
                excluded_categories = rules["excluded_categories"]
                item_category = vision_attrs.get("category")
                if item_category and item_category in excluded_categories:
                    return False

            # Check material constraints
            if "constraints" in rules and "material" in rules["constraints"]:
                allowed_materials = rules["constraints"]["material"]
                item_material = vision_attrs.get("material")
                if item_material and item_material not in allowed_materials:
                    return False

            # Check color constraints
            if "constraints" in rules and "color" in rules["constraints"]:
                allowed_colors = rules["constraints"]["color"]
                item_color = vision_attrs.get("color")
                if item_color and item_color not in allowed_colors:
                    return False

            # Check pattern constraints
            if "constraints" in rules and "pattern" in rules["constraints"]:
                allowed_patterns = rules["constraints"]["pattern"]
                item_pattern = vision_attrs.get("pattern")
                if item_pattern and item_pattern not in allowed_patterns:
                    return False

            # Check excluded patterns
            if "excluded_patterns" in rules:
                excluded_patterns = rules["excluded_patterns"]
                item_pattern = vision_attrs.get("pattern")
                if item_pattern and item_pattern in excluded_patterns:
                    return False

            # Check budget constraints
            if "budget_range" in rules:
                min_budget, max_budget = rules["budget_range"]
                item_price = item.get("price", 0)
                if not (min_budget <= item_price <= max_budget):
                    return False

            return True

        except Exception as e:
            self.logger.warning("Error checking item against rules", error=str(e))
            return False

    def _score_item_for_rules(self, item: Dict[str, Any], rules: Dict[str, Any]) -> Dict[str, Any]:
        """Score an item based on how well it matches the rules."""
        try:
            scored_item = item.copy()
            score = 0.0  # Base score

            vision_attrs = item.get("attributes", {}).get("vision_attributes", {})

            # Score based on category match
            if "constraints" in rules and "category" in rules["constraints"]:
                if vision_attrs.get("category") in rules["constraints"]["category"]:
                    score += 0.3

            # Score based on material match
            if "constraints" in rules and "material" in rules["constraints"]:
                if vision_attrs.get("material") in rules["constraints"]["material"]:
                    score += 0.2

            # Score based on color match
            if "constraints" in rules and "color" in rules["constraints"]:
                if vision_attrs.get("color") in rules["constraints"]["color"]:
                    score += 0.2

            # Score based on pattern match
            if "constraints" in rules and "pattern" in rules["constraints"]:
                if vision_attrs.get("pattern") in rules["constraints"]["pattern"]:
                    score += 0.15

            # Score based on budget fit
            if "budget_range" in rules:
                min_budget, max_budget = rules["budget_range"]
                item_price = item.get("price", 0)
                if min_budget <= item_price <= max_budget:
                    score += 0.15
                elif item_price <= max_budget:
                    score += 0.05  # Partial score for under budget

            # Normalize score to 0-1 range
            scored_item["rule_score"] = min(score, 1.0)

            return scored_item

        except Exception as e:
            self.logger.warning("Error scoring item for rules", error=str(e))
            item["rule_score"] = 0.0
            return item

    def add_custom_rule(self, intent: str, rule_data: Dict[str, Any]) -> None:
        """
        Add a custom rule for an intent.

        Args:
            intent: Intent string
            rule_data: Rule dictionary
        """
        try:
            self.rules[intent.lower().strip()] = rule_data
            self.logger.info("Custom rule added", intent=intent)
        except Exception as e:
            self.logger.error("Error adding custom rule", intent=intent, error=str(e))

    def get_all_rules(self) -> Dict[str, Any]:
        """Get all loaded rules."""
        return self.rules.copy()