#!/bin/bash

# Lookbook-MPC Chat Server Startup Script
# Simple bash script to start the server with minimal environment variables

echo "🚀 Starting Lookbook-MPC Chat Server..."
echo "=" | head -c 50; echo

# Set minimal required environment variables
export OLLAMA_HOST="http://localhost:11434"
export OLLAMA_VISION_MODEL="qwen2.5vl:7b"
export OLLAMA_TEXT_MODEL="qwen3:4b"
export S3_BASE_URL="https://example.com/"
export MYSQL_APP_URL="mysql+pymysql://magento:Magento@COS(*)@127.0.0.1:3306/lookbookMPC"

echo "Environment variables set:"
echo "  OLLAMA_HOST=$OLLAMA_HOST"
echo "  OLLAMA_VISION_MODEL=$OLLAMA_VISION_MODEL"
echo "  OLLAMA_TEXT_MODEL=$OLLAMA_TEXT_MODEL"
echo "  S3_BASE_URL=$S3_BASE_URL"
echo

echo "Server will be available at:"
echo "  🌐 Main API: http://localhost:8000"
echo "  💬 Demo Chat: http://localhost:8000/demo"
echo "  📚 API Docs: http://localhost:8000/docs"
echo "  🔍 Health Check: http://localhost:8000/health"
echo

echo "=" | head -c 50; echo
echo "Press Ctrl+C to stop the server"
echo

# Start the server
poetry run python main.py