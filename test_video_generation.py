#!/usr/bin/env python3
"""
Simple Video Generation Test Script
Tests Meta AI video generation with real-time output
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from metaai_api import MetaAI

def test_video_generation():
    """Test video generation with multiple prompts"""

    print("\n" + "="*80)
    print("  VIDEO GENERATION TEST")
    print("="*80 + "\n")

    ai = MetaAI()

    test_prompts = [
        "a cat walking through a garden",
        "a spaceship flying through stars",
        "a person dancing in the rain",
    ]

    for i, prompt in enumerate(test_prompts, 1):
        print(f"\n{'─'*80}")
        print(f"Test {i}/3: {prompt}")
        print(f"{'─'*80}\n")

        try:
            # Generate video
            print(f"⏳ Submitting video generation request...")
            start_time = time.time()

            result = ai.generate_video_new(
                prompt=prompt,
                auto_poll=False  # Just submit, don't wait
            )

            elapsed = time.time() - start_time

            # Show results
            print(f"✅ Request submitted in {elapsed:.1f}s")
            print(f"   Status: {result.get('success')}")
            print(f"   Conversation: {result.get('conversation_id')}")
            print(f"   Processing: {result.get('processing')}")

            # Show video URLs
            video_urls = result.get('video_urls', [])
            if video_urls:
                print(f"\n✅ VIDEO URLs ({len(video_urls)} generated):")
                for j, url in enumerate(video_urls, 1):
                    print(f"   {j}. {url}")
            else:
                print(f"\n⚠️  No video URLs returned")

            # Show video objects
            video_objects = result.get('video_objects', [])
            if video_objects:
                print(f"\n📊 Video Objects ({len(video_objects)}):")
                for j, obj in enumerate(video_objects, 1):
                    print(f"   {j}. ID: {obj.get('id')}")
                    print(f"      Filename: {obj.get('downloadableFileName')}")
                    if obj.get('sourceMedia'):
                        src = obj['sourceMedia']
                        print(f"      Source Image: {src.get('url', 'N/A')[:70]}...")

        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

        if i < len(test_prompts):
            print(f"\n⏳ Waiting 2 seconds before next test...")
            time.sleep(2)

    print("\n" + "="*80)
    print("  TEST COMPLETE")
    print("="*80 + "\n")

if __name__ == "__main__":
    test_video_generation()
