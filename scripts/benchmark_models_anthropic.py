#!/usr/bin/env python3
"""
Anthropic Claude Model Benchmark Script

This script benchmarks various Claude models through the Anthropic API for chatbot applications.
It measures performance, quality, and variability metrics with comprehensive reporting.
"""

# Load environment variables from .env file
try:
    from pathlib import Path
    from dotenv import load_dotenv

    # Try to load .env from the project root directory
    project_root = Path(__file__).parent.parent
    env_path = project_root / ".env"
    load_dotenv(dotenv_path=env_path)
except ImportError:
    pass  # dotenv not available, use system env vars only

# Import official Anthropic SDK
try:
    import anthropic
except ImportError:
    print("❌ anthropic package not found. Install it with: poetry add anthropic")
    sys.exit(1)

"""
SETUP:
1. Get your API key from https://console.anthropic.com/
2. Set environment variable: export ANTHROPIC_API_KEY="your-api-key"
3. Or use --api-key parameter

USAGE EXAMPLES:

# Basic benchmark with default models
python3 benchmark_models_anthropic.py --verbose

# Benchmark specific models
python3 benchmark_models_anthropic.py --models "claude-3-haiku-20240307" "claude-3-sonnet-20240229" --verbose

# List available models
python3 benchmark_models_anthropic.py --list-models

# Custom prompts with full response display
python3 benchmark_models_anthropic.py --models "claude-3-opus-20240229" \
    --prompts "What should I wear to a wedding?" "Casual outfit for work" \
    --verbose --show-full-responses

# Review saved results
python3 benchmark_models_anthropic.py --review-file benchmark_results/claude_3_haiku_results_20231215_143022.json

# Benchmark with custom parameters and sleep between requests
python3 benchmark_models_anthropic.py \
    --models "claude-3-sonnet-20240229" "claude-3-opus-20240229" \
    --repeat 5 --temperature 0.3 --max-tokens 500 --verbose \
    --request-delay 2.0

# Benchmark with custom retry settings (15 min max, faster backoff)
python3 benchmark_models_anthropic.py \
    --models "claude-3-opus-20240229" \
    --max-retry-time 900 --base-retry-delay 0.5 --max-retry-delay 120 \
    --verbose

FEATURES:
- Real-time performance metrics display
- Quality scoring based on fashion relevance
- Token usage tracking with Anthropic API
- Comprehensive comparison reports
- Response content review functionality
- System resource monitoring
- Native Claude model support
- Configurable sleep between API requests
- Exponential backoff retry strategy with 30-minute max timeout
"""

