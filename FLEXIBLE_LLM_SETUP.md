# Flexible LLM Provider Configuration Guide

This guide explains how to configure Lookbook-MPC to use either Ollama (local) or OpenRouter (cloud) LLM providers.

## Overview

The flexible LLM system supports:
- **Ollama**: Local models (qwen3, llama3.2, etc.)
- **OpenRouter**: Cloud models with free and paid options
- **Automatic fallback**: OpenRouter → Ollama if API key missing

## Quick Setup

### Option 1: Use OpenRouter (Free Models)

```bash
# Set environment variables
export LLM_PROVIDER="openrouter"
export OPENROUTER_API_KEY="your-api-key-here"
export LLM_MODEL="qwen/qwen-2.5-7b-instruct:free"

# Start the service
python main.py
```

### Option 2: Use Ollama (Local)

```bash
# Start Ollama service
ollama serve

# Pull required models
ollama pull qwen3:4b-instruct

# Set environment (or use defaults)
export LLM_PROVIDER="ollama"
export LLM_MODEL="qwen3:4b-instruct"
export OLLAMA_HOST="http://localhost:11434"

# Start the service
python main.py
```

## Environment Variables

### Core LLM Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | `ollama` | Provider type: `ollama` or `openrouter` |
| `LLM_MODEL` | `qwen3:4b-instruct` | Primary model name |
| `LLM_TIMEOUT` | `30` | Request timeout in seconds |

### OpenRouter Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENROUTER_API_KEY` | - | **Required** for OpenRouter |
| `OPENROUTER_MODEL` | `qwen/qwen-2.5-7b-instruct:free` | OpenRouter model name |
| `OPENROUTER_BASE_URL` | `https://openrouter.ai/api/v1` | API endpoint |

### Ollama Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama service URL |
| `OLLAMA_TEXT_MODEL` | `qwen3:4b-instruct` | Text model name |
| `OLLAMA_VISION_MODEL` | `qwen2.5vl:7b` | Vision model name |

## Recommended Free Models

### OpenRouter Free Models

```bash
# Fast and reliable
export LLM_MODEL="qwen/qwen-2.5-7b-instruct:free"

# Alternative free options
export LLM_MODEL="meta-llama/llama-3.2-3b-instruct:free"
export LLM_MODEL="microsoft/phi-3-mini-128k-instruct:free"
```

### Ollama Local Models

```bash
# Lightweight and fast
ollama pull qwen3:4b-instruct
export LLM_MODEL="qwen3:4b-instruct"

# Alternative local options
ollama pull llama3.2:1b-instruct-q4_K_M
export LLM_MODEL="llama3.2:1b-instruct-q4_K_M"
```

## Configuration Examples

### Development Setup (Local Ollama)

```bash
# .env file
LLM_PROVIDER=ollama
LLM_MODEL=qwen3:4b-instruct
OLLAMA_HOST=http://localhost:11434
LLM_TIMEOUT=30
```

### Production Setup (OpenRouter)

```bash
# .env file
LLM_PROVIDER=openrouter
LLM_MODEL=qwen/qwen-2.5-7b-instruct:free
OPENROUTER_API_KEY=your-production-api-key
LLM_TIMEOUT=60
```

### Hybrid Setup (OpenRouter with Ollama fallback)

```bash
# .env file
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=your-api-key
LLM_MODEL=qwen/qwen-2.5-7b-instruct:free

# Ollama fallback settings
OLLAMA_HOST=http://localhost:11434
OLLAMA_TEXT_MODEL=qwen3:4b-instruct
```

## Testing Your Setup

```bash
# Test the LLM providers
cd scripts
python3 test_llm_providers.py

# Test intent parsing specifically
python3 -c "
import asyncio
from lookbook_mpc.adapters.intent import LLMIntentParser
from lookbook_mpc.adapters.llm_providers import LLMProviderFactory

async def test():
    provider = LLMProviderFactory.create_from_env()
    parser = LLMIntentParser(provider)
    result = await parser.parse_intent('I want to do yoga')
    print(f'Provider: {provider.get_provider_name()}')
    print(f'Intent: {result}')

asyncio.run(test())
"
```

## Getting OpenRouter API Key

1. Visit [OpenRouter.ai](https://openrouter.ai/keys)
2. Sign up for a free account
3. Generate an API key
4. Set the environment variable:
   ```bash
   export OPENROUTER_API_KEY="sk-or-v1-..."
   ```

## Troubleshooting

### Common Issues

**"OpenRouter API key not found"**
```bash
# Check environment variable
echo $OPENROUTER_API_KEY

# Set it if missing
export OPENROUTER_API_KEY="your-key-here"
```

**"Ollama connection failed"**
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama if not running
ollama serve

# Pull required models
ollama pull qwen3:4b-instruct
```

**"Model not found" (OpenRouter)**
```bash
# List available models
python3 scripts/benchmark_models_openrouter.py --list-models

# Use a working free model
export LLM_MODEL="qwen/qwen-2.5-7b-instruct:free"
```

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Start with verbose output
python main.py
```

## Performance Comparison

| Provider | Model | Speed | Cost | Reliability |
|----------|-------|-------|------|-------------|
| Ollama | qwen3:4b | Fast | Free | High |
| Ollama | llama3.2:1b | Very Fast | Free | High |
| OpenRouter | qwen-2.5-7b:free | Medium | Free | Medium* |
| OpenRouter | gpt-3.5-turbo | Fast | Low Cost | High |

*Free models may have rate limits

## Advanced Configuration

### Custom Provider Creation

```python
from lookbook_mpc.adapters.llm_providers import LLMProviderFactory

# Create OpenRouter provider
provider = LLMProviderFactory.create_provider(
    provider_type="openrouter",
    model="qwen/qwen-2.5-7b-instruct:free",
    api_key="your-key",
    timeout=60
)

# Create Ollama provider
provider = LLMProviderFactory.create_provider(
    provider_type="ollama",
    model="qwen3:4b-instruct",
    host="http://localhost:11434",
    timeout=30
)
```

### Environment-based Factory

```python
from lookbook_mpc.adapters.llm_providers import LLMProviderFactory

# Automatically choose provider based on env vars
provider = LLMProviderFactory.create_from_env(
    fallback_provider="ollama",
    fallback_model="qwen3:4b-instruct"
)
```

## Migration Guide

### From Ollama-only to Flexible System

1. **Update intent parser creation**:
   ```python
   # Old way
   parser = LLMIntentParser(host="http://localhost:11434", model="qwen3")
   
   # New way
   from lookbook_mpc.config.settings import settings
   parser = LLMIntentParser.create_from_settings(settings)
   ```

2. **Set environment variables**:
   ```bash
   export LLM_PROVIDER=ollama  # Keep existing behavior
   ```

3. **Test the migration**:
   ```bash
   python3 scripts/test_llm_providers.py
   ```

### Switching to OpenRouter

1. **Get API key** from OpenRouter.ai
2. **Update environment**:
   ```bash
   export LLM_PROVIDER=openrouter
   export OPENROUTER_API_KEY="your-key"
   export LLM_MODEL="qwen/qwen-2.5-7b-instruct:free"
   ```
3. **Restart services** and test

## Support

- **Documentation**: See `PROJECT_KNOWLEDGE_BASE.md`
- **Testing**: Use `scripts/test_llm_providers.py`
- **Benchmarking**: Use `scripts/benchmark_models_openrouter.py`
- **Issues**: Check logs with `LOG_LEVEL=DEBUG`
