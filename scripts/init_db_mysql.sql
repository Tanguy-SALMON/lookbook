-- MySQL database initialization script for lookbook-MPC
-- This script creates a fresh database with optimized schema

SET FOREIGN_KEY_CHECKS = 0;

-- Drop existing tables if they exist
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS outfits;
DROP TABLE IF EXISTS outfit_items;
DROP TABLE IF EXISTS rules;

-- Create products table with optimized schema
CREATE TABLE products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sku VARCHAR(100) NOT NULL UNIQUE,
    title VARCHAR(500) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    size_range JSON,
    image_key VARCHAR(255) NOT NULL,
    attributes JSON,
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

-- Grant privileges (run this separately with appropriate user)
-- GRANT ALL PRIVILEGES ON lookbookMPC.* TO 'lookbook_user'@'%' IDENTIFIED BY 'your_password';
-- FLUSH PRIVILEGES;