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
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
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

# Request timeout (seconds) - prevents infinite hangs on long-running operations
DEFAULT_REQUEST_TIMEOUT = 120
REQUEST_TIMEOUT = int(os.getenv("META_AI_REQUEST_TIMEOUT_SECONDS", DEFAULT_REQUEST_TIMEOUT))

# CORS configuration
DEFAULT_ALLOWED_ORIGINS = ["*"]
CORS_ALLOWED_ORIGINS_ENV = os.getenv("META_AI_CORS_ALLOWED_ORIGINS", "")
CORS_ALLOWED_ORIGINS = [
    origin.strip() for origin in CORS_ALLOWED_ORIGINS_ENV.split(",")
] if CORS_ALLOWED_ORIGINS_ENV else DEFAULT_ALLOWED_ORIGINS


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

# Add CORS middleware to allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handler for unhandled exceptions - returns JSON
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Convert any unhandled exception to JSON response."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "detail": str(exc) if logger.level == logging.DEBUG else "An unexpected error occurred"
        }
    )

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

# Global MetaAI instance (initialized once at startup)
_meta_ai_instance: Optional[MetaAI] = None


async def get_cookies() -> Dict[str, str]:
    await cache.refresh_if_needed()
    return await cache.snapshot()


@app.on_event("startup")
async def _startup() -> None:
    await cache.load_seed()
    # Skip initial refresh to avoid unnecessary token fetching
    # Tokens will be refreshed on-demand if needed
    # await cache.refresh_if_needed(force=True)
    
    # Initialize global MetaAI instance to prevent repeated token extraction
    global _meta_ai_instance, refresh_task
    logger.info("Initializing global MetaAI instance...")
    
    try:
        _meta_ai_instance = MetaAI(proxy=_get_proxies())
        
        # Log token status (handle case where extraction failed)
        if _meta_ai_instance.access_token:
            logger.info(f"MetaAI instance initialized with access token: {_meta_ai_instance.access_token[:50]}...")
        else:
            logger.warning("MetaAI instance initialized but access token extraction failed (may be rate-limited). Will retry in background.")
    except Exception as init_exc:  # noqa: BLE001
        logger.error(f"Failed to initialize MetaAI instance: {init_exc}")
        logger.warning("Server will start without MetaAI instance. API requests will fail until initialization succeeds.")
        _meta_ai_instance = None
    
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
    # Use global MetaAI instance
    if _meta_ai_instance is None:
        raise HTTPException(status_code=503, detail="MetaAI instance not initialized yet. Server may be rate-limited. Please try again in a moment.")
    ai = _meta_ai_instance
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
    """Generate images from text prompts."""
    if _meta_ai_instance is None:
        return JSONResponse(
            status_code=503,
            content={
                "success": False,
                "error": "MetaAI instance not initialized",
                "detail": "Server is initializing or rate-limited. Please try again in a moment."
            }
        )
    ai = _meta_ai_instance
    try:
        # Use the new generation API with timeout protection
        result = await asyncio.wait_for(
            run_in_threadpool(
                ai.generate_image_new,
                prompt=body.prompt,
                orientation=body.orientation or "VERTICAL",
                num_images=1,
                media_ids=body.media_ids,
                attachment_metadata=body.attachment_metadata
            ),
            timeout=REQUEST_TIMEOUT
        )
        return cast(Dict[str, Any], result)
    except asyncio.TimeoutError:
        logger.warning(f"Image generation timeout after {REQUEST_TIMEOUT}s for prompt: {body.prompt[:50]}...")
        return JSONResponse(
            status_code=504,
            content={
                "success": False,
                "error": "Image generation timeout",
                "detail": f"Request exceeded {REQUEST_TIMEOUT} second timeout. The generation may still be processing."
            }
        )
    except Exception as exc:  # noqa: BLE001
        logger.error(f"Image generation error: {exc}")
        await cache.refresh_after_error()
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(exc),
                "detail": "Image generation failed"
            }
        )


