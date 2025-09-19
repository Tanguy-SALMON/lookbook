class DescriptionBuilder:
    def __init__(self, shopee_client):
        self.client = shopee_client

    def format_description(self, product_data):
        # Upload lookbook images first
        lookbook_urls = []
        for image in product_data['lookbook_images']:
            response = self.client.upload_image(
                image_path=image['path'],
                is_description=True  # Important flag for description images
            )
            lookbook_urls.append(response['image_url'])

        # Build HTML description
        description = f"""
        <p>{product_data['description']}</p>

        <h4>COMPOSITION</h4>
        <p>{product_data['composition']}</p>

        <h4>CARE INSTRUCTIONS</h4>
        <p>{product_data['care_instructions']}</p>

        <h4>LOOKBOOK</h4>
        {''.join([f'<img src="{url}" alt="Lookbook image"/>' for url in lookbook_urls])}
        """

        return description.strip()