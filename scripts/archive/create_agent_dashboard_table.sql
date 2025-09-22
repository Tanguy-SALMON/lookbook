-- Create agent_dashboard table for agent management
-- This table stores agent dashboard configurations and metrics

SET FOREIGN_KEY_CHECKS = 0;

-- Drop existing table if it exists
DROP TABLE IF EXISTS agent_dashboard;

-- Create agent_dashboard table
CREATE TABLE agent_dashboard (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'active',
    metrics JSON,
    config JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    -- Agent performance metrics
    total_sessions INT DEFAULT 0,
    successful_sessions INT DEFAULT 0,
    average_response_time DECIMAL(8,2) DEFAULT 0.00,
    success_rate DECIMAL(5,2) DEFAULT 0.00,

    -- Agent configuration
    model_name VARCHAR(100),
    temperature DECIMAL(3,2) DEFAULT 0.7,
    max_tokens INT DEFAULT 1000,
    system_prompt TEXT,

    -- Agent capabilities
    capabilities JSON DEFAULT '[]',
    supported_intents JSON DEFAULT '[]',

    -- Agent visibility and access
    is_visible TINYINT(1) DEFAULT 1,
    access_level VARCHAR(20) DEFAULT 'admin',

    -- Agent metadata
    version VARCHAR(20) DEFAULT '1.0.0',
    author VARCHAR(100),
    tags JSON DEFAULT '[]'
);

-- Create indexes for performance
CREATE INDEX idx_agent_dashboard_name ON agent_dashboard(name);
CREATE INDEX idx_agent_dashboard_status ON agent_dashboard(status);
CREATE INDEX idx_agent_dashboard_is_visible ON agent_dashboard(is_visible);
CREATE INDEX idx_agent_dashboard_created_at ON agent_dashboard(created_at);

SET FOREIGN_KEY_CHECKS = 1;

-- Insert sample data
INSERT INTO agent_dashboard (name, description, status, metrics, config, total_sessions, successful_sessions, average_response_time, success_rate, model_name, temperature, max_tokens, system_prompt, capabilities, supported_intents, is_visible, access_level, version, author, tags) VALUES
('Fashion Recommender', 'AI-powered fashion recommendation agent', 'active', '{"total_recommendations": 1250, "user_satisfaction": 4.2, "conversion_rate": 0.15}', '{"max_recommendations": 5, "confidence_threshold": 0.7}', 1250, 1180, 1.25, 0.94, 'qwen3', 0.3, 1000, 'You are a fashion expert helping users find the perfect outfits based on their preferences and needs.', '["recommendation", "styling", "outfit_planning"]', '["casual", "business", "party", "beach", "sport"]', 1, 'admin', '1.0.0', 'AI Team', '["fashion", "recommendation", "styling"]'),
('Chat Assistant', 'Customer service chatbot for fashion inquiries', 'active', '{"total_chats": 3200, "resolution_rate": 0.78, "avg_session_duration": 180}', '{"auto_response": true, "escalation_threshold": 3}', 3200, 2500, 2.1, 0.78, 'qwen3', 0.5, 1500, 'You are a helpful customer service assistant for a fashion retailer. Provide friendly and accurate information about products, orders, and services.', '["customer_service", "inquiry", "support"]', '["product_info", "order_status", "shipping", "returns", "general"]', 1, 'admin', '1.0.0', 'AI Team', '["customer_service", "chat", "support"]'),
('Style Analyzer', 'Vision-based style analysis agent', 'active', '{"total_analyses": 850, "accuracy": 0.89, "processing_time": 3.2}', '{"enable_vision": true, "confidence_threshold": 0.6}', 850, 760, 3.2, 0.89, 'qwen2.5-vl', 0.2, 800, 'You are a style analysis expert. Analyze fashion images to identify style attributes, colors, patterns, and provide style recommendations.', '["vision_analysis", "style_detection", "attribute_extraction"]', '["style_analysis", "color_analysis", "pattern_detection", "occasion_detection"]', 1, 'admin', '1.0.0', 'AI Team', '["vision", "style", "analysis"]');

-- Grant privileges (run this separately with appropriate user)
-- GRANT ALL PRIVILEGES ON lookbookMPC.* TO 'lookbook_user'@'%' IDENTIFIED BY 'your_password';
-- FLUSH PRIVILEGES;