#!/bin/bash

# Lookbook-MPC Chat Server Startup Script
# Loads environment variables from .env file and starts the server

echo "🚀 Starting Lookbook-MPC Chat Server..."
echo "=" | head -c 50; echo

# Load environment variables from .env file if it exists
if [ -f ".env" ]; then
    echo "📄 Loading environment variables from .env file..."
    while read -r line; do
        if [[ $line =~ ^[^#]*= ]]; then
            export "$line"
        fi
    done < .env
else
    echo "⚠️  No .env file found, using system environment variables"
fi

# Set default values for required environment variables if not set
export OLLAMA_HOST="${OLLAMA_HOST:-http://localhost:11434}"
export OLLAMA_VISION_MODEL="${OLLAMA_VISION_MODEL:-qwen2.5vl:7b}"
export OLLAMA_TEXT_MODEL="${OLLAMA_TEXT_MODEL:-qwen3:4b}"
export S3_BASE_URL="${S3_BASE_URL:-https://d29c1z66frfv6c.cloudfront.net/pub/media/catalog/product/large/}"
export OLLAMA_TEXT_MODEL_FAST="${OLLAMA_TEXT_MODEL_FAST:-llama3.2:1b-instruct-q4_K_M}"
export MYSQL_APP_URL="${MYSQL_APP_URL:-mysql+pymysql://magento:Magento@COS(*)@127.0.0.1:3306/lookbookMPC}"
export LLM_PROVIDER="${LLM_PROVIDER:-openrouter}"
export OPENROUTER_MODEL="${OPENROUTER_MODEL:-openai/gpt-oss-20b:free}"
export LLM_SERVICE_API="${LLM_SERVICE_API:-OpenRouter (openai/gpt-oss-20b:free)}"
export LOG_LEVEL="${LOG_LEVEL:-DEBUG}"
export LOG_FORMAT="${LOG_FORMAT:-json}"

echo "Environment variables loaded:"
echo "  LLM_SERVICE_API=$LLM_SERVICE_API"
echo "  LLM_PROVIDER=$LLM_PROVIDER"
if [ "$LLM_PROVIDER" = "openrouter" ]; then
    echo "  OPENROUTER_MODEL=$OPENROUTER_MODEL"
else
    echo "  OLLAMA_HOST=$OLLAMA_HOST"
    echo "  OLLAMA_TEXT_MODEL=$OLLAMA_TEXT_MODEL"
    echo "  OLLAMA_TEXT_MODEL_FAST=$OLLAMA_TEXT_MODEL_FAST"
fi
echo "  OLLAMA_VISION_MODEL=$OLLAMA_VISION_MODEL"
echo "  S3_BASE_URL=$S3_BASE_URL"
echo "  LOG_LEVEL=$LOG_LEVEL"
echo "  LOG_FORMAT=$LOG_FORMAT"
echo

echo "Server will be available at:"
echo "  🌐 Main Landing Page: http://localhost:8000"
echo "  💬 Demo Chat: http://localhost:8000/demo"
echo "  🧪 Test Interface: http://localhost:8000/test"
echo "  📚 Documentation Hub: http://localhost:8000/docs-index"
echo "  📖 API Docs: http://localhost:8000/docs"
echo "  🔍 Health Check: http://localhost:8000/health"
echo
echo "Image Configuration:"
echo "  📸 CDN Base URL: $S3_BASE_URL"
echo "  ✅ Product images will load from COS Thailand CloudFront"
echo

if [ "$LLM_PROVIDER" = "openrouter" ]; then
    echo "LLM Service:"
    echo "  🤖 Provider: OpenRouter"
    echo "  🧠 Model: $OPENROUTER_MODEL"
else
    echo "LLM Models:"
    echo "  🧠 Primary: $OLLAMA_TEXT_MODEL"
    echo "  ⚡ Fast (Testing): $OLLAMA_TEXT_MODEL_FAST"
fi
echo

echo "Logging Configuration:"
echo "  📊 Log Level: $LOG_LEVEL"
echo "  📋 Log Format: $LOG_FORMAT"
echo "  💬 SmartRecommender logs will be visible at $LOG_LEVEL level"
echo

echo "=" | head -c 50; echo
echo "Press Ctrl+C to stop the server"
echo

# Start the server
poetry run python main.py