import asyncio
import json
import time
import statistics
import os
import sys
import random
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import argparse
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
    anthropic_api_key: str = ""
    anthropic_base_url: str = "https://api.anthropic.com"
    timeout: float = 60.0
    max_tokens: int = 1000
    temperature: float = 0.7
    repeat_count: int = 3
    retry_on_rate_limit: bool = True
    rate_limit_delay: float = 60.0  # Wait time for rate limits
    request_delay: float = 0.0  # Sleep time between requests
    max_retry_time: float = 1800.0  # Maximum retry time (30 minutes)
    base_retry_delay: float = 1.0  # Base delay for exponential backoff
    max_retry_delay: float = 300.0  # Maximum delay between retries (5 minutes)
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

        # Get API key from environment if not provided
        if not self.anthropic_api_key:
            self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY", "") or os.getenv(
                "CLAUDE_API_KEY", ""
            )


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
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    estimated_cost: float = 0.0
    inference_speed: float = 0.0  # Pure generation speed (tokens/s excluding overhead)


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

    def _build_system_prompt(self, base_prompt: str) -> str:
        """Build system prompt with optional suffix for response control."""
        if self.config.use_system_suffix:
            return f"{base_prompt.strip()}\n\n{self.config.system_suffix}"
        return base_prompt

    async def _call_anthropic(
        self, prompt: str
    ) -> Tuple[str, float, bool, Optional[str], int, int, int, float, float]:
        """Call Anthropic API using official SDK and return response, time, success, error, token counts, cost, and inference speed."""
        start_time = time.time()
        input_tokens = 0
        output_tokens = 0
        total_tokens = 0

        if not self.config.anthropic_api_key:
            elapsed_time = time.time() - start_time
            return (
                "",
                elapsed_time,
                False,
                "Anthropic API key not provided",
                0,
                0,
                0,
                0.0,
                0.0,
            )

        # Clean the API key to remove any whitespace
        clean_api_key = self.config.anthropic_api_key.strip()

        # Exponential backoff retry logic
        retry_delay = self.config.base_retry_delay
        retry_start_time = time.time()

        while True:
            try:
                # Create Anthropic client with cleaned API key
                client = anthropic.Anthropic(api_key=clean_api_key)

                # Build the final prompt with system suffix if enabled
                final_prompt = self._build_system_prompt(prompt)

                # Record when we start the actual API call
                api_call_start = time.time()

                # Call Anthropic API using official SDK
                message = client.messages.create(
                    model=self.config.model_name,
                    max_tokens=self.config.max_tokens,
                    messages=[{"role": "user", "content": final_prompt}],
                    temperature=self.config.temperature,
                )

                elapsed_time = time.time() - start_time
                api_call_time = time.time() - api_call_start

                # Extract response text
                response_text = ""
                if hasattr(message, "content") and message.content:
                    for content_block in message.content:
                        if hasattr(content_block, "text"):
                            response_text += content_block.text

                # Extract token usage information
                estimated_cost = 0.0
                if hasattr(message, "usage") and message.usage:
                    input_tokens = message.usage.input_tokens
                    output_tokens = message.usage.output_tokens
                    total_tokens = input_tokens + output_tokens

                    # Calculate cost based on Claude pricing
                    estimated_cost = self._estimate_cost(input_tokens, output_tokens)

                # Calculate inference speed (pure generation speed)
                inference_speed = (
                    output_tokens / api_call_time
                    if api_call_time > 0 and output_tokens > 0
                    else 0.0
                )

                return (
                    response_text,
                    elapsed_time,
                    True,
                    None,
                    input_tokens,
                    output_tokens,
                    total_tokens,
                    estimated_cost,
                    inference_speed,
                )

            except anthropic.RateLimitError:
                # Rate limiting - use exponential backoff if enabled
                if not self.config.retry_on_rate_limit:
                    elapsed_time = time.time() - start_time
                    return (
                        "",
                        elapsed_time,
                        False,
                        "Rate limited and retry disabled",
                        0,
                        0,
                        0,
                        0.0,
                        0.0,
                    )

                # Check if we've exceeded maximum retry time
                total_retry_time = time.time() - retry_start_time
                if total_retry_time >= self.config.max_retry_time:
                    elapsed_time = time.time() - start_time
                    return (
                        "",
                        elapsed_time,
                        False,
                        f"Rate limit retry timeout after {total_retry_time:.1f}s (max: {self.config.max_retry_time:.1f}s)",
                        0,
                        0,
                        0,
                        0.0,
                        0.0,
                    )

                # Add jitter to prevent thundering herd
                jitter = random.uniform(0.5, 1.5)
                actual_delay = min(retry_delay * jitter, self.config.max_retry_delay)

                if self.config.verbose:
                    print(
                        f"    Rate limited, waiting {actual_delay:.1f}s (total retry time: {total_retry_time:.1f}s)"
                    )

                await asyncio.sleep(actual_delay)

                # Exponential backoff: double the delay for next time
                retry_delay = min(retry_delay * 2, self.config.max_retry_delay)
                continue  # Retry the request

            except anthropic.AuthenticationError as e:
                elapsed_time = time.time() - start_time
                return (
                    "",
                    elapsed_time,
                    False,
                    "Authentication error: invalid API key",
                    0,
                    0,
                    0,
                    0.0,
                    0.0,
                )

            except anthropic.PermissionDeniedError:
                elapsed_time = time.time() - start_time
                return (
                    "",
                    elapsed_time,
                    False,
                    "Permission denied: insufficient access",
                    0,
                    0,
                    0,
                    0.0,
                    0.0,
                )

            except anthropic.NotFoundError:
                elapsed_time = time.time() - start_time
                return (
                    "",
                    elapsed_time,
                    False,
                    f"Model '{self.config.model_name}' not found",
                    0,
                    0,
                    0,
                    0.0,
                    0.0,
                )

            except anthropic.InternalServerError:
                # Server errors - retry with backoff if enabled
                if not self.config.retry_on_rate_limit:
                    elapsed_time = time.time() - start_time
                    return (
                        "",
                        elapsed_time,
                        False,
                        "Internal server error",
                        0,
                        0,
                        0,
                        0.0,
                        0.0,
                    )

                # Check if we've exceeded maximum retry time
                total_retry_time = time.time() - retry_start_time
                if total_retry_time >= self.config.max_retry_time:
                    elapsed_time = time.time() - start_time
                    return (
                        "",
                        elapsed_time,
                        False,
                        "Server error retry timeout",
                        0,
                        0,
                        0,
                        0.0,
                        0.0,
                    )

                # Add jitter and retry
                jitter = random.uniform(0.5, 1.5)
                actual_delay = min(retry_delay * jitter, self.config.max_retry_delay)

                if self.config.verbose:
                    print(f"    Server error, retrying in {actual_delay:.1f}s")

                await asyncio.sleep(actual_delay)
                retry_delay = min(retry_delay * 2, self.config.max_retry_delay)
                continue

            except Exception as e:
                # For other errors, retry with backoff if enabled
                if self.config.retry_on_rate_limit:
                    total_retry_time = time.time() - retry_start_time
                    if total_retry_time < self.config.max_retry_time:
                        jitter = random.uniform(0.5, 1.5)
                        actual_delay = min(
                            retry_delay * jitter, self.config.max_retry_delay
                        )

                        if self.config.verbose:
                            print(
                                f"    Error, retrying in {actual_delay:.1f}s: {str(e)}"
                            )

                        await asyncio.sleep(actual_delay)
                        retry_delay = min(retry_delay * 2, self.config.max_retry_delay)
                        continue

                elapsed_time = time.time() - start_time
                return "", elapsed_time, False, str(e), 0, 0, 0, 0.0, 0.0

            # If we get here without success, break the retry loop
            break

    def _estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost based on Claude pricing."""
        # Claude pricing (as of 2025) - varies by model
        # Haiku: $0.00025/1K input, $0.00125/1K output
        # Sonnet 3/3.5: $0.003/1K input, $0.015/1K output
        # Opus 3: $0.015/1K input, $0.075/1K output
        # Claude 4: Higher pricing (estimated)

        # Use Sonnet 4 pricing as default
        input_cost_per_1k = 0.003
        output_cost_per_1k = 0.015

        # Adjust pricing based on model
        model_lower = self.config.model_name.lower()
        if "haiku" in model_lower:
            input_cost_per_1k = 0.00025
            output_cost_per_1k = 0.00125
        elif "opus-4" in model_lower:
            # Claude 4 Opus
            input_cost_per_1k = 0.015
            output_cost_per_1k = 0.075
        elif "opus" in model_lower and "4" not in model_lower:
            # Claude 3 Opus
            input_cost_per_1k = 0.015
            output_cost_per_1k = 0.075
        elif "sonnet-4" in model_lower or "3-7-sonnet" in model_lower:
            # Claude 4 Sonnet and Claude 3.7 Sonnet
            input_cost_per_1k = 0.003
            output_cost_per_1k = 0.015

        input_cost = (input_tokens / 1000.0) * input_cost_per_1k
        output_cost = (output_tokens / 1000.0) * output_cost_per_1k
        return input_cost + output_cost

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
            input_tokens,
            output_tokens,
            total_tokens,
            estimated_cost,
            inference_speed,
        ) = await self._call_anthropic(prompt)

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
        if output_tokens > 0:
            tokens_per_second = (
                output_tokens / response_time if response_time > 0 else 0
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
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            estimated_cost=estimated_cost,
            inference_speed=inference_speed,
        )

    async def run_full_benchmark(self) -> List[BenchmarkResult]:
        """Run complete benchmark suite."""
        print(f"Starting benchmark for {self.config.model_name}")
        print(
            f"Running {self.config.repeat_count} iterations for each of {len(self.config.test_prompts)} prompts"
        )

        if self.config.request_delay > 0:
            print(f"Request delay: {self.config.request_delay}s between API calls")

        if self.config.retry_on_rate_limit:
            print(
                f"Retry settings: Max {self.config.max_retry_time / 60:.1f} min, base delay {self.config.base_retry_delay}s"
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
                            f"    Tokens: {result.output_tokens} output, {result.total_tokens} total"
                        )

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

                # Sleep between requests if configured
                if self.config.request_delay > 0 and (
                    j < self.config.repeat_count - 1
                    or i < len(self.config.test_prompts) - 1
                ):
                    await asyncio.sleep(self.config.request_delay)

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
            self.config.model_name.replace(":", "_")
            .replace(".", "_")
            .replace("/", "_")
            .replace("-", "_")
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

        # Save summary (with error handling)
        summary_file = os.path.join(
            output_dir, f"{model_name_safe}_summary_{timestamp}.txt"
        )
        try:
            with open(summary_file, "w") as f:
                f.write(self.generate_summary_report())
        except Exception as e:
            # If summary generation fails, create a basic error summary
            with open(summary_file, "w") as f:
                f.write(f"Error generating summary: {e}\n")
                f.write(f"Model: {self.config.model_name}\n")
                f.write(f"Total runs: {len(self.results)}\n")
                successful = len([r for r in self.results if r.success])
                f.write(f"Successful runs: {successful}\n")
                f.write(f"Failed runs: {len(self.results) - successful}\n")

        print(f"\nResults saved to:")
        print(f"  Detailed results: {results_file}")
        print(f"  Analysis: {analysis_file}")
        print(f"  Summary: {summary_file}")

        return results_file

    def generate_summary_report(self) -> str:
        """Generate a human-readable summary report."""
        analysis = self.analyze_results()

        # Check if analysis failed due to no successful results
        if "error" in analysis:
            # Generate error report
            failed_results = [r for r in self.results if not r.success]
            error_counts = {}
            for result in failed_results:
                error = result.error_message or "Unknown error"
                error_counts[error] = error_counts.get(error, 0) + 1

            report = f"""
