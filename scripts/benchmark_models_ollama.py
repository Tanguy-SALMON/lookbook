#!/usr/bin/env python3
"""
Ollama Model Benchmark Script

This script benchmarks various models through the Ollama API for chatbot applications.
It measures performance, quality, and variability metrics with comprehensive reporting.
"""

# Load environment variables from .env file
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass  # dotenv not available, use system env vars only

"""
SETUP:
1. Install Ollama: https://ollama.ai/
2. Start Ollama service: ollama serve
3. Pull models: ollama pull qwen2.5:72b
4. Set OLLAMA_HOST if not using localhost (optional)

USAGE EXAMPLES:

# Basic benchmark with default models
python3 benchmark_models_ollama.py --verbose

# Benchmark specific models
python3 benchmark_models_ollama.py --models "qwen2.5:72b" "llama3.1:8b" --verbose

# List available models
python3 benchmark_models_ollama.py --list-models

# Custom prompts with full response display
python3 benchmark_models_ollama.py --models "qwen2.5:7b" \
    --prompts "What should I wear to a wedding?" "Casual outfit for work" \
    --verbose --show-full-responses

# Review saved results
python3 benchmark_models_ollama.py --review-file benchmark_results/qwen2_5_72b_results_20231215_143022.json

# Benchmark with custom parameters
python3 benchmark_models_ollama.py \
    --models "llama3.1:8b" "qwen2.5:14b" \
    --repeat 5 --temperature 0.3 --max-tokens 500 --verbose

FEATURES:
- Real-time performance metrics display
- Quality scoring based on fashion relevance
- Token usage tracking with Ollama API
- Comprehensive comparison reports
- Response content review functionality
- System resource monitoring
- Local model benchmarking (no API costs!)
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
    timeout: float = 120.0  # Longer timeout for local models
    max_tokens: int = 1000
    temperature: float = 0.7
    repeat_count: int = 3
    test_prompts: List[str] = None
    verbose: bool = True
    show_full_responses: bool = False
    use_system_suffix: bool = True
    system_suffix: str = (
        "Answer concisely (<=120 words). Use 4-6 short bullets. No headings."
    )

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

        # Get Ollama host from environment if not provided
        if not self.ollama_host or self.ollama_host == "http://localhost:11434":
            env_host = os.getenv("OLLAMA_HOST", "")
            if env_host:
                # Ensure it's a full URL
                if not env_host.startswith("http"):
                    env_host = f"http://{env_host}"
                self.ollama_host = env_host


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
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    inference_speed: float = 0.0  # Pure generation speed (tokens/s excluding overhead)
    load_time: float = 0.0  # Model loading time if applicable


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
            "ollama_host": self.config.ollama_host,
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

    def _build_system_prompt(self, base_prompt: str) -> str:
        """Build system prompt with optional suffix for response control."""
        if self.config.use_system_suffix:
            return f"{base_prompt.strip()}\n\n{self.config.system_suffix}"
        return base_prompt

    async def _call_ollama(
        self, prompt: str
    ) -> Tuple[str, float, bool, Optional[str], int, int, int, float, float]:
        """Call Ollama API and return response, time, success, error, token counts, and inference speed."""
        start_time = time.time()
        prompt_tokens = 0
        completion_tokens = 0
        total_tokens = 0
        load_time = 0.0

        try:
            headers = {
                "Content-Type": "application/json",
            }

            # Build the final prompt with system suffix if enabled
            final_prompt = self._build_system_prompt(prompt)

            # Ollama API format
            payload = {
                "model": self.config.model_name,
                "prompt": final_prompt,
                "stream": False,
                "options": {
                    "temperature": self.config.temperature,
                    "num_predict": self.config.max_tokens,  # Ollama uses num_predict instead of max_tokens
                    "top_p": 0.9,
                    "repeat_penalty": 1.0,
                },
            }

            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                # Record when we start the actual API call
                api_call_start = time.time()

                response = await client.post(
                    f"{self.config.ollama_host}/api/generate",
                    json=payload,
                    headers=headers,
                )

                elapsed_time = time.time() - start_time
                api_call_time = time.time() - api_call_start

                if response.status_code == 200:
                    result = response.json()

                    # Extract response text
                    response_text = result.get("response", "")

                    # Extract token counts if available
                    if "prompt_eval_count" in result:
                        prompt_tokens = result.get("prompt_eval_count", 0)
                    if "eval_count" in result:
                        completion_tokens = result.get("eval_count", 0)
                    total_tokens = prompt_tokens + completion_tokens

                    # Extract timing information
                    load_time = (
                        result.get("load_duration", 0) / 1e9
                    )  # Convert from nanoseconds
                    prompt_eval_duration = result.get("prompt_eval_duration", 0) / 1e9
                    eval_duration = result.get("eval_duration", 0) / 1e9

                    # Calculate inference speed (pure generation speed)
                    # Use eval_duration for pure generation time if available
                    if eval_duration > 0 and completion_tokens > 0:
                        inference_speed = completion_tokens / eval_duration
                    elif api_call_time > 0 and completion_tokens > 0:
                        inference_speed = completion_tokens / api_call_time
                    else:
                        inference_speed = 0.0

                    return (
                        response_text,
                        elapsed_time,
                        True,
                        None,
                        prompt_tokens,
                        completion_tokens,
                        total_tokens,
                        load_time,
                        inference_speed,
                    )
                else:
                    error_text = response.text
                    try:
                        error_json = response.json()
                        if "error" in error_json:
                            error_text = error_json["error"]
                    except:
                        pass

                    return (
                        "",
                        elapsed_time,
                        False,
                        f"HTTP {response.status_code}: {error_text}",
                        0,
                        0,
                        0,
                        0.0,
                        0.0,
                    )

        except Exception as e:
            elapsed_time = time.time() - start_time
            return "", elapsed_time, False, str(e), 0, 0, 0, 0.0, 0.0

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
        (
            response,
            response_time,
            success,
            error,
            prompt_tokens,
            completion_tokens,
            total_tokens,
            load_time,
            inference_speed,
        ) = await self._call_ollama(prompt)

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

        # Calculate tokens per second using actual token counts from API
        if completion_tokens > 0:
            tokens_per_second = (
                completion_tokens / response_time if response_time > 0 else 0
            )
        else:
            # Fallback to estimation if no token count available
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
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            inference_speed=inference_speed,
            load_time=load_time,
        )

    async def run_full_benchmark(self) -> List[BenchmarkResult]:
        """Run complete benchmark suite."""
        print(f"Starting benchmark for {self.config.model_name}")
        print(f"Ollama Host: {self.config.ollama_host}")
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
                    print(f"✓ ({result.response_time:.2f}s)", end="")
                    if self.config.verbose:
                        print(
                            f", {result.tokens_per_second:.1f} tokens/s total, {result.inference_speed:.1f} tokens/s inference"
                        )
                        print(f"    Quality Score: {result.response_quality_score:.3f}")
                        print(
                            f"    Tokens: {result.completion_tokens} completion, {result.total_tokens} total"
                        )
                        if result.load_time > 0:
                            print(f"    Load Time: {result.load_time:.2f}s")

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
                        print()  # Add blank line between iterations
                    else:
                        print()  # Just newline for non-verbose
                else:
                    print(f"✗ ({result.error_message})")

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
        inference_speeds = [r.inference_speed for r in results]
        load_times = [r.load_time for r in results if r.load_time > 0]
        memory_usage = [r.memory_usage_mb for r in results]
        cpu_usage = [r.cpu_usage_percent for r in results]

        metrics = {
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
            "inference_speed": {
                "mean": statistics.mean(inference_speeds),
                "median": statistics.median(inference_speeds),
                "std": statistics.stdev(inference_speeds)
                if len(inference_speeds) > 1
                else 0,
                "min": min(inference_speeds),
                "max": max(inference_speeds),
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

        # Add load time metrics if available
        if load_times:
            metrics["load_time"] = {
                "mean": statistics.mean(load_times),
                "median": statistics.median(load_times),
                "std": statistics.stdev(load_times) if len(load_times) > 1 else 0,
                "min": min(load_times),
                "max": max(load_times),
            }

        return metrics

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
        model_name_safe = (
            self.config.model_name.replace(":", "_").replace(".", "_").replace("/", "_")
        )

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

        # Calculate token statistics
        successful_results = [r for r in self.results if r.success]
        if successful_results:
            total_prompt_tokens = sum(r.prompt_tokens for r in successful_results)
            total_completion_tokens = sum(
                r.completion_tokens for r in successful_results
            )
            total_tokens = sum(r.total_tokens for r in successful_results)
            avg_prompt_tokens = total_prompt_tokens / len(successful_results)
            avg_completion_tokens = total_completion_tokens / len(successful_results)
            avg_load_time = (
                statistics.mean(
                    [r.load_time for r in successful_results if r.load_time > 0]
                )
                if any(r.load_time > 0 for r in successful_results)
                else 0
            )
        else:
            total_prompt_tokens = total_completion_tokens = total_tokens = 0
            avg_prompt_tokens = avg_completion_tokens = avg_load_time = 0

        report = f"""
