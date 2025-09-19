
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
