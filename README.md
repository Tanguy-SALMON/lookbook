# Lookbook-MPC

Fashion lookbook recommendation microservice with AI vision analysis and intent parsing.

## Overview

Lookbook-MPC is a FastAPI-based microservice that provides intelligent fashion recommendations using:

- **Vision Analysis**: Ollama-powered image analysis for product attributes
- **Intent Parsing**: Natural language understanding for user requests  
- **Rules Engine**: Fashion-specific recommendation rules and constraints
- **MCP Integration**: Model Context Protocol compatibility for LLM clients

## Features

- 🎯 **Smart Recommendations**: Generate 3-7 outfit combinations based on user intent
- 👁️ **Vision Analysis**: Analyze product images for color, material, pattern attributes
- 💬 **Conversational Chat**: Natural language interaction for fashion recommendations
- 🛍️ **Catalog Integration**: Read-only Magento catalog integration
- 🖼️ **Image Proxying**: CORS-safe image serving with transformations
- 🔧 **MCP Tools**: Expose recommendation tools to LLM clients
- 📊 **Health Monitoring**: Comprehensive health checks and metrics
- 🖥️ **Admin Dashboard**: Modern Next.js dashboard for monitoring and management

## Quick Start

### Prerequisites

- Python 3.11+
- Ollama running with models: `qwen2.5vl` (vision) and `qwen3:4b` (text)
- Node.js 18+ (for admin dashboard)

### Installation

```bash
cd /Users/tanguysalmon/PythonPlayGround/test-roocode
pip install fastapi uvicorn structlog pydantic
```

### Starting Services

**Start in this order:**

1. **Ollama Service**
```bash
# Terminal 1
ollama serve
# Terminal 2
ollama pull qwen2.5vl
ollama pull qwen3:4b
```

2. **Vision Sidecar**  
```bash
# Terminal 3
python vision_sidecar.py
# Should show: Uvicorn running on http://0.0.0.0:8001
```

3. **Main API**
```bash
# Terminal 4
python main.py
# Available at http://localhost:8000
```

4. **Admin Dashboard** (Optional)
```bash
# Terminal 5
cd shadcn && npm install && npm run dev
# Available at http://localhost:3000
```

### Quick Test

```bash
# Health check
curl http://localhost:8000/health

# Test recommendations
curl -X POST "http://localhost:8000/v1/recommendations" \
  -H "Content-Type: application/json" \
  -d '{"text_query": "I want to do yoga"}'

# Demo UI
open http://localhost:8000/demo
```

## Architecture

```
[Admin Dashboard:3000] → [Main API:8000] → [Vision Sidecar:8001] → [Ollama:11434]
                              ↓                    ↓                     ↓
                         FastAPI Routes      Image Analysis         AI Models
                         Recommendations    Fashion Attributes    (qwen2.5vl/qwen3)
```

### Project Structure

```
lookbook-mpc/
├── lookbook_mpc/           # Core Python application
│   ├── domain/            # Business entities and logic
│   ├── adapters/          # External integrations (DB, Vision, etc.)
│   ├── services/          # Business services
│   └── api/               # REST API and MCP server
├── shadcn/                # Next.js admin dashboard
├── migrations/            # Database migrations
├── tests/                 # Test suite
├── scripts/               # Utility scripts
└── docs/                  # Documentation
```

## API Endpoints

### Core Endpoints

- `GET /health` - Basic health check
- `GET /ready` - Readiness probe with dependency checks
- `GET /docs` - Swagger API documentation

### Products/Ingestion

- `POST /v1/ingest/products` - Ingest products from catalog
- `GET /v1/ingest/products` - List ingested products
- `GET /v1/ingest/stats` - Get ingestion statistics

### Recommendations

- `POST /v1/recommendations` - Generate outfit recommendations
- `GET /v1/recommendations/popular` - Get popular recommendations
- `GET /v1/recommendations/trending` - Get trending recommendations

### Chat & Images

