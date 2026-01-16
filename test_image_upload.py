"""
Simple test script to verify image upload functionality.
Run this to test the implementation.
"""

from metaai_api import MetaAI

def test_image_upload():
    """Test the image upload functionality."""
    
    print("=" * 60)
    print("Testing Meta AI Image Upload Functionality")
    print("=" * 60)
    
    # Example cookies - Replace with your actual cookies
    cookies = {
        "datr": "-5pnaePoirB_Y94nHinFXSBj",
        "abra_sess": "FrKF8dSY%2FfECFloYDm9yLVZKdW5VVVJVak13FqbuvJYNAA%3D%3D",
        "lsd": "n9BguAl5LgjHw8eKxIvmI9",
        "fb_dtsg": "NAfvsDdOxl0Tn0BP0IR3ZzZ5WdlIuK0Vd9ICpf4BBv0hKcFugOz3GUQ:45:1768397715",
        "dpr": "1.25",
        "wd": "1528x732",
    }
    
    # Initialize MetaAI
    print("\n1. Initializing MetaAI client...")
    try:
        ai = MetaAI(cookies=cookies)
        print("   ✓ Client initialized successfully")
    except Exception as e:
        print(f"   ✗ Failed to initialize: {e}")
        return
    
    # Test upload with a sample image path
    # IMPORTANT: Replace this with an actual image path on your system
    image_path = r"C:\path\to\your\image.jpg"
    
    print(f"\n2. Attempting to upload image: {image_path}")
    print("   Note: Make sure the file exists and is a valid image")
    
    try:
        result = ai.upload_image(image_path)
        
        print("\n3. Upload Result:")
        print("-" * 60)
        
        if result.get("success"):
            print("   Status: ✓ SUCCESS")
            print(f"   Media ID: {result.get('media_id')}")
            print(f"   Upload Session ID: {result.get('upload_session_id')}")
            print(f"   File Name: {result.get('file_name')}")
            print(f"   File Size: {result.get('file_size')} bytes")
            print(f"   MIME Type: {result.get('mime_type')}")
            
            if "response" in result:
                print(f"\n   Server Response: {result['response']}")
            
            print("\n" + "=" * 60)
            print("✓ Image uploaded successfully!")
            print(f"✓ Use Media ID '{result.get('media_id')}' in your prompts")
            print("=" * 60)
            
            # Demonstrate usage with prompt
            print("\n4. Example: Using media_id in prompts")
            print("-" * 60)
            print("   Now you can use the media_id in your prompts:\n")
            
            media_id = result.get('media_id')
            
            print(f"   # Analyze the image")
            print(f"   response = ai.prompt(")
            print(f"       message='What do you see in this image?',")
            print(f"       media_ids=['{media_id}']")
            print(f"   )")
            print(f"   print(response['message'])\n")
            
            print(f"   # Generate similar image")
            print(f"   response = ai.prompt(")
            print(f"       message='Create a similar image in watercolor style',")
            print(f"       media_ids=['{media_id}']")
            print(f"   )")
            
            print(f"\n   # Generate video from image")
            print(f"   response = ai.prompt(")
            print(f"       message='generate video of this object moving',")
            print(f"       media_ids=['{media_id}']")
            print(f"   )")
            print(f"   if response.get('media'):")
            print(f"       for media in response['media']:")
            print(f"           if media['type'] == 'VIDEO':")
            print(f"               print(f'Video: {{media[\"url\"]}}')")
            
        else:
            print("   Status: ✗ FAILED")
            print(f"   Error: {result.get('error')}")
            
            if "File not found" in result.get('error', ''):
                print("\n   💡 Tip: Update 'image_path' variable with a valid image path")
            elif "Missing required tokens" in result.get('error', ''):
                print("\n   💡 Tip: Update cookies with valid values from your browser")
            
    except Exception as e:
        print(f"\n   ✗ Exception occurred: {e}")
        import traceback
        traceback.print_exc()


def test_api_server():
    """Instructions for testing via API server."""
    print("\n\n" + "=" * 60)
    print("Testing via API Server")
    print("=" * 60)
    
    print("""
To test the API server:

1. Set up environment variables (create .env file):
   META_AI_DATR=your_datr_cookie
   META_AI_ABRA_SESS=your_abra_sess_cookie
   META_AI_DPR=1.25
   META_AI_WD=1528x732

2. Start the server:
   python -m metaai_api.api_server
   
   or
   
   uvicorn metaai_api.api_server:app --reload --port 8000

3. Test upload with curl:
   curl -X POST "http://localhost:8000/upload" \\
     -F "file=@/path/to/image.jpg"

4. Expected response:
   {
     "success": true,
     "media_id": "1595995635158281",
     "upload_session_id": "05c64ee5-1d97-43ba-9cae-0a5381644410",
     "file_name": "image.jpg",
     "file_size": 3310,
     "mime_type": "image/jpeg"
   }

5. Use media_id in prompts:
   # Chat with image
   curl -X POST "http://localhost:8000/chat" \\
     -H "Content-Type: application/json" \\
     -d '{
       "message": "What do you see in this image?",
       "media_ids": ["1595995635158281"]
     }'
   
   # Generate similar image
   curl -X POST "http://localhost:8000/image" \\
     -H "Content-Type: application/json" \\
     -d '{
       "prompt": "Create a similar image in anime style",
       "media_ids": ["1595995635158281"]
     }'
   
   # Generate video from image
   curl -X POST "http://localhost:8000/chat" \\
     -H "Content-Type: application/json" \\
     -d '{
       "message": "generate video of this object moving",
       "media_ids": ["1595995635158281"]
     }'
    """)


if __name__ == "__main__":
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 12 + "Meta AI Image Upload Test" + " " * 20 + "║")
    print("╚" + "═" * 58 + "╝")
    print()
    
    # Test SDK
    test_image_upload()
    
    # Show API server instructions
    test_api_server()
    
    print("\n" + "=" * 60)
    print("Test Complete")
    print("=" * 60)
    print("""
Next Steps:
1. Update cookies with your actual browser cookies
2. Update image_path with a real image file
3. Run this script again to test upload
4. Use the returned media_id in your prompts

For more examples, see: examples/image_upload_example.py
    """)
