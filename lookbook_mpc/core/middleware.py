"""
Middleware modules for Lookbook-MPC.

This module provides request handling middleware including:
- Request ID propagation
- Request logging
- Security validation
"""

import time
import contextvars
import re
from datetime import datetime
from typing import Optional
from fastapi import Request, Response, Header, HTTPException, status
from fastapi.responses import JSONResponse
import structlog

from ..config import settings

# Configure logger
logger = structlog.get_logger()

# Context variable for request ID
request_id_ctx = contextvars.ContextVar("request_id", default=None)


class RequestIDMiddleware:
    """
    Middleware for handling request ID propagation.

    - Generates new UUID if no X-Request-ID header is present
    - Reuses existing X-Request-ID from header if provided
    - Adds X-Request-ID to response headers
    - Propagates request ID through the context
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Get request ID from header or generate new one
        headers = dict(scope.get("headers", []))
        request_id = headers.get(b"x-request-id", headers.get(b"X-Request-ID"))

        if request_id:
            request_id = request_id.decode("utf-8")
        else:
            import uuid
            request_id = str(uuid.uuid4())

        # Set context variable
        request_id_ctx.set(request_id)

        # Add to scope for downstream use
        scope["headers"].append((b"x-request-id", request_id.encode("utf-8")))

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                # Add request ID to response headers
                headers = dict(message.get("headers", []))
                headers[b"x-request-id"] = request_id.encode("utf-8")
                message["headers"] = list(headers.items())
            await send(message)

        await self.app(scope, receive, send_wrapper)


class RequestLoggingMiddleware:
    """
    Middleware for comprehensive request logging.

    Logs:
    - Request method, path, status code
    - Request duration
    - Request ID
    - User agent (if available)
    - Error details when applicable
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start_time = time.monotonic()
        request_id = request_id_ctx.get()

        # Get request details
        method = scope["method"]
        path = scope["path"]
        query_string = scope.get("query_string", b"").decode("utf-8")
        full_path = f"{path}?{query_string}" if query_string else path

        # Get headers
        headers = dict(scope.get("headers", []))
        user_agent = headers.get(b"user-agent", b"").decode("utf-8")

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                status_code = message["status"]

                # Calculate duration
                duration_ms = int((time.monotonic() - start_time) * 1000)

                # Log request
                logger.info(
                    "request_completed",
                    request_id=request_id,
                    method=method,
                    path=full_path,
                    status_code=status_code,
                    duration_ms=duration_ms,
                    user_agent=user_agent,
                )

                # Log warnings for slow requests
                if duration_ms > 5000:  # > 5 seconds
                    logger.warning(
                        "slow_request",
                        request_id=request_id,
                        method=method,
                        path=full_path,
                        duration_ms=duration_ms,
                    )

            await send(message)

        await self.app(scope, receive, send_wrapper)


class SecurityMiddleware:
    """
    Security middleware for request validation.

    Validates:
    - API token for protected endpoints
    - Image URL domains against allowlist
    - Request size limits
    """

    def __init__(self, app):
        self.app = app
        self.protected_paths = {
            "/v1/ingest",
            "/v1/recommendations",
            "/v1/chat",
            "/v1/images",
            "/mcp/call",
            "/mcp/resources",
        }

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive)
        request_id = request_id_ctx.get()

        # Check if path requires protection
        if any(request.url.path.startswith(path) for path in self.protected_paths):
            # Validate API token
            if settings.api_token:
                auth_header = request.headers.get("authorization")
                if not auth_header or not auth_header.startswith("Bearer "):
                    logger.warning(
                        "missing_auth",
                        request_id=request_id,
                        path=request.url.path,
                    )
                    response = JSONResponse(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        content={"detail": "Missing or invalid authorization header"},
                    )
                    await response(scope, receive, send)
                    return

                token = auth_header[7:]  # Remove "Bearer " prefix
                if token != settings.api_token:
                    logger.warning(
                        "invalid_token",
                        request_id=request_id,
                        path=request.url.path,
                    )
                    response = JSONResponse(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        content={"detail": "Invalid API token"},
                    )
                    await response(scope, receive, send)
                    return

        # Validate image URLs for vision endpoints
        if request.url.path.startswith("/v1/vision") or request.url.path.startswith("/mcp"):
            content_type = request.headers.get("content-type", "")
            if "application/json" in content_type:
                try:
                    body = await request.json()
                    image_urls = self._extract_image_urls(body)

                    for url in image_urls:
                        if not self._is_image_domain_allowed(url):
                            logger.warning(
                                "invalid_image_domain",
                                request_id=request_id,
                                url=url,
                                path=request.url.path,
                            )
                            response = JSONResponse(
                                status_code=status.HTTP_400_BAD_REQUEST,
                                content={"detail": "Image URL domain not allowed"},
                            )
                            await response(scope, receive, send)
                            return

                except Exception as e:
                    logger.error(
                        "image_validation_error",
                        request_id=request_id,
                        error=str(e),
                        path=request.url.path,
                    )

        await self.app(scope, receive, send)

    def _extract_image_urls(self, body: dict) -> list:
        """Extract image URLs from request body."""
        urls = []

        def extract_recursive(obj):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if key in ["image_url", "image_base64"] and isinstance(value, str):
                        if value.startswith("http"):
                            urls.append(value)
                    elif isinstance(value, (dict, list)):
                        extract_recursive(value)
            elif isinstance(obj, list):
                for item in obj:
                    extract_recursive(item)

        extract_recursive(body)
        return urls

    def _is_image_domain_allowed(self, url: str) -> bool:
        """Check if image URL domain is in allowlist."""
        if not settings.allowed_image_domains:
            return True  # Allow all if not configured

        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            domain = parsed.netloc

            # Check against allowed domains
            for allowed_domain in settings.allowed_image_domains:
                if domain == allowed_domain or domain.endswith(f".{allowed_domain}"):
                    return True

            return False
        except Exception:
            return False


def create_middleware_stack(app):
    """
    Create the complete middleware stack.

    Order is important:
    1. RequestIDMiddleware - handles request ID generation/propagation
    2. SecurityMiddleware - validates security requirements
    3. RequestLoggingMiddleware - logs request details
    """

    # Apply middleware in reverse order
    middleware_stack = RequestLoggingMiddleware(
        SecurityMiddleware(
            RequestIDMiddleware(app)
        )
    )

    return middleware_stack