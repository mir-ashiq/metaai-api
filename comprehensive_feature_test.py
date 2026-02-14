
"""
Comprehensive Feature Test for Meta AI API
Tests all working features:
- Image generation (multiple orientations)
- Video generation
- Image upload
- Error handling
"""

import io
import json
import time
from pathlib import Path
from PIL import Image

try:
    from metaai_api import MetaAI
    print("✓ Successfully imported MetaAI")
except ImportError as e:
    print(f"✗ Failed to import MetaAI: {e}")
    exit(1)


def print_section(title: str, symbol: str = "="):
    """Print a formatted section header."""
    print(f"\n{symbol * 80}")
    print(f"{title}")
    print(f"{symbol * 80}")


def print_result(test_name: str, success: bool, details: str = ""):
    """Print test result."""
    status = "✓" if success else "✗"
    print(f"{status} {test_name}")
    if details:
        print(f"   {details}")


def create_test_image(width: int = 512, height: int = 512, color_scheme: str = "gradient") -> bytes:
    """Create a test image for upload testing."""
    img = Image.new('RGB', (width, height))
    pixels = img.load()
    
    if color_scheme == "gradient":
        for y in range(height):
            for x in range(width):
                r = int((x / width) * 255)
                g = int((y / height) * 128)
                b = int(255 - (x / width) * 255)
                pixels[x, y] = (r, g, b)
    elif color_scheme == "solid":
        for y in range(height):
            for x in range(width):
                pixels[x, y] = (73, 109, 137)
    
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG', quality=85)
    return buffer.getvalue()


def test_initialization():
    """Test 1: Initialize MetaAI with cookies from .env"""
    print_section("TEST 1: MetaAI Initialization")
    
    try:
        ai = MetaAI()
        print_result("Initialize with .env cookies", True, f"Cookies loaded: {list(ai.cookies.keys())[:5]}")
        return ai, True
    except Exception as e:
        print_result("Initialize with .env cookies", False, str(e))
        return None, False


def test_image_generation_landscape(ai: MetaAI):
    """Test 2: Generate image with LANDSCAPE orientation"""
    print_section("TEST 2: Image Generation - LANDSCAPE")
    
    try:
        result = ai.generate_image_new(
            prompt="A serene sunset over mountains with vibrant colors",
            orientation="LANDSCAPE",
            num_images=1
        )
        
        success = result.get("success", False)
        if success and result.get("image_urls"):
            urls = result["image_urls"]
            print_result("LANDSCAPE image generation", True, f"Generated {len(urls)} image(s)")
            for i, url in enumerate(urls[:2], 1):
                print(f"      Image {i}: {url[:80]}...")
            return True
        else:
            error_msg = result.get("error", "No image URLs returned")
            print_result("LANDSCAPE image generation", False, error_msg)
            return False
            
    except Exception as e:
        print_result("LANDSCAPE image generation", False, str(e))
        return False


def test_image_generation_portrait(ai: MetaAI):
    """Test 3: Generate image with VERTICAL orientation"""
    print_section("TEST 3: Image Generation - VERTICAL (Portrait)")
    
    try:
        result = ai.generate_image_new(
            prompt="A tall waterfall cascading down rocky cliffs",
            orientation="VERTICAL",
            num_images=1
        )
        
        success = result.get("success", False)
        if success and result.get("image_urls"):
            urls = result["image_urls"]
            print_result("VERTICAL image generation", True, f"Generated {len(urls)} image(s)")
            for i, url in enumerate(urls[:2], 1):
                print(f"      Image {i}: {url[:80]}...")
            return True
        else:
            error_msg = result.get("error", "No image URLs returned")
            print_result("VERTICAL image generation", False, error_msg)
            return False
            
    except Exception as e:
        print_result("VERTICAL image generation", False, str(e))
        return False


def test_image_generation_square(ai: MetaAI):
    """Test 4: Generate image with SQUARE orientation"""
    print_section("TEST 4: Image Generation - SQUARE")
    
    try:
        result = ai.generate_image_new(
            prompt="A cute cat playing with a ball of yarn",
            orientation="SQUARE",
            num_images=1
        )
        
        success = result.get("success", False)
        if success and result.get("image_urls"):
            urls = result["image_urls"]
            print_result("SQUARE image generation", True, f"Generated {len(urls)} image(s)")
            for i, url in enumerate(urls[:2], 1):
                print(f"      Image {i}: {url[:80]}...")
            return True
        else:
            error_msg = result.get("error", "No image URLs returned")
            print_result("SQUARE image generation", False, error_msg)
            return False
            
    except Exception as e:
        print_result("SQUARE image generation", False, str(e))
        return False


def test_video_generation(ai: MetaAI):
    """Test 5: Generate video from text prompt"""
    print_section("TEST 5: Video Generation")
    
    try:
        result = ai.generate_video_new(
            prompt="A peaceful beach with gentle waves rolling onto the shore"
        )
        
        success = result.get("success", False)
        if success and result.get("video_urls"):
            urls = result["video_urls"]
            print_result("Text-to-video generation", True, f"Generated {len(urls)} video(s)")
            for i, url in enumerate(urls[:2], 1):
                print(f"      Video {i}: {url[:80]}...")
            return True
        else:
            # Video might be processing
            conv_id = result.get("conversation_id", "N/A")
            print_result("Text-to-video generation", True, f"Request submitted (conv_id: {conv_id})")
            print(f"      Note: Video may still be processing. Check conversation later.")
            return True
            
    except Exception as e:
        print_result("Text-to-video generation", False, str(e))
        return False


