#!/usr/bin/env python3
"""
OpenRouter Model Listing Script with Live Metrics

This script lists all available models from OpenRouter API with real-time testing
to show pricing, actual availability, and latency metrics.
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

"""
USAGE EXAMPLES:

# List all models with basic info only (fast)
python3 list_models_with_metrics.py

# Test all models for availability and latency (slow but comprehensive)
python3 list_models_with_metrics.py --test-availability

# Show only free models
python3 list_models_with_metrics.py --free-only

# Test only free models
python3 list_models_with_metrics.py --test-availability --free-only

# Show only working models (requires testing)
python3 list_models_with_metrics.py --test-availability --working-only

# Test with custom prompt
python3 list_models_with_metrics.py --test-availability --test-prompt "What should I wear today?"

# Fast mode - limit testing to first N models
python3 list_models_with_metrics.py --test-availability --limit 10

# Export results to JSON
python3 list_models_with_metrics.py --test-availability --output results.json

# Show detailed error messages
python3 list_models_with_metrics.py --test-availability --verbose
"""

import asyncio
import json
import time
import os
import sys
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import httpx
from dataclasses import dataclass, asdict

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@dataclass
class ModelInfo:
    """Information about a model from OpenRouter API."""

    id: str
    name: str
    provider: str
    prompt_price: str
    completion_price: str
    context_length: str
    is_free: bool
    availability_status: str = "unknown"  # unknown, available, unavailable, error
    avg_latency_ms: Optional[float] = None
    error_message: Optional[str] = None
    test_timestamp: Optional[str] = None


class ModelLister:
    """Lists and tests OpenRouter models."""

    def __init__(self, api_key: str, timeout: float = 30.0, verbose: bool = False):
        self.api_key = api_key
        self.timeout = timeout
        self.verbose = verbose
        self.test_prompt = "Hi"  # Simple test prompt

    async def fetch_all_models(self) -> List[ModelInfo]:
        """Fetch all available models from OpenRouter API."""
        if not self.api_key:
            raise ValueError("OpenRouter API key is required")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    "https://openrouter.ai/api/v1/models",
                    headers=headers,
                )

                if response.status_code != 200:
                    raise Exception(
                        f"API error: HTTP {response.status_code} - {response.text}"
                    )

                result = response.json()
                models_data = result.get("data", [])

                models = []
                for model in models_data:
                    model_id = model.get("id", "")
                    provider = model_id.split("/")[0] if "/" in model_id else "other"
                    pricing = model.get("pricing", {})

                    # Determine if model is free
                    prompt_price = pricing.get("prompt", "0")
                    completion_price = pricing.get("completion", "0")
                    is_free = (
                        prompt_price == "0" and completion_price == "0"
                    ) or ":free" in model_id.lower()

                    model_info = ModelInfo(
                        id=model_id,
                        name=model.get("name", model_id),
                        provider=provider,
                        prompt_price=prompt_price,
                        completion_price=completion_price,
                        context_length=str(model.get("context_length", "Unknown")),
                        is_free=is_free,
                    )
                    models.append(model_info)

                return models

        except Exception as e:
            raise Exception(f"Failed to fetch models: {str(e)}")

    async def test_model_availability(self, model: ModelInfo) -> ModelInfo:
        """Test if a model is actually available and measure latency."""
        if self.verbose:
            print(f"Testing {model.id}...", end=" ")

        start_time = time.time()

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/model-lister",
            "X-Title": "Model Availability Checker",
        }

        payload = {
            "model": model.id,
            "messages": [{"role": "user", "content": self.test_prompt}],
            "temperature": 0.1,
            "max_tokens": 10,  # Minimal response to test quickly
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    json=payload,
                    headers=headers,
                )

                elapsed_ms = (time.time() - start_time) * 1000

                if response.status_code == 200:
                    result = response.json()
                    if "choices" in result and len(result["choices"]) > 0:
                        model.availability_status = "available"
                        model.avg_latency_ms = elapsed_ms
                        if self.verbose:
                            print(f"✓ ({elapsed_ms:.0f}ms)")
                    else:
                        model.availability_status = "error"
                        model.error_message = "No response content"
                        if self.verbose:
                            print(f"✗ (no content)")
                elif response.status_code == 404:
                    model.availability_status = "unavailable"
                    model.error_message = "Model not found"
                    if self.verbose:
                        print(f"✗ (404 not found)")
                elif response.status_code == 429:
                    model.availability_status = "rate_limited"
                    model.error_message = "Rate limited"
                    if self.verbose:
                        print(f"⚠ (rate limited)")
                elif response.status_code == 403:
                    model.availability_status = "forbidden"
                    model.error_message = (
                        "Access forbidden - may require privacy settings"
                    )
                    if self.verbose:
                        print(f"✗ (403 forbidden)")
                else:
                    model.availability_status = "error"
                    try:
                        error_data = response.json()
                        error_msg = error_data.get("error", {}).get(
                            "message", response.text[:100]
                        )
                    except:
                        error_msg = f"HTTP {response.status_code}"
                    model.error_message = error_msg
                    if self.verbose:
                        print(f"✗ ({response.status_code})")

        except asyncio.TimeoutError:
            model.availability_status = "timeout"
            model.error_message = f"Timeout after {self.timeout}s"
            if self.verbose:
                print(f"✗ (timeout)")
        except Exception as e:
            model.availability_status = "error"
            model.error_message = str(e)[:100]
            if self.verbose:
                print(f"✗ (error)")

        model.test_timestamp = datetime.now().isoformat()
        return model

    async def test_all_models(
        self, models: List[ModelInfo], limit: Optional[int] = None
    ) -> List[ModelInfo]:
        """Test availability for all models with optional limit."""
        test_models = models[:limit] if limit else models

        print(f"Testing {len(test_models)} models for availability and latency...")
        if limit and limit < len(models):
            print(f"(Limited to first {limit} models)")
        print()

        # Test models sequentially to avoid rate limiting
        tested_models = []
        for i, model in enumerate(test_models, 1):
            if not self.verbose:
                print(f"Progress: {i}/{len(test_models)} - {model.id[:50]}", end="\r")

            tested_model = await self.test_model_availability(model)
            tested_models.append(tested_model)

            # Small delay to avoid overwhelming the API
            if i < len(test_models):
                await asyncio.sleep(0.5)

        if not self.verbose:
            print()  # Clear progress line

        return tested_models

    def format_price(self, price_str: str) -> str:
        """Format price string for display."""
        try:
            price = float(price_str)
            if price == 0:
                return "FREE"
            elif price < 0.001:
                return f"${price:.6f}"
            else:
                return f"${price:.4f}"
        except:
            return price_str

    def print_models_table(
        self, models: List[ModelInfo], show_availability: bool = False
    ):
        """Print models in a formatted table."""
        if not models:
            print("No models found.")
            return

        # Group by provider
        providers = {}
        for model in models:
            if model.provider not in providers:
                providers[model.provider] = []
            providers[model.provider].append(model)

        # Print summary
        total_models = len(models)
        free_models = len([m for m in models if m.is_free])

        if show_availability:
            available_models = len(
                [m for m in models if m.availability_status == "available"]
            )
            print(
                f"\nTOTAL MODELS: {total_models} | FREE: {free_models} | TESTED AVAILABLE: {available_models}"
            )
        else:
            print(f"\nTOTAL MODELS: {total_models} | FREE: {free_models}")

        print("=" * 120)

        # Print header
        if show_availability:
            print(
                f"{'MODEL ID':<45} {'STATUS':<12} {'LATENCY':<10} {'PROMPT':<10} {'COMPLETION':<12} {'CONTEXT':<10}"
            )
            print("-" * 120)
        else:
            print(
                f"{'MODEL ID':<45} {'NAME':<25} {'PROMPT':<10} {'COMPLETION':<12} {'CONTEXT':<10}"
            )
            print("-" * 120)

        # Print models by provider
        for provider in sorted(providers.keys()):
            provider_models = providers[provider]
            print(f"\n{provider.upper()} ({len(provider_models)} models):")

            # Sort models within provider
            if show_availability:
                # Sort by availability status, then by latency
                def sort_key(m):
                    status_priority = {
                        "available": 0,
                        "rate_limited": 1,
                        "timeout": 2,
                        "forbidden": 3,
                        "unavailable": 4,
                        "error": 5,
                        "unknown": 6,
                    }
                    return (
                        status_priority.get(m.availability_status, 6),
                        m.avg_latency_ms or 9999,
                    )

                provider_models.sort(key=sort_key)
            else:
                provider_models.sort(key=lambda x: x.id)

            for model in provider_models:
                if show_availability:
                    # Format status with color-like indicators
                    status_symbols = {
                        "available": "✓ AVAILABLE",
                        "unavailable": "✗ NOT FOUND",
                        "forbidden": "⚠ FORBIDDEN",
                        "rate_limited": "⚠ RATE LIM",
                        "timeout": "⚠ TIMEOUT",
                        "error": "✗ ERROR",
                        "unknown": "? UNKNOWN",
                    }
                    status = status_symbols.get(
                        model.availability_status, model.availability_status.upper()
                    )

                    latency = (
                        f"{model.avg_latency_ms:.0f}ms" if model.avg_latency_ms else "-"
                    )

                    print(
                        f"{model.id:<45} {status:<12} {latency:<10} {self.format_price(model.prompt_price):<10} {self.format_price(model.completion_price):<12} {model.context_length:<10}"
                    )

                    # Show error details if verbose
                    if (
                        self.verbose
                        and model.error_message
                        and model.availability_status in ["error", "forbidden"]
                    ):
                        print(f"{'  └─ Error:':<47} {model.error_message[:60]}")

                else:
                    name_short = (
                        model.name[:24] + "..." if len(model.name) > 24 else model.name
                    )
                    print(
                        f"{model.id:<45} {name_short:<25} {self.format_price(model.prompt_price):<10} {self.format_price(model.completion_price):<12} {model.context_length:<10}"
                    )

        # Print legend if showing availability
        if show_availability:
            print(f"\nLEGEND:")
            print(f"✓ AVAILABLE  = Model working normally")
            print(f"✗ NOT FOUND  = Model ID invalid or discontinued")
            print(
                f"⚠ FORBIDDEN  = Access denied (may need privacy settings: https://openrouter.ai/settings/privacy)"
            )
            print(f"⚠ RATE LIM   = Rate limited (try again later)")
            print(f"⚠ TIMEOUT    = Response too slow")
            print(f"✗ ERROR      = Other error occurred")

    def save_results(self, models: List[ModelInfo], filename: str):
        """Save results to JSON file."""
        data = {
            "timestamp": datetime.now().isoformat(),
            "total_models": len(models),
            "models": [asdict(model) for model in models],
        }

        with open(filename, "w") as f:
            json.dump(data, f, indent=2)

        print(f"\nResults saved to: {filename}")


async def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="List OpenRouter models with pricing, availability, and latency metrics"
    )

    parser.add_argument(
        "--api-key",
        type=str,
        help="OpenRouter API key (or set OPENROUTER_API_KEY env var)",
    )
    parser.add_argument(
        "--test-availability",
        action="store_true",
        help="Test each model for actual availability and measure latency (slower)",
    )
    parser.add_argument(
        "--free-only", action="store_true", help="Show only free models"
    )
    parser.add_argument(
        "--working-only",
        action="store_true",
        help="Show only working models (requires --test-availability)",
    )
    parser.add_argument(
        "--test-prompt",
        type=str,
        default="Hi",
        help="Custom prompt for availability testing (default: 'Hi')",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Limit testing to first N models (useful for quick checks)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=30.0,
        help="Timeout for API requests in seconds (default: 30)",
    )
    parser.add_argument("--output", type=str, help="Save results to JSON file")
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed progress and error messages",
    )

    args = parser.parse_args()

    # Get API key
    api_key = (
        args.api_key or os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENROUTER_KEY")
    )

    if not api_key:
        print("Error: OpenRouter API key required!")
        print("Options:")
        print("  1. Set OPENROUTER_API_KEY environment variable")
        print("  2. Use --api-key parameter")
        print("  3. Get your key from: https://openrouter.ai/keys")
        return

    # Create lister
    lister = ModelLister(api_key=api_key, timeout=args.timeout, verbose=args.verbose)
    if args.test_prompt != "Hi":
        lister.test_prompt = args.test_prompt

    try:
        # Fetch all models
        print("Fetching models from OpenRouter API...")
        models = await lister.fetch_all_models()
        print(f"Found {len(models)} models")

        # Filter free models if requested
        if args.free_only:
            models = [m for m in models if m.is_free]
            print(f"Filtered to {len(models)} free models")

        if not models:
            print("No models found matching criteria.")
            return

        # Test availability if requested
        if args.test_availability:
            models = await lister.test_all_models(models, limit=args.limit)

            # Filter working models if requested
            if args.working_only:
                working_models = [
                    m for m in models if m.availability_status == "available"
                ]
                print(f"\nFiltered to {len(working_models)} working models")
                models = working_models
        elif args.working_only:
            print("Error: --working-only requires --test-availability")
            return

        # Print results
        lister.print_models_table(models, show_availability=args.test_availability)

        # Save results if requested
        if args.output:
            lister.save_results(models, args.output)

        # Print summary recommendations
        if args.test_availability:
            available_models = [
                m for m in models if m.availability_status == "available"
            ]
            if available_models:
                print(f"\nRECOMMENDATIONS:")

                # Fastest models
                fastest_models = sorted(
                    available_models, key=lambda x: x.avg_latency_ms or 9999
                )[:3]
                print(f"\nFastest Models:")
                for i, model in enumerate(fastest_models, 1):
                    print(f"  {i}. {model.id} ({model.avg_latency_ms:.0f}ms)")

                # Best free models
                free_available = [m for m in available_models if m.is_free]
                if free_available:
                    best_free = sorted(
                        free_available, key=lambda x: x.avg_latency_ms or 9999
                    )[:3]
                    print(f"\nBest Free Models:")
                    for i, model in enumerate(best_free, 1):
                        print(f"  {i}. {model.id} ({model.avg_latency_ms:.0f}ms)")

            else:
                print(f"\n⚠️  No working models found!")
                print("Common solutions:")
                print(
                    "• Configure privacy settings: https://openrouter.ai/settings/privacy"
                )
                print("• Check API key validity: https://openrouter.ai/keys")
                print("• Try again later if rate limited")

    except Exception as e:
        print(f"Error: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
