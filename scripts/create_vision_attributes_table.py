#!/usr/bin/env python3
"""
Create Vision Attributes Table Migration

This script creates a proper normalized database structure for storing
vision analysis attributes in a separate table with foreign key relationship.
"""

import asyncio
import sys
import os
import logging
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lookbook_mpc.adapters.db_lookbook import MySQLLookbookRepository
from lookbook_mpc.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def create_vision_attributes_table():
    """Create the product_vision_attributes table with proper foreign key relationship."""

    create_table_sql = """
    CREATE TABLE IF NOT EXISTS product_vision_attributes (
        id INT AUTO_INCREMENT PRIMARY KEY,
        sku VARCHAR(100) NOT NULL,

        -- Vision Analysis Results
        color VARCHAR(100) DEFAULT NULL COMMENT 'Detected primary color',
        secondary_color VARCHAR(100) DEFAULT NULL COMMENT 'Detected secondary color',
        category VARCHAR(100) DEFAULT NULL COMMENT 'Detected product category',
        material VARCHAR(100) DEFAULT NULL COMMENT 'Detected primary material',
        secondary_material VARCHAR(100) DEFAULT NULL COMMENT 'Detected secondary material',
        pattern VARCHAR(100) DEFAULT NULL COMMENT 'Detected pattern type',
        fit VARCHAR(50) DEFAULT NULL COMMENT 'Detected fit type (slim, regular, oversized, etc.)',
        season VARCHAR(50) DEFAULT NULL COMMENT 'Suitable season',
        occasion VARCHAR(100) DEFAULT NULL COMMENT 'Suitable occasion',
        style VARCHAR(100) DEFAULT NULL COMMENT 'Style classification',

        -- Additional Vision Attributes
        sleeve_length VARCHAR(50) DEFAULT NULL COMMENT 'Sleeve length (short, long, sleeveless, etc.)',
        neckline VARCHAR(50) DEFAULT NULL COMMENT 'Neckline type (crew, v-neck, turtleneck, etc.)',
        closure VARCHAR(50) DEFAULT NULL COMMENT 'Closure type (button, zip, pullover, etc.)',
        length VARCHAR(50) DEFAULT NULL COMMENT 'Garment length (mini, midi, maxi, etc.)',

        -- Style Descriptors
        plus_size BOOLEAN DEFAULT FALSE COMMENT 'Plus size indicator',
        sustainable BOOLEAN DEFAULT FALSE COMMENT 'Sustainable/eco-friendly indicator',
        formal_level ENUM('casual', 'smart_casual', 'business', 'formal', 'black_tie') DEFAULT 'casual',
        versatility_score TINYINT DEFAULT 5 COMMENT 'Versatility rating 1-10',

        -- AI Analysis Metadata
        vision_provider VARCHAR(50) DEFAULT 'mock' COMMENT 'Vision analysis provider used',
        confidence_score DECIMAL(3,2) DEFAULT 0.85 COMMENT 'Analysis confidence (0.00-1.00)',
        model_version VARCHAR(50) DEFAULT NULL COMMENT 'AI model version used',
        analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'When analysis was performed',

        -- Human-readable Description
        description TEXT DEFAULT NULL COMMENT 'Human-readable product description',
        styling_tips TEXT DEFAULT NULL COMMENT 'Styling suggestions',
        care_instructions TEXT DEFAULT NULL COMMENT 'Care and maintenance tips',

        -- Metadata
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

        -- Foreign Key Constraint
        FOREIGN KEY (sku) REFERENCES products(sku) ON DELETE CASCADE ON UPDATE CASCADE,

        -- Indexes for Performance
        INDEX idx_sku (sku),
        INDEX idx_color (color),
        INDEX idx_category (category),
        INDEX idx_material (material),
        INDEX idx_season (season),
        INDEX idx_occasion (occasion),
        INDEX idx_style (style),
        INDEX idx_formal_level (formal_level),
        INDEX idx_analysis_date (analysis_date),

        -- Composite Indexes for Common Queries
        INDEX idx_color_season (color, season),
        INDEX idx_category_occasion (category, occasion),
        INDEX idx_material_style (material, style),

        -- Unique Constraint (one vision analysis per product for now)
        UNIQUE KEY unique_sku_analysis (sku)

    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    COMMENT='Vision analysis attributes for products with AI-generated fashion metadata';
    """

    try:
        logger.info("Creating product_vision_attributes table...")
        repo = MySQLLookbookRepository(database_url=settings.lookbook_db_url)
        connection = await repo._get_connection()

        async with connection.cursor() as cursor:
            # Create the table
            await cursor.execute(create_table_sql)
            logger.info("✅ product_vision_attributes table created successfully")

            # Verify table creation
            await cursor.execute("SHOW TABLES LIKE 'product_vision_attributes';")
            result = await cursor.fetchone()
            if result:
                logger.info("✅ Table verification successful")

                # Show table structure
                await cursor.execute("DESCRIBE product_vision_attributes;")
                columns = await cursor.fetchall()
                logger.info("📋 Table structure:")
                for col in columns:
                    logger.info(f"   {col[0]:25} {col[1]:20} {col[2]:5} {col[3]:5}")

                return True
            else:
                logger.error("❌ Table creation verification failed")
                return False

    except Exception as e:
        logger.error(f"❌ Error creating vision attributes table: {e}")
        return False
    finally:
        if "connection" in locals():
            await connection.ensure_closed()


async def migrate_existing_data():
    """Migrate existing vision data from products table to product_vision_attributes table."""

    migration_sql = """
    INSERT INTO product_vision_attributes (
        sku, color, category, material, pattern, season, occasion,
        description, vision_provider, analysis_date
    )
    SELECT
        sku,
        color,
        category,
        material,
        pattern,
        season,
        occasion,
        CONCAT('AI-analyzed ', title, ' with ', COALESCE(color, 'neutral'), ' color and ', COALESCE(material, 'quality'), ' material construction.') as description,
        'mock'