-- Product Import Tables Migration for MySQL
-- Adds tables for managing product import jobs and metadata

-- Create product_import_jobs table
CREATE TABLE IF NOT EXISTS product_import_jobs (
    id VARCHAR(36) PRIMARY KEY,  -- UUID as VARCHAR
    status ENUM('queued', 'running', 'completed', 'failed') NOT NULL,
    params JSON NOT NULL,
    metrics JSON DEFAULT ('{}'),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP NULL,
    finished_at TIMESTAMP NULL,
    error_message TEXT
);

-- Create indexes for product_import_jobs
CREATE INDEX idx_product_import_jobs_status ON product_import_jobs(status);
CREATE INDEX idx_product_import_jobs_created_at ON product_import_jobs(created_at);

-- Create product_import_meta table (key-value store)
CREATE TABLE IF NOT EXISTS product_import_meta (
    `key` VARCHAR(255) PRIMARY KEY,
    value TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Insert default value for last_successful_source_id if not exists
INSERT IGNORE INTO product_import_meta (`key`, value) VALUES ('last_successful_source_id', '0');