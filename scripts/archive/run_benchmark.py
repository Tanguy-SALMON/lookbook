#!/usr/bin/env python3
"""
Model Benchmark Script
This script runs comprehensive benchmarks comparing different Ollama models.
"""

import subprocess
import sys
import json
import time
import os
import argparse
from datetime import datetime
from typing import List, Dict, Any, Optional
import requests

def check_ollama_running() -> bool:
    """Check if Ollama is running and accessible."""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

def get_available_models() -> List[str]:
    """Get list of available Ollama models."""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=10)
        if response.status_code == 200:
            data = response.json()
            return [model["name"] for model in data["models"]]
    except requests.exceptions.RequestException:
        pass
    return []

def pull_model(model_name: str) -> bool:
    """Pull a model from Ollama."""
    try:
        print(f"Pulling {model_name}...")
        process = subprocess.Popen(
            ["ollama", "pull", model_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        process.communicate()
        return process.returncode == 0
    except Exception as e:
        print(f"Error pulling {model_name}: {e}")
        return False

def check_python_dependencies() -> bool:
    """Check if required Python packages are available."""
    required_packages = ['requests']
    missing_packages = []

    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)

    if missing_packages:
        print(f"Missing packages: {', '.join(missing_packages)}")
        print("Please install them using:")
        print(f"pip install {' '.join(missing_packages)}")
        return False

    return True

def get_system_info() -> Dict[str, Any]:
    """Get system information for benchmark context."""
    # Basic system info without external dependencies
    import platform

    # CPU info
    cpu_info = {
        "physical_cores": None,  # Not available without psutil
        "logical_cores": None,   # Not available without psutil
        "cpu_freq": None,        # Not available without psutil
        "cpu_percent": None,     # Not available without psutil
        "platform": platform.processor() or "Unknown",
        "system": platform.system(),
        "machine": platform.machine(),
        "python_version": platform.python_version()
    }

    # Memory info (basic)
    try:
        import os
        memory_info = {
            "total_gb": round(os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES') / (1024**3), 2),
            "available_gb": None,  # Not easily available without psutil
            "percent_used": None   # Not easily available without psutil
        }
    except:
        memory_info = {
            "total_gb": None,
            "available_gb": None,
            "percent_used": None
        }

    # GPU info (not available without GPUtil)
    gpu_info = []

    return {
        "cpu": cpu_info,
        "memory": memory_info,
        "gpu": gpu_info,
        "timestamp": datetime.now().isoformat()
    }

def benchmark_model(model_name: str, test_prompt: str, temperature: float = 0.7, max_tokens: int = 1000) -> Dict[str, Any]:
    """Benchmark a single model with a test prompt."""
    start_time = time.time()

    try:
        # Prepare the request payload
        payload = {
            "model": model_name,
            "prompt": test_prompt,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        # Make the request to Ollama
        response = requests.post(
            "http://localhost:11434/api/generate",
            json=payload,
            timeout=60  # 60 second timeout
        )

        end_time = time.time()
        duration = end_time - start_time

        if response.status_code == 200:
            result = response.json()
            return {
                "model": model_name,
                "success": True,
                "duration_seconds": round(duration, 3),
                "response_tokens": len(result.get("response", "")),
                "total_tokens": result.get("done", False),
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "model": model_name,
                "success": False,
                "error": f"HTTP {response.status_code}: {response.text}",
                "duration_seconds": round(duration, 3),
                "timestamp": datetime.now().isoformat()
            }

    except requests.exceptions.Timeout:
        return {
            "model": model_name,
            "success": False,
            "error": "Request timed out after 60 seconds",
            "duration_seconds": 60.0,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "model": model_name,
            "success": False,
            "error": str(e),
            "duration_seconds": round(time.time() - start_time, 3),
            "timestamp": datetime.now().isoformat()
        }

def run_benchmark(models: List[str], repeat: int = 10, temperature: float = 0.7, max_tokens: int = 1000, output_dir: str = "benchmark_results") -> Dict[str, Any]:
    """Run comprehensive benchmark on multiple models."""

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # System information
    system_info = get_system_info()

    # Test prompt for benchmarking
    test_prompt = """Analyze this fashion item description and provide a detailed analysis:

Product: Classic Blue Cotton Shirt
Description: A timeless button-down shirt made from 100% cotton with a regular fit. Features a classic collar, long sleeves with button cuffs, and a single chest pocket. Perfect for business casual wear and can be dressed up or down.

Please provide:
1. Primary color and any secondary colors
2. Material composition
3. Category (top, bottom, dress, etc.)
4. Pattern type
5. Season suitability
6. Occasion appropriateness
7. Style description
8. Fit type
9. Any special features

Format your response as a structured analysis."""

    print(f"Starting benchmark with {len(models)} models...")
    print(f"Test prompt length: {len(test_prompt)} characters")
    print(f"Repeat count: {repeat}")
    print(f"Temperature: {temperature}")
    print(f"Max tokens: {max_tokens}")
    print("-" * 50)

    results = {
        "system_info": system_info,
        "benchmark_config": {
            "models": models,
            "repeat": repeat,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "test_prompt_length": len(test_prompt)
        },
        "model_results": {},
        "summary": {}
    }

    # Benchmark each model
    for model in models:
        print(f"\nBenchmarking {model}...")
        model_results = []

        successful_runs = 0
        total_duration = 0
        total_tokens = 0

        for i in range(repeat):
            print(f"  Run {i+1}/{repeat}...", end=" ")

            result = benchmark_model(model, test_prompt, temperature, max_tokens)
            model_results.append(result)

            if result["success"]:
                successful_runs += 1
                total_duration += result["duration_seconds"]
                total_tokens += result["response_tokens"]
                print(f"✓ ({result['duration_seconds']:.2f}s, {result['response_tokens']} tokens)")
            else:
                print(f"✗ ({result['error']})")

        # Calculate statistics for this model
        model_stats = {
            "total_runs": repeat,
            "successful_runs": successful_runs,
            "success_rate": round((successful_runs / repeat) * 100, 2),
            "average_duration": round(total_duration / successful_runs, 3) if successful_runs > 0 else 0,
            "min_duration": min([r["duration_seconds"] for r in model_results if r["success"]], default=0),
            "max_duration": max([r["duration_seconds"] for r in model_results if r["success"]], default=0),
            "total_tokens": total_tokens,
            "tokens_per_second": round(total_tokens / total_duration, 2) if total_duration > 0 else 0,
            "individual_results": model_results
        }

        results["model_results"][model] = model_stats
        print(f"  Success Rate: {model_stats['success_rate']}%")
        print(f"  Avg Duration: {model_stats['average_duration']:.3f}s")
        print(f"  Tokens/sec: {model_stats['tokens_per_second']:.2f}")

    # Generate summary comparison
    print("\n" + "="*50)
    print("BENCHMARK SUMMARY")
    print("="*50)

    successful_models = [model for model in models if results["model_results"][model]["success_rate"] > 0]

    if successful_models:
        # Find fastest model
        fastest_model = min(successful_models,
                          key=lambda m: results["model_results"][m]["average_duration"])

        # Find highest throughput model
        highest_throughput = max(successful_models,
                               key=lambda m: results["model_results"][m]["tokens_per_second"])

        print(f"Models tested: {', '.join(models)}")
        print(f"Successfully benchmarked: {', '.join(successful_models)}")
        print(f"Fastest model: {fastest_model} ({results['model_results'][fastest_model]['average_duration']:.3f}s avg)")
        print(f"Highest throughput: {highest_throughput} ({results['model_results'][highest_throughput]['tokens_per_second']:.2f} tokens/sec)")

        results["summary"] = {
            "total_models_tested": len(models),
            "successful_models": len(successful_models),
            "fastest_model": fastest_model,
            "fastest_avg_duration": results["model_results"][fastest_model]["average_duration"],
            "highest_throughput_model": highest_throughput,
            "highest_throughput": results["model_results"][highest_throughput]["tokens_per_second"]
        }
    else:
        print("No models completed successfully")
        results["summary"] = {
            "total_models_tested": len(models),
            "successful_models": 0,
            "error": "All models failed"
        }

    # Save results to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(output_dir, f"benchmark_results_{timestamp}.json")

    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\nResults saved to: {output_file}")
    return results

def main():
    parser = argparse.ArgumentParser(description="Benchmark Ollama models")
    parser.add_argument("--models", nargs="+",
                       help="Models to benchmark (e.g., 'qwen3:4b' 'qwen3:latest'). If not specified, benchmarks all available models.")
    parser.add_argument("--repeat", type=int, default=3,
                       help="Number of times to repeat each benchmark (default: 3)")
    parser.add_argument("--temperature", type=float, default=0.7,
                       help="Temperature for generation (default: 0.7)")
    parser.add_argument("--max-tokens", type=int, default=1000,
                       help="Maximum tokens to generate (default: 1000)")
    parser.add_argument("--output", default="benchmark_results",
                       help="Output directory for results (default: benchmark_results)")

    args = parser.parse_args()

    print("Model Benchmark Script")
    print("="*50)

    # Check if Ollama is running
    if not check_ollama_running():
        print("Error: Ollama is not running.")
        print("Please start Ollama first:")
        print("  ollama serve")
        sys.exit(1)

    # Check Python dependencies
    if not check_python_dependencies():
        sys.exit(1)

    # Get available models
    available_models = get_available_models()
    print(f"Available models: {', '.join(available_models) if available_models else 'None'}")

    # If no models specified, benchmark all available models
    if not args.models:
        if not available_models:
            print("Error: No models available for testing")
            sys.exit(1)
        models_to_test = available_models
        print(f"\nNo models specified, benchmarking all available models: {', '.join(models_to_test)}")
    else:
        # Check if requested models are available
        missing_models = [model for model in args.models if model not in available_models]
        if missing_models:
            print(f"Missing models: {', '.join(missing_models)}")
            print("Attempting to pull missing models...")

            for model in missing_models:
                if pull_model(model):
                    print(f"Successfully pulled {model}")
                    available_models.append(model)
                else:
                    print(f"Failed to pull {model}")

        # Filter models to only include available ones
        models_to_test = [model for model in args.models if model in available_models]

        if not models_to_test:
            print("Error: No models available for testing")
            sys.exit(1)

        print(f"\nTesting models: {', '.join(models_to_test)}")

    # Run benchmark
    try:
        results = run_benchmark(
            models=models_to_test,
            repeat=args.repeat,
            temperature=args.temperature,
            max_tokens=args.max_tokens,
            output_dir=args.output
        )

        print("\nBenchmark completed successfully!")

    except KeyboardInterrupt:
        print("\nBenchmark interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError during benchmark: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()