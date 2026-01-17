# Image Upload Feature Documentation

## Overview

The Meta AI API now supports **uploading images** for use in:

- 💬 **Chat/Image Analysis** - Analyze and describe uploaded images
- 🎨 **Similar Image Generation** - Create variations of uploaded images
- 🎬 **Video Generation** - Animate uploaded images with AI-generated videos

This feature uses Meta's rupload protocol with automatic `media_id` management and `attachment_metadata` (file size + MIME type) for all operations.

## Features

✅ Upload images to Meta AI  
✅ Support for JPEG, PNG, GIF, and other image formats  
✅ **Chat**: Analyze and describe images  
✅ **Image Generation**: Create similar images in different styles  
✅ **Video Generation**: Animate static images  
✅ Automatic MIME type detection and file size tracking  
✅ UUID-based upload session management  
✅ SDK and API server support  
✅ Comprehensive error handling

## Installation

The image upload functionality is included in the main package:

```bash
pip install metaai-sdk
```

Or install from source:

```bash
git clone https://github.com/mir-ashiq/metaai-api.git
cd metaai-api
pip install -e .
```

## Quick Start

### SDK Usage - Complete Workflow

```python
from metaai_api import MetaAI

# Initialize with your cookies
ai = MetaAI(cookies={
    "datr": "your_datr_cookie",
    "abra_sess": "your_abra_sess_cookie",
})

# Step 1: Upload an image
result = ai.upload_image("path/to/image.jpg")

if result["success"]:
    media_id = result["media_id"]
    file_size = result["file_size"]
    mime_type = result["mime_type"]
    print(f"✓ Uploaded: {media_id}")

    # Step 2: Analyze the image (Chat)
    response = ai.prompt(
        message="What do you see in this image? Describe it in detail.",
        media_ids=[media_id],
        attachment_metadata={'file_size': file_size, 'mime_type': mime_type}
    )
    print(f"Analysis: {response['message']}")

    # Step 3: Generate similar images
    response = ai.prompt(
        message="Create a similar image in watercolor painting style",
        media_ids=[media_id],
        attachment_metadata={'file_size': file_size, 'mime_type': mime_type},
        is_image_generation=True
    )
    for i, media in enumerate(response['media'], 1):
        print(f"Generated Image {i}: {media['url']}")

    # Step 4: Generate video from image
    video_result = ai.generate_video(
        prompt="generate a video with zoom in effect on this image",
        media_ids=[media_id],
        attachment_metadata={'file_size': file_size, 'mime_type': mime_type}
    )
    if video_result["success"]:
        print(f"Video: {video_result['video_urls'][0]}")
else:
    print(f"Error: {result['error']}")
```

````

### API Server Usage

1. **Set up environment variables** (`.env` file):

```env
META_AI_DATR=your_datr_cookie
META_AI_ABRA_SESS=your_abra_sess_cookie
META_AI_DPR=1.25
META_AI_WD=1528x732
````

2. **Start the server**:

```bash
python -m uvicorn metaai_api.api_server:app --host 0.0.0.0 --port 8000
```

3. **Complete API Workflow**:

```bash
# Step 1: Upload Image
curl -X POST "http://localhost:8000/upload" \
  -F "file=@/path/to/image.jpg"
# Response: {"success": true, "media_id": "1453149056374564", "file_size": 3310, "mime_type": "image/jpeg", ...}

# Step 2: Analyze Image (Chat)
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What do you see in this image?",
    "media_ids": ["1453149056374564"],
    "attachment_metadata": {"file_size": 3310, "mime_type": "image/jpeg"}
  }'
# Response: {"message": "The image captures a serene lake scene...", "sources": [], "media": []}

# Step 3: Generate Similar Images
curl -X POST "http://localhost:8000/image" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Create a similar image in watercolor painting style",
    "media_ids": ["1453149056374564"],
    "attachment_metadata": {"file_size": 3310, "mime_type": "image/jpeg"}
  }'
# Response: {"message": "", "sources": [], "media": [{"url": "https://...", "type": "IMAGE"}, ...]}

# Step 4: Generate Video from Image
curl -X POST "http://localhost:8000/video" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "generate a video with zoom in effect on this image",
    "media_ids": ["1453149056374564"],
    "attachment_metadata": {"file_size": 3310, "mime_type": "image/jpeg"}
  }'
# Response: {"success": true, "video_urls": ["https://..."], ...}
```

4. **Python API Client Example**:

```python
import requests

# Upload
with open("image.jpg", "rb") as f:
    upload_resp = requests.post("http://localhost:8000/upload", files={"file": f})
upload_data = upload_resp.json()
media_id = upload_data["media_id"]
metadata = {
    "file_size": upload_data["file_size"],
    "mime_type": upload_data["mime_type"]
}

