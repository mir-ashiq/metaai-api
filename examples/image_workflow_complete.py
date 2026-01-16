"""
Complete Image Upload Workflow Example

Demonstrates all three use cases:
1. Upload image
2. Chat/analyze image
3. Generate similar images
4. Generate video from image
"""

from metaai_api import MetaAI
import os

def main():
    # Initialize Meta AI with cookies
    # Replace these with your actual cookie values
    ai = MetaAI(cookies={
        "datr": os.getenv("META_AI_DATR", "your_datr_cookie"),
        "abra_sess": os.getenv("META_AI_ABRA_SESS", "your_abra_sess_cookie"),
    })
    
    print("=" * 70)
    print("Meta AI - Complete Image Upload Workflow")
    print("=" * 70)
    
    # Step 1: Upload Image
    print("\n📤 Step 1: Uploading image...")
    image_path = "path/to/your/image.jpg"  # Replace with your image path
    
    upload_result = ai.upload_image(image_path)
    
    if not upload_result["success"]:
        print(f"❌ Upload failed: {upload_result['error']}")
        return
    
    media_id = upload_result["media_id"]
    file_size = upload_result["file_size"]
    mime_type = upload_result["mime_type"]
    
    print(f"✅ Upload successful!")
    print(f"   Media ID: {media_id}")
    print(f"   File Size: {file_size} bytes")
    print(f"   MIME Type: {mime_type}")
    
    # Prepare attachment metadata for all operations
    attachment_metadata = {
        'file_size': file_size,
        'mime_type': mime_type
    }
    
    # Step 2: Analyze Image (Chat)
    print("\n💬 Step 2: Analyzing image...")
    
    chat_response = ai.prompt(
        message="What do you see in this image? Describe it in detail.",
        media_ids=[media_id],
        attachment_metadata=attachment_metadata,
        stream=False
    )
    
    print(f"✅ AI Analysis:")
    if isinstance(chat_response, dict):
        print(f"   {chat_response['message'][:200]}...")
    
    # Step 3: Generate Similar Images
    print("\n🎨 Step 3: Generating similar images...")
    
    image_response = ai.prompt(
        message="Create a similar image in watercolor painting style",
        media_ids=[media_id],
        attachment_metadata=attachment_metadata,
        is_image_generation=True,
        stream=False
    )
    
    if isinstance(image_response, dict):
        generated_images = image_response.get('media', [])
        print(f"✅ Generated {len(generated_images)} images:")
        for i, img in enumerate(generated_images, 1):
            print(f"   {i}. {img['type']}: {img['url'][:80]}...")
    
    # Step 4: Generate Video
    print("\n🎬 Step 4: Generating video from image...")
    
    video_result = ai.generate_video(
        prompt="generate a video with zoom in effect on this image",
        media_ids=[media_id],
        attachment_metadata=attachment_metadata,
        wait_before_poll=10,
        max_attempts=30,
        verbose=True
    )
    
    if video_result["success"]:
        print(f"✅ Video generated:")
        print(f"   Conversation ID: {video_result['conversation_id']}")
        print(f"   Video URL: {video_result['video_urls'][0][:80]}...")
    else:
        print(f"❌ Video generation failed: {video_result.get('error', 'Unknown error')}")
    
    print("\n" + "=" * 70)
    print("✅ Workflow complete! All features working.")
    print("=" * 70)


if __name__ == "__main__":
    main()
