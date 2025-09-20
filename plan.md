# Lookbook-MPC Project Plan

## Overview

Lookbook-MPC is a FastAPI-based fashion recommendation microservice with AI vision analysis and intent parsing.

## Architecture

### Tech Stack
- **Backend**: FastAPI + Pydantic + SQLAlchemy
- **AI Models**: Ollama (qwen2.5vl for vision, qwen3:4b for text)
- **Frontend**: Next.js admin dashboard
- **Database**: SQLite (configurable)
- **Integration**: MCP (Model Context Protocol)

### Directory Structure
```
lookbook-mpc/
├── lookbook_mpc/           # Core Python application
│   ├── domain/            # Business entities and use cases
│   ├── adapters/          # External integrations (DB, Vision, etc.)
│   ├── services/          # Business logic services
│   └── api/               # REST API and MCP server
├── shadcn/                # Next.js admin dashboard
├── migrations/            # Database migrations
├── tests/                 # Test suite
└── scripts/               # Utility scripts
```

## Core Components

### Domain Layer
- **Entities**: Item, Outfit, Rule, Intent
- **Use Cases**: Product ingestion, recommendation generation, chat interaction

### Services Layer
- **Vision Analysis**: Extract fashion attributes from images
- **Intent Parsing**: Understand user requests in natural language
- **Rules Engine**: Apply fashion coordination rules
- **Recommender**: Generate outfit combinations

### API Layer
- **Product Management**: `/v1/ingest/products` - CRUD operations
- **Recommendations**: `/v1/recommendations` - Generate outfits
- **Chat Interface**: `/v1/chat` - Conversational interaction
- **Image Serving**: `/v1/images` - CDN proxy with transformations

## Key Features

### AI-Powered Recommendations
- Natural language query processing
- Vision-based product attribute extraction
- Fashion rules engine for outfit coordination
- Context-aware suggestions (occasion, budget, style)

### Admin Dashboard
- Real-time system monitoring
- Product catalog management with comprehensive attribute editing
- Analytics and performance metrics
- Chat session management

### Integration Capabilities
- Magento catalog integration
- S3/CloudFront image serving
- MCP protocol for LLM clients
- RESTful API for external systems

## Development Workflow

### Setup
1. Start Ollama with required models
2. Launch Vision Sidecar service
3. Start Main API service
4. Run Admin Dashboard (optional)

### Testing
- Comprehensive test suite with pytest
- API integration tests
- Component-level unit tests
- Performance benchmarking

### Quality Assurance
- Type checking with mypy
- Code formatting with black
- Linting with ruff
- Automated testing pipeline

## Deployment

### Development
- Local development with auto-reload
- Docker Compose for service orchestration
- Environment-based configuration

### Production
- Docker containerization
- Health checks and monitoring
- Scalable service architecture
- Performance optimization

## Success Metrics

### Technical
- API response times < 2s for recommendations
- 95%+ uptime for all services
- Comprehensive test coverage
- Zero critical security vulnerabilities

### Functional
- Accurate fashion attribute extraction from images
- Relevant outfit recommendations based on user intent
- Intuitive admin interface for system management
- Seamless integration with external systems

This plan provides a clear roadmap for building a production-ready fashion recommendation system with modern architecture patterns and AI capabilities.