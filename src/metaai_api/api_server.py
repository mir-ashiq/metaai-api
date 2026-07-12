"""FastAPI server for Meta AI — exposes the SDK as a REST API.

Endpoints match the original metaai-api repo:
    GET  /healthz              — health check
    POST /chat                 — send a chat message
    POST /image                — generate image from text
    POST /video                — generate video (returns 501 — not available)
    POST /video/async          — async video (returns 501)
    GET  /video/jobs/{job_id}  — job status (returns 404)
    POST /video/extend         — extend video (returns 501)
    POST /upload               — upload image (not yet supported via browser)
    GET  /conversations        — list conversations
    POST /media                — fetch media by card ID
    POST /reset                — reset browser session

Run:
    META_AI_DATR=... META_AI_ECTO_1_SESS=... python -m metaai_api.api_server
"""
from __future__ import annotations

import logging
import os
import threading
import time
from typing import Optional

from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from . import __version__
from .main import MetaAI
from .exceptions import (
    AuthenticationError, BrowserNotInstalledError, GenerationError,
    MetaAIError, TimeoutError as MetaAITimeoutError,
)

logger = logging.getLogger(__name__)

# ---- Pydantic models (matching original repo) ----

class ChatRequest(BaseModel):
    message: str
    stream: bool = False
    new_conversation: bool = False
    media_ids: Optional[list] = None
    attachment_metadata: Optional[dict] = None

class ImageRequest(BaseModel):
    prompt: str
    new_conversation: bool = False
    media_ids: Optional[list] = None
    attachment_metadata: Optional[dict] = None
    orientation: Optional[str] = None
    num_images: int = Field(1, ge=1, le=4)

class VideoRequest(BaseModel):
    prompt: str
    media_ids: Optional[list] = None
    attachment_metadata: Optional[dict] = None
    auto_poll: bool = True
    max_poll_attempts: int = Field(15, ge=1, le=60)
    poll_wait_seconds: int = Field(3, ge=1, le=30)
    orientation: Optional[str] = None
    wait_before_poll: int = Field(10, ge=0, le=60)
    max_attempts: int = Field(30, ge=1, le=60)

class VideoExtendRequest(BaseModel):
    media_id: str
    source_media_url: Optional[str] = None
    conversation_id: Optional[str] = None
    auto_poll: bool = True
    max_poll_attempts: int = Field(15, ge=1, le=60)
    poll_wait_seconds: int = Field(3, ge=1, le=30)

class FetchMediaRequest(BaseModel):
    card_id: str
    card_type: str = Field("IMAGE_CARD", pattern="^(IMAGE_CARD|VIDEO_CARD)$")

class HealthResponse(BaseModel):
    status: str; version: str; browser_ready: bool


# ---- Client manager ----

class ClientManager:
    def __init__(self):
        self._client: Optional[MetaAI] = None
        self._lock = threading.Lock()

    def get_client(self) -> MetaAI:
        with self._lock:
            if self._client is None:
                logger.info("Initializing MetaAI client...")
                self._client = MetaAI()
                self._client._get_browser()
                logger.info("MetaAI client ready")
            return self._client

    def reset(self):
        with self._lock:
            if self._client:
                try: self._client.close()
                except: pass
                self._client = None

client_manager = ClientManager()


# ---- Auth ----

def verify_api_key(authorization: Optional[str] = Header(None)):
    expected_key = os.getenv("META_AI_API_KEY")
    if not expected_key:
        return True
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header.")
    token = authorization[7:] if authorization.startswith("Bearer ") else authorization
    if token != expected_key:
        raise HTTPException(status_code=401, detail="Invalid API key.")
    return True


def handle_error(e: Exception, timeout: int = 60):
    if isinstance(e, AuthenticationError):
        client_manager.reset()
        raise HTTPException(status_code=401, detail="Meta AI cookies expired.")
    if isinstance(e, MetaAITimeoutError):
        raise HTTPException(status_code=504, detail=f"Timed out after {timeout}s")
    if isinstance(e, GenerationError):
        raise HTTPException(status_code=502, detail=str(e))
    if isinstance(e, BrowserNotInstalledError):
        raise HTTPException(status_code=500, detail=str(e))
    raise HTTPException(status_code=500, detail=str(e))


# ---- App ----

app = FastAPI(
    title="MetaAI API",
    description="Unofficial API server for Meta AI — image generation, chat, and more.",
    version=__version__,
    docs_url="/docs",
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])


@app.get("/healthz", response_model=HealthResponse)
async def health():
    """Health check endpoint."""
    return HealthResponse(status="ok", version=__version__,
                          browser_ready=client_manager._client is not None)


