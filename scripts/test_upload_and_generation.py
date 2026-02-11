"""
Test script for image upload and subsequent media generation.
Tests the complete workflow: upload → video generation → similar image generation
"""

import argparse
import io
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional

import requests
from PIL import Image


DEFAULT_BASE_URL = "http://localhost:8000"
DEFAULT_TIMEOUT = 120


def create_test_image(width: int = 512, height: int = 512) -> bytes:
    """Create a simple test image (gradient)."""
    img = Image.new('RGB', (width, height))
    pixels = img.load()
    
    for y in range(height):
        for x in range(width):
            # Create a gradient from blue to orange
            r = int((x / width) * 255)
            g = int((y / height) * 128)
            b = int(255 - (x / width) * 255)
            pixels[x, y] = (r, g, b)
    
    # Save to bytes
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG', quality=85)
    return buffer.getvalue()


def print_section(title: str) -> None:
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def test_upload(base_url: str, timeout: int) -> Optional[str]:
    """Upload a test image and return media_id."""
    print_section("Image Upload Test")
    
    # Create test image
    print("Creating test image...")
    image_data = create_test_image()
    print(f"Test image created: {len(image_data)} bytes")
    
    # Upload
    print(f"Uploading to {base_url}/upload...")
    files = {'file': ('test_image.jpg', image_data, 'image/jpeg')}
    
    try:
        resp = requests.post(f"{base_url}/upload", files=files, timeout=timeout)
        print(f"POST /upload -> {resp.status_code}")
        
        if not resp.ok:
            print(f"Upload failed: {resp.text[:500]}")
            return None
        
        data = resp.json()
        print(json.dumps(data, indent=2)[:1000])
        
        media_id = data.get('media_id')
        if media_id:
            print(f"\n✅ Upload successful! media_id: {media_id}")
            return media_id
        else:
            print("❌ No media_id in response")
            return None
            
    except Exception as exc:
        print(f"Upload failed with exception: {exc}")
        return None


def test_video_with_image(base_url: str, media_id: str, timeout: int, poll_wait: int = 10, poll_attempts: int = 12) -> None:
    """Generate video from uploaded image."""
    print_section("Video Generation from Uploaded Image")
    
    payload = {
        "prompt": "animate this image with smooth motion",
        "media_ids": [media_id],
        "attachment_metadata": {
            "file_size": 50000,  # approximate
            "mime_type": "image/jpeg"
        }
    }
    
    print(f"Submitting video job with media_id: {media_id}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        resp = requests.post(f"{base_url}/video/async", json=payload, timeout=timeout)
        print(f"POST /video/async -> {resp.status_code}")
        
        if not resp.ok:
            print(f"Error: {resp.text[:500]}")
            return
        
        data = resp.json()
        job_id = data.get("job_id")
        print(f"Job ID: {job_id}")
        
        if not job_id:
            print("No job_id in response")
            return
        
        # Poll for completion
        for attempt in range(1, poll_attempts + 1):
            time.sleep(poll_wait)
            status_resp = requests.get(f"{base_url}/video/jobs/{job_id}", timeout=timeout)
            status_data = status_resp.json()
            
            status = status_data.get("status")
            print(f"Attempt {attempt}/{poll_attempts}: {status}")
            
            if status == "succeeded":
                result = status_data.get("result", {})
                video_urls = result.get("video_urls", [])
                print(f"\n✅ Video generation succeeded! {len(video_urls)} videos generated")
                for idx, url in enumerate(video_urls[:2], 1):  # Show first 2
                    print(f"  {idx}. {url[:120]}...")
                return
            elif status == "failed":
                error = status_data.get("error", "Unknown error")
                print(f"\n❌ Video generation failed: {error}")
                return
        
        print(f"\n⏱️ Video generation timed out after {poll_attempts} attempts")
        
    except Exception as exc:
        print(f"Video generation failed with exception: {exc}")


def test_image_from_image(base_url: str, media_id: str, timeout: int) -> None:
    """Generate similar images from uploaded image."""
    print_section("Similar Image Generation from Uploaded Image")
    
    payload = {
        "prompt": "create similar images in different styles",
        "media_ids": [media_id],
        "attachment_metadata": {
            "file_size": 50000,
            "mime_type": "image/jpeg"
        },
        "orientation": "SQUARE"
    }
    
    print(f"Generating similar images with media_id: {media_id}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        resp = requests.post(f"{base_url}/image", json=payload, timeout=timeout)
        print(f"POST /image -> {resp.status_code}")
        
        if not resp.ok:
            print(f"Error: {resp.text[:500]}")
            return
        
        data = resp.json()
        image_urls = data.get("image_urls", [])
        
        if image_urls:
            print(f"\n✅ Similar image generation succeeded! {len(image_urls)} images generated")
            for idx, url in enumerate(image_urls[:2], 1):  # Show first 2
                print(f"  {idx}. {url[:120]}...")
        else:
            print("\n❌ No image URLs in response")
            print(json.dumps(data, indent=2)[:1000])
        
    except Exception as exc:
        print(f"Image generation failed with exception: {exc}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Test image upload and media generation workflow")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="Base URL of running uvicorn server")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help="Request timeout in seconds")
    parser.add_argument("--poll-wait", type=int, default=10, help="Seconds between video job polls")
    parser.add_argument("--poll-attempts", type=int, default=12, help="Number of video status polls")
    parser.add_argument("--skip-video", action="store_true", help="Skip video generation test")
    parser.add_argument("--skip-image", action="store_true", help="Skip similar image generation test")
    args = parser.parse_args()
    
    # Test health
    print_section("Health Check")
    try:
        resp = requests.get(f"{args.base_url}/healthz", timeout=args.timeout)
        print(f"GET /healthz -> {resp.status_code} {resp.text}")
        if not resp.ok:
            print("⚠️ Health check failed, but continuing...")
    except Exception as exc:
        print(f"❌ Health check failed: {exc}")
        sys.exit(1)
    
    # Upload image
    media_id = test_upload(args.base_url, args.timeout)
    
    if not media_id:
        print("\n❌ Upload failed - cannot proceed with generation tests")
        sys.exit(1)
    
    # Test video generation with uploaded image
    if not args.skip_video:
        test_video_with_image(args.base_url, media_id, args.timeout, args.poll_wait, args.poll_attempts)
    
    # Test similar image generation
    if not args.skip_image:
        test_image_from_image(args.base_url, media_id, args.timeout)
    
    print("\n" + "=" * 80)
    print("Test suite completed!")
    print("=" * 80)


if __name__ == "__main__":
    main()
