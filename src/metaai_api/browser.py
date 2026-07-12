"""Browser automation backend for Meta AI.

Uses the `agent-browser` CLI to drive a headless Chrome browser.
This is the primary method for generating images and chatting — the browser
creates valid DGW messages natively, so it works for ANY prompt.
"""
from __future__ import annotations

import json
import logging
import re
import shutil
import subprocess
import time
from typing import Any, Dict, List, Optional, Set, Tuple

from .exceptions import BrowserNotInstalledError, ConnectionError
from .utils import DEFAULT_UA, MEDIA_DOMAINS, STATIC_PATTERNS, is_media_url, logger


class BrowserBackend:
    """Browser automation backend using agent-browser."""

    def __init__(self, cookies: dict, headed: bool = False,
                 session_name: str = "metaai", user_agent: str = DEFAULT_UA):
        self.cookies = cookies
        self.headed = headed
        self.session_name = session_name
        self.user_agent = user_agent
        self._ab = self._find_ab()
        self._ready = False

    def _find_ab(self) -> str:
        ab = shutil.which("agent-browser")
        if not ab:
            raise BrowserNotInstalledError(
                "agent-browser is not installed. Install it with:\n"
                "  npm install -g agent-browser\n"
                "  agent-browser install\n"
                "Or: pip install metaai-sdk[browser]"
            )
        return ab

    def _run(self, *args: str, json_output: bool = False, timeout: int = 30) -> Any:
        cmd = [self._ab, "--session", self.session_name] + list(args)
        if json_output:
            cmd.append("--json")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if result.returncode != 0:
            raise ConnectionError(f"agent-browser failed: {result.stderr[:300]}")
        if json_output:
            try:
                return json.loads(result.stdout)
            except json.JSONDecodeError:
                return {"raw": result.stdout}
        return result.stdout.strip()

    def setup(self) -> None:
        """Start browser and inject cookies."""
        try:
            self._run("close")
        except Exception:
            pass
        time.sleep(1)

        flags = ["--headed"] if self.headed else []
        self._run("open", "https://www.meta.ai/", *flags, timeout=60)
        time.sleep(5)

        for name, value in self.cookies.items():
            self._run("cookies", "set", name, value)

        self._run("reload")
        time.sleep(5)
        self._ready = True
        logger.info("Browser backend ready")

    def send_message(self, prompt: str, timeout: int = 120,
                     thinking_mode: bool = False) -> Dict[str, Any]:
        """Send a prompt and return media URLs + text response."""
        if not self._ready:
            self.setup()

        if thinking_mode:
            self._switch_mode("Thinking")
        else:
            self._switch_mode("Instant")

        snapshot = self._run("snapshot", "-i", json_output=True, timeout=15)
        input_ref = self._find_input(snapshot)
        if input_ref:
            self._run("click", input_ref)
        else:
            try:
                self._run("find", "role", "textbox", "click", timeout=10)
            except Exception:
                pass

        self._run("fill", "@last", prompt, timeout=10)
        time.sleep(0.5)
        self._run("press", "Enter")

        urls, text = self._wait_for_response(timeout)
        conv_id = self._get_conversation_id()

        return {"urls": urls, "text": text, "conversation_id": conv_id}

    def _switch_mode(self, mode_name: str) -> None:
        """Switch between Instant and Thinking modes."""
        try:
            self._run("eval",
                "Array.from(document.querySelectorAll('button')).find(b => b.textContent?.trim() === 'Instant' || b.textContent?.trim() === 'Thinking')?.click()",
                json_output=True, timeout=10)
            time.sleep(1)
            self._run("eval",
                f"Array.from(document.querySelectorAll('[role=menuitemcheckbox]')).find(e => e.textContent?.includes('{mode_name}'))?.click()",
                json_output=True, timeout=10)
            time.sleep(1)
        except Exception:
            pass

    def _wait_for_response(self, timeout: int) -> Tuple[List[str], str]:
        """Wait for either media URLs or text response. Returns (urls, text)."""
        urls: Set[str] = set()
        last_text = ""
        text_stable_count = 0
        start = time.time()

        while time.time() - start < timeout:
            time.sleep(2)

            # Check for media URLs
            try:
                js = (
                    "Array.from(document.querySelectorAll('img[src],video[src],source[src],a[href]'))"
                    ".map(e=>e.src||e.href)"
                    ".filter(s=>s&&s.includes('fbcdn'))"
                )
                result = self._run("eval", js, json_output=True, timeout=10)
                data = result.get("data", {}).get("result", []) if isinstance(result, dict) else []
                if isinstance(data, list):
                    for u in data:
                        if isinstance(u, str) and is_media_url(u):
                            urls.add(u)
            except Exception:
                pass

            if urls:
                time.sleep(3)
                return sorted(urls), self._extract_text()

            # Check for text response
            try:
                text_result = self._run("eval",
                    "(() => {"
                    "  const msgs = document.querySelectorAll('[class*=\"assistant-message\"]');"
                    "  if (msgs.length === 0) return '';"
                    "  return msgs[msgs.length - 1].textContent?.trim() || '';"
                    "})()",
                    json_output=True, timeout=10)
                if isinstance(text_result, dict):
                    text = text_result.get("data", {}).get("result", "")
                    if isinstance(text, str) and text:
                        if text == last_text:
                            text_stable_count += 1
                            if text_stable_count >= 2:
                                return [], text
                        else:
                            text_stable_count = 0
                            last_text = text
            except Exception:
                pass

        return sorted(urls), last_text

    def _extract_text(self) -> str:
        try:
            result = self._run("eval",
                "(() => {"
                "  const msgs = document.querySelectorAll('[class*=\"assistant-message\"]');"
                "  return msgs[msgs.length - 1]?.textContent?.trim() || '';"
                "})()",
                json_output=True, timeout=10)
            if isinstance(result, dict):
                text = result.get("data", {}).get("result", "")
                if isinstance(text, str):
                    return text.strip()
        except Exception:
            pass
        return ""

    def _get_conversation_id(self) -> str:
        try:
            current_url = self._run("get", "url", timeout=10)
            m = re.search(r'/prompt/([0-9a-f-]+)', current_url)
            if m:
                return m.group(1)
        except Exception:
            pass
        return ""

    def _find_input(self, snapshot: Any) -> Optional[str]:
        if not isinstance(snapshot, dict):
            return None

        def search(node: Any) -> Optional[str]:
            if isinstance(node, dict):
                if node.get("role") in ("textbox", "searchbox", "combobox") or node.get("editable"):
                    ref = node.get("ref")
                    if ref:
                        return f"@{ref}"
                for child in node.get("children", []):
                    r = search(child)
                    if r:
                        return r
            elif isinstance(node, list):
                for item in node:
                    r = search(item)
                    if r:
                        return r
            return None
        return search(snapshot)

    def list_conversations(self) -> List[dict]:
        """Get all conversations from the sidebar."""
        try:
            result = self._run("eval",
                "(() => {"
                "  const links = Array.from(document.querySelectorAll('a[href*=\"/prompt/\"]'));"
                "  return links.map(a => ({"
                "    title: a.textContent?.trim(),"
                "    url: a.href"
                "  })).filter(c => c.title);"
                "})()",
                json_output=True, timeout=15)
            convs = []
            if isinstance(result, dict):
                data = result.get("data", {}).get("result", [])
                if isinstance(data, list):
                    for c in data:
                        if isinstance(c, dict):
                            convs.append({
                                "id": c.get("url", "").split("/prompt/")[-1] if "/prompt/" in c.get("url", "") else "",
                                "title": c.get("title", ""),
                                "url": c.get("url", ""),
                            })
            return convs
        except Exception:
            return []

    def use_as_reference(self, image_url: str, prompt: str, timeout: int = 120) -> Dict[str, Any]:
        """Use an existing image as a reference for a new generation."""
        try:
            self._run("eval",
                "Array.from(document.querySelectorAll('button')).find(b => b.getAttribute('aria-label') === 'Use as reference')?.click()",
                json_output=True, timeout=10)
            time.sleep(2)
            self._run("find", "role", "textbox", "click", timeout=10)
            self._run("fill", "@last", prompt, timeout=10)
            time.sleep(0.5)
            self._run("press", "Enter")
            urls, text = self._wait_for_response(timeout)
            return {"urls": urls, "text": text, "conversation_id": self._get_conversation_id()}
        except Exception as e:
            return {"urls": [], "text": "", "conversation_id": "", "error": str(e)}

    def close(self) -> None:
        try:
            self._run("close")
        except Exception:
            pass
        self._ready = False

    def new_chat(self) -> None:
        """Start a new chat conversation."""
        try:
            self._run("find", "role", "link", "click", "--name", "New chat", timeout=10)
            time.sleep(2)
        except Exception:
            pass
