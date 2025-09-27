#!/bin/bash
# Setup script for LookbookMPC Embedding Service
# This script installs and configures the embedding service for fashion recommendations

set -e  # Exit on any error

echo "🚀 Setting up LookbookMPC Embedding Service"
echo "=============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️ $1${NC}"
}

# Check if Python 3.8+ is available
print_info "Checking Python version..."
python_version=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" = "$required_version" ]; then
    print_status "Python $python_version is compatible"
else
    print_error "Python 3.8+ required, found $python_version"
    exit 1
fi

# Create virtual environment
print_info "Creating Python virtual environment..."
if [ ! -d ".venv_embedding" ]; then
    python3 -m venv .venv_embedding
    print_status "Virtual environment created"
else
    print_warning "Virtual environment already exists"
fi

# Activate virtual environment
print_info "Activating virtual environment..."
source .venv_embedding/bin/activate

# Upgrade pip
print_info "Upgrading pip..."
pip install --upgrade pip

# Install core dependencies
print_info "Installing core ML dependencies..."
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

print_info "Installing transformers and CLIP dependencies..."
pip install transformers>=4.30.0 pillow>=9.0.0 requests>=2.28.0

print_info "Installing vector database and similarity search..."
pip install faiss-cpu>=1.7.4 scikit-learn>=1.3.0 numpy>=1.24.0

print_info "Installing FastAPI and web service dependencies..."
pip install fastapi>=0.100.0 uvicorn>=0.20.0 pydantic>=2.0.0

print_info "Installing caching and storage..."
pip install redis>=4.5.0 sqlite3  # sqlite3 is usually built-in

print_status "All dependencies installed successfully!"

# Create directory structure
print_info "Creating directory structure..."
mkdir -p embedding_service
mkdir -p embedding_service/lib
mkdir -p embedding_service/cache
mkdir -p embedding_service/models
mkdir -p logs

print_status "Directory structure created"

# Copy production files
print_info "Setting up service files..."

# Create the main service file
cat > embedding_service/main.py << 'EOF'
#!/usr/bin/env python3
"""
LookbookMPC Embedding Service - Production Entry Point
"""
import sys
import os

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from embedding_production_example import app, Config
import uvicorn

if __name__ == "__main__":
    print("🚀 Starting LookbookMPC Embedding Service")
    print(f"📊 Model: {Config.CLIP_MODEL}")
    print(f"🌐 Server: http://{Config.HOST}:{Config.PORT}")
    print(f"📖 API Docs: http://{Config.HOST}:{Config.PORT}/docs")
    print("🔥 Ready for production!")
    
    uvicorn.run(
        "main:app",
        host=Config.HOST,
        port=Config.PORT,
        reload=False,
        workers=1,
        log_level="info"
    )
EOF

# Create systemd service file
print_info "Creating systemd service file..."
cat > embedding_service/lookbook-embedding.service << EOF
[Unit]
Description=LookbookMPC Embedding Service
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$PWD/embedding_service
Environment=PATH=$PWD/.venv_embedding/bin
ExecStart=$PWD/.venv_embedding/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Create Docker setup
print_info "Creating Docker configuration..."
cat > embedding_service/Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create cache directory
RUN mkdir -p /app/cache

# Expose port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8001/embeddings/health || exit 1

# Run the service
CMD ["python", "main.py"]
EOF

# Create requirements.txt for Docker
cat > embedding_service/requirements.txt << 'EOF'
torch>=2.0.0
torchvision>=0.15.0
transformers>=4.30.0
pillow>=9.0.0
requests>=2.28.0
faiss-cpu>=1.7.4
scikit-learn>=1.3.0
numpy>=1.24.0
fastapi>=0.100.0
uvicorn>=0.20.0
pydantic>=2.0.0
redis>=4.5.0
EOF

# Create docker-compose.yml
cat > docker-compose.embedding.yml << 'EOF'
version: '3.8'

services:
  embedding-service:
    build: ./embedding_service
    ports:
      - "8001:8001"
    environment:
      - REDIS_URL=redis://redis:6379
      - DB_PATH=/app/data/lookbook.db
    volumes:
      - ./lookbook.db:/app/data/lookbook.db:ro
      - embedding_cache:/app/cache
      - embedding_models:/app/models
    depends_on:
      - redis
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/embeddings/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped
    command: redis-server --appendonly yes

