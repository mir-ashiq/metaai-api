import asyncio
import contextlib
import logging
import os
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Optional, cast

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, UploadFile, File, Form
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field

from metaai_api import MetaAI

logger = logging.getLogger(__name__)

# Load .env file if it exists
env_path = Path(__file__).parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
    logger.info(f"Loaded environment variables from {env_path}")

# Refresh interval (seconds) for keeping lsd/fb_dtsg/cookies fresh
DEFAULT_REFRESH_SECONDS = 3600
REFRESH_SECONDS = int(os.getenv("META_AI_REFRESH_INTERVAL_SECONDS", DEFAULT_REFRESH_SECONDS))


class TokenCache:
    """Thread-safe cache for Meta cookies and tokens."""

    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._cookies: Dict[str, str] = {}
        self._last_refresh: float = 0.0

    async def load_seed(self) -> None:
        seed = {
            "datr": os.getenv("META_AI_DATR", ""),
            "abra_sess": os.getenv("META_AI_ABRA_SESS", ""),
            "dpr": os.getenv("META_AI_DPR", ""),
            "wd": os.getenv("META_AI_WD", ""),
            "_js_datr": os.getenv("META_AI_JS_DATR", ""),
            "abra_csrf": os.getenv("META_AI_ABRA_CSRF", ""),
        }
        missing = [k for k in ("datr", "abra_sess") if not seed.get(k)]
        if missing:
            raise RuntimeError(f"Missing required seed cookies: {', '.join(missing)}")
        async with self._lock:
            self._cookies = {k: v for k, v in seed.items() if v}
            self._last_refresh = 0.0

    async def refresh_if_needed(self, force: bool = False) -> None:
        now = time.time()
        if not force and (now - self._last_refresh) < REFRESH_SECONDS:
            return
        async with self._lock:
            if not force and (time.time() - self._last_refresh) < REFRESH_SECONDS:
                return
            try:
                ai = MetaAI(cookies=dict(self._cookies))
                # MetaAI may fetch lsd/fb_dtsg; capture any updates
                self._cookies = getattr(ai, "cookies", self._cookies)
                self._last_refresh = time.time()
            except Exception as exc:  # noqa: BLE001
                logger.warning("Cookie refresh failed: %s", exc)
                if force:
                    raise

    async def refresh_after_error(self) -> None:
        await self.refresh_if_needed(force=True)

    async def snapshot(self) -> Dict[str, str]:
        async with self._lock:
            return dict(self._cookies)


cache = TokenCache()
refresh_task: Optional[asyncio.Task] = None
app = FastAPI(title="Meta AI API Service", version="0.1.0")


def _get_proxies() -> Optional[Dict[str, str]]:
    http_proxy = os.getenv("META_AI_PROXY_HTTP")
    https_proxy = os.getenv("META_AI_PROXY_HTTPS")
    if not http_proxy and not https_proxy:
        return None
    proxies: Dict[str, str] = {}
    if http_proxy:
        proxies["http"] = http_proxy
    if https_proxy:
        proxies["https"] = https_proxy
    return proxies


class ChatRequest(BaseModel):
    message: str
    stream: bool = False
    new_conversation: bool = False
    media_ids: Optional[list] = None
    attachment_metadata: Optional[dict] = None  # {'file_size': int, 'mime_type': str}


class ImageRequest(BaseModel):
    prompt: str
    new_conversation: bool = False
    media_ids: Optional[list] = None
    attachment_metadata: Optional[dict] = None  # {'file_size': int, 'mime_type': str}


class VideoRequest(BaseModel):
    prompt: str
    media_ids: Optional[list] = None
    attachment_metadata: Optional[dict] = None  # {'file_size': int, 'mime_type': str}
    wait_before_poll: int = Field(10, ge=0, le=60)
    max_attempts: int = Field(30, ge=1, le=60)
    wait_seconds: int = Field(5, ge=1, le=30)
    verbose: bool = False


class ImageUploadResponse(BaseModel):
    success: bool
    media_id: Optional[str] = None
    upload_session_id: Optional[str] = None
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    error: Optional[str] = None


class JobStatus(BaseModel):
    job_id: str
    status: str
    created_at: float
    updated_at: float
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class JobStore:
    def __init__(self) -> None:
        self._jobs: Dict[str, JobStatus] = {}
        self._lock = asyncio.Lock()

    async def create(self) -> JobStatus:
        now = time.time()
        job_id = str(uuid.uuid4())
        job = JobStatus(job_id=job_id, status="pending", created_at=now, updated_at=now)
        async with self._lock:
            self._jobs[job_id] = job
        return job

    async def set_running(self, job_id: str) -> None:
        await self._update(job_id, status="running")

    async def set_result(self, job_id: str, result: Dict[str, Any]) -> None:
        await self._update(job_id, status="succeeded", result=result, error=None)

    async def set_error(self, job_id: str, error: str) -> None:
        await self._update(job_id, status="failed", error=error)

    async def get(self, job_id: str) -> JobStatus:
        async with self._lock:
            if job_id not in self._jobs:
                raise KeyError(job_id)
            return self._jobs[job_id]

    async def _update(self, job_id: str, **fields: Any) -> None:
        async with self._lock:
            if job_id not in self._jobs:
                raise KeyError(job_id)
            job = self._jobs[job_id].copy(update=fields)
            job.updated_at = time.time()
            self._jobs[job_id] = job


