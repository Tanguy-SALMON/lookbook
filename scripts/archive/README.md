# Scripts Archive

This directory contains scripts that were consolidated or removed during the December 2024 scripts cleanup. These files are preserved for reference but are no longer actively maintained.

## 📚 Archive Contents

### Chat Testing Scripts (Consolidated → test_chat_comprehensive.py)
- `test_chat_direct.py` - Direct chat testing using FastAPI TestClient
- `test_chat_integration.py` - Chat integration with smart recommender
- `test_chat_summary.py` - Chat testing summary script
- `test_llm_chat.py` - LLM chat system testing
- `chat_demo.py` - Interactive chat demonstration
- `start_chat_server.py` - Chat server startup script

### Demo & Example Scripts (Outdated)
- `demo_improvements.py` - Benchmark improvements demonstration
- `demo_error_handling.py` - Error handling examples
- `demo_provider_switch.py` - Provider switching demonstration
- `test_demo.py` - Demo functionality testing
- `explain_speed_results.py` - Speed test result explanations
- `final_summary.py` - Final benchmark summary generator

### Investigation Scripts (One-time Use)
- `investigate_magento_db.py` - Magento database exploration
- `investigate_product_attributes.py` - Product attribute analysis

### Database Scripts (Consolidated → init_db.py + test_db_connections.py)
- `test_db.py` - Basic database testing
- `rebuild_db.py` - Database rebuild utilities
- `cleanup_database_schema.py` - Schema cleanup operations

### Table Creation Scripts (Consolidated → init_db_mysql_tables.py)
- `create_agent_dashboard_table.py` - Agent dashboard table creation
- `create_agent_rules_table.py` - Agent rules table creation
- `create_chat_logs_table.py` - Chat logs table creation
- `create_vision_attributes_table.py` - Vision attributes table creation
- `create_agent_dashboard_table.sql` - SQL for agent dashboard table
- `create_agent_rules_table.sql` - SQL for agent rules table

### Test Scripts (Consolidated → Core Testing Scripts)
- `test_setup.py` - Setup validation testing
- `test_batch_results.py` - Batch processing result tests
- `test_fuzzy_matcher.py` - Fuzzy matching algorithm tests
- `test_intent.py` - Intent parsing tests
- `test_smart_recommender.py` - Smart recommender testing

### Analysis & Verification Scripts
- `verify_database_results.py` - Database result verification
- `batch_analysis_summary.py` - Batch analysis summaries
- `batch_analyze_products.py` - Product batch analysis

## 🔄 Why These Scripts Were Archived

These scripts contained:
- **Duplicate functionality** consolidated into fewer comprehensive scripts
- **One-time investigation code** no longer needed for daily operations
- **Demo scripts** showing completed improvements
- **Multiple approaches** to the same testing goals
- **Outdated examples** replaced by better implementations

## 📖 Where to Find Current Functionality

The functionality from these scripts has been consolidated into:

| Archived Functionality | Current Location |
|------------------------|------------------|
| Chat testing | `test_chat_comprehensive.py` |
| Database operations | `init_db.py`, `test_db_connections.py` |
| API testing | `test_api.py` |
| Vision testing | `test_vision.py` |
| Recommendation testing | `test_recommender.py` |
| Product sync | `sync_100_products.py` |
| Product verification | `verify_product_import.py` |

## 🎯 Current Essential Scripts (Post-Cleanup)

After consolidation, the essential scripts are:

### Benchmark Scripts (All Preserved)
- `benchmark_models.py` - Main benchmark script
- `benchmark_models_anthropic.py` - Anthropic model benchmarks
- `benchmark_models_fast.py` - Fast benchmark implementation
- `benchmark_models_ollama.py` - Ollama-specific benchmarks
- `benchmark_models_openrouter.py` - OpenRouter benchmarks
- `run_benchmark.py` - Benchmark runner
- `run_benchmark.sh` - Shell benchmark runner
- `demo_both_benchmarks.py` - Benchmark comparison
- `OPENROUTER_BENCHMARK_README.md` - Benchmark documentation

### Core Testing Scripts
- `test_api.py` - API endpoint testing
- `test_chat_comprehensive.py` - Complete chat system testing
- `test_vision.py` - Vision analysis testing
- `test_recommender.py` - Recommendation engine testing
- `test_mcp.py` - MCP protocol testing

### Database & Data Scripts
- `init_db.py` - Database initialization
- `init_db_mysql_tables.py` - MySQL table creation
- `test_db_connections.py` - Database connection testing
- `sync_100_products.py` - Product synchronization
- `verify_product_import.py` - Import verification
- `check_llm_status.py` - LLM service status check

### Deployment Scripts
- `deploy.sh` - Deployment automation

### SQL Files
- `init_db_clean.sql` - Clean database initialization
- `init_db_mysql.sql` - MySQL initialization

## 🧹 Cleanup Results

**Before Cleanup**: 50+ scripts with significant duplication
**After Cleanup**: ~18 essential scripts with clear purposes
**Reduction**: ~65% fewer files to maintain
**Benefit**: Clearer script landscape, reduced confusion, easier maintenance

## 🔍 Using This Archive

**When to reference these files:**
- Understanding historical approaches to testing
- Researching specific implementation details from removed functionality
- Debugging issues that might be related to removed scripts
- Finding code snippets for similar functionality

**Current scripts to use instead:**
- For chat testing: Use `test_chat_comprehensive.py`
- For database work: Use `test_db_connections.py` and `init_db.py`
- For benchmarking: Use the preserved benchmark scripts
- For product operations: Use `sync_100_products.py` and `verify_product_import.py`

---

**Archive Created**: December 2024  
**Reason**: Scripts consolidation and cleanup  
**Status**: Historical reference only - not actively maintained  
**Total Archived Files**: 30+ scripts consolidated into essential set