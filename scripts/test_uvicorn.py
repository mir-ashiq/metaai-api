import argparse
import json
import sys
import time
from typing import Any, Dict, Optional

import requests


DEFAULT_BASE_URL = "http://localhost:8000"
DEFAULT_TIMEOUT = 120  # Image/video generation can take 60-90s with polling


def _print_section(title: str) -> None:
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def _post_json(base_url: str, path: str, payload: Dict[str, Any], timeout: int) -> requests.Response:
    url = f"{base_url}{path}"
    return requests.post(url, json=payload, timeout=timeout)


def test_health(base_url: str, timeout: int) -> bool:
    _print_section("Health check")
    try:
        resp = requests.get(f"{base_url}/healthz", timeout=timeout)
        print(f"GET /healthz -> {resp.status_code} {resp.text}")
        return resp.ok
    except Exception as exc:  # noqa: BLE001
        print(f"Health check failed: {exc}")
        return False


def test_chat(base_url: str, timeout: int) -> None:
    _print_section("Chat test")
    payload = {"message": "Hello from test", "stream": False, "new_conversation": True}
    resp = _post_json(base_url, "/chat", payload, timeout)
    print(f"POST /chat -> {resp.status_code}")
    try:
        print(json.dumps(resp.json(), indent=2)[:2000])
    except Exception:
        print(resp.text[:2000])


def test_image(base_url: str, timeout: int) -> None:
    _print_section("Image generation test")
    payload = {
        "prompt": "a serene lake at sunrise",
        "new_conversation": True,
        "orientation": "LANDSCAPE",
    }
    resp = _post_json(base_url, "/image", payload, timeout)
    print(f"POST /image -> {resp.status_code}")
    try:
        print(json.dumps(resp.json(), indent=2)[:2000])
    except Exception:
        print(resp.text[:2000])


def test_video_async(base_url: str, timeout: int, poll_wait: int, poll_attempts: int) -> None:
    _print_section("Video async test")
    payload = {
        "prompt": "a drone flythrough of a futuristic city at night",
        "orientation": "LANDSCAPE",
        "wait_before_poll": 5,
        "max_attempts": 24,
        "wait_seconds": 5,
    }
    try:
        resp = _post_json(base_url, "/video/async", payload, timeout)
    except Exception as exc:  # noqa: BLE001
        print(f"POST /video/async failed: {exc}")
        return

    print(f"POST /video/async -> {resp.status_code}")
    if not resp.ok:
        print(resp.text[:2000])
        return

    data: Optional[Dict[str, Any]] = None
    try:
        data = resp.json()
    except Exception:
        print(resp.text[:2000])
        return

    job_id = data.get("job_id") if isinstance(data, dict) else None
    if not job_id:
        print("No job_id returned; response:", data)
        return

    print(f"Job ID: {job_id}")

    for attempt in range(1, poll_attempts + 1):
        try:
            status_resp = requests.get(f"{base_url}/video/jobs/{job_id}", timeout=timeout)
        except Exception as exc:  # noqa: BLE001
            print(f"Attempt {attempt}/{poll_attempts} status check failed: {exc}")
            time.sleep(poll_wait)
            continue

        print(f"Attempt {attempt}/{poll_attempts}: status {status_resp.status_code}")
        try:
            status_json = status_resp.json()
            print(json.dumps(status_json, indent=2)[:2000])
        except Exception:
            print(status_resp.text[:2000])
            status_json = None

        if isinstance(status_json, dict):
            if status_json.get("status") in {"succeeded", "failed"}:
                break
        time.sleep(poll_wait)


def main() -> None:
    parser = argparse.ArgumentParser(description="Smoke-test uvicorn Meta AI API server")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="Base URL of running uvicorn server")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help="Request timeout in seconds")
    parser.add_argument("--poll-wait", type=int, default=10, help="Seconds between video job polls")
    parser.add_argument("--poll-attempts", type=int, default=12, help="Number of video status polls")
    parser.add_argument("--skip-chat", action="store_true", help="Skip chat endpoint test")
    parser.add_argument("--skip-image", action="store_true", help="Skip image generation test")
    parser.add_argument("--skip-video", action="store_true", help="Skip async video test")
    args = parser.parse_args()

    ok = test_health(args.base_url, args.timeout)
    if not args.skip_chat:
        test_chat(args.base_url, args.timeout)
    if not args.skip_image:
        test_image(args.base_url, args.timeout)
    if not args.skip_video:
        test_video_async(args.base_url, args.timeout, args.poll_wait, args.poll_attempts)

    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
