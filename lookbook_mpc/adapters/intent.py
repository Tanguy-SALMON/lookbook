"""
Intent Parsing Adapter

This adapter handles parsing user natural language requests into
structured intent constraints using Ollama text models.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging
import structlog

logger = structlog.get_logger()


class IntentParser(ABC):
    """Abstract base class for intent parsers."""

    @abstractmethod
    async def parse_intent(self, text: str) -> Dict[str, Any]:
        """Parse natural language text into structured intent."""
        pass


class LLMIntentParser(IntentParser):
    """LLM-based intent parser using Ollama."""

    def __init__(self, host: str, model: str, timeout: int = 30):
        self.host = host
        self.model = model
        self.timeout = timeout
        self.logger = logger.bind(parser="llm", model=model)

    async def parse_intent(self, text: str) -> Dict[str, Any]:
        """
        Parse natural language text into structured intent.

        Args:
            text: Natural language request from user

        Returns:
            Dictionary with structured intent constraints
        """
        try:
            self.logger.info("Parsing user intent", text=text)

            # Define the prompt template for intent parsing
            prompt = f"""
            You are a fashion intent parser. Convert the user's request into structured JSON constraints.

            User request: "{text}"

            Output JSON with the following structure:
            {{
                "intent": "primary_intent",
                "activity": null|"yoga"|"gym"|"running"|"walking" etc.,
                "occasion": null|"casual"|"business"|"formal"|"party"|"wedding" etc.,
                "budget_max": null|number,
                "objectives": ["slimming"|"comfort"|"style" etc.],
                "palette": null|["dark"|"light"|"bright"|"pastel" etc.],
                "formality": null|"casual"|"elevated"|"athleisure" etc.,
                "timeframe": null|"this_weekend"|"next_week"|"immediate" etc.,
                "size": null|"XS"|"S"|"M"|"L"|"XL"|"XXL" etc.
            }}

            Examples:
            - "I want to do yoga" -> {{ "intent": "recommend_outfits", "activity": "yoga", "occasion": "casual", "objectives": ["comfort"] }}
            - "Restaurant this weekend, attractive for $50" -> {{ "intent": "recommend_outfits", "occasion": "dinner", "budget_max": 50, "timeframe": "this_weekend", "formality": "elevated" }}
            - "I am fat, look slim" -> {{ "intent": "recommend_outfits", "objectives": ["slimming"], "palette": ["dark", "monochrome"] }}

            Respond with ONLY the JSON object, no other text.
            """

            # Placeholder implementation
            # In real implementation, this would:
            # 1. Send prompt to Ollama text model
            # 2. Parse JSON response
            # 3. Validate and return structured intent

            # Mock response for development
            intent_mapping = {
                "yoga": {"intent": "recommend_outfits", "activity": "yoga", "occasion": "casual", "objectives": ["comfort"], "formality": "athleisure"},
                "restaurant": {"intent": "recommend_outfits", "occasion": "dinner", "budget_max": 50, "timeframe": "this_weekend", "formality": "elevated"},
                "slim": {"intent": "recommend_outfits", "objectives": ["slimming"], "palette": ["dark", "monochrome"]},
                "casual": {"intent": "recommend_outfits", "occasion": "casual", "formality": "casual"},
                "business": {"intent": "recommend_outfits", "occasion": "business", "formality": "business"},
                "party": {"intent": "recommend_outfits", "occasion": "party", "formality": "elevated"},
                "beach": {"intent": "recommend_outfits", "occasion": "beach", "formality": "casual"},
                "sport": {"intent": "recommend_outfits", "occasion": "sport", "formality": "athleisure"}
            }

            # Find matching keywords in text
            text_lower = text.lower()
            matched_intent = None

            for keyword, intent in intent_mapping.items():
                if keyword in text_lower:
                    matched_intent = intent
                    break

            if matched_intent:
                return matched_intent
            else:
                # Default intent
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


class MockIntentParser(IntentParser):
    """Mock intent parser for testing purposes."""

    def __init__(self):
        self.logger = logger.bind(parser="mock")

    async def parse_intent(self, text: str) -> Dict[str, Any]:
        """Return mock intent based on text analysis."""
        self.logger.info("Mock intent parsing", text=text)

        text_lower = text.lower()

        # Keyword-based intent mapping
        if any(word in text_lower for word in ["yoga", "gym", "exercise", "workout"]):
            return {
                "intent": "recommend_outfits",
                "activity": "yoga",
                "occasion": "casual",
                "objectives": ["comfort"],
                "formality": "athleisure"
            }
        elif any(word in text_lower for word in ["restaurant", "dinner", "date"]):
            return {
                "intent": "recommend_outfits",
                "occasion": "dinner",
                "budget_max": 50,
                "timeframe": "this_weekend",
                "formality": "elevated"
            }
        elif any(word in text_lower for word in ["slim", "thin", "fit", "lose weight"]):
            return {
                "intent": "recommend_outfits",
                "objectives": ["slimming"],
                "palette": ["dark", "monochrome"]
            }
        elif any(word in text_lower for word in ["casual", "everyday", "normal"]):
            return {
                "intent": "recommend_outfits",
                "occasion": "casual",
                "formality": "casual"
            }
        elif any(word in text_lower for word in ["business", "office", "work"]):
            return {
                "intent": "recommend_outfits",
                "occasion": "business",
                "formality": "business"
            }
        elif any(word in text_lower for word in ["party", "event", "celebration"]):
            return {
                "intent": "recommend_outfits",
                "occasion": "party",
                "formality": "elevated"
            }
        elif any(word in text_lower for word in ["beach", "summer", "vacation"]):
            return {
                "intent": "recommend_outfits",
                "occasion": "beach",
                "formality": "casual"
            }
        elif any(word in text_lower for word in ["sport", "athletic", "active"]):
            return {
                "intent": "recommend_outfits",
                "occasion": "sport",
                "formality": "athleisure"
            }
        else:
            # Default intent
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