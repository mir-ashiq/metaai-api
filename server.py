"""FastAPI server for Meta AI SDK with cookie-based authentication."""

import os
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from metaai_api import MetaAI

app = FastAPI(
    title="Meta AI API",
    description="RESTful API wrapper for Meta AI SDK",
    version="1.0.0"
)


class ChatRequest(BaseModel):
    """Chat request model."""
    message: str = Field(..., description="The message to send to Meta AI")
    stream: bool = Field(False, description="Whether to stream the response")
    new_conversation: bool = Field(False, description="Start a new conversation")
    conversation_id: Optional[str] = Field(None, description="Existing conversation ID")
    images: Optional[List[str]] = Field(None, description="List of image URLs to analyze")
    cookies: Optional[Dict[str, str]] = Field(None, description="Custom cookies (overrides env)")


class VideoRequest(BaseModel):
    """Video generation request model."""
    prompt: str = Field(..., description="Video generation prompt")
    wait_before_poll: int = Field(10, description="Seconds to wait before polling")
    max_attempts: int = Field(30, description="Maximum polling attempts")
    wait_seconds: int = Field(5, description="Seconds between polling attempts")
    verbose: bool = Field(False, description="Enable verbose logging")
    cookies: Optional[Dict[str, str]] = Field(None, description="Custom cookies (overrides env)")


def get_cookies_from_env() -> Optional[Dict[str, str]]:
    """Load cookies from environment variables."""
    # Try JSON format first
    cookies_json = os.getenv("META_AI_COOKIES_JSON")
    if cookies_json:
        try:
            cookies = json.loads(cookies_json)
            if cookies and isinstance(cookies, dict):
                return {k: v for k, v in cookies.items() if v}
        except json.JSONDecodeError:
            pass
    
    # Try individual cookie values
    cookies = {}
    cookie_map = {
        "META_AI_ABRA_SESS": "abra_sess",
        "META_AI_ABRA_CSRF": "abra_csrf",
        "META_AI_DATR": "datr",
        "META_AI_JS_DATR": "_js_datr",
        "META_AI_LSD": "lsd",
        "META_AI_FB_DTSG": "fb_dtsg",
        "META_AI_DPR": "dpr",
        "META_AI_WD": "wd",
    }
    
    for env_var, cookie_name in cookie_map.items():
        value = os.getenv(env_var)
        if value:
            cookies[cookie_name] = value
    
    return cookies if cookies else None


def create_meta_ai_client(custom_cookies: Optional[Dict[str, str]] = None) -> MetaAI:
    """Create MetaAI client with cookies from env or custom cookies."""
    cookies = custom_cookies or get_cookies_from_env()
    
    fb_email = os.getenv("META_AI_FB_EMAIL")
    fb_password = os.getenv("META_AI_FB_PASSWORD")
    
    proxy_http = os.getenv("META_AI_PROXY_HTTP")
    proxy_https = os.getenv("META_AI_PROXY_HTTPS")
    proxy = None
    if proxy_http or proxy_https:
        proxy = {
            "http": proxy_http,
            "https": proxy_https or proxy_http
        }
    
    return MetaAI(
        fb_email=fb_email,
        fb_password=fb_password,
        cookies=cookies,
        proxy=proxy
    )


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Meta AI API Server",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    cookies = get_cookies_from_env()
    return {
        "status": "ok",
        "cookies_loaded": bool(cookies),
        "cookie_count": len(cookies) if cookies else 0
    }


@app.post("/chat")
async def chat(request: ChatRequest):
    """Chat with Meta AI."""
    try:
        client = create_meta_ai_client(request.cookies)
        
        # Set conversation ID if provided
        if request.conversation_id:
            client.external_conversation_id = request.conversation_id
        
        # Send message
        response = client.prompt(
            message=request.message,
            stream=request.stream,
            new_conversation=request.new_conversation,
            images=request.images
        )
        
        if request.stream:
            # Return streaming response
            async def generate():
                for chunk in response:
                    yield f"data: {json.dumps(chunk)}\n\n"
            
            return StreamingResponse(
                generate(),
                media_type="text/event-stream"
            )
        else:
            # Return regular response
            return {
                "message": response.get("message", ""),
                "sources": response.get("sources", []),
                "media": response.get("media", []),
                "conversation_id": client.external_conversation_id,
            }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/videos")
async def generate_video(request: VideoRequest):
    """Generate video with Meta AI."""
    try:
        client = create_meta_ai_client(request.cookies)
        
        # Check for required cookies
        cookies = request.cookies or get_cookies_from_env()
        if not cookies or "abra_sess" not in cookies:
            raise HTTPException(
                status_code=400,
                detail="Video generation requires 'abra_sess' cookie. Please set META_AI_COOKIES_JSON in .env file."
            )
        
        # Ensure prompt starts with "Generate a video of"
        prompt = request.prompt
        if not prompt.lower().startswith("generate a video"):
            prompt = f"Generate a video of {prompt}"
        
        print(f"\n{'='*60}")
        print(f"🎬 Video Generation Request")
        print(f"{'='*60}")
        print(f"Prompt: {prompt}")
        print(f"Wait before poll: {request.wait_before_poll}s")
        print(f"Max attempts: {request.max_attempts}")
        print(f"Wait between: {request.wait_seconds}s")
        print(f"{'='*60}\n")
        
        # Generate video
        result = client.generate_video(
            prompt=prompt,
            wait_before_poll=request.wait_before_poll,
            max_attempts=request.max_attempts,
            wait_seconds=request.wait_seconds,
            verbose=request.verbose
        )
        
        # Add additional info to result
        result["requested_prompt"] = request.prompt
        result["actual_prompt"] = prompt
        
        print(f"\n{'='*60}")
        print(f"✅ Video Generation Result")
        print(f"{'='*60}")
        print(f"Success: {result.get('success', False)}")
        print(f"Video URLs: {len(result.get('video_urls', []))} found")
        print(f"Conversation ID: {result.get('conversation_id', 'N/A')}")
        print(f"{'='*60}\n")
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"\n❌ Video Generation Error: {str(e)}\n")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/cookies/status")
async def cookies_status():
    """Check cookie configuration status."""
    cookies = get_cookies_from_env()
    
    if not cookies:
        return {
            "configured": False,
            "message": "No cookies found in environment. Set META_AI_COOKIES_JSON in .env file.",
            "required_for": ["video_generation"],
            "optional_for": ["chat", "image_generation"]
        }
    
    return {
        "configured": True,
        "cookie_count": len(cookies),
        "has_abra_sess": "abra_sess" in cookies,
        "cookies": list(cookies.keys()),
        "video_generation_ready": "abra_sess" in cookies
    }


if __name__ == "__main__":
    import sys
    
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", 8000))
    
    print("=" * 70)
    print(f"Starting Meta AI API Server")
    print("=" * 70)
    print(f"Server: http://{host}:{port}")
    print(f"Docs:   http://{host}:{port}/docs")
    print(f"Health: http://{host}:{port}/health")
    print("=" * 70)
    print()
    
    # Use Hypercorn for Python 3.13 compatibility
    try:
        import hypercorn.asyncio
        from hypercorn.config import Config
        import asyncio
        
        config = Config()
        config.bind = [f"{host}:{port}"]
        
        asyncio.run(hypercorn.asyncio.serve(app, config))
    except ImportError:
        print("⚠️  Hypercorn not found, trying uvicorn...")
        print("   For Python 3.13, install hypercorn: pip install hypercorn")
        print()
        import uvicorn
        uvicorn.run(app, host=host, port=port)
