# Lookbook-MPC Setup Guide

This guide provides step-by-step instructions to set up and run the Lookbook-MPC system. Follow these steps in order to ensure everything works correctly.

## Prerequisites

Before starting, make sure you have:

- Python 3.11+ installed
- Ollama installed and running
- At least 4GB of RAM available
- Ports 8000, 8001, and 11434 available
- A text editor (like VS Code, nano, or vim)

## Step 1: Clone and Navigate to Project

```bash
# Navigate to the project directory
cd /Users/tanguysalmon/PythonPlayGround/test-roocode

# Verify you're in the right directory
pwd
ls -la
```

## Step 2: Configure Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit the environment file
nano .env
```

Your `.env` file should contain these settings:

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

## Step 3: Start Ollama Service

Open **Terminal 1** and run:

```bash
# Start Ollama daemon
ollama serve

# You should see output like:
# INFO[0000] using existing socket at /var/run/ollama.sock
# listening on 127.0.0.1:11434
```

Keep this terminal open and running.

## Step 4: Pull Required Models

Open **Terminal 2** and run:

```bash
# Pull the vision model
ollama pull qwen2.5vl

# Pull the text model (4B variant for faster inference)
ollama pull qwen3:4b

# Verify models are available
ollama list

# You should see both models in the list
```

## Step 5: Start Vision Sidecar Service

Open **Terminal 3** and run:

```bash
# Navigate to project directory (if not already there)
cd /Users/tanguysalmon/PythonPlayGround/test-roocode

# Start the vision analysis service
poetry run python vision_sidecar.py

# You should see output like:
# INFO:     Started server process [PID]
# INFO:     Waiting for application startup.
# INFO:     Application startup complete.
# INFO:     Uvicorn running on http://0.0.0.0:8001 (Press CTRL+C to quit)
```

Keep this terminal open and running.

## Step 6: Start Main API Service

Open **Terminal 4** and run:

```bash
# Navigate to project directory (if not already there)
cd /Users/tanguysalmon/PythonPlayGround/test-roocode

# Start the main API service
poetry run python main.py

# You should see output like:
# INFO:     Started server process [PID]
# INFO:     Waiting for application startup.
# INFO:     Application startup complete.
# INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

Keep this terminal open and running.

## Step 7: Verify Services are Running

Open **Terminal 5** and run these verification commands:

```bash
# Check Ollama service
echo "=== Checking Ollama ==="
curl http://localhost:11434/api/tags

# Check Vision Sidecar service
echo -e "\n=== Checking Vision Sidecar ==="
curl http://localhost:8001/health

# Check Main API service
echo -e "\n=== Checking Main API ==="
curl http://localhost:8000/health

# Check Readiness probe (tests all dependencies)
echo -e "\n=== Checking Readiness Probe ==="
curl http://localhost:8000/ready

# Test image serving
echo -e "\n=== Testing Image Access ==="
curl -I "https://d29c1z66frfv6c.cloudfront.net/pub/media/catalog/product/large/3a4db8e6cba0f753558e37db7eae09614adbbf28_xxl-1.jpg"
```

You should see successful responses from all services.

## Step 8: Test the API Endpoints

```bash
# Test basic API functionality
echo "=== Testing API Endpoints ==="

# Test recommendations endpoint
curl -X POST "http://localhost:8000/v1/recommendations" \
  -H "Content-Type: application/json" \
  -d '{"text_query": "I want to do yoga"}'

# Test ingestion endpoint
curl -X POST "http://localhost:8000/v1/ingest/items" \
  -H "Content-Type: application/json" \
  -d '{"limit": 5}'

# Test chat endpoint
curl -X POST "http://localhost:8000/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test-session", "message": "Hello"}'
```

## Step 9: Access the Web Interface

Open your browser and navigate to:

- **API Documentation**: http://localhost:8000/docs
- **Alternative API Documentation**: http://localhost:8000/redoc
- **Demo Chat Interface**: http://localhost:8000/demo

## Step 10: Run the Test Suite

```bash
# Run all tests
echo "=== Running Test Suite ==="
poetry run pytest

# Run tests with verbose output
poetry run pytest -v

# Run tests with coverage
poetry run pytest --cov=lookbook_mpc --cov-report=html

# Run specific test files
poetry run pytest tests/test_api_integration.py
poetry run pytest tests/test_domain_entities.py
poetry run pytest tests/test_services.py
```

All tests should pass (117/117).

## Step 11: Test Individual Components

```bash
# Test vision sidecar directly
echo "=== Testing Vision Sidecar ==="
curl -X POST "http://localhost:8001/analyze" \
  -H "Content-Type: application/json" \
  -d '{"image_url": "https://images.unsplash.com/photo-1551698618-1dfe5d97d256"}'

# Test Ollama directly
echo -e "\n=== Testing Ollama ==="
curl -X POST "http://localhost:11434/api/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen3:4b",
    "prompt": "Hello, how are you?",
    "stream": false
  }'
```

## Troubleshooting Common Issues

### If services don't start:

1. **Port conflicts**: Check if ports are already in use

   ```bash
   lsof -i :8000
   lsof -i :8001
   lsof -i :11434
   ```

2. **Missing dependencies**: Install required packages

   ```bash
   pip install fastapi uvicorn structlog pydantic
   ```

3. **Environment variables**: Ensure all are set correctly
   ```bash
   echo $OLLAMA_HOST
   echo $S3_BASE_URL
   ```

### If tests fail:

1. **Readiness probe returns 503**: This is normal if S3 is not accessible
2. **Model not found**: Ensure Ollama models are pulled
3. **Database issues**: Check if `lookbook.db` exists

### If API endpoints fail:

1. **Check service health**: Use the health check endpoints
2. **Verify environment variables**: Ensure all are set
3. **Check logs**: Look for error messages in terminal output

## Daily Usage

### Starting the System

```bash
# Terminal 1: Ollama
ollama serve

# Terminal 2: Vision Sidecar
poetry run python vision_sidecar.py

# Terminal 3: Main API
poetry run python main.py
```

### Quick Health Checks

```bash
# Check all services
curl http://localhost:8000/health | jq
curl http://localhost:8000/ready | jq
curl http://localhost:8001/health | jq
curl http://localhost:11434/api/tags | jq
```

### Stopping the System

Press `Ctrl+C` in each terminal to stop the services.

## Next Steps

1. **Explore the API**: Use the documentation at http://localhost:8000/docs
2. **Try the demo**: Visit http://localhost:8000/demo
3. **Customize rules**: Edit recommendation rules in the code
4. **Add more data**: Ingest more products for better recommendations

## Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review the terminal output for error messages
3. Verify all services are running
4. Check the project documentation in `USER_GUIDE.md` and `DEBUG_GUIDE.md`

---

**Note**: This setup guide assumes you're running on a macOS system. If you're on a different OS, some commands may need to be adjusted.

