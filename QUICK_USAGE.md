# Quick Reference: Image Upload & Usage

## Complete Workflow Example

```python
from metaai_api import MetaAI

ai = MetaAI(cookies=your_cookies)

# 1. Upload
result = ai.upload_image("image.jpg")
media_id = result["media_id"]
metadata = {'file_size': result['file_size'], 'mime_type': result['mime_type']}

# 2. Chat/Analyze
response = ai.prompt("What's in this image?", media_ids=[media_id], attachment_metadata=metadata)
print(response["message"])

# 3. Generate Similar Images with orientation
response = ai.prompt(
    "Create similar in anime style",
    media_ids=[media_id],
    attachment_metadata=metadata,
    orientation="VERTICAL"  # Options: "LANDSCAPE", "VERTICAL" (default), "SQUARE"
)
for img in response["media"]:
    print(img["url"])

# 4. Generate Video with orientation
video = ai.generate_video(
    "animate with cinematic motion",
    media_ids=[media_id],
    attachment_metadata=metadata,
    orientation="LANDSCAPE"  # Wide format for cinematic effect
)
print(video["video_urls"][0])
```

## Upload Image

### SDK

```python
from metaai_api import MetaAI

ai = MetaAI(cookies=your_cookies)
result = ai.upload_image("image.jpg")
media_id = result["media_id"]  # e.g., "1453149056374564"
file_size = result["file_size"]  # e.g., 3310
mime_type = result["mime_type"]  # e.g., "image/jpeg"
```

### API

```bash
curl -X POST "http://localhost:8000/upload" -F "file=@image.jpg"
# Returns: {"success": true, "media_id": "1453149056374564", "file_size": 3310, "mime_type": "image/jpeg", ...}
```

## Use Uploaded Image

**Note:** `attachment_metadata` is **required** for all operations using uploaded images.

### Image Analysis (Chat)

```python
response = ai.prompt(
    message="What do you see in this image?",
    media_ids=["1453149056374564"],
    attachment_metadata={'file_size': 3310, 'mime_type': 'image/jpeg'}
)
print(response["message"])  # "The image captures a serene lake scene..."
```

```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What do you see?",
    "media_ids": ["1453149056374564"],
    "attachment_metadata": {"file_size": 3310, "mime_type": "image/jpeg"}
  }'
```

### Similar Image Generation

```python
response = ai.prompt(
    message="Create a similar image in watercolor style",
    media_ids=["1453149056374564"],
    attachment_metadata={'file_size': 3310, 'mime_type': 'image/jpeg'},
    is_image_generation=True
)
for img in response["media"]:
    print(f"{img['type']}: {img['url']}")
# Returns 4 generated images
```

```bash
curl -X POST "http://localhost:8000/image" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Create similar in anime style",
    "media_ids": ["1453149056374564"],
    "attachment_metadata": {"file_size": 3310, "mime_type": "image/jpeg"}
  }'
```

### Video Generation from Image

```python
result = ai.generate_video(
    prompt="generate a video with zoom in effect on this image",
    media_ids=["1453149056374564"],
    attachment_metadata={'file_size': 3310, 'mime_type': 'image/jpeg'}
)
if result["success"]:
    print(result["video_urls"][0])
```

```bash
curl -X POST "http://localhost:8000/video" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "generate video with cinematic motion",
    "media_ids": ["1453149056374564"],
    "attachment_metadata": {"file_size": 3310, "mime_type": "image/jpeg"}
  }'
```

## Multiple Images

```python
# Upload multiple images
media_ids = []
for img in ["img1.jpg", "img2.jpg", "img3.jpg"]:
    result = ai.upload_image(img)
    media_ids.append(result["media_id"])

# Use all in one prompt
response = ai.prompt(
    message="Compare these images",
    media_ids=media_ids
)
```

## Response Format

```python
{
    "message": "AI response text here...",
    "sources": [...],
    "media": [
        {
            "url": "https://...",
            "type": "IMAGE" or "VIDEO",
            "prompt": "..."
        }
    ]
}
```

## Parameters

### `prompt()` method

- `message` (str): Your prompt/question
- `media_ids` (list, optional): List of media IDs from uploads
- `stream` (bool): Stream response (default: False)
- `new_conversation` (bool): Start fresh conversation (default: False)

### `/chat` endpoint

```json
{
  "message": "Your message",
  "media_ids": ["media_id_1", "media_id_2"],
  "new_conversation": false,
  "stream": false
}
```

### `/image` endpoint

```json
{
  "prompt": "Your prompt",
  "media_ids": ["media_id_1"],
  "new_conversation": false
}
```

## Technical Details

The `media_id` is included in the request as:

```json
{
  "attachmentsV2": ["796999253413659"],
  "entrypoint": "KADABRA__CHAT__UNIFIED_INPUT_BAR"
}
```

When `media_ids` is provided, the entrypoint automatically changes from `ABRA__CHAT__TEXT` to `KADABRA__CHAT__UNIFIED_INPUT_BAR`.

## Error Handling

```python
result = ai.upload_image("image.jpg")
if not result["success"]:
    print(f"Error: {result['error']}")
else:
    media_id = result["media_id"]
    # Use media_id...
```

## Examples

See complete examples in:

- `examples/complete_workflow_example.py`
- `examples/image_upload_example.py`
- `test_image_upload.py`
