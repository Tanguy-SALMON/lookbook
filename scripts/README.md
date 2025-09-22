# Scripts Directory
# Lookbook-MPC Essential Scripts

This directory contains the essential scripts for Lookbook-MPC operations, testing, and benchmarking. The scripts have been consolidated and cleaned up from 50+ original files to this focused set.

## 📚 Script Categories

### 🚀 Benchmark Scripts (All Models)
Performance testing and model comparison tools.

- **[benchmark_models.py](benchmark_models.py)** - Main benchmark script with comprehensive metrics
- **[benchmark_models_anthropic.py](benchmark_models_anthropic.py)** - Anthropic Claude model benchmarks
- **[benchmark_models_fast.py](benchmark_models_fast.py)** - Fast streaming benchmark implementation
- **[benchmark_models_ollama.py](benchmark_models_ollama.py)** - Ollama-specific model benchmarks
- **[benchmark_models_openrouter.py](benchmark_models_openrouter.py)** - OpenRouter API benchmarks
- **[run_benchmark.py](run_benchmark.py)** - Benchmark runner with automation
- **[run_benchmark.sh](run_benchmark.sh)** - Shell script benchmark runner
- **[demo_both_benchmarks.py](demo_both_benchmarks.py)** - Compare different benchmark approaches
- **[OPENROUTER_BENCHMARK_README.md](OPENROUTER_BENCHMARK_README.md)** - Detailed benchmarking documentation

### 🧪 Testing Scripts
Core system testing and validation.

- **[test_api.py](test_api.py)** - Complete API endpoint testing suite
- **[test_chat_comprehensive.py](test_chat_comprehensive.py)** - Comprehensive chat system testing
- **[test_vision.py](test_vision.py)** - Vision analysis and sidecar testing
- **[test_recommender.py](test_recommender.py)** - Recommendation engine testing
- **[test_mcp.py](test_mcp.py)** - Model Context Protocol testing
- **[check_llm_status.py](check_llm_status.py)** - LLM service health checking

### 🗄️ Database & Data Scripts
Database operations and product management.

- **[init_db.py](init_db.py)** - Database initialization and setup
- **[init_db_mysql_tables.py](init_db_mysql_tables.py)** - MySQL table creation
- **[test_db_connections.py](test_db_connections.py)** - Database connection testing
- **[sync_100_products.py](sync_100_products.py)** - **CRITICAL** - Product sync from Magento
- **[verify_product_import.py](verify_product_import.py)** - Import verification and validation
- **[init_db_clean.sql](init_db_clean.sql)** - Clean database initialization SQL
- **[init_db_mysql.sql](init_db_mysql.sql)** - MySQL database initialization SQL

### 🚀 Deployment Scripts
Production deployment and operations.

- **[deploy.sh](deploy.sh)** - Deployment automation script

## 🎯 Quick Usage Guide

### Essential Daily Operations

```bash
# 1. Test database connections
poetry run python scripts/test_db_connections.py

# 2. Sync products from Magento
poetry run python scripts/sync_100_products.py

# 3. Verify import was successful
poetry run python scripts/verify_product_import.py

# 4. Test the API
poetry run python scripts/test_api.py

# 5. Test chat system
poetry run python scripts/test_chat_comprehensive.py
```

### Benchmark Operations

```bash
# Quick Ollama benchmark
poetry run python scripts/benchmark_models_ollama.py

# Comprehensive benchmarks (all models)
poetry run python scripts/run_benchmark.py

# Fast streaming benchmarks
poetry run python scripts/benchmark_models_fast.py
```

### Database Setup

```bash
# Initialize database from scratch
poetry run python scripts/init_db.py

# Create MySQL tables
poetry run python scripts/init_db_mysql_tables.py
```

## 📊 Script Descriptions

### Critical Scripts (Run These First)

#### `sync_100_products.py` ⭐
**Purpose**: Syncs products from Magento (cos-magento-4) to lookbookMPC database
**When to run**: Daily or when product catalog changes
**Requirements**: MYSQL_SHOP_URL and MYSQL_APP_URL configured
```bash
poetry run python scripts/sync_100_products.py
```

#### `test_db_connections.py` ⭐
**Purpose**: Validates both Magento and app database connections
**When to run**: Before any database operations, troubleshooting
```bash
poetry run python scripts/test_db_connections.py
```

#### `test_api.py` ⭐
**Purpose**: Tests all API endpoints (health, recommendations, chat)
**When to run**: After system startup, before production deployment
```bash
poetry run python scripts/test_api.py
```

### Benchmark Scripts (Performance Testing)

#### `benchmark_models.py`
**Purpose**: Comprehensive model performance testing with detailed metrics
**Features**: TTFT, throughput, quality scoring, system resource monitoring
**Usage**:
```bash
# Test specific models
poetry run python scripts/benchmark_models.py --models qwen3:4b qwen3 --repeat 3

# Custom prompts
poetry run python scripts/benchmark_models.py --prompts "Business outfit" "Casual wear"
```

