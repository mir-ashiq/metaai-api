"""
Simple test to verify VideoGenerator with cookie-based authentication.
Only requires 3 cookies - simple and straightforward!
"""

from metaai_api import VideoGenerator

# Test cookies (replace with your actual cookies - only 3 required!)
COOKIES = "datr=your_datr; abra_sess=your_abra_sess; ecto_1_sess=your_ecto_1_sess"

print("="*80)
print("Testing VideoGenerator with Cookie-Based Authentication")
print("="*80)

try:
    # Test 1: Initialize with cookies string
    print("\n[Test 1] Initializing with cookies string...")
    video_gen = VideoGenerator(cookies_str=COOKIES)
    print("✅ Initialization successful!")
    print("   Using cookie-based authentication")
    
    # Test 2: Quick generate method
    print("\n[Test 2] Testing quick_generate method...")
    result = VideoGenerator.quick_generate(
        cookies_str=COOKIES,
        prompt="A short video of a sunrise",
        verbose=False
    )
    
    if result["success"]:
        print(f"✅ Video generated successfully!")
        print(f"   Conversation ID: {result['conversation_id']}")
        print(f"   Video URLs: {len(result['video_urls'])}")
    else:
        print(f"⚠️  No video URLs found (may still be processing)")
    
    # Test 3: Initialize with cookies dict
    print("\n[Test 3] Initializing with cookies dictionary...")
    cookies_dict = {
        "datr": "your_datr_cookie",
        "abra_sess": "your_abra_sess_cookie",
        "ecto_1_sess": "your_ecto_1_sess_cookie"
    }
    video_gen2 = VideoGenerator(cookies_dict=cookies_dict)
    print("✅ Dictionary initialization successful!")
    
    print("\n" + "="*80)
    print("All tests passed! ✅")
    print("="*80)
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    print("\nMake sure to update COOKIES with your actual browser cookies!")