ANTHROPIC CLAUDE BENCHMARK SUMMARY
=================================
Model: {self.config.model_name}
Timestamp: {datetime.now().isoformat()}

⚠️  BENCHMARK FAILED - NO SUCCESSFUL RUNS
==========================================
Total Attempts: {len(self.results)}
Success Rate: 0.0% (0/{len(self.results)} runs)

ERROR ANALYSIS
--------------"""

            for error, count in error_counts.items():
                report += f"\n• {error}: {count} occurrences"

            report += f"""

COMMON SOLUTIONS
----------------
• HTTP 429 (Rate Limiting): Wait and retry, or use different model
• HTTP 401 (Unauthorized): Check your API key
• HTTP 403 (Forbidden): Check model access permissions
• Timeout errors: Increase timeout or try smaller prompts
• Network errors: Check internet connection

TROUBLESHOOTING TIPS
--------------------
• Try a different model: --models "claude-3-haiku-20240307"
• Reduce request rate: --repeat 1
• Use shorter prompts: --prompts "Quick outfit advice"
• Check API status: https://status.anthropic.com/
"""
            return report

        # Calculate token statistics and costs
        successful_results = [r for r in self.results if r.success]
        if successful_results:
            total_input_tokens = sum(r.input_tokens for r in successful_results)
            total_output_tokens = sum(r.output_tokens for r in successful_results)
            total_tokens = sum(r.total_tokens for r in successful_results)
            total_estimated_cost = sum(r.estimated_cost for r in successful_results)
            avg_input_tokens = total_input_tokens / len(successful_results)
            avg_output_tokens = total_output_tokens / len(successful_results)
            avg_cost_per_request = total_estimated_cost / len(successful_results)
        else:
            total_input_tokens = total_output_tokens = total_tokens = 0
            total_estimated_cost = avg_input_tokens = avg_output_tokens = (
                avg_cost_per_request
            ) = 0

        report = f"""
