"""
Strategy Service

This service manages chat strategies, tone, and persona for the fashion AI assistant.
It provides controllable strategy layers around the chat use case to influence
both recommendations and response tone based on business objectives.
"""

import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import logging
import pymysql
from dataclasses import dataclass
import re

from ..config import settings


@dataclass
class Strategy:
    """Strategy configuration for chat interactions."""

    name: str
    tone: str
    language: str
    objectives: List[str]
    guardrails: List[str]
    style_config: Dict[str, Any]
    description: Optional[str] = None
    is_active: bool = True


class StrategyService:
    """Service for managing chat strategies and tone application."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._default_strategy = None
        self._strategy_cache = {}
        self._load_default_strategy()

    def _get_db_connection(self):
        """Get database connection."""
        return pymysql.connect(
            host="127.0.0.1",
            port=3306,
            user="magento",
            password="Magento@COS(*)",
            database="lookbookMPC",
            charset="utf8mb4",
        )

    def _load_default_strategy(self):
        """Load default strategy from database."""
        try:
            connection = self._get_db_connection()
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT * FROM chat_strategies WHERE is_default = 1 LIMIT 1"
                )
                result = cursor.fetchone()
                if result:
                    self._default_strategy = self._parse_strategy_row(result)
            connection.close()
        except Exception as e:
            self.logger.error(f"Error loading default strategy: {e}")
            self._default_strategy = self._get_fallback_strategy()

    def _parse_strategy_row(self, row: Tuple) -> Strategy:
        """Parse database row into Strategy object."""
        # Assuming column order from CREATE TABLE statement
        return Strategy(
            name=row[1],  # strategy_name
            tone=row[2],  # tone
            language=row[3],  # language
            objectives=json.loads(row[4]) if row[4] else [],  # objectives
            guardrails=json.loads(row[5]) if row[5] else [],  # guardrails
            style_config=json.loads(row[6]) if row[6] else {},  # style_config
            description=row[10],  # description
            is_active=bool(row[7]),  # is_active
        )

    def _get_fallback_strategy(self) -> Strategy:
        """Get fallback strategy when database is unavailable."""
        return Strategy(
            name="fallback",
            tone="friendly",
            language="en",
            objectives=["assist", "recommend"],
            guardrails=["no_pressure", "respect_budget"],
            style_config={"max_sentences": 3, "cta": "soft", "emojis": False},
            description="Fallback strategy when database unavailable",
        )

    def get_strategy(
        self, session_id: str, strategy_override: Optional[Dict] = None
    ) -> Strategy:
        """
        Get strategy for a session with optional override.

        Args:
            session_id: Session identifier
            strategy_override: Optional strategy override from request

        Returns:
            Strategy configuration to use
        """
        try:
            # Start with default strategy
            strategy = self._default_strategy or self._get_fallback_strategy()

            # Check for session-specific strategy
            session_strategy = self._get_session_strategy(session_id)
            if session_strategy:
                strategy = session_strategy

            # Apply any request-level overrides
            if strategy_override:
                strategy = self._apply_strategy_override(strategy, strategy_override)

            return strategy

        except Exception as e:
            self.logger.error(f"Error getting strategy for session {session_id}: {e}")
            return self._get_fallback_strategy()

    def _get_session_strategy(self, session_id: str) -> Optional[Strategy]:
        """Get strategy stored for a specific session."""
        try:
            connection = self._get_db_connection()
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT current_strategy FROM chat_sessions WHERE session_id = %s",
                    (session_id,),
                )
                result = cursor.fetchone()
                if result and result[0]:
                    strategy_data = json.loads(result[0])
                    return Strategy(**strategy_data)
            connection.close()
        except Exception as e:
            self.logger.error(f"Error getting session strategy: {e}")
        return None

    def _apply_strategy_override(
        self, base_strategy: Strategy, override: Dict
    ) -> Strategy:
        """Apply override values to base strategy."""
        strategy_dict = {
            "name": override.get("name", base_strategy.name),
            "tone": override.get("tone", base_strategy.tone),
            "language": override.get("language", base_strategy.language),
            "objectives": override.get("objectives", base_strategy.objectives),
            "guardrails": override.get("guardrails", base_strategy.guardrails),
            "style_config": {
                **base_strategy.style_config,
                **override.get("style_config", {}),
            },
            "description": override.get("description", base_strategy.description),
        }
        return Strategy(**strategy_dict)

    def build_system_directive(self, strategy: Strategy) -> str:
        """
        Build system directive from strategy configuration.

        Args:
            strategy: Strategy configuration

        Returns:
            System directive string for LLM
        """
        directive_parts = []

        # Persona and tone
        tone_mapping = {
            "friendly": "Persona: Friendly fashion advisor. Tone: warm, approachable, helpful.",
            "luxury_concise": "Persona: Premium fashion advisor. Tone: concise, elegant, sophisticated.",
            "minimalist_luxury": "Persona: Minimalist luxury advisor. Tone: refined, understated, quality-focused.",
            "playful": "Persona: Trendy fashion advisor. Tone: energetic, fun, trend-aware.",
        }
        directive_parts.append(
            tone_mapping.get(
                strategy.tone, "Persona: Fashion advisor. Tone: helpful, professional."
            )
        )

        # Language requirements
        if strategy.language == "th_en":
            directive_parts.append(
                "Language: Respond in Thai first, then English translation in parentheses."
            )
        elif strategy.language == "th":
            directive_parts.append("Language: Respond only in Thai.")
        else:
            directive_parts.append("Language: Respond in English.")

        # Business objectives
        if strategy.objectives:
            objectives_text = self._format_objectives(strategy.objectives)
            directive_parts.append(f"Goals: {objectives_text}")

        # Guardrails
        if strategy.guardrails:
            guardrails_text = self._format_guardrails(strategy.guardrails)
            directive_parts.append(f"Guardrails: {guardrails_text}")

        # Style constraints
        style = strategy.style_config
        style_parts = []

        if style.get("max_sentences"):
            style_parts.append(
                f"Keep responses to {style['max_sentences']} sentences max"
            )

        if style.get("cta"):
            cta_strength = style["cta"]
            if cta_strength == "soft":
                style_parts.append("End with gentle suggestion or question")
            elif cta_strength == "medium":
                style_parts.append("Include clear call-to-action")
            elif cta_strength == "hard":
                style_parts.append("End with strong call-to-action")

        if not style.get("emojis", True):
            style_parts.append("No emojis")

        if style_parts:
            directive_parts.append(f"Style: {'; '.join(style_parts)}")

        return " ".join(directive_parts)

    def _format_objectives(self, objectives: List[str]) -> str:
        """Format objectives into readable text."""
        objective_mapping = {
            "assist": "help user find perfect outfit",
            "recommend": "provide personalized recommendations",
            "raise_aov": "suggest complementary accessories when appropriate",
            "promote_new_arrivals": "highlight new arrivals when relevant",
            "promote_quality": "emphasize quality and craftsmanship",
            "upsell_accessories": "suggest matching accessories",
            "clear_aging_stock": "promote items on sale when suitable",
            "local_engagement": "connect with local Thai culture",
            "cultural_appropriate": "be culturally sensitive and appropriate",
        }

        formatted = [objective_mapping.get(obj, obj) for obj in objectives]
        return "; ".join(formatted)

    def _format_guardrails(self, guardrails: List[str]) -> str:
        """Format guardrails into readable text."""
        guardrail_mapping = {
            "no_pressure": "never pressure user to buy",
            "respect_budget": "respect user's budget constraints",
            "no_discount_push": "avoid mentioning discounts unless asked",
            "maintain_brand_image": "maintain premium brand perception",
            "no_hard_sell": "avoid aggressive sales tactics",
            "respect_culture": "be culturally respectful",
            "clear_communication": "ensure clear, understandable communication",
            "quality_focus": "focus on quality over quantity",
        }

        formatted = [guardrail_mapping.get(guard, guard) for guard in guardrails]
        return "; ".join(formatted)

    def apply_reply_tone(self, reply: str, strategy: Strategy) -> str:
        """
        Apply tone post-processing to reply based on strategy.

        Args:
            reply: Original reply text
            strategy: Strategy configuration

        Returns:
            Tone-adjusted reply
        """
        try:
            processed_reply = reply
            style = strategy.style_config

            # Apply sentence limit
            if style.get("max_sentences"):
                processed_reply = self._limit_sentences(
                    processed_reply, style["max_sentences"]
                )

            # Apply CTA formatting
            if style.get("cta"):
                processed_reply = self._apply_cta_formatting(
                    processed_reply, style["cta"]
                )

            # Apply bilingual formatting
            if strategy.language == "th_en" and style.get("bilingual"):
                processed_reply = self._apply_bilingual_formatting(processed_reply)

            # Apply emoji policy
            if not style.get("emojis", True):
                processed_reply = self._remove_emojis(processed_reply)

            return processed_reply

        except Exception as e:
            self.logger.error(f"Error applying tone to reply: {e}")
            return reply  # Return original if processing fails

    def _limit_sentences(self, text: str, max_sentences: int) -> str:
        """Limit text to maximum number of sentences."""
        # Simple sentence splitting (can be improved)
        sentences = re.split(r"[.!?]+", text)
        sentences = [s.strip() for s in sentences if s.strip()]

        if len(sentences) > max_sentences:
            limited = sentences[:max_sentences]
            return ". ".join(limited) + "."

        return text

    def _apply_cta_formatting(self, text: str, cta_strength: str) -> str:
        """Apply call-to-action formatting based on strength."""
        # Ensure proper punctuation
        if not text.endswith(("?", "!", ".")):
            text += "."

        # Disable automatic CTA addition to keep LLM responses natural
        # The LLM already generates contextually appropriate responses
        return text

    def _apply_bilingual_formatting(self, text: str) -> str:
        """Apply bilingual Thai-English formatting."""
        # This is a simplified implementation
        # In production, you'd use proper translation service
        if not text.startswith("สวัสดี") and not text.startswith("ค่ะ"):
            # Add Thai greeting if not present
            thai_greeting = "สวัสดีค่ะ! "
            return thai_greeting + text
        return text

    def _remove_emojis(self, text: str) -> str:
        """Remove emojis from text."""
        # Simple emoji removal pattern
        emoji_pattern = re.compile(
            "["
            "\U0001f600-\U0001f64f"  # emoticons
            "\U0001f300-\U0001f5ff"  # symbols & pictographs
            "\U0001f680-\U0001f6ff"  # transport & map symbols
            "\U0001f1e0-\U0001f1ff"  # flags (iOS)
            "\U00002702-\U000027b0"
            "\U000024c2-\U0001f251"
            "]+",
            flags=re.UNICODE,
        )
        return emoji_pattern.sub("", text)

    def set_session_strategy(self, session_id: str, strategy_name: str) -> bool:
        """
        Set strategy for a specific session.

        Args:
            session_id: Session identifier
            strategy_name: Name of strategy to apply

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get strategy from database
            strategy = self._get_strategy_by_name(strategy_name)
            if not strategy:
                return False

            # Update or create session record
            connection = self._get_db_connection()
            with connection.cursor() as cursor:
                # Convert strategy to JSON
                strategy_json = json.dumps(
                    {
                        "name": strategy.name,
                        "tone": strategy.tone,
                        "language": strategy.language,
                        "objectives": strategy.objectives,
                        "guardrails": strategy.guardrails,
                        "style_config": strategy.style_config,
                    }
                )

                # Update session strategy
                cursor.execute(
                    """
                    INSERT INTO chat_sessions (session_id, current_strategy, created_at)
                    VALUES (%s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                    current_strategy = %s, last_activity = CURRENT_TIMESTAMP
                """,
                    (session_id, strategy_json, datetime.now(), strategy_json),
                )

            connection.commit()
            connection.close()
            return True

        except Exception as e:
            self.logger.error(f"Error setting session strategy: {e}")
            return False

    def _get_strategy_by_name(self, strategy_name: str) -> Optional[Strategy]:
        """Get strategy by name from database."""
        try:
            connection = self._get_db_connection()
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT * FROM chat_strategies WHERE strategy_name = %s AND is_active = 1",
                    (strategy_name,),
                )
                result = cursor.fetchone()
                if result:
                    return self._parse_strategy_row(result)
            connection.close()
        except Exception as e:
            self.logger.error(f"Error getting strategy by name: {e}")
        return None

    def get_available_strategies(self) -> List[Dict[str, Any]]:
        """Get list of available strategies."""
        try:
            strategies = []
            connection = self._get_db_connection()
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT strategy_name, tone, language, description FROM chat_strategies WHERE is_active = 1"
                )
                results = cursor.fetchall()
                for row in results:
                    strategies.append(
                        {
                            "name": row[0],
                            "tone": row[1],
                            "language": row[2],
                            "description": row[3] or "No description available",
                        }
                    )
            connection.close()
            return strategies

        except Exception as e:
            self.logger.error(f"Error getting available strategies: {e}")
            return [
                {
                    "name": "fallback",
                    "tone": "friendly",
                    "language": "en",
                    "description": "Default fallback",
                }
            ]

    def get_recommendation_weights(self, strategy: Strategy) -> Dict[str, float]:
        """
        Get recommendation scoring weights based on strategy.

        Args:
            strategy: Strategy configuration

        Returns:
            Dictionary of scoring weights
        """
        weights = {
            "base_score": 1.0,
            "margin_weight": 0.0,
            "newness_weight": 0.0,
            "stock_age_weight": 0.0,
            "popularity_weight": 0.1,
            "season_match_weight": 0.2,
        }

        # Adjust weights based on objectives
        for objective in strategy.objectives:
            if objective == "raise_aov":
                weights["margin_weight"] = 0.2
            elif objective == "promote_new_arrivals":
                weights["newness_weight"] = 0.3
            elif objective == "clear_aging_stock":
                weights["stock_age_weight"] = 0.25
            elif objective == "promote_quality":
                weights["margin_weight"] = 0.15
                weights["popularity_weight"] = 0.15

        return weights
