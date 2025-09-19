
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
            content_type = _get_content_type(format, image_key)

            # Create streaming response with CORS headers
            streaming_response = StreamingResponse(
                BytesIO(image_data),
                media_type=content_type,
                headers={
                    "Cache-Control": "public, max-age=3600",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "GET, OPTIONS",
                    "Access-Control-Allow-Headers": "Content-Type",
                    "X-Image-Key": image_key,
                    "X-Original-URL": image_url
                }
            )

            return streaming_response

    except httpx.HTTPError as e:
        logger.error("Error fetching image from source", image_key=image_key, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to fetch image from source: {str(e)}"
        )
    except Exception as e:
        logger.error("Error serving image", image_key=image_key, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to serve image: {str(e)}"
        )


@router.get("/{image_key}/redirect")
async def redirect_image(image_key: str) -> RedirectResponse:
    """
    Redirect to the original image URL.

    This endpoint provides a 302 redirect to the original image
    URL, useful for embedding in external applications.

    Args:
        image_key: S3 image key or filename

    Returns:
        RedirectResponse to the original image URL
    """
    try:
        logger.info("Redirecting to image", image_key=image_key)

        # Get the full image URL
        image_url = image_locator.get_image_url(image_key)

        return RedirectResponse(
            url=image_url,
            status_code=status.HTTP_302_FOUND,
            headers={
                "Cache-Control": "public, max-age=3600",
                "Access-Control-Allow-Origin": "*"
            }
        )

    except Exception as e:
        logger.error("Error redirecting to image", image_key=image_key, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to redirect to image: {str(e)}"
        )


@router.head("/{image_key}")
async def head_image(image_key: str) -> Dict[str, Any]:
    """
    Check if an image exists without downloading it.

    Args:
        image_key: S3 image key or filename

    Returns:
        Headers with image information

    Raises:
        HTTPException: If image is not found
    """
    try:
        logger.info("Checking image existence", image_key=image_key)

        # Get the full image URL
        image_url = image_locator.get_image_url(image_key)

        # Check if image exists with HEAD request
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.head(image_url)

            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Image {image_key} not found"
                )

            # Return useful headers
            return {
                "exists": True,
                "content_length": response.headers.get("content-length"),
                "content_type": response.headers.get("content-type"),
                "last_modified": response.headers.get("last-modified"),
                "cache_control": response.headers.get("cache-control")
            }

    except httpx.HTTPError as e:
        logger.error("Error checking image existence", image_key=image_key, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Image {image_key} not found"
        )
    except Exception as e:
        logger.error("Error checking image", image_key=image_key, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check image: {str(e)}"
        )


@router.options("/{image_key}")
async def options_image() -> Dict[str, Any]:
    """
    Handle CORS preflight requests for images.

    Returns:
        CORS headers for preflight requests
    """
    return {
        "status": "ok",
        "allowed_methods": ["GET", "HEAD", "OPTIONS"],
        "allowed_headers": ["Content-Type"],
        "allowed_origins": ["*"]
    }


@router.get("/info/{image_key}")
async def get_image_info(image_key: str) -> Dict[str, Any]:
    """
    Get information about an image.

    Args:
        image_key: S3 image key or filename

    Returns:
        Image information including metadata
    """
    try:
        logger.info("Getting image info", image_key=image_key)

        # Get the full image URL
        image_url = image_locator.get_image_url(image_key)

        # Fetch image to get metadata
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.head(image_url)

            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Image {image_key} not found"
                )

            # Extract image information
            image_info = {
                "image_key": image_key,
                "url": image_url,
                "content_type": response.headers.get("content-type"),
                "content_length": int(response.headers.get("content-length", 0)),
                "last_modified": response.headers.get("last-modified"),
                "cache_control": response.headers.get("cache-control"),
                "available": True
            }

            return image_info

    except httpx.HTTPError as e:
        logger.error("Error getting image info", image_key=image_key, error=str(e))
        return {
            "image_key": image_key,
