-- Add name column to chat_sessions table for AI-generated chat titles
ALTER TABLE chat_sessions ADD COLUMN name VARCHAR(255) DEFAULT NULL;