jobs = JobStore()


async def get_cookies() -> Dict[str, str]:
    await cache.refresh_if_needed()
    return await cache.snapshot()


@app.on_event("startup")
async def _startup() -> None:
    await cache.load_seed()
    await cache.refresh_if_needed(force=True)
    global refresh_task
    refresh_task = asyncio.create_task(_refresh_loop())


@app.on_event("shutdown")
async def _shutdown() -> None:
    global refresh_task
    if refresh_task:
        refresh_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await refresh_task


@app.post("/chat")
async def chat(body: ChatRequest, cookies: Dict[str, str] = Depends(get_cookies)) -> Dict[str, Any]:
    if body.stream:
        raise HTTPException(status_code=400, detail="Streaming not supported via HTTP JSON; set stream=false")
    ai = MetaAI(cookies=cookies, proxy=_get_proxies())
    try:
        return cast(Dict[str, Any], ai.prompt(body.message, stream=False, new_conversation=body.new_conversation, media_ids=body.media_ids, attachment_metadata=body.attachment_metadata))
    except Exception as exc:  # noqa: BLE001
        await cache.refresh_after_error()
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.post("/image")
async def image(body: ImageRequest, cookies: Dict[str, str] = Depends(get_cookies)) -> Dict[str, Any]:
    ai = MetaAI(cookies=cookies, proxy=_get_proxies())
    try:
        return cast(Dict[str, Any], ai.prompt(
            body.prompt, 
            stream=False, 
            new_conversation=body.new_conversation, 
            media_ids=body.media_ids, 
            attachment_metadata=body.attachment_metadata,
            is_image_generation=True  # Image generation uses DISCOVER entrypoint
        ))
    except Exception as exc:  # noqa: BLE001
        await cache.refresh_after_error()
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.post("/video")
async def video(body: VideoRequest, cookies: Dict[str, str] = Depends(get_cookies)) -> Dict[str, Any]:
    ai = MetaAI(cookies=cookies, proxy=_get_proxies())
    try:
        return await run_in_threadpool(
            ai.generate_video,
            body.prompt,
            body.media_ids,
            body.attachment_metadata,
            body.wait_before_poll,
            body.max_attempts,
            body.wait_seconds,
            body.verbose,
        )
    except Exception as exc:  # noqa: BLE001
        await cache.refresh_after_error()
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.post("/video/async")
async def video_async(body: VideoRequest, cookies: Dict[str, str] = Depends(get_cookies)) -> Dict[str, str]:
    job = await jobs.create()
    asyncio.create_task(_run_video_job(job.job_id, body, cookies))
    return {"job_id": job.job_id, "status": "pending"}


@app.get("/video/jobs/{job_id}")
async def video_job_status(job_id: str) -> Dict[str, Any]:
    try:
        job = await jobs.get(job_id)
        return job.dict()
    except KeyError:
        raise HTTPException(status_code=404, detail="Job not found")


@app.post("/upload")
async def upload_image(
    file: UploadFile = File(...),
    cookies: Dict[str, str] = Depends(get_cookies)
) -> Dict[str, Any]:
    """Upload an image to Meta AI for use in conversations or media generation."""
    import tempfile
    import os
    
    # Create temporary file to save the upload
    temp_dir = tempfile.gettempdir()
    temp_path = os.path.join(temp_dir, f"metaai_upload_{uuid.uuid4()}_{file.filename}")
    
    try:
        # Save uploaded file to temporary location
        content = await file.read()
        with open(temp_path, 'wb') as f:
            f.write(content)
        
        # Initialize MetaAI with cookies and upload
        ai = MetaAI(cookies=cookies, proxy=_get_proxies())
        result = await run_in_threadpool(ai.upload_image, temp_path)
        
        return cast(Dict[str, Any], result)
    
    except Exception as exc:  # noqa: BLE001
        await cache.refresh_after_error()
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    
    finally:
        # Clean up temporary file
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:  # noqa: BLE001
                pass


@app.get("/healthz")
async def health() -> Dict[str, str]:
    return {"status": "ok"}


async def _run_video_job(job_id: str, body: VideoRequest, cookies: Dict[str, str]) -> None:
    await jobs.set_running(job_id)
    ai = MetaAI(cookies=cookies, proxy=_get_proxies())
    try:
        result = await run_in_threadpool(
            ai.generate_video,
            body.prompt,
            body.media_ids,
            body.attachment_metadata,
            body.wait_before_poll,
            body.max_attempts,
            body.wait_seconds,
            body.verbose,
        )
        await jobs.set_result(job_id, result)
    except Exception as exc:  # noqa: BLE001
        await cache.refresh_after_error()
        await jobs.set_error(job_id, str(exc))


async def _refresh_loop() -> None:
    while True:
        try:
            await cache.refresh_if_needed(force=True)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Background refresh failed: %s", exc)
        await asyncio.sleep(REFRESH_SECONDS)