@app.post("/chat")
async def chat(req: ChatRequest, _=Depends(verify_api_key)):
    """Send a chat message to Meta AI."""
    start = time.time()
    try:
        client = client_manager.get_client()
        result = client.prompt(
            req.message,
            stream=req.stream,
            new_conversation=req.new_conversation,
            media_ids=req.media_ids,
            attachment_metadata=req.attachment_metadata,
        )
        return {
            "success": True,
            "message": result.get("message", ""),
            "conversation_id": result.get("conversation_id"),
            "elapsed_seconds": round(time.time()-start, 1),
        }
    except Exception as e:
        handle_error(e, 60)


@app.post("/image")
async def generate_image(req: ImageRequest, _=Depends(verify_api_key)):
    """Generate an image from a text prompt."""
    start = time.time()
    try:
        client = client_manager.get_client()
        result = client.generate_image_new(
            req.prompt,
            orientation=req.orientation or "VERTICAL",
            num_images=req.num_images,
            media_ids=req.media_ids,
            attachment_metadata=req.attachment_metadata,
            timeout=120,
        )
        return {
            "success": result["success"],
            "image_urls": result.get("image_urls", []),
            "conversation_id": result.get("conversation_id"),
            "prompt": result.get("prompt", ""),
            "elapsed_seconds": round(time.time()-start, 1),
        }
    except Exception as e:
        handle_error(e, 120)


@app.post("/video")
async def generate_video(req: VideoRequest, _=Depends(verify_api_key)):
    """Video generation is NOT available on Meta AI. Returns 501."""
    raise HTTPException(status_code=501,
        detail="Video generation is not available on Meta AI. "
               "Meta AI responds: 'I can't generate videos right now.'")


@app.post("/video/async")
async def generate_video_async(req: VideoRequest, _=Depends(verify_api_key)):
    """Video generation is NOT available on Meta AI. Returns 501."""
    raise HTTPException(status_code=501,
        detail="Video generation is not available on Meta AI.")


@app.get("/video/jobs/{job_id}")
async def video_job_status(job_id: str):
    """Video generation is NOT available. Returns 404."""
    raise HTTPException(status_code=404, detail="No video jobs — video generation is not available.")


@app.post("/video/extend")
async def video_extend(req: VideoExtendRequest, _=Depends(verify_api_key)):
    """Video generation is NOT available on Meta AI. Returns 501."""
    raise HTTPException(status_code=501,
        detail="Video extend is not available on Meta AI.")


@app.post("/upload")
async def upload_image(_=Depends(verify_api_key)):
    """Image upload is not yet supported via the browser method."""
    raise HTTPException(status_code=501,
        detail="Image upload is not yet supported via the browser method. "
               "Use the Python SDK with a browser session to upload images.")


@app.get("/conversations")
async def list_conversations(_=Depends(verify_api_key)):
    """List all conversations."""
    try:
        client = client_manager.get_client()
        convs = client.list_conversations()
        return {"success": True, "conversations": convs}
    except Exception as e:
        handle_error(e, 10)


@app.post("/media")
async def fetch_media(req: FetchMediaRequest, _=Depends(verify_api_key)):
    """Fetch media URLs by card ID."""
    try:
        client = client_manager.get_client()
        data = client.fetch_card_media(req.card_id, req.card_type)
        urls = client.generation_api.extract_media_urls(data)
        return {
            "success": True,
            "urls": urls,
            "card_id": req.card_id,
            "card_type": req.card_type,
        }
    except Exception as e:
        handle_error(e, 30)


@app.post("/reset")
async def reset_client(_=Depends(verify_api_key)):
    """Reset the browser session."""
    client_manager.reset()
    return {"status": "reset", "message": "Browser will restart on next request"}


@app.on_event("shutdown")
def shutdown():
    client_manager.reset()


def main():
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    if not os.getenv("META_AI_DATR") or not os.getenv("META_AI_ECTO_1_SESS"):
        print("ERROR: Set META_AI_DATR and META_AI_ECTO_1_SESS environment variables.")
        print("\nGet them from:")
        print("  1. Open https://www.meta.ai/ and log in")
        print("  2. DevTools → Application → Cookies")
        print("  3. Copy 'datr' and 'ecto_1_sess' values")
        raise SystemExit(1)
    print(f"Starting MetaAI API server on {host}:{port}")
    print(f"  Docs: http://localhost:{port}/docs")
    print(f"  API key: {'enabled' if os.getenv('META_AI_API_KEY') else 'disabled'}")
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    main()
