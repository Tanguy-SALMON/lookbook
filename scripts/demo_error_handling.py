#!/usr/bin/env python3
"""
Demo: Error Handling Improvements

This script demonstrates the improved error handling in the benchmark system,
especially for rate limiting and failed benchmarks.
"""

import asyncio
import json
from datetime import datetime


def demo_error_scenarios():
    """Demonstrate various error scenarios and their handling."""

    print("🚨 ERROR HANDLING IMPROVEMENTS DEMO")
    print("=" * 50)

    print("\n📋 IMPROVEMENTS MADE:")
    print("-" * 25)
    print("✅ Rate limiting detection and retry")
    print("✅ Graceful handling of failed benchmarks")
    print("✅ Detailed error reporting")
    print("✅ Prevention of crashes on zero successful runs")
    print("✅ Improved error messages with solutions")

    print("\n🔍 ERROR SCENARIOS HANDLED:")
    print("-" * 35)

    # Scenario 1: Rate Limiting (HTTP 429)
    print("\n1. RATE LIMITING (HTTP 429)")
    print("   Problem: Too many requests to OpenRouter")
    print("   Old behavior: Immediate failure")
    print("   New behavior:")
    print("     • Automatic retry with exponential backoff")
    print("     • Configurable retry count and delay")
    print("     • Clear progress messages")
    print("     • Helpful error messages with solutions")

    # Show example command
    print("\n   Usage examples:")
    print("   # Enable retries with custom delay")
    print("   python3 benchmark_models_openrouter.py \\")
    print('     --rate-limit-delay 30 --models "model-name"')
    print("")
    print("   # Disable retries for faster failure")
    print("   python3 benchmark_models_openrouter.py \\")
    print('     --no-rate-limit-retry --models "model-name"')

    # Scenario 2: Zero Successful Runs
    print("\n2. ZERO SUCCESSFUL RUNS")
    print("   Problem: All benchmark attempts failed")
    print("   Old behavior: KeyError crash when generating report")
    print("   New behavior:")
    print("     • Graceful error report generation")
    print("     • Detailed failure analysis")
    print("     • Actionable troubleshooting tips")
    print("     • Files still saved for debugging")

    # Scenario 3: API Authentication Issues
    print("\n3. AUTHENTICATION ERRORS")
    print("   Problem: Invalid or missing API key")
    print("   Handling:")
    print("     • Clear error messages")
    print("     • Setup instructions")
    print("     • Multiple environment variable options")

    # Scenario 4: Model Access Issues
    print("\n4. MODEL ACCESS ISSUES")
    print("   Problem: Model not available or requires payment")
    print("   Handling:")
    print("     • Specific error codes in messages")
    print("     • Alternative model suggestions")
    print("     • Model availability checking")

    print("\n📊 EXAMPLE ERROR REPORT:")
    print("-" * 30)

    # Show example of what an error report looks like
    example_report = """
⚠️  BENCHMARK FAILED - NO SUCCESSFUL RUNS
==========================================
Total Attempts: 10
Success Rate: 0.0% (0/10 runs)

ERROR ANALYSIS
--------------
• Rate limit exceeded after retries: 8 occurrences
• HTTP 401: Unauthorized: 2 occurrences

COMMON SOLUTIONS
----------------
• HTTP 429 (Rate Limiting): Wait and retry, or use different model
• HTTP 401 (Unauthorized): Check your API key
• HTTP 403 (Forbidden): Check model access permissions
• Timeout errors: Increase timeout or try smaller prompts
• Network errors: Check internet connection

TROUBLESHOOTING TIPS
--------------------
• Try a different model: --models "qwen/qwen-2.5-7b-instruct:free"
• Reduce request rate: --repeat 1
• Use shorter prompts: --prompts "Quick outfit advice"
• Check API status: https://status.openrouter.ai/
"""

    print(example_report)

    print("\n🛠️ NEW COMMAND LINE OPTIONS:")
    print("-" * 35)
    print("--no-rate-limit-retry     : Disable automatic retry on rate limits")
    print("--rate-limit-delay 30     : Wait 30 seconds when rate limited")
    print("--repeat 1                : Reduce load with single attempt per prompt")
    print("--timeout 120             : Increase timeout for slow models")

    print("\n🎯 BEST PRACTICES:")
    print("-" * 20)
    print("1. Start with small tests (--repeat 1)")
    print("2. Use free models for development")
    print("3. Check model availability first (--list-models)")
    print("4. Monitor rate limits and adjust delay")
    print("5. Keep API keys secure and updated")

    print("\n🔧 DEBUGGING WORKFLOW:")
    print("-" * 25)
    print("1. Check API key: echo $OPENROUTER_API_KEY")
    print("2. Test connectivity: curl https://openrouter.ai/api/v1/models")
    print("3. List available models: --list-models")
    print('4. Try simple test: --models "free-model" --repeat 1')
    print("5. Review error logs in benchmark_results/")

    print("\n📈 RESILIENCE FEATURES:")
    print("-" * 28)
    print("✅ Automatic retry with backoff")
    print("✅ Graceful degradation on failures")
    print("✅ Comprehensive error logging")
    print("✅ Recovery suggestions")
    print("✅ Partial result preservation")
    print("✅ Progress indication during retries")

    print("\n💡 RATE LIMITING STRATEGIES:")
    print("-" * 35)
    print("• Default: 2 retries with 60s delay")
    print("• Conservative: --rate-limit-delay 120")
    print("• Aggressive: --no-rate-limit-retry")
    print("• Batch processing: Spread requests over time")
    print("• Model selection: Use different providers")

    return True


