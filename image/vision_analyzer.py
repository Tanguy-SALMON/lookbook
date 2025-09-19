# Standard library
import base64
import logging
import io
import os
from typing import Dict, Optional, Union, List

# Third-party libraries
from PIL import Image
from langchain_ollama import OllamaLLM

class VisionAnalyzer:
    """
    Analyzes product images using Ollama vision models to extract product attributes,
    descriptions, and colors.
    """

    def __init__(self, model: str = "llama3.2-vision", save_processed: bool = True):
        """
        Initialize the VisionAnalyzer with specified model and settings.

        Args:
            model: Name of the Ollama vision model to use
            save_processed: Whether to save processed images (original, cropped, resized)
        """
        self.model = model
        self.save_processed = save_processed
        self.logger = logging.getLogger(__name__)

        # Initialize LLM
        self.llm = OllamaLLM(
            model=self.model,
            temperature=0,           # More deterministic for image analysis
            num_ctx=1024,            # Reduced context for faster processing
            timeout=40,              # Fail fast if too slow
            repeat_penalty=1.1,      # Slight penalty
            top_p=0.8,               # More focused
            num_predict=256,         # Number of tokens to predict
            seed=42                  # For reproducibility
        )

        self.logger.debug(f"VisionAnalyzer initialized with model: {self.model}")

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
                original_save_path = source_path.rsplit('.', 1)[0] + '_original.jpg'
                img.save(original_save_path)
                self.logger.debug(f"Saved original image to: {original_save_path}")

            # Convert to RGBA if not already
            if img.mode != 'RGBA':
                img = img.convert('RGBA')

            # Get image data
            img_data = img.getdata()
            width, height = img.size

            # Find white/transparent bands
            def is_white_or_transparent(pixel):
                return pixel[3] == 0 or (pixel[0] > 250 and pixel[1] > 250 and pixel[2] > 250)

            # Find left boundary
            left = 0
            for x in range(width):
                if any(not is_white_or_transparent(img_data[y * width + x]) for y in range(height)):
                    left = x
                    break

            # Find right boundary
            right = width - 1
            for x in range(width - 1, -1, -1):
                if any(not is_white_or_transparent(img_data[y * width + x]) for y in range(height)):
                    right = x
                    break

            # Crop if white bands found
            if left > 0 or right < width - 1:
                img = img.crop((left, 0, right + 1, height))
                self.logger.debug(f"Cropped white bands. New size: {img.size}")

                # Save cropped image before resize
                if self.save_processed and isinstance(image_source, str):
                    cropped_save_path = source_path.rsplit('.', 1)[0] + '_cropped.jpg'
                    img.convert('RGB').save(cropped_save_path)
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
                    resized_save_path = source_path.rsplit('.', 1)[0] + '_resized.jpg'
                    img.convert('RGB').save(resized_save_path)
                    self.logger.debug(f"Saved resized image to: {resized_save_path}")

            # Convert back to RGB for JPEG
            img = img.convert('RGB')

            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=85)
            encoded = base64.b64encode(buffer.getvalue()).decode('utf-8')
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
            if isinstance(image_source, str) and (image_source.startswith('http://') or
                                                 image_source.startswith('https://')):
                base64_image = self.encode_from_url(image_source)
            else:
                base64_image = self.encode_image(image_source)

            self.logger.debug("Image successfully encoded to base64")

            prompt = f"""
            <image>{base64_image}</image>

            Look at this product image and provide:
            IMPORTANT - What to analyze:
            - If the image shows a full-body model: focus on the BOTTOM garment only
            - If the image is cropped/upper body: focus on the TOP garment only
            - If single product shot: analyze that item

            1. Main Color:
            - Identify the primary color using standard fashion color terminology. Be specific about shade and tone (e.g., dusty pink, sage green, etc.)
            - Primary color with specific tone (one or two words maximum)
            - Use standard fashion color naming: pink, light pink, dusty pink, blush pink, etc.
            - Do not limit color options to: black, white, navy, brown, grey, beige
            - Consider using standard color references like Pantone naming

            2. Product Description:
            - Style: Professional but friendly
            - Length: 80-120 words
            - Include: features, materials, fit details, styling suggestions
            - Format: Short paragraphs
            - Tone: Premium but accessible (COS brand voice)

            3. Attributes (provide only the values that match exactly with the options):
            - Plus Size (Yes/No)
            - Material (select from: Cotton, Fleece, Nylon, Velvet, Leather, Chiffon, Denim, etc.)
            - Pattern (select from: Plain, Floral, Striped, Print, Checkered / Plaid, etc.)
            - Style (select from: Athletic, Basic, Boho, Korean, Minimalist, etc.)
            - Neckline (if applicable, select from: V Neck, Crew Neck, Collar, etc.)
            - Season (select from: Summer, Winter, Spring, Autumn)
            - Occasion (select from: Casual, Wedding, Business)

            Format your response exactly like this:
            COLOR: [single color word]

            DESCRIPTION:
            [your description here]

            ATTRIBUTES:
            Plus Size: [Yes/No]
            Material: [material name]
            Pattern: [pattern name]
            Style: [style name]
            Neckline: [neckline type]
            Season: [season name]
            Occasion: [occasion name]
            """

            self.logger.debug("Sending prompt to model")
            response = self.llm.invoke(prompt)
            self.logger.debug("Received response from model")

            # Parse the response
            result = self._parse_analysis_response(response)
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
            if isinstance(image_source, str) and (image_source.startswith('http://') or
                                                 image_source.startswith('https://')):
                base64_image = self.encode_from_url(image_source)
            else:
                base64_image = self.encode_image(image_source)

            prompt = f"""
            <image>{base64_image}</image>

            What is the main color of the garment in this image?
            Please be specific and use standard fashion color terminology with shade and tone.
            Respond with ONLY the color name (1-2 words maximum).
            """

            response = self.llm.invoke(prompt)
            return response.strip()

        except Exception as e:
            self.logger.error(f"Error in analyze_color: {str(e)}")
            return "Unknown"

    def _parse_analysis_response(self, response: str) -> Dict:
        """
        Parse the structured response from the LLM.

        Args:
            response: Raw text response from LLM

        Returns:
            Dictionary with parsed information
        """
        result = {
            "color": "",
            "description": "",
            "attributes": {}
        }

        try:
            # Extract color
            color_match = re.search(r"COLOR:\s*(.+?)(?:\n\n|\n|$)", response)
            if color_match:
                result["color"] = color_match.group(1).strip()

            # Extract description
            desc_match = re.search(r"DESCRIPTION:\s*(.+?)(?=\n\nATTRIBUTES:)", response, re.DOTALL)
            if desc_match:
                result["description"] = desc_match.group(1).strip()

            # Extract attributes
            attr_section = re.search(r"ATTRIBUTES:\s*(.+?)$", response, re.DOTALL)
            if attr_section:
                attr_text = attr_section.group(1)
                attr_pairs = re.findall(r"([^:\n]+):\s*([^\n]+)", attr_text)

                for key, value in attr_pairs:
                    result["attributes"][key.strip()] = value.strip()

            return result

        except Exception as e:
            self.logger.error(f"Error parsing analysis response: {str(e)}")
            return result

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


# For direct testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    try:
        analyzer = VisionAnalyzer()
        image_path = "/Users/tanguysalmon/PythonPlayGround/Langchain/Loose-Fit-T-shirt.jpg"
        logger.info("Starting analysis")
        result = analyzer.analyze_product(image_path)
        print(f"Analysis result: {result}")
        logger.info("Analysis completed")
    except Exception as e:
        logger.error(f"Main execution error: {str(e)}")