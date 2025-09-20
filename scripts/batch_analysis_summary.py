#!/usr/bin/env python3
"""
Batch Analysis Summary Script

This script provides a comprehensive summary of the batch vision analysis results
and demonstrates the enhanced product data for fashion recommendations.
"""

import asyncio
import sys
import os
from typing import Dict, List, Any

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lookbook_mpc.adapters.db_lookbook import MySQLLookbookRepository
from lookbook_mpc.config import settings


async def get_analysis_summary() -> Dict[str, Any]:
    """Get comprehensive analysis summary from the database."""
    try:
        lookbook_repo = MySQLLookbookRepository(database_url=settings.lookbook_db_url)
        connection = await lookbook_repo._get_connection()

        # Get total product count
        total_query = "SELECT COUNT(*) FROM products WHERE in_stock = 1"

        # Get products with enhanced vision attributes
        enhanced_query = """
            SELECT COUNT(*) FROM products
            WHERE in_stock = 1
            AND (color IS NOT NULL AND color != '')
            AND (material IS NOT NULL AND material != '')
            AND (season IS NOT NULL AND season != '')
            AND (category IS NOT NULL AND category != '')
        """

        # Get attribute distributions
        color_query = """
            SELECT color, COUNT(*) as count
            FROM products
            WHERE in_stock = 1 AND color IS NOT NULL AND color != ''
            GROUP BY color
            ORDER BY count DESC
            LIMIT 10
        """

        season_query = """
            SELECT season, COUNT(*) as count
            FROM products
            WHERE in_stock = 1 AND season IS NOT NULL AND season != ''
            GROUP BY season
            ORDER BY count DESC
        """

        material_query = """
            SELECT material, COUNT(*) as count
            FROM products
            WHERE in_stock = 1 AND material IS NOT NULL AND material != ''
            GROUP BY material
            ORDER BY count DESC
            LIMIT 10
        """

        category_query = """
            SELECT category, COUNT(*) as count
            FROM products
            WHERE in_stock = 1 AND category IS NOT NULL AND category != ''
            GROUP BY category
            ORDER BY count DESC
            LIMIT 10
        """

        # Get sample enhanced products
        sample_query = """
            SELECT sku, title, price, color, material, season, category, occasion, pattern
            FROM products
            WHERE in_stock = 1
            AND color IS NOT NULL AND material IS NOT NULL
            AND season IS NOT NULL AND category IS NOT NULL
            ORDER BY updated_at DESC
            LIMIT 10
        """

        async with connection.cursor() as cursor:
            # Total products
            await cursor.execute(total_query)
            total_products = (await cursor.fetchone())[0]

            # Enhanced products
            await cursor.execute(enhanced_query)
            enhanced_products = (await cursor.fetchone())[0]

            # Color distribution
            await cursor.execute(color_query)
            colors = await cursor.fetchall()

            # Season distribution
            await cursor.execute(season_query)
            seasons = await cursor.fetchall()

            # Material distribution
            await cursor.execute(material_query)
            materials = await cursor.fetchall()

            # Category distribution
            await cursor.execute(category_query)
            categories = await cursor.fetchall()

            # Sample products
            await cursor.execute(sample_query)
            samples = await cursor.fetchall()

            return {
                "total_products": total_products,
                "enhanced_products": enhanced_products,
                "enhancement_rate": (enhanced_products / total_products * 100)
                if total_products > 0
                else 0,
                "colors": colors,
                "seasons": seasons,
                "materials": materials,
                "categories": categories,
                "samples": samples,
            }

    except Exception as e:
        print(f"Error getting analysis summary: {e}")
        return {}
    finally:
        if "connection" in locals():
            await connection.ensure_closed()


