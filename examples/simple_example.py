from metaai_api import MetaAI

# Your cookies from browser (lsd and fb_dtsg are auto-fetched!)
cookies = {
    "datr": "datrcookie",
    "abra_sess": "abrasessioncookie",
    "dpr": "1.25",
    "wd": "1536x443"
}

print("="*80)
print("Initializing MetaAI...")
print("="*80)

# Initialize once - tokens are automatically fetched
ai = MetaAI(cookies=cookies)

print("\n" + "="*80)
print("Testing Chat Feature")
print("="*80)

# Use for chat
print("\nAsking: What's the weather in San Francisco?")
try:
    chat = ai.prompt("What's the weather in San Francisco?", stream=False)
    print(f"\n✅ Chat Response:\n{chat['message'][:200]}...\n")
except Exception as e:
    print(f"❌ Chat Error: {e}\n")

print("="*80)
print("Testing Video Generation")
print("="*80)

# Use for video generation
print("\nGenerating video: 'Generate a video of a sunset over mountains'")
try:
    video = ai.generate_video("Generate a video of a sunset over mountains")

    if video["success"]:
        print(f"\n✅ Video generated successfully!")
        print(f"Conversation ID: {video['conversation_id']}")
        print(f"Video URLs: {len(video['video_urls'])}")
        for i, url in enumerate(video['video_urls'], 1):
            print(f"  {i}. {url[:80]}...")
    else:
        print("\n⚠️ No video URLs found (may still be processing)")
except Exception as e:
    print(f"❌ Video Generation Error: {e}")

print("\n" + "="*80)
print("Done!")
print("="*80)