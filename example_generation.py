"""
Quick example demonstrating the new image and video generation features.
"""

from metaai_api import MetaAI

# Example cookies (replace with your actual cookies from meta.ai)
cookies = {
    'datr': 'your_datr_cookie',
    'abra_sess': 'your_abra_sess_cookie',
    'dpr': '1',
    'wd': '1920x1080'
    # Optional but recommended:
    # 'c_user': 'your_c_user',
    # 'xs': 'your_xs',
    # 'fr': 'your_fr'
}

# Initialize Meta AI client
ai = MetaAI(cookies=cookies)

# Example 1: Generate an image
print("\n=== Image Generation ===")
image_result = ai.generate_image_new(
    prompt="A futuristic cityscape at sunset",
    orientation="VERTICAL",  # Options: VERTICAL, HORIZONTAL, SQUARE
    num_images=1
)

if image_result['success']:
    print(f"✅ Successfully generated {len(image_result['image_urls'])} image(s)")
    for i, url in enumerate(image_result['image_urls'], 1):
        print(f"   Image {i}: {url}")
else:
    print(f"❌ Image generation failed: {image_result.get('error')}")

# Example 2: Generate a video
print("\n=== Video Generation ===")
video_result = ai.generate_video_new(
    prompt="A robot dancing in a neon-lit city"
)

if video_result['success']:
    print(f"✅ Successfully generated {len(video_result['video_urls'])} video(s)")
    for i, url in enumerate(video_result['video_urls'], 1):
        print(f"   Video {i}: {url}")
else:
    print(f"❌ Video generation failed: {video_result.get('error')}")

# Example 3: Generate with different orientations
print("\n=== Different Orientations ===")
orientations = ["VERTICAL", "HORIZONTAL", "SQUARE"]
for orientation in orientations:
    result = ai.generate_image_new(
        prompt="Abstract art",
        orientation=orientation
    )
    if result['success']:
        print(f"✅ {orientation}: {len(result['image_urls'])} image(s)")
    else:
        print(f"❌ {orientation}: Failed")
