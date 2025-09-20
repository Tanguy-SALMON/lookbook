"""
Fuzzy Product Matcher Service

This service handles fuzzy matching of products based on user intents,
with category correction and multi-attribute scoring for recommendations.
"""

import re
from typing import List, Dict, Any, Optional, Set
import logging
import structlog
from datetime import datetime

from ..domain.entities import Intent, Item
from ..adapters.db_lookbook import MySQLLookbookRepository

logger = structlog.get_logger()


class FuzzyProductMatcher:
    """
    Fuzzy matching service for finding products based on user intents.

    Handles category misclassifications, multi-attribute scoring,
    and intent-to-database query mapping.
    """

    def __init__(self, repository: MySQLLookbookRepository):
        self.repository = repository
        self.logger = logger.bind(service="fuzzy_matcher")

        # Intent to occasion mapping
        self.intent_occasion_map = {
            "dancing": ["party", "festival", "concert"],
            "driving": ["travel", "casual"],
            "business": ["business", "interview", "formal"],
            "casual": ["casual", "picnic", "brunch"],
            "workout": ["gym", "sport", "running", "yoga"],
            "party": ["party", "festival", "concert", "date"],
            "formal": ["formal", "gala", "wedding", "theater"],
            "date": ["date", "party", "festival"],
            "travel": ["travel", "casual", "hiking"],
            "beach": ["beach", "casual"],
            "wedding": ["wedding", "formal", "gala"],
        }

        # Color compatibility matrix
        self.color_compatibility = {
            "black": ["white", "beige", "grey", "navy"],
            "white": ["black", "beige", "grey", "navy"],
            "navy": ["white", "beige", "grey"],
            "grey": ["white", "black", "beige"],
            "beige": ["white", "black", "grey", "navy"],
        }

        # Category correction patterns
        self.category_patterns = {
            "top": [
                r"blouse",
                r"shirt",
                r"top",
                r"cardigan",
                r"sweater",
                r"t-shirt",
                r"tank",
                r"camisole",
                r"pullover",
            ],
            "bottom": [
                r"shorts",
                r"pants",
                r"trousers",
                r"jeans",
                r"skirt",
                r"leggings",
                r"joggers",
            ],
            "dress": [r"dress", r"frock", r"gown"],
            "outerwear": [
                r"jacket",
                r"coat",
                r"blazer",
                r"hoodie",
                r"vest",
                r"windbreaker",
                r"parka",
            ],
        }

    async def search_by_intent(
        self, intent: Dict[str, Any], limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search products using fuzzy matching based on user intent.

        Args:
            intent: Parsed user intent with occasion, activity, colors, etc.
            limit: Maximum number of products to return

        Returns:
            List of products with relevance scores
        """
        try:
            self.logger.info("Starting fuzzy product search", intent=intent)

            # Map intent to database searchable occasions
            search_occasions = self._map_intent_to_occasions(intent)

            # Build fuzzy search query
            products = await self._search_products_fuzzy(
                occasions=search_occasions,
                colors=intent.get("colors", []),
                budget_max=intent.get("budget_max"),
                styles=intent.get("objectives", []),
                limit=limit * 2,  # Get more to score and filter
            )

            # Score and rank products
            scored_products = []
            for product in products:
                score = self._calculate_relevance_score(product, intent)
                if score >= 50:  # Minimum threshold
                    product["relevance_score"] = score
                    product["corrected_category"] = self._fix_category_classification(
                        product
                    )
                    scored_products.append(product)

            # Sort by relevance score
            scored_products.sort(key=lambda x: x["relevance_score"], reverse=True)

            self.logger.info(
                "Fuzzy search completed",
                total_found=len(products),
                scored_products=len(scored_products),
                top_score=scored_products[0]["relevance_score"]
                if scored_products
                else 0,
            )

            return scored_products[:limit]

        except Exception as e:
            self.logger.error("Fuzzy search failed", error=str(e))
            return []

    def _map_intent_to_occasions(self, intent: Dict[str, Any]) -> List[str]:
        """Map user intent to database occasion values."""
        occasions = set()

        # Direct occasion mapping
        if intent.get("occasion"):
            occasions.add(intent["occasion"])

        # Activity to occasion mapping
        activity = intent.get("activity")
        if activity and activity in self.intent_occasion_map:
            occasions.update(self.intent_occasion_map[activity])

        # Objective to occasion mapping
        objectives = intent.get("objectives", [])
        for obj in objectives:
            if obj == "professional":
                occasions.update(["business", "interview", "formal"])
            elif obj == "comfort":
                occasions.update(["casual", "sport", "gym"])
            elif obj == "style" or obj == "trendy":
                occasions.update(["party", "date", "festival"])

        # Fallback to casual if no occasions found
        if not occasions:
            occasions.add("casual")

        return list(occasions)

    async def _search_products_fuzzy(
        self,
        occasions: List[str] = None,
        colors: List[str] = None,
        budget_max: Optional[float] = None,
        styles: List[str] = None,
        limit: int = 40,
    ) -> List[Dict[str, Any]]:
        """Execute fuzzy database search with LIKE patterns."""

        conn = await self.repository._get_connection()
        try:
            cursor = await conn.cursor()
            try:
                # Build dynamic WHERE clause with fuzzy matching
                where_conditions = ["p.in_stock = 1"]
                params = []

                # Occasion fuzzy matching
                if occasions:
                    occasion_likes = []
                    for occ in occasions:
                        occasion_likes.append("pva.occasion LIKE %s")
                        params.append(f"%{occ}%")
                    where_conditions.append("({})".format(" OR ".join(occasion_likes)))

                # Color matching (exact or compatible)
                if colors:
                    color_conditions = []
                    for color in colors:
                        color_conditions.append("pva.color = %s")
                        params.append(color)
                        # Add compatible colors
                        compatible = self.color_compatibility.get(color, [])
                        for comp_color in compatible:
                            color_conditions.append("pva.color = %s")
                            params.append(comp_color)
                    where_conditions.append(
                        "({})".format(" OR ".join(color_conditions))
                    )

                # Budget constraint
                if budget_max:
                    where_conditions.append("p.price <= %s")
                    params.append(budget_max)

                # Style/objective fuzzy matching
                if styles:
                    style_likes = []
                    for style in styles:
                        # Map objectives to style attributes
                        if style == "professional":
                            style_likes.extend(
                                [
                                    "pva.style LIKE '%%classic%%'",
                                    "pva.style LIKE '%%sophisticated%%'",
                                    "pva.formal_level IN ('business', 'formal')",
                                ]
                            )
                        elif style == "comfort":
                            style_likes.extend(
                                [
                                    "pva.style LIKE '%%casual%%'",
                                    "pva.fit IN ('relaxed', 'loose')",
                                ]
                            )
                        elif style in ["style", "trendy"]:
                            style_likes.extend(
                                [
                                    "pva.style LIKE '%%trendy%%'",
                                    "pva.style LIKE '%%modern%%'",
                                    "pva.style LIKE '%%chic%%'",
                                ]
                            )

                    if style_likes:
                        where_conditions.append("({})".format(" OR ".join(style_likes)))

                # Build final query
                where_clause = " AND ".join(where_conditions)

                query = """
                    SELECT p.sku, p.title, p.price, p.image_key, p.in_stock,
                           pva.color, pva.category, pva.occasion, pva.style,
                           pva.material, pva.formal_level, pva.fit,
                           pva.description, pva.confidence_score
                    FROM products p
                    JOIN product_vision_attributes pva ON p.sku = pva.sku
                    WHERE {}
                    ORDER BY pva.confidence_score DESC, p.price ASC
                    LIMIT %s
                """.format(where_clause)

                params.append(limit)

                await cursor.execute(query, params)
                results = await cursor.fetchall()

                # Convert to dictionaries
                columns = [
                    "sku",
                    "title",
                    "price",
                    "image_key",
                    "in_stock",
                    "color",
                    "category",
                    "occasion",
                    "style",
                    "material",
                    "formal_level",
                    "fit",
                    "description",
                    "confidence_score",
                ]

                products = []
                for row in results:
                    product = dict(zip(columns, row))
                    products.append(product)

                return products

            finally:
                await cursor.close()
        finally:
            await conn.ensure_closed()

    def _calculate_relevance_score(
        self, product: Dict[str, Any], intent: Dict[str, Any]
    ) -> float:
        """
        Calculate relevance score for a product against user intent.

        Scoring weights:
        - Occasion match: 40 points
        - Color preference: 25 points
        - Style compatibility: 20 points
        - Price range: 15 points
        """
        score = 0.0

        # Occasion scoring (40 points max)
        product_occasion = product.get("occasion", "").lower()
        intent_occasions = self._map_intent_to_occasions(intent)

        if any(occ.lower() in product_occasion for occ in intent_occasions):
            score += 40
        elif any(occ.lower() in product_occasion for occ in ["casual", "picnic"]):
            score += 20  # Partial match for general occasions

        # Color scoring (25 points max)
        product_color = product.get("color", "").lower()
        intent_colors = [c.lower() for c in intent.get("colors", [])]

        if intent_colors:
            if product_color in intent_colors:
                score += 25
            elif any(
                product_color in self.color_compatibility.get(color, [])
                for color in intent_colors
            ):
                score += 15  # Compatible color
        else:
            score += 10  # No color preference specified

        # Style scoring (20 points max)
        product_style = product.get("style", "").lower()
        objectives = intent.get("objectives", [])

        style_matches = 0
        for obj in objectives:
            if obj == "professional" and any(
                s in product_style for s in ["classic", "sophisticated", "elegant"]
            ):
                style_matches += 1
            elif obj == "comfort" and any(
                s in product_style for s in ["casual", "relaxed"]
            ):
                style_matches += 1
            elif obj in ["style", "trendy"] and any(
                s in product_style for s in ["trendy", "modern", "chic"]
            ):
                style_matches += 1

        if objectives:
            score += (style_matches / len(objectives)) * 20
        else:
            score += 10  # No style preference specified

        # Price scoring (15 points max)
        product_price = float(product.get("price", 0))
        budget_max = intent.get("budget_max")

        if budget_max:
            if product_price <= budget_max:
                # Score higher for prices in sweet spot (50-80% of budget)
                ratio = product_price / budget_max
                if 0.5 <= ratio <= 0.8:
                    score += 15
                elif ratio <= 0.5:
                    score += 12  # Very affordable
                else:
                    score += 8  # At budget limit
        else:
            score += 10  # No budget specified

        # Bonus points for high confidence vision analysis
        confidence = float(product.get("confidence_score", 0))
        if confidence >= 0.9:
            score += 5
        elif confidence >= 0.8:
            score += 2

        return min(score, 100)  # Cap at 100

    def _fix_category_classification(self, product: Dict[str, Any]) -> str:
        """Fix misclassified product categories based on title analysis."""
        title = product.get("title", "").lower()
        original_category = product.get("category", "")

        # Check each category pattern
        for category, patterns in self.category_patterns.items():
            for pattern in patterns:
                if re.search(pattern, title):
                    if category != original_category:
                        self.logger.debug(
                            "Category correction applied",
                            sku=product.get("sku"),
                            title=product.get("title")[:30],
                            original=original_category,
                            corrected=category,
                        )
                    return category

        # Keep original if no pattern matches
        return original_category

    def group_products_by_category(
        self, products: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Group products by their corrected categories."""
        groups = {
            "top": [],
            "bottom": [],
            "dress": [],
            "outerwear": [],
            "shoes": [],
            "accessory": [],
            "other": [],
        }

        for product in products:
            category = product.get(
                "corrected_category", product.get("category", "other")
            )
            if category in groups:
                groups[category].append(product)
            else:
                groups["other"].append(product)

        return groups

    def check_color_compatibility(
        self, item1: Dict[str, Any], item2: Dict[str, Any]
    ) -> bool:
        """Check if two items have compatible colors."""
        color1 = item1.get("color", "").lower()
        color2 = item2.get("color", "").lower()

        if color1 == color2:
            return True

        compatible_colors = self.color_compatibility.get(color1, [])
        return color2 in compatible_colors

    async def get_outfit_suitable_products(
        self, intent: Dict[str, Any]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get products suitable for outfit creation, grouped by category.

        Returns products with corrected categories for outfit building.
        """
        try:
            # Search with higher limit for outfit building
            products = await self.search_by_intent(intent, limit=30)

            # Group by corrected categories
            grouped = self.group_products_by_category(products)

            # Filter to only include outfit-suitable categories
            outfit_categories = {
                "top": grouped["top"],
                "bottom": grouped["bottom"],
                "dress": grouped["dress"],
                "outerwear": grouped["outerwear"],
            }

            self.logger.info(
                "Outfit products retrieved",
                tops=len(outfit_categories["top"]),
                bottoms=len(outfit_categories["bottom"]),
                dresses=len(outfit_categories["dress"]),
                outerwear=len(outfit_categories["outerwear"]),
            )

            return outfit_categories

        except Exception as e:
            self.logger.error("Failed to get outfit products", error=str(e))
            return {"top": [], "bottom": [], "dress": [], "outerwear": []}
