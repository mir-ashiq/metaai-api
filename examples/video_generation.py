"""
Complete example using MetaAI class for video generation.
This demonstrates the simplified API where MetaAI handles everything.
"""

from metaai_api import MetaAI
import json

# Your cookies (get from browser - only 3 required!)
cookies = {
    "datr": "your_datr_cookie",
    "abra_sess": "your_abra_sess_cookie",
    "ecto_1_sess": "your_ecto_1_sess_cookie"
}

print("="*80)
print("META AI VIDEO GENERATION - Simplified API")
print("="*80)

# Initialize MetaAI once
ai = MetaAI(cookies=cookies)

# Example 1: Generate a single video
print("\n[Example 1] Generate Single Video")
print("-" * 80)

prompt = "Generate a realistic video of a beautiful sunset over the ocean"
print(f"Prompt: {prompt}\n")

result = ai.generate_video_new(prompt)

if result["success"]:
    print(f"✅ Success!")
    print(f"   Conversation ID: {result['conversation_id']}")
    print(f"   Video URLs: {len(result['video_urls'])}")
    for i, url in enumerate(result['video_urls'], 1):
        print(f"   {i}. {url[:80]}...")
    
    # Save to file
    output_file = f"video_{result['conversation_id']}.json"
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)
    print(f"\n   Saved to: {output_file}")
else:
    print("❌ Failed to generate video")
    if "error" in result:
        print(f"   Error: {result['error']}")


# Example 2: Generate multiple videos with custom settings
print("\n[Example 2] Generate Multiple Videos")
print("-" * 80)

prompts = [
    "Generate a video of a cat playing piano",
    "Generate a video of dolphins swimming in the ocean",
    "Generate a video of fireworks at night"
]

for i, prompt in enumerate(prompts, 1):
    print(f"\n{i}. Generating: {prompt}")
    
    result = ai.generate_video_new(prompt=prompt)
    
    if result["success"]:
        print(f"   ✅ Success! {len(result['video_urls'])} video(s) generated")
    else:
        print(f"   ⚠️  No videos yet (may still be processing)")


# Example 3: Simple video generation with different prompt
print("\n[Example 3] Another Video Example")
print("-" * 80)

print("\nGenerating video...")
video_result = ai.generate_video_new(
    "A waterfall in a tropical rainforest"
)

if video_result["success"]:
    print(f"✅ Video generated: {video_result['video_urls'][0][:80]}...")


# Example 4: Error handling
print("\n[Example 4] Error Handling")
print("-" * 80)

try:
    result = ai.generate_video_new(
        prompt="A peaceful mountain landscape"
    )
    
    if not result["success"]:
        print("⚠️  No videos found. Check your cookies and try again.")

except Exception as e:
    print(f"❌ Error: {e}")


print("\n" + "="*80)
print("Examples Complete!")
print("="*80)
print("\n💡 Key Features:")
print("   • MetaAI class handles everything")
print("   • Cookie-based authentication (no tokens needed)")
print("   • Simple generate_video_new() interface")
print("   • Easy error handling")
print("\n📝 Basic Usage:")
print("   ai = MetaAI(cookies=cookies)")
print("   result = ai.generate_video_new('your prompt')")
