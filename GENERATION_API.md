# Generation API

## Image Generation

### Python SDK

```python
from metaai_api import MetaAI

ai = MetaAI(cookies={"datr": "...", "ecto_1_sess": "..."})

result = ai.generate_image_new(
    prompt="a watercolor painting of a red panda",
    orientation="VERTICAL",  # VERTICAL, HORIZONTAL, SQUARE
    num_images=1,
    timeout=120,
)

if result["success"]:
    for url in result["image_urls"]:
        print(f"Image URL: {url}")
```

### REST API

```bash
curl -X POST http://localhost:8000/generate-image \
  -H "Content-Type: application/json" \
  -d '{"prompt": "a watercolor painting of a red panda", "timeout": 120}'
```

Response:
```json
{
    "success": true,
    "image_urls": ["https://scontent.xx.fbcdn.net/..."],
    "conversation_id": "uuid-here",
    "prompt": "a watercolor painting of a red panda",
    "elapsed_seconds": 35.2
}
```

## Video Generation

Video generation is **NOT available** on Meta AI. When asked, Meta AI responds:
"I can't generate videos right now — that feature isn't available in Meta AI at the moment."

The `/generate-video` endpoint returns HTTP 501.

## Media Fetching

Fetch URLs for already-generated media by card ID:

```python
data = ai.fetch_card_media("123456789012345", card_type="IMAGE_CARD")
urls = ai.generation_api.extract_media_urls(data)
print(urls)
```

## DGW Frame Replay (Advanced)

For advanced users who want faster response times:

1. Capture a frame from your browser's DevTools
2. Replay it via WebSocket

```python
result = ai.replay_frame("base64_encoded_frame...", timeout=90)
print(result["image_urls"])
```

Note: Each frame can only be replayed once.