def show_before_after_comparison():
    """Show before/after comparison of error handling."""

    print("\n📊 BEFORE vs AFTER COMPARISON")
    print("=" * 45)

    scenarios = [
        {
            "scenario": "Rate Limiting (HTTP 429)",
            "before": "Immediate failure, no retry",
            "after": "Auto-retry with backoff, helpful messages",
        },
        {
            "scenario": "Zero Successful Runs",
            "before": "KeyError crash in report generation",
            "after": "Graceful error report with solutions",
        },
        {
            "scenario": "API Authentication",
            "before": "Generic HTTP 401 error",
            "after": "Clear setup instructions and alternatives",
        },
        {
            "scenario": "Network Issues",
            "before": "Cryptic connection errors",
            "after": "Network troubleshooting guidance",
        },
        {
            "scenario": "File Operations",
            "before": "Crash on summary generation failure",
            "after": "Fallback basic summary, files still saved",
        },
    ]

    print(f"\n{'Scenario':<25} {'Before':<35} {'After'}")
    print("-" * 90)

    for scenario in scenarios:
        print(
            f"{scenario['scenario']:<25} {scenario['before']:<35} {scenario['after']}"
        )

    print(f"\n🎉 RESULT: More reliable benchmarking with better user experience!")


async def demo_retry_logic():
    """Demonstrate the retry logic concept."""

    print("\n🔄 RETRY LOGIC DEMONSTRATION")
    print("=" * 40)

    print("Simulating API calls with rate limiting...")

    max_retries = 2
    rate_limit_delay = 5  # Shorter for demo

    for attempt in range(max_retries + 1):
        print(f"\n📡 Attempt {attempt + 1}/{max_retries + 1}")

        # Simulate rate limiting on first two attempts
        if attempt < 2:
            print("❌ HTTP 429: Rate limit exceeded")
            if attempt < max_retries:
                print(f"⏳ Waiting {rate_limit_delay}s before retry...")
                await asyncio.sleep(1)  # Shortened for demo
                print("🔄 Retrying...")
            else:
                print("🚫 Max retries exceeded")
                return False
        else:
            print("✅ HTTP 200: Success!")
            return True

    return False


def main():
    """Main demo function."""

    # Show error handling improvements
    demo_error_scenarios()

    # Show before/after comparison
    show_before_after_comparison()

    # Demo the retry logic
    print("\n" + "=" * 50)
    asyncio.run(demo_retry_logic())

    print(f"\n🎊 ERROR HANDLING DEMO COMPLETE!")
    print("The benchmark system is now much more robust and user-friendly.")
    print("\nTry testing it with a rate-limited model:")
    print("python3 scripts/benchmark_models_openrouter.py \\")
    print('  --models "popular-model" --repeat 1 --verbose')


if __name__ == "__main__":
    main()
