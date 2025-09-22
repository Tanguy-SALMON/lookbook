"""
LLM Provider Abstraction

This module provides flexible LLM provider system supporting both Ollama and OpenRouter,
allowing easy switching between local and remote models via configuration.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import logging
import structlog
import aiohttp
import json
import re
import os
from dataclasses import dataclass

logger = structlog.get_logger()


@dataclass
class LLMRequest:
    """Standard request format for LLM providers."""

    prompt: str
    temperature: float = 0.0
    max_tokens: int = 512
    system_prompt: Optional[str] = None
    json_mode: bool = False


@dataclass
class LLMResponse:
    """Standard response format from LLM providers."""

    content: str
    success: bool
    error_message: Optional[str] = None
    usage_tokens: Optional[int] = None
    model_used: Optional[str] = None


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    async def generate_text(self, request: LLMRequest) -> LLMResponse:
        """Generate text using the LLM provider."""
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """Get the provider name for logging."""
        pass


class OllamaProvider(LLMProvider):
    """Ollama-based LLM provider for local models."""

    def __init__(self, host: str, model: str, timeout: int = 30):
        self.host = host.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.logger = logger.bind(provider="ollama", model=model, host=host)

    async def generate_text(self, request: LLMRequest) -> LLMResponse:
        """Generate text using Ollama API."""
        try:
            self.logger.info(
                "Generating text with Ollama",
                prompt_length=len(request.prompt),
                temperature=request.temperature,
                max_tokens=request.max_tokens,
            )

            # Build the prompt with system message if provided
            final_prompt = request.prompt
            if request.system_prompt:
                final_prompt = f"{request.system_prompt}\n\n{request.prompt}"

            payload = {
                "model": self.model,
                "prompt": final_prompt,
                "temperature": request.temperature,
                "max_tokens": request.max_tokens,
                "stream": False,
            }

            # Add JSON mode instruction if requested
            if request.json_mode:
                payload["format"] = "json"

            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            ) as session:
                async with session.post(
                    f"{self.host}/api/generate", json=payload
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        content = result.get("response", "")

                        if not content or content.strip() == "":
                            return LLMResponse(
                                content="",
                                success=False,
                                error_message="Empty response from Ollama",
                                model_used=self.model,
                            )

                        return LLMResponse(
                            content=content,
                            success=True,
                            model_used=self.model,
                        )
                    else:
                        error_text = await response.text()
                        return LLMResponse(
                            content="",
                            success=False,
                            error_message=f"Ollama API error: {response.status} - {error_text}",
                            model_used=self.model,
                        )

        except Exception as e:
            self.logger.error("Error generating text with Ollama", error=str(e))
            return LLMResponse(
                content="",
                success=False,
                error_message=f"Ollama error: {str(e)}",
                model_used=self.model,
            )

    def get_provider_name(self) -> str:
        return f"ollama({self.model})"


class OpenRouterProvider(LLMProvider):
    """OpenRouter-based LLM provider for remote models."""

    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str = "https://openrouter.ai/api/v1",
        timeout: int = 60,
    ):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self.timeout = timeout
        self.logger = logger.bind(provider="openrouter", model=model)

    async def generate_text(self, request: LLMRequest) -> LLMResponse:
        """Generate text using OpenRouter API."""
        try:
            self.logger.info(
                "Generating text with OpenRouter",
                prompt_length=len(request.prompt),
                temperature=request.temperature,
                max_tokens=request.max_tokens,
            )

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://lookbook-mpc",
                "X-Title": "Lookbook-MPC",
            }

            # Build messages format for OpenRouter
            messages = []
            if request.system_prompt:
                messages.append({"role": "system", "content": request.system_prompt})
            messages.append({"role": "user", "content": request.prompt})

            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": request.temperature,
                "max_tokens": request.max_tokens,
                "top_p": 0.9,
                "presence_penalty": 0.0,
                "frequency_penalty": 0.0,
                "stream": False,
            }

            # Add JSON mode if requested (OpenAI-compatible models)
            if request.json_mode:
                payload["response_format"] = {"type": "json_object"}

            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            ) as session:
                async with session.post(
                    f"{self.base_url}/chat/completions", json=payload, headers=headers
                ) as response:
                    if response.status == 200:
                        result = await response.json()

                        if "choices" in result and len(result["choices"]) > 0:
                            content = result["choices"][0]["message"]["content"]
                            usage_tokens = result.get("usage", {}).get(
                                "total_tokens", 0
                            )

                            return LLMResponse(
                                content=content,
                                success=True,
                                usage_tokens=usage_tokens,
                                model_used=self.model,
                            )
                        else:
                            return LLMResponse(
                                content="",
                                success=False,
                                error_message="No response choices from OpenRouter",
                                model_used=self.model,
                            )

                    elif response.status == 429:
                        return LLMResponse(
                            content="",
                            success=False,
                            error_message="Rate limited by OpenRouter API",
                            model_used=self.model,
                        )
                    else:
                        error_text = await response.text()
                        try:
                            error_json = json.loads(error_text)
                            if "error" in error_json:
                                error_detail = error_json["error"]
                                if isinstance(error_detail, dict):
                                    error_text = error_detail.get("message", error_text)
                                else:
                                    error_text = str(error_detail)
                        except:
                            pass

                        return LLMResponse(
                            content="",
                            success=False,
                            error_message=f"OpenRouter API error: {response.status} - {error_text}",
                            model_used=self.model,
                        )

        except Exception as e:
            self.logger.error("Error generating text with OpenRouter", error=str(e))
            return LLMResponse(
                content="",
                success=False,
                error_message=f"OpenRouter error: {str(e)}",
                model_used=self.model,
            )

    def get_provider_name(self) -> str:
        return f"openrouter({self.model})"


class LLMProviderFactory:
    """Factory for creating LLM providers based on configuration."""

    @staticmethod
    def create_provider(
        provider_type: str,
        model: str,
        host: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: int = 30,
    ) -> LLMProvider:
        """
        Create an LLM provider based on configuration.

        Args:
            provider_type: "ollama" or "openrouter"
            model: Model name to use
            host: Host URL (for Ollama)
            api_key: API key (for OpenRouter)
            timeout: Request timeout in seconds

        Returns:
            LLMProvider instance
        """
        if provider_type.lower() == "ollama":
            if not host:
                raise ValueError("Host is required for Ollama provider")
            return OllamaProvider(host=host, model=model, timeout=timeout)

        elif provider_type.lower() == "openrouter":
            if not api_key:
                raise ValueError("API key is required for OpenRouter provider")
            return OpenRouterProvider(api_key=api_key, model=model, timeout=timeout)

        else:
            raise ValueError(f"Unsupported provider type: {provider_type}")

    @staticmethod
    def create_from_env(
        fallback_provider: str = "ollama",
        fallback_model: str = "qwen3:4b-instruct",
    ) -> LLMProvider:
        """
        Create provider from environment variables with fallback.

        Environment variables checked:
        - LLM_PROVIDER: "ollama" or "openrouter"
        - LLM_MODEL: Model name to use
        - OLLAMA_HOST: Ollama host URL
        - OPENROUTER_API_KEY: OpenRouter API key
        - LLM_TIMEOUT: Request timeout

        Args:
            fallback_provider: Provider to use if not specified in env
            fallback_model: Model to use if not specified in env

        Returns:
            LLMProvider instance
        """
        provider_type = os.getenv("LLM_PROVIDER", fallback_provider).lower()
        model = os.getenv("LLM_MODEL", fallback_model)
        timeout = int(os.getenv("LLM_TIMEOUT", "30"))

        logger.info(
            "Creating LLM provider from environment",
            provider_type=provider_type,
            model=model,
            timeout=timeout,
        )

        if provider_type == "openrouter":
            api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENROUTER_KEY")
            if not api_key:
                logger.warning(
                    "OpenRouter API key not found, falling back to Ollama",
                    fallback_provider=fallback_provider,
                    fallback_model=fallback_model,
                )
                # Fallback to Ollama
                host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
                return OllamaProvider(host=host, model=fallback_model, timeout=timeout)

            return OpenRouterProvider(api_key=api_key, model=model, timeout=timeout)

        else:  # ollama or any other value
            host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
            return OllamaProvider(host=host, model=model, timeout=timeout)


# Convenience functions for common use cases
async def generate_intent_response(
    prompt: str, provider: LLMProvider, system_prompt: Optional[str] = None
) -> LLMResponse:
    """Generate intent parsing response with JSON mode."""
    request = LLMRequest(
        prompt=prompt,
        temperature=0.1,
        max_tokens=512,
        system_prompt=system_prompt,
        json_mode=True,
    )
    return await provider.generate_text(request)


async def generate_chat_response(
    prompt: str, provider: LLMProvider, system_prompt: Optional[str] = None
) -> LLMResponse:
    """Generate chat response with moderate creativity."""
    request = LLMRequest(
        prompt=prompt,
        temperature=0.3,
        max_tokens=256,
        system_prompt=system_prompt,
        json_mode=False,
    )
    return await provider.generate_text(request)


def parse_json_response(response_content: str) -> Dict[str, Any]:
    """
    Parse JSON from LLM response, handling common formatting issues.

    Args:
        response_content: Raw text response from LLM

    Returns:
        Parsed JSON dictionary
    """
    try:
        # Try direct parsing first
        return json.loads(response_content)
    except json.JSONDecodeError:
        # Extract JSON from response (may have surrounding text)
        json_match = re.search(r"\{.*\}", response_content, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            return json.loads(json_str)
        else:
            raise ValueError("No JSON found in response")
