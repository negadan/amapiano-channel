#!/usr/bin/env python3
"""
Segment objects in images using fal.ai BiRefNet
Creates masks for use with audio-reactive ffmpeg effects
"""

import os
import sys
import requests
import json
from config import FAL_API_KEY

FAL_API_URL = "https://fal.run/fal-ai/birefnet"

def segment_image(image_path: str, output_mask_path: str, output_foreground_path: str = None) -> bool:
    """
    Segment an image to separate foreground from background.
    Returns mask image for use in ffmpeg effects.
    """

    if not FAL_API_KEY:
        print("ERROR: FAL_API_KEY not set in config.py")
        return False

    if not os.path.exists(image_path):
        print(f"ERROR: Image not found: {image_path}")
        return False

    # First, we need to upload the image or use a public URL
    # For local files, we'll use base64 encoding
    import base64

    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode("utf-8")

    # Determine mime type
    ext = os.path.splitext(image_path)[1].lower()
    mime_type = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp"
    }.get(ext, "image/jpeg")

    data_url = f"data:{mime_type};base64,{image_data}"

    headers = {
        "Authorization": f"Key {FAL_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "image_url": data_url,
        "model": "General Use (Heavy)",  # Best quality
        "operating_resolution": "1024x1024",
        "output_format": "png",
        "refine_foreground": True,
        "output_mask": True  # Get the mask!
    }

    print(f"Segmenting image: {image_path}")
    print("Using BiRefNet for high-quality segmentation...")

    try:
        response = requests.post(FAL_API_URL, headers=headers, json=payload, timeout=120)
        response.raise_for_status()
        result = response.json()

        # Get mask URL
        mask_url = None
        foreground_url = None

        if "mask_image" in result:
            mask_url = result["mask_image"].get("url")

        if "image" in result:
            foreground_url = result["image"].get("url")

        # Download mask
        if mask_url:
            print(f"Downloading mask...")
            mask_response = requests.get(mask_url, timeout=60)
            mask_response.raise_for_status()

            with open(output_mask_path, "wb") as f:
                f.write(mask_response.content)
            print(f"Mask saved to: {output_mask_path}")
        else:
            print("WARNING: No mask returned, creating from foreground...")
            # If no mask, we can create one from the foreground alpha channel

        # Download foreground (with transparency)
        if foreground_url and output_foreground_path:
            print(f"Downloading foreground...")
            fg_response = requests.get(foreground_url, timeout=60)
            fg_response.raise_for_status()

            with open(output_foreground_path, "wb") as f:
                f.write(fg_response.content)
            print(f"Foreground saved to: {output_foreground_path}")

        return True

    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text[:500]}")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False


def create_inverted_mask(mask_path: str, output_path: str) -> bool:
    """
    Invert a mask (swap foreground/background).
    Useful for targeting background objects like sky.
    """
    try:
        from PIL import Image, ImageOps

        mask = Image.open(mask_path).convert("L")
        inverted = ImageOps.invert(mask)
        inverted.save(output_path)
        print(f"Inverted mask saved to: {output_path}")
        return True
    except ImportError:
        print("PIL not installed. Install with: pip install Pillow")
        return False
    except Exception as e:
        print(f"Error inverting mask: {e}")
        return False


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Segment objects in images using AI")
    parser.add_argument("--image", "-i", required=True, help="Input image path")
    parser.add_argument("--mask", "-m", required=True, help="Output mask path")
    parser.add_argument("--foreground", "-f", help="Output foreground path (optional)")
    parser.add_argument("--invert", action="store_true", help="Also create inverted mask")

    args = parser.parse_args()

    success = segment_image(args.image, args.mask, args.foreground)

    if success and args.invert:
        base, ext = os.path.splitext(args.mask)
        inverted_path = f"{base}_inverted{ext}"
        create_inverted_mask(args.mask, inverted_path)

    sys.exit(0 if success else 1)
