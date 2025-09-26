# SmartRecommender Logging Guide

## Overview

The SmartRecommender service in Lookbook-MPC provides detailed logging at every step of the outfit recommendation process. This guide explains where to find logs, how to control them, and what each log message means.

## Quick Start

### 1. Enable Debug Logging
```bash
# Option A: Set in environment
export LOG_LEVEL=DEBUG
./start.sh

# Option B: One-time run
LOG_LEVEL=DEBUG ./start.sh

# Option C: Add to .env file
echo "LOG_LEVEL=DEBUG" >> .env
./start.sh
```

### 2. Test Logging
```bash
# Run test to see all log messages
poetry run python test_logs_in_action.py
```

## Log Configuration

### Environment Variables

| Variable | Default | Description | Options |
|----------|---------|-------------|---------|
| `LOG_LEVEL` | `INFO` | Controls verbosity | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `LOG_FORMAT` | `json` | Output format | `json`, `text` |

### Log Levels Explained

- **DEBUG**: Maximum detail, shows all internal steps
- **INFO**: General information about major steps (recommended for development)
- **WARNING**: Only warnings and non-fatal errors
- **ERROR**: Only critical errors that prevent operation

## SmartRecommender Log Messages

### Main Process Flow

```json
{"service": "smart_recommender", "message": "I go to dance", "event": "Starting smart recommendation", "level": "info", "timestamp": "2025-09-26T06:48:02.589890Z"}

{"service": "smart_recommender", "keywords_count": 6, "mood": "confident and ready to dance", "event": "Keywords generated successfully", "level": "info", "timestamp": "2025-09-26T06:48:05.411140Z"}

{"service": "smart_recommender", "count": 3, "event": "Added missing bottoms", "level": "info", "timestamp": "2025-09-26T06:48:05.463050Z"}

{"service": "smart_recommender", "original_count": 9, "diversified_count": 4, "removed_duplicates": 5, "event": "Product diversification completed", "level": "info", "timestamp": "2025-09-26T06:48:05.463181Z"}

{"service": "smart_recommender", "keywords_generated": 6, "products_found": 4, "outfits_created": 2, "event": "Smart recommendation completed", "level": "info", "timestamp": "2025-09-26T06:48:05.463420Z"}
```

### Log Message Reference

| Event | Level | Line | Meaning | Fields |
|-------|-------|------|---------|---------|
| `Starting smart recommendation` | INFO | 77 | User request received | `message` |
| `Keywords generated successfully` | INFO | 195 | LLM keyword generation completed | `keywords_count`, `mood` |
| `Added missing tops` | INFO | 623 | Fallback search for tops executed | `count` |
| `Added missing bottoms` | INFO | 629 | Fallback search for bottoms executed | `count` |
| `Product diversification completed` | INFO | 587 | Duplicate removal finished | `original_count`, `diversified_count`, `removed_duplicates` |
| `Smart recommendation completed` | INFO | 95 | Full process finished successfully | `keywords_generated`, `products_found`, `outfits_created` |

### Error Messages

| Event | Level | Line | Meaning | When It Occurs |
|-------|-------|------|---------|----------------|
| `LLM keyword generation failed` | WARNING | 207 | LLM service unavailable/timeout | Ollama/OpenRouter down |
| `Failed to parse keywords JSON` | ERROR | 242 | LLM returned invalid JSON | LLM response malformed |
| `Product search failed` | ERROR | 347 | Database query error | Database connection issues |
| `Category balance failed` | ERROR | 635 | Fallback search failed | Database problems |
| `Specific category search failed` | ERROR | 688 | Category-specific query failed | SQL syntax or connection error |
| `Outfit creation failed` | ERROR | 804 | Outfit assembly error | Missing required fields |
| `Smart recommendation failed` | ERROR | 98 | Complete process failure | Critical system error |

## Log Output Locations

### 1. Console/Terminal
- **When**: Running server with `./start.sh`
- **Format**: JSON (default) or text
- **Location**: Standard output (stdout)

### 2. Server Startup
```bash
./start.sh
```
Shows configuration:
```
Logging Configuration:
  📊 Log Level: DEBUG
  📋 Log Format: json
  💬 SmartRecommender logs will be visible at DEBUG level
```

### 3. Development Testing
```bash
# See all logs in isolation
poetry run python test_logs_in_action.py

# Test specific examples
poetry run python quick_test_examples.py
```

## Understanding Log Content

### Success Example
```json
{
  "service": "smart_recommender",
  "message": "I need something for a business meeting",
  "event": "Starting smart recommendation",
  "logger": "lookbook_mpc.services.smart_recommender",
  "level": "info",
  "timestamp": "2025-09-26T06:48:02.589890Z"
}
```

**Fields Explained:**
- `service`: Always "smart_recommender" for this module
- `message`: Original user request
- `event`: What happened (human-readable)
- `logger`: Full module path
- `level`: Log severity
- `timestamp`: ISO format timestamp
- Additional fields: Contextual data (counts, scores, etc.)

### Error Example
```json
{
  "service": "smart_recommender",
  "error": "Connection timeout",
  "event": "LLM keyword generation failed",
  "level": "warning",
  "timestamp": "2025-09-26T06:48:02.589890Z"
}
```

## Troubleshooting

### No Logs Appearing

**Check 1: Log Level**
```bash
# Ensure LOG_LEVEL is set correctly
echo $LOG_LEVEL
# Should show: DEBUG, INFO, WARNING, or ERROR
```

**Check 2: Configuration**
```bash
# Verify startup shows logging config
./start.sh
# Look for: "Logging Configuration:"
```

**Check 3: Test Directly**
```bash
# Test logging in isolation
poetry run python test_logs_in_action.py
```

### Too Many/Too Few Logs

**Too Many Logs** (DEBUG overwhelming):
```bash
# Use INFO level for normal operation
export LOG_LEVEL=INFO
```

**Too Few Logs** (Missing details):
```bash
# Use DEBUG level for troubleshooting
export LOG_LEVEL=DEBUG
```

### Log Format Issues

**Want Human-Readable Logs:**
```bash
export LOG_FORMAT=text
./start.sh
```

**Want Structured Logs (for parsing):**
```bash
export LOG_FORMAT=json
./start.sh
```

## Common Debugging Scenarios

### 1. No Outfit Recommendations
**Look for:**
- `Product search failed` - Database issues
- `keywords_count": 0` - LLM not generating keywords
- `products_found": 0` - Search returning no results

### 2. Only Single Items (No Complete Outfits)
**Look for:**
- `Added missing tops/bottoms` - Should see both
- `diversified_count` vs `original_count` - Too much filtering?
- `Outfit creation failed` - Assembly logic errors

### 3. LLM Service Issues
**Look for:**
- `LLM keyword generation failed` - Service unavailable
- `Failed to parse keywords JSON` - Response format issues
- Long delays between "Starting" and "Keywords generated"

## Performance Monitoring

### Key Metrics in Logs

```json
{
  "keywords_generated": 6,        // How many keywords LLM created
  "products_found": 4,            // Items found in database
  "outfits_created": 2,           // Final recommendations
  "original_count": 9,            // Before deduplication
  "diversified_count": 4,         // After deduplication
  "removed_duplicates": 5         // Items filtered out
}
```

**Healthy Ratios:**
- `keywords_generated`: 3-10 (good variety)
- `products_found`: 5-15 (enough choices)
- `outfits_created`: 1-5 (quality recommendations)
- `diversified_count` > 50% of `original_count
