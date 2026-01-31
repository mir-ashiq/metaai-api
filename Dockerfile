# Use official Python image as base
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt ./

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Expose port (if running a server, adjust as needed)
EXPOSE 8000

# Default command (adjust as needed, e.g., to run a server or script)
CMD ["uvicorn", "metaai_api.api_server:app", "--host", "0.0.0.0", "--port", "${PORT:-8000}", "--reload"]
