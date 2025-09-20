"""
Lookbook-MPC - Fashion Lookbook Recommendation Microservice

FastAPI-based service for fashion recommendations using vision analysis
and intent parsing with Ollama LLMs.
"""

import os
import time
import contextvars
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import structlog
import uuid
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import new modules
from lookbook_mpc.config import settings

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

# Context variable for request ID
request_id_ctx = contextvars.ContextVar("request_id", default=None)


class RequestIDMiddleware:
    """Simple middleware to add request IDs to responses."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Generate request ID
        request_id = str(uuid.uuid4())
        request_id_ctx.set(request_id)

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                # Add request ID to response headers
                headers = dict(message.get("headers", []))
                headers[b"x-request-id"] = request_id.encode("utf-8")
                message["headers"] = list(headers.items())
            await send(message)

        await self.app(scope, receive, send_wrapper)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    # Startup
    logger.info(
        "Starting Lookbook-MPC application",
        version="0.1.0",
        environment=settings.log_level,
        workers=settings.api_workers,
    )

    # Check environment
    required_vars = [
        "OLLAMA_HOST",
        "OLLAMA_VISION_MODEL",
        "OLLAMA_TEXT_MODEL",
        "S3_BASE_URL",
    ]

    missing_vars = [var for var in required_vars if not getattr(settings, var.lower().replace('_', ''), None)]
    if missing_vars:
        logger.warning("Missing required environment variables", missing=missing_vars)

    # Log configuration
    logger.info("Configuration loaded",
        ollama_host=settings.ollama_host,
        vision_model=settings.ollama_vision_model,
        text_model=settings.ollama_text_model,
        db_url=settings.lookbook_db_url,
        log_level=settings.log_level,
        feature_mcp=settings.feature_mcp,
    )

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

# Add middleware
app.add_middleware(RequestIDMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routers
app.include_router(ingest_router)
app.include_router(reco_router)
app.include_router(chat_router)
app.include_router(images_router)

# Mount MCP endpoints (if enabled)
if settings.feature_mcp:
    mcp_app = create_mcp_app()
    app.mount("/mcp", mcp_app)

# Serve demo HTML file
@app.get("/demo")
async def demo_page():
    """Serve the demo chat interface."""
    return FileResponse("docs/demo.html")

# Serve static files if they exist
static_dir = "static"
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")




# Health check endpoints
@app.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "service": "lookbook-mpc",
        "version": "0.1.0",
        "environment": settings.log_level,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


@app.get("/ready")
async def readiness_check():
    """Readiness probe with dependency checks."""
    checks = {
        "database": "not_configured",
        "ollama": "unknown",
        "s3": "unknown",
    }

    request_id = request_id_ctx.get()

    try:
        import httpx

        async with httpx.AsyncClient(
            timeout=settings.connect_timeout,
            limits=httpx.Limits(
                max_connections=10,
                max_keepalive_connections=5
            )
        ) as client:
            # Check Ollama
            try:
                response = await client.get(
                    f"{settings.ollama_host}/api/tags",
                    timeout=settings.connect_timeout
                )
                if response.status_code == 200:
                    checks["ollama"] = "ready"
                else:
                    checks["ollama"] = "unhealthy"
            except Exception as e:
                logger.warning(
                    "ollama_unreachable",
                    request_id=request_id,
                    error=str(e),
                )
                checks["ollama"] = "unreachable"

            # Check S3 base URL with a test image
            try:
                if settings.s3_base_url:
                    # Test with a known image URL that should be accessible
                    test_image_url = f"{settings.s3_base_url}3a4db8e6cba0f753558e37db7eae09614adbbf28_xxl-1.jpg"
                    response = await client.head(
                        test_image_url,
                        timeout=settings.connect_timeout
                    )
                    checks["s3"] = (
                        "reachable" if response.status_code < 500 else "unhealthy"
                    )
                else:
                    checks["s3"] = "not_configured"
            except Exception as e:
                logger.warning(
                    "s3_unreachable",
                    request_id=request_id,
                    error=str(e),
                )
                checks["s3"] = "unreachable"

        # Overall readiness
        all_ready = all(
            status in ["ready", "not_configured"] for status in checks.values()
        )
        overall_status = "ready" if all_ready else "not_ready"
        status_code = 200 if all_ready else 503

        return JSONResponse(
            status_code=status_code,
            content={
                "status": overall_status,
                "checks": checks,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "request_id": request_id,
            }
        )

    except Exception as e:
        logger.error(
            "readiness_check_failed",
            request_id=request_id,
            error=str(e),
        )
        return JSONResponse(
            status_code=503,
            content={
                "status": "error",
                "message": "Readiness check failed",
                "error": str(e),
                "request_id": request_id,
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
        "demo": "/demo",
        "features": {
            "mcp": settings.feature_mcp,
            "redis_queue": settings.feature_redis_queue,
            "metrics": settings.feature_metrics,
        },
        "environment": settings.log_level,
    }


# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    request_id = getattr(request.state, "request_id", "unknown")

    logger.error(
        "Unhandled exception",
        request_id=request_id,
        error=str(exc),
        exc_info=True,
    )

    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "Internal server error",
            "request_id": request_id,
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        workers=settings.api_workers,
        reload=settings.is_development(),
        log_level=settings.log_level,
        timeout_keep_alive=30,
    )
