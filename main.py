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

# Import API routers
from lookbook_mpc.api.routers import (
    ingest_router,
    reco_router,
    chat_router,
    images_router,
)
from lookbook_mpc.api.mcp_server import create_mcp_app

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
        structlog.processors.JSONRenderer(),
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
        "S3_BASE_URL",
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
    description="Fashion lookbook recommendation microservice with vision analysis and intent parsing",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routers
app.include_router(ingest_router)
app.include_router(reco_router)
app.include_router(chat_router)
app.include_router(images_router)

# Mount MCP endpoints
mcp_app = create_mcp_app()
app.mount("/mcp", mcp_app)


# Request ID middleware
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Add request ID to logs and response headers."""
    import uuid

    request_id = str(uuid.uuid4())
    request.state.request_id = request_id

    # Add request ID to logger context
    logger = structlog.get_logger(request_id=request_id)

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id

    return response


# Health check endpoints
@app.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {"status": "healthy", "service": "lookbook-mpc", "version": "0.1.0"}


@app.get("/ready")
async def readiness_check():
    """Readiness probe with dependency checks."""
    checks = {
        "database": "unknown",  # Will be implemented in M3
        "ollama": "unknown",  # Will be implemented in M5
        "s3": "unknown",  # Will be implemented in M4
    }

    # Basic checks
    try:
        # Check if we can connect to basic services
        import httpx

        async with httpx.AsyncClient(timeout=5.0) as client:
            # Check Ollama
            try:
                response = await client.get(
                    f"{os.getenv('OLLAMA_HOST', 'http://localhost:11434')}/api/tags"
                )
                if response.status_code == 200:
                    checks["ollama"] = "ready"
                else:
                    checks["ollama"] = "unhealthy"
            except:
                checks["ollama"] = "unreachable"

            # Check S3 base URL (basic HTTP check)
            try:
                if os.getenv("S3_BASE_URL"):
                    response = await client.get(os.getenv("S3_BASE_URL"), timeout=5.0)
                    checks["s3"] = (
                        "reachable" if response.status_code < 500 else "unhealthy"
                    )
                else:
                    checks["s3"] = "not_configured"
            except:
                checks["s3"] = "unreachable"

        # Overall readiness
        all_ready = all(
            status in ["ready", "not_configured"] for status in checks.values()
        )
        overall_status = "ready" if all_ready else "not_ready"

        return {
            "status": overall_status,
            "checks": checks,
            "timestamp": "2025-01-19T14:00:00Z",  # Will be dynamic
        }

    except Exception as e:
        logger.error("Readiness check failed", error=str(e))
        return JSONResponse(
            status_code=503,
            content={
                "status": "error",
                "message": "Readiness check failed",
                "error": str(e),
            },
        )


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": "lookbook-mpc",
        "version": "0.1.0",
        "description": "Fashion lookbook recommendation microservice",
        "docs": "/docs",
        "health": "/health",
        "ready": "/ready",
    }


# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(
        "Unhandled exception",
        request_id=getattr(request.state, "request_id", "unknown"),
        error=str(exc),
        exc_info=True,
    )

    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "Internal server error",
            "request_id": getattr(request.state, "request_id", "unknown"),
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")
