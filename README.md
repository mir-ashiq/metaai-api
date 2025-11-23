<div align="center">

# 🤖 Meta AI Python SDK

[![Python Version](https://img.shields.io/badge/python-3.7%2B-blue?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green?style=for-the-badge)](LICENSE)
[![PyPI](https://img.shields.io/badge/PyPI-v2.0.0-orange?style=for-the-badge&logo=pypi&logoColor=white)](https://pypi.org/project/metaai-api/)
[![GitHub](https://img.shields.io/badge/GitHub-mir--ashiq-black?style=for-the-badge&logo=github)](https://github.com/mir-ashiq/meta-ai-python)

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

| Feature                      | Description                                  | Status   |
| ---------------------------- | -------------------------------------------- | -------- |
| 💬 **Intelligent Chat**      | Powered by Llama 3 with internet access      | ✅ Ready |
| 🎨 **Image Generation**      | Create stunning AI-generated images          | ✅ Ready |
| 🎬 **Video Generation**      | Generate videos from text prompts            | ✅ Ready |
| 🌐 **Real-time Data**        | Get current information via Bing integration | ✅ Ready |
| 📚 **Source Citations**      | Responses include verifiable sources         | ✅ Ready |
| 🔄 **Streaming Support**     | Real-time response streaming                 | ✅ Ready |
| 🔐 **Auto Token Management** | Automatic authentication handling            | ✅ Ready |
| 🌍 **Proxy Support**         | Route requests through proxies               | ✅ Ready |

---

## 📦 Installation

```bash
# Quick install from PyPI
pip install metaai-api

# Or clone from GitHub
git clone https://github.com/mir-ashiq/meta-ai-python.git
cd meta-ai-python
pip install -e .
```

**System Requirements:** Python 3.7+ • Internet Connection • That's it!

---

## 🚀 Quick Start

### Example 1: Ask a Question

```python
from metaai_api import MetaAI

# Initialize the AI
ai = MetaAI()

# Ask anything!
response = ai.prompt("Who won the NBA championship in 2024?")
print(response["message"])
```

**Output:**

```
The Boston Celtics won the 2024 NBA Championship, defeating the Dallas Mavericks
4-1 in the Finals. Jayson Tatum and Jaylen Brown led the Celtics to their 18th
championship title, the most in NBA history. The series concluded on June 17, 2024,
with the Celtics winning Game 5 at TD Garden in Boston.
```

### Example 2: Get Stock Market Info

```python
from meta_ai_api import MetaAI

ai = MetaAI()
response = ai.prompt("What is the current price of Bitcoin?")

print(f"💰 {response['message']}")
print(f"\n📚 Sources: {len(response['sources'])} references found")
```

**Output:**

```
💰 As of November 22, 2025, Bitcoin (BTC) is trading at approximately $97,845 USD.
The cryptocurrency has seen a 3.2% increase in the last 24 hours. Bitcoin's market
capitalization stands at around $1.93 trillion, maintaining its position as the
largest cryptocurrency by market cap.

📚 Sources: 4 references found
```

### Example 3: Solve Math Problems

```python
from meta_ai_api import MetaAI

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

## 💬 Chat Features

### Streaming Responses

Watch responses appear in real-time, like ChatGPT:

```python
from meta_ai_api import MetaAI

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
from meta_ai_api import MetaAI

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
from meta_ai_api import MetaAI

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

## 🎬 Video Generation

Create AI-generated videos from text descriptions!

### Setup: Get Your Cookies

1. Visit [meta.ai](https://www.meta.ai) in your browser
2. Open DevTools (F12) → **Network** tab
3. Refresh the page
4. Click any request → **Headers** → Copy **Cookie** value
5. Extract these values: `datr`, `abra_sess`, `dpr`, `wd`

### Example 1: Generate Your First Video

```python
from meta_ai_api import MetaAI

# Your browser cookies
cookies = {
    "datr": "your_datr_value_here",
    "abra_sess": "your_abra_sess_value_here",
    "dpr": "1.25",
    "wd": "1920x1080"
}

# Initialize with cookies
ai = MetaAI(cookies=cookies)

# Generate a video
result = ai.generate_video("A majestic lion walking through the African savanna at sunset")

if result["success"]:
    print("✅ Video generated successfully!")
    print(f"🎬 Generated {len(result['video_urls'])} videos (Meta AI creates 4 by default)")
    for i, url in enumerate(result['video_urls'], 1):
        print(f"   Video {i}: {url}")
    print(f"📝 Prompt: {result['prompt']}")
    print(f"🆔 Conversation ID: {result['conversation_id']}")
else:
    print("⏳ Video is still processing, try again in a moment")
```

**Output:**

```
[*] Fetching missing tokens (lsd, fb_dtsg) from Meta AI...
[✓] Fetched lsd: AVrvi8aHxzQ
[✓] Fetched fb_dtsg: BQAB9uRXmPEYGkC...

✅ Sending video generation request...
✅ Video generation request sent successfully!
⏳ Waiting 10 seconds before polling...
🔄 Polling for video URLs (Attempt 1/30)...
✅ Video URLs found!

✅ Video generated successfully!
🎬 Generated 4 videos (Meta AI creates 4 by default)
   Video 1: https://scontent.xx.fbcdn.net/v/t66.36240-6/video1.mp4?...
   Video 2: https://scontent.xx.fbcdn.net/v/t66.36240-6/video2.mp4?...
   Video 3: https://scontent.xx.fbcdn.net/v/t66.36240-6/video3.mp4?...
   Video 4: https://scontent.xx.fbcdn.net/v/t66.36240-6/video4.mp4?...
📝 Prompt: A majestic lion walking through the African savanna at sunset
🆔 Conversation ID: abc123-def456-ghi789
```

### Example 2: Generate Multiple Videos

```python
from meta_ai_api import MetaAI
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

### Example 3: Advanced Video Generation

```python
from meta_ai_api import MetaAI

ai = MetaAI(cookies=cookies)

# Fine-tune generation parameters
result = ai.generate_video(
    prompt="A time-lapse of a flower blooming",
    wait_before_poll=15,      # Wait 15 seconds before checking
    max_attempts=50,          # Try up to 50 times
    wait_seconds=3,           # Wait 3 seconds between attempts
    verbose=True              # Show detailed progress
)

if result["success"]:
    print(f"\n🎬 Your videos are ready!")
    print(f"🔗 Generated {len(result['video_urls'])} videos:")
    for i, url in enumerate(result['video_urls'], 1):
        print(f"   Video {i}: {url}")
    print(f"⏱️ Generated at: {result['timestamp']}")
```

📖 **Full Video Guide:** See [VIDEO_GENERATION_README.md](VIDEO_GENERATION_README.md) for complete documentation!

---

## 🎨 Image Generation

Generate AI-powered images (requires Facebook authentication):

```python
from meta_ai_api import MetaAI

# Initialize with Facebook credentials
ai = MetaAI(fb_email="your_email@example.com", fb_password="your_password")

# Generate images
response = ai.prompt("Generate an image of a cyberpunk cityscape at night with neon lights")

# Display results (Meta AI generates 4 images by default)
print(f"🎨 Generated {len(response['media'])} images:")
for i, image in enumerate(response['media'], 1):
    print(f"  Image {i}: {image['url']}")
    print(f"  Prompt: {image['prompt']}")
```

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

| File                                                       | Description       | Features                          |
| ---------------------------------------------------------- | ----------------- | --------------------------------- |
| 📄 **[simple_example.py](examples/simple_example.py)**     | Quick start guide | Basic chat + video generation     |
| 📄 **[video_generation.py](examples/video_generation.py)** | Video generation  | Multiple examples, error handling |
| 📄 **[test_example.py](examples/test_example.py)**         | Testing suite     | Validation and testing            |

### Run an Example

```bash
# Clone the repository
git clone https://github.com/mir-ashiq/meta-ai-python.git
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
| 📘 **[Video Generation Guide](VIDEO_GENERATION_README.md)** | Complete video generation documentation |
| 📙 **[Quick Reference](QUICK_REFERENCE.md)**                | Fast lookup for common tasks            |
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
from meta_ai_api import VideoGenerator

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
META_AI_DPR=1.25
META_AI_WD=1920x1080
```

Load in Python:

```python
import os
from dotenv import load_dotenv
from meta_ai_api import MetaAI

load_dotenv()

cookies = {
    "datr": os.getenv("META_AI_DATR"),
    "abra_sess": os.getenv("META_AI_ABRA_SESS"),
    "dpr": os.getenv("META_AI_DPR"),
    "wd": os.getenv("META_AI_WD")
}

ai = MetaAI(cookies=cookies)
```

### Error Handling

```python
from meta_ai_api import MetaAI

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
├── 📁 src/meta_ai_api/        # Core package
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

1. **🐛 Report Bugs** - [Open an issue](https://github.com/mir-ashiq/meta-ai-python/issues)
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

- 💬 **Questions?** [GitHub Discussions](https://github.com/mir-ashiq/meta-ai-python/discussions)
- 🐛 **Bug Reports** [GitHub Issues](https://github.com/mir-ashiq/meta-ai-python/issues)
- 📧 **Contact** contact@meta-ai-sdk.dev
- ⭐ **Star us** on [GitHub](https://github.com/mir-ashiq/meta-ai-python)

---

## 🚀 Quick Links

<div align="center">

| Resource                  | Link                                                                                                                                  |
| ------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| 📦 **PyPI Package**       | [pypi.org/project/metaai_api](https://pypi.org/project/metaai_api/)                                                                   |
| 🐙 **GitHub Repository**  | [github.com/mir-ashiq/meta-ai-python](https://github.com/mir-ashiq/meta-ai-python)                                                    |
| 📖 **Full Documentation** | [Video Guide](VIDEO_GENERATION_README.md) • [Quick Ref](QUICK_REFERENCE.md)                                                           |
| 💬 **Get Help**           | [Issues](https://github.com/mir-ashiq/meta-ai-python/issues) • [Discussions](https://github.com/mir-ashiq/meta-ai-python/discussions) |

---

<sub>**Meta AI Python SDK v2.0.0** | Made with ❤️ by [mir-ashiq](https://github.com/mir-ashiq) | MIT License</sub>

**⭐ Star this repo if you find it useful!**

</div>
