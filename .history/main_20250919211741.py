
"""
Lookbook-MPC - Fashion Lookbook Recommendation Microservice

FastAPI-based service for fashion recommendations using vision analysis
and intent parsing with Ollama LLMs.
"""

import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    # Startup
    logger.info("Starting Lookbook-MPC application", version="0.1.0")

    # Check environment
    required_vars = [
        "OLLAMA_HOST",
        "OLLAMA_VISION_MODEL",
        "OLLAMA_TEXT_MODEL",
        "S3_BASE_URL"
    ]

    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        logger.warning("Missing required environment variables", missing=missing_vars)

    yield

    # Shutdown
    logger.info("Shutting down Lookbook-MPC application")

# Create FastAPI app
app = FastAPI(
    title="Lookbook-MPC",
