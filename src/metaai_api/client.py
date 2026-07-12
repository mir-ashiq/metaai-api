"""HTTP and WebSocket client for Meta AI.

Handles:
- Cookie-based authentication
- DGW WebSocket frame replay
- HTTP GraphQL queries (warmupConversation, fetchImagineCardMedia)
"""
from __future__ import annotations

import asyncio
import base64
import json
import logging
import re
import time
import uuid
from typing import Any, Dict, List, Optional, Set
from urllib.parse import urlencode

import requests

from .exceptions import (
    AuthenticationError, ConnectionError, GenerationError,
)
from .parser import build_estab_stream_frame, parse_frame
from .utils import (
    DEFAULT_UA, WARMUP_MUTATION_DOC_ID, FETCH_CARD_MEDIA_DOC_ID,
    DGW_APP_ID, DGW_APP_VERSION, DGW_AUTH_TYPE, DGW_VERSION,
    DGW_UUID, DGW_TIER, DGW_APP_ORIGIN, logger,
)

try:
    import websockets
except ImportError:
    websockets = None


class MetaAIClient:
    """Low-level HTTP/WebSocket client for Meta AI.

    This class handles the direct communication with Meta AI servers.
    Users typically interact with the higher-level MetaAI class instead.
    """

    def __init__(self, cookies: dict, access_token: Optional[str] = None,
                 user_agent: str = DEFAULT_UA):
        self.cookies = cookies
        self.access_token = access_token
        self.user_agent = user_agent
        self.session = requests.Session()
        if cookies:
            self.session.cookies.update(cookies)

    @property
    def datr(self) -> str:
        return self.cookies.get("datr", "")

    @property
    def ecto_1_sess(self) -> str:
        return self.cookies.get("ecto_1_sess", "")

    def _cookie_header(self) -> str:
        parts = [f"datr={self.datr}", f"ecto_1_sess={self.ecto_1_sess}"]
        if self.cookies.get("abra_sess"):
            parts.append(f"abra_sess={self.cookies['abra_sess']}")
        return "; ".join(parts)

    def _ws_url(self) -> str:
        if not self.access_token:
            raise ConnectionError("access_token is required for WebSocket method")
        params = {
            "x-dgw-appid": DGW_APP_ID,
            "x-dgw-appversion": DGW_APP_VERSION,
            "x-dgw-authtype": DGW_AUTH_TYPE,
            "x-dgw-version": DGW_VERSION,
            "x-dgw-uuid": DGW_UUID,
            "x-dgw-tier": DGW_TIER,
            "Authorization": f"ecto1:{self.access_token}",
            "x-dgw-app-origin": DGW_APP_ORIGIN,
            "x-dgw-app-clippy-request-id": str(uuid.uuid4()),
        }
        return f"wss://gateway.meta.ai/ws/clippy?{urlencode(params)}"

    def warmup_conversation(self, conversation_id: str) -> bool:
        """Register a new conversation_id with the server via HTTP mutation."""
        r = self.session.post(
            "https://www.meta.ai/api/graphql",
            json={"doc_id": WARMUP_MUTATION_DOC_ID,
                  "variables": {"conversationId": conversation_id}},
            headers={
                "User-Agent": self.user_agent,
                "Content-Type": "application/json",
                "Origin": "https://www.meta.ai",
                **({"Authorization": f"ecto1:{self.access_token}"} if self.access_token else {}),
            },
            timeout=15,
        )
        if r.status_code != 200:
            return False
        try:
            return r.json().get("data", {}).get("warmupConversation") is True
        except Exception:
            return False

    def fetch_card_media(self, card_id: str, card_type: str = "IMAGE_CARD") -> Dict[str, Any]:
        """Fetch media URLs by card ID via HTTP GraphQL."""
        r = self.session.post(
            "https://www.meta.ai/api/graphql",
            json={"doc_id": FETCH_CARD_MEDIA_DOC_ID,
                  "variables": {"cardId": str(card_id), "cardType": card_type}},
            headers={
                "User-Agent": self.user_agent,
                "Content-Type": "application/json",
                "Origin": "https://www.meta.ai",
                **({"Authorization": f"ecto1:{self.access_token}"} if self.access_token else {}),
            },
            timeout=30,
        )
        r.raise_for_status()
        return r.json()

    def replay_frame(self, frame_b64: str, timeout: int = 90) -> Dict[str, Any]:
        """Replay a captured DGW DATA frame via WebSocket."""
        if websockets is None:
            raise ConnectionError("websockets not installed. Run: pip install websockets")

        raw = base64.b64decode(frame_b64)
        json_start = raw.find(b"{")
        if json_start < 0:
            raise GenerationError("Invalid frame: no JSON found")

        outer = json.loads(raw[json_start:].decode("utf-8"))
        req_id = outer.get("req-id", "")

        inner = base64.b64decode(outer.get("payload", ""))
        inner_text = inner.decode("utf-8", errors="replace")
        uuids = re.findall(
            r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',
            inner_text,
        )
        conv_id = uuids[0] if uuids else ""

        image_urls: Set[str] = set()
        video_urls: Set[str] = set()
        message_count = 0

        async def _run():
            nonlocal message_count
            async with websockets.connect(
                self._ws_url(),
                additional_headers={
                    "Cookie": self._cookie_header(),
                    "User-Agent": self.user_agent,
                    "Origin": "https://www.meta.ai",
                },
            ) as ws:
                try:
                    await asyncio.wait_for(ws.recv(), timeout=2.0)
                except Exception:
                    pass

                if conv_id:
                    await ws.send(build_estab_stream_frame(conv_id))
                    try:
                        await asyncio.wait_for(ws.recv(), timeout=3.0)
                    except Exception:
                        pass

                await ws.send(raw)

                start = time.time()
                while time.time() - start < timeout:
                    try:
                        msg = await asyncio.wait_for(ws.recv(), timeout=15.0)
                        message_count += 1
                        frame = parse_frame(msg)

                        msg_text = msg.decode("utf-8", errors="ignore")
                        for u in re.findall(r'https?://[^\s"\'\\<>]+', msg_text):
                            if any(d in u for d in ("fbcdn", "scontent", "metaaiusercontent")):
                                if "video" in u or ".mp4" in u:
                                    video_urls.add(u)
                                else:
                                    image_urls.add(u)

                        if frame.is_end_of_data:
                            break
                    except asyncio.TimeoutError:
                        if message_count > 5:
                            break
                    except Exception:
                        break

        asyncio.run(_run())

        return {
            "image_urls": sorted(image_urls),
            "video_urls": sorted(video_urls),
            "conversation_id": conv_id,
            "req_id": req_id,
            "message_count": message_count,
        }
