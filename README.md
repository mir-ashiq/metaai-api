<div align="center">

# 🤖 Meta AI Python SDK

[![Python Version](https://img.shields.io/badge/python-3.7%2B-blue?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green?style=for-the-badge)](LICENSE)
[![PyPI](https://img.shields.io/badge/PyPI-v2.0.0-orange?style=for-the-badge&logo=pypi&logoColor=white)](https://pypi.org/project/metaai-api/)
[![GitHub](https://img.shields.io/badge/GitHub-mir--ashiq-black?style=for-the-badge&logo=github)](https://github.com/mir-ashiq/metaai-api)

**Unleash the Power of Meta AI with Python** 🚀

A modern, feature-rich Python SDK providing seamless access to Meta AI's cutting-edge capabilities:
Chat with Llama 3, Generate Images, Create AI Videos - All Without API Keys!

[🎯 Quick Start](#-quick-start) • [📖 Documentation](#-documentation) • [💡 Examples](#-examples) • [🎬 Video Generation](#-video-generation)

</div>

---

## ✨ Why Choose This SDK?

<table>
<tr>
<td width="33%" align="center">

### 🎯 **Zero Configuration**

No API keys needed!
Just install and start coding

</td>
<td width="33%" align="center">

### ⚡ **Lightning Fast**

Optimized for performance
Real-time responses

</td>
<td width="33%" align="center">

### 🔥 **Feature Complete**

Chat • Images • Videos
All in one SDK

</td>
</tr>
</table>

### 🌟 Core Capabilities

> **⚠️ Current Status Notice:**  
> **Chat functionality** is currently unavailable due to authentication challenges.  
> **Image & Video Generation** are fully functional using simple cookie-based authentication (only 3 cookies needed).  
> See [SPEED_TEST_REPORT.md](SPEED_TEST_REPORT.md) for performance benchmarks.

| Feature                      | Description                                     | Status         |
| ---------------------------- | ----------------------------------------------- | -------------- |
| 💬 **Intelligent Chat**      | Powered by Llama 3 with internet access         | ⚠️ Unavailable |
| 📤 **Image Upload**          | Upload images for generation/analysis           | ✅ Working     |
| 🎨 **Image Generation**      | Create stunning AI-generated images             | ✅ Working     |
| 🎬 **Video Generation**      | Generate videos from text or uploaded images    | ✅ Working     |
| 🔍 **Image Analysis**        | Describe, analyze, and extract info from images | ⚠️ Unavailable |
| 🌐 **Real-time Data**        | Get current information via Bing integration    | ⚠️ Unavailable |
| 📚 **Source Citations**      | Responses include verifiable sources            | ⚠️ Unavailable |
| 🔄 **Streaming Support**     | Real-time response streaming                    | ⚠️ Unavailable |
| 🔐 **Cookie Authentication** | Uses session cookies (no problematic tokens)    | ✅ Working     |
| 🌍 **Proxy Support**         | Route requests through proxies                  | ✅ Working     |

---

## 📦 Installation

### SDK Only (Lightweight)

For using Meta AI as a Python library:

```bash
pip install metaai-sdk
```

### SDK + API Server

For deploying as a REST API service:

```bash
pip install metaai-sdk[api]
```

### From Source

```bash
git clone https://github.com/mir-ashiq/metaai-api.git
cd metaai-api
pip install -e .          # SDK only
pip install -e ".[api]"   # SDK + API server
```

**System Requirements:** Python 3.7+ • Internet Connection • That's it!

---

## 🚀 Quick Start

> **⚠️ Note:** Chat functionality is currently unavailable. Use the working **Image Generation** and **Video Generation** features below.

### Example 1: Generate Images (WORKING ✅)

```python
from metaai_api import MetaAI

# Initialize with cookie-based authentication
ai = MetaAI()

# Generate images
result = ai.generate_image_new(
    prompt="a beautiful sunset over mountains",
    orientation="LANDSCAPE"  # LANDSCAPE, VERTICAL, or SQUARE
)

if result["success"]:
    print(f"Generated {len(result['image_urls'])} images:")
    for url in result["image_urls"]:
        print(url)
```

**Output:**

```
Generated 4 images:
https://scontent-arn2-1.xx.fbcdn.net/o1/v/t0/f2/m421/AQN...
https://scontent-arn2-1.xx.fbcdn.net/o1/v/t0/f2/m421/AQM...
https://scontent-arn2-1.xx.fbcdn.net/o1/v/t0/f2/m421/AQO...
https://scontent-arn2-1.xx.fbcdn.net/o1/v/t0/f2/m421/AQM...
```

### Example 2: Generate Videos (WORKING ✅)

```python
from metaai_api import MetaAI

ai = MetaAI()

# Generate video
result = ai.generate_video_new(
    prompt="waves crashing on a beach at sunset"
)

if result["success"]:
    print(f"Generated {len(result['video_urls'])} videos:")
    for url in result["video_urls"]:
        print(url)
```

**Output:**

```
Generated 3 videos:
https://scontent-arn2-1.xx.fbcdn.net/o1/v/t6/f2/m477/AQO...
https://scontent-arn2-1.xx.fbcdn.net/o1/v/t6/f2/m259/AQN...
https://scontent-arn2-1.xx.fbcdn.net/o1/v/t6/f2/m260/AQP...
```

### Example 3: Upload & Use Images (WORKING ✅)

```python
from metaai_api import MetaAI

ai = MetaAI()

# Complex calculation
question = "If I invest $10,000 at 7% annual interest compounded monthly for 5 years, how much will I have?"
response = ai.prompt(question)

print(response["message"])
```

**Output:**

```
With an initial investment of $10,000 at a 7% annual interest rate compounded monthly
over 5 years, you would have approximately $14,176.25.

Here's the breakdown:
- Principal: $10,000
- Interest Rate: 7% per year (0.583% per month)
- Time: 5 years (60 months)
- Compound Frequency: Monthly
- Total Interest Earned: $4,176.25
- Final Amount: $14,176.25

This calculation uses the compound interest formula: A = P(1 + r/n)^(nt)
```

---

## � Authentication Options

The SDK uses simple **cookie-based authentication** with just 3 required cookies:

```python
from metaai_api import MetaAI

# Only 3 cookies required
cookies = {
    "datr": "your_datr_value",
    "abra_sess": "your_abra_sess_value",
    "ecto_1_sess": "your_ecto_1_sess_value"  # Most important for generation
}

ai = MetaAI(cookies=cookies)
```

**Alternative: Load from environment variables**

```python
import os
from metaai_api import MetaAI

# Cookies from .env file
ai = MetaAI()  # Automatically loads from META_AI_* environment variables
```

> **💡 Note:** Token fetching (lsd/fb_dtsg) has been removed. Generation APIs work perfectly with just these 3 cookies!

---

## �💬 Chat Features

### Streaming Responses

Watch responses appear in real-time, like ChatGPT:

```python
from metaai_api import MetaAI

ai = MetaAI()

print("🤖 AI: ", end="", flush=True)
for chunk in ai.prompt("Explain quantum computing in simple terms", stream=True):
    print(chunk["message"], end="", flush=True)
print("\n")
```

**Output:**

```
🤖 AI: Quantum computing is like having a super-powered calculator that can solve
problems in completely new ways. Instead of regular computer bits that are either
0 or 1, quantum computers use "qubits" that can be both 0 and 1 at the same time -
imagine flipping a coin that's both heads and tails until you look at it! This
special ability allows quantum computers to process massive amounts of information
simultaneously, making them incredibly fast for specific tasks like drug discovery,
cryptography, and complex simulations.
```

### Conversation Context

Have natural back-and-forth conversations:

```python
from metaai_api import MetaAI

ai = MetaAI()

# First question
response1 = ai.prompt("What are the three primary colors?")
print("Q1:", response1["message"][:100])

# Follow-up question (maintains context)
response2 = ai.prompt("How do you mix them to make purple?")
print("Q2:", response2["message"][:150])

# Start fresh conversation
response3 = ai.prompt("What's the capital of France?", new_conversation=True)
print("Q3:", response3["message"][:50])
```

**Output:**

```
Q1: The three primary colors are Red, Blue, and Yellow. These colors cannot be created by mixing...

Q2: To make purple, you mix Red and Blue together. The exact shade of purple depends on the ratio - more red creates a reddish-purple (like magenta)...

Q3: The capital of France is Paris, located in the...
```

### Using Proxies

Route your requests through a proxy:

```python
from metaai_api import MetaAI

# Configure proxy
proxy = {
    'http': 'http://your-proxy-server:8080',
    'https': 'https://your-proxy-server:8080'
}

ai = MetaAI(proxy=proxy)
response = ai.prompt("Hello from behind a proxy!")
print(response["message"])
```

---

## 🌐 REST API Server (Optional)

Deploy Meta AI as a REST API service! **Image and video generation endpoints are fully functional.**

> **⚠️ Note**: Chat endpoint is currently unavailable due to token authentication issues.

### Installation

```bash
pip install metaai-sdk[api]
```

### Setup

1. **Get your Meta AI cookies** (see [Cookie Setup](#-cookie-setup) section)
2. **Create `.env` file:**

```env
META_AI_DATR=your_datr_cookie
META_AI_ABRA_SESS=your_abra_sess_cookie
META_AI_ECTO_1_SESS=your_ecto_1_sess_cookie
```

3. **Start the server:**

```bash
uvicorn metaai_api.api_server:app --host 0.0.0.0 --port 8000
```

Server starts instantly (no token pre-fetching delays).

### API Endpoints

| Endpoint               | Method | Description                            | Status         |
| ---------------------- | ------ | -------------------------------------- | -------------- |
| `/healthz`             | GET    | Health check                           | ✅ Working     |
| `/upload`              | POST   | Upload images for generation           | ✅ Working     |
| `/image`               | POST   | Generate images from text              | ✅ Working     |
| `/video`               | POST   | Generate video (blocks until complete) | ✅ Working     |
| `/video/async`         | POST   | Start async video generation           | ✅ Working     |
| `/video/jobs/{job_id}` | GET    | Poll async job status                  | ✅ Working     |
| `/chat`                | POST   | Send chat messages                     | ⚠️ Unavailable |

### Example Usage (Working Endpoints)

```python
import requests

BASE_URL = "http://localhost:8000"

# Health check
response = requests.get(f"{BASE_URL}/healthz")
print(response.json())  # {"status": "ok"}

# Image generation
images = requests.post(f"{BASE_URL}/image", json={
    "prompt": "Cyberpunk cityscape at night",
    "orientation": "LANDSCAPE"  # LANDSCAPE, VERTICAL, or SQUARE
}, timeout=200)
result = images.json()
if result["success"]:
    for url in result["image_urls"]:
        print(url)

# Video generation (synchronous)
video = requests.post(f"{BASE_URL}/video", json={
    "prompt": "waves crashing on beach"
}, timeout=400)
result = video.json()
if result["success"]:
    for url in result["video_urls"]:
        print(url)

# Async video generation
job = requests.post(f"{BASE_URL}/video/async", json={
    "prompt": "sunset over ocean"
})
job_id = job.json()["job_id"]

# Poll for result
import time
while True:
    status = requests.get(f"{BASE_URL}/video/jobs/{job_id}")
    data = status.json()
    if data["status"] == "completed":
        print("Video URLs:", data["result"]["video_urls"])
        break
    time.sleep(5)
```

### Performance

- **Image Generation**: ~2 minutes (returns 4 images)
- **Video Generation**: ~40-60 seconds (returns 3-4 videos)
- **Upload**: < 5 seconds

---

## �🎬 Video Generation

Create AI-generated videos from text descriptions!

### Setup: Get Your Cookies

1. Visit [meta.ai](https://www.meta.ai) in your browser and login
2. Open DevTools (F12) → **Application** tab → **Cookies** → https://meta.ai
3. Copy these 3 cookie values:
   - `datr`
   - `abra_sess`
   - `ecto_1_sess` (most important for generation)

> **💡 Note:** Only these 3 cookies are needed. No tokens (lsd/fb_dtsg) required!

### 🔄 Automatic Cookie Refresh

Cookies (especially `ecto_1_sess`) expire periodically. The SDK now includes **automatic cookie refresh** scripts!

#### Option 1: Manual Export (Recommended)

```bash
# 1. In your browser: Copy as cURL → save as curl.json
# 2. Run the extractor
python refresh_cookies.py
```

#### When to Refresh?

The SDK automatically detects expired cookies and will show:

```
❌ Cookie Expired: ecto_1_sess needs to be refreshed
Run: python auto_refresh_cookies.py
```

**Key Cookies:**

- `ecto_1_sess` ⭐ - Session token (expires frequently, **must refresh**)
- `rd_challenge` - Challenge cookie (auto-updated by SDK)
- `ps_l`, `ps_n` - Portal flags (required for generation)

### Example 1: Generate Your First Video

```python
from metaai_api import MetaAI

# Your browser cookies (only 3 required!)
cookies = {
    "datr": "your_datr_value_here",
    "abra_sess": "your_abra_sess_value_here",
    "ecto_1_sess": "your_ecto_1_sess_value_here"
}

# Initialize with cookies
ai = MetaAI(cookies=cookies)

# Generate a video
result = ai.generate_video_new("A majestic lion walking through the African savanna at sunset")

if result["success"]:
    print("✅ Video generated successfully!")
    print(f"🎬 Generated {len(result['video_urls'])} videos")
    for i, url in enumerate(result['video_urls'], 1):
        print(f"   Video {i}: {url[:80]}...")
    print(f"📝 Prompt: {result['prompt']}")
else:
    print("⏳ Video generation failed, check your cookies")
```

**Output:**

```
✅ Sending video generation request...
✅ Video generation request sent successfully!
⏳ Waiting before polling...
🔄 Polling for video URLs (Attempt 1/20)...
✅ Video URLs found!

✅ Video generated successfully!
🎬 Generated 3 videos
   Video 1: https://scontent.xx.fbcdn.net/v/t66.36240-6/video1.mp4?...
   Video 2: https://scontent.xx.fbcdn.net/v/t66.36240-6/video2.mp4?...
   Video 3: https://scontent.xx.fbcdn.net/v/t66.36240-6/video3.mp4?...
📝 Prompt: A majestic lion walking through the African savanna at sunset
```

### How to Get Your Cookies

1. Open https://meta.ai in your browser and login
2. Press **F12** → **Application** tab
3. Navigate to **Cookies** → `https://meta.ai`
4. Copy these 3 values:
   - `datr`
   - `abra_sess`
   - `ecto_1_sess`
5. Add to your Python code or `.env` file
6. Alternatively, right-click → **View Page Source** → Search for `"LSD",[],{"token":"` and `DTSGInitData",[],{"token":"`

### Example 2: Generate Multiple Videos

```python
from metaai_api import MetaAI
import time

ai = MetaAI(cookies=cookies)

prompts = [
    "A futuristic city with flying cars at night",
    "Ocean waves crashing on a tropical beach",
    "Northern lights dancing over a snowy mountain"
]

videos = []
for i, prompt in enumerate(prompts, 1):
    print(f"\n🎬 Generating video {i}/{len(prompts)}: {prompt}")
    result = ai.generate_video(prompt, verbose=False)

    if result["success"]:
        videos.append(result["video_urls"][0])
        print(f"✅ Success! URL: {result['video_urls'][0][:50]}...")
    else:
        print("⏳ Still processing...")

    time.sleep(5)  # Be nice to the API

print(f"\n🎉 Generated {len(videos)} videos successfully!")
```

**Output:**

```
🎬 Generating video 1/3: A futuristic city with flying cars at night
✅ Success! URL: https://scontent.xx.fbcdn.net/v/t66.36240-6/1234...

🎬 Generating video 2/3: Ocean waves crashing on a tropical beach
✅ Success! URL: https://scontent.xx.fbcdn.net/v/t66.36240-6/5678...

🎬 Generating video 3/3: Northern lights dancing over a snowy mountain
✅ Success! URL: https://scontent.xx.fbcdn.net/v/t66.36240-6/9012...

🎉 Generated 3 videos successfully!
```

### Example 3: Advanced Video Generation with Orientation

```python
from metaai_api import MetaAI

ai = MetaAI(cookies=cookies)

# Generate video with specific orientation (default is VERTICAL)
result = ai.generate_video(
    prompt="A time-lapse of a flower blooming",
    orientation="VERTICAL",   # Options: "LANDSCAPE", "VERTICAL", "SQUARE"
    wait_before_poll=15,      # Wait 15 seconds before checking
    max_attempts=50,          # Try up to 50 times
    wait_seconds=3,           # Wait 3 seconds between attempts
    verbose=True              # Show detailed progress
)

# Generate landscape video for widescreen
result_landscape = ai.generate_video(
    prompt="Panoramic view of sunset over mountains",
    orientation="LANDSCAPE"   # Wide format (16:9)
)

if result["success"]:
    print(f"\n🎬 Your videos are ready!")
    print(f"🔗 Generated {len(result['video_urls'])} videos:")
    for i, url in enumerate(result['video_urls'], 1):
        print(f"   Video {i}: {url}")
    print(f"⏱️ Generated at: {result['timestamp']}")
```

**Supported Video Orientations:**

- `"LANDSCAPE"` - Wide/horizontal (16:9) - ideal for widescreen, cinematic content
- `"VERTICAL"` - Tall/vertical (9:16) - ideal for mobile, stories, reels (default)
- `"SQUARE"` - Equal dimensions (1:1) - ideal for social posts

````

📖 **Full Video Guide:** See [VIDEO_GENERATION_README.md](https://github.com/mir-ashiq/metaai-api/blob/main/VIDEO_GENERATION_README.md) for complete documentation!

---

## 📤 Image Upload & Analysis

Upload images to Meta AI for analysis, similar image generation, and video creation:

### Upload & Analyze Images

```python
from metaai_api import MetaAI

# Initialize with Facebook cookies (required for image operations)
ai = MetaAI(cookies={
    "datr": "your_datr_cookie",
    "abra_sess": "your_abra_sess_cookie"
})

# Step 1: Upload an image
result = ai.upload_image("path/to/image.jpg")

if result["success"]:
    media_id = result["media_id"]
    metadata = {
        'file_size': result['file_size'],
        'mime_type': result['mime_type']
    }

    # Step 2: Analyze the image
    response = ai.prompt(
        message="What do you see in this image? Describe it in detail.",
        media_ids=[media_id],
        attachment_metadata=metadata
    )
    print(f"🔍 Analysis: {response['message']}")

    # Step 3: Generate similar images
    response = ai.prompt(
        message="Create a similar image in watercolor painting style",
        media_ids=[media_id],
        attachment_metadata=metadata,
        is_image_generation=True
    )
    print(f"🎨 Generated {len(response['media'])} similar images")

    # Step 4: Generate video from image
    video = ai.generate_video(
        prompt="generate a video with zoom in effect on this image",
        media_ids=[media_id],
        attachment_metadata=metadata
    )
    if video["success"]:
        print(f"🎬 Video: {video['video_urls'][0]}")
````

**Output:**

```
🔍 Analysis: The image captures a serene lake scene set against a majestic mountain backdrop. In the foreground, there's a small, golden-yellow wooden boat with a bright yellow canopy floating on calm, glass‑like water...

🎨 Generated 4 similar images

🎬 Video: https://scontent.fsxr1-2.fna.fbcdn.net/o1/v/t6/f2/m421/video.mp4
```

📖 **Full Image Upload Guide:** See [IMAGE_UPLOAD_README.md](IMAGE_UPLOAD_README.md) for complete documentation!

---

## 🎨 Image Generation

Generate AI-powered images with customizable orientations (requires Facebook authentication):

```python
from metaai_api import MetaAI

# Initialize with Facebook credentials
ai = MetaAI(fb_email="your_email@example.com", fb_password="your_password")

# Generate images with default orientation (VERTICAL)
response = ai.prompt("Generate an image of a cyberpunk cityscape at night with neon lights")

# Or specify orientation explicitly
response_landscape = ai.prompt(
    "Generate an image of a panoramic mountain landscape",
    orientation="LANDSCAPE"  # Options: "LANDSCAPE", "VERTICAL", "SQUARE"
)

response_vertical = ai.prompt(
    "Generate an image of a tall waterfall",
    orientation="VERTICAL"  # Tall/portrait format (default)
)

response_square = ai.prompt(
    "Generate an image of a centered mandala pattern",
    orientation="SQUARE"  # Square format (1:1)
)

# Display results (Meta AI generates 4 images by default)
print(f"🎨 Generated {len(response['media'])} images:")
for i, image in enumerate(response['media'], 1):
    print(f"  Image {i}: {image['url']}")
    print(f"  Prompt: {image['prompt']}")
```

**Supported Orientations:**

- `"LANDSCAPE"` - Wide/horizontal format (16:9) - ideal for panoramas, landscapes
- `"VERTICAL"` - Tall/vertical format (9:16) - ideal for portraits, mobile content (default)
- `"SQUARE"` - Equal dimensions (1:1) - ideal for social media, profile images

**Output:**

```
🎨 Generated 4 images:
  Image 1: https://scontent.xx.fbcdn.net/o1/v/t0/f1/m247/img1.jpeg
  Prompt: a cyberpunk cityscape at night with neon lights

  Image 2: https://scontent.xx.fbcdn.net/o1/v/t0/f1/m247/img2.jpeg
  Prompt: a cyberpunk cityscape at night with neon lights

  Image 3: https://scontent.xx.fbcdn.net/o1/v/t0/f1/m247/img3.jpeg
  Prompt: a cyberpunk cityscape at night with neon lights

  Image 4: https://scontent.xx.fbcdn.net/o1/v/t0/f1/m247/img4.jpeg
  Prompt: a cyberpunk cityscape at night with neon lights
```

---

## 💡 Examples

Explore working examples in the `examples/` directory:

| File                                                                     | Description             | Features                               |
| ------------------------------------------------------------------------ | ----------------------- | -------------------------------------- |
| 📄 **[image_workflow_complete.py](examples/image_workflow_complete.py)** | Complete image workflow | Upload, analyze, generate images/video |
| 📄 **[simple_example.py](examples/simple_example.py)**                   | Quick start guide       | Basic chat + video generation          |
| 📄 **[video_generation.py](examples/video_generation.py)**               | Video generation        | Multiple examples, error handling      |
| 📄 **[test_example.py](examples/test_example.py)**                       | Testing suite           | Validation and testing                 |

### Run an Example

```bash
# Clone the repository
git clone https://github.com/mir-ashiq/metaai-api.git
cd meta-ai-python

# Run simple example
python examples/simple_example.py

# Run video generation examples
python examples/video_generation.py
```

---

## 📖 Documentation

### 📚 Complete Guides

| Document                                                    | Description                             |
| ----------------------------------------------------------- | --------------------------------------- |
| 📘 **[Image Upload Guide](IMAGE_UPLOAD_README.md)**         | Complete image upload documentation     |
| 📘 **[Video Generation Guide](VIDEO_GENERATION_README.md)** | Complete video generation documentation |
| 📙 **[Quick Reference](QUICK_REFERENCE.md)**                | Fast lookup for common tasks            |
| 📙 **[Quick Usage](QUICK_USAGE.md)**                        | Image upload quick reference            |
| 📗 **[Architecture Guide](ARCHITECTURE.md)**                | Technical architecture details          |
| 📕 **[Contributing Guide](CONTRIBUTING.md)**                | How to contribute to the project        |
| 📔 **[Changelog](CHANGELOG.md)**                            | Version history and updates             |
| 📓 **[Security Policy](SECURITY.md)**                       | Security best practices                 |

### 🔧 API Reference

#### MetaAI Class

```python
class MetaAI:
    def __init__(
        self,
        fb_email: Optional[str] = None,
        fb_password: Optional[str] = None,
        cookies: Optional[dict] = None,
        proxy: Optional[dict] = None
    )
```

**Methods:**

- **`prompt(message, stream=False, new_conversation=False)`**
  - Send a chat message
  - Returns: `dict` with `message`, `sources`, and `media`

- **`generate_video(prompt, wait_before_poll=10, max_attempts=30, wait_seconds=5, verbose=True)`**
  - Generate a video from text
  - Returns: `dict` with `success`, `video_urls`, `conversation_id`, `prompt`, `timestamp`

#### VideoGenerator Class

```python
from metaai_api import VideoGenerator

# Direct video generation
generator = VideoGenerator(cookies_str="your_cookies_as_string")
result = generator.generate_video("your prompt here")

# One-liner generation
result = VideoGenerator.quick_generate(
    cookies_str="your_cookies",
    prompt="your prompt"
)
```

---

## 🎯 Use Cases

### 1. **Research Assistant**

```python
ai = MetaAI()
research = ai.prompt("Summarize recent breakthroughs in fusion energy")
print(research["message"])
# Get cited sources
for source in research["sources"]:
    print(f"📌 {source['title']}: {source['link']}")
```

### 2. **Content Creation**

```python
ai = MetaAI(cookies=cookies)

# Generate video content
promo_video = ai.generate_video("Product showcase with smooth camera movements")

# Generate images
thumbnails = ai.prompt("Generate a YouTube thumbnail for a tech review video")
```

### 3. **Educational Tool**

```python
ai = MetaAI()

# Explain complex topics
explanation = ai.prompt("Explain blockchain technology to a 10-year-old")

# Get homework help
solution = ai.prompt("Solve: 2x + 5 = 13, show steps")
```

### 4. **Real-time Information**

```python
ai = MetaAI()

# Current events
news = ai.prompt("What are the top technology news today?")

# Sports scores
scores = ai.prompt("Latest Premier League scores")

# Market data
stocks = ai.prompt("Current S&P 500 index value")
```

---

## 🛠️ Advanced Configuration

### Environment Variables

Store credentials securely:

```bash
# .env file
META_AI_DATR=your_datr_value
META_AI_ABRA_SESS=your_abra_sess_value
META_AI_ECTO_1_SESS=your_ecto_1_sess_value
```

Load in Python:

```python
from metaai_api import MetaAI

# Automatically loads from environment variables
ai = MetaAI()

# Or manually load with dotenv
import os
from dotenv import load_dotenv

load_dotenv()
cookies = {
    "datr": os.getenv("META_AI_DATR"),
    "abra_sess": os.getenv("META_AI_ABRA_SESS"),
    "ecto_1_sess": os.getenv("META_AI_ECTO_1_SESS")
}

ai = MetaAI(cookies=cookies)
```

### Error Handling

```python
from metaai_api import MetaAI

ai = MetaAI(cookies=cookies)

try:
    result = ai.generate_video("Your prompt")

    if result["success"]:
        print(f"✅ Video: {result['video_urls'][0]}")
    else:
        print("⏳ Video still processing, try again later")

except ValueError as e:
    print(f"❌ Configuration error: {e}")
except ConnectionError as e:
    print(f"❌ Network error: {e}")
except Exception as e:
    print(f"❌ Unexpected error: {e}")
```

---

## 🌟 Project Structure

```
meta-ai-python/
│
├── 📁 src/metaai_api/        # Core package
│   ├── __init__.py            # Package initialization
│   ├── main.py                # MetaAI class
│   ├── video_generation.py    # Video generation
│   ├── client.py              # Client utilities
│   ├── utils.py               # Helper functions
│   └── exceptions.py          # Custom exceptions
│
├── 📁 examples/               # Usage examples
│   ├── simple_example.py      # Quick start
│   ├── video_generation.py    # Video examples
│   └── test_example.py        # Testing
│
├── 📁 .github/                # GitHub configuration
│   ├── workflows/             # CI/CD pipelines
│   └── README.md
│
├── 📄 README.md               # This file
├── 📄 VIDEO_GENERATION_README.md
├── 📄 QUICK_REFERENCE.md
├── 📄 ARCHITECTURE.md
├── 📄 CONTRIBUTING.md
├── 📄 CHANGELOG.md
├── 📄 SECURITY.md
├── 📄 LICENSE                 # MIT License
├── 📄 setup.py                # Package setup
├── 📄 pyproject.toml          # Project metadata
└── 📄 requirements.txt        # Dependencies
```

---

## 🤝 Contributing

We welcome contributions! Here's how you can help:

1. **🐛 Report Bugs** - [Open an issue](https://github.com/mir-ashiq/metaai-api/issues)
2. **💡 Suggest Features** - Share your ideas
3. **📝 Improve Docs** - Help us document better
4. **🔧 Submit PRs** - Fix bugs or add features

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

---

## 📜 License

This project is licensed under the **MIT License** - see [LICENSE](LICENSE) for details.

### ⚖️ Disclaimer

This project is an **independent implementation** and is **not officially affiliated** with Meta Platforms, Inc. or any of its affiliates.

- ✅ Educational and development purposes
- ✅ Use responsibly and ethically
- ✅ Comply with Meta's Terms of Service
- ✅ Respect usage limits and policies

**Llama 3 License:** Visit [llama.com/llama3/license](https://www.llama.com/llama3/license/) for Llama 3 usage terms.

---

## 🙏 Acknowledgments

- **Meta AI** - For providing the AI capabilities
- **Llama 3** - The powerful language model
- **Open Source Community** - For inspiration and support

---

## 📞 Support & Community

- 💬 **Questions?** [GitHub Discussions](https://github.com/mir-ashiq/metaai-api/discussions)
- 🐛 **Bug Reports** [GitHub Issues](https://github.com/mir-ashiq/metaai-api/issues)
- 📧 **Contact** imseldrith@gmail.com
- ⭐ **Star us** on [GitHub](https://github.com/mir-ashiq/metaai-api)

---

## 🚀 Quick Links

<div align="center">

| Resource                  | Link                                                                                                                          |
| ------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| 📦 **PyPI Package**       | [pypi.org/project/metaai_api](https://pypi.org/project/metaai_api/)                                                           |
| 🐙 **GitHub Repository**  | [github.com/mir-ashiq/meta-ai-python](https://github.com/mir-ashiq/metaai-api)                                                |
| 📖 **Full Documentation** | [Video Guide](VIDEO_GENERATION_README.md) • [Quick Ref](QUICK_REFERENCE.md)                                                   |
| 💬 **Get Help**           | [Issues](https://github.com/mir-ashiq/metaai-api/issues) • [Discussions](https://github.com/mir-ashiq/metaai-api/discussions) |

---

<sub>**Meta AI Python SDK v2.0.0** | Made with ❤️ by [mir-ashiq](https://github.com/mir-ashiq) | MIT License</sub>

**⭐ Star this repo if you find it useful!**

</div>
