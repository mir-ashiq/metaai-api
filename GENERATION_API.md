# Image and Video Generation API

> **✅ Status: FULLY WORKING**  
> Image and video generation features are operational and tested. See [QUICK_START.md](QUICK_START.md) for setup.

This implementation is based on captured network requests from Meta AI's web interface for image and video generation.

## Features

- **Image Generation**: Generate images from text prompts with custom orientation ✅ Working
- **Video Generation**: Generate videos from text prompts ✅ Working
- **Image Upload**: Upload images for generation/editing ✅ Working
- **Cookie-based Authentication**: Uses browser cookies from Meta AI (no `lsd`/`fb_dtsg` needed)
- **Multipart Response Parsing**: Handles Meta AI's multipart/mixed responses
- **Optimized Polling**: Fast 2-second intervals with progressive backoff

## Installation

Make sure you have the package installed:

```bash
pip install -e .
```

## Configuration

1. Copy `.env.example` to `.env`:

   ```bash
   cp .env.example .env
   ```

2. Get your Meta AI cookies:
   - Open browser and go to https://meta.ai
   - Login if needed
   - Open Developer Tools (F12)
   - Go to Application/Storage > Cookies > https://meta.ai
   - Copy the values for: `datr`, `abra_sess`, `ecto_1_sess`

3. Add cookies to `.env` file:

   ```env
   META_AI_DATR=your_datr_value
   META_AI_ABRA_SESS=your_abra_sess_value
   META_AI_ECTO_1_SESS=your_ecto_1_sess_value
   ```

   > **Note**: Only these 3 cookies are required for image/video generation. Other cookies like `lsd`, `fb_dtsg` are NOT needed.

## Usage

### Image Generation

```python
from metaai_api import MetaAI

# Initialize with cookie-based authentication
ai = MetaAI()

# Or with explicit cookies
cookies = {
    'datr': 'your_datr_value',
    'abra_sess': 'your_abra_sess_value',
    'ecto_1_sess': 'your_ecto_1_sess_value'
}
ai = MetaAI(cookies=cookies)

# Generate image
result = ai.generate_image_new(
    prompt="Astronaut in space",
    orientation="LANDSCAPE",  # LANDSCAPE, VERTICAL, or SQUARE
    num_images=1
)

if result['success']:
    print(f"Generated {len(result['image_urls'])} images:")
    for url in result['image_urls']:
        print(f"  {url}")
```

### Video Generation

```python
from metaai_api import MetaAI

# Initialize with cookie-based authentication
ai = MetaAI()

# Or with explicit cookies
cookies = {
    'datr': 'your_datr_value',
    'abra_sess': 'your_abra_sess_value',
    'ecto_1_sess': 'your_ecto_1_sess_value'
}
ai = MetaAI(cookies=cookies)

# Generate video
result = ai.generate_video_new(
    prompt="Astronaut floating in space"
)

if result['success']:
    for url in result['video_urls']:
        print(f"Video URL: {url}")
```

## Testing

Run the test script:

```bash
python test_generation.py
```

This will test both image and video generation using the cookies from your `.env` file.

## API Details

### Endpoint

- **URL**: `https://www.meta.ai/api/graphql`
- **Method**: POST
- **Doc ID**: `904075722675ba2c1a7b333d4c525a1b`

### Image Generation

**Operation**: `TEXT_TO_IMAGE`

**Parameters**:

- `prompt`: Text description of the image
- `orientation`: Image orientation (`VERTICAL`, `HORIZONTAL`, `SQUARE`)
- `numImages`: Number of images to generate

### Video Generation

**Operation**: `TEXT_TO_VIDEO`

**Parameters**:

- `prompt`: Text description of the video

### Request Structure

Both operations use similar request structure:

```json
{
  "doc_id": "904075722675ba2c1a7b333d4c525a1b",
  "variables": {
    "conversationId": "uuid",
    "content": "Imagine/Animate <prompt>",
    "imagineOperationRequest": {
      "operation": "TEXT_TO_IMAGE" | "TEXT_TO_VIDEO",
      "textToImageParams": {
        "prompt": "<prompt>",
        "orientation": "VERTICAL" (for images)
      }
    },
    ...
  }
}
```

## Response Format

The API returns responses in multipart/mixed format or JSON. The implementation automatically:

- Parses multipart responses
- Extracts media URLs (images/videos)
- Returns structured data

## Notes

- Cookies may expire and need to be refreshed periodically
- The API requires valid Meta AI cookies for authentication
- Generated content follows Meta AI's usage policies
- Network captures show this is the same API used by meta.ai web interface

## Troubleshooting

1. **Authentication Errors**: Make sure your cookies are fresh and valid
2. **Missing URLs**: Check that the response contains the expected data structure
3. **Rate Limiting**: Meta AI may rate limit requests, add delays if needed

## Network Capture Details

This implementation is based on analyzing captured network requests:

- **network.json**: Contains video generation requests
- **network-new.json**: Contains image and video generation requests

Key patterns identified:

- Same doc_id for both image and video generation
- Different operation types (`TEXT_TO_IMAGE` vs `TEXT_TO_VIDEO`)
- Consistent request structure with UUIDs and session tracking
- Multipart/mixed response format for streaming results
