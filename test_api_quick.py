"""
Quick API test with timeout handling
"""

import requests
import json

API_URL = "http://localhost:8000"
TIMEOUT = 120  # 2 minutes timeout for each request

def test_health():
    """Test health check endpoint"""
    print("\n" + "="*70)
    print("TEST: Health Check")
    print("="*70)
    try:
        response = requests.get(f"{API_URL}/healthz", timeout=5)
        print(f"✓ Status: {response.status_code}")
        print(f"  Response: {response.json()}")
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_chat():
    """Test basic chat endpoint"""
    print("\n" + "="*70)
    print("TEST: Chat Endpoint (Simple)")
    print("="*70)
    try:
        payload = {
            "message": "What is 2+2?",
            "stream": False,
            "new_conversation": True
        }
        print(f"Request: {payload}")
        response = requests.post(
            f"{API_URL}/chat",
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=TIMEOUT
        )
        print(f"✓ Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"  Message: {result.get('message', 'No message')[:200]}")
            return True
        else:
            print(f"  Error: {response.text}")
            return False
    except requests.Timeout:
        print(f"✗ Timeout after {TIMEOUT}s")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_upload():
    """Test image upload endpoint"""
    print("\n" + "="*70)
    print("TEST: Image Upload")
    print("="*70)
    
    import os
    from pathlib import Path
    
    # Find an image to upload
    image_path = r"C:\Users\spike\Downloads\meta-ai-api-main\ChatGPT Image Jan 14, 2026, 06_59_02 PM.png"
    
    if not os.path.exists(image_path):
        print(f"✗ Image not found: {image_path}")
        return False, None
    
    try:
        with open(image_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(
                f"{API_URL}/upload",
                files=files,
                timeout=TIMEOUT
            )
        
        print(f"✓ Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            media_id = result.get('media_id')
            print(f"  Media ID: {media_id}")
            print(f"  File Size: {result.get('file_size')} bytes")
            print(f"  MIME Type: {result.get('mime_type')}")
            metadata = {
                'file_size': result.get('file_size'),
                'mime_type': result.get('mime_type')
            }
            return True, (media_id, metadata)
        else:
            print(f"  Error: {response.text}")
            return False, None
    except Exception as e:
        print(f"✗ Error: {e}")
        return False, None

def test_image_generation():
    """Test image generation endpoint"""
    print("\n" + "="*70)
    print("TEST: Image Generation")
    print("="*70)
    try:
        payload = {
            "prompt": "a cute cat wearing sunglasses",
            "new_conversation": True
        }
        print(f"Request: {payload}")
        response = requests.post(
            f"{API_URL}/image",
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=TIMEOUT
        )
        print(f"✓ Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"  Message: {result.get('message', 'No message')[:200]}")
            media = result.get('media', [])
            print(f"  Media count: {len(media)}")
            for i, m in enumerate(media[:2], 1):
                print(f"    {i}. {m.get('url', 'No URL')[:80]}...")
            return True
        else:
            print(f"  Error: {response.text}")
            return False
    except requests.Timeout:
        print(f"✗ Timeout after {TIMEOUT}s")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def main():
    """Run all tests"""
    print("\n" + "+"*70)
    print("  API QUICK TEST SUITE")
    print("+"*70)
    print(f"\nAPI URL: {API_URL}")
    print(f"Timeout: {TIMEOUT}s per request\n")
    
    results = {}
    
    # Test 1: Health
    results['health'] = test_health()
    
    # Test 2: Chat
    results['chat'] = test_chat()
    
    # Test 3: Upload
    upload_success, upload_data = test_upload()
    results['upload'] = upload_success
    
    # Test 4: Image Generation
    results['image'] = test_image_generation()
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{test_name.ljust(20)}: {status}")
    
    total = len(results)
    passed = sum(results.values())
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ All tests passed!")
    else:
        print(f"\n✗ {total - passed} test(s) failed")

if __name__ == "__main__":
    main()
