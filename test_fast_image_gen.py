#!/usr/bin/env python3
"""
Test the improved image generation with the new fast doc_id
"""
import time
from metaai_api import MetaAI

print("=" * 70)
print("Testing Fast Image Generation")
print("=" * 70)
print()

try:
    print("Initializing MetaAI...")
    ai = MetaAI()
    
    if not ai.access_token:
        print("❌ No access token - this will affect performance")
    else:
        print(f"✅ Access token loaded: {ai.access_token[:50]}...")
    
    print()
    print("Generating image with prompt: 'cat in space'")
    print("Using new fast doc_id from fast-image.py...")
    print()
    
    start_time = time.time()
    
    result = ai.generate_image_new(
        prompt="cat in space",
        orientation="VERTICAL",
        num_images=1,
        fetch_urls=True
    )
    
    elapsed = time.time() - start_time
    
    print()
    print("=" * 70)
    print(f"Generation completed in {elapsed:.2f} seconds")
    print("=" * 70)
    print()
    
    if result.get('success'):
        print("✅ SUCCESS")
        image_urls = result.get('image_urls', [])
        print(f"   Generated {len(image_urls)} image(s)")
        
        for i, url in enumerate(image_urls, 1):
            print(f"   Image {i}: {url[:100]}...")
        
        if elapsed < 30:
            print()
            print("🚀 FAST! Image generation completed in under 30 seconds!")
            print("   This means the new doc_id is working correctly.")
        elif elapsed < 60:
            print()
            print("⚡ IMPROVED! Generation took under 1 minute.")
        else:
            print()
            print("⚠️  Still slow - took over 1 minute")
            print("   Check server logs for SSE parsing details")
    else:
        print("❌ FAILED")
        print(f"   Error: {result.get('error', 'Unknown error')}")
    
    print()
    
except Exception as e:
    print()
    print(f"❌ ERROR: {e}")
    print()
    import traceback
    traceback.print_exc()
