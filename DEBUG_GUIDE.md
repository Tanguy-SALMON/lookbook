# Lookbook-MPC Debug Guide

This comprehensive debugging guide provides detailed information for developers and system administrators to troubleshoot, optimize, and debug the Lookbook-MPC system.

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Performance Benchmarking](#performance-benchmarking)
3. [Component Debugging](#component-debugging)
4. [Logging and Monitoring](#logging-and-monitoring)
5. [Common Issues and Solutions](#common-issues-and-solutions)
6. [Advanced Configuration](#advanced-configuration)
7. [Development Tools](#development-tools)

## System Architecture

### Component Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Demo UI/Web   │    │   Main API      │    │  Vision Sidecar │
│   (Port 8000)   │◄──►│   (Port 8000)   │◄──►│   (Port 8001)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                       │
                                ▼                       ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   Ollama       │    │   Ollama       │
                       │   (Port 11434) │    │   (Port 11434) │
                       └─────────────────┘    └─────────────────┘
                                │                       │
                                ▼                       ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   LLM Models    │    │   Vision Model  │
                       │   (qwen3:4b)    │    │   (qwen2.5vl)   │
                       └─────────────────┘    └─────────────────┘
```

### Data Flow

1. **User Request** → Demo UI or API
2. **Intent Parsing** → Extract fashion requirements using qwen3:4b
3. **Catalog Query** → Fetch items from Magento database
4. **Vision Analysis** → Analyze images using qwen2.5vl
5. **Rule Engine** → Apply fashion recommendation rules
6. **Outfit Assembly** → Combine items into complete outfits
7. **Response Generation** → Create recommendations with rationales

## Performance Benchmarking

### Overview

The benchmark system compares `qwen3:4b` vs `qwen3` models to determine the optimal configuration for your use case.

### Running Benchmarks

#### Quick Start

```bash
# Install benchmark requirements
pip install -r requirements-benchmark.txt

# Run comprehensive benchmark
./scripts/run_benchmark.sh

# Or run manually
poetry run python scripts/benchmark_models.py --models qwen3:4b qwen3
```

#### Advanced Benchmarking

```bash
# Benchmark with custom settings
poetry run python scripts/benchmark_models.py \
  --models qwen3:4b qwen3 \
  --repeat 20 \
  --temperature 0.7 \
  --max-tokens 500

# Single model detailed analysis
poetry run python scripts/benchmark_models.py --models qwen3:4b --repeat 50

# Custom prompts for specific use cases
poetry run python scripts/benchmark_models.py \
  --models qwen3:4b \
  --prompts "Business meeting outfit" "Beach vacation clothes" "Winter formal wear"

# Test different temperature settings
for temp in 0.1 0.3 0.5 0.7 0.9; do
  poetry run python scripts/benchmark_models.py \
    --models qwen3:4b \
    --temperature $temp \
    --repeat 10
done
```

### Benchmark Metrics

#### Performance Metrics

- **Response Time**: Mean, median, std dev, P95, P99
- **Throughput**: Tokens per second
- **Resource Usage**: CPU, memory, GPU utilization
- **System Load**: Comprehensive system monitoring

#### Quality Metrics

- **Relevance Score**: 0-1 scale based on fashion keywords
- **Coherence**: Structure and flow assessment
- **Grammar**: Basic grammar and spelling checks
- **Response Length**: Character and token counts

#### Variability Analysis

- **Cross-prompt consistency**: Performance across different prompts
- **Run-to-run consistency**: Repeatability testing
- **Standard deviation tracking**: Performance stability

#### Reliability Metrics

- **Success Rate**: Percentage of successful completions
- **Error Analysis**: Pattern recognition in failures
- **Timeout Handling**: Graceful failure management

### Ollama Parameter Testing

The benchmark evaluates these key parameters:

| Parameter           | Default | Description           | Impact                                             |
| ------------------- | ------- | --------------------- | -------------------------------------------------- |
| `temperature`       | 0.7     | Response randomness   | Higher = more creative, lower = more deterministic |
| `top_p`             | 0.9     | Nucleus sampling      | Controls diversity of next token selection         |
| `repeat_penalty`    | 1.1     | Repetition prevention | Higher = less repetitive text                      |
| `presence_penalty`  | 0.0     | Topic encouragement   | Higher = encourages new topics                     |
| `frequency_penalty` | 0.0     | Word repetition       | Higher = discourages frequent words                |
| `num_predict`       | 1000    | Token limit           | Maximum tokens to generate                         |

### Benchmark Results Analysis

#### Generated Files

- `{model}_results_{timestamp}.json` - Raw benchmark data
- `{model}_analysis_{timestamp}.json` - Statistical analysis
- `{model}_summary_{timestamp}.txt` - Human-readable summary
- `model_comparison_{timestamp}.json` - Multi-model comparison

#### Key Performance Indicators

1. **Response Time**: < 2s for good performance
2. **Tokens/Second**: > 50 tokens/sec for good throughput
3. **Success Rate**: > 95% for reliability
4. **Quality Score**: > 0.7 for good recommendations
5. **Memory Usage**: < 2GB per request for efficiency

#### Interpreting Results

```bash
# View detailed results
cat benchmark_results/qwen3_4b_analysis_*.json | jq '.performance_metrics'

# Compare models
cat benchmark_results/model_comparison_*.json | jq '.[] | {model: .model_name, mean_time: .performance_metrics.response_time.mean, quality: .quality_metrics.quality_score.mean}'

# View summary report
cat benchmark_results/qwen3_4b_summary_*.txt
```

### Performance Optimization

Based on benchmark results, consider these optimizations:

1. **Model Selection**: Use `qwen3:4b` for faster inference if quality is acceptable
2. **Temperature Tuning**: Lower temperature (0.3-0.5) for more consistent responses
3. **Batch Processing**: Process multiple requests when possible
4. **Caching**: Cache frequent queries and responses
5. **Resource Allocation**: Increase memory/CPU for larger models

## Component Debugging

### Main API Service (Port 8000)

#### Debug Mode

```bash
# Run with debug logging
export LOG_LEVEL=DEBUG
poetry run python main.py

# Or with uvicorn
poetry run uvicorn main:app --reload --log-level debug
```

#### Health Checks

```bash
# Basic health check
curl http://localhost:8000/health

# Detailed readiness check
curl http://localhost:8000/ready

# Check request IDs and tracing
curl -H "X-Request-ID: test-123" http://localhost:8000/health
```

#### API Endpoint Debugging

```bash
# Test individual endpoints with verbose output
curl -v http://localhost:8000/health

# Test with request headers
curl -H "Content-Type: application/json" \
     -H "X-Request-ID: debug-001" \
     -d '{"limit": 5}' \
     http://localhost:8000/v1/ingest/items

# View response headers
curl -I http://localhost:8000/health
```

### Vision Sidecar (Port 8001)

#### Debug Mode

```bash
# Run vision sidecar with debug logging
export LOG_LEVEL=DEBUG
poetry run python vision_sidecar.py

# Test vision analysis directly
curl -X POST "http://localhost:8001/analyze" \
  -H "Content-Type: application/json" \
  -d '{"image_url": "https://images.unsplash.com/photo-1551698618-1dfe5d97d256"}' \
  -v
```

#### Vision Analysis Debugging

```bash
# Test with different image formats
curl -X POST "http://localhost:8001/analyze" \
  -H "Content-Type: application/json" \
  -d '{"image_url": "https://example.com/image.jpg"}'

# Test with base64 encoded image
curl -X POST "http://localhost:8001/analyze" \
  -H "Content-Type: application/json" \
  -d '{"image_base64": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="}'

# Check vision service health
curl http://localhost:8001/health
```

### Ollama Service (Port 11434)

#### Debug Mode

```bash
# Check Ollama status
curl http://localhost:11434/api/tags

# Check model details
curl http://localhost:11434/api/show -d '{"name": "qwen3:4b"}'

# Test model directly
curl http://localhost:11434/api/generate -d '{
  "model": "qwen3:4b",
  "prompt": "Hello, how are you?",
  "stream": false
}'
```

#### Model Management

```bash
# Pull specific models
ollama pull qwen2.5vl:7b
ollama pull qwen3:4b

# List available models
ollama list

# Remove models
ollama rm qwen3
ollama rm qwen2.5vl

# Check model information
ollama show qwen3:4b
```

## Logging and Monitoring

### Structured Logging

The system uses structured logging with JSON format for better debugging:

```bash
# View API logs
tail -f logs/api.log

# View vision service logs
tail -f logs/vision.log

# Filter by request ID
grep "request_id=test-123" logs/api.log

# Filter by error level
grep "level=ERROR" logs/api.log

# View specific component logs
grep "component=vision" logs/api.log
```

### Request Tracing

Each request has a unique ID for tracing:

```bash
# Check request ID in response headers
curl -I http://localhost:8000/health

# Log with request ID
curl -H "X-Request-ID: trace-001" http://localhost:8000/health
```

### Performance Monitoring

```bash
# Monitor system resources
htop

# Monitor memory usage
free -h

# Monitor disk usage
df -h

# Monitor network connections
netstat -tulpn | grep :8000
```

### Custom Logging Configuration

```python
# Set log level in environment
export LOG_LEVEL=DEBUG

# Set log format
export LOG_FORMAT=json

# Set log file location
export LOG_FILE=/var/log/lookbook-mpc.log
```

## Common Issues and Solutions

### Service Startup Issues

#### 1. Port Already in Use

```bash
# Check which process is using the port
lsof -i :8000
lsof -i :8001
lsof -i :11434

# Kill the process
kill -9 <PID>

# Or change the port in the code
# In main.py: uvicorn.run("main:app", host="0.0.0.0", port=8001)
```

#### 2. Missing Dependencies

```bash
# Install missing Python packages
poetry install

# Or install specific packages
poetry install fastapi uvicorn structlog

# Check Python version
python --version  # Should be 3.11+
```

#### 3. Environment Variables Missing

```bash
# Check required environment variables
echo $OLLAMA_HOST
echo $OLLAMA_VISION_MODEL
echo $OLLAMA_TEXT_MODEL
echo $S3_BASE_URL

# Set missing variables
export OLLAMA_HOST=http://localhost:11434
export OLLAMA_VISION_MODEL=qwen2.5vl
export OLLAMA_TEXT_MODEL=qwen3:4b
export S3_BASE_URL=https://your-s3-bucket.s3.amazonaws.com
```

### API Issues

#### 1. 422 Validation Errors

```bash
# Check request format
curl -X POST "http://localhost:8000/v1/ingest/items" \
  -H "Content-Type: application/json" \
  -d '{"limit": 5}'  # Correct format

# Wrong format (will fail)
curl -X POST "http://localhost:8000/v1/ingest/items?limit=5"
```

#### 2. 500 Internal Server Errors

```bash
# Check logs for error details
tail -f logs/api.log | grep "ERROR"

# Enable debug mode
export LOG_LEVEL=DEBUG
poetry run python main.py

# Test with verbose curl
curl -v http://localhost:8000/v1/recommendations \
  -H "Content-Type: application/json" \
  -d '{"text_query": "test"}'
```

#### 3. Timeout Issues

```bash
# Increase timeout for slow requests
curl -m 30 http://localhost:8000/v1/recommendations \
  -H "Content-Type: application/json" \
  -d '{"text_query": "complex query"}'

# Check Ollama timeout settings
# In main.py, adjust the timeout in readiness check
```

### Model Issues

#### 1. Model Not Found

```bash
# Check available models
ollama list

# Pull missing models
ollama pull qwen2.5vl:7b
ollama pull qwen3:4b

# Verify model names
ollama show qwen3:4b
```

#### 2. Slow Model Response

```bash
# Test model directly
curl -m 10 http://localhost:11434/api/generate -d '{
  "model": "qwen3:4b",
  "prompt": "Hello",
  "stream": false
}'

# Check system resources
htop
nvidia-smi  # If using GPU

# Consider using smaller model
# Change OLLAMA_TEXT_MODEL to qwen3:4b if using larger qwen3
```

#### 3. Model Quality Issues

```bash
# Test with different temperature
curl http://localhost:11434/api/generate -d '{
  "model": "qwen3:4b",
  "prompt": "I want to do yoga",
  "options": {"temperature": 0.3}
}'

# Adjust prompt engineering
# Be more specific in fashion queries
```

## Advanced Configuration

### Environment Configuration

#### Development Environment

```bash
# .env file for development
OLLAMA_HOST=http://localhost:11434
OLLAMA_VISION_MODEL=qwen2.5vl:7b
OLLAMA_TEXT_MODEL=qwen3:4b
S3_BASE_URL=https://dev-cdn.example.com
LOOKBOOK_DB_URL=sqlite:///dev_lookbook.db
LOG_LEVEL=DEBUG
```

#### Production Environment

```bash
# .env file for production
OLLAMA_HOST=http://ollama-service:11434
OLLAMA_VISION_MODEL=qwen2.5vl:7b
OLLAMA_TEXT_MODEL=qwen3:4b
S3_BASE_URL=https://cdn.example.com
LOOKBOOK_DB_URL=postgresql://user:pass@db:5432/lookbook
LOG_LEVEL=INFO
CORS_ORIGINS=https://example.com
```

### Docker Configuration

#### Development Docker Compose

```yaml
# docker-compose.dev.yml
version: "3.8"
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - LOG_LEVEL=DEBUG
      - OLLAMA_HOST=http://host.docker.internal:11434
    volumes:
      - ./logs:/app/logs
      - ./.env:/app/.env
```

#### Production Docker Compose

```yaml
# docker-compose.prod.yml
version: "3.8"
services:
  api:
    build:
      context: .
      dockerfile: Dockerfile.prod
    ports:
      - "8000:8000"
    environment:
      - LOG_LEVEL=INFO
      - OLLAMA_HOST=http://ollama:11434
    depends_on:
      - ollama
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### Performance Tuning

#### Memory Optimization

```bash
# Set memory limits in Docker
docker run -m 2g lookbook-mpc

# Adjust Python memory limits
export PYTHONMALLOC=malloc
export MALLOC_ARENA_MAX=2
```

#### Concurrency Settings

```python
# In main.py, adjust uvicorn settings
uvicorn.run(
    "main:app",
    host="0.0.0.0",
    port=8000,
    workers=4,  # Number of worker processes
    limit_concurrency=100,  # Max concurrent requests
    timeout_keep_alive=30,  # Connection timeout
)
```

#### Database Optimization

```python
# For SQLite, consider WAL mode
# In database initialization
from sqlalchemy import event
from sqlalchemy import create_engine

@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.close()
```

## Development Tools

### Code Quality

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

### Testing

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=lookbook_mpc --cov-report=html

# Run specific test file
poetry run pytest tests/test_api_integration.py

# Run tests with markers
poetry run pytest -m unit
poetry run pytest -m integration
poetry run pytest -m "not slow"

# Run tests with verbose output
poetry run pytest -v

# Run tests with stop on first failure
poetry run pytest -x
```

### Debugging Tools

```bash
# Install debugging tools
pip install ipython pdb++

# Run with debugger
python -m pdb main.py

# Use ipython for interactive debugging
ipython -m pdb main.py

# Debug specific test
pytest tests/test_api_integration.py -pdb
```

### Profiling

```bash
# Profile API performance
python -m cProfile -o profile.stats main.py

# Analyze profile results
python -m pstats profile.stats

# Use line profiler
pip install line_profiler
kernprof -l -v main.py
```

### API Testing

```bash
# Test API with httpie
http POST localhost:8000/v1/recommendations \
  text_query="I want to do yoga" \
  budget:=80 \
  size:=L

# Test with different content types
curl -X POST localhost:8000/v1/recommendations \
  -H "Content-Type: application/json" \
  -d '{"text_query": "test"}'

# Test with authentication
curl -X POST localhost:8000/v1/recommendations \
  -H "Authorization: Bearer token" \
  -H "Content-Type: application/json" \
  -d '{"text_query": "test"}'
```

---

This debug guide provides comprehensive information for troubleshooting, optimizing, and developing the Lookbook-MPC system. For user-facing documentation, refer to `USER_GUIDE.md`.

## Project Structure

The project is organized with static files and assets in dedicated directories to keep the app runtime clean:

- **`docs/`**: Contains documentation files like `demo.html` and user guides
- **`assets/images/`**: Contains image files like `cos-chat.png` and `cos-chat2.png`
- **`scripts/`**: Contains utility and test scripts
- **`lookbook_mpc/`**: Main application code
- **`tests/`**: Test files
- **`migrations/`**: Database migration files

This organization ensures that the root directory remains clean and focused on runtime files only.
