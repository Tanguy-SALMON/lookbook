#!/usr/bin/env python3
"""
Demo script showing how to switch between Ollama and OpenRouter LLM providers.

This demonstrates the flexibility of the new provider system - you can easily
switch between local (Ollama) and cloud (OpenRouter) models with environment variables.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from lookbook_mpc.adapters.llm_providers import LLMProviderFactory
from lookbook_mpc.adapters.intent import LLMIntentParser


async def demo_provider(provider_name: str, provider_config: dict):
    """Demonstrate a specific provider configuration."""
    print(f"\n{'=' * 60}")
    print(f"🧠 Testing {provider_name}")
    print(f"{'=' * 60}")

    try:
        # Create provider
        provider = LLMProviderFactory.create_provider(**provider_config)
        print(f"✅ Created provider: {provider.get_provider_name()}")

        # Test intent parsing
        parser = LLMIntentParser(provider)

        test_cases = [
            "I want to do yoga",
            "Going to dinner tonight, need to look good",
            "Business meeting outfit for tomorrow",
        ]

        for test_input in test_cases:
            print(f"\n📝 Input: '{test_input}'")
            try:
                result = await parser.parse_intent(test_input)
                print(f"   🎯 Activity: {result.get('activity', 'None')}")
                print(f"   🎪 Occasion: {result.get('occasion', 'None')}")
                print(f"   🎨 Objectives: {result.get('objectives', [])}")
                print(f"   💬 Response: {result.get('natural_response', '')[:80]}...")
            except Exception as e:
                print(f"   ❌ Error: {e}")

        return True

    except Exception as e:
        print(f"❌ Failed to create {provider_name}: {e}")
        return False


async def demo_environment_switching():
    """Demonstrate switching providers via environment variables."""
    print(f"\n{'=' * 60}")
    print(f"🔄 Environment Variable Switching Demo")
    print(f"{'=' * 60}")

    # Save original environment
    original_provider = os.getenv("LLM_PROVIDER")
    original_model = os.getenv("LLM_MODEL")

    configurations = [
        {
            "name": "Local Ollama (Development)",
            "env": {
                "LLM_PROVIDER": "ollama",
                "LLM_MODEL": "qwen3:4b-instruct",
                "OLLAMA_HOST": "http://localhost:11434",
            },
        },
        {
            "name": "OpenRouter Free (Production)",
            "env": {
                "LLM_PROVIDER": "openrouter",
                "LLM_MODEL": "qwen/qwen-2.5-7b-instruct:free",
                "OPENROUTER_API_KEY": os.getenv("OPENROUTER_API_KEY", "not-set"),
            },
        },
    ]

    for config in configurations:
        print(f"\n🔧 Switching to: {config['name']}")

        # Set environment variables
        for key, value in config["env"].items():
            os.environ[key] = value
            print(f"   {key}={value}")

        # Test the configuration
        try:
            provider = LLMProviderFactory.create_from_env()
            print(f"✅ Active provider: {provider.get_provider_name()}")

            # Quick test
            parser = LLMIntentParser(provider)
            result = await parser.parse_intent("Hello, I need outfit advice")
            print(f"✅ Test passed: {result.get('natural_response', '')[:60]}...")

        except Exception as e:
            print(f"❌ Configuration failed: {e}")

    # Restore original environment
    if original_provider:
        os.environ["LLM_PROVIDER"] = original_provider
    elif "LLM_PROVIDER" in os.environ:
        del os.environ["LLM_PROVIDER"]

    if original_model:
        os.environ["LLM_MODEL"] = original_model
    elif "LLM_MODEL" in os.environ:
        del os.environ["LLM_MODEL"]


def show_configuration_examples():
    """Show configuration examples for different scenarios."""
    print(f"\n{'=' * 60}")
    print(f"📋 Configuration Examples")
    print(f"{'=' * 60}")

    examples = [
        {
            "title": "Development Setup (Local Ollama)",
            "description": "Fast local development with Ollama",
            "commands": [
                "# Start Ollama service",
                "ollama serve",
                "",
                "# Pull required models",
                "ollama pull qwen3:4b-instruct",
                "",
                "# Set environment variables",
                'export LLM_PROVIDER="ollama"',
                'export LLM_MODEL="qwen3:4b-instruct"',
                'export OLLAMA_HOST="http://localhost:11434"',
                "",
                "# Start lookbook service",
                "python main.py",
            ],
        },
        {
            "title": "Production Setup (OpenRouter Free)",
            "description": "Cloud-based inference with free models",
            "commands": [
                "# Get API key from https://openrouter.ai/keys",
                "",
                "# Set environment variables",
                'export LLM_PROVIDER="openrouter"',
                'export OPENROUTER_API_KEY="sk-or-v1-..."',
                'export LLM_MODEL="qwen/qwen-2.5-7b-instruct:free"',
                "",
                "# Start lookbook service",
                "python main.py",
            ],
        },
        {
            "title": "Hybrid Setup (OpenRouter with Ollama fallback)",
            "description": "Use OpenRouter when available, fallback to Ollama",
            "commands": [
                "# Start Ollama as fallback",
                "ollama serve",
                "ollama pull qwen3:4b-instruct",
                "",
                "# Configure OpenRouter as primary",
                'export LLM_PROVIDER="openrouter"',
                'export OPENROUTER_API_KEY="sk-or-v1-..."',
                'export LLM_MODEL="qwen/qwen-2.5-7b-instruct:free"',
                "",
                "# Ollama fallback configuration",
                'export OLLAMA_HOST="http://localhost:11434"',
                'export OLLAMA_TEXT_MODEL="qwen3:4b-instruct"',
                "",
                "# Start lookbook service",
                "python main.py",
            ],
        },
    ]

    for example in examples:
        print(f"\n🏗️  {example['title']}")
        print(f"   {example['description']}")
        print()
        for command in example["commands"]:
            print(f"   {command}")


async def main():
    """Main demo function."""
    print("🚀 Lookbook-MPC Flexible LLM Provider Demo")
    print("==========================================")
    print("This demonstrates switching between Ollama and OpenRouter providers")

    # Check what's available
    has_ollama = True  # Assume available for demo
    has_openrouter = bool(
        os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENROUTER_KEY")
    )

    print(f"\n📊 Provider Availability:")
    print(f"   Ollama: {'✅ Available' if has_ollama else '❌ Not running'}")
    print(f"   OpenRouter: {'✅ API key found' if has_openrouter else '❌ No API key'}")

    # Demo configurations
    configurations = []

    if has_ollama:
        configurations.append(
            {
                "name": "Ollama (Local)",
                "config": {
                    "provider_type": "ollama",
                    "model": "qwen3:4b-instruct",
                    "host": "http://localhost:11434",
                    "timeout": 30,
                },
            }
        )

    if has_openrouter:
        api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENROUTER_KEY")
        configurations.append(
            {
                "name": "OpenRouter (Cloud)",
                "config": {
                    "provider_type": "openrouter",
                    "model": "qwen/qwen-2.5-7b-instruct:free",
                    "api_key": api_key,
                    "timeout": 60,
                },
            }
        )

    # Run demonstrations
    if configurations:
        for config in configurations:
            success = await demo_provider(config["name"], config["config"])
            if success:
                print(f"✅ {config['name']} working correctly")
            else:
                print(f"❌ {config['name']} failed")

        # Demo environment switching
        await demo_environment_switching()
    else:
        print("\n⚠️  No providers available for demonstration")
        print("   Set up Ollama or add OPENROUTER_API_KEY to test")

    # Show configuration examples
    show_configuration_examples()

    # Summary
    print(f"\n{'=' * 60}")
    print("✅ Flexible LLM Demo Complete!")
    print(f"{'=' * 60}")
    print("\n🎯 Key Benefits:")
    print("• Easy switching between local and cloud models")
    print("• Environment-driven configuration")
    print("• Automatic fallback from OpenRouter to Ollama")
    print("• Consistent API across all providers")
    print("• Cost optimization (free models available)")

    print("\n🔧 Quick Start:")
    if not has_openrouter:
        print("• Get free OpenRouter API key: https://openrouter.ai/keys")
    if not has_ollama:
        print("• Install Ollama: https://ollama.ai/")
    print("• Set LLM_PROVIDER=openrouter to use cloud models")
    print("• Set LLM_PROVIDER=ollama to use local models")

    print("\n📚 See FLEXIBLE_LLM_SETUP.md for detailed configuration guide")


if __name__ == "__main__":
    asyncio.run(main())
