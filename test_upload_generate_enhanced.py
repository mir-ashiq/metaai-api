#!/usr/bin/env python3
"""Enhanced test for upload and image generation with detailed output."""

import requests
import json
from pathlib import Path
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

# API base URL
BASE_URL = "http://localhost:8000"

# Colors for output
GREEN = "\033[92m"
RED = "\033[91m"
BLUE = "\033[94m"
YELLOW = "\033[93m"
RESET = "\033[0m"

def create_test_image():
    """Create a simple colorful test image with text."""
    img = Image.new('RGB', (200, 200), color='skyblue')
    draw = ImageDraw.Draw(img)
    
    # Draw some shapes
    draw.rectangle([20, 20, 180, 180], outline='red', width=3)
    draw.ellipse([60, 60, 140, 140], fill='yellow', outline='blue', width=2)
    
    # Add text
    try:
        draw.text((100, 100), "TEST", fill='black', anchor='mm')
    except:
        pass
    
    img_bytes = BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    return img_bytes, "test_colorful.png"

def test_upload_image():
    """Test uploading an image."""
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}Step 1: Testing Image Upload{RESET}")
    print(f"{BLUE}{'='*70}{RESET}\n")
    
    try:
        # Create test image
        img_bytes, filename = create_test_image()
        
        # Upload the image
        print(f"{YELLOW}Uploading {filename} to Meta AI...{RESET}")
        files = {'file': (filename, img_bytes, 'image/png')}
        response = requests.post(f"{BASE_URL}/upload", files=files, timeout=70)
        
        print(f"  └─ Status Code: {response.status_code}")
        
        # Check response
        if response.status_code == 200:
            result = response.json()
            
            # Extract media ID
            if isinstance(result, dict) and result.get('success') and 'media_id' in result:
                media_id = result['media_id']
                print(f"\n{GREEN}✅ SUCCESS: Image uploaded!{RESET}")
                print(f"  ├─ Media ID: {GREEN}{media_id}{RESET}")
                print(f"  ├─ Upload Session: {result.get('upload_session_id', 'N/A')}")
                print(f"  ├─ File Size: {result.get('file_size', 'N/A')} bytes")
                print(f"  └─ MIME Type: {result.get('mime_type', 'N/A')}")
                return media_id
            else:
                print(f"\n{RED}❌ FAILED: Upload unsuccessful or missing media_id{RESET}")
                print(f"  └─ Response: {json.dumps(result, indent=4)}")
                return None
        else:
            print(f"\n{RED}❌ FAILED: Upload failed with status {response.status_code}{RESET}")
            print(f"  └─ Response: {response.text[:300]}")
            return None
    
    except Exception as e:
        print(f"\n{RED}❌ ERROR: {str(e)}{RESET}")
        return None

