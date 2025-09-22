#!/usr/bin/env python3
"""
Script to verify database results after sync and analysis.
This script will:
1. Check total number of products in database
2. Show products with vision attributes
3. Display product statistics
4. Verify data integrity
"""

import asyncio
import sys
import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lookbook_mpc.adapters.db_lookbook import SQLiteLookbookRepository
from lookbook_mpc.domain.entities import Item
from lookbook_mpc.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def get_product_statistics() -> Dict[str, Any]:
    """Get comprehensive product statistics from the database."""
    try:
        lookbook_repo = SQLiteLookbookRepository(database_url=settings.lookbook_db_url)

        # Get all products
        all_products = await lookbook_repo.get_all_items()

        if not all_products:
            return {"status": "no_products", "message": "No products found in database"}

        # Calculate statistics
        total_products = len(all_products)
        products_with_vision = 0
        products_by_category = {}
        products_by_price_range = {"under_30": 0, "30_50": 0, "50_100": 0, "over_100": 0}
        products_by_color = {}

        for product in all_products:
            if product is None:
                continue

            # Check for vision attributes
            if product.attributes and "vision_attributes" in product.attributes:
                products_with_vision += 1

            # Category statistics
            category = getattr(product, 'category', 'unknown')
            products_by_category[category] = products_by_category.get(category, 0) + 1

            # Price statistics
            price = getattr(product, 'price', 0)
            if price < 30:
                products_by_price_range["under_30"] += 1
            elif 30 <= price < 50:
                products_by_price_range["30_50"] += 1
            elif 50 <= price < 100:
                products_by_price_range["50_100"] += 1
            else:
                products_by_price_range["over_100"] += 1

            # Color statistics
            vision_attrs = product.attributes.get("vision_attributes", {}) if product.attributes else {}
            color = vision_attrs.get("color", "unknown")
            products_by_color[color] = products_by_color.get(color, 0) + 1

        return {
            "status": "success",
            "total_products": total_products,
            "products_with_vision": products_with_vision,
            "vision_analysis_percentage": (products_with_vision / total_products) * 100 if total_products > 0 else 0,
            "products_by_category": products_by_category,
            "products_by_price_range": products_by_price_range,
            "products_by_color": products_by_color,
            "sample_products": [
                {
                    "sku": p.sku,
                    "title": p.title,
                    "price": getattr(p, 'price', 0),
                    "category": getattr(p, 'category', 'unknown'),
                    "has_vision": "vision_attributes" in (p.attributes or {}),
                    "ingested_at": getattr(p, 'ingested_at', None)
                }
                for p in all_products[:10]  # Show first 10 products
            ]
        }

    except Exception as e:
        logger.error(f"Error getting product statistics: {e}")
        return {
            "status": "error",
            "error": str(e),
            "message": f"Failed to get statistics: {str(e)}"
        }

async def show_detailed_products(limit: int = 20):
    """Show detailed information about products."""
    try:
        lookbook_repo = LookbookRepository()
        products = await lookbook_repo.get_all_items(limit=limit)

        if not products:
            print("No products found in database.")
            return

        print(f"\n=== Detailed Product Information (First {len(products)}) ===")
        print("-" * 80)

        for i, product in enumerate(products, 1):
            print(f"\n{i}. Product ID: {product.id}")
            print(f"   SKU: {product.sku}")
            print(f"   Title: {product.title}")
            print(f"   Price: ${getattr(product, 'price', 0):.2f}")
            print(f"   Category: {getattr(product, 'category', 'unknown')}")
            print(f"   In Stock: {getattr(product, 'in_stock', True)}")
            print(f"   Image Key: {getattr(product, 'image_key', 'N/A')}")
            print(f"   Ingested At: {getattr(product, 'ingested_at', 'N/A')}")

            # Show vision attributes if available
            if product.attributes and "vision_attributes" in product.attributes:
                vision_attrs = product.attributes["vision_attributes"]
                print(f"   Vision Attributes:")
                for key, value in vision_attrs.items():
                    print(f"     - {key}: {value}")
            else:
                print(f"   Vision Attributes: Not analyzed")

            print("-" * 80)

    except Exception as e:
        logger.error(f"Error showing detailed products: {e}")

