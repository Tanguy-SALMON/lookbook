#!/usr/bin/env python3
"""
Detailed debug script to trace the exact search query execution in SmartRecommender.
This will help identify why _search_products_by_keywords returns 0 results.
"""

import asyncio
import os
import sys
import json

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lookbook_mpc.services.smart_recommender import SmartRecommender
from lookbook_mpc.adapters.db_lookbook import MySQLLookbookRepository
from lookbook_mpc.config.settings import get_settings


async def debug_search_query_step_by_step():
    """Step through the search query construction to find the issue."""
    print("=== DEBUGGING SEARCH QUERY STEP BY STEP ===\n")

    try:
        settings = get_settings()
        repository = MySQLLookbookRepository(settings.get_database_url())
        recommender = SmartRecommender(repository)

        # Generate keywords like the recommender does
        test_message = "I go to dance"
        keywords = await recommender._generate_keywords_from_message(test_message)

        print(f"Generated keywords: {json.dumps(keywords, indent=2)}")

        # Now let's manually trace through _search_by_keywords
        conn = await repository._get_connection()
        cursor = await conn.cursor()

        # Replicate the _search_by_keywords logic step by step
        search_terms = []
        params = []

        # Add keyword searches (this is from the actual method)
        all_keywords = (
            keywords.get("keywords", [])
            + keywords.get("colors", [])
            + keywords.get("occasions", [])
            + keywords.get("styles", [])
            + keywords.get("materials", [])
        )

        print(f"\nAll keywords combined: {all_keywords}")

        for keyword in all_keywords[:8]:  # Limit to prevent overly complex queries
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

        print(f"\nSearch clause length: {len(search_clause)} characters")
        print(f"Number of search terms: {len(search_terms)}")
        print(f"Number of params: {len(params)}")

        # Show first few search terms
        print(f"\nFirst 3 search terms:")
        for i in range(min(3, len(search_terms))):
            print(f"  {search_terms[i]} -> {params[i]}")

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
            LIMIT 15
        """

        print(f"\nFull query:\n{query}")

        # Execute the query
        params.append(15)  # Add the LIMIT parameter

        print(f"\nExecuting query with {len(params)} parameters...")

        try:
            await cursor.execute(query, params)
            results = await cursor.fetchall()

            print(f"Query executed successfully!")
            print(f"Results found: {len(results)}")

            if results:
                print("\nFirst 5 results:")
                for i, result in enumerate(results[:5]):
                    sku, title, price, image_key, color, category, occasion, style, material, desc, match_count = result
                    print(f"  {i+1}. {sku}: {title}")
                    print(f"     Category: {category}, Color: {color}, Matches: {match_count}")
            else:
                print("No results found - this is the problem!")

        except Exception as e:
            print(f"Query execution failed: {e}")
            print("This might be the issue!")

        await cursor.close()
        conn.close()

    except Exception as e:
        print(f"Error in step-by-step debug: {e}")
        import traceback
        traceback.print_exc()


async def test_simplified_search():
    """Test a simplified version of the search to isolate the issue."""
    print("\n=== TESTING SIMPLIFIED SEARCH ===\n")

    try:
        settings = get_settings()
        repository = MySQLLookbookRepository(settings.get_database_url())
        conn = await repository._get_connection()
        cursor = await conn.cursor()

        # Very simple search - just look for "dance" or "party" in any field
        simple_query = """
            SELECT p.sku, p.title, p.price, pva.category, pva.color, pva.style
            FROM products p
            JOIN product_vision_attributes pva ON p.sku = pva.sku
            WHERE p.in_stock = 1
              AND (p.title LIKE %s OR p.title LIKE %s OR pva.style LIKE %s)
            LIMIT 10
        """

        await cursor.execute(simple_query, ["%dance%", "%party%", "%party%"])
        simple_results = await cursor.fetchall()

        print(f"Simplified search found {len(simple_results)} products:")
        for sku, title, price, category, color, style in simple_results:
            print(f"  {sku}: {title} - {category} - {color}")

        # Even simpler - just get any tops and bottoms
        basic_query = """
            SELECT p.sku, p.title, p.price, pva.category, pva.color
            FROM products p
            JOIN product_vision_attributes pva ON p.sku = pva.sku
            WHERE p.in_stock = 1
              AND pva.category IN ('top', 'bottom')
            LIMIT 10
        """

        await cursor.execute(basic_query)
        basic_results = await cursor.fetchall()

        print(f"\nBasic category search found {len(basic_results)} products:")

        tops = []
        bottoms = []
        for sku, title, price, category, color in basic_results:
            print(f"  {sku}: {title} - {category} - {color}")
            if category == 'top':
                tops.append((sku, title, price, color))
            elif category == 'bottom':
                bottoms.append((sku, title, price, color))

        print(f"\nFound {len(tops)} tops and {len(bottoms)} bottoms")
        print("This should be enough to create complete outfits!")

        await cursor.close()
        conn.close()

    except Exception as e:
        print(f"Simplified search error: {e}")


async def test_actual_recommender_method():
    """Test the actual recommender method to see where it fails."""
    print("\n=== TESTING ACTUAL RECOMMENDER METHOD ===\n")

    try:
        settings = get_settings()
        repository = MySQLLookbookRepository(settings.get_database_url())
        recommender = SmartRecommender(repository)

        # Generate keywords
        keywords = {
            "keywords": ["dance", "party"],
            "colors": ["black", "white"],
            "styles": ["stylish"],
            "materials": ["comfortable"],
            "occasions": ["party"]
        }

        print(f"Test keywords: {json.dumps(keywords, indent=2)}")

        # Call the actual search method
        products = await recommender._search_products_by_keywords(keywords, limit=15)

        print(f"\nRecommender search returned {len(products)} products:")

        if products:
            for product in products[:5]:
                print(f"  {product.get('sku')}: {product.get('title')} - {product.get('category', 'unknown')}")
        else:
            print("  No products returned - this confirms the issue!")

        # Test the grouping if we have products
        if products:
            grouped = recommender._group_products_by_category(products)
            print(f"\nGrouped products:")
            for category, items in grouped.items():
                if items:
                    print(f"  {category}: {len(items)} items")

    except Exception as e:
        print(f"Actual recommender method error: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Run all detailed debugging."""
    print("DETAILED SEARCH DEBUG FOR LOOKBOOK-MPC")
    print("=" * 50)

    await debug_search_query_step_by_step()
    await test_simplified_search()
    await test_actual_recommender_method()

    print("\n" + "=" * 50)
    print("DETAILED DEBUG COMPLETE")
    print("\nIf the simplified searches work but the complex search doesn't,")
    print("the issue is likely in the query complexity or parameter handling.")


if __name__ == "__main__":
    asyncio.run(main())
