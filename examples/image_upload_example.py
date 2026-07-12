"""
Example demonstrating image upload functionality with Meta AI API.

This example shows:
1. How to upload an image using the SDK
2. How to use the uploaded image with prompts
3. API server usage with curl examples
"""

from metaai_api import MetaAI


def example_sdk_usage():
    """Example: Upload image using SDK directly."""
    print("=" * 60)
    print("Example 1: SDK Direct Usage")
    print("=" * 60)
    
    # Initialize MetaAI with your cookies (only 3 required!)
    # Get these from your browser after logging into meta.ai:
    # F12 → Application → Cookies → https://meta.ai
    ai = MetaAI(cookies={
        "datr": "your_datr_cookie",
        "abra_sess": "your_abra_sess_cookie",
        "ecto_1_sess": "your_ecto_1_sess_cookie"
    })
    
    # Upload an image
    print("\n1. Uploading image...")
    result = ai.upload_image("path/to/your/image.jpg")
    
    if result["success"]:
        print(f"✓ Upload successful!")
        print(f"  Media ID: {result['media_id']}")
        print(f"  File: {result['file_name']}")
        print(f"  Size: {result['file_size']} bytes")
        print(f"  Type: {result['mime_type']}")
        
        media_id = result['media_id']
        
        # Now you can use the media_id for various purposes:
        # Note: Integration with prompt() requires additional implementation
        print(f"\n2. Media ID can be used for:")
        print(f"   - Image analysis: Ask questions about the uploaded image")
        print(f"   - Similar image generation: Create variations")
        print(f"   - Video generation: Animate the uploaded image")
        print(f"\n   Stored Media ID: {media_id}")
        
    else:
        print(f"✗ Upload failed: {result.get('error')}")


def example_api_server_usage():
    """Example: Upload image via API server."""
    print("\n" + "=" * 60)
    print("Example 2: API Server Usage")
    print("=" * 60)
    
    print("\nFirst, start the API server:")
    print("  $ python -m metaai_api.api_server")
    print("\nOr with uvicorn:")
    print("  $ uvicorn metaai_api.api_server:app --reload --port 8000")
    
    print("\n" + "-" * 60)
    print("Upload image using curl:")
    print("-" * 60)
    
    curl_example = '''
curl -X POST "http://localhost:8000/upload" \\
  -F "file=@/path/to/your/image.jpg"
'''
    print(curl_example)
    
    print("\n" + "-" * 60)
    print("Upload image using Python requests:")
    print("-" * 60)
    
    python_example = '''
import requests

# Upload an image
with open("path/to/your/image.jpg", "rb") as f:
    files = {"file": f}
    response = requests.post("http://localhost:8000/upload", files=files)
    
result = response.json()

if result["success"]:
    print(f"Media ID: {result['media_id']}")
    # Use media_id for subsequent operations
else:
    print(f"Error: {result['error']}")
'''
    print(python_example)
    
    print("\n" + "-" * 60)
    print("Upload image using JavaScript fetch:")
    print("-" * 60)
    
    js_example = '''
const formData = new FormData();
formData.append('file', fileInput.files[0]);

fetch('http://localhost:8000/upload', {
    method: 'POST',
    body: formData
})
.then(response => response.json())
.then(result => {
    if (result.success) {
        console.log('Media ID:', result.media_id);
        // Use media_id for subsequent operations
    } else {
        console.error('Error:', result.error);
    }
});
'''
    print(js_example)


def example_complete_workflow():
    """Example: Complete workflow with image upload."""
    print("\n" + "=" * 60)
    print("Example 3: Complete Workflow")
    print("=" * 60)
    
    print("""
Step-by-step workflow for using uploaded images:

1. Upload the image
   ├─ Get media_id from response
   └─ Store media_id for later use

2. Use media_id in prompts (Future Implementation)
   ├─ Image Analysis: "What's in this image?" + media_id
   ├─ Similar Images: "Create a similar image" + media_id
   └─ Video Generation: "Animate this image" + media_id

3. Example workflow:
    """)
    
    workflow_example = '''
# Step 1: Upload
ai = MetaAI(cookies=your_cookies)
upload_result = ai.upload_image("photo.jpg")
media_id = upload_result["media_id"]

# Step 2: Analyze (requires prompt() enhancement)
# response = ai.prompt(
#     "What objects can you see in this image?",
#     media_id=media_id
# )
# print(response["message"])

# Step 3: Generate similar image (requires prompt() enhancement)
# response = ai.prompt(
#     "Create a similar image in watercolor style",
#     media_id=media_id
# )

# Step 4: Generate video (requires prompt() enhancement)
# response = ai.prompt(
#     "Create an animated video from this image",
#     media_id=media_id
# )
'''
    print(workflow_example)


def example_error_handling():
    """Example: Proper error handling."""
    print("\n" + "=" * 60)
    print("Example 4: Error Handling")
    print("=" * 60)
    
    error_example = '''
from metaai_api import MetaAI

ai = MetaAI(cookies=your_cookies)

# Example 1: File not found
result = ai.upload_image("nonexistent.jpg")
if not result["success"]:
    print(f"Error: {result['error']}")
    # Output: Error: File not found at nonexistent.jpg

# Example 2: Invalid file type
result = ai.upload_image("document.pdf")
if not result["success"]:
    print(f"Error: {result['error']}")
    # Output: Error: Invalid file type: application/pdf. Only image files are supported.

# Example 3: Missing tokens
ai = MetaAI(cookies={"datr": "only_datr"})
result = ai.upload_image("image.jpg")
if not result["success"]:
    print(f"Error: {result['error']}")
    # Output: Error: Missing required tokens (fb_dtsg, lsd). Please ensure cookies are properly set.

# Example 4: Check before using
result = ai.upload_image("image.jpg")
if result["success"]:
    media_id = result["media_id"]
    # Proceed with media_id
else:
    print(f"Upload failed: {result.get('error')}")
    # Handle error appropriately
'''
    print(error_example)


def main():
    """Run all examples."""
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 10 + "Meta AI Image Upload Examples" + " " * 18 + "║")
    print("╚" + "═" * 58 + "╝")
    
    # Run examples
    example_sdk_usage()
    example_api_server_usage()
    example_complete_workflow()
    example_error_handling()
    
    print("\n" + "=" * 60)
    print("Additional Resources")
    print("=" * 60)
    print("""
📚 Documentation:
   - README.md: Project overview and setup
   - API_SERVER_DEPLOYMENT.md: API server deployment guide
   
🔧 Configuration:
   - Set up .env file with cookies for API server
   - Get cookies from browser after logging into meta.ai
   
⚠️  Important Notes:
   1. Keep your cookies secure and private
   2. Cookies may expire - refresh them periodically
   3. Supported formats: JPEG, PNG, GIF, WEBP
   4. Recommended max size: 10MB
   5. media_id integration with prompt() coming soon
    """)


if __name__ == "__main__":
    main()
