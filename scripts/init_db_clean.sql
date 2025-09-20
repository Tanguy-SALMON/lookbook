-- Clean database initialization script
-- This script creates a fresh database with optimized schema

-- Drop existing tables if they exist
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS outfits;
DROP TABLE IF EXISTS outfit_items;
DROP TABLE IF EXISTS rules;

-- Create products table with optimized schema
CREATE TABLE products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sku TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    price REAL NOT NULL,
    size_range TEXT DEFAULT '[]',  -- JSON array as text
    image_key TEXT NOT NULL,
    attributes TEXT DEFAULT '{}',  -- JSON object as text
    in_stock INTEGER DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,

    -- Individual attribute columns for better performance
    season TEXT,
    url_key TEXT UNIQUE,
    product_created_at TEXT,
    stock_qty INTEGER DEFAULT 0,
    category TEXT,
    color TEXT,
    material TEXT,
    pattern TEXT,
    occasion TEXT
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
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    intent_tags TEXT DEFAULT '{}',  -- JSON object as text
    rationale TEXT,
    score REAL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Create outfit_items table
CREATE TABLE outfit_items (
    outfit_id INTEGER NOT NULL,
    item_id INTEGER NOT NULL,
    role TEXT NOT NULL,
    PRIMARY KEY (outfit_id, item_id),
    FOREIGN KEY (outfit_id) REFERENCES outfits(id),
    FOREIGN KEY (item_id) REFERENCES products(id)
);

-- Create rules table
CREATE TABLE rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    intent TEXT NOT NULL,
    constraints TEXT DEFAULT '{}',  -- JSON object as text
    priority INTEGER DEFAULT 1,
    is_active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for rules
CREATE INDEX idx_rules_priority ON rules(priority);
CREATE INDEX idx_rules_intent ON rules(intent);
CREATE INDEX idx_rules_is_active ON rules(is_active);