ANTHROPIC CLAUDE BENCHMARK SUMMARY
=================================
Model: {self.config.model_name}
Timestamp: {datetime.now().isoformat()}

PERFORMANCE SUMMARY
------------------
Average Response Time: {analysis["performance_metrics"]["response_time"]["mean"]:.2f}s
Average Total Tokens/sec: {analysis["performance_metrics"]["tokens_per_second"]["mean"]:.1f}
Average Inference Speed: {analysis["performance_metrics"]["inference_speed"]["mean"]:.1f} tokens/s
Response Time P95: {analysis["performance_metrics"]["response_time"]["p95"]:.2f}s
Total Tokens Used: {total_tokens:,} (Input: {total_input_tokens:,}, Output: {total_output_tokens:,})
Estimated Total Cost: ${total_estimated_cost:.4f} (Avg per request: ${avg_cost_per_request:.4f})
Success Rate: {analysis["success_rate"]:.1f}% ({analysis["successful_runs"]}/{analysis["total_runs"]} runs)

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
    print("• Response Time = Total time to get answer (includes network latency)")
    print("• Inference Speed = Pure token generation speed (excludes overhead)")
    print("• A model can have fast inference but slow response due to network/overhead")

    # Save comparison report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    comparison_file = f"benchmark_results/model_comparison_{timestamp}.json"
    with open(comparison_file, "w") as f:
        json.dump(comparison_data, f, indent=2)

    print(f"\nComparison report saved to: {comparison_file}")


