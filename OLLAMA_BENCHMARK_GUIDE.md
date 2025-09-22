# Ollama vs OpenRouter Benchmark Guide

This guide explains the differences between the two benchmark scripts and when to use each one.

## Overview

- **`benchmark_models_openrouter.py`**: Benchmarks cloud models via OpenRouter API
- **`benchmark_models_ollama.py`**: Benchmarks local models via Ollama API

## Key Differences

### 1. **Model Access**

**OpenRouter:**
- Cloud-hosted models (GPT, Claude, Qwen, etc.)
- Requires API key and internet connection
- Pay-per-use pricing
- Models like: `qwen/qwen-2.5-72b-instruct:free`, `openai/gpt-4`

**Ollama:**
- Local models running on your machine
- No API key required
- Free once models are downloaded
- Models like: `qwen2.5:7b`, `llama3.1:8b`, `mistral:7b`

### 2. **Setup Requirements**

**OpenRouter:**
```bash
# Get API key from https://openrouter.ai/keys
export OPENROUTER_API_KEY="your-api-key"
```

**Ollama:**
```bash
# Install and start Ollama
curl -fsSL https://ollama.ai/install.sh | sh
ollama serve

# Pull models
ollama pull qwen2.5:7b
ollama pull llama3.1:8b
```

### 3. **Performance Metrics**

**Both scripts measure:**
- Response time
- Tokens per second (total)
- Inference speed (pure generation)
- Quality scores
- System resource usage

**Ollama additionally measures:**
- Model loading time (for cold starts)
- Local GPU/CPU utilization

**OpenRouter additionally measures:**
- API costs and token pricing
- Network latency effects

### 4. **Configuration Differences**

**OpenRouter Config:**
```python
BenchmarkConfig(
    model_name="qwen/qwen-2.5-72b-instruct:free",
    openrouter_api_key="sk-...",
    openrouter_base_url="https://openrouter.ai/api/v1"
)
```

**Ollama Config:**
```python
BenchmarkConfig(
    model_name="qwen2.5:7b", 
    ollama_host="http://localhost:11434"
)
```

## Usage Examples

### OpenRouter Benchmarks

```bash
# Basic cloud benchmark
python3 scripts/benchmark_models_openrouter.py --verbose

# Compare cloud models
python3 scripts/benchmark_models_openrouter.py \
  --models "qwen/qwen-2.5-72b-instruct:free" "openai/gpt-oss-20b:free" \
  --repeat 5

# List available cloud models
python3 scripts/benchmark_models_openrouter.py --list-models
```

### Ollama Benchmarks

```bash
# Basic local benchmark
python3 scripts/benchmark_models_ollama.py --verbose

# Compare local models
python3 scripts/benchmark_models_ollama.py \
  --models "qwen2.5:7b" "llama3.1:8b" "mistral:7b" \
  --repeat 5

# List available local models
python3 scripts/benchmark_models_ollama.py --list-models

# Custom Ollama host
python3 scripts/benchmark_models_ollama.py \
  --ollama-host "http://192.168.1.100:11434" \
  --models "qwen2.5:72b"
```

## When to Use Each

### Use OpenRouter When:
- ✅ Testing state-of-the-art models (GPT-4, Claude, etc.)
- ✅ Comparing different model providers
- ✅ Don't want to manage local infrastructure
- ✅ Need consistent performance (no cold starts)
- ✅ Evaluating cost-effectiveness of different models

### Use Ollama When:
- ✅ Privacy is critical (data stays local)
- ✅ Cost optimization (free after download)
- ✅ Testing hardware performance limits
- ✅ Offline capability requirements
- ✅ Customizing models or fine-tuning
- ✅ Evaluating local deployment scenarios

## Performance Comparison Example

**Typical Results:**

| Metric | OpenRouter (Cloud) | Ollama (Local) |
|--------|-------------------|----------------|
| **Response Time** | 2-15s | 1-30s (depends on hardware) |
| **Inference Speed** | 20-100 tokens/s | 5-200 tokens/s (depends on GPU) |
| **Cold Start** | ~0s (always warm) | 0-10s (model loading) |
| **Cost** | $0.001-0.1 per request | $0 (after download) |
| **Privacy** | Data sent to cloud | Fully private |

## Advanced Features

### System Suffix Control (Both)
```bash
# Controlled responses
--system-suffix "Answer concisely (<=120 words). Use 4-6 short bullets."

# Disable control for natural responses
--no-system-suffix
```

### Resource Monitoring (Both)
- CPU and memory usage tracking
- GPU utilization (if available)
- Performance variability analysis

### Result Analysis (Both)
```bash
# Review saved results
python3 scripts/benchmark_models_*.py \
  --review-file benchmark_results/model_results_*.json

# Show full responses
--show-full-responses
```

## Environment Variables

**OpenRouter:**
```bash
export OPENROUTER_API_KEY="your-key"
export OPENROUTER_KEY="your-key"  # Alternative
```

**Ollama:**
```bash
export OLLAMA_HOST="http://localhost:11434"  # Default
export OLLAMA_HOST="http://gpu-server:11434"  # Remote
```

## Model Format Examples

**OpenRouter Models:**
- `qwen/qwen-2.5-72b-instruct:free`
- `openai/gpt-4-turbo`
- `anthropic/claude-3-sonnet`
- `meta-llama/llama-3.1-8b-instruct`

**Ollama Models:**
- `qwen2.5:7b`
- `qwen2.5:72b`
- `llama3.1:8b`
- `mistral:7b`
- `codellama:13b`

## Troubleshooting

### OpenRouter Issues:
```bash
# Check API key
echo $OPENROUTER_API_KEY

# Test connection
curl -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  https://openrouter.ai/api/v1/models
```

### Ollama Issues:
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama
ollama serve

# Check available models
ollama list
```

## Performance Tips

### For OpenRouter:
- Use `:free` models for cost-effective testing
- Enable system suffix for consistent comparisons
- Monitor token usage to control costs

### For Ollama:
- Use smaller models (7B) for faster iteration
- Ensure adequate GPU memory for larger models
- Consider quantized models (Q4, Q8) for better performance
- Pre-load models to avoid cold start times

## Combining Both Scripts

You can run comparative benchmarks across cloud and local models:

```bash
# Benchmark cloud models
python3 scripts/benchmark_models_openrouter.py \
  --models "qwen/qwen-2.5-7b-instruct:free" \
  --repeat 3 --verbose

# Benchmark equivalent local model
python3 scripts/benchmark_models_ollama.py \
  --models "qwen2.5:7b" \
  --repeat 3 --verbose

# Compare results manually or merge JSON outputs
```

## Output Formats

Both scripts produce identical output formats:
- **JSON results**: Detailed per-run data
- **Analysis files**: Statistical summaries
- **Text summaries**: Human-readable reports
- **Comparison tables**: Multi-model analysis

This allows you to use the same analysis tools and processes regardless of whether you're benchmarking cloud or local models.