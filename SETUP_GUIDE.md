# Lookbook-MPC Setup Guide

This guide provides step-by-step instructions to set up and run the Lookbook-MPC system.

## Prerequisites

- Python 3.11+
- Ollama installed
- Node.js 18+ (for admin dashboard)
- 4GB+ RAM available
- Ports 8000, 8001, 11434, 3000 available

## Step-by-Step Setup

### 1. Project Setup

```bash
cd /Users/tanguysalmon/PythonPlayGround/test-roocode
```

### 2. Environment Configuration

```bash
# Copy example environment
cp .env.example .env

# Edit configuration
nano .env
```

Required `.env` settings:
```bash
OLLAMA_HOST=http://localhost:11434
OLLAMA_VISION_MODEL=qwen2.5vl
OLLAMA_TEXT_MODEL=qwen3:4b
S3_BASE_URL=https://d29c1z66frfv6c.cloudfront.net/pub/media/catalog/product/large/
LOOKBOOK_DB_URL=sqlite:///lookbook.db
LOG_LEVEL=INFO
```

### 3. Start Services in Order

**Terminal 1 - Ollama**
```bash
ollama serve
```

**Terminal 2 - Pull Models**
```bash
ollama pull qwen2.5vl
ollama pull qwen3:4b
ollama list  # Verify models
```

**Terminal 3 - Vision Sidecar**
```bash
python vision_sidecar.py
# Should show: Uvicorn running on http://0.0.0.0:8001
```

**Terminal 4 - Main API**
```bash
python main.py
# Should show: Uvicorn running on http://0.0.0.0:8000
```

**Terminal 5 - Admin Dashboard (Optional)**
```bash
cd shadcn
npm install
npm run dev
# Available at http://localhost:3000
```

### 4. Verify Installation

```bash
# Check all services
curl http://localhost:11434/api/tags    # Ollama
curl http://localhost:8001/health       # Vision Sidecar
curl http://localhost:8000/health       # Main API
curl http://localhost:8000/ready        # Full readiness check
```

### 5. Test the System

```bash
# Test recommendations
curl -X POST "http://localhost:8000/v1/recommendations" \
  -H "Content-Type: application/json" \
  -d '{"text_query": "I want to do yoga"}'

# Ingest products
curl -X POST "http://localhost:8000/v1/ingest/products" \
  -H "Content-Type: application/json" \
  -d '{"limit": 5}'
```

### 6. Run Test Suite

```bash
# All tests
pytest

# With coverage
pytest --cov=lookbook_mpc

# Specific test files
pytest tests/test_api_integration.py
```

## Access Points

- **API Documentation**: http://localhost:8000/docs
- **Demo Interface**: http://localhost:8000/demo
- **Admin Dashboard**: http://localhost:3000
- **Health Check**: http://localhost:8000/health

## Troubleshooting

### Services Won't Start

1. **Port conflicts**
   ```bash
   lsof -i :8000 :8001 :11434 :3000
   # Kill conflicting processes
   ```

2. **Missing models**
   ```bash
   ollama list  # Should show qwen2.5vl and qwen3:4b
   ```

3. **Environment variables**
   ```bash
   echo $OLLAMA_HOST
   cat .env  # Verify all variables set
   ```

### API Tests Fail

1. **Check service health**
   ```bash
   curl http://localhost:8000/ready
   ```

2. **Check logs**
   - Look for error messages in terminal output
   - Enable debug logging: `export LOG_LEVEL=DEBUG`

3. **Database issues**
   ```bash
   ls -la lookbook.db  # Should exist after first run
   ```

### No Recommendations

```bash
# Make sure products are ingested
curl -X POST "http://localhost:8000/v1/ingest/products?limit=10"

# Check ingestion stats
curl http://localhost:8000/v1/ingest/stats
```

## Daily Usage

### Starting System
```bash
# Start in 4 terminals:
ollama serve                    # Terminal 1
python vision_sidecar.py        # Terminal 2  
python main.py                  # Terminal 3
cd shadcn && npm run dev        # Terminal 4 (optional)
```

### Quick Health Check
```bash
curl http://localhost:8000/ready | jq
```

### Stopping System
Press `Ctrl+C` in each terminal.

## Next Steps

1. Explore the API documentation at http://localhost:8000/docs
2. Try the demo interface at http://localhost:8000/demo
3. Use the admin dashboard at http://localhost:3000
4. Review `DEBUG_GUIDE.md` for advanced troubleshooting
5. Check `DEPLOYMENT.md` for production setup

## Support

If issues persist:
1. Check troubleshooting section above
2. Verify all prerequisites are met
3. Review terminal output for specific errors
4. Consult `DEBUG_GUIDE.md` for detailed debugging