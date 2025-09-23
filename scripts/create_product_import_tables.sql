-- Product Import Tables Migration
-- Adds tables for managing product import jobs and metadata

-- Create product_import_jobs table
CREATE TABLE IF NOT EXISTS product_import_jobs (
    id TEXT PRIMARY KEY,  -- UUID as TEXT
    status TEXT NOT NULL CHECK (status IN ('queued', 'running', 'completed', 'failed')),
    params TEXT NOT NULL,  -- JSON as TEXT
    metrics TEXT DEFAULT '{}',  -- JSON as TEXT
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    started_at TEXT,
    finished_at TEXT,
    error_message TEXT
);

-- Create indexes for product_import_jobs
CREATE INDEX IF NOT EXISTS idx_product_import_jobs_status ON product_import_jobs(status);
CREATE INDEX IF NOT EXISTS idx_product_import_jobs_created_at ON product_import_jobs(created_at);

-- Create product_import_meta table (key-value store)
CREATE TABLE IF NOT EXISTS product_import_meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Insert default value for last_successful_source_id if not exists
INSERT OR IGNORE INTO product_import_meta (key, value) VALUES ('last_successful_source_id', '0');