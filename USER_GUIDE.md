# Lookbook-MPC User Guide

## Overview

Lookbook-MPC is a FastAPI-based fashion recommendation microservice that provides intelligent outfit recommendations using vision analysis, intent parsing, and rules-based recommendations. This guide helps you get started quickly and use the system effectively.

## Prerequisites

- Python 3.11+
- Ollama installed and running
- At least 4GB of RAM available
- Port 8000, 8001, and 11434 available
- S3/CloudFront URL for image serving (configured in .env)

## Quick Start

### 1. Environment Setup

#### Step 1: Configure Environment Variables

Copy and configure the environment file:

```bash
# Copy the example environment file
cp .env.example .env

# Edit the .env file to ensure all required variables are set
nano .env
```

Your `.env` file should contain:

```bash
# Ollama Configuration
OLLAMA_HOST=http://localhost:11434
OLLAMA_VISION_MODEL=qwen2.5vl:7b
OLLAMA_TEXT_MODEL=qwen3
VISION_PORT=8001

# Storage & CDN
S3_BASE_URL=https://d29c1z66frfv6c.cloudfront.net/pub/media/catalog/product/large/

# Database Configuration
LOOKBOOK_DB_URL=sqlite:///lookbook.db
MYSQL_SHOP_URL=mysql+pymysql://lookbook_user:lookbook_password@localhost:3306/magento

# Application Settings
LOG_LEVEL=INFO
TZ=UTC
CORS_ORIGINS=http://localhost:3000,http://localhost:8080
LOG_FORMAT=json
LOG_FILE=/var/log/lookbook-mpc.log
```

#### Step 2: Start Ollama (LLM Service)

```bash
# Start Ollama daemon in a terminal
ollama serve

# In another terminal, pull the required models (if not already installed)
ollama pull qwen2.5vl
ollama pull qwen3:4b  # Use 4B variant for faster inference

# Verify models are available
ollama list
```

#### Step 3: Start Vision Sidecar Service

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

#### Step 4: Start Main API Service

```bash
# In another terminal, in the project directory
poetry run python main.py
```

The main API will be available at `http://localhost:8000`

### 2. Accessing the Application

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
- `GET /v1/recommendations/similar/{item_id}` - Get similar outfits

##### Chat

- `POST /v1/chat` - Chat interaction
- `GET /v1/chat/sessions` - List chat sessions
- `GET /v1/chat/sessions/{session_id}` - Get session details
- `GET /v1/chat/suggestions` - Get chat suggestions

##### Images

- `GET /v1/images/{image_key}` - Get image with transformations
- `GET /v1/images/{image_key}/redirect` - Redirect to original image
- `HEAD /v1/images/{image_key}` - Check image existence
- `GET /v1/images/info/{image_key}` - Get image information

### 3. Using the Demo Interface

1. Open your browser and go to: `http://localhost:8000/demo`
2. Type fashion requests like:
   - "I want to do yoga"
   - "Restaurant this weekend, attractive for $50"
   - "I am fat, look slim"
3. The AI will analyze your request and show outfit recommendations

### 4. Project Structure

The project is organized with static files and assets in dedicated directories:

- **`docs/`**: Contains documentation files like `demo.html` and user guides
- **`assets/images/`**: Contains image files like `cos-chat.png` and `cos-chat2.png`
- **`scripts/`**: Contains utility and test scripts
- **`lookbook_mpc/`**: Main application code
- **`tests/`**: Test files
- **`migrations/`**: Database migration files

### 4. Testing the Setup

#### Verify All Services are Running

```bash
# Check Ollama service
curl http://localhost:11434/api/tags

# Check Vision Sidecar service
curl http://localhost:8001/health

# Check Main API service
curl http://localhost:8000/health

# Check Readiness probe (tests all dependencies)
curl http://localhost:8000/ready
```

#### Test Vision Sidecar (Optional)

```bash
# Health check
curl http://localhost:8001/health

# Test image analysis (replace with actual image URL)
curl -X POST "http://localhost:8001/analyze" \
  -H "Content-Type: application/json" \
  -d '{"image_url": "https://images.unsplash.com/photo-1551698618-1dfe5d97d256"}'
```

#### Test Main API

```bash
# Health check
curl http://localhost:8000/health

# Test readiness probe (includes S3 and Ollama checks)
curl http://localhost:8000/ready

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

# Test image serving (with actual image from S3)
curl -I "https://d29c1z66frfv6c.cloudfront.net/pub/media/catalog/product/large/3a4db8e6cba0f753558e37db7eae09614adbbf28_xxl-1.jpg"
```