def test_generate_with_uploaded_image(media_id):
    """Test generating image with uploaded image."""
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}Step 2: Testing Image Generation with Uploaded Media{RESET}")
    print(f"{BLUE}{'='*70}{RESET}\n")
    
    if not media_id:
        print(f"{RED}❌ SKIPPED: No media_id from upload{RESET}")
        return False
    
    try:
        # Create generation request with uploaded image
        prompt = "Transform this image into an artistic masterpiece with vibrant colors"
        payload = {
            "prompt": prompt,
            "media_ids": [media_id]
        }
        
        print(f"{YELLOW}Generating new image based on uploaded media...{RESET}")
        print(f"  ├─ Prompt: {prompt}")
        print(f"  └─ Media ID: {media_id}")
        print(f"\n{YELLOW}Waiting for Meta AI to generate images...{RESET}")
        
        response = requests.post(
            f"{BASE_URL}/image",
            json=payload,
            timeout=150
        )
        
        print(f"  └─ Status Code: {response.status_code}")
        
        # Check response
        if response.status_code == 200:
            result = response.json()
            
            if isinstance(result, dict):
                print(f"\n{GREEN}✅ SUCCESS: Image generation completed!{RESET}")
                
                # Show all available keys
                print(f"  ├─ Response Keys: {list(result.keys())}")
                
                # Show specific fields
                if 'prompt' in result:
                    print(f"  ├─ Prompt Used: {result['prompt']}")
                if 'orientation' in result:
                    print(f"  ├─ Orientation: {result['orientation']}")
                if 'num_images' in result:
                    print(f"  ├─ Number of Images: {result['num_images']}")
                
                # Show image URLs if available
                if 'image_urls' in result and result['image_urls']:
                    print(f"  ├─ Generated Images:")
                    for i, url in enumerate(result['image_urls'][:3]):
                        print(f"  │  └─ Image {i+1}: {url[:80]}...")
                elif 'images' in result and result['images']:
                    print(f"  ├─ Generated Images:")
                    for i, img_data in enumerate(result['images'][:3]):
                        if isinstance(img_data, str):
                            print(f"  │  └─ Image {i+1}: {img_data[:80]}...")
                        else:
                            print(f"  │  └─ Image {i+1}: {str(img_data)[:80]}...")
                
                print(f"  └─ Status: {GREEN}Complete{RESET}")
                return True
            else:
                print(f"\n{YELLOW}⚠ WARNING: Unexpected response format{RESET}")
                print(f"  └─ Response: {str(result)[:200]}")
                return True
        elif response.status_code == 504:
            print(f"\n{RED}❌ TIMEOUT: Generation took too long{RESET}")
            print(f"  └─ The request exceeded the timeout limit")
            return False
        else:
            print(f"\n{RED}❌ FAILED: Generation failed with status {response.status_code}{RESET}")
            try:
                error = response.json()
                print(f"  ├─ Error: {error.get('error', 'Unknown')}")
                print(f"  └─ Detail: {error.get('detail', 'No details')}")
            except:
                print(f"  └─ Response: {response.text[:300]}")
            return False
    
    except Exception as e:
        print(f"\n{RED}❌ ERROR: {str(e)}{RESET}")
        return False

def test_server_running():
    """Check if server is running."""
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}Pre-Test: Checking API Server{RESET}")
    print(f"{BLUE}{'='*70}{RESET}\n")
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        print(f"{GREEN}✅ Server is running at {BASE_URL}{RESET}")
        return True
    except requests.exceptions.ConnectionError:
        print(f"{RED}❌ Cannot connect to server at {BASE_URL}{RESET}")
        print(f"   Make sure to start the server first:")
        print(f"   python -m uvicorn src.metaai_api.api_server:app --reload")
        return False
    except Exception as e:
        print(f"{RED}❌ Server error: {str(e)}{RESET}")
        return False

def main():
    """Run all tests."""
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}🧪 Meta AI Upload & Generation Test Suite{RESET}")
    print(f"{BLUE}{'='*70}{RESET}")
    
    # Check server
    if not test_server_running():
        return
    
    # Test upload
    media_id = test_upload_image()
    
    # Test generation with uploaded image
    if media_id:
        success = test_generate_with_uploaded_image(media_id)
    else:
        print(f"\n{RED}⚠ Skipping generation test - upload failed{RESET}")
        success = False
    
    # Final summary
    print(f"\n{BLUE}{'='*70}{RESET}")
    if media_id and success:
        print(f"{GREEN}🎉 ALL TESTS PASSED!{RESET}")
        print(f"{GREEN}Both upload and image generation with uploaded media work correctly.{RESET}")
    elif media_id:
        print(f"{YELLOW}⚠ PARTIAL SUCCESS{RESET}")
        print(f"{YELLOW}Upload works but generation had issues.{RESET}")
    else:
        print(f"{RED}❌ TESTS FAILED{RESET}")
        print(f"{RED}Upload failed - check API credentials and configuration.{RESET}")
    print(f"{BLUE}{'='*70}{RESET}\n")

if __name__ == "__main__":
    main()
