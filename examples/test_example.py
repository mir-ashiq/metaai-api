"""
Simple test to verify VideoGenerator with automatic token fetching.
Only requires cookies - everything else is automatic!
"""

from metaai_api import VideoGenerator

# Test cookies (replace with your actual cookies)
COOKIES = "datr=datrcookie; wd=1536x443; abra_sess=abrasessioncookie; dpr=1.25"

print("="*80)
print("Testing VideoGenerator with Automatic Token Fetching")
print("="*80)

try:
    # Test 1: Initialize with cookies string
    print("\n[Test 1] Initializing with cookies string...")
    video_gen = VideoGenerator(cookies_str=COOKIES)
    print("✅ Initialization successful!")
    print(f"   LSD: {video_gen.lsd}")
    print(f"   FB_DTSG: {video_gen.fb_dtsg[:50]}...")
    
    # Test 2: Quick generate method
    print("\n[Test 2] Testing quick_generate method...")
    result = VideoGenerator.quick_generate(
        cookies_str=COOKIES,
        prompt="Generate a short video of a sunrise",
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
        "datr": "datrcookie",
        "wd": "1536x443",
        "abra_sess": "abrasessioncookie",
        "dpr": "1.25"
    }
    video_gen2 = VideoGenerator(cookies_dict=cookies_dict)
    print("✅ Dictionary initialization successful!")
    
    print("\n" + "="*80)
    print("All tests passed! ✅")
    print("="*80)
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    print("\nMake sure to update COOKIES with your actual browser cookies!")
