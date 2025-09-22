# Quick Fail Improvement for OpenRouter Benchmark

## Problem Solved

The original benchmark script would retry unavailable models (like `moonshotai/kimi-k2:free`) for up to 30 minutes using exponential backoff, wasting significant time on models that are permanently unavailable or severely rate-limited.

## Solution: Smart Model Failure Detection

Added intelligent failure detection that quickly identifies and skips unavailable models instead of retrying indefinitely.

### Key Features

1. **Immediate Skip for Known Unavailable Models**
   - Detects error messages indicating permanent unavailability
   - Keywords: "not found", "not available", "does not exist", "access denied", etc.
   - Immediately marks model as unavailable and skips further testing

2. **Quick Fail for Rate-Limited Models**
   - Tracks consecutive rate limit failures within a time window
   - Default: Skip after 3 consecutive failures within 60 seconds
   - Prevents 30-minute retry cycles for effectively unavailable models

3. **Smart Continuation**
   - Skips remaining prompts/iterations for detected unavailable models
   - Continues with other models in multi-model benchmarks
   - Provides clear feedback about why models were skipped

## Configuration Options

### Command Line Arguments

```bash
--quick-fail-threshold N        # Skip after N consecutive failures (default: 3)
--quick-fail-time-limit SECONDS # Time window for failure detection (default: 60)
```

### Examples

```bash
# Quick fail for problematic models (2 failures in 30 seconds)
python3 benchmark_models_openrouter.py \
    --models "moonshotai/kimi-k2:free" "openai/gpt-3.5-turbo" \
    --quick-fail-threshold 2 --quick-fail-time-limit 30 \
    --verbose

# Conservative settings (5 failures in 2 minutes)
python3 benchmark_models_openrouter.py \
    --models "model1" "model2" \
    --quick-fail-threshold 5 --quick-fail-time-limit 120
```

## Error Detection Logic

### Immediate Skip Conditions
- "not found", "not available", "does not exist"
- "invalid model", "model not supported"
- "access denied", "forbidden", "not accessible"

### Rate Limit Quick Fail
- Tracks consecutive "rate limit" failures
- If `quick_fail_threshold` failures occur within `quick_fail_time_limit`, skip model
- Resets counter on successful responses or different error types

## Benefits

### Time Savings
- **Before**: 30 minutes per unavailable model
- **After**: ~60 seconds per unavailable model (with defaults)
- **Example**: Testing 5 unavailable models saves ~145 minutes

### Better User Experience
- Clear feedback when models are skipped
- Continues with available models instead of getting stuck
- Prevents frustrating long waits for hopeless cases

### Flexibility
- Configurable thresholds for different use cases
- Can be disabled by setting high thresholds
- Works alongside existing retry logic for temporary failures

## Usage Patterns

### Testing Unknown Models
```bash
# Aggressive quick fail for initial model discovery
python3 benchmark_models_openrouter.py \
    --models "unknown/model1:free" "unknown/model2:free" \
    --quick-fail-threshold 2 --quick-fail-time-limit 30
```

### Production Benchmarking
```bash
# Conservative settings for established models
python3 benchmark_models_openrouter.py \
    --models "openai/gpt-4" "anthropic/claude-3-sonnet" \
    --quick-fail-threshold 5 --quick-fail-time-limit 120
```

### Batch Testing Free Models
```bash
# Quick discovery of working free models
python3 benchmark_models_openrouter.py \
    --models "qwen/qwen-2.5-7b-instruct:free" "meta-llama/llama-3.2-3b-instruct:free" \
    --quick-fail-threshold 2 --quick-fail-time-limit 30 \
    --repeat 2
```

## Implementation Details

### State Tracking
- `consecutive_failures`: Count of consecutive rate limit failures
- `first_failure_time`: Timestamp of first failure in current sequence
- `model_is_likely_unavailable`: Flag to skip remaining tests

### Error Handling
- Distinguishes between temporary and permanent failures
- Maintains existing retry logic for server errors (5xx)
- Immediate failure for client errors (4xx) except rate limits

### Output
- Clear messages when models are skipped
- Explanation of why model was skipped
- Time saved information in verbose mode

## Testing

Use `scripts/test_quick_fail.py` to test the feature:

```bash
cd scripts
python3 test_quick_fail.py
```

This will:
1. Test error message detection patterns
2. Optionally test with real API calls (requires API key)
3. Show time savings comparison

## Backward Compatibility

- All existing functionality preserved
- Default settings maintain current behavior for working models
- Can be disabled with high threshold values
- No impact on successful model benchmarking

## Future Enhancements

1. **Model Reputation Database**
   - Track historically problematic models
   - Skip known bad models immediately

2. **Adaptive Thresholds**
   - Adjust thresholds based on model provider
   - Learn from usage patterns

3. **Parallel Model Testing**
   - Test multiple models concurrently
   - Skip slow models more aggressively

## Related Files

- `scripts/benchmark_models_openrouter.py` - Main benchmark script
- `scripts/test_quick_fail.py` - Testing utility
- `benchmark_results/` - Output directory for results