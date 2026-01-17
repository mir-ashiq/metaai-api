"""
Final Comprehensive Test - All Endpoints
Tests chat, image, and video endpoints with and without media_ids
"""

import requests
import json
import time

API_URL = "http://localhost:8000"
IMAGE_PATH = r"C:\Users\spike\Downloads\meta-ai-api-main\ChatGPT Image Jan 14, 2026, 06_59_02 PM.png"

def print_header(title):
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)

def print_result(success, message):
    symbol = "✓" if success else "✗"
    print(f"{symbol} {message}")

# ============================================================================
# SETUP: Upload Image
# ============================================================================
print_header("SETUP: Upload Image for Tests")

with open(IMAGE_PATH, 'rb') as f:
    upload_response = requests.post(f"{API_URL}/upload", files={'file': f})

if upload_response.status_code != 200:
    print_result(False, f"Upload failed: {upload_response.text}")
    exit(1)

upload_result = upload_response.json()
media_id = upload_result['media_id']
file_size = upload_result['file_size']
mime_type = upload_result['mime_type']
attachment_metadata = {"file_size": file_size, "mime_type": mime_type}

print_result(True, f"Uploaded - Media ID: {media_id}")

# ============================================================================
# TEST 1: CHAT WITHOUT MEDIA
# ============================================================================
print_header("TEST 1: CHAT Endpoint - WITHOUT media_ids")

payload = {
    "message": "What is the capital of France?",
    "stream": False,
    "new_conversation": True
}

try:
    response = requests.post(
        f"{API_URL}/chat",
        headers={"Content-Type": "application/json"},
        data=json.dumps(payload),
        timeout=30
    )
    
    if response.status_code == 200:
        result = response.json()
        message = result.get('message', '')
        print_result(True, f"Chat response received ({len(message)} chars)")
        print(f"Response: {message[:200]}...")
    else:
        print_result(False, f"Status {response.status_code}: {response.text[:200]}")
except Exception as e:
    print_result(False, f"Error: {e}")

# ============================================================================
# TEST 2: CHAT WITH MEDIA
# ============================================================================
print_header("TEST 2: CHAT Endpoint - WITH media_ids")

payload = {
    "message": "What do you see in this image? Describe it in detail.",
    "media_ids": [media_id],
    "attachment_metadata": attachment_metadata,
    "stream": False,
    "new_conversation": True
}

try:
    response = requests.post(
        f"{API_URL}/chat",
        headers={"Content-Type": "application/json"},
        data=json.dumps(payload),
        timeout=30
    )
    
    if response.status_code == 200:
        result = response.json()
        message = result.get('message', '')
        print_result(True, f"Chat with image response received ({len(message)} chars)")
        print(f"Response: {message[:200]}...")
    else:
        print_result(False, f"Status {response.status_code}: {response.text[:200]}")
except Exception as e:
    print_result(False, f"Error: {e}")

# ============================================================================
# TEST 3: IMAGE WITHOUT MEDIA (Text-to-Image)
# ============================================================================
print_header("TEST 3: IMAGE Endpoint - WITHOUT media_ids (Text-to-Image)")

payload = {
    "prompt": "A serene mountain landscape at sunset with a lake in the foreground",
    "new_conversation": True
}

try:
    response = requests.post(
        f"{API_URL}/image",
        headers={"Content-Type": "application/json"},
        data=json.dumps(payload),
        timeout=30
    )
    
    if response.status_code == 200:
        result = response.json()
        message = result.get('message', '')
        media = result.get('media', [])
        print_result(True, f"Image generation response received")
        print(f"Message: {message[:200]}...")
        print(f"Generated Images: {len(media)}")
        for idx, m in enumerate(media[:2], 1):  # Show first 2
            print(f"  {idx}. Type: {m.get('type')}, URL: {m.get('url', '')[:80]}...")
    else:
        print_result(False, f"Status {response.status_code}: {response.text[:200]}")
except Exception as e:
    print_result(False, f"Error: {e}")

# ============================================================================
# TEST 4: IMAGE WITH MEDIA (Image-to-Image)
# ============================================================================
print_header("TEST 4: IMAGE Endpoint - WITH media_ids (Image-to-Image)")

payload = {
    "prompt": "Create a similar image in anime style",
    "media_ids": [media_id],
    "attachment_metadata": attachment_metadata,
    "new_conversation": True
}

try:
    response = requests.post(
        f"{API_URL}/image",
        headers={"Content-Type": "application/json"},
        data=json.dumps(payload),
        timeout=30
    )
    
    if response.status_code == 200:
        result = response.json()
        message = result.get('message', '')
        media = result.get('media', [])
        print_result(True, f"Image-to-image response received")
        print(f"Message: {message[:200]}...")
        print(f"Generated Images: {len(media)}")
        for idx, m in enumerate(media[:2], 1):  # Show first 2
            print(f"  {idx}. Type: {m.get('type')}, URL: {m.get('url', '')[:80]}...")
    else:
        print_result(False, f"Status {response.status_code}: {response.text[:200]}")
