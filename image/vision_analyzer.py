# Standard library
import base64
import json
import logging
import io
import os
import re
from typing import Dict, Optional, Union, List

# Third-party libraries
from PIL import Image
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


class VisionAnalyzer:
    """
    Analyzes product images using Ollama vision models to extract product attributes,
    descriptions, and colors.
    """

    def __init__(self, model: str = "qwen2.5-vl:7b", save_processed: bool = True):
        """
        Initialize the VisionAnalyzer with specified model and settings.

        Args:
            model: Name of the Ollama vision model to use
            save_processed: Whether to save processed images (original, cropped, resized)
        """
        self.model = model
        self.save_processed = save_processed
        self.logger = logging.getLogger(__name__)
        self.ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")

        self.logger.debug(f"VisionAnalyzer initialized with model: {self.model}")

    def _call_ollama(self, prompt: str, image_data: str = None) -> str:
        """
        Call Ollama API with optional image data.

        Args:
            prompt: Text prompt for the model
            image_data: Base64 encoded image data (optional)

        Returns:
            Model response text
        """
        try:
            url = f"{self.ollama_host}/api/generate"
            payload = {
                "model": self.model,
                "prompt": prompt,
                "temperature": 0,
                "max_tokens": 256,
                "stream": False,
            }

            if image_data:
                payload["images"] = [image_data]

            response = requests.post(url, json=payload, timeout=60)
            response.raise_for_status()

            return response.json().get("response", "")

        except Exception as e:
            self.logger.error(f"Error calling Ollama API: {str(e)}")
            raise

    def encode_image(self, image_source: Union[str, bytes]) -> str:
        """
        Process and encode an image to base64 for LLM analysis.

        Args:
            image_source: Either a file path or image bytes

        Returns:
            Base64 encoded image string
        """
        try:
            # Handle different input types
            if isinstance(image_source, str):
                # It's a file path
                img = Image.open(image_source)
                source_path = image_source
            else:
                # It's bytes
                img = Image.open(io.BytesIO(image_source))
                source_path = "memory_image"

            self.logger.debug(f"Original image size: {img.size}, mode: {img.mode}")

            # Save original image if needed
            if self.save_processed and isinstance(image_source, str):
                original_save_path = source_path.rsplit(".", 1)[0] + "_original.jpg"
                img.save(original_save_path)
                self.logger.debug(f"Saved original image to: {original_save_path}")

            # Convert to RGBA if not already
            if img.mode != "RGBA":
                img = img.convert("RGBA")

            # Get image data
            img_data = img.getdata()
            width, height = img.size

            # Find white/transparent bands
            def is_white_or_transparent(pixel):
                return pixel[3] == 0 or (
                    pixel[0] > 250 and pixel[1] > 250 and pixel[2] > 250
                )

            # Find left boundary
            left = 0
            for x in range(width):
                if any(
                    not is_white_or_transparent(img_data[y * width + x])
                    for y in range(height)
                ):
                    left = x
                    break

            # Find right boundary
            right = width - 1
            for x in range(width - 1, -1, -1):
                if any(
                    not is_white_or_transparent(img_data[y * width + x])
                    for y in range(height)
                ):
                    right = x
                    break

            # Crop if white bands found
            if left > 0 or right < width - 1:
                img = img.crop((left, 0, right + 1, height))
                self.logger.debug(f"Cropped white bands. New size: {img.size}")

                # Save cropped image before resize
                if self.save_processed and isinstance(image_source, str):
                    cropped_save_path = source_path.rsplit(".", 1)[0] + "_cropped.jpg"
                    img.convert("RGB").save(cropped_save_path)
                    self.logger.debug(f"Saved cropped image to: {cropped_save_path}")

            # Resize if needed
            max_size = 200
            if max(img.size) > max_size:
                ratio = max_size / max(img.size)
                new_size = tuple([int(x * ratio) for x in img.size])
                img = img.resize(new_size, Image.Resampling.LANCZOS)
                self.logger.debug(f"Resized to: {new_size}")

                # Save resized image
                if self.save_processed and isinstance(image_source, str):
                    resized_save_path = source_path.rsplit(".", 1)[0] + "_resized.jpg"
                    img.convert("RGB").save(resized_save_path)
                    self.logger.debug(f"Saved resized image to: {resized_save_path}")

            # Convert back to RGB for JPEG
            img = img.convert("RGB")

            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=85)
            encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")
            return encoded

        except Exception as e:
            self.logger.error(f"Image processing error: {str(e)}")
            raise

    def encode_from_url(self, url: str) -> str:
        """
        Download and encode an image from a URL.

        Args:
            url: URL of the image

        Returns:
            Base64 encoded image string
        """
        import requests

        try:
            response = requests.get(url)
            response.raise_for_status()
            return self.encode_image(response.content)
        except Exception as e:
            self.logger.error(f"Error downloading image from {url}: {str(e)}")
            raise

    def analyze_product(self, image_source: Union[str, bytes]) -> Dict:
        """
        Analyze a product image to extract color, description, and attributes.

        Args:
            image_source: Either a file path, URL, or image bytes

        Returns:
            Dictionary with extracted product information
        """
        try:
            self.logger.debug("Starting product analysis")

            # Handle URL input
            if isinstance(image_source, str) and (
                image_source.startswith("http://")
                or image_source.startswith("https://")
            ):
                base64_image = self.encode_from_url(image_source)
            else:
                base64_image = self.encode_image(image_source)

            self.logger.debug("Image successfully encoded to base64")

            prompt = """You are an expert fashion vision tagger. Analyze this product image and return ONLY valid JSON with no additional text.

Required JSON format:
{"color":"", "category":"", "material":"", "pattern":"", "style":"", "season":"", "occasion":"", "fit":"", "plus_size":true/false, "description":""}

STRICT RULES - Use only these exact values:

Color: Use specific fashion colors like "black", "white", "navy", "grey", "beige", "red", "blue", "green", "yellow", "pink", "brown", "burgundy", "olive", "cream", "charcoal", "denim-blue", "forest-green"

Category: MUST be one of: "top", "bottom", "dress", "outerwear", "shoes", "accessory", "underwear", "swimwear"

Material: MUST be one of: "cotton", "polyester", "nylon", "wool", "silk", "linen", "denim", "leather", "velvet", "chiffon", "fleece"

Pattern: MUST be one of: "plain", "striped", "floral", "print", "checked", "plaid", "polka_dot", "animal_print", "geometric"

Season: MUST be one of: "spring", "summer", "autumn", "winter"

Occasion: MUST be one of: "casual", "business", "formal", "party", "wedding", "sport", "beach", "sleep"

Fit: MUST be one of: "slim", "regular", "relaxed", "loose", "tight", "baggy"

Plus_size: MUST be true or false (boolean)

Description: 2-3 sentences describing the garment, fabric, and style

Examples:
- T-shirt: {"color":"white","category":"top","material":"cotton","pattern":"plain","style":"casual","season":"summer","occasion":"casual","fit":"regular","plus_size":false,"description":"Classic white cotton t-shirt with short sleeves and crew neck. Soft comfortable fabric perfect for everyday wear."}
- Jeans: {"color":"denim-blue","category":"bottom","material":"denim","pattern":"plain","style":"casual","season":"autumn","occasion":"casual","fit":"slim","plus_size":false,"description":"Slim-fit blue jeans with classic five-pocket styling. Durable denim construction with modern tapered leg."}

Return ONLY the JSON object, no other text."""

            self.logger.debug("Sending prompt to model")
            response = self._call_ollama(prompt, base64_image)
            self.logger.debug("Received response from model")

            # Parse the JSON response
            result = self._parse_json_response(response)
            return result

        except Exception as e:
            self.logger.error(f"Error in analyze_product: {str(e)}")
            raise

    def analyze_color(self, image_source: Union[str, bytes]) -> str:
        """
        Extract only the color from a product image.

        Args:
            image_source: Either a file path, URL, or image bytes

        Returns:
            Color name as string
        """
        try:
            # Handle URL input
            if isinstance(image_source, str) and (
                image_source.startswith("http://")
                or image_source.startswith("https://")
            ):
                base64_image = self.encode_from_url(image_source)
            else:
                base64_image = self.encode_image(image_source)

            prompt = """What is the main color of the garment in this image?
Use standard fashion color terminology.
Respond with ONLY the color name (1-2 words maximum).
Examples: black, white, navy, denim-blue, forest-green, burgundy"""

            response = self._call_ollama(prompt, base64_image)
            return response.strip()

        except Exception as e:
            self.logger.error(f"Error in analyze_color: {str(e)}")
            return "Unknown"

    def _parse_json_response(self, response: str) -> Dict:
        """
        Parse the JSON response from the LLM.

        Args:
            response: Raw text response from LLM

        Returns:
            Dictionary with parsed information
        """
        try:
            # Clean the response - remove any markdown formatting
            cleaned_response = response.strip()
            if cleaned_response.startswith("```json"):
                cleaned_response = (
                    cleaned_response.replace("```json", "").replace("```", "").strip()
                )

            # Extract JSON from response (may have surrounding text)
            json_match = re.search(r"\{.*\}", cleaned_response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                result = json.loads(json_str)

                # Validate and ensure all required fields exist with proper types
                required_fields = {
                    "color": str,
                    "category": str,
                    "material": str,
                    "pattern": str,
                    "style": str,
                    "season": str,
                    "occasion": str,
                    "fit": str,
                    "plus_size": bool,
                    "description": str,
                }

                for field, expected_type in required_fields.items():
                    if field not in result:
                        if expected_type == bool:
                            result[field] = False
                        else:
                            result[field] = "unknown"
                    else:
                        # Type conversion if needed
                        if expected_type == bool and not isinstance(
                            result[field], bool
                        ):
                            result[field] = str(result[field]).lower() in [
                                "true",
                                "1",
                                "yes",
                            ]
                        elif expected_type == str and result[field] is None:
                            result[field] = "unknown"

                return result
            else:
                raise ValueError("No JSON found in response")

        except Exception as e:
            self.logger.error(f"Error parsing JSON response: {str(e)}")
            # Return fallback response that matches expected schema
            return {
                "color": "black",
                "category": "accessory",
                "material": "polyester",
                "pattern": "plain",
                "style": "modern",
                "season": "autumn",
                "occasion": "casual",
                "fit": "regular",
                "plus_size": False,
                "description": "Unable to analyze image due to processing error.",
            }

    def batch_analyze(self, image_sources: List[Union[str, bytes]]) -> List[Dict]:
        """
        Analyze multiple product images in batch.

        Args:
            image_sources: List of image sources (paths, URLs, or bytes)

        Returns:
            List of analysis results
        """
        results = []
        for source in image_sources:
            try:
                result = self.analyze_product(source)
                results.append(result)
            except Exception as e:
                self.logger.error(f"Error analyzing image {source}: {str(e)}")
                results.append({"error": str(e)})

        return results


# FastAPI HTTP service wrapper
class AnalyzeRequest(BaseModel):
    """Request model for vision analysis."""

    image_key: str
    image_url: Optional[str] = None
    image_bytes: Optional[str] = None  # Base64 encoded


class AnalyzeResponse(BaseModel):
    """Response model for vision analysis."""

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


# Create FastAPI app for vision sidecar
app = FastAPI(
    title="Lookbook Vision Analyzer",
    description="Vision analysis sidecar for fashion product images",
    version="1.0.0",
)

# Global analyzer instance
analyzer = None


@app.on_event("startup")
async def startup_event():
    """Initialize the vision analyzer on startup."""
    global analyzer
    model = os.getenv("OLLAMA_VISION_MODEL", "qwen2.5-vl:7b")
    analyzer = VisionAnalyzer(model=model, save_processed=False)
    logging.basicConfig(level=logging.INFO)


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_image(request: AnalyzeRequest):
    """
    Analyze a product image and return fashion attributes.

    Args:
        request: Analysis request with image data

    Returns:
        Vision analysis results
    """
    try:
        if not analyzer:
            raise HTTPException(
                status_code=500, detail="Vision analyzer not initialized"
            )

        # Determine image source
        image_source = None
        if request.image_url:
            image_source = request.image_url
        elif request.image_bytes:
            # Decode base64 image bytes
            image_data = base64.b64decode(request.image_bytes)
            image_source = image_data
        else:
            # For now, use a placeholder - in production this would fetch from S3
            # using the image_key and S3_BASE_URL
            s3_base_url = os.getenv("S3_BASE_URL", "")
            if s3_base_url:
                image_source = f"{s3_base_url}/{request.image_key}"
            else:
                raise HTTPException(
                    status_code=400,
                    detail="No image source provided (url, bytes, or S3 configuration)",
                )

        # Analyze the image
        result = analyzer.analyze_product(image_source)

        return AnalyzeResponse(**result)

    except Exception as e:
        logging.error(f"Analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "vision-analyzer",
        "model": analyzer.model if analyzer else "not_initialized",
    }


@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": "lookbook-vision-analyzer",
        "version": "1.0.0",
        "description": "Fashion product image analysis using Ollama vision models",
        "endpoints": {
            "analyze": "POST /analyze - Analyze product images",
            "health": "GET /health - Health check",
        },
    }


# For direct testing
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "serve":
        # Run as HTTP service
        import uvicorn

        uvicorn.run(
            "vision_analyzer:app",
            host="0.0.0.0",
            port=int(os.getenv("VISION_PORT", "8001")),
            reload=True,
            log_level="info",
        )
    else:
        # Run direct testing
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)

        try:
            analyzer = VisionAnalyzer()
            image_path = (
                "/Users/tanguysalmon/PythonPlayGround/Langchain/Loose-Fit-T-shirt.jpg"
            )
            logger.info("Starting analysis")
            result = analyzer.analyze_product(image_path)
            print(f"Analysis result: {result}")
            logger.info("Analysis completed")
        except Exception as e:
            logger.error(f"Main execution error: {str(e)}")
