"""
Vision Sidecar Service

FastAPI service that wraps VisionAnalyzer as an HTTP endpoint.
This runs as a separate service that can be scaled independently.
"""

import os
import logging
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional
import uvicorn
import structlog

from image.vision_analyzer import VisionAnalyzer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = structlog.get_logger()

app = FastAPI(
    title="Vision Sidecar",
    description="Vision analysis service for fashion product images",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Initialize vision analyzer
vision_analyzer = VisionAnalyzer(
    model=os.getenv("OLLAMA_VISION_MODEL", "qwen2.5vl"),
    save_processed=False,  # Don't save processed images in sidecar
)


class ImageAnalysisRequest(BaseModel):
    """Request model for image analysis."""

    image_url: Optional[str] = None
    image_bytes: Optional[str] = None  # Base64 encoded
    image_key: Optional[str] = None


class ImageAnalysisResponse(BaseModel):
    """Response model for image analysis."""

    color: str
    category: str
    material: str
    pattern: str
    style: str
    season: str
    occasion: str
    fit: str
    plus_size: bool
    description: str
    request_id: Optional[str] = None


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "vision_sidecar"}


@app.post("/analyze", response_model=ImageAnalysisResponse)
async def analyze_image(request: ImageAnalysisRequest):
    """
    Analyze a product image and extract attributes.

    Args:
        request: Image analysis request with image URL, bytes, or key

    Returns:
        Image analysis response with extracted attributes
    """
    try:
        logger.info("Starting image analysis", request=request)

        # Determine image source
        image_source = None
        if request.image_url:
            image_source = request.image_url
        elif request.image_bytes:
            import base64

            image_source = base64.b64decode(request.image_bytes)
        elif request.image_key:
            # In a real implementation, this would fetch from S3
            # For now, we'll use a placeholder URL
            image_source = f"https://example.com/images/{request.image_key}"
        else:
            raise HTTPException(status_code=400, detail="No image source provided")

        # Analyze the image
        result = vision_analyzer.analyze_product(image_source)

        # Map to response model
        response = ImageAnalysisResponse(
            color=result.get("color", "unknown"),
            category=result.get("category", "unknown"),
            material=result.get("material", "unknown"),
            pattern=result.get("pattern", "unknown"),
            style=result.get("style", "unknown"),
            season=result.get("season", "unknown"),
            occasion=result.get("occasion", "unknown"),
            fit=result.get("fit", "unknown"),
            plus_size=result.get("plus_size", False),
            description=result.get("description", "No description available"),
        )

        logger.info("Image analysis completed", result=result)
        return response

    except Exception as e:
        logger.error("Error analyzing image", error=str(e))
        raise HTTPException(status_code=500, detail=f"Image analysis failed: {str(e)}")


@app.post("/batch-analyze")
async def batch_analyze_images(requests: list[ImageAnalysisRequest]):
    """
    Analyze multiple images in batch.

    Args:
        requests: List of image analysis requests

    Returns:
        List of image analysis responses
    """
    try:
        logger.info("Starting batch image analysis", count=len(requests))

        results = []
        for i, req in enumerate(requests):
            try:
                # Process each request
                image_source = None
                if req.image_url:
                    image_source = req.image_url
                elif req.image_bytes:
                    import base64

                    image_source = base64.b64decode(req.image_bytes)
                elif req.image_key:
                    image_source = f"https://example.com/images/{req.image_key}"
                else:
                    results.append({"error": "No image source provided", "index": i})
                    continue

                # Analyze the image
                result = vision_analyzer.analyze_product(image_source)
                results.append(result)

            except Exception as e:
                logger.error(f"Error analyzing image {i}", error=str(e))
                results.append({"error": str(e), "index": i})

        logger.info("Batch image analysis completed", processed=len(results))
        return results

    except Exception as e:
        logger.error("Error in batch analysis", error=str(e))
        raise HTTPException(status_code=500, detail=f"Batch analysis failed: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(
        "vision_sidecar:app", host="0.0.0.0", port=8001, reload=True, log_level="info"
    )
