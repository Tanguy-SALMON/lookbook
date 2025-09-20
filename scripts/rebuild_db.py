#!/usr/bin/env python3
"""
Script to rebuild the database with clean schema
"""

import sqlite3
import os
from pathlib import Path

def rebuild_database():
    """Rebuild the database with clean schema"""

    # Get database path
    db_path = Path(__file__).parent.parent / "lookbook.db"

    # Remove existing database
    if db_path.exists():
        print(f"Removing existing database: {db_path}")
        db_path.unlink()

    # Read and execute SQL script
    sql_path = Path(__file__).parent / "init_db_clean.sql"

    if not sql_path.exists():
        print(f"SQL script not found: {sql_path}")
        return False

    print(f"Creating new database from: {sql_path}")

    try:
        # Read SQL script
        with open(sql_path, 'r') as f:
            sql_content = f.read()

        # Connect to database and execute SQL
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Execute SQL script
        cursor.executescript(sql_content)

        # Commit changes
        conn.commit()
        conn.close()

        print("Database rebuilt successfully!")
        print(f"Database created at: {db_path}")

        # Verify database structure
        verify_database(db_path)

        return True

    except Exception as e:
        print(f"Error rebuilding database: {e}")
        return False

def verify_database(db_path):
    """Verify the database structure and content"""

    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        print("\n=== Database Verification ===")

        # Check tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"Tables: {[table[0] for table in tables]}")

        # Check products table structure
        cursor.execute("PRAGMA table_info(products);")
        columns = cursor.fetchall()
        print(f"Products table columns: {[col[1] for col in columns]}")

        # Check sample data
        cursor.execute("SELECT COUNT(*) FROM products;")
        product_count = cursor.fetchone()[0]
        print(f"Products: {product_count}")

        cursor.execute("SELECT COUNT(*) FROM outfits;")
        outfit_count = cursor.fetchone()[0]
        print(f"Outfits: {outfit_count}")

        cursor.execute("SELECT COUNT(*) FROM rules;")
        rule_count = cursor.fetchone()[0]
        print(f"Rules: {rule_count}")

        # Show sample products
        cursor.execute("SELECT id, sku, title, price, category, color FROM products LIMIT 3;")
        sample_products = cursor.fetchall()
        print("\nSample products:")
        for product in sample_products:
            print(f"  ID: {product[0]}, SKU: {product[1]}, Title: {product[2]}, Price: {product[3]}, Category: {product[4]}, Color: {product[5]}")

        conn.close()

    except Exception as e:
        print(f"Error verifying database: {e}")

if __name__ == "__main__":
    print("=== Database Rebuild Script ===")
    print("This script will rebuild the database with a clean schema.")
    print()

    success = rebuild_database()

    if success:
        print("\n=== Next Steps ===")
        print("1. Run the sync script to populate with products")
        print("2. Run tests to verify everything works")
        print("3. Test the API endpoints")
    else:
        print("\nDatabase rebuild failed!")