OLLAMA BENCHMARK SUMMARY
========================
Model: {self.config.model_name}
Ollama Host: {self.config.ollama_host}
Timestamp: {datetime.now().isoformat()}

PERFORMANCE SUMMARY
------------------
Average Response Time: {analysis["performance_metrics"]["response_time"]["mean"]:.2f}s
Average Total Tokens/sec: {analysis["performance_metrics"]["tokens_per_second"]["mean"]:.1f}
Average Inference Speed: {analysis["performance_metrics"]["inference_speed"]["mean"]:.1f} tokens/s
Response Time P95: {analysis["performance_metrics"]["response_time"]["p95"]:.2f}s
Total Tokens Used: {total_tokens:,} (Prompt: {total_prompt_tokens:,}, Completion: {total_completion_tokens:,})
Success Rate: {analysis["success_rate"]:.1f}% ({analysis["successful_runs"]}/{analysis["total_runs"]} runs)"""

        if avg_load_time > 0:
            report += f"\nAverage Load Time: {avg_load_time:.2f}s"

        report += f"""

QUALITY SUMMARY
--------------
Average Quality Score: {analysis["quality_metrics"]["quality_score"]["mean"]:.3f}/1.000
Average Response Length: {analysis["quality_metrics"]["response_length"]["mean"]:.0f} characters