async def main():
    """Main function to run benchmarks."""
    parser = argparse.ArgumentParser(
        description="Benchmark Claude models via Anthropic API for chatbot applications"
    )
    parser.add_argument(
        "--models",
        nargs="+",
        default=["claude-3-5-sonnet-20241022"],
        help="Claude models to benchmark (e.g., claude-3-5-haiku-20241022)",
    )
    parser.add_argument(
        "--repeat", type=int, default=3, help="Number of repetitions per prompt"
    )
    parser.add_argument(
        "--no-rate-limit-retry",
        action="store_true",
        help="Disable automatic retry on rate limits",
    )
    parser.add_argument(
        "--rate-limit-delay",
        type=float,
        default=60.0,
        help="Wait time in seconds when rate limited (default: 60, deprecated - use exponential backoff instead)",
    )
    parser.add_argument(
        "--request-delay",
        type=float,
        default=0.0,
        help="Sleep time in seconds between API requests (default: 0)",
    )
    parser.add_argument(
        "--max-retry-time",
        type=float,
        default=1800.0,
        help="Maximum total retry time in seconds (default: 1800 = 30 minutes)",
    )
    parser.add_argument(
        "--base-retry-delay",
        type=float,
        default=1.0,
        help="Base delay for exponential backoff in seconds (default: 1.0)",
    )
    parser.add_argument(
        "--max-retry-delay",
        type=float,
        default=300.0,
        help="Maximum delay between retries in seconds (default: 300 = 5 minutes)",
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
        "--api-key",
        type=str,
        help="Anthropic API key (can also be set via ANTHROPIC_API_KEY env var)",
    )
    parser.add_argument(
        "--list-models",
        action="store_true",
        help="List available Claude models and exit",
    )

    args = parser.parse_args()

    # Handle list models mode
    if args.list_models:
        list_available_models()
        return

    # Handle review mode
    if args.review_file:
        review_responses_from_file(args.review_file or "", args.max_review_responses)
        return

    # Track actual results files for comparison
    results_files = {}

    # Update config with custom arguments
    for model in args.models:
        api_key = (
            args.api_key
            or os.getenv("ANTHROPIC_API_KEY", "")
            or os.getenv("CLAUDE_API_KEY", "")
        )

        if not api_key:
            print("Error: Anthropic API key is required!")
            print("Options:")
            print("  1. Set ANTHROPIC_API_KEY or CLAUDE_API_KEY environment variable")
            print("  2. Use --api-key parameter")
            print("  3. Get your API key from: https://console.anthropic.com/")
            return

        # Validate model name against known working models
        valid_models = [
            "claude-opus-4-1-20250805",
            "claude-opus-4-20250514",
            "claude-sonnet-4-20250514",
            "claude-3-7-sonnet-20250219",
            "claude-3-5-sonnet-20241022",
            "claude-3-5-sonnet-20240620",
            "claude-3-5-haiku-20241022",
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
        ]
        if model not in valid_models:
            print(
                f"Warning: Model '{model}' is not in the list of known working models."
            )
            print(f"Valid models include: {', '.join(valid_models[:3])}...")
            print("Run --list-models for full list")
            print("Proceeding anyway...")

        config = BenchmarkConfig(
            model_name=model,
            anthropic_api_key=api_key,
            repeat_count=args.repeat,
            temperature=args.temperature,
            max_tokens=args.max_tokens,
            test_prompts=args.prompts,
            verbose=args.verbose,
            show_full_responses=args.show_full_responses,
            use_system_suffix=not args.no_system_suffix,
            system_suffix=args.system_suffix,
            retry_on_rate_limit=not args.no_rate_limit_retry,
            rate_limit_delay=args.rate_limit_delay,
            request_delay=args.request_delay,
            max_retry_time=args.max_retry_time,
            base_retry_delay=args.base_retry_delay,
            max_retry_delay=args.max_retry_delay,
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


def list_available_models():
    """List available Claude models."""
    print("\nAvailable Claude Models:")
    print("=" * 40)

    models = [
        {
            "id": "claude-opus-4-1-20250805",
            "name": "Claude Opus 4.1",
            "description": "Latest and most capable model - best for coding and complex tasks",
            "input_cost": "$15/1M tokens",
            "output_cost": "$75/1M tokens",
        },
        {
            "id": "claude-opus-4-20250514",
            "name": "Claude Opus 4",
            "description": "Most capable Claude 4 model for complex reasoning",
            "input_cost": "$15/1M tokens",
            "output_cost": "$75/1M tokens",
        },
        {
            "id": "claude-sonnet-4-20250514",
            "name": "Claude Sonnet 4",
            "description": "Balanced Claude 4 model with superior coding",
            "input_cost": "$3/1M tokens",
            "output_cost": "$15/1M tokens",
        },
        {
            "id": "claude-3-7-sonnet-20250219",
            "name": "Claude 3.7 Sonnet",
            "description": "First hybrid reasoning model with extended thinking",
            "input_cost": "$3/1M tokens",
            "output_cost": "$15/1M tokens",
        },
        {
            "id": "claude-3-5-sonnet-20241022",
            "name": "Claude 3.5 Sonnet",
            "description": "Enhanced version of Sonnet (deprecated soon)",
            "input_cost": "$3/1M tokens",
            "output_cost": "$15/1M tokens",
        },
        {
            "id": "claude-3-5-sonnet-20240620",
            "name": "Claude 3.5 Sonnet (June)",
            "description": "Previous version of Claude 3.5 Sonnet",
            "input_cost": "$3/1M tokens",
            "output_cost": "$15/1M tokens",
        },
        {
            "id": "claude-3-5-haiku-20241022",
            "name": "Claude 3.5 Haiku",
            "description": "Fast and affordable model",
            "input_cost": "$0.25/1M tokens",
            "output_cost": "$1.25/1M tokens",
        },
        {
            "id": "claude-3-opus-20240229",
            "name": "Claude 3 Opus",
            "description": "Most capable Claude 3 model",
            "input_cost": "$15/1M tokens",
            "output_cost": "$75/1M tokens",
        },
        {
            "id": "claude-3-sonnet-20240229",
            "name": "Claude 3 Sonnet",
            "description": "Balanced Claude 3 model",
            "input_cost": "$3/1M tokens",
            "output_cost": "$15/1M tokens",
        },
        {
            "id": "claude-3-haiku-20240307",
            "name": "Claude 3 Haiku",
            "description": "Fastest Claude 3 model",
            "input_cost": "$0.25/1M tokens",
            "output_cost": "$1.25/1M tokens",
        },
    ]

    for model in models:
        print(f"\n{model['name']} ({model['id']})")
        print(f"  Description: {model['description']}")
        print(f"  Pricing: {model['input_cost']} input, {model['output_cost']} output")

    print(f"Usage examples:")
    print(f"  --models claude-sonnet-4-20250514")
    print(f"  --models claude-3-5-haiku-20241022 claude-sonnet-4-20250514")
    print(f"  --models claude-opus-4-1-20250805  # Most capable model")

    print(f"\nNOTE: Claude 4 models are now available! Try the latest:")
    print(f'• For best performance: --models "claude-opus-4-1-20250805"')
    print(f'• For balanced use: --models "claude-sonnet-4-20250514"')


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
