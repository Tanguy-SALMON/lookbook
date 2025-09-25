"""
Intent Parsing Adapter

This adapter handles parsing user natural language requests into
structured intent constraints using flexible LLM providers (Ollama or OpenRouter).
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging
import structlog
import json
import re
from .llm_providers import (
    LLMProvider,
    LLMProviderFactory,
    LLMRequest,
    LLMResponse,
    parse_json_response,
    generate_intent_response,
)

logger = structlog.get_logger()


class IntentParser(ABC):
    """Abstract base class for intent parsers."""

    @abstractmethod
    async def parse_intent(self, text: str) -> Dict[str, Any]:
        """Parse natural language text into structured intent."""
        pass


class LLMIntentParser(IntentParser):
    """LLM-based intent parser using flexible LLM providers."""

    def __init__(self, provider: LLMProvider):
        self.provider = provider
        self.logger = logger.bind(parser="llm", provider=provider.get_provider_name())

    async def parse_intent(self, text: str) -> Dict[str, Any]:
        """
        Parse natural language text into structured intent using flexible LLM provider.

        This is the entry point for converting user messages into structured fashion intents.
        The LLM analyzes the natural language and extracts key information like activity,
        occasion, style preferences, and generates an appropriate natural response.

        Example Input: "I go to dance"
        Example Output: {
            "intent": "recommend_outfits",
            "activity": "dancing",
            "occasion": "party",
            "objectives": ["style", "trendy"],
            "formality": "elevated",
            "natural_response": "Perfect! I'll help you find stylish outfits for dancing..."
        }

        Example Input: "Hello"
        Example Output: {
            "intent": "recommend_outfits",
            "occasion": "casual",
            "objectives": ["style"],
            "formality": "casual",
            "natural_response": "Hello! I'm your AI fashion assistant. What are you looking for today?"
        }

        Args:
            text: Natural language request from user (e.g., "I go to dance", "need work clothes")

        Returns:
            Dictionary with structured intent constraints and natural response for user
        """
        try:
            self.logger.info("Parsing user intent", text=text)

            system_prompt = """You are a fashion assistant parsing customer requests. Convert the user's message into structured JSON. Be natural and understanding.

Output format (JSON only):
{
  "intent": "recommend_outfits",
  "activity": null|"yoga"|"gym"|"running"|"walking"|"hiking"|"swimming"|"cycling"|"dancing"|"fitness"|"driving"|"traveling",
  "occasion": null|"casual"|"business"|"formal"|"party"|"wedding"|"sport"|"beach"|"sleep"|"travel"|"date"|"shopping",
  "budget_max": null|number,
  "objectives": ["slimming"|"comfort"|"style"|"professional"|"trendy"|"classic"|"bold"|"minimalist"|"attractive"],
  "palette": null|["dark"|"light"|"bright"|"pastel"|"earth"|"neon"|"monochrome"|"neutral"],
  "formality": "casual"|"elevated"|"athleisure"|"business_casual"|"cocktail"|"gala",
  "timeframe": null|"this_weekend"|"next_week"|"immediate"|"next_month"|"seasonal",
  "size": null|"XS"|"S"|"M"|"L"|"XL"|"XXL"|"XXXL"|"PLUS",
  "natural_response": "A helpful response to the user"
}

Examples:
"I go to dance" -> {"intent":"recommend_outfits","activity":"dancing","occasion":"party","objectives":["style","trendy"],"formality":"elevated","natural_response":"Perfect! I'll help you find stylish outfits for dancing. Let me show you some great options that will make you look amazing on the dance floor!"}
"I like drive" -> {"intent":"recommend_outfits","activity":"driving","occasion":"travel","objectives":["comfort","style"],"formality":"casual","natural_response":"Great! I'll find you comfortable and stylish outfits perfect for driving and traveling. Let me show you some options!"}
"Hello" -> {"intent":"recommend_outfits","occasion":"casual","objectives":["style"],"formality":"casual","natural_response":"Hello! I'm your AI fashion assistant. I can help you find the perfect outfit for any occasion. What are you looking for today?"}

