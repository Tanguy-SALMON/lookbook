#!/usr/bin/env python3
"""
LLM Status Checker

Diagnostic script to verify LLM availability and model status for the chat system.
"""

import asyncio
import aiohttp
import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from lookbook_mpc.config.settings import settings


async def check_ollama_health():
    """Check if Ollama service is running."""
    print("🔍 Checking Ollama Service Health...")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{settings.ollama_host}/api/tags") as response:
                if response.status == 200:
                    print("✅ Ollama service is running")
                    return True
                else:
                    print(f"❌ Ollama service returned status {response.status}")
                    return False
    except Exception as e:
        print(f"❌ Cannot connect to Ollama: {str(e)}")
        return False


async def list_available_models():
    """List all available Ollama models."""
    print("\n📋 Available Ollama Models:")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{settings.ollama_host}/api/tags") as response:
                if response.status == 200:
                    data = await response.json()
                    models = data.get("models", [])

                    if not models:
                        print("   No models found")
                        return []

                    for model in models:
                        name = model.get("name", "Unknown")
                        size = model.get("size", 0)
                        size_mb = round(size / (1024 * 1024), 1)
                        print(f"   • {name} ({size_mb} MB)")

                    return [model.get("name") for model in models]
                else:
                    print(f"   Failed to fetch models: {response.status}")
                    return []
    except Exception as e:
        print(f"   Error fetching models: {str(e)}")
        return []


async def test_model_response(model_name: str):
    """Test if a specific model can respond to queries."""
    print(f"\n🧪 Testing Model: {model_name}")

    test_prompt = "Hello, are you working?"

    try:
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=15)
        ) as session:
            payload = {
                "model": model_name,
                "prompt": test_prompt,
                "stream": False,
                "temperature": 0.3,
                "max_tokens": 50,
            }

            async with session.post(
                f"{settings.ollama_host}/api/generate", json=payload
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    response_text = result.get("response", "")

                    if response_text.strip():
                        print(f"   ✅ Model responds: '{response_text[:100]}...'")
                        return True
                    else:
                        print("   ❌ Model returned empty response")
                        return False
                else:
                    error_text = await response.text()
                    print(f"   ❌ Model error: {response.status} - {error_text}")
                    return False
    except asyncio.TimeoutError:
        print("   ⏰ Model response timed out (>15s)")
        return False
    except Exception as e:
        print(f"   ❌ Model test error: {str(e)}")
        return False


async def test_chat_intent_parsing():
    """Test the chat intent parsing with configured model."""
    print(f"\n🎯 Testing Chat Intent Parsing with {settings.ollama_text_model}")

    from lookbook_mpc.adapters.intent import LLMIntentParser

    parser = LLMIntentParser(
        host=settings.ollama_host, model=settings.ollama_text_model, timeout=15
    )

    test_messages = [
        "I go to dance",
        "Hello",
        "I need something for work",
    ]

    success_count = 0

    for msg in test_messages:
        try:
            print(f"   Testing: '{msg}'")
            intent = await parser.parse_intent(msg)

            natural_response = intent.get("natural_response", "No response")
            activity = intent.get("activity", "None")
            occasion = intent.get("occasion", "None")

            print(f"      ✅ Activity: {activity}, Occasion: {occasion}")
            print(f"      💬 Response: {natural_response[:80]}...")
            success_count += 1

        except Exception as e:
            print(f"      ❌ Error: {str(e)}")

    print(
        f"\n   📊 Success Rate: {success_count}/{len(test_messages)} ({round(success_count / len(test_messages) * 100)}%)"
    )
    return success_count == len(test_messages)


async def main():
    """Main diagnostic function."""
    print("🚀 LLM Status Diagnostic")
    print("=" * 50)

    print(f"📍 Configuration:")
    print(f"   Ollama Host: {settings.ollama_host}")
    print(f"   Text Model: {settings.ollama_text_model}")
    print(f"   Vision Model: {settings.ollama_vision_model}")

    # Check Ollama health
    ollama_healthy = await check_ollama_health()

    if not ollama_healthy:
        print("\n❌ Cannot proceed - Ollama service is not available")
        return

    # List available models
    available_models = await list_available_models()

    # Check if configured model is available
    configured_model = settings.ollama_text_model
    if configured_model in available_models:
        print(f"\n✅ Configured text model '{configured_model}' is available")
    else:
        print(
            f"\n⚠️  Configured text model '{configured_model}' not found in available models"
        )

        # Suggest alternatives
        qwen_models = [m for m in available_models if "qwen" in m.lower()]
        if qwen_models:
            print("   Available Qwen models:")
            for model in qwen_models:
                print(f"      • {model}")

    # Test the configured model
    if configured_model in available_models:
        model_works = await test_model_response(configured_model)

        if model_works:
            # Test full chat intent parsing
            chat_works = await test_chat_intent_parsing()

            if chat_works:
                print(f"\n🎉 All systems are working perfectly!")
                print("✅ Ollama service: Online")
                print(f"✅ Model '{configured_model}': Responding")
                print("✅ Chat intent parsing: Working")
                print("\n💡 Your LLM-powered chat is ready for natural conversations!")
            else:
                print(f"\n⚠️  Chat intent parsing has issues")
        else:
            print(f"\n❌ Model '{configured_model}' is not responding properly")

    print("\n" + "=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
