"""
Configuration settings for Lookbook-MPC using pydantic BaseSettings.

This module provides type-safe configuration management with environment variable support.
"""

import os
import re
from typing import List, Optional
from pydantic import Field, AnyHttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Settings are loaded with the following precedence:
    1. Environment variables
    2. .env file (if present)
    3. Default values defined in this class
    """

    # Model configuration
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    # LLM Configuration
    llm_provider: str = Field(
        default="ollama", description="LLM provider: 'ollama' or 'openrouter'"
    )
    llm_model: str = Field(
        default="qwen3:4b-instruct",
        description="Primary model name for text generation",
    )
    llm_timeout: int = Field(default=30, description="LLM request timeout in seconds")

    # Ollama Configuration (when llm_provider="ollama")
    ollama_host: str = Field(
        default="http://localhost:11434", description="Ollama service URL"
    )
    ollama_text_model: str = Field(
        default="qwen3:4b-instruct",
        description="Text model for intent parsing and rationales",
    )
    ollama_text_model_fast: str = Field(
        default="llama3.2:1b-instruct-q4_K_M",
        description="Fast text model for testing and development",
    )
    ollama_vision_model: str = Field(
        default="qwen2.5vl:7b", description="Vision model for image analysis"
    )

    # OpenRouter Configuration (when llm_provider="openrouter")
    openrouter_api_key: Optional[str] = Field(
        default=None, description="OpenRouter API key for remote model access"
    )
    openrouter_base_url: str = Field(
        default="https://openrouter.ai/api/v1", description="OpenRouter API base URL"
    )
    openrouter_model: str = Field(
        default="qwen/qwen-2.5-7b-instruct:free",
        description="OpenRouter model name (free models: qwen/qwen-2.5-7b-instruct:free)",
    )

    # Database Configuration
    lookbook_db_url: str = Field(
        default="mysql+pymysql://magento:Magento@COS(*)@127.0.0.1:3306/lookbookMPC",
        description="Database URL for lookbook data (MySQL by default)",
        alias="MYSQL_APP_URL",
    )
    mysql_shop_url: Optional[str] = Field(
        default=None,
        description="MySQL connection string for Magento catalog (optional)",
    )

    # S3/CDN Configuration
    s3_base_url: str = Field(..., description="Base URL for S3 image storage")

    # Logging Configuration
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(default="json", description="Log format (json or text)")

    # Feature Flags
    feature_mcp: bool = Field(default=True, description="Enable MCP server")
    feature_redis_queue: bool = Field(
        default=False, description="Enable Redis job queue"
    )
    feature_metrics: bool = Field(default=True, description="Enable metrics endpoint")

    # Security Configuration
    api_token: Optional[str] = Field(
        default=None, description="Bearer token for protecting write/vision endpoints"
    )
    allowed_image_domains: List[str] = Field(
        default_factory=lambda: [], description="List of allowed image URL domains"
    )

    # Vision Service Configuration
    vision_sidecar_host: str = Field(
        default="http://localhost:8001", description="Vision sidecar URL"
    )
    vision_sidecar_timeout: int = Field(
        default=30, description="Vision analysis timeout in seconds"
    )
    vision_max_batch_size: int = Field(
        default=20, description="Maximum batch size for vision analysis"
    )
    vision_max_workers: int = Field(
        default=2, description="Number of vision worker threads"
    )

    # API Configuration
    api_host: str = Field(default="0.0.0.0", description="API host bind address")
    api_port: int = Field(default=8000, description="API port")
    api_workers: int = Field(default=1, description="Number of API worker processes")

    # Request Configuration
    request_timeout: int = Field(
        default=30, description="Total request timeout in seconds"
    )
    connect_timeout: int = Field(default=2, description="Connection timeout in seconds")
    read_timeout: int = Field(default=8, description="Read timeout in seconds")

    # Retry Configuration
    max_retries: int = Field(
        default=2, description="Maximum number of retries for failed requests"
    )
    retry_backoff_factor: float = Field(
        default=1.0, description="Exponential backoff factor for retries"
    )

    # Nginx Configuration
    nginx_server_name: str = Field(
        default="lookbook.internal", description="Nginx server name for co-existence"
    )
    nginx_path_prefix: str = Field(default="/lookbook", description="Nginx path prefix")

    # Rate Limiting
    rate_limit_requests: int = Field(
        default=5, description="Rate limit requests per second"
    )
    rate_limit_burst: int = Field(default=10, description="Rate limit burst size")

    # Image Processing
    max_image_size_bytes: int = Field(
        default=5 * 1024 * 1024, description="Maximum image size in bytes (5MB)"
    )

    # Feature Flags Table
    feature_flags_table: str = Field(
        default="feature_flags", description="Name of feature flags table"
    )

    @property
    def s3_base_url_with_trailing_slash(self) -> str:
        """Ensure S3 base URL ends with a slash."""
        return self.s3_base_url.rstrip("/") + "/"

    @property
    def allowed_image_domains_regex(self) -> str:
        """Generate regex pattern for allowed image domains."""
        if not self.allowed_image_domains:
            return r".*"  # Allow all if not configured
        return "|".join(re.escape(domain) for domain in self.allowed_image_domains)

    def get_database_url(self) -> str:
        """Get the database URL with proper dialect handling."""
        return self.lookbook_db_url

    def is_mysql_database(self) -> bool:
        """Check if using MySQL database."""
        return self.lookbook_db_url.startswith("mysql+pymysql://")

    def get_mysql_url(self) -> Optional[str]:
        """Get the MySQL URL if configured."""
        return self.mysql_shop_url

    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.log_level.upper() in ("WARNING", "ERROR") and self.api_workers > 1

    def is_development(self) -> bool:
        """Check if running in development mode."""
        return not self.is_production()

    def get_llm_provider_type(self) -> str:
        """Get the configured LLM provider type."""
        return self.llm_provider.lower()

    def get_llm_model_name(self) -> str:
        """Get the model name based on provider type."""
        if self.get_llm_provider_type() == "openrouter":
            return self.openrouter_model
        else:
            return self.llm_model or self.ollama_text_model

    def get_openrouter_api_key(self) -> Optional[str]:
        """Get OpenRouter API key from config or environment."""
        return (
            self.openrouter_api_key
            or os.getenv("OPENROUTER_API_KEY")
            or os.getenv("OPENROUTER_KEY")
        )

    def is_llm_provider_available(self) -> bool:
        """Check if the configured LLM provider is available."""
        if self.get_llm_provider_type() == "openrouter":
            return bool(self.get_openrouter_api_key())
        else:  # ollama
            return True  # Assume Ollama is available if configured


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get the settings instance."""
    return settings