# Chat
chat_resp = requests.post("http://localhost:8000/chat", json={
    "message": "What's in this image?",
    "media_ids": [media_id],
    "attachment_metadata": metadata
})
print(chat_resp.json()["message"])

# Generate Images
image_resp = requests.post("http://localhost:8000/image", json={
    "prompt": "Create similar in anime style",
    "media_ids": [media_id],
    "attachment_metadata": metadata
})
for media in image_resp.json()["media"]:
    print(media["url"])

# Generate Video
video_resp = requests.post("http://localhost:8000/video", json={
    "prompt": "animate this image with cinematic motion",
    "media_ids": [media_id],
    "attachment_metadata": metadata
})
print(video_resp.json()["video_urls"][0])
```

````

## API Reference

### `MetaAI.upload_image(file_path: str) -> Dict`

Upload an image file to Meta AI.

**Parameters:**

- `file_path` (str): Path to the local image file

**Returns:**

- `Dict` containing:
  - `success` (bool): Whether the upload succeeded
  - `media_id` (str): The uploaded image's media ID (if successful)
  - `upload_session_id` (str): Unique upload session ID
  - `file_name` (str): Original filename
  - `file_size` (int): File size in bytes (required for prompts)
  - `mime_type` (str): MIME type of the image (required for prompts)
  - `error` (str): Error message (if failed)

**Example:**

```python
result = ai.upload_image("photo.jpg")

if result["success"]:
    media_id = result["media_id"]
    file_size = result["file_size"]
    mime_type = result["mime_type"]

    # Use in chat/analysis
    response = ai.prompt(
        message="Describe this image",
        media_ids=[media_id],
        attachment_metadata={'file_size': file_size, 'mime_type': mime_type}
    )
    print(response["message"])
else:
    print(f"Upload failed: {result['error']}")
````

### `MetaAI.prompt()` with Images

Use uploaded images in prompts for chat, analysis, or image generation.

**Parameters:**

- `message` (str): Your prompt/question
- `media_ids` (list): List of media IDs from uploaded images
- `attachment_metadata` (dict): **Required** - `{'file_size': int, 'mime_type': str}`
- `is_image_generation` (bool): Set True for image generation (optional)

**Example:**

```python
# Chat/Analysis
response = ai.prompt(
    message="What objects are in this image?",
    media_ids=["1453149056374564"],
    attachment_metadata={'file_size': 3310, 'mime_type': 'image/jpeg'}
)
print(response["message"])  # Text response

# Image Generation
response = ai.prompt(
    message="Create similar in cyberpunk style",
    media_ids=["1453149056374564"],
    attachment_metadata={'file_size': 3310, 'mime_type': 'image/jpeg'},
    is_image_generation=True
)
for img in response["media"]:
    print(img["url"])  # 4 generated image URLs
```

### `MetaAI.generate_video()` with Images

Generate videos from uploaded images.

**Parameters:**

- `prompt` (str): Video generation prompt
- `media_ids` (list): List of media IDs from uploaded images
- `attachment_metadata` (dict): **Required** - `{'file_size': int, 'mime_type': str}`

**Example:**

```python
result = ai.generate_video(
    prompt="generate a video with zoom in effect",
    media_ids=["1453149056374564"],
    attachment_metadata={'file_size': 3310, 'mime_type': 'image/jpeg'}
)
if result["success"]:
    print(result["video_urls"][0])
```

## Response Format

### Success Response

```json
{
  "success": true,
  "media_id": "1595995635158281",
  "upload_session_id": "05c64ee5-1d97-43ba-9cae-0a5381644410",
  "file_name": "photo.jpg",
  "file_size": 3310,
  "mime_type": "image/jpeg",
  "response": {
    "media_id": "1595995635158281"
  }
}
```

### Error Response

```json
{
  "success": false,
  "error": "File not found at /path/to/image.jpg"
}
```

## Supported Image Formats

- JPEG (`.jpg`, `.jpeg`)
- PNG (`.png`)
- GIF (`.gif`)
- WEBP (`.webp`)
- Other formats supported by `mimetypes` module

## Error Handling

The upload method returns detailed error messages for various scenarios:

### File Not Found

```python
result = ai.upload_image("nonexistent.jpg")
# Error: File not found at nonexistent.jpg
```

### Invalid File Type

```python
result = ai.upload_image("document.pdf")
# Error: Invalid file type: application/pdf. Only image files are supported.
```

### Missing Tokens

```python
ai = MetaAI(cookies={"datr": "only_datr"})
result = ai.upload_image("image.jpg")
# Error: Missing required tokens (fb_dtsg, lsd). Please ensure cookies are properly set.
```

