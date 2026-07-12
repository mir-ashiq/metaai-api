# Base Python image
FROM python:3.11-slim

# Don't write .pyc files & keep logs unbuffered
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system deps for Chrome
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates fonts-liberation libasound2 libatk-bridge2.0-0 \
    libatk1.0-0 libcups2 libdbus-1-3 libdrm2 libgbm1 libgtk-3-0 \
    libnspr4 libnss3 libx11-xcb1 libxcomposite1 libxdamage1 libxrandr2 \
    xdg-utils curl \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js for agent-browser
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    npm install -g agent-browser && \
    agent-browser install

# Install deps
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Install the package itself
RUN pip install --no-cache-dir -e ".[api]"

# Tell container what port will be used
EXPOSE 8000

# Launch Uvicorn binding to 0.0.0.0 on port 8000
CMD ["uvicorn", "metaai_api.api_server:app", "--host", "0.0.0.0", "--port", "8000"]
