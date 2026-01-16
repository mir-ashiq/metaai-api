"""
Complete workflow example: Upload image and use it in prompts.

This demonstrates the full integration of image upload with Meta AI's
chat, image generation, and video generation capabilities.
"""

from typing import Dict, Any, cast
from metaai_api import MetaAI


def complete_workflow_example():
    """Complete workflow: Upload → Analyze → Generate → Create Video."""
    
    print("=" * 70)
    print("Complete Workflow: Upload Image & Use in Prompts")
    print("=" * 70)
    
    # Step 1: Initialize MetaAI
    print("\n[Step 1] Initializing MetaAI...")
    ai = MetaAI(cookies={
        "datr": "your_datr_cookie",
        "abra_sess": "your_abra_sess_cookie",
        "lsd": "your_lsd",
        "fb_dtsg": "your_fb_dtsg",
    })
    print("✓ MetaAI initialized")
    
    # Step 2: Upload an image
    print("\n[Step 2] Uploading image...")
    image_path = "path/to/your/boat.jpg"
    upload_result = ai.upload_image(image_path)
    
    if not upload_result["success"]:
        print(f"✗ Upload failed: {upload_result['error']}")
        return
    
    media_id = upload_result["media_id"]
    print(f"✓ Image uploaded successfully!")
    print(f"  Media ID: {media_id}")
    print(f"  File: {upload_result['file_name']}")
    print(f"  Size: {upload_result['file_size']} bytes")
    
    # Step 3: Ask questions about the uploaded image
    print("\n[Step 3] Analyzing the uploaded image...")
    response = cast(Dict[str, Any], ai.prompt(
        message="What do you see in this image?",
        media_ids=[media_id],
        stream=False
    ))
    print(f"✓ AI Response: {response['message']}")
    
    # Step 4: Generate similar image
    print("\n[Step 4] Generating similar image...")
    response = cast(Dict[str, Any], ai.prompt(
        message="Create a similar image in watercolor painting style",
        media_ids=[media_id],
        stream=False
    ))
    print(f"✓ AI Response: {response['message']}")
    if response.get('media'):
        for media in response['media']:
            print(f"  Generated Image: {media['url']}")
    
    # Step 5: Generate video from uploaded image
    print("\n[Step 5] Generating video from uploaded image...")
    response = cast(Dict[str, Any], ai.prompt(
        message="generate video of this boat coming towards me",
        media_ids=[media_id],
        stream=False
    ))
    print(f"✓ AI Response: {response['message']}")
    if response.get('media'):
        for media in response['media']:
            if media['type'] == 'VIDEO':
                print(f"  Generated Video: {media['url']}")
    
    print("\n" + "=" * 70)
    print("Workflow Complete!")
    print("=" * 70)


def api_server_workflow_example():
    """Example using API server endpoints."""
    
    print("\n" + "=" * 70)
    print("API Server Workflow Example")
    print("=" * 70)
    
    print("""
# Step 1: Upload image
curl -X POST "http://localhost:8000/upload" \\
  -F "file=@boat.jpg"

# Response:
# {
#   "success": true,
#   "media_id": "796999253413659",
#   ...
# }

# Step 2: Analyze uploaded image
curl -X POST "http://localhost:8000/chat" \\
  -H "Content-Type: application/json" \\
  -d '{
    "message": "What do you see in this image?",
    "media_ids": ["796999253413659"]
  }'

# Step 3: Generate similar image
curl -X POST "http://localhost:8000/image" \\
  -H "Content-Type: application/json" \\
  -d '{
    "prompt": "Create a similar image in watercolor style",
    "media_ids": ["796999253413659"]
  }'

# Step 4: Generate video from image
curl -X POST "http://localhost:8000/chat" \\
  -H "Content-Type: application/json" \\
  -d '{
    "message": "generate video of this boat coming towards me",
    "media_ids": ["796999253413659"]
  }'
    """)


def python_requests_example():
    """Example using Python requests library with API server."""
    
    print("\n" + "=" * 70)
    print("Python Requests Example")
    print("=" * 70)
    
    example_code = '''
import requests

API_URL = "http://localhost:8000"

# Step 1: Upload image
with open("boat.jpg", "rb") as f:
    files = {"file": f}
    response = requests.post(f"{API_URL}/upload", files=files)
    upload_result = response.json()

if not upload_result["success"]:
    print(f"Upload failed: {upload_result['error']}")
    exit(1)

media_id = upload_result["media_id"]
print(f"Uploaded! Media ID: {media_id}")

# Step 2: Analyze the image
response = requests.post(f"{API_URL}/chat", json={
    "message": "What do you see in this image?",
    "media_ids": [media_id]
})
result = response.json()
print(f"Analysis: {result['message']}")

# Step 3: Generate similar image
response = requests.post(f"{API_URL}/image", json={
    "prompt": "Create a similar image in anime style",
    "media_ids": [media_id]
})
result = response.json()
print(f"Generated: {result['message']}")
if result.get('media'):
    for media in result['media']:
        print(f"Image URL: {media['url']}")

# Step 4: Generate video from image
response = requests.post(f"{API_URL}/chat", json={
    "message": "generate video of this boat coming towards me",
    "media_ids": [media_id]
})
result = response.json()
print(f"Video: {result['message']}")
if result.get('media'):
    for media in result['media']:
        if media['type'] == 'VIDEO':
            print(f"Video URL: {media['url']}")
    '''
    
    print(example_code)