async def verify_data_integrity() -> Dict[str, Any]:
    """Verify data integrity in the database."""
    try:
        lookbook_repo = LookbookRepository()
        products = await lookbook_repo.get_all_items(limit=1000)

        integrity_issues = []

        for product in products:
            # Check for required fields
            if not product.sku:
                integrity_issues.append(f"Product {product.id} missing SKU")
            if not product.title:
                integrity_issues.append(f"Product {product.id} missing title")
            if not getattr(product, 'price', 0):
                integrity_issues.append(f"Product {product.id} missing or invalid price")

            # Check for valid image key
            image_key = getattr(product, 'image_key', None)
            if not image_key:
                integrity_issues.append(f"Product {product.id} missing image key")

        return {
            "status": "success",
            "total_products_checked": len(products),
            "integrity_issues": integrity_issues,
            "issues_count": len(integrity_issues)
        }

    except Exception as e:
        logger.error(f"Error verifying data integrity: {e}")
        return {
            "status": "error",
            "error": str(e),
            "message": f"Failed to verify data integrity: {str(e)}"
        }

async def main():
    """Main function to verify database results."""
    print("=== Database Verification Script ===")
    print("This script will verify the database results after sync and analysis.")
    print()

    # Get product statistics
    print("Fetching product statistics...")
    stats = await get_product_statistics()

    print("\n=== Product Statistics ===")
    print(f"Status: {stats['status']}")

    if stats['status'] == 'success':
        print(f"Total Products: {stats['total_products']}")
        print(f"Products with Vision Analysis: {stats['products_with_vision']}")
        print(f"Vision Analysis Percentage: {stats['vision_analysis_percentage']:.1f}%")

        print(f"\nProducts by Category:")
        for category, count in stats['products_by_category'].items():
            print(f"  {category}: {count}")

        print(f"\nProducts by Price Range:")
        for price_range, count in stats['products_by_price_range'].items():
            print(f"  {price_range}: {count}")

        print(f"\nProducts by Color (from vision analysis):")
        for color, count in stats['products_by_color'].items():
            print(f"  {color}: {count}")

        print(f"\nSample Products:")
        for product in stats['sample_products']:
            vision_status = "✓" if product['has_vision'] else "✗"
            print(f"  {vision_status} {product['sku']} - {product['title']} (${product['price']:.2f})")

    # Show detailed products
    await show_detailed_products(limit=10)

    # Verify data integrity
    print("\n=== Data Integrity Check ===")
    integrity = await verify_data_integrity()

    print(f"Status: {integrity['status']}")
    print(f"Products Checked: {integrity.get('total_products_checked', 0)}")
    print(f"Issues Found: {integrity.get('issues_count', 0)}")

    if integrity['status'] == 'success' and integrity.get('integrity_issues'):
        print("\nIntegrity Issues:")
        for issue in integrity['integrity_issues']:
            print(f"  - {issue}")

    print("\n=== Summary ===")
    if stats['status'] == 'success':
        total = stats['total_products']
        with_vision = stats['products_with_vision']
        print(f"Database contains {total} products")
        print(f"{with_vision} products have been analyzed with vision AI")

        if total > 0:
            percentage = (with_vision / total) * 100
            print(f"Analysis completion: {percentage:.1f}%")

            if percentage == 100:
                print("✓ All products have been analyzed!")
            elif percentage > 0:
                print(f"✓ Partial analysis complete - {int(percentage)}% done")
            else:
                print("✗ No products have been analyzed yet")

    print("\n=== Next Steps ===")
    if stats['status'] == 'success' and stats['products_with_vision'] > 0:
        print("1. Test recommendations with the analyzed products")
        print("2. Try the demo interface at http://localhost:8000/demo")
        print("3. Use the recommendation API to generate outfit suggestions")
    else:
        print("1. Run the sync script to add more products")
        print("2. Run the batch analysis script to analyze products")
        print("3. Then run this verification script again")

if __name__ == "__main__":
    asyncio.run(main())