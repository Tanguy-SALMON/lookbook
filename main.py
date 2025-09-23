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
    agents_router,
    personas_router,
    settings_router,
    products_router,
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

    missing_vars = [
        var
        for var in required_vars
        if not getattr(settings, var.lower().replace("_", ""), None)
    ]
    if missing_vars:
        logger.warning("Missing required environment variables", missing=missing_vars)

    # Log configuration
    logger.info(
        "Configuration loaded",
        llm_service_api=os.getenv("LLM_SERVICE_API", f"{settings.llm_provider.upper()} ({settings.get_llm_model_name()})"),
        llm_provider=settings.llm_provider.upper(),
        llm_model=settings.get_llm_model_name(),
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
app.include_router(agents_router)
app.include_router(personas_router)
app.include_router(settings_router)
app.include_router(products_router)

# Mount MCP endpoints (if enabled)
if settings.feature_mcp:
    mcp_app = create_mcp_app()
    app.mount("/mcp", mcp_app)


# Serve demo HTML file
@app.get("/demo")
async def demo_page():
    """Serve the demo chat interface."""
    return FileResponse("docs/demo.html")


# Serve test chat frontend
@app.get("/test")
async def test_chat_page():
    """Serve the test chat frontend page."""
    return FileResponse("docs/test_chat_frontend.html")


# Serve docs index page
@app.get("/docs-index")
async def docs_index_page():
    """Serve the documentation index page."""
    return FileResponse("docs/index.html")


# Serve static files if they exist
static_dir = "static"
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Serve assets directory for images
assets_dir = "assets"
if os.path.exists(assets_dir):
    app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")


# Health check endpoints
@app.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "service": "lookbook-mpc",
        "version": "0.1.0",
        "environment": settings.log_level,
        "timestamp": datetime.utcnow().isoformat() + "Z",
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
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
        ) as client:
            # Check Ollama
            try:
                response = await client.get(
                    f"{settings.ollama_host}/api/tags", timeout=settings.connect_timeout
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
                        test_image_url, timeout=settings.connect_timeout
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
            },
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
async def root(request: Request):
    """Root endpoint with service information and navigation links."""
    from fastapi.responses import HTMLResponse

    # Check if client wants JSON (for tests)
    accept_header = request.headers.get("accept", "")
    if "application/json" in accept_header:
        return {
            "service": "lookbook-mpc",
            "version": "0.1.0",
            "description": "Fashion Lookbook Recommendation Microservice",
            "docs": "/docs",
            "health": "/health",
            "ready": True,
            "endpoints": {
                "demo": "/demo",
                "test": "/test",
                "api": "/v1/",
                "chat": "/v1/chat",
                "recommendations": "/v1/recommendations",
            },
        }

    html_content = (
        """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Lookbook-MPC - Fashion Recommendation Service</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-50 min-h-screen">
        <div class="container mx-auto px-4 py-8 max-w-4xl">
            <div class="text-center mb-8">
                <h1 class="text-4xl font-bold text-gray-900 mb-4">Lookbook-MPC</h1>
                <p class="text-lg text-gray-600 mb-2">Fashion Lookbook Recommendation Microservice</p>
                <p class="text-sm text-gray-500">Version 0.1.0 • Environment: """
        + settings.log_level
        + """</p>
            </div>

            <!-- Navigation Links -->
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
                <!-- Chat Interfaces -->
                <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                    <h2 class="text-xl font-semibold text-gray-900 mb-4 flex items-center">
                        💬 Chat Interfaces
                    </h2>
                    <div class="space-y-3">
                        <a href="/demo" class="block px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors text-center">
                            Demo Chat Interface
                        </a>
                        <a href="/test" class="block px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors text-center">
                            Test Chat Frontend
                        </a>
                    </div>
                    <p class="text-xs text-gray-500 mt-3">
                        Interactive chat interfaces with AI fashion recommendations
                    </p>
                </div>

                <!-- API Documentation -->
                <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                    <h2 class="text-xl font-semibold text-gray-900 mb-4 flex items-center">
                        📚 API Documentation
                    </h2>
                    <div class="space-y-3">
                        <a href="/docs-index" class="block px-4 py-2 bg-orange-500 text-white rounded-lg hover:bg-orange-600 transition-colors text-center">
                            Documentation Hub
                        </a>
                        <a href="/docs" class="block px-4 py-2 bg-purple-500 text-white rounded-lg hover:bg-purple-600 transition-colors text-center">
                            Swagger UI (OpenAPI)
                        </a>
                        <a href="/redoc" class="block px-4 py-2 bg-indigo-500 text-white rounded-lg hover:bg-indigo-600 transition-colors text-center">
                            ReDoc Documentation
                        </a>
                    </div>
                    <p class="text-xs text-gray-500 mt-3">
                        Complete API documentation and interactive testing
                    </p>
                </div>

                <!-- System Status -->
                <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                    <h2 class="text-xl font-semibold text-gray-900 mb-4 flex items-center">
                        🔍 System Status
                    </h2>
                    <div class="space-y-3">
                        <a href="/health" class="block px-4 py-2 bg-emerald-500 text-white rounded-lg hover:bg-emerald-600 transition-colors text-center">
                            Health Check
                        </a>
                        <a href="/ready" class="block px-4 py-2 bg-yellow-500 text-white rounded-lg hover:bg-yellow-600 transition-colors text-center">
                            Readiness Probe
                        </a>
                    </div>
                    <p class="text-xs text-gray-500 mt-3">
                        System health and dependency status
                    </p>
                </div>
            </div>

            <!-- API Endpoints -->
            <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
                <h2 class="text-xl font-semibold text-gray-900 mb-4">🔌 API Endpoints</h2>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                    <div>
                        <h3 class="font-medium text-gray-700 mb-2">Chat API</h3>
                        <ul class="space-y-1 text-gray-600">
                            <li><code class="bg-gray-100 px-2 py-1 rounded">POST /v1/chat</code> - Chat with AI</li>
                            <li><code class="bg-gray-100 px-2 py-1 rounded">GET /v1/chat/suggestions</code> - Get chat suggestions</li>
                            <li><code class="bg-gray-100 px-2 py-1 rounded">GET /v1/chat/sessions</code> - List chat sessions</li>
                        </ul>
                    </div>
                    <div>
                        <h3 class="font-medium text-gray-700 mb-2">Recommendations</h3>
                        <ul class="space-y-1 text-gray-600">
                            <li><code class="bg-gray-100 px-2 py-1 rounded">POST /v1/recommend</code> - Get recommendations</li>
                            <li><code class="bg-gray-100 px-2 py-1 rounded">GET /v1/images/{key}</code> - Get product images</li>
                        </ul>
                    </div>
                </div>
            </div>

            <!-- Features Status -->
            <div class="bg-gray-100 rounded-lg p-6">
                <h2 class="text-lg font-semibold text-gray-800 mb-4">Features Status</h2>
                <div class="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                    <div class="flex items-center justify-between">
                        <span>MCP Integration</span>
                        <span class="px-2 py-1 rounded text-xs """
        + (
            "bg-green-100 text-green-800"
            if settings.feature_mcp
            else "bg-gray-100 text-gray-600"
        )
        + """">
                            """
        + ("Enabled" if settings.feature_mcp else "Disabled")
        + """
                        </span>
                    </div>
                    <div class="flex items-center justify-between">
                        <span>Redis Queue</span>
                        <span class="px-2 py-1 rounded text-xs """
        + (
            "bg-green-100 text-green-800"
            if settings.feature_redis_queue
            else "bg-gray-100 text-gray-600"
        )
        + """">
                            """
        + ("Enabled" if settings.feature_redis_queue else "Disabled")
        + """
                        </span>
                    </div>
                    <div class="flex items-center justify-between">
                        <span>Metrics</span>
                        <span class="px-2 py-1 rounded text-xs """
        + (
            "bg-green-100 text-green-800"
            if settings.feature_metrics
            else "bg-gray-100 text-gray-600"
        )
        + """">
                            """
        + ("Enabled" if settings.feature_metrics else "Disabled")
        + """
                        </span>
                    </div>
                </div>
            </div>

            <!-- Footer -->
            <div class="text-center mt-8 text-sm text-gray-500">
                <p>Lookbook-MPC Fashion Recommendation Service</p>
                <p>AI-powered outfit recommendations for COS Thailand</p>
            </div>
        </div>

        <script>
            // Add real-time status checking
            async function checkStatus() {
                try {
                    const response = await fetch('/health');
                    const data = await response.json();
                    console.log('Service status:', data.status);
                } catch (error) {
                    console.log('Service status check failed:', error);
                }
            }

            // Check status on load
            checkStatus();
        </script>
    </body>
    </html>
    """
    )

    return HTMLResponse(content=html_content)


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
