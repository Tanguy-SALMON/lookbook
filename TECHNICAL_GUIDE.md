# Technical Guide
# Lookbook-MPC Fashion Recommendation System

Complete technical documentation for developers, system administrators, and advanced users.

## 🏗️ System Architecture

### High-Level Architecture
```
[Client Apps] → [Nginx Proxy] → [Next.js Dashboard:3000]
                                ↓
[Chat Interface] → [Main API:8000] → [Vision Sidecar:8001] → [Ollama:11434]
                         ↓                    ↓                     ↓
                   [MySQL Database]    [Image Analysis]      [AI Models]
                   [Session Storage]   [Product Attributes]  [qwen2.5vl/qwen3]
```

### Component Breakdown

**Main API (FastAPI)**
- REST endpoints for recommendations, chat, product management
- Business logic and rules engine
- Database interactions and session management
- MCP (Model Context Protocol) server
- Health monitoring and metrics collection

**Vision Sidecar (FastAPI)**
- Dedicated service for image analysis
- Ollama integration for vision models
- Product attribute extraction
- Image processing and caching

**Admin Dashboard (Next.js)**
- Real-time system monitoring
- Analytics visualization
- Administrative controls
- User management interface

**Database Layer (MySQL)**
- Product catalog with Thai market data
- User sessions and chat history
- System metrics and analytics
- Configuration and rules storage

## 🔧 Technical Implementation

### Core Technologies

**Backend Stack**
```python
# Core dependencies
FastAPI==0.104.1          # Web framework
Pydantic==2.5.0           # Data validation
SQLAlchemy==2.0.23        # Database ORM
Ollama-Python==0.1.7     # AI model integration
Structlog==23.2.0         # Structured logging
```

**Frontend Stack**
```javascript
// Package.json dependencies
"next": "15.0.0",         // React framework
"react": "18.2.0",        // UI library
"tailwindcss": "3.4.0",  // Styling
"shadcn/ui": "latest",    // Component library
"lucide-react": "0.294.0" // Icons
```

### Database Schema

**Products Table**
```sql
CREATE TABLE products (
    id INT PRIMARY KEY AUTO_INCREMENT,
    sku VARCHAR(50) UNIQUE NOT NULL,
    title VARCHAR(500) NOT NULL,
    price DECIMAL(10,2) NOT NULL COMMENT 'Thai Baht',
    color VARCHAR(100),
    material VARCHAR(100),
    season VARCHAR(50),
    category VARCHAR(100),
    image_key VARCHAR(500),
    url_key VARCHAR(500),
    stock_qty INT DEFAULT 0,
    in_stock BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_sku (sku),
    INDEX idx_category (category),
    INDEX idx_color (color),
    INDEX idx_price (price)
);
```

**Chat Sessions**
```sql
CREATE TABLE chat_sessions (
    session_id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(100),
    context JSON,
    strategy JSON COMMENT 'AI persona and objectives',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_user_id (user_id),
    INDEX idx_created_at (created_at)
);
```

**Product Attributes (Vision Analysis Results)**
```sql
CREATE TABLE product_vision_attributes (
    id INT PRIMARY KEY AUTO_INCREMENT,
    product_id INT,
    dominant_colors JSON,
    materials JSON,
    style_tags JSON,
    pattern_info JSON,
    confidence_scores JSON,
    analysis_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id),
    INDEX idx_product_id (product_id)
);
```

## 🤖 AI Integration

### Model Configuration

**Text Generation (qwen3:4b-instruct)**
```python
# Recommended settings for optimal performance
MODEL_CONFIG = {
    "model": "qwen3:4b-instruct",
    "temperature": 0.3,           # Balanced creativity/consistency
    "num_predict": 256,           # Token limit for speed
    "top_p": 0.9,                # Nucleus sampling
    "repeat_penalty": 1.05,       # Avoid repetition
    "num_thread": 8,              # Match CPU cores
    "timeout": 15.0               # Prevent long waits
}
```

**Vision Analysis (qwen2.5vl)**
```python
# Vision model configuration
VISION_CONFIG = {
    "model": "qwen2.5vl",
    "temperature": 0.2,           # Lower for consistent analysis
    "num_predict": 192,           # Shorter responses for attributes
    "format": "json",             # Structured output
    "timeout": 30.0               # Vision processing takes longer
}
```

