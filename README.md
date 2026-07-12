# metaai-api

Unofficial Python SDK and API server for **Meta AI** — generate images, chat with Llama, and manage conversations. No API key required, just your browser cookies.

> **⚠️ Disclaimer**: This is an unofficial, reverse-engineered client. It is not affiliated with, endorsed by, or sponsored by Meta. Use at your own risk and in compliance with Meta's Terms of Service. Cookie-based authentication may break at any time as Meta updates their platform.

## What's New in v3.0.0

Meta AI migrated from HTTP GraphQL to **DGW (Datagram WebSocket)** for all chat and image generation. The old HTTP-based methods no longer work — Meta's GraphQL schema changed (removed `RewriteOptionsInput`, `AttachmentInput`, `MentionInput`, `sendMessageStream`, and more).

This version uses **browser automation** (via `agent-browser`) as the primary method, which works for ANY prompt. The browser creates valid DGW messages natively.

### Breaking Changes from v2.x
- `prompt()` now uses browser automation (no more OAuth token extraction)
- `generate_image_new()` uses browser automation
- Video generation is **NOT available** on Meta AI (Meta says "I can't generate videos right now")
- `upload_image()` is not yet supported via browser method
- Cookie-based auth replaces access token for primary methods

### What Still Works
- ✅ Image generation (text → image)
- ✅ Chat (text conversation, Instant + Thinking modes)
- ✅ Conversation management (list, new)
- ✅ Media fetching by card ID (HTTP GraphQL)
- ✅ DGW frame replay (advanced WebSocket method)

## Features

- 🖼️ **Image generation** — Create images from text prompts
- 💬 **Chat** — Text conversation with Meta AI (Instant + Thinking modes)
- 📋 **Conversation management** — List conversations
- 🔗 **Media fetching** — Get URLs for already-generated media by card ID
- 🔓 **No API key** — Uses your browser cookies for authentication
- 🌐 **REST API server** — Deploy once, call from any language
- 📦 **Python SDK** — Use as a library in your Python projects

## Install

```bash
pip install metaai-sdk[api,browser]
agent-browser install  # downloads Chrome for browser automation
```

Or from source:
```bash
git clone https://github.com/mir-ashiq/metaai-api.git
cd metaai-api
pip install -e ".[api,browser]"
agent-browser install
```

## Quick Start

### As a Python SDK

```python
from metaai_api import MetaAI

ai = MetaAI(cookies={
    "datr": "your_datr_cookie",
    "ecto_1_sess": "your_ecto_1_sess_cookie",
})

# Generate an image
result = ai.generate_image_new("a watercolor painting of a red panda")
print(result["image_urls"])

# Chat
reply = ai.prompt("What is 2+2?")
print(reply["message"])

# List conversations
convs = ai.list_conversations()
for c in convs:
    print(c["title"])

ai.close()
```

### As an API server

```bash
export META_AI_DATR="your_datr_cookie"
export META_AI_ECTO_1_SESS="your_ecto_1_sess_cookie"
export META_AI_API_KEY="your_secret_key"  # optional

python -m metaai_api.api_server
```

Then call from any language:

```bash
curl -X POST http://localhost:8000/image \
  -H "Authorization: Bearer your_secret_key" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "a watercolor painting of a cat"}'
```

## Getting Your Cookies

