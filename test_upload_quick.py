"""
Quick test of image upload with retry logic
"""
import requests
import io
from PIL import Image

def create_test_image():
    """Create a simple test image."""
    img = Image.new('RGB', (256, 256), color=(73, 109, 137))
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG')
    return buffer.getvalue()

def test_upload():
    print("Creating test image...")
    image_data = create_test_image()
    print(f"Test image: {len(image_data)} bytes")
    
    print("\nUploading to http://localhost:8000/upload...")
    files = {'file': ('test.jpg', image_data, 'image/jpeg')}
    
    try:
        resp = requests.post("http://localhost:8000/upload", files=files, timeout=90)
        print(f"Status: {resp.status_code}")
        print(f"Response: {resp.json()}")
        
        if resp.ok and resp.json().get('success'):
            print(f"\n✅ Upload successful! media_id: {resp.json().get('media_id')}")
        else:
            print(f"\n❌ Upload failed: {resp.json().get('error')}")
            
    except Exception as e:
        print(f"\n❌ Exception: {e}")

if __name__ == "__main__":
    test_upload()