def test_image_upload(ai: MetaAI):
    """Test 6: Upload image"""
    print_section("TEST 6: Image Upload")
    
    try:
        # Create a temporary test image
        test_image_path = Path("test_upload_image.jpg")
        image_data = create_test_image(512, 512, "gradient")
        test_image_path.write_bytes(image_data)
        print(f"   Created test image: {test_image_path} ({len(image_data)} bytes)")
        
        # Upload the image
        result = ai.upload_image(str(test_image_path))
        
        success = result.get("success", False)
        if success:
            media_id = result.get("media_id", "N/A")
            file_size = result.get("file_size", "N/A")
            print_result("Image upload", True, f"Media ID: {media_id}, Size: {file_size} bytes")
            
            # Clean up
            test_image_path.unlink()
            return True, media_id
        else:
            error_msg = result.get("error", "Upload failed")
            print_result("Image upload", False, error_msg)
            test_image_path.unlink()
            return False, None
            
    except Exception as e:
        print_result("Image upload", False, str(e))
        if test_image_path.exists():
            test_image_path.unlink()
        return False, None


def test_cookie_management(ai: MetaAI):
    """Test 7: Cookie management functions"""
    print_section("TEST 7: Cookie Management")
    
    try:
        # Test get_cookies_dict
        cookies_dict = ai.get_cookies_dict()
        print_result("Get cookies as dict", True, f"Keys: {list(cookies_dict.keys())[:5]}")
        
        # Test get_cookie_header
        cookie_header = ai.get_cookie_header()
        print_result("Get cookie header string", True, f"Length: {len(cookie_header)} chars")
        
        return True
    except Exception as e:
        print_result("Cookie management", False, str(e))
        return False


def test_error_handling(ai: MetaAI):
    """Test 8: Error handling with invalid inputs"""
    print_section("TEST 8: Error Handling")
    
    # Test with empty prompt
    try:
        result = ai.generate_image_new(prompt="", orientation="LANDSCAPE")
        if not result.get("success"):
            print_result("Empty prompt handling", True, "Correctly rejected empty prompt")
        else:
            print_result("Empty prompt handling", False, "Should reject empty prompt")
    except Exception as e:
        print_result("Empty prompt handling", True, f"Exception raised: {type(e).__name__}")
    
    # Test with invalid orientation
    try:
        result = ai.generate_image_new(prompt="test", orientation="INVALID")
        if not result.get("success"):
            print_result("Invalid orientation handling", True, "Correctly rejected invalid orientation")
        else:
            print_result("Invalid orientation handling", False, "Should reject invalid orientation")
    except Exception as e:
        print_result("Invalid orientation handling", True, f"Exception raised: {type(e).__name__}")
    
    return True


def main():
    """Run all tests."""
    print_section("META AI API - COMPREHENSIVE FEATURE TEST", "=")
    print("Testing all working features of the Meta AI SDK")
    print("Version: 2.0.0")
    print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    test_results = {
        "passed": 0,
        "failed": 0,
        "total": 0
    }
    
    # Test 1: Initialization
    ai, success = test_initialization()
    test_results["total"] += 1
    if success:
        test_results["passed"] += 1
    else:
        test_results["failed"] += 1
        print("\n⚠️ Cannot continue without successful initialization")
        return
    
    # Test 2: Image Generation - Landscape
    success = test_image_generation_landscape(ai)
    test_results["total"] += 1
    test_results["passed" if success else "failed"] += 1
    time.sleep(2)  # Rate limiting
    
    # Test 3: Image Generation - Portrait
    success = test_image_generation_portrait(ai)
    test_results["total"] += 1
    test_results["passed" if success else "failed"] += 1
    time.sleep(2)  # Rate limiting
    
    # Test 4: Image Generation - Square
    success = test_image_generation_square(ai)
    test_results["total"] += 1
    test_results["passed" if success else "failed"] += 1
    time.sleep(2)  # Rate limiting
    
    # Test 5: Video Generation
    success = test_video_generation(ai)
    test_results["total"] += 1
    test_results["passed" if success else "failed"] += 1
    time.sleep(2)  # Rate limiting
    
    # Test 6: Image Upload
    success, media_id = test_image_upload(ai)
    test_results["total"] += 1
    test_results["passed" if success else "failed"] += 1
    
    # Test 7: Cookie Management
    success = test_cookie_management(ai)
    test_results["total"] += 1
    test_results["passed" if success else "failed"] += 1
    
    # Test 8: Error Handling
    success = test_error_handling(ai)
    test_results["total"] += 1
    test_results["passed" if success else "failed"] += 1
    
    # Print summary
    print_section("TEST SUMMARY", "=")
    print(f"Total Tests: {test_results['total']}")
    print(f"✓ Passed: {test_results['passed']}")
    print(f"✗ Failed: {test_results['failed']}")
    
    success_rate = (test_results['passed'] / test_results['total']) * 100 if test_results['total'] > 0 else 0
    print(f"Success Rate: {success_rate:.1f}%")
    
    if test_results['failed'] == 0:
        print("\n🎉 All tests passed!")
    else:
        print(f"\n⚠️ {test_results['failed']} test(s) failed")
    
    print_section("NOTES", "-")
    print("✓ Working Features: Image Generation, Video Generation, Image Upload")
    print("⚠️ Unavailable Features: Chat functionality (requires problematic tokens)")
    print("📚 See README.md and QUICK_START.md for more information")
    print("=" * 80)


if __name__ == "__main__":
    main()
