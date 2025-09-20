# Lookbook-MPC User Documentation

## Overview

Lookbook-MPC is a FastAPI-based fashion recommendation microservice that provides intelligent outfit recommendations using vision analysis, intent parsing, and rules-based recommendations. This document provides comprehensive instructions for starting the server, running tests, and accessing the application.

## Prerequisites

- Python 3.11+
- Ollama installed and running
- At least 4GB of RAM available
- Port 8000, 8001, and 11434 available

## Quick Start

### 1. Starting the Server

The system consists of two main services that need to run simultaneously:

#### Step 1: Start Ollama (LLM Service)

```bash
# Start Ollama daemon in a terminal
ollama serve

# In another terminal, pull the required models (if not already installed)
ollama pull qwen2.5vl
ollama pull qwen3:4b  # Use 4B variant for faster inference

# Verify models are available
ollama list
```

#### Step 2: Start Vision Sidecar Service

```bash
# In the project directory, start the vision analysis service
poetry run python vision_sidecar.py
```

You should see output similar to:

```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8001
```

#### Step 3: Start Main API Service

```bash
# In another terminal, in the project directory
poetry run python main.py
```

The main API will be available at `http://localhost:8000`

### 2. Starting the Test Suite

#### Running All Tests

```bash
# Run all tests using pytest
poetry run pytest

# Run tests with coverage
poetry run pytest --cov=lookbook_mpc

# Run specific test categories
poetry run pytest -m unit          # Run only unit tests
poetry run pytest -m integration   # Run only integration tests
poetry run pytest -m "not slow"    # Skip slow tests
```

#### Running Individual Test Scripts

```bash
# Test API endpoints
poetry run python scripts/test_api.py

# Test recommender system
poetry run python scripts/test_recommender.py

# Test demo UI
poetry run python scripts/test_demo.py

# Test MCP server
poetry run python scripts/test_mcp.py
```

#### Running Tests with Docker

```bash
# Run tests in Docker environment
docker-compose exec api python -m pytest

# Run tests with coverage in Docker
docker-compose exec api python -m pytest --cov=lookbook_mpc
```

### 3. Accessing the Application

#### Web Interface

- **Main API Documentation**: `http://localhost:8000/docs`
- **Alternative API Documentation**: `http://localhost:8000/redoc`
- **Demo Chat Interface**: `http://localhost:8000/demo`
- **Health Check**: `http://localhost:8000/health`
- **Readiness Check**: `http://localhost:8000/ready`

#### API Endpoints

##### Health and Status

- `GET /health` - Basic health check
- `GET /ready` - Readiness probe with dependency checks

##### Ingestion

- `POST /v1/ingest/items` - Ingest items from catalog
- `GET /v1/ingest/items` - List ingested items
- `GET /v1/ingest/stats` - Get ingestion statistics

##### Recommendations

- `POST /v1/recommendations` - Generate outfit recommendations
- `GET /v1/recommendations/preview` - Preview recommendations
- `GET /v1/recommendations/constraints` - Get constraint options
- `GET /v1/recommendations/popular` - Get popular recommendations
- `GET /v1/recommendations/trending` - Get trending recommendations

##### Chat

- `POST /v1/chat` - Chat interaction
- `GET /v1/chat/sessions` - List chat sessions
- `GET /v1/chat/suggestions` - Get chat suggestions

##### Images

- `GET /v1/images/{image_key}` - Get image with transformations
- `GET /v1/images/{image_key}/redirect` - Redirect to original image

#### MCP Integration

The service exposes Model Context Protocol (MCP) tools and resources:

##### Available Tools

- `recommend_outfits(query, budget?, size?)` - Generate outfit recommendations
- `search_items(filters)` - Search catalog items
- `ingest_batch(limit?)` - Ingest items from catalog

##### Available Resources

- `openapi` - OpenAPI specification
- `rules_catalog` - Fashion recommendation rules
- `schemas` - JSON schemas for API models

MCP endpoints are available at: `http://localhost:8000/mcp`

## Configuration

### Environment Variables

Create a `.env` file based on `.env.example`:

```bash
# Required variables
OLLAMA_HOST=http://localhost:11434
OLLAMA_VISION_MODEL=qwen2.5vl
OLLAMA_TEXT_MODEL=qwen3:4b  # Use 4B variant for faster inference
S3_BASE_URL=https://your-s3-bucket.s3.amazonaws.com

# Optional variables
LOOKBOOK_DB_URL=sqlite:///./lookbook.db
MYSQL_SHOP_URL=mysql+pymysql://user:password@localhost:3306/magento_db
LOG_LEVEL=INFO
TZ=UTC
```

### Service Ports