### Recommendation Algorithm

**Multi-Factor Scoring System**
```python
def calculate_outfit_score(outfit: Outfit, user_context: dict) -> float:
    """
    Comprehensive scoring algorithm for outfit recommendations
    """
    base_score = 0.0
    
    # Style compatibility (40% weight)
    style_score = calculate_style_compatibility(outfit.items)
    base_score += style_score * 0.4
    
    # Occasion appropriateness (25% weight)
    occasion_score = match_occasion(outfit, user_context.get('occasion'))
    base_score += occasion_score * 0.25
    
    # Budget fit (20% weight)
    budget_score = calculate_budget_fit(outfit.total_price, user_context.get('budget'))
    base_score += budget_score * 0.2
    
    # Color harmony (10% weight)
    color_score = analyze_color_harmony(outfit.items)
    base_score += color_score * 0.1
    
    # Seasonal appropriateness (5% weight)
    season_score = match_season(outfit, user_context.get('season'))
    base_score += season_score * 0.05
    
    return min(base_score, 1.0)  # Cap at 1.0
```

### Intent Parsing Pipeline

**Natural Language Understanding**
```python
class LLMIntentParser:
    def parse_intent(self, text: str) -> IntentResult:
        system_prompt = """
        Analyze fashion-related requests and extract:
        1. Occasion (work, casual, formal, sports, etc.)
        2. Preferred colors or color families
        3. Budget constraints if mentioned
        4. Style preferences (modern, classic, trendy)
        5. Specific item types requested
        6. Generate a natural, helpful response
        
        Respond in JSON format with these fields:
        - occasion: string
        - colors: list
        - budget_max: number (Thai Baht)
        - style: string
        - items: list
        - natural_response: string
        """
        
        # Send to Ollama for processing
        response = self.ollama_client.generate(
            model="qwen3:4b-instruct",
            prompt=f"{system_prompt}\n\nUser request: {text}",
            **MODEL_CONFIG
        )
        
        return self.parse_json_response(response)
```

## 🔐 Security Implementation

### Input Validation
```python
from pydantic import BaseModel, validator
from typing import Optional, List

class ChatRequest(BaseModel):
    session_id: str
    message: str
    budget_max: Optional[float] = None
    
    @validator('message')
    def validate_message(cls, v):
        if len(v.strip()) == 0:
            raise ValueError('Message cannot be empty')
        if len(v) > 1000:
            raise ValueError('Message too long')
        return v.strip()
    
    @validator('budget_max')
    def validate_budget(cls, v):
        if v is not None and v < 0:
            raise ValueError('Budget must be positive')
        return v
```

### SQL Injection Prevention
```python
# Use parameterized queries exclusively
def get_products_by_category(category: str, limit: int = 10):
    query = """
    SELECT id, sku, title, price, color, image_key 
    FROM products 
    WHERE category = %s AND in_stock = TRUE
    ORDER BY created_at DESC
    LIMIT %s
    """
    return db.execute(query, (category, limit)).fetchall()

# NEVER use string formatting for SQL
# BAD: f"SELECT * FROM products WHERE category = '{category}'"
# GOOD: Use parameterized queries as shown above
```

### Environment Variable Security
```python
# Secure environment configuration
import os
from typing import Optional

class Settings:
    # Database (never commit real credentials)
    MYSQL_HOST: str = os.getenv('MYSQL_HOST', 'localhost')
    MYSQL_USER: str = os.getenv('MYSQL_USER', 'lookbook_user')
    MYSQL_PASSWORD: str = os.getenv('MYSQL_PASSWORD')  # Required
    MYSQL_DATABASE: str = os.getenv('MYSQL_DATABASE', 'lookbookMPC')
    
    # AI Services
    OLLAMA_HOST: str = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
    OLLAMA_TEXT_MODEL: str = os.getenv('OLLAMA_TEXT_MODEL', 'qwen3:4b-instruct')
    OLLAMA_VISION_MODEL: str = os.getenv('OLLAMA_VISION_MODEL', 'qwen2.5vl')
    
    # CDN and Storage
    S3_BASE_URL: str = os.getenv('S3_BASE_URL', '')
    
    def validate(self):
        if not self.MYSQL_PASSWORD:
            raise ValueError("MYSQL_PASSWORD environment variable required")
```

