FROM python:3.10-slim

ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

# Install Chrome and dependencies for Selenium
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gnupg \
    unzip \
    fonts-liberation \
    chromium \
    chromium-driver \
    build-essential \
    python3-dev \
    postgresql-client \
    jq \
    bc \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# FIX THE MODULE ERROR: This tells Python to look in /app for 'utils'
ENV PYTHONPATH="/app"

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all your files
COPY . .

# Use Chromium in headless mode by default
ENV HEADLESS=true
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

# Start the app
CMD ["python", "main.py"]