except Exception as e:
    print_result(False, f"Error: {e}")

# ============================================================================
# TEST 5: VIDEO WITHOUT MEDIA (Text-to-Video)
# ============================================================================
print_header("TEST 5: VIDEO Endpoint - WITHOUT media_ids (Text-to-Video)")

payload = {
    "prompt": "A beautiful sunset over the ocean with waves",
    "wait_before_poll": 10,
    "max_attempts": 30,
    "wait_seconds": 5,
    "verbose": False
}

try:
    print("Submitting async video job (text-to-video)...")
    response = requests.post(
        f"{API_URL}/video/async",
        headers={"Content-Type": "application/json"},
        data=json.dumps(payload),
        timeout=30
    )
    
    if response.status_code == 200:
        result = response.json()
        job_id = result['job_id']
        print_result(True, f"Job submitted - ID: {job_id}")
        
        # Poll for result
        print("Polling for result (max 15 attempts, 3s interval)...")
        for attempt in range(1, 16):
            time.sleep(3)
            print(f"  Attempt {attempt}/15...", end=" ")
            
            status_response = requests.get(f"{API_URL}/video/jobs/{job_id}")
            if status_response.status_code == 200:
                job_status = status_response.json()
                status = job_status['status']
                print(f"Status: {status}")
                
                if status == 'succeeded':
                    job_result = job_status.get('result', {})
                    video_urls = job_result.get('video_urls', [])
                    print_result(True, f"Text-to-video SUCCEEDED! Found {len(video_urls)} video(s)")
                    for idx, url in enumerate(video_urls, 1):
                        print(f"    Video {idx}: {url[:80]}...")
                    break
                elif status == 'failed':
                    error = job_status.get('error', 'Unknown error')
                    print_result(False, f"Text-to-video FAILED: {error}")
                    break
            else:
                print(f"Failed to get status")
        else:
            print_result(False, "Max polling attempts reached")
    else:
        print_result(False, f"Status {response.status_code}: {response.text[:200]}")
except Exception as e:
    print_result(False, f"Error: {e}")

# ============================================================================
# TEST 6: VIDEO WITH MEDIA (Image-to-Video)
# ============================================================================
print_header("TEST 6: VIDEO Endpoint - WITH media_ids (Image-to-Video)")

payload = {
    "prompt": "generate a cinematic video with smooth zoom effect",
    "media_ids": [media_id],
    "attachment_metadata": attachment_metadata,
    "wait_before_poll": 10,
    "max_attempts": 30,
    "wait_seconds": 5,
    "verbose": False
}

try:
    print("Submitting async video job (image-to-video)...")
    response = requests.post(
        f"{API_URL}/video/async",
        headers={"Content-Type": "application/json"},
        data=json.dumps(payload),
        timeout=30
    )
    
    if response.status_code == 200:
        result = response.json()
        job_id = result['job_id']
        print_result(True, f"Job submitted - ID: {job_id}")
        
        # Poll for result
        print("Polling for result (max 15 attempts, 3s interval)...")
        for attempt in range(1, 16):
            time.sleep(3)
            print(f"  Attempt {attempt}/15...", end=" ")
            
            status_response = requests.get(f"{API_URL}/video/jobs/{job_id}")
            if status_response.status_code == 200:
                job_status = status_response.json()
                status = job_status['status']
                print(f"Status: {status}")
                
                if status == 'succeeded':
                    job_result = job_status.get('result', {})
                    video_urls = job_result.get('video_urls', [])
                    print_result(True, f"Image-to-video SUCCEEDED! Found {len(video_urls)} video(s)")
                    for idx, url in enumerate(video_urls, 1):
                        print(f"    Video {idx}: {url[:80]}...")
                    break
                elif status == 'failed':
                    error = job_status.get('error', 'Unknown error')
                    print_result(False, f"Image-to-video FAILED: {error}")
                    break
            else:
                print(f"Failed to get status")
        else:
            print_result(False, "Max polling attempts reached")
    else:
        print_result(False, f"Status {response.status_code}: {response.text[:200]}")
except Exception as e:
    print_result(False, f"Error: {e}")

# ============================================================================
# SUMMARY
# ============================================================================
print_header("TEST SUMMARY")
print("""
Tests Completed:
  ✓ Chat without media (text chat)
  ✓ Chat with media (image analysis)
  ✓ Image without media (text-to-image)
  ✓ Image with media (image-to-image)
  ✓ Video without media (text-to-video)
  ✓ Video with media (image-to-video)

All major use cases tested!
""")
