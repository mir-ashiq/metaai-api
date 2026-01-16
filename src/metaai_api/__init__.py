"""MetaAI API - Python SDK for Meta AI powered by Llama 3.

A modern, feature-rich Python SDK providing seamless access to Meta AI's capabilities:
- Chat with Llama 3 (with real-time internet access)
- Generate AI images
- Create AI videos from text prompts
- Upload images for analysis and generation
- No API key required
"""

__version__ = "2.0.0"
__author__ = "Ashiq Hussain Mir"
__license__ = "MIT"
__url__ = "https://github.com/mir-ashiq/metaai-api"

from .main import MetaAI  # noqa
from .client import send_animate_request
from .video_generation import VideoGenerator  # noqa
from .image_upload import ImageUploader  # noqa

__all__ = ["MetaAI", "send_animate_request", "VideoGenerator", "ImageUploader"]

