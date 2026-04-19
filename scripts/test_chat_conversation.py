"""
Conversation-style chat test runner.

This script lets you send messages in a conversation and validate responses using:
- SDK mode: MetaAI.prompt(...)
- API mode: POST /chat

Conversation behavior is controlled via --conversation-type:
- continuous: keeps one conversation across turns (unless /new is used)
- new_each_message: starts a fresh conversation on every turn

Usage examples:
  python scripts/test_chat_conversation.py --mode sdk
  python scripts/test_chat_conversation.py --mode api --base-url http://127.0.0.1:8001
  python scripts/test_chat_conversation.py --mode sdk --message "Hello" --message "What did I just say?"
"""

from __future__ import annotations

import argparse
import logging
import json
import re
import time
from typing import Any, Dict, List, Optional

import requests

from metaai_api import MetaAI


TEXT_ONLY_GUARD = (
    "Reply in plain conversational text only. "
    "Do not offer to create, animate, generate, or edit images/videos unless explicitly asked."
)


def _build_effective_message(user_message: str, *, use_text_only_guard: bool) -> str:
    if not use_text_only_guard:
        return user_message
    return f"{user_message}\n\n[Instruction: {TEXT_ONLY_GUARD}]"


def _looks_like_capability_drift(reply: str) -> bool:
    lowered = (reply or "").lower()
    drift_markers = (
        "what can i create",
        "what would you like to create",
        "what can i help you create",
        "what would you like me to create",
        "want me to animate",
        "want me to make",
        "want me to turn",
        "create something",
        "generate images",
        "generate a video",
        "animate the numbers",
        "animate this",
        "animate it",
        "make images",
        "make videos",
    )
    return any(marker in lowered for marker in drift_markers)


def _strip_capability_drift_text(reply: str) -> tuple[str, bool]:
    """Remove create/media suggestion lines for cleaner text-only chat previews."""
    text = (reply or "").strip()
    if not text:
        return text, False

    removed = False
    lines = [line.strip() for line in re.split(r"[\r\n]+", text) if line.strip()]
    kept_lines: List[str] = []

    for line in lines:
        if _looks_like_capability_drift(line):
            removed = True
            continue
        kept_lines.append(line)

    cleaned = "\n\n".join(kept_lines).strip()

    if cleaned:
        return cleaned, removed

    # Fallback to sentence-level filtering when drift and normal content are in one line.
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
    kept_sentences: List[str] = []
    for sentence in sentences:
        if _looks_like_capability_drift(sentence):
            removed = True
            continue
        kept_sentences.append(sentence)

    fallback_cleaned = " ".join(kept_sentences).strip()
    if fallback_cleaned:
        return fallback_cleaned, removed

    return text, removed


def _preview(text: str, length: int = 220) -> str:
    return (text or "").replace("\n", " ").strip()[:length]


def _send_sdk(
    ai: MetaAI,
    message: str,
    *,
    new_conversation: bool,
    stream: bool,
    max_stream_chunks: int,
) -> Dict[str, Any]:
    start = time.time()

    if stream:
        chunks: List[str] = []
        for chunk in ai.prompt(message, stream=True, new_conversation=new_conversation):
            chunk_text = ""
            if isinstance(chunk, dict):
                chunk_text = str(chunk.get("message", ""))
            if chunk_text:
                chunks.append(chunk_text)
            if len(chunks) >= max_stream_chunks:
                break

        full_text = "".join(chunks).strip()
        return {
            "ok": bool(full_text),
            "elapsed_seconds": round(time.time() - start, 2),
            "reply": full_text,
            "preview": _preview(full_text),
            "chunk_count": len(chunks),
            "stream": True,
        }

    resp = ai.prompt(message, stream=False, new_conversation=new_conversation)
    reply = str(resp.get("message", "")) if isinstance(resp, dict) else ""
    return {
        "ok": bool(reply.strip()),
        "elapsed_seconds": round(time.time() - start, 2),
        "reply": reply,
        "preview": _preview(reply),
        "stream": False,
    }


def _send_api(
    base_url: str,
    timeout: int,
    message: str,
    *,
    new_conversation: bool,
) -> Dict[str, Any]:
    start = time.time()
    payload = {
        "message": message,
        "stream": False,
        "new_conversation": new_conversation,
    }

    response = requests.post(f"{base_url}/chat", json=payload, timeout=timeout)

    body: Dict[str, Any] = {}
    try:
        body = response.json()
    except Exception:
        body = {"raw": response.text[:300]}

    reply = str(body.get("message", "")) if isinstance(body, dict) else ""

    return {
        "ok": response.status_code == 200 and bool(reply.strip()),
        "elapsed_seconds": round(time.time() - start, 2),
        "status_code": response.status_code,
        "reply": reply,
        "preview": _preview(reply),
        "error": body.get("detail") if isinstance(body, dict) else None,
    }