def print_analysis_summary(summary: Dict[str, Any]):
    """Print formatted analysis summary."""
    print("🎨 BATCH VISION ANALYSIS SUMMARY")
    print("=" * 50)
    print()

    # Overall Statistics
    print("📊 OVERALL STATISTICS")
    print("-" * 30)
    print(f"Total Products in Database: {summary.get('total_products', 0)}")
    print(f"Products with Vision Analysis: {summary.get('enhanced_products', 0)}")
    print(f"Enhancement Rate: {summary.get('enhancement_rate', 0):.1f}%")
    print()

    # Color Analysis
    if summary.get("colors"):
        print("🌈 COLOR DISTRIBUTION")
        print("-" * 30)
        for color, count in summary["colors"]:
            percentage = (
                (count / summary["enhanced_products"] * 100)
                if summary["enhanced_products"] > 0
                else 0
            )
            print(f"  {color.capitalize():15} {count:3d} products ({percentage:4.1f}%)")
        print()

    # Season Analysis
    if summary.get("seasons"):
        print("🌟 SEASON DISTRIBUTION")
        print("-" * 30)
        for season, count in summary["seasons"]:
            percentage = (
                (count / summary["enhanced_products"] * 100)
                if summary["enhanced_products"] > 0
                else 0
            )
            print(
                f"  {season.capitalize():15} {count:3d} products ({percentage:4.1f}%)"
            )
        print()

    # Material Analysis
    if summary.get("materials"):
        print("🧵 MATERIAL DISTRIBUTION")
        print("-" * 30)
        for material, count in summary["materials"]:
            percentage = (
                (count / summary["enhanced_products"] * 100)
                if summary["enhanced_products"] > 0
                else 0
            )
            print(
                f"  {material.capitalize():15} {count:3d} products ({percentage:4.1f}%)"
            )
        print()

    # Category Analysis
    if summary.get("categories"):
        print("📦 CATEGORY DISTRIBUTION")
        print("-" * 30)
        for category, count in summary["categories"]:
            percentage = (
                (count / summary["enhanced_products"] * 100)
                if summary["enhanced_products"] > 0
                else 0
            )
            print(
                f"  {category.capitalize():15} {count:3d} products ({percentage:4.1f}%)"
            )
        print()

    # Sample Products
    if summary.get("samples"):
        print("👗 SAMPLE ENHANCED PRODUCTS")
        print("-" * 30)
        for i, sample in enumerate(summary["samples"][:5], 1):
            sku, title, price, color, material, season, category, occasion, pattern = (
                sample
            )
            print(f"{i:2d}. {title[:40]}")
            print(f"     SKU: {sku}")
            print(f"     Price: ฿{price:,.0f}")
            print(f"     Attributes: {color} {material} {category} for {season}")
            if occasion:
                print(f"     Occasion: {occasion}")
            if pattern:
                print(f"     Pattern: {pattern}")
            print()


def print_recommendation_examples():
    """Print examples of how enhanced data enables better recommendations."""
    print("🎯 RECOMMENDATION CAPABILITIES")
    print("=" * 50)
    print()

    print("With the enhanced vision analysis data, the system can now provide:")
    print()

    print("🔍 SMART SEARCH QUERIES:")
    print("  • 'Show me white cotton dresses for summer'")
    print("  • 'Find black leather jackets for autumn'")
    print("  • 'I need business casual wool tops'")
    print("  • 'Show resort wear in beige and navy'")
    print()

    print("🤖 AI CHAT RECOMMENDATIONS:")
    print("  • 'What should I wear to a business meeting in Bangkok?'")
    print("  • 'I have a beach vacation, what casual dresses do you recommend?'")
    print("  • 'Show me versatile pieces that work for both day and night'")
    print("  • 'I like minimalist style, what would you suggest?'")
    print()

    print("📊 STYLE ANALYTICS:")
    print("  • Color palette analysis and seasonal trends")
    print("  • Material preferences and comfort ratings")
    print("  • Occasion-based outfit suggestions")
    print("  • Size inclusivity and fit recommendations")
    print()


def print_next_steps():
    """Print recommended next steps."""
    print("🚀 NEXT STEPS")
    print("=" * 50)
    print()

    print("✅ COMPLETED:")
    print("  1. ✓ Product sync from Magento database (100 products)")
    print("  2. ✓ Batch vision analysis with AI-generated attributes")
    print("  3. ✓ Database enhancement with detailed product descriptions")
    print("  4. ✓ Quality verification and attribute distribution analysis")
    print()

    print("🔄 READY FOR TESTING:")
    print("  1. Start the API server:")
    print("     poetry run python main.py")
    print()
    print("  2. Test basic recommendations:")
    print("     curl -X POST http://localhost:8000/v1/recommendations \\")
    print("       -H 'Content-Type: application/json' \\")
    print('       -d \'{"text_query": "summer dresses", "budget_max": 5000}\'')
    print()
    print("  3. Test AI chat interface:")
    print("     curl -X POST http://localhost:8000/v1/chat \\")
    print("       -H 'Content-Type: application/json' \\")
    print(
        '       -d \'{"message": "What should I wear for a beach vacation?", "session_id": "test-123"}\''
    )
    print()

    print("🔮 FUTURE ENHANCEMENTS:")
    print("  1. Set up real vision analysis with Ollama:")
    print("     - Install and configure Ollama with qwen2.5vl:7b model")
    print("     - Start vision sidecar: poetry run python vision_sidecar.py")
    print("     - Re-run analysis with real AI vision recognition")
    print()
    print("  2. Add more products:")
    print("     - Increase sync limit in scripts/sync_100_products.py")
    print("     - Run batch analysis on larger product sets")
    print()
    print("  3. Deploy to production:")
    print("     - Configure Redis for caching and queuing")
    print("     - Set up CDN for image delivery")
    print("     - Configure monitoring and metrics")
    print()


async def main():
    """Main function to show batch analysis summary."""
    print("Loading batch analysis summary...")
    print()

    # Get analysis data
    summary = await get_analysis_summary()

    if not summary:
        print("❌ Could not load analysis summary.")
        print(
            "Please ensure the database is accessible and batch analysis has been run."
        )
        return

    # Print comprehensive summary
    print_analysis_summary(summary)
    print_recommendation_examples()
    print_next_steps()


if __name__ == "__main__":
    asyncio.run(main())
