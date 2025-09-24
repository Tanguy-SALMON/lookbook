-- Lookbook tables for Akeneo integration
-- Database: lookbookMPC

-- Lookbooks table
CREATE TABLE lookbooks (
    id VARCHAR(36) PRIMARY KEY,
    slug VARCHAR(255) UNIQUE NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    cover_image_key VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    akeneo_lookbook_id VARCHAR(255),
    akeneo_score DECIMAL(5,2),
    akeneo_last_update DATETIME,
    akeneo_sync_status ENUM('never','linked','pending','exported','failed') DEFAULT 'never',
    akeneo_last_error TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Indexes for lookbooks
CREATE INDEX idx_lookbooks_slug ON lookbooks(slug);
CREATE INDEX idx_lookbooks_akeneo_sync_status ON lookbooks(akeneo_sync_status);
CREATE INDEX idx_lookbooks_created_at ON lookbooks(created_at);

-- Lookbook products table (junction table)
CREATE TABLE lookbook_products (
    lookbook_id VARCHAR(36) NOT NULL,
    product_sku VARCHAR(255) NOT NULL,
    position INT DEFAULT 0,
    note TEXT,
    PRIMARY KEY (lookbook_id, product_sku),
    FOREIGN KEY (lookbook_id) REFERENCES lookbooks(id) ON DELETE CASCADE
);

-- Indexes for lookbook_products
CREATE INDEX idx_lookbook_products_product_sku ON lookbook_products(product_sku);
CREATE INDEX idx_lookbook_products_position ON lookbook_products(position);