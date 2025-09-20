#!/usr/bin/env python3
"""
Manual migration script to add product attributes columns
"""

import sqlite3
import json
import os
from datetime import datetime

def apply_migration():
    """Apply the migration to add product attributes columns"""
    db_path = "./lookbook.db"

    if not os.path.exists(db_path):
        print(f"Database file not found: {db_path}")
        return False

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check if table is named 'items' or 'products'
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='items'")
        items_exists = cursor.fetchone()

        if items_exists:
            # Rename table from 'items' to 'products'
            cursor.execute("ALTER TABLE items RENAME TO products")
            print("Renamed table 'items' to 'products'")

        # Add new columns
        columns_to_add = [
            "season TEXT",
            "url_key TEXT",
            "product_created_at TEXT",
            "stock_qty INTEGER DEFAULT 0",
            "category TEXT",
            "color TEXT",
            "material TEXT",
            "pattern TEXT",
            "occasion TEXT"
        ]

        for column in columns_to_add:
            try:
                cursor.execute(f"ALTER TABLE products ADD COLUMN {column}")
                print(f"Added column: {column}")
            except sqlite3.OperationalError as e:
                if "duplicate column name" not in str(e):
                    print(f"Error adding column {column}: {e}")

        # Create index for url_key
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS ix_products_url_key ON products(url_key)")
            print("Created index for url_key")
        except Exception as e:
            print(f"Error creating index: {e}")

        # Migrate data from JSON attributes to individual columns
        cursor.execute("SELECT id, attributes FROM products WHERE attributes IS NOT NULL")
        rows = cursor.fetchall()

        print(f"Migrating data for {len(rows)} products...")

        for row in rows:
            product_id, attributes_json = row

            try:
                if attributes_json:
                    attributes = json.loads(attributes_json)
                else:
                    attributes = {}
            except:
                attributes = {}

            # Update the product with the extracted attributes
            update_query = """
            UPDATE products SET
                season = ?,
                url_key = ?,
                product_created_at = ?,
                stock_qty = ?,
                category = ?,
                color = ?,
                material = ?,
                pattern = ?,
                occasion = ?
            WHERE id = ?
            """

            cursor.execute(update_query, (
                attributes.get('season'),
                attributes.get('url_key'),
                attributes.get('created_at'),
                attributes.get('stock_qty', 0),
                attributes.get('category'),
                attributes.get('color'),
                attributes.get('material'),
                attributes.get('pattern'),
                attributes.get('occasion'),
                product_id
            ))

        # Make url_key unique
        try:
            cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_products_url_key ON products(url_key)")
            print("Created unique constraint for url_key")
        except Exception as e:
            print(f"Error creating unique constraint: {e}")

        conn.commit()
        print("Migration completed successfully!")
        return True

    except Exception as e:
        print(f"Error during migration: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    print("=== Applying Database Migration ===")
    success = apply_migration()

    if success:
        print("\n=== Migration Summary ===")
        print("✅ Added product attributes columns")
        print("✅ Migrated data from JSON to individual columns")
        print("✅ Created indexes and constraints")
        print("\nNext steps:")
        print("1. Test the product sync script")
        print("2. Verify the database structure")
        print("3. Test recommendations with the updated schema")
    else:
        print("\n❌ Migration failed")