def _run_turn(
    *,
    mode: str,
    ai: Optional[MetaAI],
    base_url: str,
    timeout: int,
    message: str,
    new_conversation: bool,
    stream: bool,
    max_stream_chunks: int,
) -> Dict[str, Any]:
    if mode == "sdk":
        if ai is None:
            raise RuntimeError("SDK mode requires MetaAI instance")
        return _send_sdk(
            ai,
            message,
            new_conversation=new_conversation,
            stream=stream,
            max_stream_chunks=max_stream_chunks,
        )

    return _send_api(
        base_url,
        timeout,
        message,
        new_conversation=new_conversation,
    )


def _compute_new_conversation_flag(
    *,
    conversation_type: str,
    turn_index: int,
    force_new: bool,
) -> bool:
    if force_new:
        return True
    if conversation_type == "new_each_message":
        return True
    return turn_index == 0


def _save_results(path: str, data: Dict[str, Any]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def main() -> int:
    parser = argparse.ArgumentParser(description="Conversation-style chat tester")
    parser.add_argument("--mode", choices=["sdk", "api"], default="sdk", help="Run against SDK or /chat API")
    parser.add_argument("--base-url", default="http://127.0.0.1:8001", help="API base URL for --mode api")
    parser.add_argument("--timeout", type=int, default=180, help="HTTP timeout in seconds")
    parser.add_argument(
        "--conversation-type",
        choices=["continuous", "new_each_message"],
        default="continuous",
        help="Conversation behavior across turns",
    )
    parser.add_argument(
        "--message",
        action="append",
        help="Message to send (repeat for multiple turns). If omitted, interactive mode is used.",
    )
    parser.add_argument("--interactive", action="store_true", help="Force interactive mode")
    parser.add_argument("--stream", action="store_true", help="Use streaming in SDK mode")
    parser.add_argument("--max-stream-chunks", type=int, default=40, help="Max streamed chunks per turn")
    parser.add_argument(
        "--verbose-internal-logs",
        action="store_true",
        help="Show internal SDK warning logs (doc_id fallback, transport warnings)",
    )
    parser.add_argument(
        "--disable-text-only-guard",
        action="store_true",
        help="Disable text-only guard instruction (allows create/image/video suggestions)",
    )
    parser.add_argument(
        "--strict-text-only",
        dest="strict_text_only",
        action="store_true",
        default=None,
        help="Mark a turn as failed if a reply includes create/image/video suggestion drift",
    )
    parser.add_argument(
        "--non-strict-text-only",
        dest="strict_text_only",
        action="store_false",
        help="Allow capability drift warnings without failing turns",
    )
    parser.add_argument("--output", default="chat_conversation_test_results.json", help="Output JSON path")
    args = parser.parse_args()

    if not args.verbose_internal_logs:
        logging.getLogger().setLevel(logging.ERROR)

    if args.mode == "api" and args.stream:
        print("[warn] API mode does not support stream=true for /chat; streaming will be ignored.")

    ai: Optional[MetaAI] = None
    if args.mode == "sdk":
        ai = MetaAI()

    scripted_messages = args.message or []
    interactive_mode = args.interactive or not scripted_messages

    if args.strict_text_only is None:
        # Prefer warnings-only in interactive chat, strict validation in scripted runs.
        args.strict_text_only = not interactive_mode

    results: Dict[str, Any] = {
        "mode": args.mode,
        "conversation_type": args.conversation_type,
        "base_url": args.base_url if args.mode == "api" else None,
        "text_only_guard_enabled": not args.disable_text_only_guard,
        "strict_text_only": bool(args.strict_text_only),
        "turns": [],
        "all_passed": False,
        "total_turns": 0,
    }

    if args.mode == "api":
        try:
            health = requests.get(f"{args.base_url}/healthz", timeout=args.timeout)
            results["api_healthz_status"] = health.status_code
        except Exception as exc:  # noqa: BLE001
            results["fatal_error"] = f"Failed to reach API health endpoint: {exc}"
            _save_results(args.output, results)
            print(f"Wrote results to {args.output}")
            print(json.dumps(results, indent=2))
            return 1

    turn_index = 0
    force_new_next = False

    def run_and_store(user_message: str, *, bypass_text_only_guard: bool = False) -> Dict[str, Any]:
        nonlocal turn_index, force_new_next

        guard_enabled = (not args.disable_text_only_guard) and (not bypass_text_only_guard)
        effective_message = _build_effective_message(
            user_message,
            use_text_only_guard=guard_enabled,
        )

        new_flag = _compute_new_conversation_flag(
            conversation_type=args.conversation_type,
            turn_index=turn_index,
            force_new=force_new_next,
        )

        turn_result = _run_turn(
            mode=args.mode,
            ai=ai,
            base_url=args.base_url,
            timeout=args.timeout,
            message=effective_message,
            new_conversation=new_flag,
            stream=bool(args.stream and args.mode == "sdk"),
            max_stream_chunks=args.max_stream_chunks,
        )

        raw_reply = str(turn_result.get("reply", ""))
        drift_detected = guard_enabled and _looks_like_capability_drift(raw_reply)
        cleaned_reply, drift_text_removed = _strip_capability_drift_text(raw_reply) if guard_enabled else (raw_reply, False)

        if drift_text_removed and cleaned_reply and cleaned_reply != raw_reply:
            turn_result["reply_raw"] = raw_reply
            turn_result["reply"] = cleaned_reply
            turn_result["preview"] = _preview(cleaned_reply)
            turn_result["capability_drift_text_removed"] = True

        if drift_detected:
            turn_result["capability_drift"] = True
            if args.strict_text_only:
                turn_result["ok"] = False
                turn_result["error"] = "Capability drift detected: reply included create/image/video suggestion"

        row = {
            "turn": turn_index + 1,
            "new_conversation": new_flag,
            "user_message": user_message,
            "text_only_guard_applied": guard_enabled,
            **turn_result,
        }
        if effective_message != user_message:
            row["request_message"] = effective_message
        results["turns"].append(row)

        turn_index += 1
        if args.conversation_type == "new_each_message":
            force_new_next = True
        else:
            force_new_next = False

        return row

    try:
        if interactive_mode:
            print("Conversation chat tester started.")
            print("Commands: /new (start new conversation), /raw <message> (bypass text-only guard for one turn), /quit (exit)")
            print(f"Mode: {args.mode} | Conversation type: {args.conversation_type}")
            if not args.disable_text_only_guard:
                print("[info] Text-only guard is enabled")
            if args.strict_text_only:
                print("[info] Strict text-only mode is enabled")
            else:
                print("[info] Strict text-only mode is disabled (drift warns but does not fail)")
            while True:
                user_message = input("You> ").strip()
                if not user_message:
                    continue
                if user_message.lower() in {"/quit", "quit", "exit"}:
                    break
                if user_message.lower() == "/new":
                    force_new_next = True
                    print("[info] Next message will start a new conversation")
                    continue

                bypass_text_only_guard = False
                if user_message.lower().startswith("/raw "):
                    raw_message = user_message[5:].strip()
                    if not raw_message:
                        print("[warn] /raw requires a message")
                        continue
                    user_message = raw_message
                    bypass_text_only_guard = True

                row = run_and_store(user_message, bypass_text_only_guard=bypass_text_only_guard)
                print(f"Bot> {row.get('preview', '')}")
                if row.get("ok") is not True and row.get("error"):
                    print(f"[error] {row['error']}")
                if row.get("capability_drift"):
                    print("[warn] Capability drift detected in reply (create/image/video suggestion)")
        else:
            for msg in scripted_messages:
                row = run_and_store(msg)
                print(f"turn {row['turn']}: ok={row['ok']} preview={row.get('preview', '')}")
                if row.get("capability_drift"):
                    print(f"turn {row['turn']}: drift detected (reply contains create/image/video suggestion)")

    except KeyboardInterrupt:
        results["interrupted"] = True

    all_ok = all(bool(turn.get("ok")) for turn in results["turns"])
    drift_turns = [int(turn.get("turn")) for turn in results["turns"] if turn.get("capability_drift")]
    results["total_turns"] = len(results["turns"])
    results["all_passed"] = all_ok and len(results["turns"]) > 0
    results["has_capability_drift"] = bool(drift_turns)
    results["capability_drift_turns"] = drift_turns

    _save_results(args.output, results)

    print(f"Wrote results to {args.output}")
    print(json.dumps(results, indent=2))

    return 0 if results["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