## 📊 Performance Optimization

### Database Optimization

**Query Performance**
```sql
-- Optimize product searches with proper indexing
EXPLAIN SELECT p.*, pva.dominant_colors, pva.style_tags 
FROM products p
LEFT JOIN product_vision_attributes pva ON p.id = pva.product_id
WHERE p.category = 'dresses' 
  AND p.price BETWEEN 2000 AND 8000
  AND p.in_stock = TRUE
ORDER BY p.created_at DESC
LIMIT 20;

-- Ensure these indexes exist:
-- INDEX idx_category_price_stock ON products(category, price, in_stock)
-- INDEX idx_product_id ON product_vision_attributes(product_id)
```

**Connection Pooling**
```python
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

# Configure connection pool for production
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,           # Base connections
    max_overflow=20,        # Additional connections under load
    pool_pre_ping=True,     # Validate connections
    pool_recycle=3600,      # Refresh connections hourly
    echo=False              # Disable SQL logging in production
)
```

### Caching Strategy

**Redis Integration (Optional)**
```python
import redis
from typing import Optional
import json

class CacheManager:
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis = redis.from_url(redis_url)
    
    def get_recommendations(self, cache_key: str) -> Optional[dict]:
        """Get cached recommendations"""
        cached = self.redis.get(f"rec:{cache_key}")
        return json.loads(cached) if cached else None
    
    def set_recommendations(self, cache_key: str, data: dict, ttl: int = 300):
        """Cache recommendations for 5 minutes"""
        self.redis.setex(f"rec:{cache_key}", ttl, json.dumps(data))
    
    def get_product_attributes(self, product_id: int) -> Optional[dict]:
        """Get cached vision analysis results"""
        cached = self.redis.get(f"vision:{product_id}")
        return json.loads(cached) if cached else None
```

### Async Processing

**Background Tasks**
```python
from fastapi import BackgroundTasks
import asyncio

async def analyze_product_image_background(product_id: int):
    """Background task for vision analysis"""
    try:
        product = await get_product(product_id)
        if not product.image_key:
            return
        
        # Call vision sidecar
        vision_result = await vision_client.analyze_image(product.image_key)
        
        # Store results
        await save_vision_attributes(product_id, vision_result)
        
        logger.info(f"Vision analysis complete for product {product_id}")
        
    except Exception as e:
        logger.error(f"Vision analysis failed for product {product_id}: {e}")

@app.post("/v1/products/{product_id}/analyze")
async def trigger_analysis(product_id: int, background_tasks: BackgroundTasks):
    background_tasks.add_task(analyze_product_image_background, product_id)
    return {"message": "Analysis started", "product_id": product_id}
```

## 🚀 Deployment Configuration

### Production Docker Setup

**Dockerfile for Main API**
```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY pyproject.toml poetry.lock ./
RUN pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --only=main

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 lookbook && \
    chown -R lookbook:lookbook /app
USER lookbook

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000
CMD ["python", "main.py"]
```

**Docker Compose for Development**
```yaml
version: '3.8'

services:
  mysql:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: rootpassword
      MYSQL_DATABASE: lookbookMPC
      MYSQL_USER: lookbook_user
      MYSQL_PASSWORD: lookbook_pass
    volumes:
      - mysql_data:/var/lib/mysql
    ports:
      - "3306:3306"
    command: --sql-mode="STRICT_TRANS_TABLES,NO_ZERO_DATE,NO_ZERO_IN_DATE,ERROR_FOR_DIVISION_BY_ZERO"

  main-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      MYSQL_HOST: mysql
      MYSQL_USER: lookbook_user
      MYSQL_PASSWORD: lookbook_pass
      MYSQL_DATABASE: lookbookMPC
      OLLAMA_HOST: http://ollama:11434
    depends_on:
      - mysql
      - ollama

  vision-sidecar:
    build:
      context: .
      dockerfile: Dockerfile.vision
    ports:
      - "8001:8001"
    environment:
      OLLAMA_HOST: http://ollama:11434
    depends_on:
      - ollama

  dashboard:
    build:
      context: ./shadcn
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      NEXT_PUBLIC_API_URL: http://main-api:8000

  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama

volumes:
  mysql_data:
  ollama_data:
```