@app.post("/video")
async def video(body: VideoRequest) -> Dict[str, Any]:
    """Generate videos from text prompts (synchronous)."""
    if _meta_ai_instance is None:
        return JSONResponse(
            status_code=503,
            content={
                "success": False,
                "error": "MetaAI instance not initialized",
                "detail": "Server is initializing or rate-limited. Please try again in a moment."
            }
        )
    ai = _meta_ai_instance
    try:
        # Use the new generation API with timeout protection
        result = await asyncio.wait_for(
            run_in_threadpool(
                ai.generate_video_new,
                prompt=body.prompt,
                media_ids=body.media_ids,
                attachment_metadata=body.attachment_metadata
            ),
            timeout=REQUEST_TIMEOUT
        )
        return cast(Dict[str, Any], result)
    except asyncio.TimeoutError:
        logger.warning(f"Video generation timeout after {REQUEST_TIMEOUT}s for prompt: {body.prompt[:50]}...")
        return JSONResponse(
            status_code=504,
            content={
                "success": False,
                "error": "Video generation timeout",
                "detail": f"Request exceeded {REQUEST_TIMEOUT} second timeout. Use /video/async for longer operations."
            }
        )
    except Exception as exc:  # noqa: BLE001
        logger.error(f"Video generation error: {exc}")
        await cache.refresh_after_error()
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(exc),
                "detail": "Video generation failed"
            }
        )


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
        
        # Use global MetaAI instance
        if _meta_ai_instance is None:
            return JSONResponse(
                status_code=503,
                content={
                    "success": False,
                    "error": "MetaAI instance not initialized",
                    "detail": "Server is initializing or rate-limited. Please try again in a moment."
                }
            )
        ai = _meta_ai_instance
        
        # Upload with timeout protection
        result = await asyncio.wait_for(
            run_in_threadpool(ai.upload_image, temp_path),
            timeout=60
        )
        
        return cast(Dict[str, Any], result)
    
    except asyncio.TimeoutError:
        logger.warning(f"Image upload timeout after 60s for file: {file.filename}")
        return JSONResponse(
            status_code=504,
            content={
                "success": False,
                "error": "Upload timeout",
                "detail": "Image upload exceeded 60 second timeout. Please try again."
            }
        )
    except Exception as exc:  # noqa: BLE001
        logger.error(f"Image upload error: {exc}")
        await cache.refresh_after_error()
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(exc),
                "detail": "Image upload failed"
            }
        )
    
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
    # Use global MetaAI instance
    if _meta_ai_instance is None:
        await jobs.set_error(job_id, "MetaAI instance not initialized yet. Server may be rate-limited.")
        return
    ai = _meta_ai_instance
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
    # If initial token extraction failed, retry after a short delay
    global _meta_ai_instance
    
    # If MetaAI instance creation completely failed, retry after delay
    if _meta_ai_instance is None:
        logger.info("MetaAI instance not initialized. Waiting 30 seconds before retry...")
        await asyncio.sleep(30)
        try:
            logger.info("Retrying MetaAI instance initialization...")
            _meta_ai_instance = MetaAI(proxy=_get_proxies())
            if _meta_ai_instance and _meta_ai_instance.access_token:
                logger.info(f"MetaAI instance successfully initialized: {_meta_ai_instance.access_token[:50]}...")
            else:
                logger.warning("MetaAI instance created but token extraction failed. Will retry in next cycle.")
        except Exception as init_exc:  # noqa: BLE001
            logger.error(f"Failed to initialize MetaAI instance on retry: {init_exc}")
            logger.info("Will retry in next refresh cycle.")
    
    # If token extraction failed but instance exists, retry immediately
    elif not _meta_ai_instance.access_token:
        logger.info("Initial token extraction failed. Waiting 30 seconds before retry...")
        await asyncio.sleep(30)
        try:
            logger.info("Retrying access token extraction...")
            _meta_ai_instance.access_token = _meta_ai_instance.extract_access_token_from_page()
            if _meta_ai_instance.access_token:
                logger.info(f"Access token successfully extracted: {_meta_ai_instance.access_token[:50]}...")
            else:
                logger.warning("Token extraction retry failed. Will retry in next refresh cycle.")
        except Exception as token_exc:  # noqa: BLE001
            logger.error(f"Failed to extract access token on retry: {token_exc}")
    
    while True:
        try:
            await cache.refresh_if_needed(force=True)
            
            # Refresh access token for the global MetaAI instance
            if _meta_ai_instance:
                logger.info("Refreshing access token for global MetaAI instance...")
                try:
                    new_token = _meta_ai_instance.extract_access_token_from_page()
                    if new_token:
                        _meta_ai_instance.access_token = new_token
                        logger.info(f"Access token refreshed: {_meta_ai_instance.access_token[:50]}...")
                    else:
                        logger.warning("Token refresh returned None. Keeping existing token.")
                except Exception as token_exc:  # noqa: BLE001
                    logger.error(f"Failed to refresh access token: {token_exc}")
            else:
                # Try to recreate MetaAI instance if it's still None
                logger.info("MetaAI instance is None. Attempting to recreate...")
                try:
                    _meta_ai_instance = MetaAI(proxy=_get_proxies())
                    if _meta_ai_instance and _meta_ai_instance.access_token:
                        logger.info(f"MetaAI instance recreated successfully: {_meta_ai_instance.access_token[:50]}...")
                except Exception as recreate_exc:  # noqa: BLE001
                    logger.error(f"Failed to recreate MetaAI instance: {recreate_exc}")
        except Exception as exc:  # noqa: BLE001
            logger.warning("Background refresh failed: %s", exc)
        await asyncio.sleep(REFRESH_SECONDS)
