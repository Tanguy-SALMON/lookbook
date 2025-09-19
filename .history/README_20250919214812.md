# Lookbook-MPC

Fashion lookbook recommendation microservice with vision analysis and intent parsing.

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

## Quick Start

### Prerequisites

- Python 3.11+
- Ollama running with models: `qwen2.5-vl:7b` and `qwen3`
- Optional: MySQL database for Magento integration

### Installation

1. Clone the repository:

```bash
git clone <repository-url>
cd lookbook-mpc
```

2. Install dependencies:

```bash
pip install -e .
```

3. Set up environment:

```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Run the application:

```bash
python main.py
```

The API will be available at `http://localhost:8000`

### API Documentation

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Architecture

```
lookbook-mpc/
├── lookbook_mpc/
│   ├── domain/          # Domain entities and use cases
│   ├── adapters/        # Infrastructure adapters
│   ├── services/       # Business logic services
│   └── api/            # API layer and MCP server
├── migrations/          # Database migrations
├── tests/              # Test files
└── scripts/            # Utility scripts
```

### Core Components

#### Domain Layer

- **Entities**: Item, Outfit, Rule, Intent
- **Use Cases**: IngestItems, RecommendOutfits, ChatTurn

#### Adapters Layer

- **db_shop**: Magento catalog adapter
- **db_lookbook**: Lookbook database adapter
- **vision**: Vision analysis adapter
- **intent**: Intent parsing adapter
- **images**: Image handling adapter

#### Services Layer

- **rules**: Fashion recommendation rules engine
- **recommender**: Outfit composition and scoring

#### API Layer

- **routers**: RESTful API endpoints
- **mcp_server**: Model Context Protocol server

## API Endpoints

### Ingestion

- `POST /v1/ingest/items` - Ingest items from catalog
- `GET /v1/ingest/status/{request_id}` - Check ingestion status
- `GET /v1/ingest/items` - List ingested items
- `GET /v1/ingest/stats` - Get ingestion statistics

### Recommendations

- `POST /v1/recommendations` - Generate outfit recommendations
- `GET /v1/recommendations/preview` - Preview recommendations
- `GET /v1/recommendations/constraints` - Get constraint options
- `GET /v1/recommendations/popular` - Get popular recommendations
- `GET /v1/recommendations/trending` - Get trending recommendations
- `GET /v1/recommendations/similar/{item_id}` - Get similar outfits

### Chat

- `POST /v1/chat` - Chat interaction
- `GET /v1/chat/sessions` - List chat sessions
- `GET /v1/chat/sessions/{session_id}` - Get session details
- `GET /v1/chat/suggestions` - Get chat suggestions

### Images

- `GET /v1/images/{image_key}` - Get image with transformations
- `GET /v1/images/{image_key}/redirect` - Redirect to original image
- `HEAD /v1/images/{image_key}` - Check image existence
- `GET /v1/images/info/{image_key}` - Get image information

### Health

- `GET /health` - Basic health check
- `GET /ready` - Readiness probe

## MCP Integration

The service exposes MCP tools and resources for LLM client integration:

### Available Tools

- `recommend_outfits(query, budget?, size?)` - Generate outfit recommendations
- `search_items(filters)` - Search catalog items
- `ingest_batch(limit?)` - Ingest items from catalog

### Available Resources

- `openapi` - OpenAPI specification
- `rules_catalog` - Fashion recommendation rules
- `schemas` - JSON schemas for API models

## Configuration

### Environment Variables

| Variable              | Description             | Default                  |
| --------------------- | ----------------------- | ------------------------ |
| `MYSQL_SHOP_URL`      | MySQL connection string | -                        |
| `LOOKBOOK_DB_URL`     | Lookbook database URL   | `sqlite:///lookbook.db`  |
| `OLLAMA_HOST`         | Ollama daemon URL       | `http://localhost:11434` |
| `OLLAMA_VISION_MODEL` | Vision model name       | `qwen2.5-vl:7b`          |
| `OLLAMA_TEXT_MODEL`   | Text model name         | `qwen3`                  |
| `S3_BASE_URL`         | S3 base URL             | -                        |
| `LOG_LEVEL`           | Logging level           | `INFO`                   |

### Development

```bash
# Run with auto-reload
uvicorn main:app --reload

# Run tests
pytest

# Format code
black .

# Lint code
ruff check .

# Type check
mypy .
```

## Development Tools

### Code Quality

- **Ruff**: Fast Python linter and formatter
- **Black**: Opinionated Python code formatter
- **MyPy**: Static type checker
- **Pytest**: Test framework

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=lookbook_mpc

# Run specific test file
pytest tests/test_main.py
```

## Deployment

### Docker Compose (Development)

```yaml
version: "3.8"
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - OLLAMA_HOST=http://ollama:11434
    depends_on:
      - ollama

  ollama:
    image: ollama/ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    command: ["serve"]

volumes:
  ollama_data:
```

### Production

1. Set up environment variables
2. Configure database
3. Set up reverse proxy (Nginx)
4. Configure SSL/TLS
5. Set up monitoring and logging

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run quality checks
6. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For support and questions:

- Create an issue in the repository
- Check the documentation
- Review the API endpoints
