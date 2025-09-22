#!/usr/bin/env python3
"""
Model Benchmark Script

This script benchmarks qwen3:4b vs qwen3 models for chatbot applications.
It measures performance, quality, and variability metrics with comprehensive reporting.
"""

import asyncio
import json
import time
import statistics
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import argparse
import httpx
import psutil
import GPUtil
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import numpy as np

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@dataclass
class BenchmarkConfig:
    """Configuration for benchmark tests."""

    model_name: str
    ollama_host: str = "http://localhost:11434"
    timeout: float = 60.0
    max_tokens: int = 1000
    temperature: float = 0.7
    repeat_count: int = 3
    test_prompts: List[str] = None
    verbose: bool = True
    show_full_responses: bool = False

    def __post_init__(self):
        if self.test_prompts is None:
            self.test_prompts = [
                "I want to do yoga, what should I wear? ",
                "Restaurant this weekend, attractive for $50",
                "I am fat, I want something to look slim",
                "Business meeting outfit for office",
                "Beach vacation clothes for hot weather",
                "First date outfit ideas",
                "Gym workout clothes recommendation",
                "Winter formal dress suggestions",
                "Casual Friday office attire",
                "Hiking trip clothing advice",
            ]


@dataclass
class BenchmarkResult:
    """Results for a single benchmark run."""

    model_name: str
    prompt: str
    response_time: float
    tokens_per_second: float
    memory_usage_mb: float
    cpu_usage_percent: float
    gpu_usage_percent: Optional[float]
    gpu_memory_mb: Optional[float]
    response_length: int
    response_quality_score: float
    timestamp: str
    success: bool
    response_content: str = ""
    error_message: Optional[str] = None


