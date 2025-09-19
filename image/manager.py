# Standard library
import base64
import logging
from PIL import Image
import io
import requests
from image_classifier.classifier import Classifier


class ImageManager:
    def __init__(self, api_client):
        self.api = api_client
        self.classifier = Classifier()
        self.logger = logging.getLogger(__name__)
        self.base_url = "https://d29c1z66frfv6c.cloudfront.net/pub/media/catalog/product/large/"

    def map_images_by_suffix(images):
        """Map images to their appropriate types based on suffixes"""
        mapped = {
            'gc_swatchImage': [],
            'gc_thumbnail': [],
            'gc_smallImage': [],
            'aa_mediaLink': []
        }

        for img in images:
            if '_sw' in img:
                mapped['gc_swatchImage'].append(img)
            elif '_th' in img:
                mapped['gc_thumbnail'].append(img)
            elif '_sm' in img:
                mapped['gc_smallImage'].append(img)
            else:
                mapped['aa_mediaLink'].append(img)

        return mapped

        try:
            # Get all images from aa_mediaLink
            all_images = []
            if prod["values"].get("aa_mediaLink"):
                all_images = prod["values"]["aa_mediaLink"][0]['data']

            # Map images to their types
            mapped_images = map_images_by_suffix(all_images)

            # Update product values with mapped images
            if mapped_images['gc_swatchImage']:
                prod["values"]["gc_swatchImage"] = [{'data': mapped_images['gc_swatchImage'][0]}]

            if mapped_images['gc_thumbnail']:
                prod["values"]["gc_thumbnail"] = [{'data': mapped_images['gc_thumbnail'][0]}]

            if mapped_images['gc_smallImage']:
                prod["values"]["gc_smallImage"] = [{'data': mapped_images['gc_smallImage'][0]}]

            # Prepare final image list
            image_urls = []

            # Add images in priority order
            for field in ['gc_swatchImage', 'gc_thumbnail', 'gc_smallImage', 'aa_mediaLink']:
                if prod["values"].get(field):
                    if field == 'aa_mediaLink':
                        # Use remaining images
                        images = mapped_images[field]
                    else:
                        images = [prod["values"][field][0]['data']]

                    for img in images:
                        clean_url = f"{img.split('_')[0]}_xxl-1.jpg"
                        if clean_url not in image_urls:  # Avoid duplicates
                            image_urls.append(clean_url)

            # Upload images
            return [self.api.upload_image(url) for url in image_urls[:9]]  # Shopee limit

        except Exception as e:
            logger.error(f"Error processing images: {str(e)}")
            return []

    def process_product_images(self, prod):
        """Upload images with intelligent suffix mapping"""

        def map_images_by_suffix(images):
            """Map images to their appropriate types based on suffixes"""
            mapped = {
                'gc_swatchImage': [],
                'gc_thumbnail': [],
                'gc_smallImage': [],
                'aa_mediaLink': []
            }

            for img in images:
                if '_sw' in img:
                    mapped['gc_swatchImage'].append(img)
                elif '_th' in img:
                    mapped['gc_thumbnail'].append(img)
                elif '_sm' in img:
                    mapped['gc_smallImage'].append(img)
                else:
                    mapped['aa_mediaLink'].append(img)

            return mapped

        try:
            # Get all images from aa_mediaLink
            all_images = []
            if prod["values"].get("aa_mediaLink"):
                all_images = prod["values"]["aa_mediaLink"][0]['data']

            # Map images to their types
            mapped_images = map_images_by_suffix(all_images)

            # Update product values with mapped images
            if mapped_images['gc_swatchImage']:
                prod["values"]["gc_swatchImage"] = [{'data': mapped_images['gc_swatchImage'][0]}]

            if mapped_images['gc_thumbnail']:
                prod["values"]["gc_thumbnail"] = [{'data': mapped_images['gc_thumbnail'][0]}]

            if mapped_images['gc_smallImage']:
                prod["values"]["gc_smallImage"] = [{'data': mapped_images['gc_smallImage'][0]}]

            # Prepare final image list
            image_urls = []

            # Add images in priority order
            for field in ['gc_swatchImage', 'gc_thumbnail', 'gc_smallImage', 'aa_mediaLink']:
                if prod["values"].get(field):
                    if field == 'aa_mediaLink':
                        # Use remaining images
                        images = mapped_images[field]
                    else:
                        images = [prod["values"][field][0]['data']]

                    for img in images:
                        clean_url = f"{img.split('_')[0]}_xxl-1.jpg"
                        if clean_url not in image_urls:  # Avoid duplicates
                            image_urls.append(clean_url)

            # Upload images
            # return [self.api.upload_image(url) for url in image_urls[:9]]  # Shopee limit
            return [self.base_url + url for url in image_urls[:9]]  # Shopee limit
            

        except Exception as e:
            logger.error(f"Error processing images: {str(e)}")
            return []





