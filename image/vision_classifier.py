# Standard library
from langchain_ollama import OllamaLLM
import base64
import logging
from PIL import Image
import io
import requests

class Classifier:
    def __init__(self):
        self.llm = OllamaLLM(
            model="llama3.2-vision",
            temperature=0,
            num_ctx=1024,
            timeout=40,
            repeat_penalty=1.1,
            top_p=0.8,
            num_predict=256,
            seed=42
        )
        self.logger = logging.getLogger(__name__)

    def classify_product_images(self, image_urls: list) -> dict:
        """
        Classify product images into categories:
        - model_shots: Images with models
        - product_shots: Full product without model
        - detail_shots: Close-up details
        - other_shots: Miscellaneous shots
        """
        classifications = {
            'model_shots': [],
            'product_shots': [],
            'detail_shots': [],
            'other_shots': []
        }

        for url in image_urls:
            try:
                base64_image = self._encode_image(url)
                category = self._analyze_single_image(base64_image)
                classifications[f'{category}_shots'].append(url)
            except Exception as e:
                self.logger.error(f"Error processing {url}: {str(e)}")
                classifications['other_shots'].append(url)

        return classifications

    def _encode_image(self, url: str) -> str:
        """Download and encode image to base64"""
        response = requests.get(url)
        response.raise_for_status()
        return base64.b64encode(response.content).decode('utf-8')

    def _analyze_single_image(self, base64_image: str) -> str:
        prompt = f"""
        <image>{base64_image}</image>

        Classify this product image into ONE of these categories:
        - model (if shows person wearing product)
        - product (if shows full product without model)
        - detail (if shows close-up/detail shot)
        - other (if none of above)

        Reply with ONLY ONE word: model, product, detail, or other
        """

        try:
            response = self.llm.invoke(prompt)
            category = response.strip().lower()
            return category if category in ['model', 'product', 'detail'] else 'other'
        except Exception as e:
            self.logger.error(f"Analysis error: {str(e)}")
            return 'other'