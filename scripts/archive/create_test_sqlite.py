#!/usr/bin/env python3
"""
Create simple SQLite database for tests

This script creates a minimal SQLite database with sample data
to satisfy the test requirements that expect a lookbook.db file.
"""

import sqlite3
from pathlib import Path


def create_test_database():
    """Create a simple SQLite database with sample data for tests."""

    # Database path (same as expected by tests)
    db_path = Path(__file__).parent / "lookbook.db"

    # Remove existing database if it exists
    if db_path.exists():
        db_path.unlink()

    # Create new database
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Create products table
    cursor.execute("""
        CREATE TABLE products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sku TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            price REAL NOT NULL,
            size_range TEXT,
            image_key TEXT,
            attributes TEXT,
            in_stock BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            category TEXT,
            color TEXT,
            material TEXT
        )
    """)

    # Create items table (alias for compatibility)
    cursor.execute("""
        CREATE VIEW items AS SELECT * FROM products
    """)

    # Create other required tables
    cursor.execute("""
        CREATE TABLE outfits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            total_price REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE outfit_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            outfit_id INTEGER,
            item_id INTEGER,
            FOREIGN KEY (outfit_id) REFERENCES outfits (id),
            FOREIGN KEY (item_id) REFERENCES products (id)
        )
    """)

    cursor.execute("""
        CREATE TABLE rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            conditions TEXT,
            actions TEXT
        )
    """)

    # Insert sample data
    sample_products = [
        (
            "SKU001",
            "Black T-Shirt",
            29.99,
            '["S", "M", "L"]',
            "tshirt_black.jpg",
            '{"color": "black", "style": "casual"}',
            1,
            "top",
            "black",
            "cotton",
        ),
        (
            "SKU002",
            "Blue Jeans",
            59.99,
            '["S", "M", "L", "XL"]',
            "jeans_blue.jpg",
            '{"color": "blue", "style": "casual"}',
            1,
            "bottom",
            "blue",
            "denim",
        ),
        (
            "SKU003",
            "Summer Dress",
            79.99,
            '["XS", "S", "M", "L"]',
            "dress_summer.jpg",
            '{"color": "white", "style": "elegant"}',
            1,
            "dress",
            "white",
            "cotton",
        ),
        (
            "SKU004",
            "Business Jacket",
            129.99,
            '["S", "M", "L", "XL"]',
            "jacket_business.jpg",
            '{"color": "navy", "style": "professional"}',
            1,
            "outerwear",
            "navy",
            "wool",
        ),
        (
            "SKU005",
            "Casual Sneakers",
            89.99,
            '["6", "7", "8", "9", "10"]',
            "sneakers_white.jpg",
            '{"color": "white", "style": "casual"}',
            1,
            "shoes",
            "white",
            "synthetic",
        ),
    ]

    cursor.executemany(
        """
        INSERT INTO products (sku, title, price, size_range, image_key, attributes, in_stock, category, color, material)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        sample_products,
    )

    # Insert sample outfit
    cursor.execute("""
        INSERT INTO outfits (title, total_price) VALUES ('Casual Day Out', 89.98)
    """)

    # Link outfit items
    cursor.execute("""
        INSERT INTO outfit_items (outfit_id, item_id) VALUES (1, 1), (1, 2)
    """)

    # Insert sample rule
    cursor.execute("""
        INSERT INTO rules (name, conditions, actions) VALUES ('Color Matching', 'color compatibility', 'suggest matching colors')
    """)

    # Commit and close
    conn.commit()
    conn.close()

    print(f"✅ Test SQLite database created at {db_path}")
    print(f"📊 Sample data: {len(sample_products)} products, 1 outfit, 1 rule")


if __name__ == "__main__":
    create_test_database()
