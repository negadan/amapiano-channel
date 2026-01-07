#!/usr/bin/env python3
"""
Generate visuals for Amapiano videos using fal.ai
"""

import os
import sys
import requests
import json
import time
from config import FAL_API_KEY, VISUAL_STYLES

# Use fal.ai REST API
FAL_API_URL = "https://fal.run/fal-ai/flux/schnell"

def generate_image(prompt: str, output_path: str, width: int = 1920, height: int = 1080) -> bool:
    """Generate an image using fal.ai FLUX"""

    if not FAL_API_KEY:
        print("ERROR: FAL_API_KEY not set in config.py")
        return False

    headers = {
        "Authorization": f"Key {FAL_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "prompt": prompt,
        "image_size": "landscape_16_9",
        "num_images": 1,
        "enable_safety_checker": False
    }

    print(f"Generating image...")
    print(f"Prompt: {prompt[:100]}...")

    try:
        # Submit request (synchronous endpoint)
        response = requests.post(FAL_API_URL, headers=headers, json=payload, timeout=120)

        if response.status_code == 401 or response.status_code == 403:
            print(f"Auth error. Trying alternative endpoint...")
            # Try alternative endpoint
            alt_url = "https://fal.run/fal-ai/fast-sdxl"
            response = requests.post(alt_url, headers=headers, json=payload, timeout=120)

        response.raise_for_status()
        result = response.json()

        print(f"Response: {json.dumps(result, indent=2)[:500]}")

        # Get image URL from response
        image_url = None
        if "images" in result and len(result["images"]) > 0:
            image_url = result["images"][0].get("url")
        elif "image" in result:
            image_url = result["image"].get("url")
        elif "output" in result:
            image_url = result["output"]

        if image_url:
            # Download image
            print(f"Downloading image from: {image_url[:80]}...")
            img_response = requests.get(image_url, timeout=60)
            img_response.raise_for_status()

            with open(output_path, "wb") as f:
                f.write(img_response.content)

            print(f"Image saved to: {output_path}")
            return True
        else:
            print(f"No image URL in response")
            return False

    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text[:500]}")
        return False
    except Exception as e:
        print(f"Error generating image: {e}")
        return False


def generate_for_track(track_name: str, style: str = "nostalgic") -> str:
    """Generate a visual for a specific track"""

    # Get style prompt
    prompt = VISUAL_STYLES.get(style, VISUAL_STYLES["nostalgic"])

    # Output path
    output_dir = os.path.join(os.path.dirname(__file__), "assets")
    os.makedirs(output_dir, exist_ok=True)

    safe_name = track_name.replace(" ", "_").lower()
    output_path = os.path.join(output_dir, f"{safe_name}_{style}.png")

    if generate_image(prompt, output_path):
        return output_path
    return None


if __name__ == "__main__":
    # Test generation
    if len(sys.argv) > 1:
        style = sys.argv[1]
    else:
        style = "nostalgic"

    result = generate_for_track("remember_when", style)
    if result:
        print(f"Success! Image at: {result}")
    else:
        print("Failed to generate image")
