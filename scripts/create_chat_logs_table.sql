-- Create chat_logs table for comprehensive chat interaction logging
-- This table stores all chat messages, responses, and analytics data

CREATE TABLE chat_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_id VARCHAR(36) NOT NULL,
    request_id VARCHAR(36) NOT NULL,
    user_message TEXT NOT NULL,
    user_message_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ai_response TEXT,
    ai_response_type VARCHAR(50) DEFAULT 'general',
    ai_response_timestamp TIMESTAMP NULL,
    parsed_intent JSON,
    intent_confidence DECIMAL(3,2),
    intent_parser_type VARCHAR(20) DEFAULT 'mock',
    strategy_config JSON,
    tone_applied VARCHAR(20),
    system_directive TEXT,
    outfits_count INT DEFAULT 0,
    outfits_data JSON,
    recommendation_engine_version VARCHAR(10) DEFAULT 'v1',
    response_time_ms INT,
    intent_parsing_time_ms INT,
    recommendation_time_ms INT,
    user_ip VARCHAR(45),
    user_agent TEXT,
    language_detected VARCHAR(10),
    conversation_turn_number INT DEFAULT 1,
    previous_message_id INT,
    is_follow_up BOOLEAN DEFAULT FALSE,
    error_occurred BOOLEAN DEFAULT FALSE,
    error_message TEXT,
    error_stack_trace TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Indexes for performance
    INDEX idx_session_id (session_id),
    INDEX idx_created_at (created_at),
    INDEX idx_ai_response_type (ai_response_type),
    INDEX idx_error_occurred (error_occurred),
    INDEX idx_conversation_turn (session_id, conversation_turn_number),

    -- Foreign key constraint (optional, depends on chat_sessions table)
    FOREIGN KEY (session_id) REFERENCES chat_sessions(session_id) ON DELETE CASCADE
);

-- Create chat_sessions table if it doesn't exist
CREATE TABLE IF NOT EXISTS chat_sessions (
    session_id VARCHAR(36) PRIMARY KEY,
    total_messages INT DEFAULT 0,
    total_recommendations INT DEFAULT 0,
    avg_response_time_ms DECIMAL(10,2),
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    name VARCHAR(255),
    context_data JSON,
    current_strategy JSON,
    satisfaction_score DECIMAL(3,1),
    is_active BOOLEAN DEFAULT TRUE,

    INDEX idx_is_active (is_active),
    INDEX idx_last_activity (last_activity)
);