### Nginx Configuration

**Production Reverse Proxy**
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /etc/ssl/certs/your-cert.pem;
    ssl_certificate_key /etc/ssl/private/your-key.pem;
    
    # Admin Dashboard
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Main API
    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Increase timeouts for AI processing
        proxy_read_timeout 60s;
        proxy_connect_timeout 10s;
        proxy_send_timeout 60s;
    }
    
    # Vision Sidecar
    location /vision/ {
        proxy_pass http://127.0.0.1:8001/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Longer timeouts for vision processing
        proxy_read_timeout 120s;
        proxy_connect_timeout 10s;
        proxy_send_timeout 120s;
    }
    
    # Static files and images
    location /static/ {
        alias /var/www/lookbook/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

## 🔍 Monitoring and Logging

### Structured Logging

**Logger Configuration**
```python
import structlog
from structlog.processors import JSONRenderer
import logging

# Configure structured logging
logging.basicConfig(
    format="%(message)s",
    stream=sys.stdout,
    level=logging.INFO,
)

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.ConsoleRenderer() if DEBUG else JSONRenderer()
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()
```

**Usage in Code**
```python
# Rich contextual logging
logger.info(
    "recommendation_generated",
    session_id=session_id,
    user_query=query,
    outfit_count=len(outfits),
    total_price=sum(outfit.total_price for outfit in outfits),
    processing_time_ms=processing_time * 1000,
    model_used=model_name
)

logger.error(
    "vision_analysis_failed",
    product_id=product_id,
    image_key=image_key,
    error=str(e),
    retry_count=retry_count
)
```

### Health Monitoring

**Comprehensive Health Checks**
```python
from fastapi import HTTPException
import asyncio

class HealthChecker:
    async def check_database(self) -> dict:
        try:
            result = await db.execute("SELECT 1 as health")
            return {
                "status": "healthy",
                "response_time_ms": result.execution_time * 1000
            }
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    async def check_ollama(self) -> dict:
        try:
            response = await ollama_client.list_models()
            return {
                "status": "healthy",
                "models": len(response.get("models", [])),
                "available_models": [m["name"] for m in response.get("models", [])]
            }
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    async def check_vision_sidecar(self) -> dict:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get("http://localhost:8001/health", timeout=5.0)
                return {
                    "status": "healthy" if response.status_code == 200 else "unhealthy",
                    "status_code": response.status_code
                }
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

@app.get("/ready")
async def readiness_check():
    """Comprehensive readiness check for all dependencies"""
    health_checker = HealthChecker()
    
    checks = await asyncio.gather(
        health_checker.check_database(),
        health_checker.check_ollama(),
        health_checker.check_vision_sidecar(),
        return_exceptions=True
    )
    
    db_health, ollama_health, vision_health = checks
    
    all_healthy = all(
        check.get("status") == "healthy" 
        for check in [db_health, ollama_health, vision_health]
        if isinstance(check, dict)
    )
    
    return {
        "status": "ready" if all_healthy else "not_ready",
        "checks": {
            "database": db_health,
            "ollama": ollama_health,
            "vision_sidecar": vision_health
        },
        "timestamp": datetime.utcnow().isoformat()
    }
```

## 🧪 Testing Strategy

### Test Structure

**Test Categories**
```python
# Unit Tests
class TestRecommendationEngine:
    def test_outfit_scoring_algorithm(self):
        """Test the core recommendation scoring"""
        outfit = create_test_outfit()
        context = {"occasion": "work", "budget": 5000}
        
        score = calculate_outfit_score(outfit, context)
        
        assert 0.0 <= score <= 1.0
        assert score > 0.5  # Should be reasonable match

# Integration Tests  
class TestAPIIntegration:
    async def test_recommendation_flow(self):
        """Test complete recommendation pipeline"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/v1/recommendations",
                json={"text_query": "business meeting outfit"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert len(data["outfits"]) >= 1
            assert all(outfit["total_price"] > 0 for outfit in data["outfits"])

# Performance Tests
@pytest.mark.performance
def test_recommendation_performance():
    """Ensure recommendations complete within time limits"""
    start_time = time.time()
    
    result = generate_recommendations("casual dinner date")
    
    duration = time.time() - start_time
    assert duration < 10.0  # Should complete within 10 seconds
```

### Load Testing

**Basic Load Test Script**
```python
import asyncio
import aiohttp
import time

async def test_concurrent_requests():
    """Test system under concurrent load"""
    async def make_request(session, request_id):
        try:
            async with session.post(
                'http://localhost:8000/v1/recommendations',
                json={'text_query': f'outfit for request {request_id}'},
                timeout=30
            ) as response:
                return await response.json()
        except Exception as e:
            return {"error": str(e)}
    
    # Test with 20 concurrent requests
    async with aiohttp.ClientSession() as session:
        tasks = [
            make_request(session, i) 
            for i in range(20)
        ]
        
        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        duration = time.time() - start_time
        
        successful = sum(1 for r in results if isinstance(r, dict) and "outfits" in r)
        print(f"Load test: {successful}/20 requests successful in {duration:.2f}s")
```

## 🔄 Maintenance Procedures

### Database Maintenance

**Regular Maintenance Tasks**
```bash
#!/bin/bash
# Database maintenance script

# Optimize tables
mysql -u $MYSQL_USER -p$MYSQL_PASSWORD $MYSQL_DATABASE -e "
OPTIMIZE TABLE products;
OPTIMIZE TABLE product_vision_attributes;  
OPTIMIZE TABLE chat_sessions;
"

# Check for orphaned vision attributes
mysql -u $MYSQL_USER -p$MYSQL_PASSWORD $MYSQL_DATABASE -e "
DELETE pva FROM product_vision_attributes pva
LEFT JOIN products p ON pva.product_id = p.id
WHERE p.id IS NULL;
"

# Clean old chat sessions (older than 30 days)
mysql -u $MYSQL_USER -p$MYSQL_PASSWORD $MYSQL_DATABASE -e "
DELETE FROM chat_sessions 
WHERE created_at < DATE_SUB(NOW(), INTERVAL 30 DAY);
"
```

### Model Updates

**Update AI Models Script**
```bash
#!/bin/bash
# Update Ollama models

echo "Updating Ollama models..."

# Pull latest versions
ollama pull qwen3:4b-instruct
ollama pull qwen2.5vl

# Verify models are working
echo "Testing text model..."
ollama run qwen3:4b-instruct --prompt "Hello" --num-predict 10

echo "Testing vision model..."
ollama run qwen2.5vl --prompt "Describe this image" --num-predict 20

echo "Model update complete"
```

### System Monitoring

**Monitoring Script**
```python
#!/usr/bin/env python3
"""System monitoring and alerting"""

import requests
import time
import smtplib
from email.mime.text import MIMEText

def check_service_health():
    services = {
        "main_api": "http://localhost:8000/health",
        "vision_sidecar": "http://localhost:8001/health", 
        "ollama": "http://localhost:11434/api/tags"
    }
    
    results = {}
    for name, url in services.items():
        try:
            response = requests.get(url, timeout=10)
            results[name] = {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds()
            }
        except Exception as e:
            results[name] = {
                "status": "down",
                "error": str(e)
            }
    
    return results

def send_alert_if_needed(results):
    unhealthy = [name for name, result in results.items() 
                if result["status"] != "healthy"]
    
    if unhealthy:
        message = f"Services down: {', '.join(unhealthy)}"
        # Send email, Slack notification, etc.
        print(f"ALERT: {message}")

if __name__ == "__main__":
    while True:
        results = check_service_health()
        send_alert_if_needed(results)
        time.sleep(300)  # Check every 5 minutes
```

---

## 📚 Additional Resources

### API Documentation
- **OpenAPI Spec**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Endpoints**: http://localhost:8000/health, /ready

### Development Tools
- **Poetry**: Python dependency management
- **Pytest**: Testing framework
- **Black**: Code formatting
- **Ruff**: Fast Python linter
- **MyPy**: Static type checking

### External Documentation
- **FastAPI**: https://fastapi.tiangolo.com/
- **Ollama**: https://ollama.ai/docs
- **Next.js**: https://nextjs.org/docs
- **shadcn/ui**: https://ui.shadcn.com/docs

---

**Status**: Production Ready  
**Last Updated**: December 2024  
**Maintainer**: Lookbook-MPC Development Team