## Getting Cookies

To use the image upload feature, you need valid Meta AI cookies. Here's how to get them:

1. **Open your browser** (Chrome, Edge, Firefox)
2. **Navigate to** https://www.meta.ai/
3. **Log in** if required
4. **Open Developer Tools** (F12)
5. **Go to Application/Storage → Cookies**
6. **Copy the values** for:
   - `datr`
   - `abra_sess`
   - `lsd` (optional, will auto-fetch)
   - `fb_dtsg` (optional, will auto-fetch)

## Upload Process Flow

The image upload follows Meta's rupload protocol:

```
1. Generate UUID session ID
   ↓
2. Perform GET handshake (check if session exists)
   ↓
3. POST image data with headers:
   - x-entity-length: file size
   - x-entity-name: filename
   - x-entity-type: MIME type
   - desired_upload_handler: genai_document
   ↓
4. Receive media_id from server
   ↓
5. Use media_id in prompts/operations
```

## Advanced Usage

### Custom Session Parameters

```python
from metaai_api.image_upload import ImageUploader

uploader = ImageUploader(session, cookies)
result = uploader.upload_image(
    file_path="image.jpg",
    fb_dtsg="your_fb_dtsg",
    jazoest="your_jazoest",
    lsd="your_lsd",
    rev="1032041898",  # Optional
    s="custom_session",  # Optional
    hsi="custom_hsi"  # Optional
)
```

### Batch Upload

```python
import os
from metaai_api import MetaAI

ai = MetaAI(cookies=your_cookies)

image_dir = "path/to/images"
media_ids = []

for filename in os.listdir(image_dir):
    if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
        file_path = os.path.join(image_dir, filename)
        result = ai.upload_image(file_path)

        if result["success"]:
            media_ids.append({
                "filename": filename,
                "media_id": result["media_id"]
            })
            print(f"✓ {filename}: {result['media_id']}")
        else:
            print(f"✗ {filename}: {result['error']}")

print(f"\nUploaded {len(media_ids)} images successfully")
```

## Future Enhancements

The following features are planned for future releases:

- [ ] Integration of `media_id` with `prompt()` method for image analysis
- [ ] Support for using uploaded images in similar image generation
- [ ] Support for using uploaded images in video generation
- [ ] Batch upload optimization
- [ ] Upload progress callbacks
- [ ] Image preprocessing (resize, compression)

## Troubleshooting

### Upload Returns 400 Error

**Issue:** Server returns 400 Bad Request

**Solution:**

- Refresh your cookies (they may have expired)
- Ensure all required tokens are present
- Check that the image file is valid

### Upload Returns 401/403 Error

**Issue:** Authentication failure

**Solution:**

- Log in to meta.ai in your browser
- Get fresh cookies
- Ensure `abra_sess` cookie is valid

### "Missing required tokens" Error

**Issue:** `fb_dtsg` or `lsd` tokens are missing

**Solution:**

- The SDK will auto-fetch these tokens if you provide `datr` and `abra_sess`
- Manually add them to your cookies dict if auto-fetch fails

### Large File Upload Fails

**Issue:** Upload times out or fails for large images

**Solution:**

- Resize images before upload (recommended max: 10MB)
- Use compression tools to reduce file size
- Check your network connection

## Examples

See the following files for complete examples:

- `examples/image_upload_example.py` - Comprehensive examples
- `test_image_upload.py` - Simple test script

## API Endpoints

### POST `/upload`

Upload an image file.

**Request:**

- Method: `POST`
- Content-Type: `multipart/form-data`
- Body: `file` (image file)

**Response:**

```json
{
  "success": true,
  "media_id": "1595995635158281",
  "upload_session_id": "05c64ee5-1d97-43ba-9cae-0a5381644410",
  "file_name": "image.jpg",
  "file_size": 3310,
  "mime_type": "image/jpeg"
}
```

## Security Considerations

⚠️ **Important Security Notes:**

1. **Never commit cookies to version control**
2. **Store cookies in environment variables or secure vaults**
3. **Refresh cookies periodically** (they expire)
4. **Use HTTPS** when deploying API server
5. **Implement rate limiting** for production deployments
6. **Validate file sizes** to prevent abuse

## License

This feature is part of the Meta AI API package and is licensed under the MIT License.

## Support

For issues, questions, or contributions:

- GitHub Issues: https://github.com/mir-ashiq/metaai-api/issues
- Documentation: See README.md and other documentation files

## Changelog

### Version 2.0.0+

- ✨ Added image upload functionality
- ✨ Added `ImageUploader` class
- ✨ Added `/upload` API endpoint
- ✨ Added comprehensive examples and documentation
