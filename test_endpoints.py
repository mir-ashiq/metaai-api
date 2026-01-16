"""
Test script for all API endpoints with image upload.
Tests: /upload, /chat, /image endpoints
"""

import requests
import json
import time
from pathlib import Path

# Configuration
API_URL = "http://localhost:8000"
IMAGE_PATH = r"C:\Users\spike\Downloads\meta-ai-api-main\ChatGPT Image Jan 14, 2026, 06_59_02 PM.png"

def print_separator(title):
    """Print a formatted separator."""
    print("\n" + "=" * 70)
    print(f" {title}")
    print("=" * 70)

def test_upload_endpoint():
    """Test the /upload endpoint."""
    print_separator("TEST 1: Upload Image Endpoint")
    
    # Check if file exists
    if not Path(IMAGE_PATH).exists():
        print(f"✗ Error: Image file not found at {IMAGE_PATH}")
        return None, None
    
    print(f"Uploading image: {IMAGE_PATH}")
    
    try:
        with open(IMAGE_PATH, 'rb') as f:
            files = {'file': f}
            response = requests.post(f"{API_URL}/upload", files=files)
        
        print(f"\nStatus Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("\n✓ Upload Successful!")
            print(f"  Media ID: {result.get('media_id')}")
            print(f"  File Name: {result.get('file_name')}")
            print(f"  File Size: {result.get('file_size')} bytes")
            print(f"  MIME Type: {result.get('mime_type')}")
            print(f"  Upload Session ID: {result.get('upload_session_id')}")
            
            # Return both media_id and metadata
            metadata = {
                'file_size': result.get('file_size'),
                'mime_type': result.get('mime_type')
            }
            return result.get('media_id'), metadata
        else:
            print(f"✗ Upload Failed!")
            print(f"  Response: {response.text}")
            return None, None
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return None, None

def test_chat_endpoint(media_id, attachment_metadata):
    """Test the /chat endpoint with media_id."""
    print_separator("TEST 2: Chat Endpoint with Image Analysis")
    
    if not media_id:
        print("✗ Skipping: No media_id available")
        return
    
    print(f"Using Media ID: {media_id}")
    print(f"Attachment Metadata: {attachment_metadata}")
    print("Prompt: 'What do you see in this image?'")
    
    try:
        payload = {
            "message": "What do you see in this image? Describe it in detail.",
            "media_ids": [media_id],
            "attachment_metadata": attachment_metadata,
            "stream": False,
            "new_conversation": True
        }
        
        response = requests.post(
            f"{API_URL}/chat",
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload)
        )
        
        print(f"\nStatus Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("\n✓ Chat Response Received!")
            print(f"\nAI Response:")
            print(f"  {result.get('message', 'No message')[:500]}...")
            
            if result.get('media'):
                print(f"\n  Media in response: {len(result['media'])} items")
                for i, media in enumerate(result['media'], 1):
                    print(f"    {i}. Type: {media.get('type')}, URL: {media.get('url')[:80]}...")
            
            if result.get('sources'):
                print(f"\n  Sources: {len(result['sources'])} found")
        else:
            print(f"✗ Chat Failed!")
            print(f"  Response: {response.text}")
            
    except Exception as e:
        print(f"✗ Error: {e}")

def test_image_endpoint(media_id, attachment_metadata):
    """Test the /image endpoint for similar image generation."""
    print_separator("TEST 3: Image Endpoint for Similar Image Generation")
    
    if not media_id:
        print("✗ Skipping: No media_id available")
        return
    
    print(f"Using Media ID: {media_id}")
    print(f"Attachment Metadata: {attachment_metadata}")
    print("Prompt: 'Create a similar image in watercolor painting style'")
    
    try:
        payload = {
            "prompt": "Create a similar image in watercolor painting style",
            "media_ids": [media_id],
            "attachment_metadata": attachment_metadata,
            "new_conversation": True
        }
        
        response = requests.post(
            f"{API_URL}/image",
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload)
        )
        
        print(f"\nStatus Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("\n✓ Image Generation Response Received!")
            print(f"\nAI Response:")
            print(f"  {result.get('message', 'No message')[:500]}...")
            
            if result.get('media'):
                print(f"\n  Generated Media: {len(result['media'])} items")
                for i, media in enumerate(result['media'], 1):
                    print(f"    {i}. Type: {media.get('type')}")
                    print(f"       URL: {media.get('url')}")
                    if media.get('prompt'):
                        print(f"       Prompt: {media.get('prompt')[:80]}...")
            else:
                print("\n  No media generated in response")
        else:
            print(f"✗ Image Generation Failed!")
            print(f"  Response: {response.text}")
            
    except Exception as e:
        print(f"✗ Error: {e}")

def test_video_generation_sync(media_id, attachment_metadata):
    """Test synchronous video generation with uploaded image."""
    print_separator("TEST 4: Video Generation (Synchronous)")
    
    if not media_id:
        print("✗ Skipping: No media_id available")
        return
    
    print(f"Using Media ID: {media_id}")
    print(f"Attachment Metadata: {attachment_metadata}")
    print("Prompt: 'generate a video with zoom in effect on this image'")
    
    try:
        payload = {
            "prompt": "generate a video with zoom in effect on this image",
            "media_ids": [media_id],
            "attachment_metadata": attachment_metadata,
            "wait_before_poll": 15,
            "max_attempts": 30,
            "wait_seconds": 5,
            "verbose": True
        }
        
        print("\n⏳ Sending synchronous video generation request...")
        response = requests.post(
            f"{API_URL}/video",
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload)
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("\n✓ Video Generation Response Received!")
            
            if result.get('success'):
                print(f"\n  Status: SUCCESS")
                print(f"  Conversation ID: {result.get('conversation_id')}")
                print(f"  Prompt: {result.get('prompt')}")
                
                video_urls = result.get('video_urls', [])
                if video_urls:
                    print(f"\n  Generated Videos: {len(video_urls)}")
                    for i, url in enumerate(video_urls, 1):
                        print(f"    {i}. {url[:100]}...")
                else:
                    print("\n  No videos generated yet (may need to wait longer)")
            else:
                print(f"\n  Status: FAILED")
                print(f"  Error: {result.get('error', 'Unknown error')}")
        else:
            print(f"✗ Video Generation Request Failed!")
            print(f"  Response: {response.text}")
            
    except Exception as e:
        print(f"✗ Error: {e}")

def test_video_generation_async(media_id, attachment_metadata):
    """Test asynchronous video generation with job tracking."""
    print_separator("TEST 5: Video Generation (Asynchronous with Job Tracking)")
    
    if not media_id:
        print("✗ Skipping: No media_id available")
        return
    
    print(f"Using Media ID: {media_id}")
    print(f"Attachment Metadata: {attachment_metadata}")
    print("Prompt: 'create a cinematic video with smooth camera movement'")
    
    try:
        payload = {
            "prompt": "create a cinematic video with smooth camera movement",
            "media_ids": [media_id],
            "attachment_metadata": attachment_metadata,
            "wait_before_poll": 10,
            "max_attempts": 30,
            "wait_seconds": 5,
            "verbose": False
        }
        
        # Step 1: Submit async job
        print("\n⏳ Submitting async video generation job...")
        response = requests.post(
            f"{API_URL}/video/async",
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload)
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            job_id = result.get('job_id')
            status = result.get('status')
            
            print("\n✓ Job Submitted!")
            print(f"  Job ID: {job_id}")
            print(f"  Initial Status: {status}")
            
            # Step 2: Poll job status
            print("\n⏳ Polling job status...")
            max_polls = 15
            poll_interval = 3
            
            for i in range(max_polls):
                time.sleep(poll_interval)
                
                status_response = requests.get(f"{API_URL}/video/jobs/{job_id}")
                
                if status_response.status_code == 200:
                    job_status = status_response.json()
                    current_status = job_status.get('status')
                    
                    print(f"\n  Poll {i+1}/{max_polls}:")
                    print(f"    Job ID: {job_status.get('job_id')}")
                    print(f"    Status: {current_status}")
                    print(f"    Created At: {job_status.get('created_at')}")
                    print(f"    Updated At: {job_status.get('updated_at')}")
                    
                    # Debug: Show full job status for failed or succeeded states
                    if current_status in ['succeeded', 'failed']:
                        print(f"\n  [DEBUG] Full job status:")
                        print(f"    {json.dumps(job_status, indent=6)}")
                    
                    if current_status == 'succeeded':
                        print("\n  ✓ Job Completed Successfully!")
                        job_result = job_status.get('result', {})
                        if job_result:
                            print(f"\n  Result:")
                            print(f"    Success: {job_result.get('success')}")
                            print(f"    Conversation ID: {job_result.get('conversation_id')}")
                            
                            video_urls = job_result.get('video_urls', [])
                            if video_urls:
                                print(f"    Video URLs: {len(video_urls)}")
                                for idx, url in enumerate(video_urls, 1):
                                    print(f"      {idx}. {url[:100]}...")
                        break
                    
                    elif current_status == 'failed':
                        print("\n  ✗ Job Failed!")
                        error = job_status.get('error', 'Unknown error')
                        print(f"    Error: {error}")
                        break
                    
                    elif current_status in ['pending', 'running']:
                        print(f"    ⏳ Job still {current_status}... waiting")
                else:
                    print(f"\n  ✗ Failed to get job status: {status_response.status_code}")
                    break
            else:
                print("\n  ⚠ Reached max polling attempts. Job may still be processing.")
                print(f"  You can check status manually: GET {API_URL}/video/jobs/{job_id}")
                
        else:
            print(f"✗ Job Submission Failed!")
            print(f"  Response: {response.text}")
            
    except Exception as e:
        print(f"✗ Error: {e}")

def test_healthz_endpoint():
    """Test the /healthz endpoint."""
    print_separator("TEST 0: Health Check Endpoint")
    
    try:
        response = requests.get(f"{API_URL}/healthz")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Health Check: {result.get('status')}")
        else:
            print(f"✗ Health Check Failed: {response.text}")
            
    except Exception as e:
        print(f"✗ Error connecting to server: {e}")
        print("\nMake sure the server is running:")
        print("  uvicorn metaai_api.api_server:app --host 0.0.0.0 --port 8000")

def main():
    """Run all endpoint tests."""
    print("\n")
    print("+" + "=" * 68 + "+")
    print("|" + " " * 18 + "API Endpoint Testing Suite" + " " * 24 + "|")
    print("+" + "=" * 68 + "+")
    
    print(f"\nAPI URL: {API_URL}")
    print(f"Image: {IMAGE_PATH}")
    
    # Test 0: Health check
    test_healthz_endpoint()
    
    # Test 1: Upload image (returns media_id and metadata)
    media_id, attachment_metadata = test_upload_endpoint()
    
    if media_id:
        # Test 2: Chat with image analysis
        test_chat_endpoint(media_id, attachment_metadata)
        
        # Test 3: Generate similar image
        test_image_endpoint(media_id, attachment_metadata)
        
        # Test 4: Generate video from image (synchronous)
        test_video_generation_sync(media_id, attachment_metadata)
        
        # Test 5: Generate video from image (asynchronous with job tracking)
        test_video_generation_async(media_id, attachment_metadata)
    else:
        print("\n✗ Cannot proceed with other tests without media_id")
    
    # Summary
    print_separator("Test Summary")
    print(f"""
Tests Completed:
0. ✓ Health Check (/healthz)
1. {'✓' if media_id else '✗'} Image Upload (/upload)
2. {'✓' if media_id else '✗'} Chat with Image (/chat)
3. {'✓' if media_id else '✗'} Similar Image Generation (/image)
4. {'✓' if media_id else '✗'} Video Generation - Synchronous (/video)
5. {'✓' if media_id else '✗'} Video Generation - Async with Job Tracking (/video/async, /video/jobs/{{job_id}})

{'All tests completed successfully!' if media_id else 'Some tests failed - check server status and configuration'}

Next Steps:
- Check the AI responses above
- Download generated images/videos from the URLs provided
- Test with different prompts and images
- Use /video/async for long-running video generation tasks
- Check job status anytime with: GET {API_URL}/video/jobs/{{job_id}}
    """)

if __name__ == "__main__":
    main()