class ModelBenchmark:
    """Comprehensive model benchmark for chatbot applications."""

    def __init__(self, config: BenchmarkConfig):
        self.config = config
        self.results: List[BenchmarkResult] = []
        self.system_info = self._get_system_info()

    def _get_system_info(self) -> Dict[str, Any]:
        """Get system information for benchmark context."""
        return {
            "cpu_count": psutil.cpu_count(),
            "cpu_freq": psutil.cpu_freq().current if psutil.cpu_freq() else None,
            "total_memory_gb": psutil.virtual_memory().total / (1024**3),
            "gpu_info": self._get_gpu_info(),
            "python_version": sys.version,
            "benchmark_timestamp": datetime.now().isoformat(),
        }

    def _get_gpu_info(self) -> List[Dict[str, Any]]:
        """Get GPU information."""
        try:
            gpus = GPUtil.getGPUs()
            return [
                {
                    "name": gpu.name,
                    "memory_total": gpu.memoryTotal,
                    "memory_used": gpu.memoryUsed,
                    "memory_free": gpu.memoryFree,
                    "load": gpu.load * 100,
                }
                for gpu in gpus
            ]
        except Exception as e:
            return [{"error": str(e)}]

    def _get_system_metrics(
        self,
    ) -> Tuple[float, float, Optional[float], Optional[float]]:
        """Get current system metrics."""
        memory = psutil.Process().memory_info()
        memory_mb = memory.rss / 1024 / 1024
        cpu_percent = psutil.Process().cpu_percent()

        gpu_percent = None
        gpu_memory = None
        try:
            gpus = GPUtil.getGPUs()
            if gpus:
                gpu_percent = gpus[0].load * 100
                gpu_memory = gpus[0].memoryUsed
        except:
            pass

        return memory_mb, cpu_percent, gpu_percent, gpu_memory

    async def _call_ollama(self, prompt: str) -> Tuple[str, float, bool, Optional[str]]:
        """Call Ollama API and return response, time, success, and error."""
        start_time = time.time()
        success = True
        error = None

        try:
            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                payload = {
                    "model": self.config.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": self.config.temperature,
                        "num_predict": self.config.max_tokens,
                        "top_p": 0.9,
                        "repeat_penalty": 1.1,
                        "presence_penalty": 0.0,
                        "frequency_penalty": 0.0,
                    },
                }

                response = await client.post(
                    f"{self.config.ollama_host}/api/generate", json=payload
                )

                if response.status_code == 200:
                    result = response.json()
                    response_text = result.get("response", "")
                    elapsed_time = time.time() - start_time

                    # Estimate tokens (rough approximation)
                    tokens = (
                        len(response_text.split()) * 1.3
                    )  # Average 1.3 tokens per word
                    tokens_per_second = tokens / elapsed_time if elapsed_time > 0 else 0

                    return response_text, elapsed_time, True, None
                else:
                    elapsed_time = time.time() - start_time
                    return (
                        "",
                        elapsed_time,
                        False,
                        f"HTTP {response.status_code}: {response.text}",
                    )

        except Exception as e:
            elapsed_time = time.time() - start_time
            return "", elapsed_time, False, str(e)

    def _evaluate_response_quality(self, prompt: str, response: str) -> float:
        """Evaluate response quality (0-1 scale)."""
        if not response.strip():
            return 0.0

        # Simple quality metrics
        score = 0.0

        # Length adequacy (0.2 weight)
        word_count = len(response.split())
        if 10 <= word_count <= 200:
            score += 0.2
        elif word_count < 10:
            score += 0.1  # Too short but has some content

        # Relevance to prompt (0.3 weight)
        prompt_lower = prompt.lower()
        response_lower = response.lower()

        # Check for key fashion-related terms
        fashion_keywords = [
            "wear",
            "outfit",
            "clothes",
            "fashion",
            "style",
            "look",
            "fit",
        ]
        relevant_keywords = [kw for kw in fashion_keywords if kw in response_lower]

        if len(relevant_keywords) >= 2:
            score += 0.3
        elif len(relevant_keywords) == 1:
            score += 0.15

        # Structure and coherence (0.3 weight)
        sentences = response.split(".")
        if len(sentences) >= 2:
            score += 0.2
        if any(
            word in response_lower
            for word in ["recommend", "suggest", "consider", "try"]
        ):
            score += 0.1

        # Grammar and spelling (0.2 weight)
        # Simple check for basic grammar patterns
        if response.strip()[0].isupper():
            score += 0.05
        if response.strip()[-1] in [".", "!", "?"]:
            score += 0.05
        if not response.strip().count("  ") > 2:  # Not too many double spaces
            score += 0.05
        if (
            len([c for c in response if c.isupper()]) / len(response) < 0.3
        ):  # Not all caps
            score += 0.05

        return min(score, 1.0)

    async def run_single_benchmark(self, prompt: str) -> BenchmarkResult:
        """Run a single benchmark test."""
        # Get initial system metrics
        memory_mb, cpu_percent, gpu_percent, gpu_memory = self._get_system_metrics()

        # Run the model inference
        response, response_time, success, error = await self._call_ollama(prompt)

        # Get final system metrics
        final_memory, final_cpu, final_gpu, final_gpu_memory = (
            self._get_system_metrics()
        )

        # Calculate average metrics
        avg_memory = (memory_mb + final_memory) / 2
        avg_cpu = (cpu_percent + final_cpu) / 2
        avg_gpu = (gpu_percent + final_gpu) / 2 if gpu_percent is not None else None
        avg_gpu_memory = (
            (gpu_memory + final_gpu_memory) / 2 if gpu_memory is not None else None
        )

        # Calculate tokens per second
        tokens = len(response.split()) * 1.3  # Rough approximation
        tokens_per_second = tokens / response_time if response_time > 0 else 0

        # Evaluate response quality
        quality_score = (
            self._evaluate_response_quality(prompt, response) if success else 0.0
        )

        return BenchmarkResult(
            model_name=self.config.model_name,
            prompt=prompt,
            response_time=response_time,
            tokens_per_second=tokens_per_second,
            memory_usage_mb=avg_memory,
            cpu_usage_percent=avg_cpu,
            gpu_usage_percent=avg_gpu,
            gpu_memory_mb=avg_gpu_memory,
            response_length=len(response),
            response_quality_score=quality_score,
            timestamp=datetime.now().isoformat(),
            success=success,
            response_content=response,
            error_message=error,
        )

    async def run_full_benchmark(self) -> List[BenchmarkResult]:
        """Run complete benchmark suite."""
        print(f"Starting benchmark for {self.config.model_name}")
        print(
            f"Running {self.config.repeat_count} iterations for each of {len(self.config.test_prompts)} prompts"
        )

        for i, prompt in enumerate(self.config.test_prompts):
            print(
                f"\nProcessing prompt {i + 1}/{len(self.config.test_prompts)}: {prompt[:50]}..."
            )

            for j in range(self.config.repeat_count):
                print(f"  Run {j + 1}/{self.config.repeat_count}...", end=" ")

                result = await self.run_single_benchmark(prompt)
                self.results.append(result)

                if result.success:
                    if self.config.verbose:
                        print(
                            f"✓ ({result.response_time:.2f}s, {result.tokens_per_second:.1f} tokens/s)"
                        )
                        print(f"    Quality Score: {result.response_quality_score:.3f}")

                        # Show response preview
                        if self.config.show_full_responses:
                            print(
                                f"    Full Response ({len(result.response_content)} chars):"
                            )
                            print(f"    {'-' * 60}")
                            print(f"    {result.response_content}")
                            print(f"    {'-' * 60}")
                        else:
                            response_preview = result.response_content[:150]
                            if len(result.response_content) > 150:
                                response_preview += "..."
                            print(f"    Response: {response_preview}")
                    else:
                        print(f"✓ ({result.response_time:.2f}s)")
                else:
                    print(f"✗ ({result.error_message})")

                if self.config.verbose:
                    print()  # Add blank line between iterations

        return self.results

    def analyze_results(self) -> Dict[str, Any]:
        """Analyze benchmark results and return statistics."""
        if not self.results:
            return {}

        # Filter successful results
        successful_results = [r for r in self.results if r.success]
        failed_results = [r for r in self.results if not r.success]

        if not successful_results:
            return {"error": "No successful benchmark runs"}

        # Group by prompt for variability analysis
        prompt_results = {}
        for result in successful_results:
            if result.prompt not in prompt_results:
                prompt_results[result.prompt] = []
            prompt_results[result.prompt].append(result)

        analysis = {
            "model_name": self.config.model_name,
            "total_runs": len(self.results),
            "successful_runs": len(successful_results),
            "failed_runs": len(failed_results),
            "success_rate": len(successful_results) / len(self.results) * 100,
            "system_info": self.system_info,
            "performance_metrics": self._calculate_performance_metrics(
                successful_results
            ),
            "quality_metrics": self._calculate_quality_metrics(successful_results),
            "variability_metrics": self._calculate_variability_metrics(prompt_results),
            "prompt_analysis": self._analyze_by_prompt(prompt_results),
            "error_analysis": self._analyze_errors(failed_results),
        }

        return analysis

    def _calculate_performance_metrics(
        self, results: List[BenchmarkResult]
    ) -> Dict[str, Any]:
        """Calculate performance statistics."""
        response_times = [r.response_time for r in results]
        tokens_per_second = [r.tokens_per_second for r in results]
        memory_usage = [r.memory_usage_mb for r in results]
        cpu_usage = [r.cpu_usage_percent for r in results]

        return {
            "response_time": {
                "mean": statistics.mean(response_times),
                "median": statistics.median(response_times),
                "std": statistics.stdev(response_times)
                if len(response_times) > 1
                else 0,
                "min": min(response_times),
                "max": max(response_times),
                "p95": np.percentile(response_times, 95),
                "p99": np.percentile(response_times, 99),
            },
            "tokens_per_second": {
                "mean": statistics.mean(tokens_per_second),
                "median": statistics.median(tokens_per_second),
                "std": statistics.stdev(tokens_per_second)
                if len(tokens_per_second) > 1
                else 0,
                "min": min(tokens_per_second),
                "max": max(tokens_per_second),
            },
            "memory_usage_mb": {
                "mean": statistics.mean(memory_usage),
                "median": statistics.median(memory_usage),
                "std": statistics.stdev(memory_usage) if len(memory_usage) > 1 else 0,
                "min": min(memory_usage),
                "max": max(memory_usage),
            },
            "cpu_usage_percent": {
                "mean": statistics.mean(cpu_usage),
                "median": statistics.median(cpu_usage),
                "std": statistics.stdev(cpu_usage) if len(cpu_usage) > 1 else 0,
                "min": min(cpu_usage),
                "max": max(cpu_usage),
            },
        }

    def _calculate_quality_metrics(
        self, results: List[BenchmarkResult]
    ) -> Dict[str, Any]:
        """Calculate quality statistics."""
        quality_scores = [r.response_quality_score for r in results]
        response_lengths = [r.response_length for r in results]

        return {
            "quality_score": {
                "mean": statistics.mean(quality_scores),
                "median": statistics.median(quality_scores),
                "std": statistics.stdev(quality_scores)
                if len(quality_scores) > 1
                else 0,
                "min": min(quality_scores),
                "max": max(quality_scores),
            },
            "response_length": {
                "mean": statistics.mean(response_lengths),
                "median": statistics.median(response_lengths),
                "std": statistics.stdev(response_lengths)
                if len(response_lengths) > 1
                else 0,
                "min": min(response_lengths),
                "max": max(response_lengths),
            },
        }

    def _calculate_variability_metrics(
        self, prompt_results: Dict[str, List[BenchmarkResult]]
    ) -> Dict[str, Any]:
        """Calculate variability across prompts."""
        prompt_variability = {}

        for prompt, results in prompt_results.items():
            response_times = [r.response_time for r in results]
            quality_scores = [r.response_quality_score for r in results]

            prompt_variability[prompt] = {
                "response_time_std": statistics.stdev(response_times)
                if len(response_times) > 1
                else 0,
                "quality_score_std": statistics.stdev(quality_scores)
                if len(quality_scores) > 1
                else 0,
                "runs_count": len(results),
            }

        # Overall variability
        all_response_times = [
            r.response_time for r in prompt_results.values() for r in r
        ]
        all_quality_scores = [
            r.response_quality_score for r in prompt_results.values() for r in r
        ]

        return {
            "overall_response_time_std": statistics.stdev(all_response_times)
            if len(all_response_times) > 1
            else 0,
            "overall_quality_score_std": statistics.stdev(all_quality_scores)
            if len(all_quality_scores) > 1
            else 0,
            "prompt_variability": prompt_variability,
        }

    def _analyze_by_prompt(
        self, prompt_results: Dict[str, List[BenchmarkResult]]
    ) -> Dict[str, Any]:
        """Analyze performance by prompt."""
        analysis = {}

        for prompt, results in prompt_results.items():
            response_times = [r.response_time for r in results]
            quality_scores = [r.response_quality_score for r in results]

            analysis[prompt] = {
                "avg_response_time": statistics.mean(response_times),
                "avg_quality_score": statistics.mean(quality_scores),
                "response_time_std": statistics.stdev(response_times)
                if len(response_times) > 1
                else 0,
                "quality_score_std": statistics.stdev(quality_scores)
                if len(quality_scores) > 1
                else 0,
                "total_runs": len(results),
            }

        return analysis

    def _analyze_errors(self, failed_results: List[BenchmarkResult]) -> Dict[str, Any]:
        """Analyze error patterns."""
        error_counts = {}
        for result in failed_results:
            error = result.error_message or "Unknown error"
            error_counts[error] = error_counts.get(error, 0) + 1

        return {"total_errors": len(failed_results), "error_types": error_counts}

    def save_results(self, output_dir: str = "benchmark_results") -> str:
        """Save benchmark results to files."""
        os.makedirs(output_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_name_safe = self.config.model_name.replace(":", "_").replace(".", "_")

        # Save detailed results
        results_file = os.path.join(
            output_dir, f"{model_name_safe}_results_{timestamp}.json"
        )
        with open(results_file, "w") as f:
            json.dump([r.__dict__ for r in self.results], f, indent=2)

        # Save analysis
        analysis = self.analyze_results()
        analysis_file = os.path.join(
            output_dir, f"{model_name_safe}_analysis_{timestamp}.json"
        )
        with open(analysis_file, "w") as f:
            json.dump(analysis, f, indent=2)

        # Save summary
        summary_file = os.path.join(
            output_dir, f"{model_name_safe}_summary_{timestamp}.txt"
        )
        with open(summary_file, "w") as f:
            f.write(self.generate_summary_report())

        print(f"\nResults saved to:")
        print(f"  Detailed results: {results_file}")
        print(f"  Analysis: {analysis_file}")
        print(f"  Summary: {summary_file}")

        return results_file

    def generate_summary_report(self) -> str:
        """Generate a human-readable summary report."""
        analysis = self.analyze_results()

        report = f"""
BENCHMARK SUMMARY REPORT
========================
Model: {self.config.model_name}
Timestamp: {datetime.now().isoformat()}

PERFORMANCE SUMMARY
------------------
Average Response Time: {analysis["performance_metrics"]["response_time"]["mean"]:.2f}s
Average Tokens/sec: {analysis["performance_metrics"]["tokens_per_second"]["mean"]:.1f}
Success Rate: {analysis["success_rate"]:.1f}% ({analysis["successful_runs"]}/{analysis["total_runs"]} runs)
"""

        # Add top performing prompts
        prompt_analysis = analysis["prompt_analysis"]
        sorted_prompts = sorted(
            prompt_analysis.items(),
            key=lambda x: x[1]["avg_quality_score"],
            reverse=True,
        )

        for i, (prompt, metrics) in enumerate(sorted_prompts[:5]):
            report += f"{i + 1}. {prompt[:60]}...\n"
            report += f"   Quality: {metrics['avg_quality_score']:.3f}, Time: {metrics['avg_response_time']:.2f}s\n"

        return report


async def benchmark_models(models: List[str], repeat_count: int = 10):
    """Benchmark multiple models and compare results."""
    all_results = {}

    for model in models:
        print(f"\n{'=' * 60}")
        print(f"BENCHMARKING MODEL: {model}")
        print(f"{'=' * 60}")

        config = BenchmarkConfig(model_name=model, repeat_count=repeat_count)

        benchmark = ModelBenchmark(config)
        await benchmark.run_full_benchmark()

        # Save results
        results_file = benchmark.save_results()
        all_results[model] = results_file

        # Print summary
        print(f"\n{benchmark.generate_summary_report()}")

    # Generate comparison report
    if len(all_results) > 1:
        await generate_comparison_report(all_results)


async def generate_comparison_report(results_files: Dict[str, str]):
    """Generate a comparison report between models."""
    print(f"\n{'=' * 60}")
    print("MODEL COMPARISON REPORT")
    print(f"{'=' * 60}")

    comparison_data = {}

    for model, results_file in results_files.items():
        if not os.path.exists(results_file):
            print(f"Warning: Results file not found for {model}: {results_file}")
            continue

        try:
            with open(results_file, "r") as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error reading results file for {model}: {e}")
            continue

        # Initialize analysis variable
        analysis = None

        # Load analysis if available, otherwise calculate
        analysis_file = results_file.replace("_results_", "_analysis_")
        if os.path.exists(analysis_file):
            try:
                with open(analysis_file, "r") as f:
                    analysis = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError) as e:
                print(f"Error reading analysis file for {model}: {e}")

        if analysis is None:
            # Calculate basic metrics from raw results
            successful_results = [r for r in data if r.get("success", False)]
            if successful_results:
                response_times = [r["response_time"] for r in successful_results]
                quality_scores = [
                    r["response_quality_score"] for r in successful_results
                ]

                analysis = {
                    "model_name": model,
                    "performance_metrics": {
                        "response_time": {
                            "mean": statistics.mean(response_times),
                            "median": statistics.median(response_times),
                            "std": statistics.stdev(response_times)
                            if len(response_times) > 1
                            else 0,
                        }
                    },
                    "quality_metrics": {
                        "quality_score": {
                            "mean": statistics.mean(quality_scores),
                            "median": statistics.median(quality_scores),
                            "std": statistics.stdev(quality_scores)
                            if len(quality_scores) > 1
                            else 0,
                        }
                    },
                    "success_rate": len(successful_results) / len(data) * 100,
                }
            else:
                # No successful results - create empty analysis
                analysis = {
                    "model_name": model,
                    "performance_metrics": {
                        "response_time": {"mean": 0, "median": 0, "std": 0}
                    },
                    "quality_metrics": {
                        "quality_score": {"mean": 0, "median": 0, "std": 0}
                    },
                    "success_rate": 0,
                }

        if analysis is not None:
            comparison_data[model] = analysis

    # Generate comparison table
    print("\nPERFORMANCE COMPARISON")
    print("-" * 80)
    print(
        f"{'Model':<15} {'Mean Time (s)':<12} {'Median Time (s)':<15} {'Quality Score':<12} {'Success Rate':<12}"
    )
    print("-" * 80)

    for model, data in comparison_data.items():
        perf = data["performance_metrics"]["response_time"]
        quality = data["quality_metrics"]["quality_score"]
        success_rate = data["success_rate"]

        print(
            f"{model:<15} {perf['mean']:<12.2f} {perf['median']:<15.2f} {quality['mean']:<12.3f} {success_rate:<12.1f}"
        )

    # Find best model
    best_performance = min(
        comparison_data.items(),
        key=lambda x: x[1]["performance_metrics"]["response_time"]["mean"],
    )
    best_quality = max(
        comparison_data.items(),
        key=lambda x: x[1]["quality_metrics"]["quality_score"]["mean"],
    )

    print(f"\nRECOMMENDATIONS:")
    print(
        f"Fastest Model: {best_performance[0]} ({best_performance[1]['performance_metrics']['response_time']['mean']:.2f}s)"
    )
    print(
        f"Best Quality: {best_quality[0]} ({best_quality[1]['quality_metrics']['quality_score']['mean']:.3f})"
    )

    # Save comparison report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    comparison_file = f"benchmark_results/model_comparison_{timestamp}.json"
    with open(comparison_file, "w") as f:
        json.dump(comparison_data, f, indent=2)

    print(f"\nComparison report saved to: {comparison_file}")


