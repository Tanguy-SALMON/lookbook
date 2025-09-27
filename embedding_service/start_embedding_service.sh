#!/bin/bash
# Simple startup script for LookbookMPC Embedding Service

echo "🚀 Starting LookbookMPC Embedding Service..."
echo ""

# Check if virtual environment exists
if [ ! -d ".venv_embedding" ]; then
    echo "❌ Virtual environment not found!"
    echo "Please run: python -m venv .venv_embedding"
    echo "Then install requirements: pip install torch transformers pillow requests faiss-cpu scikit-learn fastapi uvicorn pydantic"
    exit 1
fi

# Activate virtual environment
echo "📦 Activating virtual environment..."
source .venv_embedding/bin/activate

# Check if database exists
if [ ! -f "lookbook.db" ]; then
    echo "⚠️  Database not found: lookbook.db"
    echo "Service will run with mock data for testing"
fi

# Check Python dependencies
echo "🔍 Checking dependencies..."
python -c "import torch, transformers, fastapi; print('✅ All dependencies available')" 2>/dev/null || {
    echo "❌ Missing dependencies!"
    echo "Install with: pip install torch transformers pillow requests faiss-cpu scikit-learn fastapi uvicorn pydantic"
    exit 1
}

echo "✅ Environment ready"
echo ""
echo "🌐 Starting server on http://localhost:8001"
echo "📖 API docs will be available at http://localhost:8001/docs"
echo "🔍 Health check: http://localhost:8001/health"
echo ""
echo "Press Ctrl+C to stop the service"
echo ""

# Start the service
cd embedding_service
exec python main.py