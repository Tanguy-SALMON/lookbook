# Lookbook-MPC Implementation Plan - Step 1 (M1: Scaffold + Quality)

## Overview

This document outlines the implementation of Step 1 from the `.lookbook.PRP` - M1 (Scaffold + quality). This milestone establishes the foundation for the FastAPI-based recommendation microservice.

## Technical Requirements

Based on `.lookbook.PRD` and `.lookbook.PRP`:

### Core Stack

- **Framework**: FastAPI + Pydantic + SQLAlchemy + Alembic
- **LLMs**: Ollama (qwen2.5-vl:7b for vision, qwen3 for intent parsing)
- **Architecture**: Clean Architecture (ports/adapters)
- **Database**: SQLite by default (switchable via URL)
- **MCP**: Model Context Protocol compatibility

### Directory Structure (CNS)

```
lookbook-mpc/
├── lookbook_mpc/
│   ├── domain/
│   │   ├── entities.py
│   │   └── use_cases.py
│   ├── adapters/
│   │   ├── db_shop.py
│   │   ├── db_lookbook.py
│   │   ├── vision.py
│   │   ├── intent.py
│   │   └── images.py
│   ├── services/
│   │   ├── rules.py
│   │   └── recommender.py
│   └── api/
│       ├── routers/
│       │   ├── ingest.py
│       │   ├── reco.py
│       │   ├── chat.py
│       │   └── images.py
│       └── mcp_server.py
├── migrations/
├── tests/
├── scripts/
├── .env.example
└── main.py
```

## Implementation Tasks

### M1.1 - FastAPI App Structure with pyproject.toml

**Objective**: Create the complete Python project structure with proper dependencies

**Files to create**:

- `pyproject.toml` - Project configuration and dependencies
- `main.py` - FastAPI application entry point
- `requirements.txt` - Python dependencies
- `.gitignore` - Git ignore rules

**Dependencies**:

```toml
[tool.poetry]
name = "lookbook-mpc"
version = "0.1.0"
description = "Fashion lookbook recommendation microservice"
authors = ["Your Name <your.email@example.com>"]

[tool.poetry.dependencies]
python = "^3.11"
fastapi = "^0.104.1"
uvicorn = {extras = ["standard"], version = "^0.24.0"}
pydantic = "^2.5.0"
sqlalchemy = "^2.0.23"
alembic = "^1.12.1"
python-multipart = "^0.0.6"
requests = "^2.31.0"
pillow = "^10.1.0"
langchain-ollama = "^0.0.1"
httpx = "^0.25.2"
structlog = "^23.2.0"
python-dotenv = "^1.0.0"

[tool.poetry.group.dev.dependencies]
ruff = "^0.1.6"
black = "^23.11.0"
mypy = "^1.7.1"
pytest = "^7.4.3"
pytest-asyncio = "^0.21.1"
pytest-cov = "^4.1.0"
httpx = "^0.25.2"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
```

### M1.2 - Development Tools Setup

**Objective**: Configure code quality and testing tools

**Configuration files**:

- `ruff.toml` - Ruff linter configuration
- `.black` - Black formatter configuration
- `mypy.ini` - MyPy type checker configuration
- `pytest.ini` - PyTest configuration

### M1.3 - Environment Configuration

**Objective**: Create environment configuration and documentation

**Files to create**:

- `.env.example` - Template with required environment variables
- `.env` - Local environment (gitignored)

**Environment Variables**:

```env
# Database Configuration
MYSQL_SHOP_URL=mysql+pymysql://user:pass@localhost:3306/magento
LOOKBOOK_DB_URL=sqlite:///lookbook.db

# Ollama Configuration
OLLAMA_HOST=http://localhost:11434
OLLAMA_VISION_MODEL=qwen2.5-vl:7b
OLLAMA_TEXT_MODEL=qwen3:4b  # Use 4B variant for faster inference

# S3 Configuration
S3_BASE_URL=https://your-s3-bucket.s3.amazonaws.com

# Application Configuration
TZ=UTC
LOG_LEVEL=INFO
```

### M1.4 - Health Endpoints

**Objective**: Implement health check endpoints for monitoring

**Endpoints**:

- `GET /health` - Basic health check
- `GET /ready` - Readiness probe with dependency checks

### M1.5 - CNS Directory Structure

**Objective**: Create the canonical naming and structure

**Directories**:

- `lookbook_mpc/` - Main package
- `lookbook_mpc/domain/` - Domain entities and use cases
- `lookbook_mpc/adapters/` - Infrastructure adapters
- `lookbook_mpc/services/` - Business logic services
- `lookbook_mpc/api/` - API layer
- `migrations/` - Database migrations
- `tests/` - Test files
- `scripts/` - Utility scripts

### M1.6 - Logging with Request IDs

**Objective**: Set up structured logging with request correlation

**Features**:

- Request ID generation and propagation
- Structured logging with `structlog`
- Log format with timestamps, request ID, and level
- Context-aware logging

### M1.7 - Domain Modules

**Objective**: Create empty domain modules with basic structure

**Files**:

- `lookbook_mpc/domain/entities.py` - Domain entities
- `lookbook_mpc/domain/use_cases.py` - Use case definitions

### M1.8 - Adapter Modules

**Objective**: Create empty adapter modules

**Files**:

- `lookbook_mpc/adapters/db_shop.py` - Shop database adapter
- `lookbook_mpc/adapters/db_lookbook.py` - Lookbook database adapter
- `lookbook_mpc/adapters/vision.py` - Vision analysis adapter
- `lookbook_mpc/adapters/intent.py` - Intent parsing adapter
- `lookbook_mpc/adapters/images.py` - Image handling adapter

### M1.9 - Service Modules

**Objective**: Create empty service modules

**Files**:

- `lookbook_mpc/services/rules.py` - Rules engine
- `lookbook_mpc/services/recommender.py` - Recommendation engine

### M1.10 - API Router Modules

**Objective**: Create empty API router modules

**Files**:

- `lookbook_mpc/api/routers/ingest.py` - Ingestion endpoints
- `lookbook_mpc/api/routers/reco.py` - Recommendation endpoints
- `lookbook_mpc/api/routers/chat.py` - Chat endpoints
- `lookbook_mpc/api/routers/images.py` - Image endpoints
- `lookbook_mpc/api/mcp_server.py` - MCP server implementation

### M1.11 - Basic Project Configuration

**Objective**: Set up basic project configuration files

**Files**:

- `.gitignore` - Git ignore rules
- `README.md` - Project documentation
- `Dockerfile` - Container configuration (optional for M1)

### M1.12 - Basic Tests

**Objective**: Validate setup with basic tests

**Test files**:

- `tests/test_main.py` - Basic application tests
- `tests/test_health.py` - Health endpoint tests
- `tests/conftest.py` - Test configuration

## Success Criteria

- [ ] FastAPI application starts successfully
- [ ] All dependencies are properly configured
- [ ] Health endpoints return correct responses
- [ ] Directory structure follows CNS conventions
- [ ] Code passes linting and type checking
- [ ] Basic tests pass
- [ ] Environment configuration is complete

## Next Steps

After completing M1, the next milestone will be M2 (Domain entities) where we'll implement the Pydantic/SQLAlchemy models for Item, Outfit, Rule, etc.

## Notes

- This implementation follows the Clean Architecture principles
- All configuration should be environment-driven
- No hardcoded credentials or secrets
- Focus on testability and maintainability
