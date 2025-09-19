
"""
Images API Router

This module handles endpoints for image proxying and serving
with CORS control for embedding in external applications.
"""

from fastapi import APIRouter, HTTPException, status, Request
from fastapi.responses import RedirectResponse, StreamingResponse
from typing import Dict, Any, Optional
import logging
import structlog
import httpx
from io import BytesIO

from ...adapters.images import S3ImageLocator, MockImageLocator

router = APIRouter(prefix="/v1/images", tags=["images"])
logger = structlog.get_logger()


# Initialize image locator (will be replaced with proper DI in later milestones)
image_locator = MockImageLocator("https://mock-cdn.example.com")


@router.get("/{image_key}")
async def get_image(
    image_key: str,
    request: Request,
    width: Optional[int] = None,
    height: Optional[int] = None,
    quality: Optional[int] = None,
    format: Optional[str] = None
) -> StreamingResponse:
    """
    Get an image with optional resizing and format conversion.

    This endpoint serves images with CORS headers and optional
    transformations like resizing and format conversion.

    Args:
        image_key: S3 image key or filename
        request: FastAPI request object for headers
        width: Optional width for resizing
        height: Optional height for resizing
        quality: Optional quality (1-100) for JPEG/WebP
        format: Optional format conversion (jpeg, webp, png)

    Returns:
        StreamingResponse with the image

    Raises:
        HTTPException: If image is not found or processing fails
    """
    try:
        logger.info("Serving image",
                   image_key=image_key,
                   width=width,
                   height=height,
                   quality=quality,
                   format=format)

        # Get the full image URL
        image_url = image_locator.get_image_url(image_key)

        # Fetch the image
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(image_url)

            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Image {image_key} not found"
                )

            image_data = response.content

            # Apply transformations if requested
            if width or height or format or quality:
                image_data = await _transform_image(
                    image_data, width, height, quality, format
                )

            # Determine content type
