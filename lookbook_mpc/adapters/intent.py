"""
Intent Parsing Adapter

This adapter handles parsing user natural language requests into
structured intent constraints using Ollama text models.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging
import structlog
import aiohttp
import json
import re

logger = structlog.get_logger()


class IntentParser(ABC):
    """Abstract base class for intent parsers."""

    @abstractmethod
    async def parse_intent(self, text: str) -> Dict[str, Any]:
        """Parse natural language text into structured intent."""
        pass


class LLMIntentParser(IntentParser):
    """LLM-based intent parser using Ollama qwen3."""

    def __init__(self, host: str, model: str, timeout: int = 30):
        self.host = host.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.logger = logger.bind(parser="llm", model=model)

    async def parse_intent(self, text: str) -> Dict[str, Any]:
        """
        Parse natural language text into structured intent using qwen3.

        Args:
            text: Natural language request from user

        Returns:
            Dictionary with structured intent constraints
        """
        try:
            self.logger.info("Parsing user intent", text=text)

            prompt = """You are a fashion assistant parsing customer requests. Convert the user's message into structured JSON. Be natural and understanding.

User message: "{text}"

Output format (JSON only):
{{
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
}}

Examples:
"I go to dance" -> {{"intent":"recommend_outfits","activity":"dancing","occasion":"party","objectives":["style","trendy"],"formality":"elevated","natural_response":"Perfect! I'll help you find stylish outfits for dancing. Let me show you some great options that will make you look amazing on the dance floor!"}}
"I like drive" -> {{"intent":"recommend_outfits","activity":"driving","occasion":"travel","objectives":["comfort","style"],"formality":"casual","natural_response":"Great! I'll find you comfortable and stylish outfits perfect for driving and traveling. Let me show you some options!"}}
"Hello" -> {{"intent":"recommend_outfits","occasion":"casual","objectives":["style"],"formality":"casual","natural_response":"Hello! I'm your AI fashion assistant. I can help you find the perfect outfit for any occasion. What are you looking for today?"}}

Return ONLY the JSON object."""

            # Call Ollama API
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            ) as session:
                payload = {
                    "model": self.model,
                    "prompt": prompt.format(text=text),
                    "temperature": 0.3,  # Slightly more creative for natural responses
                    "max_tokens": 512,  # More tokens for natural responses
                    "stream": False,
                }

                async with session.post(
                    f"{self.host}/api/generate", json=payload
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        response_text = result.get("response", "")

                        if not response_text or response_text.strip() == "":
                            raise Exception("Empty response from Ollama")

                        # Parse JSON response
                        return self._parse_json_response(response_text)
                    else:
                        error_text = await response.text()
                        raise Exception(
                            f"Ollama API error: {response.status} - {error_text}"
                        )

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
        Parse the JSON response from the LLM.

        Args:
            response: Raw text response from LLM

        Returns:
            Dictionary with parsed intent
        """
        try:
            # Extract JSON from response (may have surrounding text)
            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                result = json.loads(json_str)

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
            else:
                raise ValueError("No JSON found in response")

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


# Removed HybridIntentParser - now using pure LLM only


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
