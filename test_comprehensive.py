"""
Comprehensive API Test Script
Tests all endpoints with proper error handling and timeouts
"""

import requests
import json
import time
from pathlib import Path

API_URL = "http://localhost:8000"
TIMEOUT = 120  # 2 minutes timeout
VIDEO_TIMEOUT = 300  # 5 minutes for video generation
IMAGE_PATH = r"C:\Users\spike\Downloads\meta-ai-api-main\ChatGPT Image Jan 14, 2026, 06_59_02 PM.png"

def print_header(text):
    print("\n" + "="*80)
    print(f"  {text}")
    print("="*80)

def test_1_health():
    """Test 1: Health Check"""
    print_header("TEST 1: Health Check (/healthz)")
    try:
        response = requests.get(f"{API_URL}/healthz", timeout=5)
        if response.status_code == 200:
            print("✅ PASS - Health check successful")
            print(f"   Response: {response.json()}")
            return True
        else:
            print(f"❌ FAIL - Status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ FAIL - Error: {e}")
        return False

def test_2_chat_simple():
    """Test 2: Simple Chat"""
    print_header("TEST 2: Simple Chat without Media (/chat)")
    try:
        payload = {
            "message": "What is 5+5? Reply with just the number.",
            "stream": False,
            "new_conversation": True
        }
        print(f"Request: {payload['message']}")
        response = requests.post(
            f"{API_URL}/chat",
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=TIMEOUT
        )
        if response.status_code == 200:
            result = response.json()
            print("✅ PASS - Chat endpoint working")
            print(f"   AI Response: {result.get('message', 'No message')[:150]}")
            return True
        else:
            print(f"❌ FAIL - Status: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
    except requests.Timeout:
        print(f"❌ FAIL - Timeout after {TIMEOUT}s")
        return False
    except Exception as e:
        print(f"❌ FAIL - Error: {e}")
        return False

def test_3_upload():
    """Test 3: Image Upload"""
    print_header("TEST 3: Image Upload (/upload)")
    
    if not Path(IMAGE_PATH).exists():
        print(f"⚠️  SKIP - Image not found: {IMAGE_PATH}")
        return False, None
    
    try:
        print(f"Uploading: {Path(IMAGE_PATH).name}")
        with open(IMAGE_PATH, 'rb') as f:
            files = {'file': f}
            response = requests.post(
                f"{API_URL}/upload",
                files=files,
                timeout=TIMEOUT
            )
        
        if response.status_code == 200:
            result = response.json()
            media_id = result.get('media_id')
            metadata = {
                'file_size': result.get('file_size'),
                'mime_type': result.get('mime_type')
            }
            print("✅ PASS - Upload successful")
            print(f"   Media ID: {media_id}")
            print(f"   Size: {result.get('file_size')} bytes")
            print(f"   MIME: {result.get('mime_type')}")
            return True, (media_id, metadata)
        else:
            print(f"❌ FAIL - Status: {response.status_code}")
            print(f"   Error: {response.text}")
            return False, None
    except Exception as e:
        print(f"❌ FAIL - Error: {e}")
        return False, None

def test_4_chat_with_image(media_id, metadata):
    """Test 4: Chat with Uploaded Image"""
    print_header("TEST 4: Chat with Image Analysis (/chat)")
    
    if not media_id:
        print("⚠️  SKIP - No media_id available")
        return False
    
    try:
        payload = {
            "message": "What do you see in this image? Describe briefly.",
            "media_ids": [media_id],
            "attachment_metadata": metadata,
            "stream": False,
            "new_conversation": True
        }
        print(f"Request: {payload['message']}")
        print(f"Media ID: {media_id}")
        
        response = requests.post(
            f"{API_URL}/chat",
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=TIMEOUT
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ PASS - Image analysis working")
            print(f"   AI Response: {result.get('message', 'No message')[:200]}")
            if result.get('media'):
                print(f"   Media in response: {len(result['media'])} items")
            return True
        else:
            print(f"❌ FAIL - Status: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
    except requests.Timeout:
        print(f"❌ FAIL - Timeout after {TIMEOUT}s")
        return False
    except Exception as e:
        print(f"❌ FAIL - Error: {e}")
        return False

def test_5_image_generation():
    """Test 5: Image Generation"""
    print_header("TEST 5: Image Generation without Upload (/image)")
    try:
        payload = {
            "prompt": "a red apple on a wooden table",
            "new_conversation": True,
            "orientation": "SQUARE"
        }
        print(f"Request: {payload['prompt']}")
        
        response = requests.post(
            f"{API_URL}/image",
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=TIMEOUT
        )
        
        if response.status_code == 200:
            result = response.json()
            media = result.get('media', [])
            print("✅ PASS - Image generation working")
            print(f"   Generated images: {len(media)}")
            for i, m in enumerate(media[:3], 1):
                url = m.get('url', 'No URL')
                print(f"   {i}. {url[:70]}...")
            return True
        else:
            print(f"❌ FAIL - Status: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
    except requests.Timeout:
        print(f"❌ FAIL - Timeout after {TIMEOUT}s")
        return False
    except Exception as e:
        print(f"❌ FAIL - Error: {e}")
        return False

def test_6_image_with_uploaded(media_id, metadata):
    """Test 6: Similar Image Generation"""
    print_header("TEST 6: Similar Image Generation (/image)")
    
    if not media_id:
        print("⚠️  SKIP - No media_id available")
        return False
    
    try:
        payload = {
            "prompt": "create a similar image in watercolor style",
            "media_ids": [media_id],
            "attachment_metadata": metadata,
            "new_conversation": True,
            "orientation": "VERTICAL"
        }
        print(f"Request: {payload['prompt']}")
        print(f"Media ID: {media_id}")
        
        response = requests.post(
            f"{API_URL}/image",
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=TIMEOUT
        )
        
        if response.status_code == 200:
            result = response.json()
            media = result.get('media', [])
            print("✅ PASS - Similar image generation working")
            print(f"   Generated images: {len(media)}")
            print(f"  Image URLs:")
            for i, m in enumerate(media[:3], 1):
                url = m.get('url', 'No URL')
                print(f"   {i}. {url[:70]}...")
            return True
        else:
            print(f"❌ FAIL - Status: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
    except requests.Timeout:
        print(f"❌ FAIL - Timeout after {TIMEOUT}s")
        return False
    except Exception as e:
        print(f"❌ FAIL - Error: {e}")
        return False

def test_7_image_with_orientation():
    """Test 7: Image Generation with Orientation"""
    print_header("TEST 7: Image Generation with Orientation (/image)")
    try:
        # Test VERTICAL orientation 
        payload = {
            "prompt": "a beautiful sunset over mountains",
            "new_conversation": True,
            "orientation": "LANDSCAPE"
        }
        print(f"Request: {payload['prompt']}")
        print(f"Orientation: {payload['orientation']}")
        
        response = requests.post(
            f"{API_URL}/image",
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=TIMEOUT
        )
        
        if response.status_code == 200:
            result = response.json()
            media = result.get('media', [])
            print("✅ PASS - Image with orientation working")
            print(f"   Generated images: {len(media)}")
            print(f"  Image URLs:")
            for i, m in enumerate(media[:3], 1):
                url = m.get('url', 'No URL')
                print(f"   {i}. {url[:70]}...")
            return True
        else:
            print(f"❌ FAIL - Status: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
    except requests.Timeout:
        print(f"❌ FAIL - Timeout after {TIMEOUT}s")
        return False
    except Exception as e:
        print(f"❌ FAIL - Error: {e}")
        return False

def test_8_video_sync(media_id, metadata):
    """Test 8: Synchronous Video Generation"""
    print_header("TEST 8: Video Generation - Synchronous (/video)")
    
    if not media_id:
        print("⚠️  SKIP - No media_id available")
        return False
    
    try:
        payload = {
            "prompt": "create a video with zoom in effect on this image",
            "media_ids": [media_id],
            "attachment_metadata": metadata,
            "wait_before_poll": 20,  # Wait longer before first check
            "max_attempts": 25,  # More attempts
            "wait_seconds": 6,  # Longer between checks
            "verbose": True  # Enable verbose for debugging
        }
        print(f"Request: {payload['prompt']}")
        print(f"Media ID: {media_id}")
        print(f"⏳ This may take 2-4 minutes...")
        
        response = requests.post(
            f"{API_URL}/video",
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=VIDEO_TIMEOUT
        )
        
        if response.status_code == 200:
            result = response.json()
            success = result.get('success', False)
            video_urls = result.get('video_urls', [])
            
            if success and video_urls:
                print("✅ PASS - Video generation successful")
                print(f"   Video URLs: {len(video_urls)}")
                for i, url in enumerate(video_urls[:2], 1):
                    print(f"   {i}. {url[:70]}...")
                return True
            elif success:
                print(f"⚠️  PARTIAL - Generation reported success but no video URLs found")
                print(f"   This might mean videos are still processing")
                return False
            else:
                print(f"❌ FAIL - Video generation failed")
                print(f"   Error: {result.get('error', 'No error message')}")
                print(f"   Conversation ID: {result.get('conversation_id', 'None')}")
                return False
        else:
            print(f"❌ FAIL - Status: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
    except requests.Timeout:
        print(f"❌ FAIL - Timeout after {VIDEO_TIMEOUT}s")
        return False
    except Exception as e:
        print(f"❌ FAIL - Error: {e}")
        return False

def test_9_video_async(media_id, metadata):
    """Test 9: Asynchronous Video Generation with Job Tracking"""
    print_header("TEST 9: Video Generation - Async with Job Tracking (/video/async)")
    
    if not media_id:
        print("⚠️  SKIP - No media_id available")
        return False
    
    try:
        payload = {
            "prompt": "create a cinematic video with smooth camera movement",
            "media_ids": [media_id],
            "attachment_metadata": metadata,
            "wait_before_poll": 20,  # Wait longer before first check
            "max_attempts": 25,  # More attempts
            "wait_seconds": 6,  # Longer between checks
            "verbose": True  # Enable verbose for debugging
        }
        print(f"Request: {payload['prompt']}")
        print(f"Media ID: {media_id}")
        
        # Submit async job
        response = requests.post(
            f"{API_URL}/video/async",
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            job_id = result.get('job_id')
            print(f"✅ Job submitted successfully")
            print(f"   Job ID: {job_id}")
            
            # Poll job status
            print(f"   ⏳ Polling job status (max 15 attempts, ~3 minutes)...")
            max_polls = 15
            poll_interval = 12  # Check every 12 seconds
            
            for i in range(max_polls):
                time.sleep(poll_interval)
                status_response = requests.get(f"{API_URL}/video/jobs/{job_id}", timeout=10)
                
                if status_response.status_code == 200:
                    job_status = status_response.json()
                    current_status = job_status.get('status')
                    
                    if current_status == 'succeeded':
                        job_result = job_status.get('result', {})
                        video_urls = job_result.get('video_urls', [])
                        if video_urls:
                            print(f"   ✅ PASS - Job completed successfully")
                            print(f"      Video URLs: {len(video_urls)}")
                            for idx, url in enumerate(video_urls[:2], 1):
                                print(f"      {idx}. {url[:70]}...")
                            return True
                        else:
                            print(f"   ⚠️  Job succeeded but no video URLs found")
                            return False
                    elif current_status == 'failed':
                        error = job_status.get('error', 'Unknown error')
                        print(f"   ❌ Job failed: {error}")
                        result = job_status.get('result', {})
                        if result:
                            print(f"   Result details: {result}")
                        return False
                    elif current_status in ['pending', 'running']:
                        print(f"   Poll {i+1}/{max_polls}: Status={current_status}")
                else:
                    print(f"   ❌ Failed to get job status")
                    return False
            
            print(f"   ⚠️  Job still processing after {max_polls} polls (~{max_polls * poll_interval}s)")
            print(f"   Check manually: GET {API_URL}/video/jobs/{job_id}")
            return False
        else:
            print(f"❌ FAIL - Status: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
    except requests.Timeout:
        print(f"❌ FAIL - Timeout")
        return False
    except Exception as e:
        print(f"❌ FAIL - Error: {e}")
        return False

def main():
    """Run all tests"""
    print("\n" + "╔" + "="*78 + "╗")
    print("║" + " "*20 + "COMPREHENSIVE API TEST SUITE" + " "*30 + "║")
    print("╚" + "="*78 + "╝")
    print(f"\nAPI URL: {API_URL}")
    print(f"Timeout: {TIMEOUT}s per request")
    print(f"Image: {IMAGE_PATH}")
    
    results = {}
    
    # Test 1: Health
    results['1. Health Check'] = test_1_health()
    time.sleep(1)
    
    # Test 2: Simple Chat
    results['2. Simple Chat'] = test_2_chat_simple()
    time.sleep(1)
    
    # Test 3: Upload
    upload_success, upload_data = test_3_upload()
    results['3. Upload Image'] = upload_success
    media_id, metadata = upload_data if upload_data else (None, None)
    time.sleep(1)
    
    # Test 4: Chat with Image
    if media_id:
        results['4. Chat with Image'] = test_4_chat_with_image(media_id, metadata)
        time.sleep(1)
    else:
        print_header("TEST 4: SKIPPED - No media_id")
        results['4. Chat with Image'] = False
    
    # Test 5: Image Generation
    results['5. Image Generation'] = test_5_image_generation()
    time.sleep(1)
    
    # Test 6: Similar Image
    if media_id:
        results['6. Similar Image'] = test_6_image_with_uploaded(media_id, metadata)
        time.sleep(1)
    else:
        print_header("TEST 6: SKIPPED - No media_id")
        results['6. Similar Image'] = False
    
    # Test 7: Image with Orientation
    results['7. Image Orientation'] = test_7_image_with_orientation()
    time.sleep(1)
    
    # Test 8: Video Generation (Sync)
    if media_id:
        results['8. Video Sync'] = test_8_video_sync(media_id, metadata)
        time.sleep(2)
    else:
        print_header("TEST 8: SKIPPED - No media_id")
        results['8. Video Sync'] = False
    
    # Test 9: Video Generation (Async)
    if media_id:
        results['9. Video Async'] = test_9_video_async(media_id, metadata)
    else:
        print_header("TEST 9: SKIPPED - No media_id")
        results['9. Video Async'] = False
    
    # Summary
    print("\n" + "="*80)
    print("  FINAL SUMMARY")
    print("="*80)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name.ljust(30)}: {status}")
    
    total = len(results)
    passed = sum(results.values())
    percentage = (passed / total * 100) if total > 0 else 0
    
    print("\n" + "-"*80)
    print(f"Total: {passed}/{total} tests passed ({percentage:.1f}%)")
    print("-"*80)
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! 🎉")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Review logs above.")
    
    print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    main()
