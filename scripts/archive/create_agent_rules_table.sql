-- Create agent_rules table for agent management
-- This table stores agent-specific rules and configurations

SET FOREIGN_KEY_CHECKS = 0;

-- Drop existing table if it exists
DROP TABLE IF EXISTS agent_rules;

-- Create agent_rules table
CREATE TABLE agent_rules (
    id INT AUTO_INCREMENT PRIMARY KEY,
    agent_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    rule_type VARCHAR(50) NOT NULL,
    conditions JSON,
    actions JSON,
    priority INT DEFAULT 1,
    is_active TINYINT(1) DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    -- Rule metadata
    description TEXT,
    author VARCHAR(100),
    version VARCHAR(20) DEFAULT '1.0.0',

    -- Rule execution settings
    execution_order INT DEFAULT 1,
    timeout_seconds INT DEFAULT 30,
    retry_count INT DEFAULT 0,
    retry_delay_seconds INT DEFAULT 5,

    -- Rule scope and targeting
    scope VARCHAR(50) DEFAULT 'global',
    target_agents JSON DEFAULT '[]',
    target_intents JSON DEFAULT '[]',
    target_users JSON DEFAULT '[]',

    -- Rule validation and testing
    test_cases JSON DEFAULT '[]',
    validation_rules JSON DEFAULT '[]',
    last_tested_at TIMESTAMP NULL,
    test_results JSON,

    -- Rule performance tracking
    execution_count INT DEFAULT 0,
    success_count INT DEFAULT 0,
    average_execution_time DECIMAL(8,2) DEFAULT 0.00,

    -- Rule dependencies and exclusions
    dependencies JSON DEFAULT '[]',
    exclusions JSON DEFAULT '[]',

    -- Rule visibility and access
    is_editable TINYINT(1) DEFAULT 1,
    access_level VARCHAR(20) DEFAULT 'admin',
    tags JSON DEFAULT '[]',

    -- Foreign key to agent_dashboard
    FOREIGN KEY (agent_id) REFERENCES agent_dashboard(id) ON DELETE CASCADE
);

-- Create indexes for performance
CREATE INDEX idx_agent_rules_agent_id ON agent_rules(agent_id);
CREATE INDEX idx_agent_rules_name ON agent_rules(name);
CREATE INDEX idx_agent_rules_rule_type ON agent_rules(rule_type);
CREATE INDEX idx_agent_rules_priority ON agent_rules(priority);
CREATE INDEX idx_agent_rules_is_active ON agent_rules(is_active);
CREATE INDEX idx_agent_rules_execution_order ON agent_rules(execution_order);
CREATE INDEX idx_agent_rules_scope ON agent_rules(scope);
CREATE INDEX idx_agent_rules_created_at ON agent_rules(created_at);

SET FOREIGN_KEY_CHECKS = 1;

-- Insert sample data
INSERT INTO agent_rules (agent_id, name, rule_type, conditions, actions, priority, is_active, description, author, version, execution_order, timeout_seconds, target_agents, target_intents, test_cases, validation_rules, is_editable, access_level, tags) VALUES
(1, 'Budget Constraint Rule', 'filter', '{"max_budget": {"$exists": true, "$gt": 0}}', {"filter": {"price": {"$lte": "$max_budget"}}}, 1, 1, 'Filter products based on user budget constraints', 'AI Team', '1.0.0', 1, 10, '[1]', '["casual", "business", "party"]', '[{"input": {"max_budget": 100}, "expected": "products under $100"}]', '["budget_validation"]', 1, 'admin', '["budget", "filter", "constraint"]'),
(1, 'Seasonal Recommendations', 'recommendation', '{"season": {"$exists": true}}', {"recommend": {"seasonal_items": true, "seasonal_boost": 0.3}}, 2, 1, 'Boost seasonal relevance in recommendations', 'AI Team', '1.0.0', 2, 15, '[1]', '["casual", "beach", "sport"]', '[{"input": {"season": "summer"}, "expected": "summer items boosted"}]', '["seasonal_validation"]', 1, 'admin', '["seasonal", "recommendation", "boost"]'),
(1, 'Size Availability Check', 'validation', '{"size": {"$exists": true}}', {"validate": {"size_available": true, "alternative_sizes": true}}, 3, 1, 'Validate size availability and suggest alternatives', 'AI Team', '1.0.0', 3, 8, '[1]', '["casual", "business", "party"]', '[{"input": {"size": "M"}, "expected": "check size M availability"}]', '["size_validation"]', 1, 'admin', '["size", "validation", "availability"]'),
(2, 'Escalation Rule', 'workflow', '{"intent": "complaint", "sentiment": {"$lt": 0.3}}', {"escalate": {"level": "supervisor", "timeout": 300}}, 1, 1, 'Escalate negative sentiment complaints to supervisor', 'AI Team', '1.0.0', 1, 30, '[2]', '["complaint", "support"]', '[{"input": {"intent": "complaint", "sentiment": 0.2}, "expected": "escalate to supervisor"}]', '["escalation_validation"]', 1, 'admin', '["escalation", "workflow", "sentiment"]'),
(2, 'Auto-Response Rule', 'response', {'"query_type": {"$in": ["faq", "general"]}'}, {"auto_reply": {"template": "faq_response", "confidence": 0.8}}, 2, 1, 'Auto-respond to FAQ and general queries', 'AI Team', '1.0.0', 2, 5, '[2]', '["faq", "general"]', '[{"input": {"query_type": "faq"}, "expected": "auto-reply with FAQ template"}]', '["auto_response_validation"]', 1, 'admin', '["auto_response", "faq", "efficiency"]'),
(3, 'Color Analysis Rule', 'vision', '{"image_features": {"$exists": true}}', {"extract": {"dominant_colors": true, "color_palette": true}}, 1, 1, 'Extract dominant colors and color palette from images', 'AI Team', '1.0.0', 1, 20, '[3]', '["style_analysis", "color_analysis"]', '[{"input": {"image_features": "color_data"}, "expected": "extract color palette"}]', '["color_extraction_validation"]', 1, 'admin', '["color", "vision", "analysis"]'),
(3, 'Pattern Detection Rule', 'vision', '{"image_features": {"$exists": true}}', {"detect": {"patterns": true, "confidence_threshold": 0.6}}, 2, 1, 'Detect patterns in fashion images', 'AI Team', '1.0.0', 2, 25, '[3]', '["pattern_detection", "style_analysis"]', '[{"input": {"image_features": "pattern_data"}, "expected": "detect patterns"}]', '["pattern_detection_validation"]', 1, 'admin', '["pattern", "vision", "detection"]');

-- Grant privileges (run this separately with appropriate user)
-- GRANT ALL PRIVILEGES ON lookbookMPC.* TO 'lookbook_user'@'%' IDENTIFIED BY 'your_password';
-- FLUSH PRIVILEGES;