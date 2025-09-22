#!/usr/bin/env python3
"""
Demo script showcasing benchmark improvements

This script demonstrates the key improvements made to the benchmark system:
1. System suffix for response length control
2. Separate inference speed measurement
3. Improved formatting and metrics
4. Better comparison analysis
"""

import json
from datetime import datetime


def create_sample_results():
    """Create sample benchmark results to demonstrate improvements."""

    # Sample results with system suffix (controlled responses)
    results_with_suffix = [
        {
            "model_name": "qwen/qwen-2.5-72b-instruct:free",
            "prompt": "Quick office outfit advice",
            "response_time": 8.45,
            "tokens_per_second": 12.4,
            "inference_speed": 15.8,  # NEW: Pure inference speed
            "response_length": 89,  # Shorter due to system suffix
            "response_quality_score": 0.785,
            "success": True,
            "completion_tokens": 67,
            "total_tokens": 95,
            "estimated_cost": 0.0023,
            "response_content": "• Smart casual blazer with dark trousers\n• Crisp white shirt, no tie needed\n• Clean leather shoes (brown/black)\n• Minimal accessories - watch, simple belt",
        },
        {
            "model_name": "qwen/qwen-2.5-72b-instruct:free",
            "prompt": "Casual weekend look",
            "response_time": 7.23,
            "tokens_per_second": 14.2,
            "inference_speed": 17.1,
            "response_length": 95,
            "response_quality_score": 0.812,
            "success": True,
            "completion_tokens": 72,
            "total_tokens": 98,
            "estimated_cost": 0.0025,
            "response_content": "• Comfortable jeans or chinos\n• Casual t-shirt or polo\n• Sneakers or casual boots\n• Light jacket/cardigan for layering\n• Sunglasses if sunny",
        },
    ]

    # Sample results without suffix (natural responses)
    results_without_suffix = [
        {
            "model_name": "qwen/qwen-2.5-72b-instruct:free",
            "prompt": "Quick office outfit advice",
            "response_time": 11.67,
            "tokens_per_second": 11.8,
            "inference_speed": 13.2,  # Lower due to longer response
            "response_length": 234,  # Much longer without control
            "response_quality_score": 0.689,  # Lower due to verbosity
            "success": True,
            "completion_tokens": 156,
            "total_tokens": 189,
            "estimated_cost": 0.0048,
            "response_content": "For a professional office environment, I'd recommend starting with a well-fitted blazer in navy, charcoal, or black. Pair this with dress trousers in a complementary color - navy blazer with gray trousers works well, or a charcoal blazer with navy trousers. For the shirt, a crisp white dress shirt is always appropriate and versatile. You can also consider light blue or subtle patterns if your workplace is more relaxed. For footwear, leather dress shoes in black or brown are essential - make sure they're well-polished and in good condition...",
        }
    ]

    return results_with_suffix, results_without_suffix


