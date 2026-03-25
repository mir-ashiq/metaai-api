#!/usr/bin/env python3
"""
Comprehensive Image and Video Generation Test
Tests all orientations and multiple prompts
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from metaai_api import MetaAI

def print_header(title):
    """Print formatted header"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80 + "\n")

def print_section(title):
    """Print formatted section"""
    print(f"\n{title}")
    print("─" * 80)

def test_image_orientations():
    """Test image generation with all orientations"""
    print_header("IMAGE GENERATION - ALL ORIENTATIONS")

    ai = MetaAI()

    test_cases = [
        ("VERTICAL", "a tall portrait of a cat"),
        ("LANDSCAPE", "a wide mountain landscape with lake"),
        ("SQUARE", "a mandala pattern"),
    ]

    results = {}

    for orientation, prompt in test_cases:
        print_section(f"📸 Orientation: {orientation}")
        print(f"Prompt: {prompt}\n")

        try:
            start_time = time.time()
            print("⏳ Generating...")

            result = ai.generate_image_new(
                prompt=prompt,
                orientation=orientation,
                num_images=1
            )

            elapsed = time.time() - start_time

            success = result.get('success')
            image_urls = result.get('image_urls', [])

            print(f"✅ Generated in {elapsed:.1f}s")
            print(f"   Success: {success}")
            print(f"   Images: {len(image_urls)}")

            if image_urls:
                print(f"\n   URLs:")
                for i, url in enumerate(image_urls, 1):
                    print(f"   {i}. {url[:75]}...")

            results[orientation] = {
                'success': success,
                'count': len(image_urls),
                'urls': image_urls
            }

        except Exception as e:
            print(f"❌ Error: {e}")
            results[orientation] = {'success': False, 'error': str(e)}

        time.sleep(1)

    return results

def test_video_generation():
    """Test video generation with various prompts"""
    print_header("VIDEO GENERATION - MULTIPLE PROMPTS")

    ai = MetaAI()

    test_prompts = [
        "a golden retriever running on the beach",
        "a galaxy with planets and stars",
        "a person painting a mural",
        "waves crashing on a rocky shore",
    ]

    results = {}

    for i, prompt in enumerate(test_prompts, 1):
        print_section(f"🎬 Video {i}/{len(test_prompts)}")
        print(f"Prompt: {prompt}\n")

        try:
            start_time = time.time()
            print("⏳ Submitting video request...")

            result = ai.generate_video_new(
                prompt=prompt,
                auto_poll=False
            )

            elapsed = time.time() - start_time

            success = result.get('success')
            video_urls = result.get('video_urls', [])
            conversation_id = result.get('conversation_id')

            print(f"✅ Submitted in {elapsed:.1f}s")
            print(f"   Success: {success}")
            print(f"   Conversation: {conversation_id}")
            print(f"   Videos: {len(video_urls)}")

            if video_urls:
                print(f"\n   Video URLs:")
                for j, url in enumerate(video_urls, 1):
                    print(f"   {j}. {url}")

            results[prompt] = {
                'success': success,
                'count': len(video_urls),
                'urls': video_urls,
                'conversation_id': conversation_id
            }

        except Exception as e:
            print(f"❌ Error: {e}")
            results[prompt] = {'success': False, 'error': str(e)}

        time.sleep(1)

    return results

def test_mixed_generation():
    """Test both image and video in sequence"""
    print_header("MIXED TEST - IMAGE THEN VIDEO")

    ai = MetaAI()

    test_case = {
        'image': {
            'prompt': 'a futuristic robot in a neon city',
            'orientation': 'LANDSCAPE'
        },
        'video': {
            'prompt': 'Animate the futuristic robot walking'
        }
    }

    results = {}

    # Test image
    print_section("📸 Step 1: Generate Image")
    print(f"Prompt: {test_case['image']['prompt']}")
    print(f"Orientation: {test_case['image']['orientation']}\n")

    try:
        start_time = time.time()
        print("⏳ Generating image...")

        img_result = ai.generate_image_new(
            prompt=test_case['image']['prompt'],
            orientation=test_case['image']['orientation'],
            num_images=1
        )

        elapsed = time.time() - start_time
        img_urls = img_result.get('image_urls', [])

        print(f"✅ Image generated in {elapsed:.1f}s")
        print(f"   Count: {len(img_urls)}")
        if img_urls:
            print(f"   URL: {img_urls[0][:75]}...")

        results['image'] = {
            'success': img_result.get('success'),
            'count': len(img_urls),
            'urls': img_urls
        }

    except Exception as e:
        print(f"❌ Error: {e}")
        results['image'] = {'success': False, 'error': str(e)}

    time.sleep(2)

    # Test video
    print_section("🎬 Step 2: Generate Video")
    print(f"Prompt: {test_case['video']['prompt']}\n")

    try:
        start_time = time.time()
        print("⏳ Generating video...")

        vid_result = ai.generate_video_new(
            prompt=test_case['video']['prompt'],
            auto_poll=False
        )

        elapsed = time.time() - start_time
        vid_urls = vid_result.get('video_urls', [])

        print(f"✅ Video submitted in {elapsed:.1f}s")
        print(f"   Count: {len(vid_urls)}")
        if vid_urls:
            print(f"   URL: {vid_urls[0]}")

        results['video'] = {
            'success': vid_result.get('success'),
            'count': len(vid_urls),
            'urls': vid_urls
        }

    except Exception as e:
        print(f"❌ Error: {e}")
        results['video'] = {'success': False, 'error': str(e)}

    return results

def print_summary(image_results, video_results, mixed_results):
    """Print summary of all tests"""
    print_header("TEST SUMMARY")

    print("IMAGE GENERATION (Orientations):")
    print("─" * 80)
    for orientation, result in image_results.items():
        status = "✅" if result.get('success') else "❌"
        count = result.get('count', 0)
        print(f"{status} {orientation:12} - {count} images generated")

    print("\n\nVIDEO GENERATION (Multiple Prompts):")
    print("─" * 80)
    for i, (prompt, result) in enumerate(video_results.items(), 1):
        status = "✅" if result.get('success') else "❌"
        count = result.get('count', 0)
        print(f"{status} Video {i} - {count} videos generated")
        print(f"   Prompt: {prompt[:60]}...")

    print("\n\nMIXED TEST (Image → Video):")
    print("─" * 80)
    img_ok = "✅" if mixed_results['image'].get('success') else "❌"
    vid_ok = "✅" if mixed_results['video'].get('success') else "❌"
    print(f"{img_ok} Image: {mixed_results['image'].get('count', 0)} images")
    print(f"{vid_ok} Video: {mixed_results['video'].get('count', 0)} videos")

    print("\n")

def main():
    """Run all tests"""
    print("\n" + "█"*80)
    print("█" + " "*78 + "█")
    print("█" + "  COMPREHENSIVE IMAGE & VIDEO GENERATION TEST".center(78) + "█")
    print("█" + " "*78 + "█")
    print("█"*80)

    try:
        # Run all tests
        image_results = test_image_orientations()
        video_results = test_video_generation()
        mixed_results = test_mixed_generation()

        # Print summary
        print_summary(image_results, video_results, mixed_results)

        print("█"*80)
        print("█" + "  ALL TESTS COMPLETE".center(78) + "█")
        print("█"*80 + "\n")

    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