TOP PERFORMING PROMPTS
---------------------"""

        # Add top performing prompts
        prompt_analysis = analysis["prompt_analysis"]
        sorted_prompts = sorted(
            prompt_analysis.items(),
            key=lambda x: x[1]["avg_quality_score"],
            reverse=True,
        )

        for i, (prompt, metrics) in enumerate(sorted_prompts[:5]):
            report += f"\n{i + 1}. {prompt[:70]}..."
            report += f"\n   Quality: {metrics['avg_quality_score']:.3f}, Time: {metrics['avg_response_time']:.2f}s"

        return report


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
    print("-" * 105)
    print(
        f"{'Model':<30} {'Mean Time (s)':<13} {'Median Time (s)':<15} {'Inference (t/s)':<15} {'Quality Score':<15} {'Success Rate':<13}"
    )
    print("-" * 105)

    for model, data in comparison_data.items():
        perf = data["performance_metrics"]["response_time"]
        inference = data["performance_metrics"].get("inference_speed", {"mean": 0})
        quality = data["quality_metrics"]["quality_score"]
        success_rate = data["success_rate"]

        print(
            f"{model:<30} {perf['mean']:<13.2f} {perf['median']:<15.2f} {inference['mean']:<15.1f} {quality['mean']:<15.3f} {success_rate:<13.1f}"
        )

    # Find best models for different metrics
    best_response_time = min(
        comparison_data.items(),
        key=lambda x: x[1]["performance_metrics"]["response_time"]["mean"],
    )
    best_inference_speed = max(
        comparison_data.items(),
        key=lambda x: x[1]["performance_metrics"].get("inference_speed", {"mean": 0})[
            "mean"
        ],
    )
    best_quality = max(
        comparison_data.items(),
        key=lambda x: x[1]["quality_metrics"]["quality_score"]["mean"],
    )

    print(f"\nRECOMMENDATIONS:")
    print(
        f"Fastest Response Time: {best_response_time[0]} ({best_response_time[1]['performance_metrics']['response_time']['mean']:.2f}s)"
    )
    print(
        f"Highest Inference Speed: {best_inference_speed[0]} ({best_inference_speed[1]['performance_metrics'].get('inference_speed', {'mean': 0})['mean']:.1f} tokens/s)"
    )
    print(
        f"Best Quality: {best_quality[0]} ({best_quality[1]['quality_metrics']['quality_score']['mean']:.3f})"
    )

    print(f"\nSPEED METRICS EXPLAINED:")
    print("• Response Time = Total time to get answer (includes model loading)")
    print("• Inference Speed = Pure token generation speed (excludes overhead)")
    print("• Local models may have loading time on first run")

    # Save comparison report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    comparison_file = f"benchmark_results/ollama_model_comparison_{timestamp}.json"
    with open(comparison_file, "w") as f:
        json.dump(comparison_data, f, indent=2)

    print(f"\nComparison report saved to: {comparison_file}")


async def main():
    """Main function to run benchmarks."""
    parser = argparse.ArgumentParser(
        description="Benchmark LLM models via Ollama API for chatbot applications"
    )
    parser.add_argument(
        "--models",
        nargs="+",
        default=["qwen2.5:7b", "llama3.1:8b"],
        help="Models to benchmark (Ollama format)",
    )
    parser.add_argument(
        "--repeat", type=int, default=3, help="Number of repetitions per prompt"
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
        "--no-system-suffix",
        action="store_true",
        help="Disable system suffix for response length control",
    )
    parser.add_argument(
        "--system-suffix",
        type=str,
        default="Answer concisely (<=120 words). Use 4-6 short bullets. No headings.",
        help="Custom system suffix to control response format",
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
    parser.add_argument(
        "--ollama-host",
        type=str,
        default="http://localhost:11434",
        help="Ollama host URL (can also be set via OLLAMA_HOST env var)",
    )
    parser.add_argument(
        "--list-models",
        action="store_true",
        help="List available models from Ollama and exit",
    )

    args = parser.parse_args()

    # Handle list models mode
    if args.list_models:
        await list_available_models(args.ollama_host)
        return

    # Handle review mode
    if args.review_file:
        review_responses_from_file(args.review_file or "", args.max_review_responses)
        return

    # Track actual results files for comparison
    results_files = {}

    # Update config with custom arguments
    for model in args.models:
        config = BenchmarkConfig(
            model_name=model,
            ollama_host=args.ollama_host,
            repeat_count=args.repeat,
            temperature=args.temperature,
            max_tokens=args.max_tokens,
            test_prompts=args.prompts,
            verbose=args.verbose,
            show_full_responses=args.show_full_responses,
            use_system_suffix=not args.no_system_suffix,
            system_suffix=args.system_suffix,
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


async def list_available_models(ollama_host: str = "http://localhost:11434"):
    """List available models from Ollama."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{ollama_host}/api/tags")

            if response.status_code == 200:
                result = response.json()
                models = result.get("models", [])

                print(f"\nAvailable Ollama Models ({len(models)} total):")
                print("=" * 60)
                print(f"Host: {ollama_host}")
                print()

                if not models:
                    print(
                        "No models found. Pull models using: ollama pull <model_name>"
                    )
                    print("Popular models:")
                    print("  ollama pull qwen2.5:7b")
                    print("  ollama pull llama3.1:8b")
                    print("  ollama pull mistral:7b")
                    return

                # Sort by name for consistent output
                models.sort(key=lambda x: x.get("name", ""))

                print(
                    f"{'Model Name':<25} {'Size':<10} {'Modified':<20} {'Family':<15}"
                )
                print("-" * 80)

                for model in models:
                    name = model.get("name", "Unknown")
                    size = model.get("size", 0)
                    modified = model.get("modified_at", "")
                    details = model.get("details", {})
                    family = details.get("family", "Unknown")

                    # Format size
                    if size > 1e9:
                        size_str = f"{size / 1e9:.1f}GB"
                    elif size > 1e6:
                        size_str = f"{size / 1e6:.0f}MB"
                    else:
                        size_str = f"{size}B"

                    # Format modified date
                    if modified:
                        try:
                            from datetime import datetime

                            dt = datetime.fromisoformat(modified.replace("Z", "+00:00"))
                            modified_str = dt.strftime("%Y-%m-%d %H:%M")
                        except:
                            modified_str = modified[:16]
                    else:
                        modified_str = "Unknown"

                    print(f"{name:<25} {size_str:<10} {modified_str:<20} {family:<15}")

                print(
                    f"\nUsage: --models {models[0]['name']} {models[1]['name'] if len(models) > 1 else ''}"
                )

            else:
                print(f"Error fetching models: HTTP {response.status_code}")
                print(response.text)
                print("\nMake sure Ollama is running:")
                print("  ollama serve")

    except Exception as e:
        print(f"Error listing models: {e}")
        print("\nMake sure Ollama is running and accessible:")
        print(f"  Host: {ollama_host}")
        print("  Command: ollama serve")


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
                inference_speed = result.get("inference_speed", 0)
                load_time = result.get("load_time", 0)

                print(f"\nIteration {j + 1}:")
                print(
                    f"  Time: {response_time:.2f}s | Quality: {quality_score:.3f} | Tokens/s: {tokens_per_sec:.1f} | Inference: {inference_speed:.1f}"
                )
                if load_time > 0:
                    print(f"  Load Time: {load_time:.2f}s")
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
