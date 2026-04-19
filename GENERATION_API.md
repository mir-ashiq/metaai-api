# Image and Video Generation API

> **✅ Status: FULLY WORKING**  
> Image and video generation features are operational and tested. See [QUICK_START.md](QUICK_START.md) for setup.

This implementation is based on captured network requests from Meta AI's web interface for chat, image, and video generation.

## Features

- **Image Generation**: Generate images from text prompts with custom orientation ✅ Working
- **Video Generation**: Generate videos from text prompts ✅ Working
- **Image Upload**: Upload images for generation/editing ✅ Working
- **Chat**: Send chat prompts and stream responses ✅ Working
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
   - Copy the values for: `datr`, `ecto_1_sess` (required), and `abra_sess` if available (optional)

3. Add cookies to `.env` file:

   ```env
   META_AI_DATR=your_datr_value
   META_AI_ECTO_1_SESS=your_ecto_1_sess_value
   META_AI_ABRA_SESS=your_abra_sess_value  # Optional - may not be available in all regions (e.g., Indonesia)
   ```

   > **Note**: Only `datr` and `ecto_1_sess` are required for image/video generation. `abra_sess` is optional and improves compatibility in some cases. Other cookies like `lsd`, `fb_dtsg` are NOT needed.

For chat usage, the SDK also needs a Meta AI OAuth access token. The SDK can load it from `META_AI_ACCESS_TOKEN` or extract it from the Meta AI page when cookies are valid.

## Usage

### Image Generation

```python
from metaai_api import MetaAI

# Initialize with cookie-based authentication
ai = MetaAI()

# Or with explicit cookies (minimum required)
cookies = {
    'datr': 'your_datr_value',
    'ecto_1_sess': 'your_ecto_1_sess_value'
}
ai = MetaAI(cookies=cookies)

# Or with optional abra_sess if available:
cookies = {
    'datr': 'your_datr_value',
    'abra_sess': 'your_abra_sess_value',  # Optional
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

### Chat

```python
from metaai_api import MetaAI

ai = MetaAI()
response = ai.prompt("What is 7% of 10000?", stream=False, new_conversation=True)
print(response["message"])
```

### Video Generation

```python
from metaai_api import MetaAI

# Initialize with cookie-based authentication
ai = MetaAI()

# Or with explicit cookies (minimum required)
cookies = {
    'datr': 'your_datr_value',
    'ecto_1_sess': 'your_ecto_1_sess_value'
}
ai = MetaAI(cookies=cookies)

# Optional cookie for broader compatibility
# cookies['abra_sess'] = 'your_abra_sess_value'

# Generate video (auto-polls by default)
result = ai.generate_video_new("Astronaut floating in space")

if result['success']:
    print(f"Generated {len(result['video_urls'])} videos")
    for url in result['video_urls']:
        print(f"Video URL: {url}")
  # Example: https://scontent-xxx.fbcdn.net/.../video.mp4?...
  print("Media IDs:", result.get('media_ids', []))

# Extend a generated video using one of the media IDs
if result.get('media_ids'):
  extended = ai.extend_video(result['media_ids'][0])
  if extended.get('success'):
    print("Extended URLs:", extended.get('video_urls', []))
    print("Extended Media IDs:", extended.get('media_ids', []))

# For quick return without waiting (disable auto-polling)
result = ai.generate_video_new(
    "Astronaut floating in space",
    auto_poll=False  # Returns immediately in ~17s
)

if result['success']:
    # View videos manually at:
    print(f"https://www.meta.ai/prompt/{result['conversation_id']}")
```

## Testing

Run tests in this order:

```bash
# 1) Upload + image/video generation from uploaded image
python scripts/test_upload_and_generation.py --base-url http://127.0.0.1:8001

# 2) Comprehensive SDK + API test suite
python scripts/test_all_features_complete.py --base-url http://127.0.0.1:8001 --output tests/integration/outputs/feature_test_report_sdk_api_final.json
```

## API Details

### Endpoint

- **URL**: `https://www.meta.ai/api/graphql`
- **Method**: POST
- **Doc ID**: Runtime-resolved in `GenerationAPI` (defaults can be overridden via env)

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
  "doc_id": "<resolved_doc_id>",
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

### Runtime `doc_id` Overrides

When Meta rotates persisted queries, you can hotfix without code edits by setting env vars:

- `META_AI_DOC_ID_TEXT_TO_IMAGE`
- `META_AI_DOC_ID_TEXT_TO_VIDEO`
- `META_AI_DOC_ID_IMAGE_ALT`
- `META_AI_DOC_ID_EXTEND_VIDEO`
- `META_AI_DOC_ID_FETCH_CONVERSATION`
- `META_AI_DOC_ID_FETCH_MEDIA`
- `META_AI_DOC_ID_POLL_MEDIA`

Backward-compatible shortcut:

- `META_AI_DOC_ID` (applies to both text-to-image and text-to-video)

The SDK logs active doc_id sources on startup (default vs env override) to simplify diagnostics.

## Response Format

The API returns responses in multipart/mixed format, SSE (`text/event-stream`), or JSON. The implementation automatically:

- Parses multipart responses
- Extracts media URLs (images/videos)
- Surfaces GraphQL validation/runtime errors from SSE events
- Returns structured status fields

For generation methods (`generate_image_new`, `generate_video_new`, `extend_video`), responses now include:

- `success`: Strict success indicator
- `status`: `READY`, `PROCESSING`, or `FAILED`
- `processing`: Convenience boolean (`status == PROCESSING`)
- `has_graphql_errors`: Whether GraphQL errors were detected in events
- `graphql_errors`: Normalized error list with message/code
- Media payload fields (`image_urls`, `video_urls`, `media_ids`, etc.)

Success contract:

- `success=false` if GraphQL errors exist
- `success=false` if no media output (`media_ids`/URLs) was produced
- `success=true` only when media output exists and no GraphQL errors are present

Example failure payload:

```json
{
  "success": false,
  "status": "FAILED",
  "processing": false,
  "has_graphql_errors": true,
  "graphql_errors": [
    {
      "message": "Cannot query field \"name\" on type \"User\".",
      "code": "GRAPHQL_VALIDATION_FAILED"
    }
  ],
  "error": "GraphQL error (GRAPHQL_VALIDATION_FAILED): Cannot query field \"name\" on type \"User\"."
}
```

## Notes

- Cookies may expire and need to be refreshed periodically
- The API requires valid Meta AI cookies for authentication
- Generated content follows Meta AI's usage policies
- Network captures show this is the same API used by meta.ai web interface

## Troubleshooting

1. **Authentication Errors**: Make sure your cookies are fresh and valid
2. **GraphQL Validation Errors**: If you see `GRAPHQL_VALIDATION_FAILED` with HTTP 200, persisted query doc*ids likely drifted. Update with fresh browser-captured values or use `META_AI_DOC_ID*\*` overrides.
3. **Missing URLs**: Check `status`, `has_graphql_errors`, and `graphql_errors` before retrying.
4. **Rate Limiting**: Meta AI may rate limit requests, add delays if needed

## Network Capture Details

This implementation is based on analyzing captured network requests:

- **network.json**: Contains video generation requests
- **network-new.json**: Contains image and video generation requests

Key patterns identified:

- Persisted query doc_ids can change as Meta backend evolves
- Different operation types (`TEXT_TO_IMAGE` vs `TEXT_TO_VIDEO`)
- Consistent request structure with UUIDs and session tracking
- Multipart/mixed response format for streaming results