Return ONLY the JSON object."""

            prompt = f'User message: "{text}"'

            # Use the flexible provider system
            response = await generate_intent_response(
                prompt=prompt,
                provider=self.provider,
                system_prompt=system_prompt,
            )

            if not response.success:
                raise Exception(f"LLM error: {response.error_message}")

            # Parse JSON response
            return self._parse_json_response(response.content)

        except Exception as e:
            self.logger.error("Error parsing intent", text=text, error=str(e))
            # Return a more helpful default response that acknowledges the user's input
            return {
                "intent": "recommend_outfits",
                "activity": None,
                "occasion": "casual",
                "budget_max": None,
                "objectives": ["style"],
                "palette": None,
                "formality": "casual",
                "timeframe": None,
                "size": None,
                "natural_response": f"I'd love to help you with that! Could you tell me a bit more about what kind of outfit you're looking for? Are you going somewhere special?",
            }

    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """
        Parse the JSON response from the LLM with error handling and field validation.

        The LLM sometimes returns JSON wrapped in other text or with formatting issues.
        This method extracts the JSON and ensures all required fields are present.

        Example Input: 'Here is the analysis: {"intent":"recommend_outfits","activity":"dancing",...}'
        Example Output: {"intent":"recommend_outfits","activity":"dancing","occasion":null,...}

        Args:
            response: Raw text response from LLM (may contain JSON embedded in text)

        Returns:
            Dictionary with parsed intent, validated and with all required fields
        """
        try:
            # Use the common JSON parsing utility
            result = parse_json_response(response)

            # Ensure all required fields exist with defaults
            required_fields = {
                "intent": "recommend_outfits",
                "activity": None,
                "occasion": None,
                "budget_max": None,
                "objectives": [],
                "palette": None,
                "formality": "casual",
                "timeframe": None,
                "size": None,
                "natural_response": "I'm here to help you find the perfect outfit! What are you looking for?",
            }

            for field, default_value in required_fields.items():
                if field not in result:
                    result[field] = default_value

            return result

        except Exception as e:
            self.logger.error(f"Error parsing JSON response: {str(e)}")
            return {
                "intent": "recommend_outfits",
                "activity": None,
                "occasion": "casual",
                "budget_max": None,
                "objectives": ["style"],
                "palette": None,
                "formality": "casual",
                "timeframe": None,
                "size": None,
                "natural_response": "I'm here to help you find the perfect outfit! What are you looking for?",
            }

    @classmethod
    def create_from_settings(cls, settings) -> "LLMIntentParser":
        """Create intent parser from application settings."""
        if settings.get_llm_provider_type() == "openrouter":
            api_key = settings.get_openrouter_api_key()
            if not api_key:
                logger.warning(
                    "OpenRouter API key not found, falling back to Ollama for intent parsing"
                )
                provider = LLMProviderFactory.create_provider(
                    provider_type="ollama",
                    model=settings.ollama_text_model,
                    host=settings.ollama_host,
                    timeout=settings.llm_timeout,
                )
            else:
                provider = LLMProviderFactory.create_provider(
                    provider_type="openrouter",
                    model=settings.get_llm_model_name(),
                    api_key=api_key,
                    timeout=settings.llm_timeout,
                )
        else:
            provider = LLMProviderFactory.create_provider(
                provider_type="ollama",
                model=settings.get_llm_model_name(),
                host=settings.ollama_host,
                timeout=settings.llm_timeout,
            )

        return cls(provider=provider)


# Convenience factory function for backward compatibility
def create_intent_parser(settings) -> IntentParser:
    """Create intent parser based on configuration."""
    return LLMIntentParser.create_from_settings(settings)


class MockIntentParser(IntentParser):
    """Mock intent parser for testing purposes."""

    def __init__(self):
        self.logger = logger.bind(parser="mock")

    async def parse_intent(self, text: str) -> Dict[str, Any]:
        """Return mock intent based on text analysis."""
        self.logger.info("Mock intent parsing", text=text)

        text_lower = text.lower()

        # Keyword-based intent mapping
        base_intent = {
            "intent": "recommend_outfits",
            "activity": None,
            "occasion": None,
            "budget_max": None,
            "objectives": [],
            "palette": None,
            "formality": None,
            "timeframe": None,
            "size": None,
        }

        # Extract budget from text
        budget_patterns = [
            r"under ฿?(\d+)",
            r"less than ฿?(\d+)",
            r"maximum ฿?(\d+)",
            r"max ฿?(\d+)",
            r"budget ฿?(\d+)",
            r"฿(\d+)",
        ]

        for pattern in budget_patterns:
            match = re.search(pattern, text_lower)
            if match:
                base_intent["budget_max"] = int(match.group(1))
                break

        # Handle time-related keywords
        if any(word in text_lower for word in ["tonight", "this evening"]):
            base_intent["timeframe"] = "immediate"
        elif any(word in text_lower for word in ["tomorrow", "next day"]):
            base_intent["timeframe"] = "immediate"
        elif any(word in text_lower for word in ["weekend", "saturday", "sunday"]):
            base_intent["timeframe"] = "this_weekend"
        elif any(
            word in text_lower
            for word in [
                "next week",
                "monday",
                "tuesday",
                "wednesday",
                "thursday",
                "friday",
            ]
        ):
            base_intent["timeframe"] = "next_week"

        # Handle greeting/hello responses
        if any(
            word in text_lower
            for word in [
                "hello",
                "hi",
                "hey",
                "good morning",
                "good afternoon",
                "good evening",
            ]
        ):
            base_intent.update(
                {"occasion": "casual", "formality": "casual", "objectives": ["style"]}
            )
        # Handle social occasions
        elif any(
            word in text_lower
            for word in ["friend", "friends", "social", "hang out", "meet", "see"]
        ):
            if any(
                word in text_lower
                for word in ["night", "evening", "dinner", "restaurant"]
            ):
                base_intent.update(
                    {
                        "occasion": "party",
                        "formality": "elevated",
                        "objectives": ["style", "trendy"],
                    }
                )
            else:
                base_intent.update(
                    {
                        "occasion": "casual",
                        "formality": "casual",
                        "objectives": ["style", "comfort"],
                    }
                )
        # Handle dating scenarios
        elif any(
            word in text_lower
            for word in ["date", "dating", "romantic", "boyfriend", "girlfriend"]
        ):
            base_intent.update(
                {
                    "occasion": "party",
                    "formality": "elevated",
                    "objectives": ["style", "trendy"],
                    "palette": ["bright"],
                }
            )
        # Handle party/night out
        elif any(
            word in text_lower
            for word in ["party", "club", "bar", "night out", "going out"]
        ):
            base_intent.update(
                {
                    "occasion": "party",
                    "formality": "elevated",
                    "objectives": ["style", "bold"],
                }
            )
        # Handle workout/fitness
        elif any(
            word in text_lower
            for word in ["yoga", "gym", "exercise", "workout", "fitness", "sport"]
        ):
            base_intent.update(
                {
                    "activity": "yoga",
                    "occasion": "sport",
                    "objectives": ["comfort"],
                    "formality": "athleisure",
                }
            )
        # Handle dining out
        elif any(
            word in text_lower
            for word in ["restaurant", "dinner", "lunch", "brunch", "dining"]
        ):
            base_intent.update(
                {"occasion": "party", "formality": "elevated", "objectives": ["style"]}
            )
        # Handle body image/slimming
        elif any(
            word in text_lower
            for word in ["slim", "thin", "fat", "slimming", "look good", "attractive"]
        ):
            base_intent.update(
                {
                    "objectives": ["slimming", "style"],
                    "palette": ["dark", "monochrome"],
                    "formality": "elevated",
                }
            )
        # Handle work/business
        elif any(
            word in text_lower
            for word in [
                "business",
                "office",
                "work",
                "meeting",
                "interview",
                "professional",
            ]
        ):
            base_intent.update(
                {
                    "occasion": "business",
                    "formality": "business",
                    "objectives": ["professional"],
                }
            )
        # Handle casual wear
        elif any(
            word in text_lower
            for word in ["casual", "everyday", "normal", "comfortable", "relax"]
        ):
            base_intent.update(
                {"occasion": "casual", "formality": "casual", "objectives": ["comfort"]}
            )
        # Handle beach/vacation
        elif any(
            word in text_lower
            for word in ["beach", "vacation", "holiday", "travel", "summer"]
        ):
            base_intent.update(
                {"occasion": "beach", "formality": "casual", "objectives": ["comfort"]}
            )
        # Handle colors
        elif any(
            word in text_lower
            for word in ["black", "white", "red", "blue", "green", "yellow", "pink"]
        ):
            if "black" in text_lower or "white" in text_lower:
                base_intent["palette"] = ["monochrome"]
            elif any(word in text_lower for word in ["red", "pink", "yellow"]):
                base_intent["palette"] = ["bright"]
            else:
                base_intent["palette"] = ["neutral"]

            base_intent.update(
                {"occasion": "casual", "formality": "casual", "objectives": ["style"]}
            )
        # Handle dress/clothing types
        elif any(
            word in text_lower
            for word in ["dress", "top", "shirt", "pants", "skirt", "suit"]
        ):
            base_intent.update(
                {"occasion": "casual", "formality": "casual", "objectives": ["style"]}
            )
        # Default case - general style request
        else:
            base_intent.update(
                {"occasion": "casual", "formality": "casual", "objectives": ["style"]}
            )

        return base_intent
