"""Image and video generation API for Meta AI.

Based on captured network requests from meta.ai. Uses both browser
automation (primary) and DGW WebSocket (advanced) methods.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from .browser import BrowserBackend
from .client import MetaAIClient
from .exceptions import GenerationError
from .utils import is_media_url, logger

# Persisted-query doc_ids (discovered in Meta's web JS)
FETCH_IMAGINE_CARD_MEDIA_DOC_ID = "344570a4b8110dd9848829731d35c74a"
VIDEO_POLLING_SUBSCRIPTION_DOC_ID = "9928a9b87ec492a16326f18925191c0f"


class GenerationAPI:
    """
    Image and Video Generation API based on Meta AI GraphQL patterns.

    This class provides both browser-based (primary) and WebSocket-based
    (advanced) methods for generating images and fetching media.
    """

    ENDPOINT = "https://www.meta.ai/api/graphql"

    def __init__(self, session=None, cookies: Optional[Dict] = None,
                 access_token: Optional[str] = None,
                 browser: Optional[BrowserBackend] = None):
        """Initialize Generation API.

        Args:
            session: Optional requests.Session (legacy compatibility).
            cookies: Optional cookies dictionary.
            access_token: Optional DGW access token for WebSocket method.
            browser: Optional BrowserBackend instance for browser method.
        """
        self.session = session
        self.cookies = cookies or {}
        self.access_token = access_token
        self.browser = browser

        if session is None and cookies:
            import requests
            self.session = requests.Session()
            self.session.cookies.update(cookies)

        self.logger = logging.getLogger(__name__)

    def generate_image(self, prompt: str, timeout: int = 120) -> Dict[str, Any]:
        """Generate an image using the browser method.

        Args:
            prompt: Text description of the image.
            timeout: Max seconds to wait.

        Returns:
            Response dict with 'images', 'success', 'prompt', etc.
        """
        if not self.browser:
            raise GenerationError("Browser backend is required for image generation")

        result = self.browser.send_message(prompt, timeout=timeout)
        urls = result.get("urls", [])
        text = result.get("text", "")

        if not urls:
            raise GenerationError(
                "No image URLs returned.",
                detail=f"Prompt: {prompt!r}, text: {text[:200]}",
            )

        return {
            "success": True,
            "prompt": prompt,
            "image_urls": urls,
            "images": urls,
            "conversation_id": result.get("conversation_id"),
            "raw": result,
        }

    def generate_image_new(self, prompt: str, orientation: str = "VERTICAL",
                           num_images: int = 1, **kwargs) -> Dict[str, Any]:
        """Generate images using the browser method (new API).

        Args:
            prompt: Text description of the image.
            orientation: Image orientation (VERTICAL, HORIZONTAL, SQUARE).
            num_images: Number of images (browser typically generates 1-4).
            **kwargs: Additional parameters.

        Returns:
            Dictionary with response data and extracted image URLs.
        """
        return self.generate_image(prompt, timeout=kwargs.get("timeout", 120))

    def generate_video(self, prompt: str, timeout: int = 180) -> Dict[str, Any]:
        """Attempt to generate a video.

        NOTE: Video generation is NOT currently available on Meta AI.
        Meta AI responds: "I can't generate videos right now."

        Args:
            prompt: Text description of the video.
            timeout: Max seconds to wait.

        Raises:
            GenerationError: Video generation is not available.
        """
        if not self.browser:
            raise GenerationError("Browser backend is required")

        result = self.browser.send_message(prompt, timeout=timeout)
        urls = result.get("urls", [])
        text = result.get("text", "")

        # Check if any URL is actually a video
        if urls:
            import requests
            for url in urls:
                try:
                    r = requests.head(url, timeout=10)
                    ct = r.headers.get("Content-Type", "")
                    if "video" in ct or ".mp4" in url:
                        return {
                            "success": True,
                            "prompt": prompt,
                            "video_urls": urls,
                            "videos": urls,
                            "conversation_id": result.get("conversation_id"),
                            "raw": result,
                        }
                except Exception:
                    pass

        raise GenerationError(
            "Video generation is not available on Meta AI. "
            "Meta AI responded: " + (text[:200] if text else "(no response)"),
            detail=f"Prompt: {prompt!r}",
        )

    def fetch_imagine_card_media(self, card_id: str, card_type: str = "IMAGE_CARD",
                                  **kwargs) -> Dict[str, Any]:
        """Fetch an imagine card's media by card ID.

        Uses the fetchImagineCardMediaQuery persisted query.

        Args:
            card_id: The card ID (from meta.ai/create/{card_id}).
            card_type: "IMAGE_CARD" or "VIDEO_CARD".

        Returns:
            Parsed GraphQL response.
        """
        if self.session:
            r = self.session.post(
                self.ENDPOINT,
                json={
                    "doc_id": FETCH_IMAGINE_CARD_MEDIA_DOC_ID,
                    "variables": {"cardId": str(card_id), "cardType": card_type},
                },
                headers={
                    "User-Agent": kwargs.get("user_agent", "Mozilla/5.0"),
                    "Content-Type": "application/json",
                    "Origin": "https://www.meta.ai",
                    "Referer": "https://www.meta.ai/",
                    **({"Authorization": f"ecto1:{self.access_token}"} if self.access_token else {}),
                },
                timeout=30,
            )
            r.raise_for_status()
            return r.json()
        raise GenerationError("No session available for HTTP requests")

    def extract_media_urls(self, response_data: Dict[str, Any]) -> List[str]:
        """Extract media URLs from a response."""
        urls = []
        try:
            media = response_data.get("data", {}).get("imagineCardMedia", {})
            for img in media.get("images", []) or []:
                url = img.get("url") or img.get("fallbackUrl")
                if url:
                    urls.append(url)
            for vid in media.get("videos", []) or []:
                url = vid.get("url") or vid.get("fallbackUrl")
                if url:
                    urls.append(url)
        except (KeyError, TypeError):
            pass
        return urls
