# Lookbook MPC Tests

This directory contains comprehensive tests for the Lookbook MPC system, following a **Python-first testing approach** that aligns with our architecture principles.

## Testing Philosophy

Our testing strategy reflects the system architecture:
- **Python backend**: Contains all business logic, API endpoints, and data processing
- **Next.js frontend**: Pure UI interface that proxies requests to Python backend
- **Testing focus**: Comprehensive backend testing with lightweight frontend testing

## Test Files Overview

### `test_api_architecture.py` 🏗️
**Purpose**: Tests the overall system architecture and API integration
- Database schema and data integrity
- API endpoint availability and responses  
- Frontend-backend integration points
- Error handling and edge cases
- Performance and concurrent request handling

### `test_api_integration.py` 🔗
**Purpose**: Integration tests for specific API endpoints
- Ingestion API endpoints (`/v1/ingest/*`)
- Recommendation API endpoints (`/v1/recommendations/*`)
- Chat API endpoints (`/v1/chat/*`)
- Image serving endpoints (`/v1/images/*`)
- Health and monitoring endpoints

### `test_domain_entities.py` 📦
**Purpose**: Tests for domain entities and business logic
- Entity validation and constraints
- Data model consistency
- Business rule enforcement

### `test_services.py` ⚙️
**Purpose**: Tests for service layer components
- Rules engine functionality
- Recommendation algorithms
- Data transformation logic

### `test_main.py` 🚀
**Purpose**: Tests for main application setup and configuration
- Application startup and initialization
- Configuration management
- Dependency injection

### `conftest.py` 🔧
**Purpose**: Shared test configuration and fixtures
- Test environment setup
- Mock data generation
- Common utilities

## Running Tests

### Run All Tests
```bash
cd test-roocode
poetry run pytest
```

### Run Specific Test Files
```bash
# Architecture and integration tests
poetry run pytest tests/test_api_architecture.py -v

# API endpoint tests
poetry run pytest tests/test_api_integration.py -v

# Domain logic tests
poetry run pytest tests/test_domain_entities.py -v
```

### Run Tests with Coverage
```bash
poetry run pytest --cov=lookbook_mpc --cov-report=html
```

### Run Tests in Parallel
```bash
poetry run pytest -n auto  # Requires pytest-xdist
```

## Test Categories

### 🔍 **Architecture Tests** (`test_api_architecture.py`)
- **Database Integration**: SQLite schema, data consistency, connection handling
- **API Architecture**: Endpoint availability, response formats, error handling
- **Frontend Integration**: CORS, JSON responses, request/response formats
- **Performance**: Response times, concurrent request handling
- **Configuration**: Environment variables, database connections

### 🌐 **API Integration Tests** (`test_api_integration.py`)
- **Ingestion Endpoints**: Item listing, deletion, statistics
- **Recommendation Endpoints**: Outfit generation, constraints handling
- **Chat Endpoints**: Conversational interface, session management
- **Image Endpoints**: Image serving, transformations, redirects
- **Health Endpoints**: Service health, readiness checks

### 🧪 **Unit Tests** (Other files)
- **Domain Entities**: Data validation, business rules
- **Services**: Algorithm correctness, data processing
- **Utilities**: Helper functions, data transformations

## Test Data Strategy

### Real Database Testing
- Tests run against the actual SQLite database (`lookbook.db`)
- Verifies real data consistency and API responses
- Tests database schema and migrations

### Mock Data Usage
- External services (Ollama, S3) are mocked in test environment
- Business logic tests use controlled mock data
- Isolated testing of individual components

### Test Environment Setup
```python
# Test environment variables are configured in conftest.py
@pytest.fixture
def test_env():
    test_vars = {
        "OLLAMA_HOST": "http://localhost:11434",
        "OLLAMA_VISION_MODEL": "qwen2.5-vl:7b",
        "OLLAMA_TEXT_MODEL": "qwen3:4b",
        "S3_BASE_URL": "https://test-cdn.example.com",
        "LOG_LEVEL": "DEBUG",
    }
```

## Frontend Testing Approach

### Why Minimal Frontend Testing?
- **Architecture**: Frontend is a pure UI proxy to Python backend
- **Logic Location**: No business logic in JavaScript to test
- **Integration**: Backend tests cover API integration points
- **Efficiency**: Focus testing efforts where logic exists (Python)

### Frontend Test Coverage
- **UI Component Testing**: Basic rendering and interaction
- **Navigation Testing**: Route handling and page loading  
- **Integration Testing**: Covered by backend API tests
- **Manual Testing**: Architecture test page for visual verification

## CI/CD Integration

### Recommended Test Pipeline
```yaml
# Example GitHub Actions workflow
test:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v3
    - uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    - run: poetry install
    - run: poetry run pytest tests/ --cov=lookbook_mpc
    - run: poetry run pytest tests/test_api_architecture.py -v
```

## Test Best Practices

### 1. **Test the Architecture, Not Just Code**
```python
def test_frontend_backend_integration(client, db_path):
    """Test that API responses match database data."""
    # This tests the entire data flow from DB → API → Frontend
```

### 2. **Focus on Integration Points**
```python
def test_items_data_consistency(client, db_path):
    """Verify API responses match database state."""
    # Tests the critical integration between components
```

### 3. **Test Real Scenarios**
```python
def test_concurrent_requests_handling(client):
    """Test API can handle multiple concurrent requests."""
    # Tests realistic usage patterns
```

### 4. **Validate Configuration**
```python
def test_required_environment_variables():
    """Test that required environment variables are considered."""
    # Tests system configuration and setup
```

## Debugging Failed Tests

### Common Issues and Solutions

**Database Connection Errors**
```bash
# Check database exists and is accessible
ls -la lookbook.db
sqlite3 lookbook.db ".tables"
```

**API Endpoint Not Found (404)**
```bash
# Verify Python backend is running
curl http://localhost:8000/health
curl http://localhost:8000/v1/ingest/items
```

**Environment Configuration Issues**
```bash
# Check required environment variables
poetry run python -c "import os; print('OLLAMA_HOST:', os.getenv('OLLAMA_HOST'))"
```

**Mock Data Issues**
```bash
# Run tests with verbose output to see mock data
poetry run pytest tests/test_api_integration.py::TestIngestEndpoints -v -s
```

## Contributing

When adding new features:

1. **Add API tests** for new endpoints in `test_api_integration.py`
2. **Add architecture tests** for new integration points in `test_api_architecture.py`
3. **Add unit tests** for new business logic in appropriate test files
4. **Update this README** if adding new test categories or approaches

## Test Metrics and Goals

- **Coverage Target**: >80% for Python backend code
- **Performance Target**: API responses <2s in test environment
- **Integration Target**: All critical user flows tested end-to-end
- **Architecture Target**: All API endpoints and database operations tested

The goal is **confidence in the system architecture** through comprehensive testing of the Python backend where all the logic resides, while keeping frontend testing focused on UI functionality.