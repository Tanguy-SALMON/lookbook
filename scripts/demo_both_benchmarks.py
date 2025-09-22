#!/usr/bin/env python3
"""
Demo Script: OpenRouter vs Ollama Benchmark Comparison

This script demonstrates both benchmark systems and compares their outputs.
It shows how to use both cloud (OpenRouter) and local (Ollama) model benchmarking.
"""

import os
import sys
import asyncio
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def check_requirements():
    """Check if required services and credentials are available."""
    print("🔍 CHECKING REQUIREMENTS")
    print("=" * 40)

    # Check OpenRouter
    openrouter_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENROUTER_KEY")
    if openrouter_key:
        print("✅ OpenRouter API key found")
        openrouter_available = True
    else:
        print("❌ OpenRouter API key not found")
        print("   Set OPENROUTER_API_KEY environment variable")
        openrouter_available = False

    # Check Ollama
    import httpx

    try:
        with httpx.Client(timeout=5) as client:
            response = client.get("http://localhost:11434/api/tags")
            if response.status_code == 200:
                models = response.json().get("models", [])
                print(f"✅ Ollama available with {len(models)} models")
                ollama_available = len(models) > 0

                if models:
                    print("   Available models:")
                    for model in models[:3]:  # Show first 3
                        name = model.get("name", "Unknown")
                        size = model.get("size", 0)
                        size_gb = size / (1024**3) if size > 0 else 0
                        print(f"   - {name} ({size_gb:.1f}GB)")
                    if len(models) > 3:
                        print(f"   - ... and {len(models) - 3} more")
                else:
                    print("   No models installed. Use: ollama pull <model>")
            else:
                print("❌ Ollama not responding")
                ollama_available = False
    except Exception as e:
        print("❌ Ollama not available")
        print(f"   Error: {e}")
        print("   Make sure to run: ollama serve")
        ollama_available = False

    return openrouter_available, ollama_available


async def demo_openrouter():
    """Demonstrate OpenRouter benchmarking."""
    print("\n🌐 OPENROUTER BENCHMARK DEMO")
    print("=" * 45)

    from scripts.benchmark_models_openrouter import BenchmarkConfig, ModelBenchmark

    # Use a fast, free model for demo
    config = BenchmarkConfig(
        model_name="qwen/qwen-2.5-7b-instruct:free",
        repeat_count=1,  # Just 1 run for demo
        test_prompts=["Quick casual outfit for coffee date"],  # Single prompt
        verbose=True,
        use_system_suffix=True,
    )

    print(f"Model: {config.model_name}")
    print(f"Host: {config.openrouter_base_url}")
    print(f"System Suffix: {config.system_suffix}")

    benchmark = ModelBenchmark(config)
    results = await benchmark.run_full_benchmark()

    if results and results[0].success:
        result = results[0]
        print(f"\n📊 OPENROUTER RESULTS:")
        print(f"  Response Time: {result.response_time:.2f}s")
        print(f"  Total Tokens/s: {result.tokens_per_second:.1f}")
        print(f"  Inference Speed: {result.inference_speed:.1f} tokens/s")
        print(f"  Quality Score: {result.response_quality_score:.3f}")
        print(
            f"  Tokens Used: {result.total_tokens} ({result.completion_tokens} completion)"
        )
        print(f"  Response Length: {result.response_length} chars")
        print(f"  Response Preview: {result.response_content[:100]}...")
        return result
    else:
        print("❌ OpenRouter benchmark failed")
        if results:
            print(f"   Error: {results[0].error_message}")
        return None


async def demo_ollama():
    """Demonstrate Ollama benchmarking."""
    print("\n🏠 OLLAMA BENCHMARK DEMO")
    print("=" * 40)

    from scripts.benchmark_models_ollama import BenchmarkConfig, ModelBenchmark

    # Check what models are available
    import httpx

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get("http://localhost:11434/api/tags")
            models = response.json().get("models", [])

            if not models:
                print("❌ No Ollama models available")
                print("   Install models with: ollama pull qwen2.5:7b")
                return None

            # Use the first available model
            model_name = models[0]["name"]
            print(f"Using available model: {model_name}")

    except Exception as e:
        print("❌ Cannot connect to Ollama")
        return None

    config = BenchmarkConfig(
        model_name=model_name,
        repeat_count=1,  # Just 1 run for demo
        test_prompts=[
            "Quick casual outfit for coffee date"
        ],  # Same prompt as OpenRouter
        verbose=True,
        use_system_suffix=True,
    )

    print(f"Model: {config.model_name}")
    print(f"Host: {config.ollama_host}")
    print(f"System Suffix: {config.system_suffix}")

    benchmark = ModelBenchmark(config)
    results = await benchmark.run_full_benchmark()

    if results and results[0].success:
        result = results[0]
        print(f"\n📊 OLLAMA RESULTS:")
        print(f"  Response Time: {result.response_time:.2f}s")
        print(f"  Total Tokens/s: {result.tokens_per_second:.1f}")
        print(f"  Inference Speed: {result.inference_speed:.1f} tokens/s")
        print(f"  Quality Score: {result.response_quality_score:.3f}")
        print(
            f"  Tokens Used: {result.total_tokens} ({result.completion_tokens} completion)"
        )
        print(f"  Response Length: {result.response_length} chars")
        if result.load_time > 0:
            print(f"  Load Time: {result.load_time:.2f}s")
        print(f"  Response Preview: {result.response_content[:100]}...")
        return result
    else:
        print("❌ Ollama benchmark failed")
        if results:
            print(f"   Error: {results[0].error_message}")
        return None


