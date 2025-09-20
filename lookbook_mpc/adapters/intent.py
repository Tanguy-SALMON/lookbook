u"""
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
        self.host = host.rstrip('/')
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

            prompt = """You convert a shopper request into structured constraints. Output JSON only. Unknown fields = null.

User text: "{text}"

Response schema:
{{
  "intent":"recommend_outfits",
  "activity":null|"yoga"|"gym"|"running"|"walking"|"hiking"|"swimming"|"cycling"|"dancing"|"fitness",
  "occasion":null|"casual"|"business"|"formal"|"party"|"wedding"|"sport"|"beach"|"sleep"|"travel",
  "budget_max":null|number,
  "objectives":["slimming"|"comfort"|"style"|"professional"|"trendy"|"classic"|"bold"|"minimalist"],
  "palette":null|["dark"|"light"|"bright"|"pastel"|"earth"|"neon"|"monochrome"|"neutral"],
  "formality":"casual"|"elevated"|"athleisure"|"business_casual"|"cocktail"|"gala",
  "timeframe":null|"this_weekend"|"next_week"|"immediate"|"next_month"|"seasonal",
  "size":null|"XS"|"S"|"M"|"L"|"XL"|"XXL"|"XXXL"|"PLUS"
}}

Examples:
"I want to do yoga" -> {{"intent":"recommend_outfits","activity":"yoga","occasion":"casual","objectives":["comfort"],"formality":"athleisure"}}
"Restaurant this weekend, attractive for $50" -> {{"intent":"recommend_outfits","occasion":"dinner","budget_max":50,"timeframe":"this_weekend","formality":"elevated"}}
"I am fat, I want something to look slim" -> {{"intent":"recommend_outfits","objectives":["slimming"],"palette":["dark","monochrome"]}}

Respond with ONLY the JSON object, no other text."""

            # Call Ollama API
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                payload = {
                    "model": self.model,
                    "prompt": prompt.format(text=text),
                    "temperature": 0,
                    "max_tokens": 256,
                    "stream": False
                }

                async with session.post(f"{self.host}/api/generate", json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        response_text = result.get("response", "")

                        # Parse JSON response
                        return self._parse_json_response(response_text)
                    else:
                        error_text = await response.text()
                        raise Exception(f"Ollama API error: {response.status} - {error_text}")

        except Exception as e:
            self.logger.error("Error parsing intent", text=text, error=str(e))
            # Return default intent on error
            return {
                "intent": "recommend_outfits",
                "activity": None,
                "occasion": None,
                "budget_max": None,
                "objectives": [],
                "palette": None,
                "formality": None,
                "timeframe": None,
                "size": None
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
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
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
                    "formality": None,
                    "timeframe": None,
                    "size": None
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
                "occasion": None,
                "budget_max": None,
                "objectives": [],
                "palette": None,
                "formality": None,
                "timeframe": None,
                "size": None
            }


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
            "size": None
        }

        # Handle special keywords first
        if any(word in text_lower for word in ["test"]):
            # Test mode - return a simple test intent
            base_intent.update({
                "activity": "test",
                "occasion": "debug",
                "objectives": ["testing"],
                "formality": "casual"
            })
        elif any(word in text_lower for word in ["prod", "agent", "shop", "sell"]):
            # Production/agent mode - treat as general recommendation
            base_intent.update({
                "occasion": "casual",
                "formality": "casual",
                "objectives": ["style"]
            })
        elif any(word in text_lower for word in ["yoga", "gym", "exercise", "workout"]):
            base_intent.update({
                "activity": "yoga",
                "occasion": "casual",
                "objectives": ["comfort"],
                "formality": "athleisure"
            })
        elif any(word in text_lower for word in ["restaurant", "dinner", "date"]):
            base_intent.update({
                "occasion": "dinner",
                "budget_max": 50,
                "timeframe": "this_weekend",
                "formality": "elevated"
            })
        elif any(word in text_lower for word in ["slim", "thin", "fit", "lose weight"]):
            base_intent.update({
                "objectives": ["slimming"],
                "palette": ["dark", "monochrome"]
            })
        elif any(word in text_lower for word in ["casual", "everyday", "normal"]):
            base_intent.update({
                "occasion": "casual",
                "formality": "casual"
            })
        elif any(word in text_lower for word in ["business", "office", "work"]):
            base_intent.update({
                "occasion": "business",
                "formality": "business"
            })
        elif any(word in text_lower for word in ["party", "event", "celebration"]):
            base_intent.update({
                "occasion": "party",
                "formality": "elevated"
            })
        elif any(word in text_lower for word in ["beach", "summer", "vacation"]):
            base_intent.update({
                "occasion": "beach",
                "formality": "casual"
            })
        elif any(word in text_lower for word in ["sport", "athletic", "active"]):
            base_intent.update({
                "occasion": "sport",
                "formality": "athleisure"
            })

        return base_intent