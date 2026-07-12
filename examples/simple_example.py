from metaai_api import MetaAI

# Your cookies from browser - only these 3 are required!
cookies = {
    "datr": "your_datr_cookie",
    "abra_sess": "your_abra_sess_cookie",
    "ecto_1_sess": "your_ecto_1_sess_cookie",  # Optional but recommended
}

print("="*80)
print("Initializing MetaAI...")
print("="*80)

# Initialize with cookie-based authentication
ai = MetaAI(cookies=cookies)

print("\n" + "="*80)
print("WORKING FEATURES:")
print("✅ Image Generation")
print("✅ Video Generation")  
print("✅ Image Upload")
print("\nUNAVAILABLE FEATURES:")
print("⚠️  Chat/Prompt (requires problematic tokens)")
print("="*80)

print("\n" + "="*80)
print("Testing Image Generation")
print("="*80)

# Generate an image
print("\nGenerating image: 'A serene sunset over mountains'")
try:
    image_result = ai.generate_image_new(
        prompt="A serene sunset over mountains",
        orientation="LANDSCAPE",
        num_images=1
    )
    
    if image_result["success"]:
        print(f"\n✅ Image generated successfully!")
        print(f"URLs: {len(image_result['image_urls'])}")
        for i, url in enumerate(image_result['image_urls'], 1):
            print(f"  {i}. {url[:80]}...")
    else:
        print("\n⚠️ Image generation failed")
except Exception as e:
    print(f"❌ Image Generation Error: {e}\n")

print("\n" + "="*80)
print("Testing Video Generation")
print("="*80)

# Generate a video
print("\nGenerating video: 'A peaceful waterfall in a forest'")
try:
    video_result = ai.generate_video_new(
        prompt="A peaceful waterfall in a forest"
    )

    if video_result["success"]:
        print(f"\n✅ Video generated successfully!")
        print(f"Video URLs: {len(video_result['video_urls'])}")
        for i, url in enumerate(video_result['video_urls'], 1):
            print(f"  {i}. {url[:80]}...")
    else:
        print("\n⚠️ Video generation failed")
except Exception as e:
    print(f"❌ Video Generation Error: {e}")

print("\n" + "="*80)
print("Done!")
print("="*80)