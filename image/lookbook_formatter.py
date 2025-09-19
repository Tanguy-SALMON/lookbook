# description_formatter.py

import logging
from typing import Dict, List
import re

class DescriptionFormatter:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.base_url = "https://d29c1z66frfv6c.cloudfront.net/pub/media/catalog/product/large/"

    def format_description(self, product_data: Dict) -> str:
        """Creates formatted product description for Shopee"""
        try:
            sections = []

            # Main description
            if product_data.get('values', {}).get('gc_metaDescription'):
                desc = product_data['values']['gc_metaDescription'][0]['data']
                sections.append(f"📝 Description:\n{desc}\n")

            # Care instructions
            if product_data.get('values', {}).get('gc_careinstruction'):
                care = product_data['values']['gc_careinstruction'][0]['data']
                formatted_care = self._format_care_instructions(care)
                sections.append(f"👕 Care Instructions:\n{formatted_care}\n")

            # Lookbook images
            if product_data.get('values', {}).get('gc_lookbookRandom'):
                lookbook_images = product_data['values']['gc_lookbookRandom'][0]['data'].split('|')
                lookbook_urls = [f"{self.base_url}{img}" for img in lookbook_images]
                sections.append(f"📸 Style Gallery:\n" + "\n".join(lookbook_urls))

            return "\n".join(sections)

        except Exception as e:
            self.logger.error(f"Error formatting description: {str(e)}")
            return ""

    def _format_care_instructions(self, care: str) -> str:
        """Format care instructions into bullet points"""
        instructions = care.split(',')
        return "\n".join(f"• {instruction.strip()}" for instruction in instructions)