async def main():
    """Main function to run benchmarks."""
    parser = argparse.ArgumentParser(
        description="Benchmark LLM models for chatbot applications"
    )
    parser.add_argument(
        "--models", nargs="+", default=["qwen3:4b", "qwen3"], help="Models to benchmark"
    )
    parser.add_argument(
        "--repeat", type=int, default=10, help="Number of repetitions per prompt"
    )
    parser.add_argument(
        "--prompts", nargs="+", help="Custom prompts to use for benchmarking"
    )
    parser.add_argument(
        "--output", default="benchmark_results", help="Output directory for results"
    )
    parser.add_argument(
        "--temperature", type=float, default=0.7, help="Temperature for generation"
    )
    parser.add_argument(
        "--max-tokens", type=int, default=1000, help="Maximum tokens to generate"
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Show detailed output for each iteration"
    )
    parser.add_argument(
        "--show-full-responses",
        action="store_true",
        help="Show full LLM responses (not just previews)",
    )
    parser.add_argument(
        "--review-file",
        type=str,
        help="Review responses from a saved benchmark results file",
    )
    parser.add_argument(
        "--max-review-responses",
        type=int,
        help="Maximum number of responses to show when reviewing (default: all)",
    )

    args = parser.parse_args()

    # Handle review mode
    if args.review_file:
        review_responses_from_file(args.review_file, args.max_review_responses)
        return

    # Track actual results files for comparison
    results_files = {}

    # Update config with custom arguments
    for model in args.models:
        config = BenchmarkConfig(
            model_name=model,
            repeat_count=args.repeat,
            temperature=args.temperature,
            max_tokens=args.max_tokens,
            test_prompts=args.prompts,
            verbose=args.verbose,
            show_full_responses=args.show_full_responses,
        )

        print(f"\n{'=' * 60}")
        print(f"BENCHMARKING MODEL: {model}")
        print(f"{'=' * 60}")

        benchmark = ModelBenchmark(config)
        await benchmark.run_full_benchmark()

        # Save results and track the actual file path
        results_file = benchmark.save_results(args.output)
        results_files[model] = results_file

        # Print summary
        print(f"\n{benchmark.generate_summary_report()}")

    # Generate comparison if multiple models
    if len(args.models) > 1:
        await generate_comparison_report(results_files)


