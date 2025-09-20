#!/usr/bin/env python3
"""
MySQL Database Initialization Script

This script initializes the lookbook MySQL database with all required tables.
It uses the MYSQL_APP_URL environment variable to connect to the database.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lookbook_mpc.config import settings
import aiomysql
from urllib.parse import urlparse


async def create_tables():
    """Create all required tables for the lookbook application."""

    # SQL script to create tables
    create_tables_sql = """
    -- MySQL database initialization script for lookbook-MPC
    -- This script creates a fresh database with optimized schema

    SET FOREIGN_KEY_CHECKS = 0;

    -- Drop existing tables if they exist
    DROP TABLE IF EXISTS outfit_items;
    DROP TABLE IF EXISTS outfits;
    DROP TABLE IF EXISTS rules;
    DROP TABLE IF EXISTS products;

    -- Create products table with optimized schema
    CREATE TABLE products (
        id INT AUTO_INCREMENT PRIMARY KEY,
        sku VARCHAR(100) NOT NULL UNIQUE,
        title VARCHAR(500) NOT NULL,
        price DECIMAL(10,2) NOT NULL,
        size_range JSON,
        image_key VARCHAR(255) NOT NULL,
        in_stock TINYINT(1) DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

        -- Individual attribute columns for better performance
        season VARCHAR(50),
        url_key VARCHAR(255) UNIQUE,
        product_created_at TIMESTAMP,
        stock_qty INT DEFAULT 0,
        category VARCHAR(100),
        color VARCHAR(100),
        material VARCHAR(100),
        pattern VARCHAR(100),
        occasion VARCHAR(100)
    );

    -- Create indexes for performance
    CREATE INDEX idx_products_sku ON products(sku);
    CREATE INDEX idx_products_price ON products(price);
    CREATE INDEX idx_products_in_stock ON products(in_stock);
    CREATE INDEX idx_products_category ON products(category);
    CREATE INDEX idx_products_color ON products(color);
    CREATE INDEX idx_products_material ON products(material);
    CREATE INDEX idx_products_season ON products(season);
    CREATE INDEX idx_products_occasion ON products(occasion);
    CREATE INDEX idx_products_url_key ON products(url_key);

    -- Create outfits table
    CREATE TABLE outfits (
        id INT AUTO_INCREMENT PRIMARY KEY,
        title VARCHAR(255) NOT NULL,
        intent_tags JSON,
        rationale TEXT,
        score DECIMAL(5,4),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- Create outfit_items table
    CREATE TABLE outfit_items (
        outfit_id INT NOT NULL,
        item_id INT NOT NULL,
        role VARCHAR(50) NOT NULL,
        PRIMARY KEY (outfit_id, item_id),
        FOREIGN KEY (outfit_id) REFERENCES outfits(id) ON DELETE CASCADE,
        FOREIGN KEY (item_id) REFERENCES products(id) ON DELETE CASCADE
    );

    -- Create rules table
    CREATE TABLE rules (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        intent VARCHAR(100) NOT NULL,
        constraints JSON,
        priority INT DEFAULT 1,
        is_active TINYINT(1) DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- Create indexes for rules
    CREATE INDEX idx_rules_priority ON rules(priority);
    CREATE INDEX idx_rules_intent ON rules(intent);
    CREATE INDEX idx_rules_is_active ON rules(is_active);

    SET FOREIGN_KEY_CHECKS = 1;
    """

    try:
        print("=== MySQL Database Initialization ===")
        print(f"Database URL: {settings.lookbook_db_url}")

        # Parse the database URL
        parsed_url = urlparse(settings.lookbook_db_url)

        # Connect to MySQL database
        conn = await aiomysql.connect(
            host=parsed_url.hostname,
            port=parsed_url.port or 3306,
            user=parsed_url.username,
            password="Magento@COS(*)",  # Direct password to avoid URL parsing issues
            db=parsed_url.path[1:],  # Remove leading slash
            autocommit=True,
        )

        print(f"✅ Connected to database: {parsed_url.path[1:]}")

        # Execute the SQL script
        cursor = await conn.cursor()

        # Split the SQL script into individual statements
        statements = [
            stmt.strip() for stmt in create_tables_sql.split(";") if stmt.strip()
        ]

        for statement in statements:
            if statement.upper().startswith(("CREATE", "DROP", "SET")):
                print(f"Executing: {statement[:50]}...")
                await cursor.execute(statement)

        # Verify tables were created
        await cursor.execute("SHOW TABLES")
        tables = await cursor.fetchall()
        table_names = [table[0] for table in tables]

        print(f"✅ Tables created successfully: {', '.join(table_names)}")

        # Show table structures
        for table_name in table_names:
            await cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = await cursor.fetchone()
            print(f"   {table_name}: {count[0]} rows")

        await cursor.close()
        conn.close()

        print("\n🎉 Database initialization completed successfully!")
        print("\n💡 Next steps:")
        print("   1. Run product sync: poetry run python scripts/sync_100_products.py")
        print("   2. Test the API: poetry run python main.py")

        return True

    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False


async def verify_connection():
    """Verify database connection before initialization."""
    try:
        if not settings.lookbook_db_url:
            print("❌ MYSQL_APP_URL is not configured in .env file")
            return False

        parsed_url = urlparse(settings.lookbook_db_url)

        conn = await aiomysql.connect(
            host=parsed_url.hostname,
            port=parsed_url.port or 3306,
            user=parsed_url.username,
            password="Magento@COS(*)",
            db=parsed_url.path[1:],
            autocommit=True,
        )

        cursor = await conn.cursor()
        await cursor.execute("SELECT 1")
        await cursor.close()
        conn.close()

        return True

    except Exception as e:
        print(f"❌ Cannot connect to database: {e}")
        print("\n💡 Make sure:")
        print("   1. MySQL server is running")
        print("   2. Database 'lookbookMPC' exists")
        print("   3. User 'magento' has access to the database")
        print("   4. MYSQL_APP_URL is correctly set in .env file")
        return False


async def main():
    """Main function."""
    print("🔧 MySQL Database Initialization Script")
    print("=" * 50)

    # Check environment configuration
    print("📋 Configuration Check:")
    print(f"   Lookbook DB URL: {settings.lookbook_db_url}")
    print(f"   Shop DB URL: {settings.mysql_shop_url}")

    # Verify connection first
    if not await verify_connection():
        sys.exit(1)

    # Initialize tables
    success = await create_tables()

    if not success:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
