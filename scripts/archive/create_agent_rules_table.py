#!/usr/bin/env python3
"""
Script to create agent_rules table in the database
"""

import sys
import os
import structlog
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from lookbook_mpc.services.database import DatabaseService

logger = structlog.get_logger()

def create_agent_rules_table():
    """Create the agent_rules table in the database"""
    try:
        db = DatabaseService()

        # SQL to create agent_rules table
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS agent_rules (
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
            tags JSON DEFAULT '[]'
        );
        """

        # Create indexes
        create_indexes_sql = """
        CREATE INDEX IF NOT EXISTS idx_agent_rules_agent_id ON agent_rules(agent_id);
        CREATE INDEX IF NOT EXISTS idx_agent_rules_name ON agent_rules(name);
        CREATE INDEX IF NOT EXISTS idx_agent_rules_rule_type ON agent_rules(rule_type);
        CREATE INDEX IF NOT EXISTS idx_agent_rules_priority ON agent_rules(priority);
        CREATE INDEX IF NOT EXISTS idx_agent_rules_is_active ON agent_rules(is_active);
        CREATE INDEX IF NOT EXISTS idx_agent_rules_execution_order ON agent_rules(execution_order);
        CREATE INDEX IF NOT EXISTS idx_agent_rules_scope ON agent_rules(scope);
        CREATE INDEX IF NOT EXISTS idx_agent_rules_created_at ON agent_rules(created_at);
        """

        logger.info("Creating agent_rules table...")

        # Execute table creation
        db.execute_raw_sql(create_table_sql)

        # Execute index creation
        for index_sql in create_indexes_sql.strip().split(';'):
            if index_sql.strip():
                db.execute_raw_sql(index_sql.strip() + ';')

        logger.info("Agent rules table created successfully")

        # Get agent IDs for sample data
        agents = db.execute_query("SELECT id, name FROM agent_dashboard")
        agent_map = {agent['name']: agent['id'] for agent in agents}

        if not agent_map:
            logger.warning("No agents found. Please run create_agent_dashboard_table.py first.")
            return

        # Insert sample data
        sample_rules = [
            {
                'agent_id': agent_map['Fashion Recommender'],
                'name': 'Budget Constraint Rule',
                'rule_type': 'filter',
                'conditions': '{"max_budget": {"$exists": true, "$gt": 0}}',
                'actions': '{"filter": {"price": {"$lte": "$max_budget"}}}',
                'priority': 1,
                'is_active': 1,
                'description': 'Filter products based on user budget constraints',
                'author': 'AI Team',
                'version': '1.0.0',
                'execution_order': 1,
                'timeout_seconds': 10,
                'target_agents': '[1]',
                'target_intents': '["casual", "business", "party"]',
                'test_cases': '[{"input": {"max_budget": 100}, "expected": "products under $100"}]',
                'validation_rules': '["budget_validation"]',
                'is_editable': 1,
                'access_level': 'admin',
                'tags': '["budget", "filter", "constraint"]'
            },
            {
                'agent_id': agent_map['Fashion Recommender'],
                'name': 'Seasonal Recommendations',
                'rule_type': 'recommendation',
                'conditions': '{"season": {"$exists": true}}',
                'actions': '{"recommend": {"seasonal_items": true, "seasonal_boost": 0.3}}',
                'priority': 2,
                'is_active': 1,
                'description': 'Boost seasonal relevance in recommendations',
                'author': 'AI Team',
                'version': '1.0.0',
                'execution_order': 2,
                'timeout_seconds': 15,
                'target_agents': '[1]',
                'target_intents': '["casual", "beach", "sport"]',
                'test_cases': '[{"input": {"season": "summer"}, "expected": "summer items boosted"}]',
                'validation_rules': '["seasonal_validation"]',
                'is_editable': 1,
                'access_level': 'admin',
                'tags': '["seasonal", "recommendation", "boost"]'
            },
            {
                'agent_id': agent_map['Fashion Recommender'],
                'name': 'Size Availability Check',
                'rule_type': 'validation',
                'conditions': '{"size": {"$exists": true}}',
                'actions': '{"validate": {"size_available": true, "alternative_sizes": true}}',
                'priority': 3,
                'is_active': 1,
                'description': 'Validate size availability and suggest alternatives',
                'author': 'AI Team',
                'version': '1.0.0',
                'execution_order': 3,
                'timeout_seconds': 8,
                'target_agents': '[1]',
                'target_intents': '["casual", "business", "party"]',
                'test_cases': '[{"input": {"size": "M"}, "expected": "check size M availability"}]',
                'validation_rules': '["size_validation"]',
                'is_editable': 1,
                'access_level': 'admin',
                'tags': '["size", "validation", "availability"]'
            },
            {
                'agent_id': agent_map['Chat Assistant'],
                'name': 'Escalation Rule',
                'rule_type': 'workflow',
                'conditions': '{"intent": "complaint", "sentiment": {"$lt": 0.3}}',
                'actions': '{"escalate": {"level": "supervisor", "timeout": 300}}',
                'priority': 1,
                'is_active': 1,
                'description': 'Escalate negative sentiment complaints to supervisor',
                'author': 'AI Team',
                'version': '1.0.0',
                'execution_order': 1,
                'timeout_seconds': 30,
                'target_agents': '[2]',
                'target_intents': '["complaint", "support"]',
                'test_cases': '[{"input": {"intent": "complaint", "sentiment": 0.2}, "expected": "escalate to supervisor"}]',
                'validation_rules': '["escalation_validation"]',
                'is_editable': 1,
                'access_level': 'admin',
                'tags': '["escalation", "workflow", "sentiment"]'
            },
            {
                'agent_id': agent_map['Chat Assistant'],
                'name': 'Auto-Response Rule',
                'rule_type': 'response',
                'conditions': '{"query_type": {"$in": ["faq", "general"]}}',
                'actions': '{"auto_reply": {"template": "faq_response", "confidence": 0.8}}',
                'priority': 2,
                'is_active': 1,
                'description': 'Auto-respond to FAQ and general queries',
                'author': 'AI Team',
                'version': '1.0.0',
                'execution_order': 2,
                'timeout_seconds': 5,
                'target_agents': '[2]',
                'target_intents': '["faq", "general"]',
                'test_cases': '[{"input": {"query_type": "faq"}, "expected": "auto-reply with FAQ template"}]',
                'validation_rules': '["auto_response_validation"]',
                'is_editable': 1,
                'access_level': 'admin',
                'tags': '["auto_response", "faq", "efficiency"]'
            },
            {
                'agent_id': agent_map['Style Analyzer'],
                'name': 'Color Analysis Rule',
                'rule_type': 'vision',
                'conditions': '{"image_features": {"$exists": true}}',
                'actions': '{"extract": {"dominant_colors": true, "color_palette": true}}',
                'priority': 1,
                'is_active': 1,
                'description': 'Extract dominant colors and color palette from images',
                'author': 'AI Team',
                'version': '1.0.0',
                'execution_order': 1,
                'timeout_seconds': 20,
                'target_agents': '[3]',
                'target_intents': '["style_analysis", "color_analysis"]',
                'test_cases': '[{"input": {"image_features": "color_data"}, "expected": "extract color palette"}]',
                'validation_rules': '["color_extraction_validation"]',
                'is_editable': 1,
                'access_level': 'admin',
                'tags': '["color", "vision", "analysis"]'
            },
            {
                'agent_id': agent_map['Style Analyzer'],
                'name': 'Pattern Detection Rule',
                'rule_type': 'vision',
                'conditions': '{"image_features": {"$exists": true}}',
                'actions': '{"detect": {"patterns": true, "confidence_threshold": 0.6}}',
                'priority': 2,
                'is_active': 1,
                'description': 'Detect patterns in fashion images',
                'author': 'AI Team',
                'version': '1.0.0',
                'execution_order': 2,
                'timeout_seconds': 25,
                'target_agents': '[3]',
                'target_intents': '["pattern_detection", "style_analysis"]',
                'test_cases': '[{"input": {"image_features": "pattern_data"}, "expected": "detect patterns"}]',
                'validation_rules': '["pattern_detection_validation"]',
                'is_editable': 1,
                'access_level': 'admin',
                'tags': '["pattern", "vision", "detection"]'
            }
        ]

        logger.info("Inserting sample agent rules data...")

        for rule in sample_rules:
            # Check if rule already exists
            existing = db.execute_query(
                "SELECT id FROM agent_rules WHERE name = %s AND agent_id = %s",
                (rule['name'], rule['agent_id'])
            )

            if not existing:
                # Insert rule
                columns = ', '.join(rule.keys())
                placeholders = ', '.join(['%s'] * len(rule))
                values = list(rule.values())

                insert_sql = f"""
                INSERT INTO agent_rules ({columns})
                VALUES ({placeholders})
                """

                db.execute_raw_sql(insert_sql, values)
                logger.info(f"Inserted rule: {rule['name']} for agent {rule['agent_id']}")
            else:
                logger.info(f"Rule already exists: {rule['name']} for agent {rule['agent_id']}")

        logger.info("Agent rules table setup completed successfully")

    except Exception as e:
        logger.error("Error creating agent rules table", error=str(e))
        raise

if __name__ == "__main__":
    create_agent_rules_table()