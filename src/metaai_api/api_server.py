import asyncio
import contextlib
import logging
import os
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Optional, cast

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, UploadFile, File, Form, Request
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field
import time as time_module

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
            "ecto_1_sess": os.getenv("META_AI_ECTO_1_SESS", ""),
            "dpr": os.getenv("META_AI_DPR", ""),
            "wd": os.getenv("META_AI_WD", ""),
            "_js_datr": os.getenv("META_AI_JS_DATR", ""),
            "abra_csrf": os.getenv("META_AI_ABRA_CSRF", ""),
            "rd_challenge": os.getenv("META_AI_RD_CHALLENGE", ""),
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
                # Create MetaAI with current cookies (cookie-based auth only)
                ai = MetaAI(cookies=dict(self._cookies))
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


# Middleware to log all requests
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time_module.time()
    logger.warning(f"[REQUEST] {request.method} {request.url.path} - Content-Type: {request.headers.get('content-type', 'none')}")
    
    try:
        response = await call_next(request)
        process_time = time_module.time() - start_time
        logger.warning(f"[RESPONSE] {request.method} {request.url.path} - Status: {response.status_code} - Time: {process_time:.2f}s")
        return response
    except Exception as exc:
        logger.error(f"[ERROR] {request.method} {request.url.path} - {exc}")
        raise


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
    orientation: Optional[str] = None  # 'VERTICAL', 'LANDSCAPE' (not HORIZONTAL), or 'SQUARE'


class VideoRequest(BaseModel):
    prompt: str
    media_ids: Optional[list] = None
    attachment_metadata: Optional[dict] = None  # {'file_size': int, 'mime_type': str}
    orientation: Optional[str] = None  # 'VERTICAL', 'LANDSCAPE', or 'SQUARE'
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
    # Skip initial refresh to avoid unnecessary token fetching
    # Tokens will be refreshed on-demand if needed
    # await cache.refresh_if_needed(force=True)
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
async def chat(body: ChatRequest) -> Dict[str, Any]:
    if body.stream:
        raise HTTPException(status_code=400, detail="Streaming not supported via HTTP JSON; set stream=false")
    # Create MetaAI - chat functionality is currently unavailable
    ai = MetaAI(proxy=_get_proxies())
    try:
        return cast(Dict[str, Any], await run_in_threadpool(
            ai.prompt,
            body.message,
            stream=False,
            new_conversation=body.new_conversation,
            media_ids=body.media_ids,
            attachment_metadata=body.attachment_metadata
        ))
    except Exception as exc:  # noqa: BLE001
        await cache.refresh_after_error()
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.post("/image")
async def image(body: ImageRequest) -> Dict[str, Any]:
    # Create MetaAI - image generation uses cookie-based auth
    ai = MetaAI(proxy=_get_proxies())
    try:
        # Use the new generation API that doesn't require fb_dtsg/lsd tokens
        result = await run_in_threadpool(
            ai.generate_image_new,
            prompt=body.prompt,
            orientation=body.orientation or "VERTICAL",
            num_images=1,
            media_ids=body.media_ids,
            attachment_metadata=body.attachment_metadata
        )
        return cast(Dict[str, Any], result)
    except Exception as exc:  # noqa: BLE001
        await cache.refresh_after_error()
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.post("/video")
async def video(body: VideoRequest) -> Dict[str, Any]:
    # Create MetaAI - video generation uses cookie-based auth
    ai = MetaAI(proxy=_get_proxies())
    try:
        # Use the new generation API that doesn't require fb_dtsg/lsd tokens
        result = await run_in_threadpool(
            ai.generate_video_new,
            prompt=body.prompt,
            media_ids=body.media_ids,
            attachment_metadata=body.attachment_metadata
        )
        return cast(Dict[str, Any], result)
    except Exception as exc:  # noqa: BLE001
        await cache.refresh_after_error()
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.post("/video/async")
async def video_async(body: VideoRequest) -> Dict[str, str]:
    job = await jobs.create()
    asyncio.create_task(_run_video_job(job.job_id, body))
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
    file: UploadFile = File(...)
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
        
        # Initialize MetaAI - upload uses cookie-based auth
        ai = MetaAI(proxy=_get_proxies())
        
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


async def _run_video_job(job_id: str, body: VideoRequest) -> None:
    logger.info(f"[JOB {job_id}] Starting video generation job")
    await jobs.set_running(job_id)
    # Create MetaAI - video generation uses cookie-based auth
    ai = MetaAI(proxy=_get_proxies())
    try:
        logger.info(f"[JOB {job_id}] Calling generate_video_new with prompt: {body.prompt[:100]}...")
        result = await run_in_threadpool(
            ai.generate_video_new,
            prompt=body.prompt,
            media_ids=body.media_ids,
            attachment_metadata=body.attachment_metadata
        )
        
        logger.info(f"[JOB {job_id}] Video generation completed")
        logger.info(f"[JOB {job_id}] Result success: {result.get('success', False)}")
        logger.info(f"[JOB {job_id}] Video URLs count: {len(result.get('video_urls', []))}")
        
        # Check if video generation actually succeeded AND we have video URLs
        video_urls = result.get('video_urls', [])
        if result.get('success', False) and video_urls and len(video_urls) > 0:
            logger.info(f"[JOB {job_id}] Marking as SUCCEEDED with {len(video_urls)} video(s)")
            for idx, url in enumerate(video_urls, 1):
                logger.info(f"[JOB {job_id}] Video URL {idx}: {url[:150]}...")
            await jobs.set_result(job_id, result)
        else:
            # Video generation failed or no videos generated - mark job as failed
            if not result.get('success', False):
                error_msg = result.get('error', 'Video generation failed')
                logger.warning(f"[JOB {job_id}] Marking as FAILED: {error_msg}")
            else:
                error_msg = 'Video generation completed but no video URLs were found. The video may still be processing or the extraction failed.'
                logger.warning(f"[JOB {job_id}] Marking as FAILED: Success=true but no URLs found")
                logger.debug(f"[JOB {job_id}] Full result: {result}")
            await jobs.set_error(job_id, error_msg)
    except Exception as exc:  # noqa: BLE001
        logger.error(f"[JOB {job_id}] Exception occurred: {exc}", exc_info=True)
        await cache.refresh_after_error()
        await jobs.set_error(job_id, str(exc))


async def _refresh_loop() -> None:
    while True:
        try:
            await cache.refresh_if_needed(force=True)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Background refresh failed: %s", exc)
        await asyncio.sleep(REFRESH_SECONDS)
