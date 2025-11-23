#!/bin/sh
# Startup script for the Meta AI API server

# Use PORT from environment or default to 8000
PORT=${PORT:-8000}
HOST=${HOST:-0.0.0.0}

echo "Starting Meta AI API Server..."
echo "Host: $HOST"
echo "Port: $PORT"

# Try hypercorn first (preferred for Python 3.13)
if command -v hypercorn >/dev/null 2>&1; then
    echo "Using Hypercorn ASGI server"
    exec hypercorn server:app --bind "$HOST:$PORT"
else
    echo "Hypercorn not found, using Uvicorn"
    exec uvicorn server:app --host "$HOST" --port "$PORT"
fi
