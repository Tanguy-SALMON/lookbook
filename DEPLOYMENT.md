# Lookbook-MPC Deployment Guide

This guide explains how to deploy the Lookbook-MPC system using Docker Compose.

## Prerequisites

- Docker and Docker Compose installed
- At least 4GB of RAM available
- Port 8000, 8001, 8002, and 11434 available

## Quick Start

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd lookbook-mpc
   ```

2. **Configure environment**

   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Run the deployment script**

   ```bash
   ./scripts/deploy.sh setup
   ./scripts/deploy.sh start
   ```

4. **Access the application**
   - API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - Demo UI: http://localhost/demo
   - Health Check: http://localhost:8000/health

## Detailed Deployment Steps

### 1. Setup

```bash
./scripts/deploy.sh setup
```

This command will:

- Check prerequisites (Docker, Docker Compose)
- Create necessary directories (logs, ssl, data)
- Check environment variables

### 2. Environment Configuration

Edit the `.env` file with your configuration:

```bash
# Required variables
OLLAMA_HOST=http://localhost:11434
OLLAMA_VISION_MODEL=qwen2.5-vl:7b
OLLAMA_TEXT_MODEL=qwen3:4b  # Use 4B variant for faster inference
S3_BASE_URL=https://your-s3-bucket.s3.amazonaws.com

# Optional variables
LOOKBOOK_DB_URL=sqlite:///./lookbook.db
MYSQL_SHOP_URL=mysql+pymysql://user:password@localhost:3306/magento_db
LOG_LEVEL=INFO
TZ=UTC
```

### 3. Build and Deploy

```bash
# Pull pre-built images (recommended)
./scripts/deploy.sh pull

# Or build from scratch
./scripts/deploy.sh build

# Initialize database
./scripts/deploy.sh init-db

# Start all services
./scripts/deploy.sh start
```

### 4. Verify Deployment

```bash
# Check service health
./scripts/deploy.sh health

# View service status
./scripts/deploy.sh status

# View logs
./scripts/deploy.sh logs
```

## Service Architecture

The system consists of the following services:

### 1. Ollama (Port 11434)

- Provides LLM models for vision analysis and intent parsing
- Models: qwen2.5-vl:7b (vision), qwen3 (text)
- Health check: http://localhost:11434/api/tags

### 2. API Service (Port 8000)

- FastAPI-based recommendation microservice
- Provides REST API and MCP server
- Health check: http://localhost:8000/health

### 3. Vision Sidecar (Port 8001)

- Separate service for image analysis
- Wraps VisionAnalyzer with Ollama integration
- Health check: http://localhost:8001/health

### 4. Nginx (Port 80) - Optional

- Reverse proxy for load balancing and SSL termination
- Rate limiting and security headers
- Only enabled with `--profile nginx`

## Environment Variables

### Required Variables

- `OLLAMA_HOST`: Ollama service URL
- `OLLAMA_VISION_MODEL`: Vision model name (qwen2.5-vl:7b)
- `OLLAMA_TEXT_MODEL`: Text model name (qwen3:4b for faster inference)
- `S3_BASE_URL`: Base URL for S3 image storage

### Optional Variables

- `LOOKBOOK_DB_URL`: Database URL (default: SQLite)
- `MYSQL_SHOP_URL`: Magento database URL
- `LOG_LEVEL`: Logging level (INFO, DEBUG, etc.)
- `TZ`: Timezone
- `CORS_ORIGINS`: Allowed CORS origins
- `VISION_SIDECAR_HOST`: Vision sidecar URL
- `MCP_HOST`: MCP server host
- `MCP_PORT`: MCP server port

## Development Mode

For development, you can run individual services:

```bash
# Start Ollama
docker-compose up -d ollama

# Start API service
docker-compose up -d api

# Start vision sidecar
docker-compose up -d vision
```

## Production Deployment

### 1. Security Considerations

- Use strong passwords for database connections
- Configure SSL/TLS certificates
- Set up proper CORS policies
- Implement API authentication
- Use environment variables for sensitive data

### 2. Performance Optimization

- Increase Docker memory limits
- Use persistent volumes for data
- Configure proper logging levels
- Monitor resource usage
- Set up health checks and alerts

### 3. Scaling

- Add multiple API service instances
- Use load balancing
- Implement caching with Redis
- Use database connection pooling

## Troubleshooting

### Common Issues

1. **Ollama models not loaded**

   ```bash
   # Check available models
   curl http://localhost:11434/api/tags

   # Pull models manually
   docker exec -it lookbook-ollama ollama pull qwen2.5-vl:7b
   docker exec -it lookbook-ollama ollama pull qwen3
   ```

2. **Database connection issues**

   ```bash
   # Check database logs
   docker-compose logs api

   # Reinitialize database
   ./scripts/deploy.sh init-db
   ```

3. **Vision service not responding**

   ```bash
   # Check vision service logs
   docker-compose logs vision

   # Restart vision service
   docker-compose restart vision
   ```

### Debug Mode

Enable debug logging:

```bash
# Set debug level
export LOG_LEVEL=DEBUG

# Restart services
./scripts/deploy.sh restart
```

### Health Checks

Monitor service health:

```bash
# Check all services
./scripts/deploy.sh health

# Check specific service
curl http://localhost:8000/health
curl http://localhost:11434/api/tags
curl http://localhost:8001/health
```

## Backup and Recovery

### Database Backup

```bash
# Backup SQLite database
cp lookbook.db lookbook.db.backup

# Backup with timestamp
cp lookbook.db lookbook.db.$(date +%Y%m%d_%H%M%S).backup
```

### Configuration Backup

```bash
# Backup environment configuration
cp .env .env.backup

# Backup Docker Compose files
cp docker-compose.yml docker-compose.yml.backup
```

## Monitoring and Logging

### Log Locations

- API logs: `logs/api.log`
- Vision logs: `logs/vision.log`
- Nginx logs: `/var/log/nginx/`
- Docker logs: `docker-compose logs [service]`

### Monitoring Tools

- **Docker Stats**: `docker stats`
- **Prometheus**: Configure with Docker metrics
- **Grafana**: Create dashboards for monitoring
- **ELK Stack**: For centralized logging

## Support

For issues and questions:

- Check the troubleshooting section
- Review the logs for error messages
- Open an issue on GitHub
- Contact the development team

## License

This project is licensed under the MIT License. See the LICENSE file for details.