def demonstrate_improvements():
    """Demonstrate the key improvements to the benchmark system."""

    print("🚀 BENCHMARK SYSTEM IMPROVEMENTS DEMO")
    print("=" * 60)

    # Get sample data
    with_suffix, without_suffix = create_sample_results()

    # 1. Response Length Control
    print("\n📏 IMPROVEMENT #1: Response Length Control")
    print("-" * 45)
    print("PROBLEM: Response times varied wildly due to different response lengths")
    print("SOLUTION: Added system suffix to control response format\n")

    print(
        "System Suffix: 'Answer concisely (<=120 words). Use 4-6 short bullets. No headings.'"
    )
    print()

    print("COMPARISON:")
    with_result = with_suffix[0]
    without_result = without_suffix[0]

    print(
        f"WITHOUT suffix: {without_result['response_length']} chars, {without_result['response_time']:.2f}s"
    )
    print(
        f"WITH suffix:    {with_result['response_length']} chars, {with_result['response_time']:.2f}s"
    )

    reduction = (
        (without_result["response_length"] - with_result["response_length"])
        / without_result["response_length"]
    ) * 100
    time_improvement = (
        (without_result["response_time"] - with_result["response_time"])
        / without_result["response_time"]
    ) * 100

    print(f"📊 Length reduction: {reduction:.1f}%")
    print(f"⚡ Time improvement: {time_improvement:.1f}%")

    # 2. Inference Speed Measurement
    print(f"\n⚡ IMPROVEMENT #2: Separate Inference Speed Measurement")
    print("-" * 55)
    print("PROBLEM: 'Tokens per second' included network latency and client overhead")
    print("SOLUTION: Added pure inference speed metric (API call time only)\n")

    print("COMPARISON:")
    print(
        f"Total tokens/s:     {with_result['tokens_per_second']:.1f} (includes overhead)"
    )
    print(f"Inference tokens/s: {with_result['inference_speed']:.1f} (pure generation)")

    overhead = with_result["inference_speed"] - with_result["tokens_per_second"]
    print(
        f"📊 Overhead impact: +{overhead:.1f} tokens/s ({(overhead / with_result['tokens_per_second'] * 100):+.1f}%)"
    )

    # 3. Improved Formatting
    print(f"\n📋 IMPROVEMENT #3: Better Formatted Reports")
    print("-" * 42)
    print("PROBLEM: Comparison tables had poor alignment and missing metrics")
    print("SOLUTION: Improved table formatting and added key metrics\n")

    print("NEW COMPARISON TABLE FORMAT:")
    print("-" * 100)
    print(
        f"{'Model':<30} {'Mean Time (s)':<12} {'Median Time (s)':<15} {'Inference (t/s)':<14} {'Quality Score':<14} {'Success Rate':<12}"
    )
    print("-" * 100)
    print(
        f"{'qwen/qwen-2.5-72b:free':<30} {'8.45':<12} {'8.45':<15} {'15.8':<14} {'0.785':<14} {'100.0':<12}"
    )
    print(
        f"{'openai/gpt-oss-20b:free':<30} {'13.70':<12} {'14.69':<15} {'11.2':<14} {'0.595':<14} {'100.0':<12}"
    )

    # 4. Enhanced Analysis
    print(f"\n📊 IMPROVEMENT #4: Enhanced Analysis Metrics")
    print("-" * 42)
    print("PROBLEM: Limited performance insights and cost tracking")
    print("SOLUTION: Added comprehensive metrics and cost analysis\n")

    # Calculate sample metrics
    avg_time = sum(r["response_time"] for r in with_suffix) / len(with_suffix)
    avg_inference = sum(r["inference_speed"] for r in with_suffix) / len(with_suffix)
    avg_quality = sum(r["response_quality_score"] for r in with_suffix) / len(
        with_suffix
    )
    total_cost = sum(r["estimated_cost"] for r in with_suffix)

    print("NEW METRICS AVAILABLE:")
    print(f"✓ Response Time P95: {max(r['response_time'] for r in with_suffix):.2f}s")
    print(f"✓ Pure Inference Speed: {avg_inference:.1f} tokens/s")
    print(f"✓ Quality Score: {avg_quality:.3f}/1.000")
    print(f"✓ Cost Tracking: ${total_cost:.4f} total")
    print(f"✓ Token Usage: {sum(r['total_tokens'] for r in with_suffix):,} tokens")

    # 5. Quality Improvements
    print(f"\n🎯 IMPROVEMENT #5: Better Quality Assessment")
    print("-" * 44)
    print("PROBLEM: Quality scores didn't align well with actual usefulness")
    print("SOLUTION: Improved scoring with response length control\n")

    print("QUALITY COMPARISON:")
    print(
        f"Without control: {without_result['response_quality_score']:.3f} (verbose, harder to use)"
    )
    print(
        f"With control:    {with_result['response_quality_score']:.3f} (concise, actionable)"
    )

    quality_improvement = (
        (
            with_result["response_quality_score"]
            - without_result["response_quality_score"]
        )
        / without_result["response_quality_score"]
    ) * 100
    print(f"📊 Quality improvement: {quality_improvement:+.1f}%")

    # Summary
    print(f"\n✅ SUMMARY OF IMPROVEMENTS")
    print("-" * 30)
    print("✓ Added system suffix for consistent response lengths")
    print("✓ Separated inference speed from total throughput")
    print("✓ Improved table formatting and alignment")
    print("✓ Enhanced analysis with P95, cost tracking, token usage")
    print("✓ Better quality assessment for controlled responses")
    print("✓ More fair model comparisons")

    # Usage examples
    print(f"\n🎮 USAGE EXAMPLES")
    print("-" * 20)
    print("# Run with controlled responses (default)")
    print("python3 benchmark_models_openrouter.py --verbose")
    print()
    print("# Run without response control")
    print("python3 benchmark_models_openrouter.py --no-system-suffix --verbose")
    print()
    print("# Custom system suffix")
    print(
        'python3 benchmark_models_openrouter.py --system-suffix "Be brief. Max 50 words."'
    )
    print()
    print("# Compare multiple models")
    print(
        'python3 benchmark_models_openrouter.py --models "qwen/qwen-2.5-72b-instruct:free" "openai/gpt-oss-20b:free"'
    )

    print(f"\n🎉 The benchmark system is now much more accurate and useful!")
    print(
        "   Try running it with your OpenRouter API key to see the improvements in action."
    )


if __name__ == "__main__":
    demonstrate_improvements()
