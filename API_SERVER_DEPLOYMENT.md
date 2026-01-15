# 🚀 API Server Deployment Guide

This guide explains how to deploy the Meta AI API server for production use.

## Quick Start

### 1. Install with API Dependencies

```bash
pip install metaai-sdk[api]
```

### 2. Configure Environment

Create a `.env` file with your Meta AI cookies:

```env
# Required cookies (get from https://meta.ai browser session)
META_AI_DATR=your_datr_cookie_value
META_AI_ABRA_SESS=your_abra_sess_cookie_value
META_AI_DPR=1
META_AI_WD=1920x1080

# Optional
META_AI_REFRESH_INTERVAL_SECONDS=3600  # Refresh every hour
```

### 3. Run the Server

```bash
uvicorn metaai_api.api_server:app --host 0.0.0.0 --port 8000
```

## Getting Meta AI Cookies

1. Open your browser and go to https://meta.ai
2. Open Developer Tools (F12)
3. Go to **Application** (Chrome) or **Storage** (Firefox) tab
4. Click **Cookies** → **https://meta.ai**
5. Copy these cookie values:
   - `datr`
   - `abra_sess`
   - `dpr`
   - `wd`

## API Endpoints

### Health Check

```bash
GET /healthz
```

**Response:**

```json
{ "status": "ok" }
```

### Chat Endpoint

```bash
POST /chat
Content-Type: application/json

{
  "message": "Your question here",
  "stream": false,
  "new_conversation": false
}
```

**Response:**

```json
{
  "message": "AI response text",
  "sources": [],
  "media": []
}
```

### Video Generation (Synchronous)

Blocks until video is ready or timeout.

```bash
POST /video
Content-Type: application/json

{
  "prompt": "Generate a video of a sunset",
  "wait_before_poll": 10,
  "max_attempts": 30,
  "wait_seconds": 5,
  "verbose": false
}
```

**Response:**

```json
{
  "success": true,
  "conversation_id": "uuid",
  "prompt": "Generate a video of a sunset",
  "video_urls": ["https://..."],
  "timestamp": 1234567890.123
}
```

### Video Generation (Asynchronous)

Returns immediately with job ID for polling.

```bash
POST /video/async
Content-Type: application/json

{
  "prompt": "Generate a video of a cat"
}
```

**Response:**

```json
{
  "job_id": "uuid",
  "status": "pending"
}
```

### Job Status

```bash
GET /video/jobs/{job_id}
```

**Response:**

```json
{
  "job_id": "uuid",
  "status": "succeeded",
  "created_at": 1234567890.0,
  "updated_at": 1234567891.0,
  "result": {
    "success": true,
    "video_urls": ["https://..."]
  },
  "error": null
}
```

**Job Statuses:**

- `pending` - Job created, not started yet
- `running` - Currently generating video
- `succeeded` - Video ready, check `result`
- `failed` - Error occurred, check `error`

## Production Deployment

### Docker

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir metaai-api[api]

# Copy environment (or use Docker secrets)
COPY .env .

# Run server
CMD ["uvicorn", "metaai_api.api_server:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:

```bash
docker build -t metaai-api .
docker run -p 8000:8000 --env-file .env metaai-api
```

### Using Gunicorn (Production)

```bash
pip install gunicorn

gunicorn metaai_api.api_server:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 120
```

### Environment Variables

| Variable                           | Required | Default | Description                       |
| ---------------------------------- | -------- | ------- | --------------------------------- |
| `META_AI_DATR`                     | ✅ Yes   | -       | Meta AI datr cookie               |
| `META_AI_ABRA_SESS`                | ✅ Yes   | -       | Meta AI abra_sess cookie          |
| `META_AI_DPR`                      | ❌ No    | -       | Device pixel ratio cookie         |
| `META_AI_WD`                       | ❌ No    | -       | Window dimensions cookie          |
| `META_AI_JS_DATR`                  | ❌ No    | -       | JavaScript datr cookie (optional) |
| `META_AI_ABRA_CSRF`                | ❌ No    | -       | CSRF token (optional)             |
| `META_AI_REFRESH_INTERVAL_SECONDS` | ❌ No    | 3600    | Cookie refresh interval           |
| `META_AI_PROXY_HTTP`               | ❌ No    | -       | HTTP proxy URL                    |
| `META_AI_PROXY_HTTPS`              | ❌ No    | -       | HTTPS proxy URL                   |

## Auto-Refresh Mechanism

The API server automatically refreshes Meta AI cookies to keep sessions alive:

1. **Startup Refresh**: Forced refresh when server starts
2. **Background Loop**: Refreshes every `REFRESH_INTERVAL_SECONDS` (default: 1 hour)
3. **Error Recovery**: Automatic refresh on 401/403 errors

This means you provide cookies **once** and the server maintains them automatically!

## Testing

Run the test suite:

```bash
python test_api.py
```

Test individual endpoints:

```bash
# Health check
curl http://localhost:8000/healthz

# Chat
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Hello Meta AI!","stream":false}'

# Async video
curl -X POST http://localhost:8000/video/async \
  -H "Content-Type: application/json" \
  -d '{"prompt":"Generate a sunset video"}'

# Check job status
curl http://localhost:8000/video/jobs/{job_id}
```

## Security Considerations

⚠️ **Important Security Notes:**

1. **Never commit `.env` file** - Add to `.gitignore`
2. **Protect your cookies** - They provide full access to your Meta AI account
3. **Use HTTPS** in production - Deploy behind nginx/Cloudflare
4. **Rate limiting** - Add rate limiting middleware for public deployments
5. **Authentication** - Consider adding API keys for production use

## Performance Tips

1. **Use async endpoints** for video generation to avoid blocking
2. **Set reasonable timeouts** - Video generation can take 2-5 minutes
3. **Monitor cookie refresh** - Check logs for refresh failures
4. **Use caching** - Consider caching chat responses for identical queries

## Troubleshooting

### Server won't start

**Error:** `RuntimeError: Missing required seed cookies`

**Solution:** Make sure `.env` file exists with `META_AI_DATR` and `META_AI_ABRA_SESS` values.

### 401/403 Errors

**Cause:** Cookies expired or invalid

**Solution:** The server auto-refreshes, but if persistent:

1. Get fresh cookies from browser
2. Update `.env` file
3. Restart server

### Video generation timeout

**Cause:** Meta AI servers slow or overloaded

**Solution:**

- Increase `max_attempts` in request
- Increase `wait_seconds` between polls
- Use async endpoint and poll manually

## Cloud Deployment Examples

### Railway

1. Fork the repository
2. Connect to Railway
3. Add environment variables in Railway dashboard
4. Deploy!

### Heroku

```bash
heroku create metaai-api
heroku config:set META_AI_DATR=your_value
heroku config:set META_AI_ABRA_SESS=your_value
git push heroku main
```

### Render

1. Create new Web Service
2. Connect GitHub repo
3. Set environment variables
4. Deploy

## Support

- 📖 [Main Documentation](README.md)
- 🎬 [Video Generation Guide](VIDEO_GENERATION_README.md)
- 🐛 [Report Issues](https://github.com/mir-ashiq/metaai-api/issues)
- ⭐ [Star on GitHub](https://github.com/mir-ashiq/metaai-api)
