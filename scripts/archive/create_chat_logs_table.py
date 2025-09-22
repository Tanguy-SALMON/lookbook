#!/usr/bin/env python3
"""
Create Chat Logs Table

This script creates a comprehensive chat logging table to track all chat interactions,
sessions, strategies, and performance metrics for the Lookbook-MPC system.
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import pymysql

# Add the project root to the path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from lookbook_mpc.config import settings


def create_chat_logs_table():
    """Create the chat_logs table with comprehensive logging capabilities."""

    # Use known connection parameters directly
    host = "127.0.0.1"
    port = 3306
    username = "magento"
    password = "Magento@COS(*)"
    database = "lookbookMPC"

    print(f"Connecting to MySQL: {host}:{port}/{database}")

    # Connect to MySQL
    connection = pymysql.connect(
        host=host,
        port=port,
        user=username,
        password=password,
        database=database,
        charset="utf8mb4",
    )

    try:
        with connection.cursor() as cursor:
            # Create chat_logs table
            create_chat_logs_sql = """
            CREATE TABLE IF NOT EXISTS chat_logs (
                id INT AUTO_INCREMENT PRIMARY KEY,

                -- Session Information
                session_id VARCHAR(255) NOT NULL,
                request_id VARCHAR(255) NOT NULL,

                -- User Message
                user_message TEXT NOT NULL,
                user_message_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                -- AI Response
                ai_response TEXT DEFAULT NULL,
                ai_response_type ENUM('greeting', 'recommendations', 'no_results', 'helpful_response', 'general', 'error') DEFAULT 'general',
                ai_response_timestamp TIMESTAMP NULL,

                -- Intent Analysis
                parsed_intent JSON DEFAULT NULL,
                intent_confidence DECIMAL(3,2) DEFAULT NULL,
                intent_parser_type ENUM('mock', 'llm', 'hybrid') DEFAULT 'mock',

                -- Strategy & Tone
                strategy_config JSON DEFAULT NULL,
                tone_applied VARCHAR(100) DEFAULT NULL,
                system_directive TEXT DEFAULT NULL,

                -- Recommendations
                outfits_count INT DEFAULT 0,
                outfits_data JSON DEFAULT NULL,
                recommendation_engine_version VARCHAR(50) DEFAULT 'v1',

                -- Performance Metrics
                response_time_ms INT DEFAULT NULL,
                intent_parsing_time_ms INT DEFAULT NULL,
                recommendation_time_ms INT DEFAULT NULL,

                -- User Context
                user_ip VARCHAR(45) DEFAULT NULL,
                user_agent TEXT DEFAULT NULL,
                language_detected VARCHAR(10) DEFAULT NULL,

                -- Conversation Flow
                conversation_turn_number INT DEFAULT 1,
                previous_message_id INT DEFAULT NULL,
                is_follow_up BOOLEAN DEFAULT FALSE,

                -- Business Metrics
                clicked_recommendations JSON DEFAULT NULL,
                conversion_events JSON DEFAULT NULL,
                satisfaction_score TINYINT DEFAULT NULL,

                -- Error Tracking
                error_occurred BOOLEAN DEFAULT FALSE,
                error_message TEXT DEFAULT NULL,
                error_stack_trace TEXT DEFAULT NULL,

                -- Timestamps
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

                -- Indexes
                INDEX idx_session_id (session_id),
                INDEX idx_request_id (request_id),
                INDEX idx_created_at (created_at),
                INDEX idx_session_timestamp (session_id, created_at),
                INDEX idx_response_type (ai_response_type),
                INDEX idx_outfits_count (outfits_count),
                INDEX idx_error_occurred (error_occurred),
                INDEX idx_conversation_flow (session_id, conversation_turn_number),

                -- Foreign key constraint
                FOREIGN KEY (previous_message_id) REFERENCES chat_logs(id) ON DELETE SET NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """

            cursor.execute(create_chat_logs_sql)
            print("✅ Created chat_logs table")

            # Create chat_sessions table for session management
            create_chat_sessions_sql = """
            CREATE TABLE IF NOT EXISTS chat_sessions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                session_id VARCHAR(255) NOT NULL UNIQUE,

                -- Session Metadata
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                ended_at TIMESTAMP NULL,
                is_active BOOLEAN DEFAULT TRUE,

                -- User Information
                user_ip VARCHAR(45) DEFAULT NULL,
                user_agent TEXT DEFAULT NULL,
                language_preference VARCHAR(10) DEFAULT NULL,

                -- Session Strategy
                default_strategy JSON DEFAULT NULL,
                current_strategy JSON DEFAULT NULL,
                strategy_ab_bucket VARCHAR(50) DEFAULT NULL,

                -- Conversation Context
                total_messages INT DEFAULT 0,
                total_recommendations INT DEFAULT 0,
                context_data JSON DEFAULT NULL,

                -- Performance Metrics
                avg_response_time_ms INT DEFAULT NULL,
                satisfaction_score DECIMAL(3,2) DEFAULT NULL,
                conversion_events JSON DEFAULT NULL,

                -- Business Intelligence
                customer_segment VARCHAR(50) DEFAULT NULL,
                marketing_campaign VARCHAR(100) DEFAULT NULL,
                referrer_source VARCHAR(100) DEFAULT NULL,

                INDEX idx_session_id (session_id),
                INDEX idx_created_at (created_at),
                INDEX idx_last_activity (last_activity),
                INDEX idx_is_active (is_active),
                INDEX idx_customer_segment (customer_segment),
                INDEX idx_strategy_bucket (strategy_ab_bucket)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """

            cursor.execute(create_chat_sessions_sql)
            print("✅ Created chat_sessions table")

            # Create chat_strategies table for strategy presets
            create_chat_strategies_sql = """
            CREATE TABLE IF NOT EXISTS chat_strategies (
                id INT AUTO_INCREMENT PRIMARY KEY,
                strategy_name VARCHAR(100) NOT NULL UNIQUE,

                -- Strategy Configuration
                tone VARCHAR(50) NOT NULL,
                language VARCHAR(10) DEFAULT 'en',
                objectives JSON DEFAULT NULL,
                guardrails JSON DEFAULT NULL,
                style_config JSON DEFAULT NULL,

                -- Business Rules
                is_active BOOLEAN DEFAULT TRUE,
                is_default BOOLEAN DEFAULT FALSE,
                target_segments JSON DEFAULT NULL,

                -- Metadata
                description TEXT DEFAULT NULL,
                created_by VARCHAR(100) DEFAULT NULL,
                version VARCHAR(20) DEFAULT 'v1.0',

                -- Performance Tracking
                usage_count INT DEFAULT 0,
                avg_satisfaction DECIMAL(3,2) DEFAULT NULL,
                conversion_rate DECIMAL(5,4) DEFAULT NULL,

                -- Timestamps
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

                INDEX idx_strategy_name (strategy_name),
                INDEX idx_is_active (is_active),
                INDEX idx_is_default (is_default),
                INDEX idx_tone (tone)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """

            cursor.execute(create_chat_strategies_sql)
            print("✅ Created chat_strategies table")

            # Insert default strategy presets
            default_strategies = [
                {
                    "strategy_name": "default",
                    "tone": "friendly",
                    "language": "en",
                    "objectives": '["assist", "recommend"]',
                    "guardrails": '["no_pressure", "respect_budget"]',
                    "style_config": '{"max_sentences": 3, "cta": "soft", "emojis": false}',
                    "is_default": 1,
                    "description": "Default friendly assistant tone",
                },
                {
                    "strategy_name": "luxury_concise",
                    "tone": "luxury_concise",
                    "language": "en",
                    "objectives": '["raise_aov", "promote_quality"]',
                    "guardrails": '["no_discount_push", "maintain_brand_image"]',
                    "style_config": '{"max_sentences": 2, "cta": "soft", "emojis": false}',
                    "is_default": 0,
                    "description": "Concise luxury brand tone for premium customers",
                },
                {
                    "strategy_name": "thai_bilingual",
                    "tone": "friendly",
                    "language": "th_en",
                    "objectives": '["local_engagement", "cultural_appropriate"]',
                    "guardrails": '["respect_culture", "clear_communication"]',
                    "style_config": '{"max_sentences": 3, "cta": "medium", "emojis": true, "bilingual": true}',
                    "is_default": 0,
                    "description": "Bilingual Thai-English for local customers",
                },
                {
                    "strategy_name": "new_arrivals_spotlight",
                    "tone": "minimalist_luxury",
                    "language": "th_en",
                    "objectives": '["promote_new_arrivals", "raise_aov"]',
                    "guardrails": '["no_hard_sell", "quality_focus"]',
                    "style_config": '{"max_sentences": 2, "cta": "soft", "emojis": false}',
                    "is_default": 0,
                    "description": "Focus on new arrivals with minimal luxury approach",
                },
            ]

            for strategy in default_strategies:
                insert_strategy_sql = """
                INSERT IGNORE INTO chat_strategies
                (strategy_name, tone, language, objectives, guardrails, style_config, is_default, description)
                VALUES (%(strategy_name)s, %(tone)s, %(language)s, %(objectives)s, %(guardrails)s, %(style_config)s, %(is_default)s, %(description)s)
                """
                cursor.execute(insert_strategy_sql, strategy)

            print("✅ Inserted default strategy presets")

        # Commit changes
        connection.commit()
        print("\n🎉 Chat logging tables created successfully!")

        # Print table information
        with connection.cursor() as cursor:
            cursor.execute("SHOW TABLES LIKE 'chat_%'")
            tables = cursor.fetchall()
            print(f"\n📊 Created {len(tables)} chat-related tables:")
            for table in tables:
                print(f"  - {table[0]}")

    except Exception as e:
        connection.rollback()
        print(f"❌ Error creating chat logging tables: {e}")
        raise
    finally:
        connection.close()


def main():
    """Main execution function."""
    print("🚀 Creating Chat Logging Database Tables")
    print("=" * 50)

    try:
        create_chat_logs_table()
        print("\n✅ Database setup completed successfully!")
        print("\n📝 Next steps:")
        print("1. Update chat router to log interactions")
        print("2. Implement strategy service")
        print("3. Switch to LLM intent parser")

    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
