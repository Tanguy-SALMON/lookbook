#!/usr/bin/env python3
"""
Script to create agent_dashboard table in the database
"""

import sys
import os
import structlog
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from lookbook_mpc.adapters.database import DatabaseManager

logger = structlog.get_logger()

def create_agent_dashboard_table():
    """Create the agent_dashboard table in the database"""
    try:
        db = ChatLogger()

        # SQL to create agent_dashboard table
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS agent_dashboard (
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
        """

        # Create indexes
        create_indexes_sql = """
        CREATE INDEX IF NOT EXISTS idx_agent_dashboard_name ON agent_dashboard(name);
        CREATE INDEX IF NOT EXISTS idx_agent_dashboard_status ON agent_dashboard(status);
        CREATE INDEX IF NOT EXISTS idx_agent_dashboard_is_visible ON agent_dashboard(is_visible);
        CREATE INDEX IF NOT EXISTS idx_agent_dashboard_created_at ON agent_dashboard(created_at);
        """

        logger.info("Creating agent_dashboard table...")

        # Execute table creation
        db.execute_raw_sql(create_table_sql)

        # Execute index creation
        for index_sql in create_indexes_sql.strip().split(';'):
            if index_sql.strip():
                db.execute_raw_sql(index_sql.strip() + ';')

        logger.info("Agent dashboard table created successfully")

        # Insert sample data
        sample_agents = [
            {
                'name': 'Fashion Recommender',
                'description': 'AI-powered fashion recommendation agent',
                'status': 'active',
                'metrics': '{"total_recommendations": 1250, "user_satisfaction": 4.2, "conversion_rate": 0.15}',
                'config': '{"max_recommendations": 5, "confidence_threshold": 0.7}',
                'total_sessions': 1250,
                'successful_sessions': 1180,
                'average_response_time': 1.25,
                'success_rate': 0.94,
                'model_name': 'qwen3',
                'temperature': 0.3,
                'max_tokens': 1000,
                'system_prompt': 'You are a fashion expert helping users find the perfect outfits based on their preferences and needs.',
                'capabilities': '["recommendation", "styling", "outfit_planning"]',
                'supported_intents': '["casual", "business", "party", "beach", "sport"]',
                'is_visible': 1,
                'access_level': 'admin',
                'version': '1.0.0',
                'author': 'AI Team',
                'tags': '["fashion", "recommendation", "styling"]'
            },
            {
                'name': 'Chat Assistant',
                'description': 'Customer service chatbot for fashion inquiries',
                'status': 'active',
                'metrics': '{"total_chats": 3200, "resolution_rate": 0.78, "avg_session_duration": 180}',
                'config': '{"auto_response": true, "escalation_threshold": 3}',
                'total_sessions': 3200,
                'successful_sessions': 2500,
                'average_response_time': 2.1,
                'success_rate': 0.78,
                'model_name': 'qwen3',
                'temperature': 0.5,
                'max_tokens': 1500,
                'system_prompt': 'You are a helpful customer service assistant for a fashion retailer. Provide friendly and accurate information about products, orders, and services.',
                'capabilities': '["customer_service", "inquiry", "support"]',
                'supported_intents': '["product_info", "order_status", "shipping", "returns", "general"]',
                'is_visible': 1,
                'access_level': 'admin',
                'version': '1.0.0',
                'author': 'AI Team',
                'tags': '["customer_service", "chat", "support"]'
            },
            {
                'name': 'Style Analyzer',
                'description': 'Vision-based style analysis agent',
                'status': 'active',
                'metrics': '{"total_analyses": 850, "accuracy": 0.89, "processing_time": 3.2}',
                'config': '{"enable_vision": true, "confidence_threshold": 0.6}',
                'total_sessions': 850,
                'successful_sessions': 760,
                'average_response_time': 3.2,
                'success_rate': 0.89,
                'model_name': 'qwen2.5-vl',
                'temperature': 0.2,
                'max_tokens': 800,
                'system_prompt': 'You are a style analysis expert. Analyze fashion images to identify style attributes, colors, patterns, and provide style recommendations.',
                'capabilities': '["vision_analysis", "style_detection", "attribute_extraction"]',
                'supported_intents': '["style_analysis", "color_analysis", "pattern_detection", "occasion_detection"]',
                'is_visible': 1,
                'access_level': 'admin',
                'version': '1.0.0',
                'author': 'AI Team',
                'tags': '["vision", "style", "analysis"]'
            }
        ]

        logger.info("Inserting sample agent dashboard data...")

        for agent in sample_agents:
            # Check if agent already exists
            existing = db.execute_query(
                "SELECT id FROM agent_dashboard WHERE name = %s",
                (agent['name'],)
            )

            if not existing:
                # Insert agent
                columns = ', '.join(agent.keys())
                placeholders = ', '.join(['%s'] * len(agent))
                values = list(agent.values())

                insert_sql = f"""
                INSERT INTO agent_dashboard ({columns})
                VALUES ({placeholders})
                """

                db.execute_raw_sql(insert_sql, values)
                logger.info(f"Inserted agent: {agent['name']}")
            else:
                logger.info(f"Agent already exists: {agent['name']}")

        logger.info("Agent dashboard table setup completed successfully")

    except Exception as e:
        logger.error("Error creating agent dashboard table", error=str(e))
        raise

if __name__ == "__main__":
    create_agent_dashboard_table()