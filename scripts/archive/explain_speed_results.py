#!/usr/bin/env python3
"""
Explain Speed Results - Analysis of the Benchmark Speed Contradiction

This script explains why a model can have higher inference speed
but slower overall response time.
"""


def analyze_speed_contradiction():
    """Analyze the speed contradiction in benchmark results."""

    print("🔍 BENCHMARK SPEED CONTRADICTION ANALYSIS")
    print("=" * 55)

    # Your actual results
    qwen_data = {
        "model": "qwen/qwen-2.5-72b-instruct:free",
        "response_time": 2.43,
        "inference_speed": 27.5,
        "estimated_tokens": 67,  # Typical for controlled responses
    }

    openai_data = {
        "model": "openai/gpt-oss-20b:free",
        "response_time": 3.47,
        "inference_speed": 91.1,
        "estimated_tokens": 314,  # Calculated from the speeds
    }

    print("\n📊 YOUR RESULTS:")
    print("-" * 40)
    print(
        f"{'Model':<25} {'Response Time':<13} {'Inference Speed':<16} {'Est. Tokens'}"
    )
    print("-" * 65)
    print(
        f"{qwen_data['model'][:24]:<25} {qwen_data['response_time']:<13.2f} {qwen_data['inference_speed']:<16.1f} {qwen_data['estimated_tokens']}"
    )
    print(
        f"{openai_data['model'][:24]:<25} {openai_data['response_time']:<13.2f} {openai_data['inference_speed']:<16.1f} {openai_data['estimated_tokens']}"
    )

    print("\n🤔 THE CONTRADICTION:")
    print("-" * 20)
    print("❓ How can OpenAI generate tokens 3.3x faster but take longer overall?")
    print(
        f"   OpenAI: {openai_data['inference_speed']:.1f} tokens/s vs Qwen: {qwen_data['inference_speed']:.1f} tokens/s"
    )
    print(
        f"   But OpenAI takes {openai_data['response_time']:.2f}s vs Qwen: {qwen_data['response_time']:.2f}s"
    )

    # Calculate what's happening
    print("\n🔬 MATHEMATICAL BREAKDOWN:")
    print("-" * 30)

    # Estimate tokens generated based on inference speed and response time
    qwen_est_tokens = qwen_data["inference_speed"] * qwen_data["response_time"]
    openai_est_tokens = openai_data["inference_speed"] * openai_data["response_time"]

    print(f"Estimated tokens generated:")
    print(
        f"  Qwen: {qwen_data['inference_speed']:.1f} tokens/s × {qwen_data['response_time']:.2f}s = {qwen_est_tokens:.0f} tokens"
    )
    print(
        f"  OpenAI: {openai_data['inference_speed']:.1f} tokens/s × {openai_data['response_time']:.2f}s = {openai_est_tokens:.0f} tokens"
    )

    token_ratio = openai_est_tokens / qwen_est_tokens
    print(f"\n📈 OpenAI generated {token_ratio:.1f}x more tokens!")

    print("\n💡 EXPLANATION:")
    print("-" * 15)
    print("The system suffix should control response length, but:")
    print("1. OpenAI model might ignore or interpret the suffix differently")
    print("2. Different models have different 'styles' even with same prompt")
    print("3. OpenAI might add more verbose explanations despite instructions")

    # What this means for fair comparison
    print("\n⚖️ FAIR COMPARISON IMPLICATIONS:")
    print("-" * 35)

    # Calculate what OpenAI time would be if it generated same tokens as Qwen
    fair_openai_time = qwen_est_tokens / openai_data["inference_speed"]
    time_advantage = qwen_data["response_time"] - fair_openai_time

    print(f"If OpenAI generated same {qwen_est_tokens:.0f} tokens as Qwen:")
    print(
        f"  OpenAI time would be: {qwen_est_tokens:.0f} ÷ {openai_data['inference_speed']:.1f} = {fair_openai_time:.2f}s"
    )
    print(f"  Qwen actual time: {qwen_data['response_time']:.2f}s")
    print(
        f"  OpenAI would be {abs(time_advantage):.2f}s {'faster' if time_advantage > 0 else 'slower'}"
    )

    print("\n🎯 RECOMMENDATIONS:")
    print("-" * 20)
    print("✓ OpenAI model has superior inference speed (3.3x faster)")
    print("✓ BUT generates much longer responses despite system suffix")
    print("✓ For speed-critical apps: OpenAI (if you can control output length)")
    print("✓ For consistent short responses: Qwen follows instructions better")

    # Propose better system suffix
    print("\n🛠️ SUGGESTED IMPROVEMENTS:")
    print("-" * 30)
    print("Try stricter system suffix:")
    print('--system-suffix "EXACTLY 3 bullets. MAX 60 words total. No explanations."')
    print()
    print("Or test with max-tokens limit:")
    print("--max-tokens 100")

    print("\n📋 SUMMARY:")
    print("-" * 12)
    print("• Response Time = Total time (what users experience)")
    print("• Inference Speed = Generation rate (technical capability)")
    print("• OpenAI generates faster but talks more")
    print("• Qwen is slower at generation but follows length limits better")
    print("• Choose based on your use case: speed vs consistency")


if __name__ == "__main__":
    analyze_speed_contradiction()
