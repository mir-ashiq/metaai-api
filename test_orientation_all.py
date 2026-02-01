"""
Test script for comprehensive orientation testing of images and videos.
Tests all three orientation modes: VERTICAL, LANDSCAPE, SQUARE
"""

import requests
import time
from pathlib import Path

# API Configuration
BASE_URL = "http://localhost:8000"
TIMEOUT = 180

# Test image path
TEST_IMAGE = Path(__file__).parent / "ChatGPT Image Jan 14, 2026, 06_59_02 PM.png"

def print_header(title):
    """Print a formatted header"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)

def print_result(success, message):
    """Print test result"""
    icon = "✅" if success else "❌"
    print(f"{icon} {message}")

def upload_image():
    """Upload test image and return media ID"""
    print_header("UPLOADING TEST IMAGE")
    
    with open(TEST_IMAGE, "rb") as f:
        files = {"file": (TEST_IMAGE.name, f, "image/png")}
        response = requests.post(f"{BASE_URL}/upload", files=files, timeout=TIMEOUT)
    
    if response.status_code == 200:
        data = response.json()
        media_id = data.get("media_id")
        print_result(True, f"Image uploaded successfully - Media ID: {media_id}")
        return media_id
    else:
        print_result(False, f"Upload failed - Status: {response.status_code}")
        return None

def test_image_orientation(orientation, prompt):
    """Test image generation with specific orientation"""
    print_header(f"IMAGE GENERATION - {orientation}")
    print(f"Prompt: {prompt}")
    
    payload = {
        "prompt": prompt,
        "orientation": orientation
    }
    
    response = requests.post(f"{BASE_URL}/image", json=payload, timeout=TIMEOUT)
    
    if response.status_code == 200:
        data = response.json()
        # API returns 'media' array, not 'images'
        media = data.get("media", [])
        images = [m for m in media if m.get("type") == "IMAGE"]
        print_result(True, f"Generated {len(images)} images with {orientation} orientation")
        if images:
            print(f"  Sample URL: {images[0]['url'][:80]}...")
        return True
    else:
        print_result(False, f"Failed - Status: {response.status_code}")
        return False

def test_video_orientation(orientation, prompt, media_id):
    """Test video generation with specific orientation"""
    print_header(f"VIDEO GENERATION - {orientation}")
    print(f"Prompt: {prompt}")
    print(f"Media ID: {media_id}")
    print("⏳ Generating video (this may take 2-3 minutes)...")
    
    payload = {
        "prompt": prompt,
        "media_id": media_id,
        "orientation": orientation
    }
    
    start_time = time.time()
    response = requests.post(f"{BASE_URL}/video", json=payload, timeout=TIMEOUT)
    elapsed = time.time() - start_time
    
    if response.status_code == 200:
        data = response.json()
        success = data.get("success", False)
        video_urls = data.get("video_urls", [])
        
        if success and video_urls:
            print_result(True, f"Generated {len(video_urls)} video(s) with {orientation} orientation")
            print(f"  Time taken: {elapsed:.1f}s")
            print(f"  Video URL: {video_urls[0][:80]}...")
            return True
        else:
            print_result(False, f"Generation succeeded but no videos returned")
            return False
    else:
        print_result(False, f"Failed - Status: {response.status_code}")
        return False

def main():
    print("\n" + "╔" + "="*78 + "╗")
    print("║" + " "*20 + "ORIENTATION TEST SUITE" + " "*37 + "║")
    print("╚" + "="*78 + "╝")
    
    results = {
        "image_vertical": False,
        "image_landscape": False,
        "image_square": False,
        "video_vertical": False,
        "video_landscape": False,
        "video_square": False
    }
    
    # Upload test image first
    media_id = upload_image()
    if not media_id:
        print("\n❌ Cannot proceed without uploaded image")
        return
    
    # ==================== IMAGE ORIENTATION TESTS ====================
    print("\n" + "█"*80)
    print("  PART 1: IMAGE ORIENTATION TESTS")
    print("█"*80)
    
    # Test VERTICAL orientation for images
    results["image_vertical"] = test_image_orientation(
        "VERTICAL",
        "a tall lighthouse on a rocky cliff at sunset"
    )
    time.sleep(2)  # Brief pause between tests
    
    # Test LANDSCAPE orientation for images
    results["image_landscape"] = test_image_orientation(
        "LANDSCAPE",
        "a wide panoramic view of mountains and valleys"
    )
    time.sleep(2)
    
    # Test SQUARE orientation for images
    results["image_square"] = test_image_orientation(
        "SQUARE",
        "a perfectly centered mandala design"
    )
    time.sleep(2)
    
    # ==================== VIDEO ORIENTATION TESTS ====================
    print("\n" + "█"*80)
    print("  PART 2: VIDEO ORIENTATION TESTS")
    print("█"*80)
    
    # Test VERTICAL orientation for videos
    results["video_vertical"] = test_video_orientation(
        "VERTICAL",
        "create a vertical video with upward camera movement",
        media_id
    )
    time.sleep(2)
    
    # Test LANDSCAPE orientation for videos
    results["video_landscape"] = test_video_orientation(
        "LANDSCAPE",
        "create a cinematic wide-angle video with smooth panning",
        media_id
    )
    time.sleep(2)
    
    # Test SQUARE orientation for videos
    results["video_square"] = test_video_orientation(
        "SQUARE",
        "create a square format video with zoom effect",
        media_id
    )
    
    # ==================== FINAL SUMMARY ====================
    print_header("FINAL TEST RESULTS")
    
    print("\nIMAGE ORIENTATION:")
    print(f"  • VERTICAL   : {'✅ PASS' if results['image_vertical'] else '❌ FAIL'}")
    print(f"  • LANDSCAPE  : {'✅ PASS' if results['image_landscape'] else '❌ FAIL'}")
    print(f"  • SQUARE     : {'✅ PASS' if results['image_square'] else '❌ FAIL'}")
    
    print("\nVIDEO ORIENTATION:")
    print(f"  • VERTICAL   : {'✅ PASS' if results['video_vertical'] else '❌ FAIL'}")
    print(f"  • LANDSCAPE  : {'✅ PASS' if results['video_landscape'] else '❌ FAIL'}")
    print(f"  • SQUARE     : {'✅ PASS' if results['video_square'] else '❌ FAIL'}")
    
    total_tests = len(results)
    passed_tests = sum(1 for v in results.values() if v)
    percentage = (passed_tests / total_tests) * 100
    
    print("\n" + "-"*80)
    print(f"Total: {passed_tests}/{total_tests} tests passed ({percentage:.1f}%)")
    print("-"*80)
    
    if passed_tests == total_tests:
        print("\n🎉 ALL ORIENTATION TESTS PASSED! 🎉")
    else:
        print(f"\n⚠️  {total_tests - passed_tests} test(s) failed")
    
    print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ ERROR: {e}")
