#!/bin/bash

# Lookbook-MPC Chat Server Startup Script
echo "🚀 Starting Lookbook-MPC Chat Server..."
echo "=================================================="

# --- Load .env file (required) ---
if [ ! -f ".env" ]; then
    echo "❌ Error: .env file not found!"
    echo "Please create a .env file with all required environment variables."
    echo
    echo "Required variables:"
    echo "  LLM_PROVIDER=ollama or openrouter"
    echo "  OLLAMA_HOST=http://localhost:11434"
    echo "  OLLAMA_TEXT_MODEL=llama3.2:latest"
    echo "  OLLAMA_TEXT_MODEL_FAST=llama3.2:1b"
    echo "  OLLAMA_VISION_MODEL=llava:latest"
    echo "  OPENROUTER_MODEL=openai/gpt-4o-mini"
    echo "  OPENROUTER_API_KEY=your-api-key-here"
    echo "  S3_BASE_URL=https://your-cdn-url.cloudfront.net"
    echo "  LOG_LEVEL=INFO"
    echo "  LOG_FORMAT=detailed"
    echo
    exit 1
fi

echo "📄 Loading environment variables from .env file..."

# Load environment variables from .env file
while IFS= read -r line || [ -n "$line" ]; do
    # Skip empty lines and comments
    [ -z "$line" ] && continue
    case "$line" in
        \#*) continue ;;
        *=*)
            # Extract key and value
            key="${line%%=*}"
            value="${line#*=}"
            
            # Remove leading/trailing whitespace from key
            key="$(echo "$key" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
            
            # Skip if key is empty or invalid
            [ -z "$key" ] && continue
            case "$key" in
                *[!A-Za-z0-9_]*) continue ;;
            esac
            
            # Remove quotes from value if present
            case "$value" in
                \"*\") value="${value#\"}" ; value="${value%\"}" ;;
                \'*\') value="${value#\'}" ; value="${value%\'}" ;;
            esac
            
            # Export the variable
            export "$key"="$value"
            ;;
    esac
done < .env

# --- Validate required variables ---
missing_vars=""

# Always required
[ -z "$LLM_PROVIDER" ] && missing_vars="$missing_vars LLM_PROVIDER"
[ -z "$S3_BASE_URL" ] && missing_vars="$missing_vars S3_BASE_URL"
[ -z "$LOG_LEVEL" ] && missing_vars="$missing_vars LOG_LEVEL"
[ -z "$LOG_FORMAT" ] && missing_vars="$missing_vars LOG_FORMAT"

# Provider-specific validation
if [ "$LLM_PROVIDER" = "openrouter" ]; then
    [ -z "$OPENROUTER_MODEL" ] && missing_vars="$missing_vars OPENROUTER_MODEL"
    [ -z "$OPENROUTER_API_KEY" ] && missing_vars="$missing_vars OPENROUTER_API_KEY"
elif [ "$LLM_PROVIDER" = "ollama" ]; then
    [ -z "$OLLAMA_HOST" ] && missing_vars="$missing_vars OLLAMA_HOST"
    [ -z "$OLLAMA_TEXT_MODEL" ] && missing_vars="$missing_vars OLLAMA_TEXT_MODEL"
    [ -z "$OLLAMA_TEXT_MODEL_FAST" ] && missing_vars="$missing_vars OLLAMA_TEXT_MODEL_FAST"
else
    echo "❌ Error: LLM_PROVIDER must be either 'ollama' or 'openrouter'"
    exit 1
fi

# Always check vision model
[ -z "$OLLAMA_VISION_MODEL" ] && missing_vars="$missing_vars OLLAMA_VISION_MODEL"

if [ -n "$missing_vars" ]; then
    echo "❌ Error: Missing required environment variables:$missing_vars"
    echo "Please add them to your .env file."
    exit 1
fi

# --- Print summary ---
echo "✅ Environment variables loaded successfully!"
echo
echo "Configuration Summary:"
echo "  LLM_PROVIDER=$LLM_PROVIDER"
if [ "$LLM_PROVIDER" = "openrouter" ]; then
    echo "  OPENROUTER_MODEL=$OPENROUTER_MODEL"
    # Show only last 4 characters of API key for security
    key_length=${#OPENROUTER_API_KEY}
    if [ "$key_length" -gt 4 ]; then
        masked_key="***${OPENROUTER_API_KEY#"${OPENROUTER_API_KEY%????}"}"
    else
        masked_key="***"
    fi
    echo "  OPENROUTER_API_KEY=$masked_key"
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
echo "  ✅ Product images will load from CDN"
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

echo "=================================================="
echo "Press Ctrl+C to stop the server"
echo

# Check if port 8000 is already in use
if command -v lsof >/dev/null 2>&1 && lsof -i :8000 >/dev/null 2>&1; then
    echo "⚠️  Port 8000 is already in use. Please stop the existing server first."
    echo "   You can find the process with: lsof -i :8000"
    echo "   Or kill it with: pkill -f 'python.*main.py'"
    exit 1
fi

# Start the server
poetry run python main.py