volumes:
  embedding_cache:
  embedding_models:
  redis_data:
EOF

# Create environment configuration
print_info "Creating environment configuration..."
cat > embedding_service/.env << EOF
# LookbookMPC Embedding Service Configuration

# Service Settings
HOST=localhost
PORT=8001

# Database
DB_PATH=../lookbook.db
EMBEDDING_CACHE_PATH=cache/embeddings_cache.db

# Model Settings
CLIP_MODEL=openai/clip-vit-base-patch32
EMBEDDING_DIMENSION=512

# Performance
MAX_CACHE_SIZE=10000
BATCH_SIZE=32

# S3/CDN
S3_BASE_URL=https://d29c1z66frfv6c.cloudfront.net/pub/media/catalog/product/large/

# Redis (optional)
REDIS_URL=redis://localhost:6379
CACHE_EXPIRY_HOURS=24

# Logging
LOG_LEVEL=INFO
EOF

# Create startup script
print_info "Creating startup script..."
cat > start_embedding_service.sh << 'EOF'
#!/bin/bash
# Startup script for LookbookMPC Embedding Service

echo "🚀 Starting LookbookMPC Embedding Service..."

# Activate virtual environment
source .venv_embedding/bin/activate

# Check if database exists
if [ ! -f "lookbook.db" ]; then
    echo "❌ Database not found: lookbook.db"
    echo "Please ensure your database is set up first"
    exit 1
fi

# Start the service
cd embedding_service
python main.py
EOF

chmod +x start_embedding_service.sh

# Create test script
print_info "Creating test script..."
cat > test_embedding_service.sh << 'EOF'
#!/bin/bash
# Test script for embedding service

echo "🧪 Testing LookbookMPC Embedding Service..."

# Check if service is running
if ! curl -s http://localhost:8001/embeddings/health > /dev/null; then
    echo "❌ Service is not running. Start with: ./start_embedding_service.sh"
    exit 1
fi

echo "✅ Service is running"

# Test health endpoint
echo "🔍 Testing health endpoint..."
curl -s http://localhost:8001/embeddings/health | jq .

echo ""
echo "🎯 Testing similarity search..."
curl -s -X POST http://localhost:8001/embeddings/similar \
  -H "Content-Type: application/json" \
  -d '{
    "image_url": "https://d29c1z66frfv6c.cloudfront.net/pub/media/catalog/product/large/dress_summer.jpg",
    "limit": 3
  }' | jq .

echo ""
echo "✅ All tests completed!"
EOF

chmod +x test_embedding_service.sh

# Create monitoring script
cat > monitor_embedding_service.sh << 'EOF'
#!/bin/bash
# Simple monitoring script for embedding service

while true; do
    if curl -s http://localhost:8001/embeddings/health > /dev/null; then
        echo "$(date): ✅ Service is healthy"
    else
        echo "$(date): ❌ Service is down!"
        # Optionally restart the service
        # ./start_embedding_service.sh &
    fi
    sleep 30
done
EOF

chmod +x monitor_embedding_service.sh

print_status "Setup complete!"

echo ""
echo "📋 NEXT STEPS:"
echo "=============="
echo ""
print_info "1. Test the simple demo:"
echo "   python test_embeddings_simple.py"
echo ""
print_info "2. Start the production service:"
echo "   ./start_embedding_service.sh"
echo ""
print_info "3. Test the API endpoints:"
echo "   ./test_embedding_service.sh"
echo ""
print_info "4. For production deployment:"
echo "   docker-compose -f docker-compose.embedding.yml up -d"
echo ""
print_info "5. Integration with Next.js:"
echo "   - Add EMBEDDING_SERVICE_URL=http://localhost:8001 to .env.local"
echo "   - Use the functions in nextjs_integration_example.ts"
echo ""

echo "🎉 LookbookMPC Embedding Service is ready!"
echo ""
echo "📖 Documentation: EMBEDDING_GUIDE.md"
echo "🌐 API Docs: http://localhost:8001/docs (when service is running)"
echo "💡 For help: Check the generated files and examples"