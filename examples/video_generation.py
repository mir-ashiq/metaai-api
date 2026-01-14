"""
Complete example using MetaAI class for video generation.
This demonstrates the simplified API where MetaAI handles everything.
"""

from metaai_api import MetaAI
import json

# Your cookies (get from browser)
cookies = {
    "datr": "datrcookie",
    "wd": "1536x443",
    "abra_sess": "abrasessioncookie",
    "dpr": "1.25"
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

result = ai.generate_video(prompt)

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
    
    result = ai.generate_video(
        prompt=prompt,
        wait_before_poll=5,    # Wait 5 seconds before polling
        max_attempts=20,       # Try 20 times
        wait_seconds=5,        # 5 seconds between attempts
        verbose=False          # Don't print detailed status
    )
    
    if result["success"]:
        print(f"   ✅ Success! {len(result['video_urls'])} video(s) generated")
    else:
        print(f"   ⚠️  No videos yet (may still be processing)")


# Example 3: Combine text chat with video generation
print("\n[Example 3] Chat + Video Generation")
print("-" * 80)

# First, have a text conversation
print("\nAsking Meta AI for ideas...")
chat_response = ai.prompt(
    "Give me 3 creative video ideas for nature scenes",
    stream=False
)
print(f"Meta AI says: {chat_response['message'][:200]}...")

# Then generate a video based on one of the ideas
print("\nGenerating video from first idea...")
video_result = ai.generate_video(
    "Generate a video of a waterfall in a tropical rainforest"
)

if video_result["success"]:
    print(f"✅ Video generated: {video_result['video_urls'][0][:80]}...")


# Example 4: Error handling
print("\n[Example 4] Error Handling")
print("-" * 80)

try:
    result = ai.generate_video(
        prompt="Generate a video",
        wait_before_poll=2,
        max_attempts=3,  # Very short timeout
        verbose=False
    )
    
    if not result["success"]:
        print("⚠️  No videos found yet. Try again with longer timeout:")
        print("   result = ai.generate_video(prompt, max_attempts=30, wait_seconds=5)")

except Exception as e:
    print(f"❌ Error: {e}")


print("\n" + "="*80)
print("Examples Complete!")
print("="*80)
print("\n💡 Key Features:")
print("   • MetaAI class handles everything")
print("   • Automatic token fetching (lsd, fb_dtsg)")
print("   • Same interface for chat and video generation")
print("   • Easy error handling")
print("\n📝 Basic Usage:")
print("   ai = MetaAI(cookies=cookies)")
print("   result = ai.generate_video('your prompt')")