#### `benchmark_models_fast.py`
**Purpose**: Fast streaming benchmarks optimized for speed
**Features**: Async streaming, connection reuse, minimal overhead
**Best for**: Quick performance checks

#### `benchmark_models_openrouter.py`
**Purpose**: Benchmark external API providers via OpenRouter
**Features**: Cost tracking, API comparison, external model testing
**Requirements**: OPENROUTER_API_KEY environment variable

### Testing Scripts (System Validation)

#### `test_chat_comprehensive.py`
**Purpose**: Complete chat system testing including LLM integration
**Coverage**: Intent parsing, recommendations, session management, error handling
**Usage**: Run after chat system changes or LLM model updates

#### `test_vision.py`
**Purpose**: Vision sidecar and image analysis testing
**Coverage**: Image processing, attribute extraction, Ollama vision integration
**Requirements**: Vision sidecar running on port 8001

#### `test_recommender.py`
**Purpose**: Recommendation engine testing and validation
**Coverage**: Outfit generation, scoring algorithms, rules engine
**Usage**: Run after recommendation logic changes

### Database Scripts

#### `init_db.py`
**Purpose**: Complete database initialization from scratch
**Features**: Creates tables, indexes, sample data
**When to run**: First setup, database reset
**Warning**: Destructive operation - will drop existing data

#### `init_db_mysql_tables.py`
**Purpose**: MySQL-specific table creation
**Features**: Creates production-ready schema with proper indexes
**Usage**: Production database setup

## 🗂️ Archive Information

**Cleaned up from**: 50+ original scripts
**Archived location**: `scripts/archive/`
**Archived count**: 30+ scripts moved to archive
**Reduction**: ~65% fewer files to maintain

### What Was Archived
- Duplicate chat testing scripts
- One-time investigation scripts
- Demo and example scripts
- Individual table creation scripts
- Redundant database utilities

### Archive Access
All archived scripts are preserved in `scripts/archive/` with a complete README explaining their original purpose and current alternatives.

## 🛠️ Development Workflow

### Adding New Scripts
1. **Single purpose**: Each script should have one clear responsibility
2. **Proper naming**: Use descriptive names following the pattern `verb_noun.py`
3. **Documentation**: Include docstring with purpose, usage, and requirements
4. **Error handling**: Implement proper error handling and logging
5. **Testing**: Test scripts with various scenarios before committing

### Script Standards
- **Python scripts**: Use `#!/usr/bin/env python3` shebang
- **Poetry integration**: Assume `poetry run python` execution
- **Environment variables**: Use settings from `lookbook_mpc.config.settings`
- **Logging**: Use structured logging with appropriate levels
- **Exit codes**: Return proper exit codes for automation

## 🔧 Troubleshooting

### Common Issues

#### "No module named 'lookbook_mpc'"
**Solution**: Run scripts with `poetry run python` from project root
```bash
cd /path/to/lookbookMPC
poetry run python scripts/script_name.py
```

#### Database Connection Errors
**Solution**: Check environment variables and run connection test
```bash
poetry run python scripts/test_db_connections.py
```

#### Benchmark Scripts Fail
**Solution**: Ensure Ollama is running and models are available
```bash
ollama list  # Check available models
ollama serve  # Start Ollama service
```

#### Vision Tests Fail
**Solution**: Start vision sidecar
```bash
poetry run python vision_sidecar.py  # In separate terminal
```

### Script Dependencies
Most scripts require:
- **Ollama service**: Running on localhost:11434
- **Database access**: MySQL connections configured
- **Environment variables**: Proper .env configuration
- **Vision sidecar**: For vision-related testing (port 8001)

## 📈 Performance Guidelines

### Benchmark Best Practices
- **Warmup runs**: Always include model warmup
- **Multiple iterations**: Use 3-5 iterations for reliable averages
- **Resource monitoring**: Monitor CPU/memory during benchmarks
- **Consistent environment**: Run benchmarks in consistent conditions

### Testing Efficiency
- **Parallel testing**: Use async where possible
- **Selective testing**: Run specific test categories as needed
- **Cache results**: Cache expensive operations when appropriate
- **Timeout handling**: Set appropriate timeouts for all network calls

## 🎯 Script Maintenance

### Regular Maintenance Tasks
1. **Update model names**: Keep benchmark scripts current with available models
2. **Review test coverage**: Ensure tests cover new features
3. **Performance monitoring**: Regular benchmark runs to detect regressions
4. **Dependency updates**: Keep script dependencies current
5. **Archive cleanup**: Move outdated scripts to archive as needed

### Quarterly Review
- **Script effectiveness**: Remove or consolidate underused scripts
- **Performance trends**: Analyze benchmark results for patterns
- **Error tracking**: Review and improve error handling
- **Documentation**: Update script documentation and usage examples

---

**Total Scripts**: 23 essential files (reduced from 50+ originals)
**Maintenance Burden**: 65% reduction while preserving all functionality
**Documentation**: Complete with usage examples and troubleshooting
**Status**: ✅ Production Ready - All essential operations covered

**Last Updated**: December 2024
**Cleanup Version**: 2.0 (Consolidated)