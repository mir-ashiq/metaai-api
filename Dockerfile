# Base Python image
FROM python:3.11-slim

# Don’t write .pyc files & keep logs unbuffered
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install deps
COPY requirements.txt .

RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir metaai-sdk

# Copy app code
COPY . .

# Tell container what port will be used
EXPOSE 8000

# Launch Uvicorn binding to 0.0.0.0 on port 8000
CMD ["uvicorn", "metaai_api.api_server:app", "--host", "0.0.0.0", "--port", "8000"]
