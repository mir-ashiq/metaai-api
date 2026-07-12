"""
MetaAI — Main entry point for the Meta AI SDK.

Provides image generation, chat, conversation management, media fetching,
and image upload. Uses browser automation as the primary method (works for
ANY prompt). Also supports legacy HTTP/WebSocket methods for advanced users.

```python
from metaai_api import MetaAI

ai = MetaAI(cookies={"datr": "...", "ecto_1_sess": "..."})

# Generate an image
result = ai.generate_image_new("a watercolor painting of a cat")
print(result["image_urls"])

# Chat
reply = ai.prompt("What is 2+2?")
print(reply["message"])

# List conversations
convs = ai.list_conversations()
```
"""
from __future__ import annotations

import logging
import os
import time
from typing import Any, Dict, Generator, List, Optional, Union

from .browser import BrowserBackend
from .client import MetaAIClient
from .exceptions import (
    AuthenticationError, GenerationError, MetaAIError, TimeoutError,
)
from .generation import GenerationAPI
from .utils import DEFAULT_UA, get_cookies_from_env, logger

__version__ = "5.2.0"


class MetaAI:
    """Meta AI SDK client.

    The main entry point for all Meta AI operations. Uses browser automation
    for image generation and chat, and HTTP/WebSocket for media fetching.

    Args:
        cookies: Dict with 'datr' and 'ecto_1_sess' keys.
            If None, loads from META_AI_DATR and META_AI_ECTO_1_SESS env vars.
        access_token: Optional DGW access token for WebSocket/media methods.
        headed: If True, show the browser window (debugging).
        session_name: Browser session name for isolation.
        user_agent: User-Agent string.

    Example:
        ```python
        ai = MetaAI(cookies={"datr": "...", "ecto_1_sess": "..."})
        result = ai.generate_image_new("a sunset")
        print(result["image_urls"])
        ai.close()
        ```
    """

    def __init__(
        self,
        cookies: Optional[Dict[str, str]] = None,
        access_token: Optional[str] = None,
        headed: bool = False,
        session_name: str = "metaai",
        user_agent: str = DEFAULT_UA,
        fb_email: Optional[str] = None,
        fb_password: Optional[str] = None,
    ):
        # Load cookies from env if not provided
        if cookies is None:
            cookies = get_cookies_from_env()

        if not cookies.get("datr") or not cookies.get("ecto_1_sess"):
            raise MetaAIError(
                "cookies with 'datr' and 'ecto_1_sess' are required.\n\n"
                "Get them from:\n"
                "1. Open https://www.meta.ai/ and log in\n"
                "2. DevTools (F12) → Application → Cookies\n"
                "3. Copy 'datr' and 'ecto_1_sess' values\n\n"
                "Or set env vars: META_AI_DATR and META_AI_ECTO_1_SESS"
            )

        self.cookies = cookies
        self.access_token = access_token or os.getenv("META_AI_ACCESS_TOKEN")
        self.headed = headed
        self.session_name = session_name
        self.user_agent = user_agent
        self.fb_email = fb_email
        self.fb_password = fb_password

        # Initialize HTTP/WebSocket client
        self.client = MetaAIClient(
            cookies=cookies,
            access_token=self.access_token,
            user_agent=user_agent,
        )

        # Initialize browser backend (lazy — starts on first use)
        self._browser: Optional[BrowserBackend] = None

        # Initialize generation API
        self.generation_api = GenerationAPI(
            session=self.client.session,
            cookies=cookies,
            access_token=self.access_token,
        )

    def _get_browser(self):
        """Get or create the browser backend.

        Automatically selects Playwright (pure Python, no Node.js) if available,
        otherwise falls back to agent-browser.
        """
        if self._browser is None:
            # Try Playwright first (works on Colab, no Node.js needed)
            try:
                from .playwright_backend import PlaywrightBackend
                self._browser = PlaywrightBackend(
                    cookies=self.cookies,
                    headed=self.headed,
                    session_name=self.session_name,
                    user_agent=self.user_agent,
                )
                logger.info("Using Playwright backend")
            except ImportError:
                # Fall back to agent-browser
                self._browser = BrowserBackend(
                    cookies=self.cookies,
                    headed=self.headed,
                    session_name=self.session_name,
                    user_agent=self.user_agent,
                )
                logger.info("Using agent-browser backend")
            self._browser.setup()
            self.generation_api.browser = self._browser
        return self._browser

    # ================================================================
    # Image Generation
    # ================================================================

    def generate_image_new(
        self,
        prompt: str,
        orientation: str = "VERTICAL",
        num_images: int = 1,
        **kwargs,
    ) -> Dict[str, Any]:
        """Generate images using the new API (browser method).

        Args:
            prompt: Text description of the image to generate.
            orientation: Image orientation - "VERTICAL", "HORIZONTAL", or "SQUARE".
            num_images: Number of images to generate (default: 1).
            **kwargs: Additional parameters (timeout, etc.).

        Returns:
            Dictionary with 'success', 'image_urls', 'conversation_id', etc.

        Example:
            ```python
            result = ai.generate_image_new("a watercolor of a cat")
            if result["success"]:
                for url in result["image_urls"]:
                    print(url)
            ```
        """
        timeout = kwargs.get("timeout", 120)
        self._get_browser()  # Ensure browser is initialized
        return self.generation_api.generate_image(prompt, timeout=timeout)

    def generate_image(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Alias for generate_image_new (backward compatibility)."""
        return self.generate_image_new(prompt, **kwargs)

    # ================================================================
    # Video Generation (NOT AVAILABLE on Meta AI)
    # ================================================================

    def generate_video_new(
        self,
        prompt: str,
        auto_poll: bool = True,
        max_poll_attempts: int = 15,
        poll_wait_seconds: int = 3,
        **kwargs,
    ) -> Dict[str, Any]:
        """Generate video using the new API.

        NOTE: Video generation is NOT currently available on Meta AI.
        Meta AI responds: "I can't generate videos right now."

        Raises:
            GenerationError: Video generation is not available.
        """
        timeout = kwargs.get("timeout", 180)
        return self.generation_api.generate_video(prompt, timeout=timeout)

    def generate_video(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Alias for generate_video_new (backward compatibility)."""
        return self.generate_video_new(prompt, **kwargs)

    def extend_video(
        self,
        media_id: str,
        source_media_url: Optional[str] = None,
        conversation_id: Optional[str] = None,
        auto_poll: bool = True,
        max_poll_attempts: int = 15,
        poll_wait_seconds: int = 3,
        **kwargs,
    ) -> Dict[str, Any]:
        """Extend an existing video.

        NOTE: Video generation is NOT currently available on Meta AI.

        Raises:
            GenerationError: Video generation is not available.
        """
        raise GenerationError(
            "Video generation (extend) is not available on Meta AI. "
            "Meta AI does not currently support video generation."
        )

    # ================================================================
    # Chat
    # ================================================================

    def prompt(
        self,
        message: str,
        stream: bool = False,
        attempts: int = 0,
        new_conversation: bool = True,
        images: Optional[list] = None,
        media_ids: Optional[list] = None,
        attachment_metadata: Optional[Dict[str, Any]] = None,
        is_image_generation: bool = False,
        orientation: Optional[str] = None,
        timeout: int = 60,
        thinking_mode: bool = False,
        **kwargs,
    ) -> Union[Dict, Generator[Dict, None, None]]:
        """Send a chat prompt to Meta AI.

        Args:
            message: The text to send.
            stream: If True, returns a streaming response (not yet supported via browser).
            attempts: Number of retry attempts (backward compat).
            new_conversation: If True, starts a new conversation.
            images: List of image paths (not yet supported via browser).
            media_ids: List of media IDs for attachments.
            attachment_metadata: Attachment metadata.
            is_image_generation: Whether this is an image generation request.
            orientation: Image orientation (for image generation).
            timeout: Max seconds to wait.
            thinking_mode: If True, uses Thinking mode for longer reasoning.

        Returns:
            Dictionary with 'message', 'conversation_id', etc.

        Example:
            ```python
            reply = ai.prompt("What is the capital of France?")
            print(reply["message"])
            ```
        """
        self._get_browser()  # Ensure browser is initialized
        if new_conversation:
            self._browser.new_chat()

        result = self._browser.send_message(message, timeout=timeout, thinking_mode=thinking_mode)
        return {
            "message": result.get("text", ""),
            "conversation_id": result.get("conversation_id"),
            "raw": result,
        }

    def retry(self, message: str, stream: bool = False, attempts: int = 0,
              new_conversation: bool = False, **kwargs) -> Dict[str, Any]:
        """Retry a prompt (backward compatibility)."""
        return self.prompt(message, stream=stream, new_conversation=new_conversation, **kwargs)

    # ================================================================
    # Conversation Management
    # ================================================================

    def list_conversations(self) -> List[Dict[str, str]]:
        """List all conversations from the sidebar.

        Returns:
            List of dicts with 'id', 'title', 'url' keys.
        """
        self._get_browser()  # Ensure browser is initialized
        return self._browser.list_conversations()

    def new_conversation(self) -> None:
        """Start a new chat conversation."""
        self._get_browser()  # Ensure browser is initialized
        self._browser.new_chat()

    # ================================================================
    # Media Fetching (HTTP)
    # ================================================================

    def fetch_card_media(self, card_id: str, card_type: str = "IMAGE_CARD") -> Dict[str, Any]:
        """Fetch media URLs by card ID via HTTP GraphQL.

        Args:
            card_id: Card ID from meta.ai/create/{card_id}.
            card_type: "IMAGE_CARD" or "VIDEO_CARD".

        Returns:
            GraphQL response with image/video URLs.
        """
        return self.generation_api.fetch_imagine_card_media(card_id, card_type)

    # ================================================================
    # DGW Frame Replay (Advanced)
    # ================================================================

    def replay_frame(self, frame_b64: str, timeout: int = 90) -> Dict[str, Any]:
        """Replay a captured DGW DATA frame (advanced method).

        Each frame can only be replayed once (server enforces idempotency).
        Requires access_token.

        Args:
            frame_b64: Base64-encoded DATA frame from browser DevTools.
            timeout: Response timeout in seconds.

        Returns:
            Dict with image_urls, video_urls, conversation_id, message_count.
        """
        return self.client.replay_frame(frame_b64, timeout=timeout)

    # ================================================================
    # Warmup
    # ================================================================

    def warmup_conversation(self, conversation_id: str) -> bool:
        """Register a new conversation_id with the server.

        Args:
            conversation_id: A UUID for the new conversation.

        Returns:
            True if warmup succeeded.
        """
        return self.client.warmup_conversation(conversation_id)

    # ================================================================
    # Cookie Management (backward compat)
    # ================================================================

    def get_cookies(self) -> dict:
        """Return the current cookies dict."""
        return self.cookies

    def get_cookies_dict(self) -> Dict[str, str]:
        """Return the current cookies as a dict (backward compat)."""
        return self.cookies

    def get_cookie_header(self) -> str:
        """Return cookies as a Cookie header string."""
        parts = []
        for k, v in self.cookies.items():
            parts.append(f"{k}={v}")
        return "; ".join(parts)

    def get_access_token(self) -> Optional[str]:
        """Return the access token (if set)."""
        return self.access_token

    # ================================================================
    # Cleanup
    # ================================================================

    def close(self) -> None:
        """Close the browser session."""
        if self._browser is not None:
            self._browser.close()
            self._browser = None

    def __enter__(self) -> "MetaAI":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
