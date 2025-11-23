# Meta AI Python SDK

> A powerful, feature-rich Python SDK for Meta AI - Chat, Image & Video Generation

[![Python](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![PyPI](https://img.shields.io/badge/pypi-v2.0.0-blue.svg)](https://pypi.org/project/metaai_api/)
[![CI](https://github.com/meta-ai-sdk/meta-ai-python/workflows/CI/badge.svg)](https://github.com/meta-ai-sdk/meta-ai-python/actions)

## Overview

This SDK provides seamless access to Meta AI's capabilities including:

- 💬 **Chat** - Powered by Llama 3 with real-time internet access
- 🎨 **Image Generation** - Create AI-generated images
- 🎬 **Video Generation** - Generate videos from text prompts
- 🌐 **Real-time Information** - Get up-to-date info via Bing
- 🔐 **No API Key** - Uses browser cookies for authentication

## Quick Links

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Video Generation](VIDEO_GENERATION_README.md)
- [API Reference](VIDEO_GENERATION_README.md#api-reference)
- [Examples](examples/)
- [Contributing](CONTRIBUTING.md)
- [Changelog](CHANGELOG.md)

## Installation

```bash
pip install metaai_api
```

## Quick Start

```python
from meta_ai_api import MetaAI

# Initialize
ai = MetaAI()

# Chat
response = ai.prompt("What's the weather today?")
print(response["message"])
```

## Documentation

- **[Complete README](README.md)** - Full documentation
- **[Video Generation Guide](VIDEO_GENERATION_README.md)** - Detailed video generation docs
- **[Quick Reference](QUICK_REFERENCE.md)** - Fast lookup guide
- **[Contributing](CONTRIBUTING.md)** - How to contribute

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Disclaimer

This project is independent and not officially affiliated with Meta Platforms, Inc.

---

**Made with ❤️ for the AI community**
