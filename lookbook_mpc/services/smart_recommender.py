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
        self.llm_model = settings.ollama_text_model_fast

    async def recommend_outfits(
        self, user_message: str, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Generate outfit recommendations based on user message using LLM-powered analysis.

        This is the main entry point for the recommendation engine. It orchestrates:
        1. LLM keyword generation from natural language
        2. Database product search using generated keywords
        3. Outfit combination assembly with scoring
        4. Response formatting for frontend consumption

        Example Input:
            user_message: "I go to dance"
            limit: 3

        Example Output:
            [
                {
                    "title": "Party Ready Look",
                    "items": [
                        {"sku": "123", "title": "Black Top", "price": 45.0, "category": "top"},
                        {"sku": "456", "title": "Party Skirt", "price": 39.0, "category": "bottom"}
                    ],
                    "total_price": 84.0,
                    "style_explanation": "Perfect for dancing - stylish and comfortable",
                    "outfit_type": "coordinated_set"
                }
            ]

        Args:
            user_message: Original user request (e.g., "I go to dance", "need business outfit")
            limit: Maximum number of outfits to return (default: 5)

        Returns:
            List of outfit recommendation dictionaries with items, prices, and explanations
        """
        try:
            self.logger.info("Starting smart recommendation process", message=user_message, limit=limit)

            # Step 1: Use LLM to generate rich keywords
            self.logger.info("Step 1: Generating keywords from user message")
            keywords = await self._generate_keywords_from_message(user_message)
            self.logger.info("Step 1 completed: Keywords generated",
                           keyword_count=len(keywords.get("keywords", [])),
                           colors=len(keywords.get("colors", [])),
                           categories=len(keywords.get("categories", [])))

            # Step 2: Search products using keywords
            self.logger.info("Step 2: Searching products using generated keywords")
            search_limit = limit * 3  # Get more products than needed for better selection
            products = await self._search_products_by_keywords(keywords, search_limit)
            self.logger.info("Step 2 completed: Products found", product_count=len(products))

            # Step 3: Create outfit combinations
            self.logger.info("Step 3: Creating outfit combinations from products")
            outfits = await self._create_outfit_combinations(products, keywords, limit)
            self.logger.info("Step 3 completed: Outfits created", outfit_count=len(outfits))

            self.logger.info(
                "Smart recommendation process completed successfully",
                user_message=user_message,
                keywords_generated=len(keywords.get("keywords", [])),
                products_found=len(products),
                outfits_created=len(outfits),
                limit_requested=limit
            )

            return outfits

        except Exception as e:
            self.logger.error("Smart recommendation process failed",
                            error=str(e),
                            user_message=user_message,
                            limit=limit)
            return []

    async def _generate_keywords_from_message(self, message: str) -> Dict[str, Any]:
        """
        Use LLM to generate expanded keywords from user message.

        This method is crucial - it transforms natural language into searchable fashion terms.
        The LLM understands context and generates comprehensive keyword sets that our
        simple keyword matching can use effectively.

        Example Input: "I go to dance"
        Example Output: {
            "keywords": ["party", "dance", "movement", "stylish", "trendy", "night out"],
            "colors": ["black", "navy", "white"],
            "occasions": ["party", "festival", "concert"],
            "styles": ["trendy", "chic", "modern", "bold"],
            "categories": ["dress", "top", "bottom"],
            "materials": ["stretchy", "comfortable", "breathable"],
            "mood": "confident and ready to dance",
            "explanation": "Dancing requires stylish, comfortable clothes that allow movement"
        }

        Args:
            message: User's original message (e.g., "I go to dance", "need work clothes")

        Returns:
            Dictionary with expanded keywords across multiple fashion dimensions
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
            self.logger.info("Sending prompt to LLM for keyword generation",
                            llm_host=self.llm_host,
                            llm_model=self.llm_model,
                            prompt_length=len(prompt),
                            user_message=message)

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

                        self.logger.info("LLM response received",
                                        llm_model=self.llm_model,
                                        response_length=len(response_text),
                                        prompt_sent=prompt,
                                        response_received=response_text)

                        # Parse JSON from LLM response
                        keywords = self._parse_keywords_json(response_text)

                        self.logger.info(
                            "Keywords generated successfully",
                            llm_info=f"{self.llm_model}@{self.llm_host}",
                            keywords_count=len(keywords.get("keywords", [])),
                            colors_count=len(keywords.get("colors", [])),
                            categories_count=len(keywords.get("categories", [])),
                            mood=keywords.get("mood", "N/A"),
                        )

                        return keywords
                    else:
                        raise Exception(f"LLM API error: {response.status}")

        except Exception as e:
            self.logger.warning(
                "LLM keyword generation failed, falling back to rule-based extraction",
                error=str(e),
                reason="LLM API unavailable or returned invalid response",
                message=message
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
            self.logger.warning("Failed to parse LLM keywords JSON, falling back to rule-based extraction",
                              error=str(e),
                              reason="LLM response was not valid JSON or missing required fields")
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
            categories = ["dress", "top", "bottom"]
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
        Search products using generated keywords with relevance scoring and category balancing.

        Uses direct keyword matching against product attributes (title, color, style, material, occasion).
        Products are scored based on how many keywords match and in which attributes.
        Includes fallback strategy to ensure balanced mix across categories.

        Example Input: keywords = {"keywords": ["party", "stylish"], "colors": ["black"], "styles": ["chic"]}
        Example Output: [
            {"sku": "123", "title": "Black Party Dress", "score": 0.89, "color": "black", "price": 79.0},
            {"sku": "456", "title": "Stylish Top", "score": 0.72, "color": "navy", "price": 45.0}
        ]

        Args:
            keywords: Dictionary with keyword arrays from LLM generation
            limit: Maximum number of products to return (default: 15)

        Returns:
            List of products with relevance scores, sorted by score descending
        """
        try:
            self.logger.info("Starting product search with keywords", keywords=keywords, limit=limit)
            conn = await self.repository._get_connection()
            try:
                cursor = await conn.cursor()
                try:
                    # Strategy 1: Try keyword-based search first
                    self.logger.info("Strategy 1: Executing keyword-based search")
                    products = await self._search_by_keywords(cursor, keywords, limit)
                    self.logger.info("Keyword search completed", products_found=len(products))

                    # Strategy 2: If we don't have enough variety, add category-based fallback
                    if len(products) < limit:
                        self.logger.info("Strategy 2: Insufficient products from keyword search, using category-based fallback",
                                       current_count=len(products), target_limit=limit,
                                       reason="Need more products for balanced recommendations")
                        fallback_products = await self._search_by_categories(cursor, keywords, limit - len(products))
                        products.extend(fallback_products)
                        self.logger.info("Category fallback completed", additional_products=len(fallback_products))

                    # Strategy 3: Ensure we have both tops and bottoms for complete outfits
                    self.logger.info("Strategy 3: Ensuring category balance for complete outfits")
                    products = await self._ensure_category_balance(cursor, products, keywords, limit)
                    self.logger.info("Category balance check completed", final_count=len(products))

                    # Remove duplicates and diversify
                    self.logger.info("Diversifying products to remove duplicates")
                    products = self._diversify_products(products)

                    final_products = products[:limit]
                    self.logger.info("Product search completed successfully",
                                   total_products_found=len(final_products),
                                   keywords_used=len(keywords.get("keywords", [])))

                    return final_products

                finally:
                    await cursor.close()
            finally:
                await conn.ensure_closed()

        except Exception as e:
            self.logger.error("Product search failed", error=str(e))
            return []

    async def _search_by_keywords(self, cursor, keywords: Dict[str, Any], limit: int) -> List[Dict[str, Any]]:
        """Search products using keyword matching."""
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

        # Validate and clean keywords
        valid_keywords = []
        for keyword in all_keywords:
            if isinstance(keyword, str) and keyword.strip():
                # Remove potentially problematic characters and limit length
                clean_keyword = keyword.strip()[:50]  # Limit to 50 chars
                # Remove quotes and semicolons that could break SQL
                clean_keyword = clean_keyword.replace("'", "").replace('"', '').replace(';', '')
                if clean_keyword:
                    valid_keywords.append(clean_keyword)

        self.logger.info("Keyword validation completed",
                        original_keywords=all_keywords,
                        valid_keywords=valid_keywords[:8])

        for keyword in valid_keywords[:8]:  # Limit to prevent overly complex queries
            search_terms.extend([
                "pva.occasion LIKE %s",
                "pva.color = %s",
                "pva.style LIKE %s",
                "pva.material LIKE %s",
                "p.title LIKE %s",
            ])
            params.extend([
                f"%{keyword}%",  # occasion
                keyword,  # color (exact match)
                f"%{keyword}%",  # style
                f"%{keyword}%",  # material
                f"%{keyword}%",  # title
            ])

        search_clause = " OR ".join(search_terms) if search_terms else "1=1"

        query = """
            SELECT p.sku, p.title, p.price, p.image_key,
                   pva.color, pva.category, pva.occasion, pva.style,
                   pva.material, pva.description,
                   COUNT(*) as match_count
            FROM products p
            JOIN product_vision_attributes pva ON p.sku = pva.sku
            WHERE p.in_stock = 1 AND ({})
            GROUP BY p.sku, p.title, p.price, p.image_key,
                     pva.color, pva.category, pva.occasion, pva.style,
                     pva.material, pva.description
            ORDER BY match_count DESC, p.price ASC
            LIMIT %s
        """.format(search_clause)

        params.append(limit)

        # Validate query before execution
        self.logger.info("Preparing keyword search query",
                        search_terms_count=len(search_terms),
                        params_count=len(params),
                        keywords_used=all_keywords[:8])

        # Create full query string with parameters for logging
        try:
            # Format parameters with proper quoting for strings
            formatted_params = []
            for param in params:
                if isinstance(param, str):
                    # Escape single quotes and wrap in single quotes
                    escaped = param.replace("'", "''")
                    formatted_params.append(f"'{escaped}'")
                else:
                    formatted_params.append(str(param))

            full_query = query.strip() % tuple(formatted_params)
            self.logger.info("Query formatting successful")
        except (TypeError, ValueError) as e:
            self.logger.error("Query formatting failed", error=str(e), query_template=query.strip(), params=params)
            # Try to identify the issue
            for i, param in enumerate(params):
                if not isinstance(param, (str, int, float)):
                    self.logger.error("Invalid parameter type", param_index=i, param_value=param, param_type=type(param))
            return []

        self.logger.info("Executing keyword-based SQL query",
                        full_query=full_query,
                        params=params)

        try:
            await cursor.execute(query, params)
            results = await cursor.fetchall()
        except Exception as e:
            self.logger.error("SQL execution failed", error=str(e), query=full_query, params=params)

            # Try a simple test query to check database connectivity
            try:
                await cursor.execute("SELECT COUNT(*) FROM products WHERE in_stock = 1")
                test_result = await cursor.fetchone()
                self.logger.info("Database connectivity test", total_products=test_result[0] if test_result else 0)
            except Exception as test_e:
                self.logger.error("Database connectivity test failed", error=str(test_e))

            # Try a simplified version of the query to isolate the issue
            try:
                simple_query = """
                    SELECT p.sku, p.title, p.price, p.image_key,
                           pva.color, pva.category
                    FROM products p
                    JOIN product_vision_attributes pva ON p.sku = pva.sku
                    WHERE p.in_stock = 1 AND p.title LIKE %s
                    LIMIT 5
                """
                await cursor.execute(simple_query, ['%professional%'])
                simple_results = await cursor.fetchall()
                self.logger.info("Simplified query test", results_count=len(simple_results), sample=simple_results[:2] if simple_results else [])
            except Exception as simple_e:
                self.logger.error("Simplified query test failed", error=str(simple_e))

            return []

        # Log query results for debugging
        self.logger.info("Keyword search SQL executed",
                        results_count=len(results),
                        sample_results=results[:3] if results else [])  # Show first 3 results for debugging

        return self._convert_results_to_products(results, keywords)

    async def _search_by_categories(self, cursor, keywords: Dict[str, Any], limit: int) -> List[Dict[str, Any]]:
        """Fallback search to ensure we get products from desired categories."""
        self.logger.info("Starting category-based fallback search", target_limit=limit)
        products = []
        categories = keywords.get("categories", ["top", "bottom", "dress"])

        for category in categories:
            if len(products) >= limit:
                break

            # Get top products from this category, prioritizing matching colors
            color_conditions = []
            color_params = []

            for color in keywords.get("colors", []):
                color_conditions.append("pva.color = %s")
                color_params.append(color)

            color_clause = " OR ".join(color_conditions) if color_conditions else "1=1"

            query = f"""
                SELECT p.sku, p.title, p.price, p.image_key,
                       pva.color, pva.category, pva.occasion, pva.style,
                       pva.material, pva.description,
                       1 as match_count
                FROM products p
                JOIN product_vision_attributes pva ON p.sku = pva.sku
                WHERE p.in_stock = 1 AND pva.category = %s AND ({color_clause})
                ORDER BY p.price ASC
                LIMIT %s
            """

            params = [category] + color_params + [max(1, limit // len(categories))]

            # Create full query string with parameters for logging
            try:
                # Format parameters with proper quoting for strings
                formatted_params = []
                for param in params:
                    if isinstance(param, str):
                        # Escape single quotes and wrap in single quotes
                        escaped = param.replace("'", "''")
                        formatted_params.append(f"'{escaped}'")
                    else:
                        formatted_params.append(str(param))

                full_query = query.strip() % tuple(formatted_params)
            except (TypeError, ValueError):
                full_query = f"Query formatting failed: {query.strip()}"

            self.logger.info("Executing category fallback SQL query",
                            category=category,
                            full_query=full_query,
                            params=params)

            await cursor.execute(query, params)
            results = await cursor.fetchall()

            # Log query results for debugging
            self.logger.info("Category fallback SQL executed",
                            category=category,
                            results_count=len(results),
                            sample_results=results[:2] if results else [])  # Show first 2 results for debugging

            category_products = self._convert_results_to_products(results, keywords)
            products.extend(category_products)

            self.logger.info("Category search completed", category=category, products_found=len(category_products))

        self.logger.info("Category-based fallback search completed", total_products=len(products))
        return products

    def _convert_results_to_products(self, results, keywords) -> List[Dict[str, Any]]:
        """Convert database results to product dictionaries with scores."""
        columns = [
            "sku", "title", "price", "image_key", "color", "category",
            "occasion", "style", "material", "description", "match_count",
        ]

        products = []
        for row in results:
            product = dict(zip(columns, row))
            product["relevance_score"] = self._calculate_keyword_score(product, keywords)
            products.append(product)

        return products

    def _balance_categories(self, products: List[Dict[str, Any]], keywords: Dict[str, Any], limit: int) -> List[Dict[str, Any]]:
        """Ensure we have a balanced mix of categories for outfit creation."""
        grouped = self._group_products_by_category(products)
        balanced = []

        # Prioritize getting at least one item from each desired category
        desired_categories = keywords.get("categories", ["top", "bottom", "dress"])

        for category in desired_categories:
            if category in grouped and grouped[category] and len(balanced) < limit:
                # Add the best item from this category
                best_item = max(grouped[category], key=lambda x: x["relevance_score"])
                balanced.append(best_item)
                grouped[category].remove(best_item)

        # Fill remaining slots with best remaining items
        remaining_items = []
        for category_items in grouped.values():
            remaining_items.extend(category_items)

        remaining_items.sort(key=lambda x: x["relevance_score"], reverse=True)

        for item in remaining_items:
            if len(balanced) >= limit:
                break
            if item not in balanced:
                balanced.append(item)

        return balanced

    def _calculate_keyword_score(
        self, product: Dict[str, Any], keywords: Dict[str, Any]
    ) -> float:
        """
        Calculate relevance score based on keyword matches with weighted scoring.

        This is the core scoring algorithm that ranks products by relevance to user intent.
        Different attributes have different weights based on fashion importance:
        - Color matches: 25 points (most important for visual appeal)
        - Occasion/Category: 20 points (functional fit)
        - Style/Material: 10-15 points (quality indicators)
        - Title keywords: 5 points (general relevance)

        Example Input:
            product = {"title": "Black Party Dress", "color": "black", "occasion": "party", "style": "elegant"}
            keywords = {"colors": ["black"], "occasions": ["party"], "styles": ["elegant"]}

        Example Output: 65.0 (25 + 20 + 15 + 5 bonus points)

        Args:
            product: Product dictionary with attributes (color, style, material, etc.)
            keywords: Generated keywords dictionary from LLM

        Returns:
            Float score 0-100 representing product relevance to user intent
        """
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

    def _diversify_products(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Remove duplicate product variants to ensure outfit diversity.

        Keeps only one variant per product title to prevent multiple sizes/colors
        of the same item from dominating recommendations.

        Example Input: [
            {"title": "RIBBED TANK TOP", "sku": "001", "color": "black"},
            {"title": "RIBBED TANK TOP", "sku": "002", "color": "white"},
            {"title": "PARTY DRESS", "sku": "003", "color": "red"}
        ]
        Example Output: [
            {"title": "RIBBED TANK TOP", "sku": "001", "color": "black"},
            {"title": "PARTY DRESS", "sku": "003", "color": "red"}
        ]
        """
        seen_titles = set()
        diversified = []

        for product in products:
            title = product.get("title", "").strip()
            if title and title not in seen_titles:
                seen_titles.add(title)
                diversified.append(product)

        self.logger.info(
            "Product diversification completed",
            original_count=len(products),
            diversified_count=len(diversified),
            removed_duplicates=len(products) - len(diversified)
        )

        return diversified

    async def _ensure_category_balance(
        self, cursor, products: List[Dict[str, Any]], keywords: Dict[str, Any], limit: int
    ) -> List[Dict[str, Any]]:
        """
        Ensure we have both tops and bottoms for complete outfit creation.

        If the main search didn't return both categories, explicitly search for missing ones.
        This guarantees we can create complete outfits with tops AND bottoms.
        """
        try:
            # Group existing products by category
            grouped = self._group_products_by_category(products)

            has_tops = len(grouped.get('top', [])) > 0
            has_bottoms = len(grouped.get('bottom', [])) > 0
            has_dresses = len(grouped.get('dress', [])) > 0

            self.logger.info("Checking category balance",
                           has_tops=has_tops,
                           has_bottoms=has_bottoms,
                           has_dresses=has_dresses,
                           current_product_count=len(products))

            # If we have dresses, that's fine - they are complete outfits
            if has_dresses:
                self.logger.info("Category balance satisfied: Dresses available for complete outfits")
                return products

            # If we're missing tops or bottoms, search specifically for them
            additional_products = []

            if not has_tops:
                # Search for tops with broader criteria
                self.logger.info("Category balance fallback: Searching for missing tops",
                               reason="No tops found in initial search, needed for complete outfits")
                tops = await self._search_specific_category(cursor, 'top', keywords, 3)
                additional_products.extend(tops)
                self.logger.info("Added missing tops via fallback search", count=len(tops))

            if not has_bottoms:
                # Search for bottoms with broader criteria
                self.logger.info("Category balance fallback: Searching for missing bottoms",
                               reason="No bottoms found in initial search, needed for complete outfits")
                bottoms = await self._search_specific_category(cursor, 'bottom', keywords, 3)
                additional_products.extend(bottoms)
                self.logger.info("Added missing bottoms via fallback search", count=len(bottoms))

            final_products = products + additional_products
            self.logger.info("Category balance check completed",
                           additional_products_added=len(additional_products),
                           final_product_count=len(final_products))

            return final_products

        except Exception as e:
            self.logger.error("Category balance failed", error=str(e))
            return products

    async def _search_specific_category(
        self, cursor, category: str, keywords: Dict[str, Any], limit: int
    ) -> List[Dict[str, Any]]:
        """Search for specific category (top/bottom/dress) with broader criteria."""
        try:
            self.logger.info("Searching for specific missing category", category=category, limit=limit)
            # Use basic color and style matching for the specific category
            colors = keywords.get("colors", [])
            if not colors:
                colors = ["black", "navy", "white"]  # Default colors

            # Build a simpler search for this category
            if colors:
                color_conditions = " OR ".join(["pva.color = %s"] * len(colors))
                query = f"""
                    SELECT p.sku, p.title, p.price, p.image_key,
                           pva.color, pva.category, pva.occasion, pva.style,
                           pva.material, pva.description,
                           1 as match_count
                    FROM products p
                    JOIN product_vision_attributes pva ON p.sku = pva.sku
                    WHERE p.in_stock = 1
                      AND pva.category = %s
                      AND ({color_conditions} OR pva.style = 'casual')
                    ORDER BY p.price ASC
                    LIMIT %s
                """
                params = [category] + colors + [limit]

                # Create full query string with parameters for logging
                try:
                    # Format parameters with proper quoting for strings
                    formatted_params = []
                    for param in params:
                        if isinstance(param, str):
                            # Escape single quotes and wrap in single quotes
                            escaped = param.replace("'", "''")
                            formatted_params.append(f"'{escaped}'")
                        else:
                            formatted_params.append(str(param))

                    full_query = query.strip() % tuple(formatted_params)
                except (TypeError, ValueError):
                    full_query = f"Query formatting failed: {query.strip()}"

                self.logger.info("Executing specific category SQL query with colors",
                                category=category,
                                full_query=full_query,
                                params=params,
                                colors=colors)
            else:
                # Fallback without color conditions
                query = """
                    SELECT p.sku, p.title, p.price, p.image_key,
                           pva.color, pva.category, pva.occasion, pva.style,
                           pva.material, pva.description,
                           1 as match_count
                    FROM products p
                    JOIN product_vision_attributes pva ON p.sku = pva.sku
                    WHERE p.in_stock = 1
                      AND pva.category = %s
                      AND pva.style = 'casual'
                    ORDER BY p.price ASC
                    LIMIT %s
                """
                params = [category, limit]

                # Create full query string with parameters for logging
                try:
                    # Format parameters with proper quoting for strings
                    formatted_params = []
                    for param in params:
                        if isinstance(param, str):
                            # Escape single quotes and wrap in single quotes
                            escaped = param.replace("'", "''")
                            formatted_params.append(f"'{escaped}'")
                        else:
                            formatted_params.append(str(param))

                    full_query = query.strip() % tuple(formatted_params)
                except (TypeError, ValueError):
                    full_query = f"Query formatting failed: {query.strip()}"

                self.logger.info("Executing specific category SQL query without colors",
                                category=category,
                                full_query=full_query,
                                params=params,
                                reason="No preferred colors specified, using casual style fallback")

            await cursor.execute(query, params)
            results = await cursor.fetchall()

            # Log query results for debugging
            self.logger.info("Specific category SQL executed",
                            category=category,
                            results_count=len(results),
                            sample_results=results[:2] if results else [])  # Show first 2 results for debugging

            products = self._convert_results_to_products(results, keywords)
            self.logger.info("Specific category search completed", category=category, products_found=len(products))

            return products

        except Exception as e:
            self.logger.error("Specific category search failed", category=category, error=str(e))
            return []

    async def _create_outfit_combinations(
        self, products: List[Dict[str, Any]], keywords: Dict[str, Any], limit: int
    ) -> List[Dict[str, Any]]:
        """
        Create outfit combinations from products using fashion rules.

        Groups products by category and creates complete outfits:
        - Single dress = complete outfit
        - Top + bottom = coordinated set
        - Ensures color compatibility
        - Generates appropriate titles and explanations

        Example Input: products = [dress1, top1, bottom1], keywords = {...}, limit = 2
        Example Output: [
            {
                "title": "Elegant Evening Look",
                "items": [dress1],
                "total_price": 89.0,
                "style_explanation": "Perfect standalone piece for your occasion",
                "outfit_type": "single_piece"
            },
            {
                "title": "Coordinated Casual Set",
                "items": [top1, bottom1],
                "total_price": 124.0,
                "style_explanation": "Stylish coordination with complementary pieces",
                "outfit_type": "coordinated_set"
            }
        ]

        Args:
            products: List of scored products from search
            keywords: Generated keywords for context
            limit: Maximum number of outfit combinations to create

        Returns:
            List of complete outfit dictionaries ready for frontend display
        """
        try:
            self.logger.info("Starting outfit combination creation",
                           available_products=len(products),
                           target_limit=limit)

            # Group products by category (with simple correction)
            categorized = self._group_products_by_category(products)
            self.logger.info("Products categorized",
                           dress_count=len(categorized.get("dress", [])),
                           top_count=len(categorized.get("top", [])),
                           bottom_count=len(categorized.get("bottom", [])),
                           other_count=len(categorized.get("other", [])))

            outfits = []

            # Strategy 1: Complete dress outfits
            dress_outfits = 0
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
                dress_outfits += 1

            self.logger.info("Strategy 1 completed: Dress outfits created", count=dress_outfits)

            # Strategy 2: Top + Bottom combinations
            combo_outfits = 0
            tops = categorized.get("top", [])
            bottoms = categorized.get("bottom", [])

            if tops and bottoms:
                self.logger.info("Strategy 2: Creating top+bottom combinations",
                               available_tops=len(tops),
                               available_bottoms=len(bottoms))

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
                            combo_outfits += 1

                            if len(outfits) >= limit:
                                break
                    if len(outfits) >= limit:
                        break

                self.logger.info("Strategy 2 completed: Combination outfits created", count=combo_outfits)
            else:
                self.logger.info("Strategy 2 skipped: Missing tops or bottoms for combinations",
                               has_tops=bool(tops),
                               has_bottoms=bool(bottoms))

            # Strategy 3: Single standout pieces
            single_outfits = 0
            if len(outfits) < limit:
                remaining_slots = limit - len(outfits)
                self.logger.info("Strategy 3: Adding single standout pieces", remaining_slots=remaining_slots)

                for product in products[:remaining_slots]:
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
                        single_outfits += 1

                self.logger.info("Strategy 3 completed: Single piece outfits created", count=single_outfits)

            # Sort by relevance and price
            self.logger.info("Sorting outfits by relevance and price")
            outfits.sort(
                key=lambda x: (
                    -max(item["relevance_score"] for item in x["items"]),
                    x["total_price"],
                )
            )

            final_outfits = outfits[:limit]
            self.logger.info("Outfit creation completed successfully",
                           total_outfits=len(final_outfits),
                           dress_outfits=dress_outfits,
                           combo_outfits=combo_outfits,
                           single_outfits=single_outfits)

            return final_outfits

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
        """
        Format product for outfit response - converts database format to frontend format.

        Example Input: {"id": 123, "sku": "ABC123", "title": "Black Top", "price": 45.0, "image_key": "img.jpg"}
        Example Output: {"sku": "ABC123", "title": "Black Top", "price": 45.0, "image_url": "https://cdn.../img.jpg", "category": "top"}

        Args:
            product: Raw product dictionary from database query

        Returns:
            Frontend-formatted product dictionary with image_url and proper structure
        """
        return {
            "sku": product["sku"],
            "title": product["title"],
            "price": float(product["price"]),
            "image_url": f"{settings.s3_base_url_with_trailing_slash}{product['image_key']}",
            "product_url": f"https://th.cos.com/th_en/{product['sku']}.html",
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

        # Define compatible color pairs - more permissive for better outfit combinations
        compatible_pairs = {
            "black": ["white", "grey", "beige", "navy", "blue", "denim-blue"],
            "white": ["black", "grey", "navy", "beige", "blue", "denim-blue"],
            "navy": ["white", "beige", "grey", "black", "blue", "denim-blue"],
            "grey": ["white", "black", "beige", "navy", "blue"],
            "beige": ["white", "black", "grey", "navy", "brown"],
            "blue": ["white", "black", "grey", "navy", "denim-blue"],
            "denim-blue": ["black", "white", "navy", "grey", "blue"],
            "brown": ["beige", "white", "black"],
        }

        # If colors aren't in our compatibility map, be more permissive
        if color1 in compatible_pairs:
            return color2 in compatible_pairs[color1]
        elif color2 in compatible_pairs:
            return color1 in compatible_pairs[color2]
        else:
            # For unknown colors, allow the combination (be permissive)
            return True

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