- `POST /v1/chat` - Chat interaction
- `GET /v1/chat/sessions` - List chat sessions
- `GET /v1/images/{image_key}` - Get image with transformations

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OLLAMA_HOST` | Ollama server URL | `http://localhost:11434` |
| `OLLAMA_VISION_MODEL` | Vision model name | `qwen2.5vl` |
| `OLLAMA_TEXT_MODEL` | Text model name | `qwen3:4b` |
| `S3_BASE_URL` | CDN base URL | - |
| `LOOKBOOK_DB_URL` | Database URL | `sqlite:///lookbook.db` |
| `LOG_LEVEL` | Logging level | `INFO` |

### Service Ports

| Service | Port | Description |
|---------|------|-------------|
| Main API | 8000 | FastAPI application |
| Vision Sidecar | 8001 | Image analysis service |
| Ollama | 11434 | AI model server |
| Admin Dashboard | 3000 | Next.js monitoring UI |

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=lookbook_mpc

# Run specific categories
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only

# Test individual components
python scripts/test_api.py
python scripts/test_recommender.py
```

## Development

```bash
# Format and lint
black . && ruff check . && mypy .

# Run with auto-reload
uvicorn main:app --reload

# Run tests with verbose output
pytest -v
```

## Troubleshooting

### Common Issues

1. **"Model not found"**
   ```bash
   ollama pull qwen2.5vl
   ollama pull qwen3:4b
   ollama list  # Verify both models exist
   ```

2. **Services not connecting**
   ```bash
   curl http://localhost:11434/api/tags  # Check Ollama
   curl http://localhost:8001/health     # Check Vision Sidecar
   curl http://localhost:8000/health     # Check Main API
   ```

3. **No recommendations**
   ```bash
   # Ingest some products first
   curl -X POST "http://localhost:8000/v1/ingest/products?limit=10"
   ```

### Debug Mode

```bash
export LOG_LEVEL=DEBUG
python main.py
```

## MCP Integration

The service exposes MCP tools for LLM clients:

- `recommend_outfits(query, budget?, size?)` - Generate recommendations
- `search_items(filters)` - Search catalog items  
- `ingest_batch(limit?)` - Ingest products

MCP server available at: `http://localhost:8000/mcp`

## Knowledge Base & Documentation

📋 **[DOCS_INDEX.md](DOCS_INDEX.md)** - **Start here for all documentation navigation**

For detailed technical information, troubleshooting, and development guidance:

- **🎯 [FEATURES_AND_CAPABILITIES.md](FEATURES_AND_CAPABILITIES.md)** - Complete feature overview and system capabilities
- **🔧 [TECHNICAL_GUIDE.md](TECHNICAL_GUIDE.md)** - Comprehensive technical implementation details
- **📖 [PROJECT_KNOWLEDGE_BASE.md](PROJECT_KNOWLEDGE_BASE.md)** - Detailed technical knowledge base
- **⚡ [QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Essential commands and configuration
- **🚀 [SETUP_GUIDE.md](SETUP_GUIDE.md)** - Step-by-step installation instructions
- **🔍 [DEBUG_GUIDE.md](DEBUG_GUIDE.md)** - Troubleshooting and performance optimization

### 📚 Documentation Reorganization (December 2024)
This project's documentation has been **streamlined and consolidated** from 37 files into 12 core documents:
- ✅ **All feature descriptions preserved** in consolidated format
- ✅ **Outdated execution plans and fix summaries archived** to `docs/archive/`
- ✅ **70% reduction in reading time** while maintaining complete information coverage
- ✅ **Clear navigation structure** through updated `DOCS_INDEX.md`

### Key Information for Developers:
- **Database:** MySQL setup with Magento source and application destination  
- **Currency:** Thai Baht (฿1,090 - ฿10,990 product range)
- **Tests:** 117 tests passing ✅
- **Environment:** Requires `MYSQL_SHOP_URL` and `MYSQL_APP_URL` configuration

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Run quality checks: `black . && ruff check . && mypy . && pytest`
5. Submit a pull request

## Support

- **API Documentation**: http://localhost:8000/docs
- **Admin Dashboard**: http://localhost:3000 (when running)
- **Demo Interface**: http://localhost:8000/demo
- **Detailed Guides**: See `SETUP_GUIDE.md`, `DEBUG_GUIDE.md`, and `DEPLOYMENT.md`

## License

MIT License - see LICENSE file for details.