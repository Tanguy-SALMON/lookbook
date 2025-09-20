#!/bin/bash

# Model Benchmark Script Runner
# This script runs comprehensive benchmarks comparing qwen3:4b vs qwen3

set -e

echo "Starting Model Benchmark Comparison"
echo "=================================="

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "Error: Ollama is not running. Please start Ollama first:"
    echo "  ollama serve"
    exit 1
fi

# Check if required models are available
echo "Checking required models..."
MODELS=("qwen2.5vl:7b" "qwen3:4b" "qwen3")
MISSING_MODELS=()

for model in "${MODELS[@]}"; do
    if ! ollama list | grep -q "$model"; then
        MISSING_MODELS+=("$model")
    fi
done

if [ ${#MISSING_MODELS[@]} -gt 0 ]; then
    echo "The following models are missing: ${MISSING_MODELS[*]}"
    echo "Pulling missing models..."
    for model in "${MISSING_MODELS[@]}"; do
        echo "Pulling $model..."
        ollama pull "$model"
    done
fi

# Install benchmark requirements if needed
if ! python -c "import psutil, GPUtil, numpy" 2>/dev/null; then
    echo "Installing benchmark requirements..."
    pip install -r requirements-benchmark.txt
fi

# Create results directory
mkdir -p benchmark_results

# Run benchmark
echo ""
echo "Running comprehensive benchmark..."
echo "This may take several minutes depending on your hardware..."

# Benchmark both models
poetry run python scripts/benchmark_models.py \
    --models qwen3:4b qwen3 \
    --repeat 10 \
    --temperature 0.7 \
    --max-tokens 1000 \
    --output benchmark_results

echo ""
echo "Benchmark completed! Results saved to benchmark_results/ directory"
echo ""
echo "Generated files:"
ls -la benchmark_results/ | grep -E "(qwen3|comparison)"

echo ""
echo "To view the comparison report:"
echo "  cat benchmark_results/model_comparison_*.json | jq '.'"

echo ""
echo "To run another benchmark with different settings:"
echo "  poetry run python scripts/benchmark_models.py --models qwen3:4b --repeat 20"