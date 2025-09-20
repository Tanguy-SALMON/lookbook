"""
Smart Recommendation Engine

This service uses LLM to generate rich keywords from user requests,
then ranks products based on keyword matching and relevance scoring.
No fuzzy matching needed - LLM does the heavy lifting for keyword expansion.
"""

import asyncio
import aiohttp
import json
import re
from typing import List, Dict, Any, Optional, Set
import logging
import structlog

from ..domain.entities import Intent, Item, Outfit, OutfitItem
from ..adapters.db_lookbook import MySQLLookbookRepository
from ..config.settings import settings

logger = structlog.get_logger()


class SmartRecommender:
    """
    LLM-powered smart recommendation engine.

    Uses LLM to expand user requests into rich keyword sets,
    then ranks products based on keyword matching.
    """

    def __init__(self, repository: MySQLLookbookRepository):
        self.repository = repository
        self.logger = logger.bind(service="smart_recommender")
        self.llm_host = settings.ollama_host
        self.llm_model = settings.ollama_text_model

    async def recommend_outfits(
        self, user_message: str, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Generate outfit recommendations based on user message.

        Args:
            user_message: Original user request
            limit: Maximum number of outfits to return

        Returns:
            List of outfit recommendations with products and explanations
        """
        try:
            self.logger.info("Starting smart recommendation", message=user_message)

            # Step 1: Use LLM to generate rich keywords
            keywords = await self._generate_keywords_from_message(user_message)

            # Step 2: Search products using keywords
            products = await self._search_products_by_keywords(keywords, limit * 3)

            # Step 3: Create outfit combinations
            outfits = await self._create_outfit_combinations(products, keywords, limit)

            self.logger.info(
                "Smart recommendation completed",
                keywords_generated=len(keywords.get("keywords", [])),
                products_found=len(products),
                outfits_created=len(outfits),
            )

            return outfits

        except Exception as e:
            self.logger.error("Smart recommendation failed", error=str(e))
            return []

    async def _generate_keywords_from_message(self, message: str) -> Dict[str, Any]:
        """
        Use LLM to generate expanded keywords from user message.

        Args:
            message: User's original message

        Returns:
            Dictionary with expanded keywords and context
        """
        prompt = f"""You are a fashion stylist. Expand this customer request into detailed fashion keywords for product search.

Customer says: "{message}"

Generate comprehensive keywords in JSON format:

{{
  "keywords": ["keyword1", "keyword2", "keyword3"],
  "colors": ["color1", "color2"],
  "occasions": ["occasion1", "occasion2"],
  "styles": ["style1", "style2"],
  "categories": ["category1", "category2"],
  "materials": ["material1", "material2"],
  "mood": "description of desired mood/vibe",
  "price_range": "budget_indication",
  "explanation": "why these keywords fit the request"
}}

Examples:
"I go to dance" -> {{
  "keywords": ["party", "dance", "movement", "stylish", "trendy", "night out", "social", "energetic", "fun"],
  "colors": ["black", "navy", "white"],
  "occasions": ["party", "festival", "concert", "date"],
  "styles": ["trendy", "chic", "modern", "bold"],
  "categories": ["dress", "top", "bottom"],
  "materials": ["stretchy", "comfortable", "breathable"],
  "mood": "confident and ready to dance",
  "price_range": "mid_range",
  "explanation": "Dancing requires stylish, comfortable clothes that allow movement and make you feel confident"
}}

"I like drive" -> {{
  "keywords": ["comfortable", "travel", "casual", "versatile", "practical", "journey", "road trip", "relaxed"],
  "colors": ["beige", "grey", "navy", "white"],
  "occasions": ["travel", "casual", "hiking"],
  "styles": ["casual", "comfortable", "minimalist"],
  "categories": ["top", "bottom", "outerwear"],
  "materials": ["cotton", "soft", "stretchy"],
  "mood": "relaxed and comfortable for travel",
  "price_range": "practical",
  "explanation": "Driving and travel require comfortable, versatile clothes that work for long periods"
}}

Return ONLY the JSON object for: "{message}"
"""

        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=10)
            ) as session:
                payload = {
                    "model": self.llm_model,
                    "prompt": prompt,
                    "temperature": 0.4,
                    "max_tokens": 400,
                    "stream": False,
                }

                async with session.post(
                    f"{self.llm_host}/api/generate", json=payload
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        response_text = result.get("response", "")

                        # Parse JSON from LLM response
                        keywords = self._parse_keywords_json(response_text)

                        self.logger.info(
                            "Keywords generated successfully",
                            keywords_count=len(keywords.get("keywords", [])),
                            mood=keywords.get("mood", "N/A"),
                        )

                        return keywords
                    else:
                        raise Exception(f"LLM API error: {response.status}")

        except Exception as e:
            self.logger.warning(
                "LLM keyword generation failed, using fallback", error=str(e)
            )
            return self._generate_fallback_keywords(message)

    def _parse_keywords_json(self, response: str) -> Dict[str, Any]:
        """Parse JSON keywords from LLM response."""
        try:
            # Extract JSON from response
            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                keywords = json.loads(json_str)

                # Ensure required fields exist
                required_fields = {
                    "keywords": [],
                    "colors": [],
                    "occasions": [],
                    "styles": [],
                    "categories": [],
                    "materials": [],
                    "mood": "",
                    "price_range": "mid_range",
                    "explanation": "",
                }

                for field, default in required_fields.items():
                    if field not in keywords:
                        keywords[field] = default

                return keywords
            else:
                raise ValueError("No JSON found in response")

        except Exception as e:
            self.logger.error("Failed to parse keywords JSON", error=str(e))
            return self._generate_fallback_keywords("")

    def _generate_fallback_keywords(self, message: str) -> Dict[str, Any]:
        """Generate basic keywords when LLM fails."""
        message_lower = message.lower()

        # Simple keyword extraction
        keywords = []
        colors = []
        occasions = []
        styles = ["casual"]
        categories = []

        # Basic keyword mapping
        if any(word in message_lower for word in ["dance", "dancing", "party"]):
            keywords = ["party", "dance", "stylish", "trendy"]
            occasions = ["party", "festival"]
            styles = ["trendy", "chic"]
            categories = ["dress", "top"]
            colors = ["black", "navy"]

        elif any(word in message_lower for word in ["drive", "driving", "travel"]):
            keywords = ["comfortable", "travel", "casual", "practical"]
            occasions = ["travel", "casual"]
            styles = ["casual", "comfortable"]
            categories = ["top", "bottom"]
            colors = ["beige", "grey"]

        elif any(word in message_lower for word in ["business", "work", "office"]):
            keywords = ["professional", "business", "formal", "elegant"]
            occasions = ["business", "interview"]
            styles = ["professional", "classic"]
            categories = ["top", "bottom", "dress"]
            colors = ["black", "navy", "white"]

        else:
            keywords = ["casual", "comfortable", "style"]
            occasions = ["casual"]
            styles = ["casual"]
            categories = ["top", "bottom", "dress"]
            colors = ["white", "beige"]

        return {
            "keywords": keywords,
            "colors": colors,
            "occasions": occasions,
            "styles": styles,
            "categories": categories,
            "materials": ["cotton", "comfortable"],
            "mood": "casual and comfortable",
            "price_range": "mid_range",
            "explanation": f"Basic keywords for: {message}",
        }

    async def _search_products_by_keywords(
        self, keywords: Dict[str, Any], limit: int = 15
    ) -> List[Dict[str, Any]]:
        """
        Search products using generated keywords.

        Uses direct keyword matching against product attributes.
        """
        try:
            conn = await self.repository._get_connection()
            try:
                cursor = await conn.cursor()
                try:
                    # Build search query using keywords
                    search_terms = []
                    params = []

                    # Add keyword searches
                    all_keywords = (
                        keywords.get("keywords", [])
                        + keywords.get("colors", [])
                        + keywords.get("occasions", [])
                        + keywords.get("styles", [])
                        + keywords.get("materials", [])
                    )

                    for keyword in all_keywords[
                        :10
                    ]:  # Limit to prevent overly complex queries
                        search_terms.extend(
                            [
                                "pva.occasion LIKE %s",
                                "pva.color = %s",
                                "pva.style LIKE %s",
                                "pva.material LIKE %s",
                                "p.title LIKE %s",
                            ]
                        )
                        params.extend(
                            [
                                f"%{keyword}%",  # occasion
                                keyword,  # color (exact match)
                                f"%{keyword}%",  # style
                                f"%{keyword}%",  # material
                                f"%{keyword}%",  # title
                            ]
                        )

                    # Build the query
                    search_clause = " OR ".join(search_terms) if search_terms else "1=1"

                    query = f"""
                        SELECT p.sku, p.title, p.price, p.image_key,
                               pva.color, pva.category, pva.occasion, pva.style,
                               pva.material, pva.description,
                               COUNT(*) as match_count
                        FROM products p
                        JOIN product_vision_attributes pva ON p.sku = pva.sku
                        WHERE p.in_stock = 1 AND ({search_clause})
                        GROUP BY p.sku, p.title, p.price, p.image_key,
                                 pva.color, pva.category, pva.occasion, pva.style,
                                 pva.material, pva.description
                        ORDER BY match_count DESC, p.price ASC
                        LIMIT %s
                    """

                    params.append(limit)

                    await cursor.execute(query, params)
                    results = await cursor.fetchall()

                    # Convert to dictionaries
                    columns = [
                        "sku",
                        "title",
                        "price",
                        "image_key",
                        "color",
                        "category",
                        "occasion",
                        "style",
                        "material",
                        "description",
                        "match_count",
                    ]

                    products = []
                    for row in results:
                        product = dict(zip(columns, row))
                        # Calculate relevance score based on keyword matches
                        product["relevance_score"] = self._calculate_keyword_score(
                            product, keywords
                        )
                        products.append(product)

                    # Sort by relevance score
                    products.sort(key=lambda x: x["relevance_score"], reverse=True)

                    return products

                finally:
                    await cursor.close()
            finally:
                await conn.ensure_closed()

        except Exception as e:
            self.logger.error("Product search failed", error=str(e))
            return []

    def _calculate_keyword_score(
        self, product: Dict[str, Any], keywords: Dict[str, Any]
    ) -> float:
        """Calculate relevance score based on keyword matches."""
        score = 0.0

        # Get product attributes with null safety
        title = (product.get("title") or "").lower()
        color = (product.get("color") or "").lower()
        occasion = (product.get("occasion") or "").lower()
        style = (product.get("style") or "").lower()
        material = (product.get("material") or "").lower()
        category = (product.get("category") or "").lower()

        # Score keyword matches with different weights

        # Exact color matches (high weight)
        for kw_color in keywords.get("colors", []):
            if kw_color.lower() == color:
                score += 25

        # Occasion matches (high weight)
        for kw_occasion in keywords.get("occasions", []):
            if kw_occasion.lower() in occasion:
                score += 20

        # Category matches (high weight)
        for kw_category in keywords.get("categories", []):
            if kw_category.lower() == category:
                score += 20

        # Style matches (medium weight)
        for kw_style in keywords.get("styles", []):
            if kw_style.lower() in style:
                score += 15

        # Material matches (medium weight)
        for kw_material in keywords.get("materials", []):
            if kw_material.lower() in material:
                score += 10

        # General keyword matches in title (lower weight)
        for keyword in keywords.get("keywords", []):
            if keyword.lower() in title:
                score += 5

        # Bonus for database match_count
        score += min(product.get("match_count", 0) * 2, 10)

        return min(score, 100)  # Cap at 100

    async def _create_outfit_combinations(
        self, products: List[Dict[str, Any]], keywords: Dict[str, Any], limit: int
    ) -> List[Dict[str, Any]]:
        """Create outfit combinations from found products."""
        try:
            # Group products by category (with simple correction)
            categorized = self._group_products_by_category(products)

            outfits = []

            # Strategy 1: Complete dress outfits
            for dress in categorized.get("dress", [])[:2]:
                outfit = {
                    "title": self._generate_outfit_title(dress, keywords),
                    "items": [self._format_product_item(dress)],
                    "total_price": float(dress["price"]),
                    "style_explanation": self._generate_style_explanation(
                        dress, keywords
                    ),
                    "outfit_type": "complete_look",
                }
                outfits.append(outfit)

            # Strategy 2: Top + Bottom combinations
            tops = categorized.get("top", [])
            bottoms = categorized.get("bottom", [])

            if tops and bottoms:
                for top in tops[:2]:
                    for bottom in bottoms[:2]:
                        if self._check_color_compatibility(top, bottom):
                            outfit = {
                                "title": self._generate_combo_title(
                                    top, bottom, keywords
                                ),
                                "items": [
                                    self._format_product_item(top),
                                    self._format_product_item(bottom),
                                ],
                                "total_price": float(top["price"])
                                + float(bottom["price"]),
                                "style_explanation": self._generate_combo_explanation(
                                    top, bottom, keywords
                                ),
                                "outfit_type": "coordinated_set",
                            }
                            outfits.append(outfit)

                            if len(outfits) >= limit:
                                break
                    if len(outfits) >= limit:
                        break

            # Strategy 3: Single standout pieces
            if len(outfits) < limit:
                for product in products[: limit - len(outfits)]:
                    if product.get("category") in ["top", "dress", "outerwear"]:
                        outfit = {
                            "title": self._generate_single_title(product, keywords),
                            "items": [self._format_product_item(product)],
                            "total_price": float(product["price"]),
                            "style_explanation": self._generate_single_explanation(
                                product, keywords
                            ),
                            "outfit_type": "statement_piece",
                        }
                        outfits.append(outfit)

            # Sort by relevance and price
            outfits.sort(
                key=lambda x: (
                    -max(item["relevance_score"] for item in x["items"]),
                    x["total_price"],
                )
            )

            return outfits[:limit]

        except Exception as e:
            self.logger.error("Outfit creation failed", error=str(e))
            return []

    def _group_products_by_category(
        self, products: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Group products by category with simple title-based correction."""
        groups = {"top": [], "bottom": [], "dress": [], "outerwear": [], "other": []}

        for product in products:
            title = (product.get("title") or "").lower()
            category = product.get("category") or "other"

            # Simple category correction
            corrected_category = category
            if any(word in title for word in ["dress", "frock", "gown"]):
                corrected_category = "dress"
            elif any(
                word in title
                for word in ["blouse", "shirt", "top", "cardigan", "sweater"]
            ):
                corrected_category = "top"
            elif any(word in title for word in ["shorts", "pants", "skirt", "jeans"]):
                corrected_category = "bottom"
            elif any(word in title for word in ["jacket", "coat", "blazer", "hoodie"]):
                corrected_category = "outerwear"

            if corrected_category in groups:
                groups[corrected_category].append(product)
            else:
                groups["other"].append(product)

        return groups

    def _format_product_item(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """Format product for outfit item."""
        return {
            "sku": product["sku"],
            "title": product["title"],
            "price": float(product["price"]),
            "image_url": f"{settings.s3_base_url_with_trailing_slash}{product['image_key']}",
            "color": product.get("color") or "N/A",
            "category": product.get("category") or "N/A",
            "relevance_score": product.get("relevance_score", 0),
        }

    def _check_color_compatibility(
        self, item1: Dict[str, Any], item2: Dict[str, Any]
    ) -> bool:
        """Simple color compatibility check."""
        color1 = (item1.get("color") or "").lower()
        color2 = (item2.get("color") or "").lower()

        # Same color is always compatible
        if color1 == color2:
            return True

        # Define compatible color pairs
        compatible_pairs = {
            "black": ["white", "grey", "beige"],
            "white": ["black", "grey", "navy", "beige"],
            "navy": ["white", "beige", "grey"],
            "grey": ["white", "black", "beige"],
            "beige": ["white", "black", "grey", "navy"],
        }

        return color2 in compatible_pairs.get(color1, [])

    def _generate_outfit_title(
        self, dress: Dict[str, Any], keywords: Dict[str, Any]
    ) -> str:
        """Generate title for dress outfit."""
        mood = (keywords.get("mood") or "").lower()
        occasion = dress.get("occasion") or "casual"

        if "confident" in mood or "dance" in mood:
            return f"Confident {occasion.title()} Look"
        elif "comfortable" in mood or "travel" in mood:
            return f"Comfortable {occasion.title()} Style"
        elif "professional" in mood or "business" in mood:
            return f"Professional {occasion.title()} Outfit"
        else:
            return f"Perfect {occasion.title()} Dress"

    def _generate_combo_title(
        self, top: Dict[str, Any], bottom: Dict[str, Any], keywords: Dict[str, Any]
    ) -> str:
        """Generate title for top+bottom combination."""
        mood = keywords.get("mood", "")
        return f"{mood.title() if mood else 'Stylish'} Coordinated Set"

    def _generate_single_title(
        self, product: Dict[str, Any], keywords: Dict[str, Any]
    ) -> str:
        """Generate title for single piece."""
        category = product.get("category", "piece").title()
        return f"Statement {category}"

    def _generate_style_explanation(
        self, dress: Dict[str, Any], keywords: Dict[str, Any]
    ) -> str:
        """Generate explanation for dress outfit."""
        explanation = keywords.get("explanation") or ""
        color = dress.get("color") or "colored"
        material = dress.get("material") or "fabric"

        return f"This {color} dress in {material} is {explanation.lower() if explanation else 'perfect for your needs'}"

    def _generate_combo_explanation(
        self, top: Dict[str, Any], bottom: Dict[str, Any], keywords: Dict[str, Any]
    ) -> str:
        """Generate explanation for combination outfit."""
        explanation = keywords.get("explanation") or ""
        top_color = top.get("color") or "colored"
        bottom_color = bottom.get("color") or "colored"

        return f"This {top_color} top paired with {bottom_color} bottom creates the perfect look. {explanation if explanation else 'Great for your occasion!'}"

    def _generate_single_explanation(
        self, product: Dict[str, Any], keywords: Dict[str, Any]
    ) -> str:
        """Generate explanation for single piece."""
        explanation = keywords.get("explanation") or ""
        return f"This {product.get('color') or 'beautiful'} piece is {explanation.lower() if explanation else 'perfect for making a statement'}"
