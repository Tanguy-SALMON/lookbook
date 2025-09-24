-- Akeneo integration tables
-- Database: lookbookMPC

-- Akeneo export jobs table
CREATE TABLE akeneo_export_jobs (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status ENUM('pending', 'running', 'completed', 'failed') DEFAULT 'pending',
    config JSON NOT NULL,  -- Export configuration
    lookbook_ids JSON,     -- Which lookbooks to export
    total_items INT DEFAULT 0,
    processed_items INT DEFAULT 0,
    errors JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP NULL,
    completed_at TIMESTAMP NULL,
    created_by VARCHAR(100) DEFAULT 'system'
);

-- Indexes for akeneo_export_jobs
CREATE INDEX idx_akeneo_export_jobs_status ON akeneo_export_jobs(status);
CREATE INDEX idx_akeneo_export_jobs_created_at ON akeneo_export_jobs(created_at);

-- Akeneo connection settings table
CREATE TABLE akeneo_settings (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    base_url VARCHAR(500) NOT NULL,
    client_id VARCHAR(255),
    client_secret VARCHAR(500),
    username VARCHAR(100),
    password_hash VARCHAR(500),  -- Encrypted
    is_active BOOLEAN DEFAULT FALSE,
    is_default BOOLEAN DEFAULT FALSE,
    connection_timeout INT DEFAULT 30,
    retry_attempts INT DEFAULT 3,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_tested_at TIMESTAMP NULL,
    last_test_result ENUM('success', 'failed', 'untested') DEFAULT 'untested'
);

-- Indexes for akeneo_settings
CREATE INDEX idx_akeneo_settings_is_active ON akeneo_settings(is_active);
CREATE INDEX idx_akeneo_settings_is_default ON akeneo_settings(is_default);

-- Akeneo attribute mappings table
CREATE TABLE akeneo_attribute_mappings (
    id VARCHAR(36) PRIMARY KEY,
    setting_id VARCHAR(36) NOT NULL,
    local_field VARCHAR(100) NOT NULL,
    akeneo_attribute VARCHAR(100) NOT NULL,
    akeneo_type VARCHAR(50) DEFAULT 'text',
    is_required BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (setting_id) REFERENCES akeneo_settings(id) ON DELETE CASCADE
);

-- Indexes for akeneo_attribute_mappings
CREATE INDEX idx_akeneo_mappings_setting_id ON akeneo_attribute_mappings(setting_id);
CREATE INDEX idx_akeneo_mappings_local_field ON akeneo_attribute_mappings(local_field);