| Service        | Port  | Description                        |
| -------------- | ----- | ---------------------------------- |
| Main API       | 8000  | FastAPI application with endpoints |
| Vision Sidecar | 8001  | Image analysis service             |
| Ollama         | 11434 | LLM and vision model server        |
| Demo UI        | 8000  | Web interface at /demo             |

## Testing the Setup

### Testing Vision Sidecar

```bash
# Health check
curl http://localhost:8001/health

# Test image analysis (replace with actual image URL)
poetry run python vision_sidecar.py
```

### Testing Main API

```bash
# Health check
curl http://localhost:8000/health

# Ingest products (pulls from Magento and analyzes images)
curl -X POST "http://localhost:8000/v1/ingest/items" \
  -H "Content-Type: application/json" \
  -d '{"limit": 5}'

# Ingest products with timestamp filter
curl -X POST "http://localhost:8000/v1/ingest/items" \
  -H "Content-Type: application/json" \
  -d '{"limit": 10, "since": "2025-01-19T00:00:00Z"}'

# Test recommendations
curl -X POST "http://localhost:8000/v1/recommendations" \
  -H "Content-Type: application/json" \
  -d '{"text_query": "I want to do yoga"}'
```

### Using the Demo Interface

1. Open your browser and navigate to: `http://localhost:8000/demo`
2. Type fashion requests like:
   - "I want to do yoga"
   - "Restaurant this weekend, attractive for $50"
   - "I am fat, look slim"
3. The AI will analyze your request and show outfit recommendations

## Docker Deployment

### Using Docker Compose

```bash
# Start all services
docker-compose up -d

# View service status
docker-compose ps

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

### Services Overview

- **ollama**: Provides LLM models (qwen2.5vl, qwen3)
- **api**: FastAPI recommendation microservice
- **vision**: Image analysis sidecar service
- **nginx**: Optional reverse proxy (use `--profile nginx`)

### Development Mode

```bash
# Start individual services
docker-compose up -d ollama
docker-compose up -d api
docker-compose up -d vision
```

## Troubleshooting

### Common Issues

#### 1. "Model not found" error

```bash
# Make sure you have the correct model names
ollama pull qwen2.5vl
ollama pull qwen3:4b
ollama list  # Should show both models
```

#### 2. Vision Sidecar connection refused

```bash
# Make sure vision sidecar is running on port 8001
curl http://localhost:8001/health
```

#### 3. Main API not starting

```bash
# Check if port 8000 is available
lsof -i :8000
# Kill any conflicting process if needed
```

#### 4. No outfit recommendations returned

```bash
# Make sure you've ingested some products first
curl -X POST "http://localhost:8000/v1/ingest/items" \
  -H "Content-Type: application/json" \
  -d '{"limit": 10}'
```

#### 5. Ollama not responding

```bash
# Check Ollama service
curl http://localhost:11434/api/tags

# Restart Ollama if needed
pkill -f ollama
ollama serve
```

### Debug Mode

Enable debug logging:

```bash
export LOG_LEVEL=DEBUG
poetry run python main.py
```

### Health Checks

Monitor service health:

```bash
# Check all services
curl http://localhost:8000/health
curl http://localhost:11434/api/tags
curl http://localhost:8001/health
```

## Development

### Code Quality Tools

```bash
# Format code
poetry run black .

# Lint code
poetry run ruff check .

# Type check
poetry run mypy .

# Run all quality checks
poetry run black . && poetry run ruff check . && poetry run mypy .
```

### Running Tests in Development

```bash
# Run with auto-reload for development
poetry run uvicorn main:app --reload

# Run specific test file
poetry run pytest tests/test_api_integration.py

# Run tests with verbose output
poetry run pytest -v
```

## Architecture

### System Components

```
[Demo UI] → [Main API:8000] → [Vision Sidecar:8001] → [Ollama:11434]
                ↓                      ↓                     ↓
           FastAPI Routes        Image Analysis         qwen2.5vl
           Recommendations      Fashion Attributes      Vision Model
```

### Core Layers

- **Domain Layer**: Entities, use cases
- **Adapters Layer**: Database, vision, intent, image adapters
- **Services Layer**: Rules engine, recommender
- **API Layer**: REST endpoints, MCP server

## Support

### Getting Help

1. Check the troubleshooting section above
2. Review the logs for error messages
3. Test individual components using the provided test scripts
4. Verify all services are running and accessible

### Creating Issues

When reporting issues, please include:

- System information (OS, Python version)
- Error messages and stack traces
- Steps to reproduce the issue
- Expected vs actual behavior

### Additional Resources

- API Documentation: `http://localhost:8000/docs`
- Project README: `README.md`
- Deployment Guide: `DEPLOYMENT.md`
- Test Scripts: `scripts/test_*.py`

---

_This documentation covers the essential information needed to start, test, and use the Lookbook-MPC system. For more detailed information about specific components or advanced configuration, refer to the project's README.md and source code documentation._
