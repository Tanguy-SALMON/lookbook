# OpenRouter Model Benchmark Guide

This guide explains how to use the `benchmark_models_openrouter.py` script to benchmark various LLM models through the OpenRouter API for fashion chatbot applications.

## Setup

### 1. Get OpenRouter API Key
- Visit [https://openrouter.ai/keys](https://openrouter.ai/keys)
- Create an account and generate an API key
- Note: You'll need credits in your OpenRouter account to run benchmarks

### 2. Set API Key
Choose one of these methods:

**Option A: Environment Variable (Recommended)**
```bash
export OPENROUTER_API_KEY="your-api-key-here"
```

**Option B: Command Line Parameter**
```bash
python3 benchmark_models_openrouter.py --api-key "your-api-key-here" [other options]
```

### 3. Install Dependencies
```bash
pip install httpx psutil GPUtil numpy
```

## Usage Examples

### List Available Models
```bash
python3 scripts/benchmark_models_openrouter.py --list-models
```

### Basic Benchmark (Default Models)
```bash
python3 scripts/benchmark_models_openrouter.py --verbose
```
*Uses: openai/gpt-3.5-turbo and anthropic/claude-3-haiku*

### Benchmark Specific Models
```bash
python3 scripts/benchmark_models_openrouter.py \
    --models "openai/gpt-4" "anthropic/claude-3-sonnet" "meta-llama/llama-2-70b-chat" \
    --verbose --show-full-responses
```

### Custom Configuration
```bash
python3 scripts/benchmark_models_openrouter.py \
    --models "openai/gpt-3.5-turbo" \
    --repeat 5 \
    --temperature 0.3 \
    --max-tokens 500 \
    --verbose \
    --output benchmark_results_custom
```

### Custom Prompts
```bash
python3 scripts/benchmark_models_openrouter.py \
    --models "openai/gpt-4" \
    --prompts "What should I wear to a wedding?" "Casual outfit for work from home" \
    --repeat 3 \
    --verbose --show-full-responses
```

### Review Saved Results
```bash
python3 scripts/benchmark_models_openrouter.py \
    --review-file benchmark_results/openai_gpt-4_results_20231215_143022.json \
    --max-review-responses 5
```

## Output Files

The script generates three types of files for each model:

### 1. Detailed Results (`*_results_*.json`)
Contains raw data for each benchmark run:
- Response times
- Token counts
- Quality scores
- Response content
- System metrics
- Cost estimates

### 2. Analysis (`*_analysis_*.json`)
Statistical analysis including:
- Performance metrics (mean, median, std dev, percentiles)
- Quality metrics
- Variability analysis
- Error analysis

### 3. Summary Report (`*_summary_*.txt`)
Human-readable summary with:
- Performance overview
- Token usage statistics
- Cost estimates
- Quality scores
- Top performing prompts

### 4. Comparison Report
When benchmarking multiple models, generates:
- `model_comparison_*.json` - Detailed comparison data
- Console output with recommendation table

## Understanding the Output

### Real-time Display (with --verbose)
```
Processing prompt 1/10: I want to do yoga, what should I wear?...
  Run 1/3... ✓ (2.34s, 45.2 tokens/s)
    Quality Score: 0.750
    Tokens: 87 completion, 124 total
    Est. Cost: $0.000186
    Response: For yoga, I recommend wearing comfortable, breathable clothing that allows for easy movement...
```

### Quality Scoring (0-1 scale)
- **Length adequacy** (20%): Appropriate response length
- **Relevance** (30%): Fashion-related keywords and context
- **Structure** (30%): Well-formed sentences and recommendations
- **Grammar** (20%): Basic grammar and formatting

### Cost Estimation
- Based on OpenRouter's token-based pricing
- Varies significantly by model (GPT-4 > Claude > Llama)
- Includes both prompt and completion costs
- Estimates may differ from actual billing

## Popular Models to Benchmark

### Fast & Affordable
- `openai/gpt-3.5-turbo` - Good balance of speed and quality
- `anthropic/claude-3-haiku` - Very fast, good for simple tasks
- `meta-llama/llama-2-70b-chat` - Open source, good performance

### High Quality (More Expensive)
- `openai/gpt-4-turbo` - Excellent quality, latest model
- `anthropic/claude-3-sonnet` - Very good reasoning
- `anthropic/claude-3-opus` - Highest quality, most expensive

### Specialized
- `mistralai/mixtral-8x7b-instruct` - Good for structured responses
- `google/gemini-pro` - Google's flagship model
- `cohere/command-r-plus` - Good for business applications

## Best Practices

### 1. Start Small
- Begin with 1-2 models and few iterations
- Use `--repeat 3` for initial testing
- Increase iterations for production benchmarks

### 2. Monitor Costs
- Check your OpenRouter dashboard regularly
- GPT-4 can cost 10-50x more than GPT-3.5-turbo
- Use `--max-tokens` to control response length and costs

### 3. Use Appropriate Temperature
- `0.1-0.3`: More consistent, factual responses
- `0.7`: Good balance (default)
- `0.9-1.0`: More creative, varied responses

### 4. Custom Prompts for Your Use Case
- Default prompts focus on fashion/clothing
- Add your specific use case prompts with `--prompts`
- Test edge cases and problematic inputs

### 5. Compare Fairly
- Use same prompts and settings across models
- Run multiple iterations to account for variability
- Consider both speed and quality in your evaluation

## Troubleshooting

### API Key Issues
```
Error: OpenRouter API key is required!
```
- Verify your API key is correct
- Check environment variable: `echo $OPENROUTER_API_KEY`
- Ensure you have credits in your OpenRouter account

### Model Not Found
```
HTTP 404: Model not found
```
- Use `--list-models` to see available models
- Check model name formatting (provider/model-name)
- Some models may require special access

### Rate Limiting
```
HTTP 429: Too many requests
```
- Add delays between requests
- Reduce `--repeat` count
- Check your OpenRouter plan limits

### High Costs
- Monitor token usage in the verbose output
- Use `--max-tokens` to limit response length
- Start with cheaper models like gpt-3.5-turbo
- Consider the `--repeat` count impact on total cost

## Integration with Your Application

The benchmark results can help you choose models for your fashion chatbot:

1. **Performance**: Response time requirements
2. **Quality**: Fashion relevance and helpfulness
3. **Cost**: Budget constraints for production usage
4. **Consistency**: Low variability in response quality

Use the comparison reports to make data-driven decisions about model selection.