#### Run Comprehensive Test Suite

```bash
# Run all tests
poetry run pytest

# Run tests with verbose output
poetry run pytest -v

# Run tests with coverage
poetry run pytest --cov=lookbook_mpc --cov-report=html

# Run specific test categories
poetry run pytest -m unit          # Run only unit tests
poetry run pytest -m integration   # Run only integration tests
poetry run pytest -m "not slow"    # Skip slow tests

# Run individual test files
poetry run pytest tests/test_api_integration.py
poetry run pytest tests/test_domain_entities.py
poetry run pytest tests/test_services.py
```

## Configuration

### Environment Variables

| Variable              | Description             | Default                     |
| --------------------- | ----------------------- | --------------------------- |
| `MYSQL_SHOP_URL`      | MySQL connection string | -                           |
| `LOOKBOOK_DB_URL`     | Lookbook database URL   | `sqlite:///lookbook.db`     |
| `OLLAMA_HOST`         | Ollama daemon URL       | `http://localhost:11434`    |
| `OLLAMA_VISION_MODEL` | Vision model name       | `qwen2.5vl:7b`              |
| `OLLAMA_TEXT_MODEL`   | Text model name         | `qwen3:4b` (faster)         |
| `S3_BASE_URL`         | S3 base URL             | -                           |
| `LOG_LEVEL`           | Logging level           | `INFO`                      |
| `CORS_ORIGINS`        | Allowed CORS origins    | `http://localhost:3000`     |
| `LOG_FORMAT`          | Log format              | `json`                      |
| `LOG_FILE`            | Log file path           | `/var/log/lookbook-mpc.log` |

### Service Ports

| Service        | Port  | Description                        |
| -------------- | ----- | ---------------------------------- |
| Main API       | 8000  | FastAPI application with endpoints |
| Vision Sidecar | 8001  | Image analysis service             |
| Ollama         | 11434 | LLM and vision model server        |
| Demo UI        | 8000  | Web interface at /demo.html        |

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

#### 6. Readiness probe returns 503 Service Unavailable

```bash
# The readiness probe checks all dependencies
# If it returns 503, check individual services:

# Check Ollama
curl http://localhost:11434/api/tags

# Check S3 image access (test with actual image)
curl -I "https://d29c1z66frfv6c.cloudfront.net/pub/media/catalog/product/large/3a4db8e6cba0f753558e37db7eae09614adbbf28_xxl-1.jpg"

# Check database
curl http://localhost:8000/health

# If S3 is not accessible, the readiness probe will still work
# but mark S3 as "unreachable" rather than failing the entire check
```

#### 7. CORS issues in development

```bash
# The system now has simplified CORS configuration
# If you're seeing CORS errors, check your .env file:

# Ensure CORS_ORIGINS is set to your frontend URL
echo $CORS_ORIGINS

# For development, you can use:
export CORS_ORIGINS=http://localhost:3000,http://localhost:8080
```

#### 8. Request ID headers missing

```bash
# The system now includes request ID middleware
# All responses should include an X-Request-ID header

curl -I http://localhost:8000/health
# Look for "x-request-id" in the response headers
```

### Health Checks

Monitor service health:

```bash
# Check basic health
curl http://localhost:8000/health

# Check readiness with dependency checks
curl http://localhost:8000/ready

# Check individual services
curl http://localhost:11434/api/tags
curl http://localhost:8001/health

# Check request IDs in responses
curl -H "X-Request-ID: test-123" http://localhost:8000/health
```

### Debug Mode

Enable debug logging for troubleshooting:

```bash
# Set debug logging
export LOG_LEVEL=DEBUG

# Start services with debug output
poetry run python main.py
poetry run python vision_sidecar.py

# Or run with uvicorn for development
poetry run uvicorn main:app --reload --log-level debug
```

## Development

### Running Tests

```bash
# Run all tests using pytest
poetry run pytest

# Run tests with coverage
poetry run pytest --cov=lookbook_mpc

# Run specific test categories
poetry run pytest -m unit          # Run only unit tests
poetry run pytest -m integration   # Run only integration tests
poetry run pytest -m "not slow"    # Skip slow tests

# Running individual test scripts
poetry run python scripts/test_api.py
poetry run python scripts/test_recommender.py
poetry run python scripts/test_demo.py
```

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
- Debug Guide: `DEBUG_GUIDE.md`
- Test Scripts: `scripts/test_*.py`

---

_This user guide covers the essential information needed to start, test, and use the Lookbook-MPC system. For more detailed information about specific components or advanced configuration, refer to the project's README.md and source code documentation._