def compare_results(openrouter_result, ollama_result):
    """Compare results from both benchmarks."""
    print("\n🔍 COMPARISON ANALYSIS")
    print("=" * 35)

    if not openrouter_result or not ollama_result:
        print("❌ Cannot compare - missing results")
        return

    print(f"{'Metric':<20} {'OpenRouter':<15} {'Ollama':<15} {'Winner'}")
    print("-" * 65)

    # Response Time
    or_time = openrouter_result.response_time
    ol_time = ollama_result.response_time
    winner = "OpenRouter" if or_time < ol_time else "Ollama"
    print(f"{'Response Time':<20} {or_time:<15.2f} {ol_time:<15.2f} {winner}")

    # Inference Speed
    or_inf = openrouter_result.inference_speed
    ol_inf = ollama_result.inference_speed
    winner = "OpenRouter" if or_inf > ol_inf else "Ollama"
    print(f"{'Inference Speed':<20} {or_inf:<15.1f} {ol_inf:<15.1f} {winner}")

    # Quality
    or_qual = openrouter_result.response_quality_score
    ol_qual = ollama_result.response_quality_score
    winner = "OpenRouter" if or_qual > ol_qual else "Ollama"
    print(f"{'Quality Score':<20} {or_qual:<15.3f} {ol_qual:<15.3f} {winner}")

    # Response Length
    or_len = openrouter_result.response_length
    ol_len = ollama_result.response_length
    print(
        f"{'Response Length':<20} {or_len:<15} {ol_len:<15} {'Similar' if abs(or_len - ol_len) < 50 else 'Different'}"
    )

    print("\n💡 INSIGHTS:")

    # Speed comparison
    if or_time < ol_time:
        improvement = (ol_time - or_time) / ol_time * 100
        print(f"  • OpenRouter is {improvement:.1f}% faster in response time")
    else:
        improvement = (or_time - ol_time) / or_time * 100
        print(f"  • Ollama is {improvement:.1f}% faster in response time")

    # Inference speed comparison
    if or_inf > ol_inf:
        improvement = (or_inf - ol_inf) / ol_inf * 100
        print(f"  • OpenRouter has {improvement:.1f}% higher inference speed")
    else:
        improvement = (ol_inf - or_inf) / or_inf * 100
        print(f"  • Ollama has {improvement:.1f}% higher inference speed")

    # Cost consideration
    print(f"  • OpenRouter: ~$0.001-0.01 per request")
    print(f"  • Ollama: $0 (free after model download)")

    # Privacy
    print(f"  • OpenRouter: Data sent to cloud")
    print(f"  • Ollama: Data stays local (private)")


def show_usage_examples():
    """Show usage examples for both scripts."""
    print("\n📚 USAGE EXAMPLES")
    print("=" * 30)

    print("\n🌐 OpenRouter Examples:")
    print("  # Basic benchmark")
    print("  python3 scripts/benchmark_models_openrouter.py --verbose")
    print()
    print("  # Compare multiple cloud models")
    print("  python3 scripts/benchmark_models_openrouter.py \\")
    print('    --models "qwen/qwen-2.5-7b-instruct:free" "openai/gpt-oss-20b:free" \\')
    print("    --repeat 5")
    print()
    print("  # List available models")
    print("  python3 scripts/benchmark_models_openrouter.py --list-models")

    print("\n🏠 Ollama Examples:")
    print("  # Basic benchmark")
    print("  python3 scripts/benchmark_models_ollama.py --verbose")
    print()
    print("  # Compare multiple local models")
    print("  python3 scripts/benchmark_models_ollama.py \\")
    print('    --models "qwen2.5:7b" "llama3.1:8b" "mistral:7b" \\')
    print("    --repeat 5")
    print()
    print("  # List available models")
    print("  python3 scripts/benchmark_models_ollama.py --list-models")

    print("\n⚙️ Advanced Options (Both):")
    print("  # Custom system suffix")
    print('  --system-suffix "Be brief. Max 50 words."')
    print()
    print("  # Disable response control")
    print("  --no-system-suffix")
    print()
    print("  # Custom prompts")
    print('  --prompts "Outfit for job interview" "Casual weekend look"')


async def main():
    """Main demo function."""
    print("🚀 BENCHMARK SYSTEMS DEMO")
    print("=" * 50)
    print("This demo shows both OpenRouter (cloud) and Ollama (local) benchmarking")
    print()

    # Check requirements
    openrouter_ok, ollama_ok = check_requirements()

    if not openrouter_ok and not ollama_ok:
        print("\n❌ Neither OpenRouter nor Ollama is available")
        print("Please set up at least one service to run the demo")
        return

    print(f"\n🎯 Running demo with available services...")

    # Run benchmarks
    openrouter_result = None
    ollama_result = None

    if openrouter_ok:
        try:
            openrouter_result = await demo_openrouter()
        except Exception as e:
            print(f"❌ OpenRouter demo failed: {e}")

    if ollama_ok:
        try:
            ollama_result = await demo_ollama()
        except Exception as e:
            print(f"❌ Ollama demo failed: {e}")

    # Compare results if both succeeded
    if openrouter_result and ollama_result:
        compare_results(openrouter_result, ollama_result)
    elif openrouter_result:
        print("\n✅ OpenRouter benchmark completed successfully!")
        print("💡 Install Ollama to compare with local models")
    elif ollama_result:
        print("\n✅ Ollama benchmark completed successfully!")
        print("💡 Set OPENROUTER_API_KEY to compare with cloud models")
    else:
        print("\n❌ No benchmarks completed successfully")

    # Show usage examples
    show_usage_examples()

    print(f"\n🎉 Demo completed!")
    print("Try running the full benchmark scripts for comprehensive analysis")


if __name__ == "__main__":
    asyncio.run(main())
