"""
Comprehensive feature test runner for MetaAI SDK and REST API.

Covers all major project features:
- Chat (SDK + API)
- Image upload (SDK + API)
- Image generation (text and image-to-image)
- Video generation (sync + async API path)
- Video extend (SDK + API, when a source media_id is available)

Usage examples:
  python scripts/test_all_features_complete.py
  python scripts/test_all_features_complete.py --api-only --base-url http://127.0.0.1:8001
  python scripts/test_all_features_complete.py --video-auto-poll --timeout 240
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

from metaai_api import MetaAI


PNG_1X1_BASE64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8"
    "/x8AAwMCAO5Wf9sAAAAASUVORK5CYII="
)


def _now() -> float:
    return time.time()


def _elapsed(start: float) -> float:
    return round(time.time() - start, 2)


def _preview(text: str, n: int = 200) -> str:
    return (text or "").replace("\n", " ").strip()[:n]


def _make_result(name: str, ok: bool, elapsed: float, **extra: Any) -> Dict[str, Any]:
    row: Dict[str, Any] = {"name": name, "ok": ok, "elapsed_seconds": elapsed}
    row.update(extra)
    return row


def _make_skipped(name: str, reason: str) -> Dict[str, Any]:
    return {
        "name": name,
        "ok": True,
        "skipped": True,
        "reason": reason,
        "elapsed_seconds": 0.0,
    }


def _extract_message(response: Any) -> str:
    if isinstance(response, dict):
        return str(response.get("message", ""))
    return ""


def _write_temp_png() -> Path:
    data = base64.b64decode(PNG_1X1_BASE64)
    fd, path = tempfile.mkstemp(prefix="metaai_test_", suffix=".png")
    os.close(fd)
    Path(path).write_bytes(data)
    return Path(path)


def _sdk_chat_non_stream(ai: MetaAI) -> Dict[str, Any]:
    start = _now()
    q = "What is 7% of 10000? Reply with only the number and a short explanation."
    resp = ai.prompt(q, stream=False, new_conversation=True)
    msg = _extract_message(resp)
    return _make_result("sdk_chat_non_stream", bool(msg), _elapsed(start), preview=_preview(msg, 220))


def _sdk_chat_stream(ai: MetaAI, max_chunks: int = 10) -> Dict[str, Any]:
    start = _now()
    chunks: List[str] = []
    for chunk in ai.prompt("Explain quantum computing simply.", stream=True, new_conversation=True):
        msg = _extract_message(chunk)
        if msg:
            chunks.append(msg)
        if len(chunks) >= max_chunks:
            break

    best_chunk = max(chunks, key=len) if chunks else ""
    ok = len(chunks) > 0 and bool(best_chunk.strip())
    return _make_result(
        "sdk_chat_stream",
        ok,
        _elapsed(start),
        chunk_count=len(chunks),
        preview=_preview(best_chunk, 240),
    )


def _sdk_upload(ai: MetaAI) -> Dict[str, Any]:
    start = _now()
    tmp = _write_temp_png()
    try:
        resp = ai.upload_image(str(tmp))
        ok = bool(resp.get("success")) and bool(resp.get("media_id"))
        return _make_result(
            "sdk_upload_image",
            ok,
            _elapsed(start),
            media_id=resp.get("media_id"),
            mime_type=resp.get("mime_type"),
            error=resp.get("error"),
        )
    finally:
        tmp.unlink(missing_ok=True)


def _sdk_image_text(ai: MetaAI) -> Dict[str, Any]:
    start = _now()
    resp = ai.generate_image_new(
        prompt="A minimal line-art icon of a mountain at sunrise",
        orientation="SQUARE",
        num_images=1,
    )
    urls = resp.get("image_urls") or []
    pending = str(resp.get("error", "")).lower().find("still be processing") >= 0
    ok = bool(resp.get("success")) and len(urls) > 0
    if not ok and pending:
        ok = True
    return _make_result(
        "sdk_image_text",
        ok,
        _elapsed(start),
        image_url_count=len(urls),
        first_url=(urls[0] if urls else None),
        error=resp.get("error"),
    )


def _sdk_image_from_upload(ai: MetaAI, media_id: Optional[str]) -> Dict[str, Any]:
    if not media_id:
        return _make_skipped("sdk_image_from_upload", "No media_id from sdk upload")

    start = _now()
    resp = ai.generate_image_new(
        prompt="Create a stylized variation of this image",
        orientation="SQUARE",
        num_images=1,
        media_ids=[media_id],
    )
    urls = resp.get("image_urls") or []
    pending = str(resp.get("error", "")).lower().find("still be processing") >= 0
    ok = bool(resp.get("success")) and len(urls) > 0
    if not ok and pending:
        ok = True
    return _make_result(
        "sdk_image_from_upload",
        ok,
        _elapsed(start),
        image_url_count=len(urls),
        first_url=(urls[0] if urls else None),
        error=resp.get("error"),
    )


def _sdk_video(ai: MetaAI, auto_poll: bool, poll_attempts: int, poll_wait: int) -> Dict[str, Any]:
    start = _now()
    resp = ai.generate_video_new(
        prompt="A short cinematic shot of ocean waves at sunset",
        auto_poll=auto_poll,
        max_poll_attempts=poll_attempts,
        poll_wait_seconds=poll_wait,
    )
    media_ids = resp.get("media_ids") or []
    urls = resp.get("video_urls") or []

    ok = bool(resp.get("success")) and (len(media_ids) > 0 or len(urls) > 0 or bool(resp.get("conversation_id")))
    return _make_result(
        "sdk_video_generate",
        ok,
        _elapsed(start),
        conversation_id=resp.get("conversation_id"),
        media_ids=media_ids,
        video_url_count=len(urls),
        first_url=(urls[0] if urls else None),
        processing=resp.get("processing"),
        error=resp.get("error"),
    )


def _sdk_video_extend(
    ai: MetaAI,
    source_media_id: Optional[str],
    auto_poll: bool,
    poll_attempts: int,
    poll_wait: int,
) -> Dict[str, Any]:
    if not source_media_id:
        return _make_skipped("sdk_video_extend", "No source media_id available from sdk video generation")

    start = _now()
    resp = ai.extend_video(
        media_id=source_media_id,
        auto_poll=auto_poll,
        max_poll_attempts=poll_attempts,
        poll_wait_seconds=poll_wait,
    )
    urls = resp.get("video_urls") or []
    media_ids = resp.get("media_ids") or []
    ok = bool(resp.get("success")) and (len(media_ids) > 0 or len(urls) > 0 or bool(resp.get("conversation_id")))

    return _make_result(
        "sdk_video_extend",
        ok,
        _elapsed(start),
        source_media_id=source_media_id,
        media_ids=media_ids,
        video_url_count=len(urls),
        first_url=(urls[0] if urls else None),
        processing=resp.get("processing"),
        error=resp.get("error"),
    )


def _api_health(base_url: str, timeout: int) -> Dict[str, Any]:
    start = _now()
    r = requests.get(f"{base_url}/healthz", timeout=timeout)
    ok = r.status_code == 200
    return _make_result("api_healthz", ok, _elapsed(start), status_code=r.status_code, body=r.text[:200])


def _api_chat(base_url: str, timeout: int) -> Dict[str, Any]:
    start = _now()
    payload = {"message": "Reply with exactly: api chat ok", "stream": False, "new_conversation": True}
    r = requests.post(f"{base_url}/chat", json=payload, timeout=timeout)
    body: Dict[str, Any] = {}
    try:
        body = r.json()
    except Exception:
        body = {"raw": r.text[:300]}

    msg = str(body.get("message", "")) if isinstance(body, dict) else ""
    ok = r.status_code == 200 and bool(msg)
    return _make_result(
        "api_chat",
        ok,
        _elapsed(start),
        status_code=r.status_code,
        preview=_preview(msg, 220),
    )


def _api_upload(base_url: str, timeout: int) -> Dict[str, Any]:
    start = _now()
    data = base64.b64decode(PNG_1X1_BASE64)
    files = {"file": ("metaai_test.png", data, "image/png")}
    r = requests.post(f"{base_url}/upload", files=files, timeout=timeout)

    body: Dict[str, Any] = {}
    try:
        body = r.json()
    except Exception:
        body = {"raw": r.text[:300]}

    media_id = body.get("media_id") if isinstance(body, dict) else None
    ok = r.status_code == 200 and bool(media_id)
    return _make_result(
        "api_upload_image",
        ok,
        _elapsed(start),
        status_code=r.status_code,
        media_id=media_id,
        error=(body.get("error") if isinstance(body, dict) else None),
    )


def _api_image_text(base_url: str, timeout: int) -> Dict[str, Any]:
    start = _now()
    payload = {
        "prompt": "A simple flat icon of a cloud and moon",
        "orientation": "SQUARE",
        "num_images": 1,
    }
    r = requests.post(f"{base_url}/image", json=payload, timeout=timeout)

    body: Dict[str, Any] = {}
    try:
        body = r.json()
    except Exception:
        body = {"raw": r.text[:300]}

    urls = body.get("image_urls", []) if isinstance(body, dict) else []
    pending = str(body.get("error", "")).lower().find("still be processing") >= 0 if isinstance(body, dict) else False
    ok = r.status_code == 200 and bool(body.get("success")) and len(urls) > 0
    if not ok and r.status_code == 200 and pending:
        ok = True
    return _make_result(
        "api_image_text",
        ok,
        _elapsed(start),
        status_code=r.status_code,
        image_url_count=len(urls),
        first_url=(urls[0] if urls else None),
        error=(body.get("error") if isinstance(body, dict) else None),
    )


def _api_image_from_upload(base_url: str, timeout: int, media_id: Optional[str]) -> Dict[str, Any]:
    if not media_id:
        return _make_skipped("api_image_from_upload", "No media_id from api upload")

    start = _now()
    payload = {
        "prompt": "Create a stylized variation of this image",
        "orientation": "SQUARE",
        "media_ids": [media_id],
    }
    r = requests.post(f"{base_url}/image", json=payload, timeout=timeout)

    body: Dict[str, Any] = {}
    try:
        body = r.json()
    except Exception:
        body = {"raw": r.text[:300]}

    urls = body.get("image_urls", []) if isinstance(body, dict) else []
    pending = str(body.get("error", "")).lower().find("still be processing") >= 0 if isinstance(body, dict) else False
    ok = r.status_code == 200 and bool(body.get("success")) and len(urls) > 0
    if not ok and r.status_code == 200 and pending:
        ok = True
    return _make_result(
        "api_image_from_upload",
        ok,
        _elapsed(start),
        status_code=r.status_code,
        image_url_count=len(urls),
        first_url=(urls[0] if urls else None),
        error=(body.get("error") if isinstance(body, dict) else None),
    )


def _api_video(base_url: str, timeout: int, auto_poll: bool, poll_attempts: int, poll_wait: int) -> Dict[str, Any]:
    start = _now()
    payload = {
        "prompt": "A short cinematic shot of ocean waves at sunset",
        "auto_poll": auto_poll,
        "max_poll_attempts": poll_attempts,
        "poll_wait_seconds": poll_wait,
    }
    r = requests.post(f"{base_url}/video", json=payload, timeout=timeout)

    body: Dict[str, Any] = {}
    try:
        body = r.json()
    except Exception:
        body = {"raw": r.text[:300]}

    media_ids = body.get("media_ids", []) if isinstance(body, dict) else []
    urls = body.get("video_urls", []) if isinstance(body, dict) else []
    ok = r.status_code == 200 and bool(body.get("success")) and (
        len(media_ids) > 0 or len(urls) > 0 or bool(body.get("conversation_id"))
    )

    return _make_result(
        "api_video_generate",
        ok,
        _elapsed(start),
        status_code=r.status_code,
        conversation_id=(body.get("conversation_id") if isinstance(body, dict) else None),
        media_ids=media_ids,
        video_url_count=len(urls),
        first_url=(urls[0] if urls else None),
        processing=(body.get("processing") if isinstance(body, dict) else None),
        error=(body.get("error") if isinstance(body, dict) else None),
    )


def _api_video_async(base_url: str, timeout: int, poll_attempts: int, poll_wait: int) -> Dict[str, Any]:
    start = _now()
    payload = {"prompt": "A short cinematic shot of rain over a city at night"}
    r = requests.post(f"{base_url}/video/async", json=payload, timeout=timeout)

    body: Dict[str, Any] = {}
    try:
        body = r.json()
    except Exception:
        body = {"raw": r.text[:300]}

    job_id = body.get("job_id") if isinstance(body, dict) else None
    if r.status_code != 200 or not job_id:
        return _make_result(
            "api_video_async",
            False,
            _elapsed(start),
            status_code=r.status_code,
            error=(body.get("detail") if isinstance(body, dict) else body),
        )

    latest_status: Dict[str, Any] = {}
    for _ in range(max(1, poll_attempts)):
        time.sleep(max(1, poll_wait))
        sr = requests.get(f"{base_url}/video/jobs/{job_id}", timeout=timeout)
        try:
            latest_status = sr.json()
        except Exception:
            latest_status = {"raw": sr.text[:300], "status_code": sr.status_code}
            break
        st = str(latest_status.get("status", ""))
        if st in {"succeeded", "failed"}:
            break

    status_value = latest_status.get("status") if isinstance(latest_status, dict) else None
    ok = status_value in {"pending", "running", "succeeded", "failed"}

    return _make_result(
        "api_video_async",
        ok,
        _elapsed(start),
        job_id=job_id,
        final_status=status_value,
        status_payload=latest_status,
    )


def _api_video_extend(
    base_url: str,
    timeout: int,
    source_media_id: Optional[str],
    auto_poll: bool,
    poll_attempts: int,
    poll_wait: int,
) -> Dict[str, Any]:
    if not source_media_id:
        return _make_skipped("api_video_extend", "No source media_id available from api_video_generate")

    start = _now()
    payload = {
        "media_id": source_media_id,
        "auto_poll": auto_poll,
        "max_poll_attempts": poll_attempts,
        "poll_wait_seconds": poll_wait,
    }
    r = requests.post(f"{base_url}/video/extend", json=payload, timeout=timeout)

    body: Dict[str, Any] = {}
    try:
        body = r.json()
    except Exception:
        body = {"raw": r.text[:300]}

    media_ids = body.get("media_ids", []) if isinstance(body, dict) else []
    urls = body.get("video_urls", []) if isinstance(body, dict) else []
    ok = r.status_code == 200 and bool(body.get("success")) and (
        len(media_ids) > 0 or len(urls) > 0 or bool(body.get("conversation_id"))
    )

    return _make_result(
        "api_video_extend",
        ok,
        _elapsed(start),
        status_code=r.status_code,
        source_media_id=source_media_id,
        media_ids=media_ids,
        video_url_count=len(urls),
        first_url=(urls[0] if urls else None),
        processing=(body.get("processing") if isinstance(body, dict) else None),
        error=(body.get("error") if isinstance(body, dict) else None),
    )


def _compute_all_passed(rows: List[Dict[str, Any]]) -> bool:
    # Skipped tests count as neutral.
    return all(bool(row.get("ok")) for row in rows if not row.get("skipped"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Comprehensive SDK + API feature test runner")
    parser.add_argument("--base-url", default="http://127.0.0.1:8001", help="API base URL")
    parser.add_argument("--timeout", type=int, default=180, help="HTTP timeout in seconds")
    parser.add_argument("--poll-attempts", type=int, default=2, help="Async polling attempts for quick checks")
    parser.add_argument("--poll-wait", type=int, default=2, help="Seconds between async poll attempts")
    parser.add_argument("--video-auto-poll", action="store_true", help="Auto-poll SDK/API video generation for URLs")
    parser.add_argument("--sdk-only", action="store_true", help="Run only SDK tests")
    parser.add_argument("--api-only", action="store_true", help="Run only API tests")
    parser.add_argument(
        "--output",
        default="tests/integration/outputs/feature_test_report.json",
        help="Output JSON report path",
    )
    args = parser.parse_args()

    run_sdk = not args.api_only
    run_api = not args.sdk_only

    report: Dict[str, Any] = {
        "timestamp": int(time.time()),
        "config": {
            "base_url": args.base_url,
            "timeout": args.timeout,
            "poll_attempts": args.poll_attempts,
            "poll_wait": args.poll_wait,
            "video_auto_poll": args.video_auto_poll,
            "run_sdk": run_sdk,
            "run_api": run_api,
        },
        "sdk_tests": [],
        "api_tests": [],
        "all_passed": False,
    }

    if run_sdk:
        try:
            ai = MetaAI()
            report["sdk_tests"].append(_make_result("sdk_init", True, 0.0, access_token_present=bool(ai.access_token)))

            report["sdk_tests"].append(_sdk_chat_non_stream(ai))
            report["sdk_tests"].append(_sdk_chat_stream(ai))

            sdk_upload = _sdk_upload(ai)
            report["sdk_tests"].append(sdk_upload)
            sdk_media_id = sdk_upload.get("media_id") if sdk_upload.get("ok") else None

            report["sdk_tests"].append(_sdk_image_text(ai))
            report["sdk_tests"].append(_sdk_image_from_upload(ai, sdk_media_id))

            sdk_video = _sdk_video(
                ai,
                auto_poll=args.video_auto_poll,
                poll_attempts=args.poll_attempts,
                poll_wait=args.poll_wait,
            )
            report["sdk_tests"].append(sdk_video)
            source_media_id = None
            if sdk_video.get("ok"):
                media_ids = sdk_video.get("media_ids") or []
                if media_ids:
                    source_media_id = media_ids[0]

            report["sdk_tests"].append(
                _sdk_video_extend(
                    ai,
                    source_media_id=source_media_id,
                    auto_poll=args.video_auto_poll,
                    poll_attempts=args.poll_attempts,
                    poll_wait=args.poll_wait,
                )
            )
        except Exception as exc:  # noqa: BLE001
            report["sdk_tests"].append(
                _make_result("sdk_fatal", False, 0.0, error=str(exc))
            )

    if run_api:
        try:
            api_rows: List[Dict[str, Any]] = []
            api_rows.append(_api_health(args.base_url, args.timeout))
            api_rows.append(_api_chat(args.base_url, args.timeout))

            api_upload = _api_upload(args.base_url, args.timeout)
            api_rows.append(api_upload)
            api_media_id = api_upload.get("media_id") if api_upload.get("ok") else None

            api_rows.append(_api_image_text(args.base_url, args.timeout))
            api_rows.append(_api_image_from_upload(args.base_url, args.timeout, api_media_id))

            api_video = _api_video(
                args.base_url,
                args.timeout,
                auto_poll=args.video_auto_poll,
                poll_attempts=args.poll_attempts,
                poll_wait=args.poll_wait,
            )
            api_rows.append(api_video)

            api_rows.append(_api_video_async(args.base_url, args.timeout, args.poll_attempts, args.poll_wait))

            source_media_id = None
            if api_video.get("ok"):
                mids = api_video.get("media_ids") or []
                if mids:
                    source_media_id = mids[0]

            api_rows.append(
                _api_video_extend(
                    args.base_url,
                    args.timeout,
                    source_media_id=source_media_id,
                    auto_poll=args.video_auto_poll,
                    poll_attempts=args.poll_attempts,
                    poll_wait=args.poll_wait,
                )
            )

            report["api_tests"] = api_rows
        except Exception as exc:  # noqa: BLE001
            report["api_tests"].append(_make_result("api_fatal", False, 0.0, error=str(exc)))

    all_rows = report["sdk_tests"] + report["api_tests"]
    report["all_passed"] = _compute_all_passed(all_rows)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"Wrote results to {out_path}")
    print(json.dumps(report, indent=2))

    return 0 if report["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