1. Open [https://www.meta.ai/](https://www.meta.ai/) and log in
2. Press F12 → Application → Cookies → `https://www.meta.ai`
3. Copy the values of `datr` and `ecto_1_sess`

Or set them as environment variables:
```bash
export META_AI_DATR="..."
export META_AI_ECTO_1_SESS="..."
```

See [CHANGES_AND_COOKIES.md](CHANGES_AND_COOKIES.md) for details on cookie expiration and the optional access token.

## API Reference

### Python SDK

| Method | Description | Status |
|--------|-------------|--------|
| `ai.generate_image_new(prompt)` | Generate image from text | ✅ Works |
| `ai.prompt(message)` | Send a chat message | ✅ Works |
| `ai.list_conversations()` | List all conversations | ✅ Works |
| `ai.new_conversation()` | Start a new conversation | ✅ Works |
| `ai.fetch_card_media(card_id)` | Fetch media by card ID | ✅ Works |
| `ai.replay_frame(frame_b64)` | Replay captured DGW frame (advanced) | ✅ Works |
| `ai.warmup_conversation(conv_id)` | Register a new conversation | ✅ Works |
| `ai.generate_video_new(prompt)` | Generate video | ❌ Not available |
| `ai.extend_video(media_id)` | Extend a video | ❌ Not available |
| `ai.close()` | Close browser session | ✅ Works |

### REST API Endpoints

| Endpoint | Method | Description | Status |
|----------|--------|-------------|--------|
| `/healthz` | GET | Health check | ✅ |
| `/chat` | POST | Send a chat message | ✅ |
| `/image` | POST | Generate image from text | ✅ |
| `/video` | POST | Generate video | ❌ 501 |
| `/video/async` | POST | Async video generation | ❌ 501 |
| `/video/jobs/{job_id}` | GET | Video job status | ❌ 404 |
| `/video/extend` | POST | Extend a video | ❌ 501 |
| `/upload` | POST | Upload an image | ❌ 501 |
| `/conversations` | GET | List conversations | ✅ |
| `/media` | POST | Fetch media by card ID | ✅ |
| `/reset` | POST | Reset browser session | ✅ |
| `/docs` | GET | Swagger UI | ✅ |

## How It Works

Meta AI uses a custom WebSocket protocol called **DGW (Datagram WebSocket)** for image generation and chat. The server validates message integrity, so you can't construct valid messages from scratch in Python.

This SDK uses **browser automation** (via `agent-browser`) to drive a real headless Chrome browser:
1. Launches Chrome with your cookies injected
2. Types the prompt into the meta.ai chat input
3. Waits for the image/response to appear
4. Extracts URLs and text from the page

For advanced users, the `replay_frame()` method allows replaying captured DGW frames via WebSocket (each frame works once).

See [GENERATION_API.md](GENERATION_API.md) for detailed API usage.

## Deployment

### Docker

```bash
export META_AI_DATR="..."
export META_AI_ECTO_1_SESS="..."
export META_AI_API_KEY="..."

docker-compose up -d
```

### Direct

```bash
pip install metaai-sdk[api,browser]
agent-browser install
python -m metaai_api.api_server
```

See [QUICK_START.md](QUICK_START.md) for a step-by-step guide.

## Limitations

- **Video generation**: NOT available on Meta AI. Meta AI responds: "I can't generate videos right now."
- **Cookie expiration**: `ecto_1_sess` expires frequently. Re-extract if requests fail.
- **Speed**: ~30-40s per image (browser startup + generation).
- **Region**: Meta AI isn't available in all regions.
- **Image upload**: Not yet supported via browser method.

## Environment Variables

| Variable | Description |
|----------|-------------|
| `META_AI_DATR` | datr cookie (required) |
| `META_AI_ECTO_1_SESS` | ecto_1_sess cookie (required) |
| `META_AI_ABRA_SESS` | abra_sess cookie (optional, some regions) |
| `META_AI_ACCESS_TOKEN` | DGW access token (for WebSocket method, optional) |
| `META_AI_API_KEY` | API key for the server (optional) |
| `META_AI_HEADED` | Show browser window: "true" or "false" (default) |

## Project Structure

```
metaai-api/
├── src/metaai_api/
│   ├── __init__.py          # Package exports
│   ├── main.py              # MetaAI class (main entry point)
│   ├── generation.py        # GenerationAPI (image/video generation)
│   ├── client.py            # MetaAIClient (HTTP/WebSocket)
│   ├── browser.py           # BrowserBackend (agent-browser automation)
│   ├── api_server.py        # FastAPI server
│   ├── parser.py            # DGW frame parser
│   ├── exceptions.py        # Error hierarchy
│   ├── utils.py             # Constants and helpers
│   ├── html_scraper.py      # HTML scraping (legacy)
│   ├── image_upload.py      # Image upload (legacy)
│   ├── video_generation.py  # Video generation (legacy)
│   └── video_generation_new.py  # Video generation (legacy)
├── examples/                # Example scripts
├── scripts/                 # Test scripts
├── test/                    # Test suite
├── Dockerfile               # Docker deployment
├── docker-compose.yml       # Docker Compose
├── pyproject.toml           # Package config
└── requirements.txt         # Dependencies
```

## License

MIT

## Author

Ashiq Hussain Mir
