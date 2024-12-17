"""Script to publish blog post to Medium.

This script takes a markdown file and publishes it to Medium using their API.
It handles image uploads and markdown conversion.
"""

import os
import sys
import json
import base64
import requests
import markdown
from pathlib import Path
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
import argparse
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MediumPublisher:
    """Handles publishing content to Medium."""
    
    def __init__(self, integration_token: str):
        """Initialize with Medium integration token.
        
        Args:
            integration_token: Medium API integration token
        """
        self.token = integration_token
        self.api_url = "https://api.medium.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
    def get_user_id(self) -> str:
        """Get Medium user ID for the integration token.
        
        Returns:
            Medium user ID
            
        Raises:
            requests.exceptions.RequestException: If API request fails
        """
        response = requests.get(
            f"{self.api_url}/me",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()["data"]["id"]
        
    def upload_image(self, image_path: str) -> str:
        """Upload an image to Medium.
        
        Args:
            image_path: Path to image file
            
        Returns:
            URL of uploaded image
            
        Raises:
            FileNotFoundError: If image file doesn't exist
            requests.exceptions.RequestException: If upload fails
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")
            
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode()
            
        response = requests.post(
            f"{self.api_url}/images",
            headers=self.headers,
            json={"image": image_data}
        )
        response.raise_for_status()
        return response.json()["data"]["url"]
        
    def process_images(self, content: str, base_path: str) -> str:
        """Process and upload images in content.
        
        Args:
            content: Markdown content with image references
            base_path: Base path for resolving relative image paths
            
        Returns:
            Content with image references replaced with Medium URLs
        """
        soup = BeautifulSoup(markdown.markdown(content), "html.parser")
        
        for img in soup.find_all("img"):
            src = img["src"]
            if not src.startswith(("http://", "https://")):
                # Handle relative path
                img_path = os.path.join(base_path, src)
                try:
                    medium_url = self.upload_image(img_path)
                    img["src"] = medium_url
                except Exception as e:
                    logger.error(f"Failed to upload image {img_path}: {e}")
                    
        return str(soup)
        
    def publish_post(
        self,
        title: str,
        content: str,
        tags: List[str],
        publish_status: str = "draft"
    ) -> str:
        """Publish a post to Medium.
        
        Args:
            title: Post title
            content: Post content (HTML)
            tags: List of tags
            publish_status: Publication status ("draft", "public", "unlisted")
            
        Returns:
            URL of published post
            
        Raises:
            requests.exceptions.RequestException: If publishing fails
        """
        user_id = self.get_user_id()
        
        post_data = {
            "title": title,
            "contentFormat": "html",
            "content": content,
            "tags": tags,
            "publishStatus": publish_status
        }
        
        response = requests.post(
            f"{self.api_url}/users/{user_id}/posts",
            headers=self.headers,
            json=post_data
        )
        response.raise_for_status()
        return response.json()["data"]["url"]

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Publish markdown post to Medium")
    parser.add_argument("markdown_file", help="Path to markdown file")
    parser.add_argument("--token", help="Medium integration token", required=True)
    parser.add_argument("--tags", help="Comma-separated list of tags", default="")
    parser.add_argument(
        "--status",
        help="Publication status",
        choices=["draft", "public", "unlisted"],
        default="draft"
    )
    
    args = parser.parse_args()
    
    try:
        # Read markdown file
        with open(args.markdown_file, "r") as f:
            content = f.read()
            
        # Extract title from first line
        title = content.split("\n")[0].lstrip("# ")
        
        # Initialize publisher
        publisher = MediumPublisher(args.token)
        
        # Process images
        base_path = os.path.dirname(os.path.abspath(args.markdown_file))
        processed_content = publisher.process_images(content, base_path)
        
        # Parse tags
        tags = [tag.strip() for tag in args.tags.split(",") if tag.strip()]
        
        # Publish post
        post_url = publisher.publish_post(
            title=title,
            content=processed_content,
            tags=tags,
            publish_status=args.status
        )
        
        logger.info(f"Successfully published to Medium: {post_url}")
        
    except Exception as e:
        logger.error(f"Failed to publish post: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 