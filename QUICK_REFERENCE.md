# Meta AI Python SDK - Quick Reference

> Fast lookup guide for Meta AI Python SDK v2.0.0

## 🚀 Installation

```bash
# Install from PyPI
pip install metaai-api

# Or install from source
git clone https://github.com/mir-ashiq/metaai-api.git
cd metaai-api
pip install -e .
```

---

## 💬 Chat

```python
from metaai_api import MetaAI

ai = MetaAI()

# Simple chat
response = ai.prompt("What's the weather?")
print(response['message'])

# Streaming
for chunk in ai.prompt("Tell me a story", stream=True):
    print(chunk['message'], end='')

# New conversation
response = ai.prompt("Hello", new_conversation=True)
```

---

## 🎬 Video Generation

```python
from metaai_api import MetaAI

# Your cookies
cookies = {
    "datr": "...",
    "abra_sess": "...",
    "dpr": "1.25",
    "wd": "1536x443"
}

ai = MetaAI(cookies=cookies)

# Generate video
result = ai.generate_video("Generate a video of a sunset")

if result["success"]:
    print(f"Generated {len(result['video_urls'])} videos (4 by default)")
    for url in result['video_urls']:
        print(url)
```

### Custom Parameters

```python
result = ai.generate_video(
    prompt="Your prompt",
    wait_before_poll=10,    # Wait before polling
    max_attempts=30,        # Max polling attempts
    wait_seconds=5,         # Wait between attempts
    verbose=True            # Show status messages
)
```

---

## 🎨 Image Generation

```python
from metaai_api import MetaAI

# Requires FB credentials
ai = MetaAI(fb_email="email@example.com", fb_password="password")

response = ai.prompt("Generate an image of a mountain")
print(response['media'])
```

---

## 🍪 Getting Cookies

1. Visit https://www.meta.ai
2. Open DevTools (F12) → Network tab
3. Refresh page
4. Click any request
5. Copy Cookie header
6. Extract: `datr`, `abra_sess`, `dpr`, `wd`

---

## 🔧 Common Parameters

### `prompt()` method

| Parameter          | Type   | Default  | Description            |
| ------------------ | ------ | -------- | ---------------------- |
| `message`          | `str`  | Required | Your message/prompt    |
| `stream`           | `bool` | `False`  | Stream response        |
| `new_conversation` | `bool` | `False`  | Start new conversation |

### `generate_video()` method

| Parameter          | Type   | Default  | Description            |
| ------------------ | ------ | -------- | ---------------------- |
| `prompt`           | `str`  | Required | Video description      |
| `wait_before_poll` | `int`  | `10`     | Initial wait (seconds) |
| `max_attempts`     | `int`  | `30`     | Max polling attempts   |
| `wait_seconds`     | `int`  | `5`      | Wait between polls     |
| `verbose`          | `bool` | `True`   | Show messages          |

---

## 📦 Response Format

### Chat Response

```python
{
    "message": "The response text",
    "sources": [
        {
            "link": "https://...",
            "title": "Source title"
        }
    ],
    "media": []
}
```

### Video Response

```python
{
    "success": True,
    "conversation_id": "abc-123",
    "prompt": "Your prompt",
    "video_urls": ["https://...mp4"],
    "timestamp": 1234567890.0
}
```

---

## ⚙️ Advanced Usage

### Proxy Support

```python
proxy = {
    'http': 'http://proxy:port',
    'https': 'https://proxy:port'
}
ai = MetaAI(proxy=proxy)
```

### Error Handling

```python
try:
    result = ai.generate_video("prompt")
    if not result["success"]:
        print("Video still processing...")
except ValueError as e:
    print(f"Config error: {e}")
except Exception as e:
    print(f"Error: {e}")
```

---

## 🐛 Troubleshooting

### No video URLs found

- Wait longer: increase `max_attempts` or `wait_seconds`
- Be specific with your prompt
- Check if video generation is available in your region

### Token errors

- Refresh your browser cookies
- Ensure all required cookies are present
- Try visiting https://www.meta.ai first

### Connection issues

- Check internet connection
- Try using a proxy
- Verify Meta AI is accessible

---

## 📚 More Info

- **Full Docs**: [VIDEO_GENERATION_README.md](VIDEO_GENERATION_README.md)
- **Examples**: `examples/` directory
- **Changelog**: [CHANGELOG.md](CHANGELOG.md)

---

## 💡 Tips

1. **Cookies expire** - Refresh every 24-48 hours
2. **Be specific** - Detailed prompts = better videos
3. **Be patient** - Videos take 30-180 seconds to generate
4. **One instance** - Reuse `MetaAI` for multiple requests
5. **Error handling** - Always check `response["success"]`

---

## 🔗 Links

- **GitHub**: [mir-ashiq/meta-ai-python](https://github.com/mir-ashiq/meta-ai-python)
- **PyPI**: [metaai-api](https://pypi.org/project/metaai-api/)
- **Documentation**: [README.md](README.md)
- **Changelog**: [CHANGELOG.md](CHANGELOG.md)
- **Meta AI**: https://www.meta.ai/

---

**Meta AI Python SDK v2.0.0** | MIT License | Made with ❤️ for developers
