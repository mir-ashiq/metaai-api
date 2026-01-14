# Meta AI Python SDK - Video Generation Guide

[![Python](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)](https://github.com/mir-ashiq/metaai-api)

Complete guide for generating AI videos using Meta AI Python SDK with automatic token management and seamless integration.

## ✨ Features

- 🎬 **Video Generation** - Create videos from text prompts
- 💬 **Chat Integration** - Unified interface for chat and video
- 🔐 **Auto Token Management** - Automatic lsd/fb_dtsg fetching
- 🍪 **Simple Authentication** - Just provide browser cookies
- 📦 **Easy to Use** - Clean, intuitive API

---

## 🚀 Quick Start

```python
from metaai_api import MetaAI

# Your cookies from browser
cookies = {
    "datr": "...",
    "abra_sess": "...",
    "dpr": "1.25",
    "wd": "1536x443"
}

# Initialize once
ai = MetaAI(cookies=cookies)

# Generate video
response = ai.generate_video("Generate a video of a sunset")

if response["success"]:
    print(f"Video URLs: {response['video_urls']}")
```

That's it! No need to manually fetch tokens or use separate classes. 🎉

---

## 📖 Table of Contents

1. [Installation](#installation)
2. [Getting Cookies](#getting-cookies)
3. [Basic Usage](#basic-usage)
4. [Advanced Usage](#advanced-usage)
5. [API Reference](#api-reference)
6. [Examples](#examples)
7. [Troubleshooting](#troubleshooting)

---

## 📦 Installation

```bash
# Install from source
git clone https://github.com/mir-ashiq/metaai-api.git
cd metaai-api
pip install -e .

# Or install directly
pip install git+https://github.com/mir-ashiq/metaai-api.git
```

---

## 🍪 Getting Cookies

1. Open https://www.meta.ai in your browser
2. Open Developer Tools (F12)
3. Go to **Network** tab
4. Refresh the page
5. Click any request to `meta.ai`
6. Find the **Cookie** header
7. Copy the entire cookie string

**Required cookies:**

- `datr` - Device authentication token
- `abra_sess` - Session token
- `dpr` - Device pixel ratio
- `wd` - Window dimensions

**Example cookie string:**

```
datr=XYZ123; abra_sess=ABC456; dpr=1.25; wd=1536x443
```

**As dictionary:**

```python
cookies = {
    "datr": "XYZ123",
    "abra_sess": "ABC456",
    "dpr": "1.25",
    "wd": "1536x443"
}
```

---

## 🎯 Basic Usage

### Initialize MetaAI

```python
from metaai_api import MetaAI

# Method 1: With cookies dictionary (recommended)
ai = MetaAI(cookies={
    "datr": "...",
    "abra_sess": "...",
    "dpr": "1.25",
    "wd": "1536x443"
})

# Method 2: With Facebook credentials (if you have them)
ai = MetaAI(fb_email="your@email.com", fb_password="password")
```

### Generate a Video

```python
# Simple generation
response = ai.generate_video("Generate a video of a cat playing piano")

# Check if successful
if response["success"]:
    print(f"Generated {len(response['video_urls'])} video(s)!")

    for url in response['video_urls']:
        print(f"Video URL: {url}")

    # Access other info
    print(f"Conversation ID: {response['conversation_id']}")
    print(f"Prompt: {response['prompt']}")
else:
    print("Video generation failed or still processing")
```

---

## 🔧 Advanced Usage

### Custom Generation Parameters

Control polling behavior and timeout:

```python
response = ai.generate_video(
    prompt="Generate a video of dolphins swimming",
    wait_before_poll=10,    # Wait 10 seconds before first check
    max_attempts=30,        # Try up to 30 times
    wait_seconds=5,         # Wait 5 seconds between attempts
    verbose=True            # Print status messages
)

# Total max wait: 10 + (30 × 5) = 160 seconds
```

### Generate Multiple Videos

```python
prompts = [
    "Generate a video of a sunset",
    "Generate a video of a waterfall",
    "Generate a video of city lights"
]

for prompt in prompts:
    print(f"Generating: {prompt}")

    result = ai.generate_video(prompt, verbose=False)

    if result["success"]:
        print(f"✅ Success: {result['video_urls'][0]}")
    else:
        print("⚠️ Still processing...")
```

### Combine Chat and Video

Use the same `MetaAI` instance for both chat and video generation:

```python
# Have a conversation
chat = ai.prompt("Give me creative video ideas about nature")
print(chat['message'])

# Generate video based on the ideas
video = ai.generate_video("Generate a video of a forest at sunrise")
print(video['video_urls'])
```

### Save Results

```python
import json

response = ai.generate_video("Generate a video of fireworks")

if response["success"]:
    # Save to JSON file
    filename = f"video_{response['conversation_id']}.json"
    with open(filename, 'w') as f:
        json.dump(response, f, indent=2)

    print(f"Saved to {filename}")
```

### Error Handling

```python
try:
    response = ai.generate_video(
        "Generate a video of northern lights",
        max_attempts=20
    )

    if response["success"]:
        print("Success!")
    else:
        print("No videos yet. Try longer timeout.")

except ValueError as e:
    print(f"Configuration error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

---

## 📚 API Reference

### `MetaAI.generate_video()`

Generate a video from a text prompt.

**Signature:**

```python
def generate_video(
    self,
    prompt: str,
    wait_before_poll: int = 10,
    max_attempts: int = 30,
    wait_seconds: int = 5,
    verbose: bool = True
) -> Dict
```

**Parameters:**

| Parameter          | Type   | Default  | Description                                         |
| ------------------ | ------ | -------- | --------------------------------------------------- |
| `prompt`           | `str`  | Required | Text description of the video to generate           |
| `wait_before_poll` | `int`  | `10`     | Seconds to wait before starting to poll for results |
| `max_attempts`     | `int`  | `30`     | Maximum number of polling attempts                  |
| `wait_seconds`     | `int`  | `5`      | Seconds to wait between polling attempts            |
| `verbose`          | `bool` | `True`   | Whether to print status messages during generation  |

**Returns:**

Dictionary with the following keys:

```python
{
    "success": bool,              # True if video(s) were found
    "conversation_id": str,       # Unique conversation identifier
    "prompt": str,                # The prompt that was used
    "video_urls": List[str],      # List of generated video URLs
    "timestamp": float,           # Unix timestamp of generation
    "error": str                  # Error message (only if success=False)
}
```

**Example:**

```python
result = ai.generate_video(
    prompt="Generate a video of a sunset over mountains",
    wait_before_poll=15,
    max_attempts=25,
    verbose=True
)

if result["success"]:
    print(f"Videos: {result['video_urls']}")
```

---

## 📋 Examples

### Example 1: Simple Video Generation

```python
from metaai_api import MetaAI

ai = MetaAI(cookies={"datr": "...", "abra_sess": "..."})
result = ai.generate_video("Generate a video of a cat")

if result["success"]:
    print(f"Generated {len(result['video_urls'])} videos (Meta AI creates 4 by default)")
    for i, url in enumerate(result['video_urls'], 1):
        print(f"Video {i}: {url}")
```

### Example 2: Batch Generation

```python
from metaai_api import MetaAI

ai = MetaAI(cookies=cookies)

prompts = [
    "Generate a video of rain falling",
    "Generate a video of clouds moving",
    "Generate a video of waves crashing"
]

results = []
for prompt in prompts:
    result = ai.generate_video(prompt, verbose=False)
    results.append(result)

successful = [r for r in results if r["success"]]
print(f"Generated {len(successful)}/{len(prompts)} videos")
```

### Example 3: Custom Timeout

```python
from metaai_api import MetaAI

ai = MetaAI(cookies=cookies)

# For longer/complex videos, increase timeout
result = ai.generate_video(
    "Generate a cinematic video of a futuristic city",
    wait_before_poll=20,    # Wait longer before first check
    max_attempts=40,        # More attempts
    wait_seconds=8          # Longer between attempts
)
# Max wait: 20 + (40 × 8) = 340 seconds (~5.5 minutes)
```

### Example 4: Download Generated Videos

```python
from metaai_api import MetaAI
import requests

ai = MetaAI(cookies=cookies)
result = ai.generate_video("Generate a video of a sunset")

if result["success"]:
    for i, url in enumerate(result['video_urls'], 1):
        # Download video
        video_data = requests.get(url).content

        # Save to file
        filename = f"video_{i}.mp4"
        with open(filename, 'wb') as f:
            f.write(video_data)

        print(f"Downloaded {filename}")
```

### Example 5: Complete Workflow

```python
from metaai_api import MetaAI
import json
from datetime import datetime

# Initialize
ai = MetaAI(cookies=cookies)

# Generate video
prompt = "Generate a video of northern lights"
print(f"Generating: {prompt}")

result = ai.generate_video(prompt, verbose=True)

# Process results
if result["success"]:
    print(f"\n✅ Success!")
    print(f"Generated {len(result['video_urls'])} video(s)")

    # Display URLs
    for i, url in enumerate(result['video_urls'], 1):
        print(f"\nVideo {i}:")
        print(f"  URL: {url}")
        print(f"  Length: {len(url)} chars")

    # Save metadata
    metadata = {
        "prompt": result['prompt'],
        "conversation_id": result['conversation_id'],
        "generated_at": datetime.fromtimestamp(result['timestamp']).isoformat(),
        "video_count": len(result['video_urls']),
        "video_urls": result['video_urls']
    }

    with open("video_metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"\n💾 Metadata saved to video_metadata.json")
else:
    print("\n❌ Generation failed or timed out")
    print("Try increasing max_attempts or wait_seconds")
```

---

## 🐛 Troubleshooting

### "Failed to auto-fetch tokens" Error

**Problem:** Cannot fetch `lsd` and `fb_dtsg` tokens automatically.

**Solutions:**

1. Verify cookies are valid and not expired
2. Visit https://www.meta.ai in browser to refresh cookies
3. Copy fresh cookies from browser DevTools
4. Ensure all required cookies are present (datr, abra_sess, dpr, wd)

### No Video URLs Found

**Problem:** `response["success"]` is `False` and no videos returned.

**Reasons & Solutions:**

1. **Still Processing** - Videos take 30-180 seconds to generate

   ```python
   result = ai.generate_video(prompt, max_attempts=40, wait_seconds=5)
   ```

2. **Prompt Too Vague** - Be more specific

   ```python
   # ❌ Vague
   result = ai.generate_video("make a video")

   # ✅ Specific
   result = ai.generate_video("Generate a realistic video of a sunset over mountains")
   ```

3. **Region Blocked** - Some regions can't access Meta AI
   - Try using a VPN
   - Check if https://www.meta.ai loads in browser

### Connection Errors

**Problem:** Network or timeout errors.

**Solutions:**

1. Check internet connection
2. Verify Meta AI is accessible from your location
3. Try increasing timeout values
4. Check firewall/proxy settings

### Cookies Expired

**Problem:** Authentication fails after some time.

**Solution:**

- Cookies expire periodically (usually 24-48 hours)
- Get fresh cookies from browser when this happens
- Consider automating cookie refresh

---

## 🔄 Migration Guide

### From Standalone `VideoGenerator`

**Before:**

```python
from metaai_api import VideoGenerator

video_gen = VideoGenerator(cookies_str="...")
result = video_gen.generate_video(prompt)
```

**After:**

```python
from metaai_api import MetaAI

ai = MetaAI(cookies={"datr": "...", "abra_sess": "..."})
result = ai.generate_video(prompt)
```

### From Manual Token Fetching

**Before:**

```python
video_gen = VideoGenerator(
    cookies_str="...",
    lsd="...",
    fb_dtsg="..."
)
```

**After:**

```python
ai = MetaAI(cookies={"datr": "...", "abra_sess": "..."})
# Tokens automatically fetched!
```

---

## 📄 License

This project is provided as-is for educational purposes.

## 🤝 Contributing

Contributions welcome! Please open issues or pull requests.

---

**Made with ❤️ for the Meta AI community**