def advanced_use_cases():
    """Advanced use cases with multiple images."""
    
    print("\n" + "=" * 70)
    print("Advanced Use Cases")
    print("=" * 70)
    
    print("""
# Use Case 1: Multiple images in one prompt
ai = MetaAI(cookies=your_cookies)

# Upload multiple images
media_ids = []
for image_path in ["image1.jpg", "image2.jpg", "image3.jpg"]:
    result = ai.upload_image(image_path)
    if result["success"]:
        media_ids.append(result["media_id"])

# Use multiple images in one prompt
response = ai.prompt(
    message="Compare these images and describe the differences",
    media_ids=media_ids
)
print(response["message"])

# Use Case 2: Iterative refinement
result = ai.upload_image("sketch.jpg")
media_id = result["media_id"]

# First iteration
response = ai.prompt(
    message="Make this sketch more detailed",
    media_ids=[media_id]
)

# Get the new generated image from response
if response.get('media'):
    new_image_url = response['media'][0]['url']
    # Download and upload the new image for further refinement
    # Continue iterating...

# Use Case 3: Image + Video generation pipeline
# 1. Upload reference image
upload_result = ai.upload_image("reference.jpg")
ref_media_id = upload_result["media_id"]

# 2. Generate similar image with modifications
response = ai.prompt(
    message="Create a similar scene but at sunset",
    media_ids=[ref_media_id]
)

# 3. Extract generated image
if response.get('media'):
    generated_image_url = response['media'][0]['url']
    # Download this image and upload again to get its media_id
    
# 4. Generate video from the generated image
# video_response = ai.prompt(
#     message="Animate this sunset scene",
#     media_ids=[new_media_id]
# )
    """)


def best_practices():
    """Best practices for using image upload with prompts."""
    
    print("\n" + "=" * 70)
    print("Best Practices")
    print("=" * 70)
    
    print("""
1. Error Handling
   ✓ Always check upload_result["success"] before using media_id
   ✓ Handle network errors and timeouts gracefully
   ✓ Validate image files before upload

2. Media ID Management
   ✓ Store media_ids for reuse in multiple prompts
   ✓ Media IDs persist across the session
   ✓ Start new_conversation=True to reset context when needed

3. Prompt Engineering
   ✓ Be specific about what you want to do with the image
   ✓ Examples:
     - "Describe what you see in this image"
     - "Create a similar image in [style]"
     - "Generate a video where [action]"
     - "What is the main subject of this image?"

4. Performance Optimization
   ✓ Reuse MetaAI instance for multiple operations
   ✓ Upload images once, use media_id multiple times
   ✓ Use appropriate image sizes (not too large)

5. Security
   ✓ Don't expose media_ids publicly
   ✓ Validate file types before upload
   ✓ Set upload size limits
   ✓ Keep cookies secure

6. API Usage
   ✓ Use /upload endpoint to get media_id
   ✓ Use /chat endpoint for analysis and video generation
   ✓ Use /image endpoint for image generation tasks
   ✓ Check response media array for generated content
    """)


def main():
    """Run all examples."""
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 12 + "Complete Image Upload & Usage Workflow" + " " * 17 + "║")
    print("╚" + "═" * 68 + "╝")
    
    complete_workflow_example()
    api_server_workflow_example()
    python_requests_example()
    advanced_use_cases()
    best_practices()
    
    print("\n" + "=" * 70)
    print("Summary")
    print("=" * 70)
    print("""
The complete workflow:
1. Upload image → Get media_id
2. Use media_id in prompts for:
   ✓ Image analysis ("What's in this image?")
   ✓ Similar image generation ("Create similar image in [style]")
   ✓ Video generation ("Generate video of [action]")
   ✓ Image comparison ("Compare these images")
   ✓ And more...

Key Points:
- media_id goes in the attachmentsV2 array
- Can use multiple media_ids in one prompt
- Works with /chat, /image endpoints
- Entrypoint changes to KADABRA__CHAT__UNIFIED_INPUT_BAR
- Media content returned in response['media'] array

For more information:
- README.md
- IMAGE_UPLOAD_README.md
- API_SERVER_DEPLOYMENT.md
    """)


if __name__ == "__main__":
    main()