def review_responses_from_file(results_file: str, max_responses: int = None):
    """Review LLM responses from a saved benchmark results file."""
    try:
        with open(results_file, "r") as f:
            results = json.load(f)

        print(f"\nReviewing responses from: {results_file}")
        print(f"Total results: {len(results)}")
        print("=" * 80)

        successful_results = [r for r in results if r.get("success", False)]

        if not successful_results:
            print("No successful results found in the file.")
            return

        # Group by prompt
        prompt_responses = {}
        for result in successful_results:
            prompt = result.get("prompt", "Unknown")
            if prompt not in prompt_responses:
                prompt_responses[prompt] = []
            prompt_responses[prompt].append(result)

        response_count = 0
        for i, (prompt, responses) in enumerate(prompt_responses.items()):
            print(f"\nPROMPT {i + 1}: {prompt}")
            print("-" * 60)

            for j, result in enumerate(responses):
                if max_responses and response_count >= max_responses:
                    print(f"\n... (showing first {max_responses} responses)")
                    return

                response_content = result.get(
                    "response_content", "No response content saved"
                )
                response_time = result.get("response_time", 0)
                quality_score = result.get("response_quality_score", 0)
                tokens_per_sec = result.get("tokens_per_second", 0)

                print(f"\nIteration {j + 1}:")
                print(
                    f"  Time: {response_time:.2f}s | Quality: {quality_score:.3f} | Tokens/s: {tokens_per_sec:.1f}"
                )
                print(f"  Response:")
                print(f"  {'-' * 50}")
                print(f"  {response_content}")
                print(f"  {'-' * 50}")

                response_count += 1

            print()

    except FileNotFoundError:
        print(f"Error: File not found: {results_file}")
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in file: {e}")
    except Exception as e:
        print(f"Error reviewing file: {e}")


if __name__ == "__main__":
    asyncio.run(main())
