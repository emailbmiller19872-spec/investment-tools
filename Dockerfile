FROM python:3.12-slim-bullseye

ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gnupg \
    unzip \
    fonts-liberation \
    chromium \
    chromium-driver \
    jq \
    bc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip setuptools && pip install -r requirements.txt

COPY . .

# Use Chromium in headless mode by default
ENV HEADLESS=true
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

# Run from the correct subdirectory based on BOT_TYPE
CMD if [ "$BOT_TYPE" = "coinbot" ]; then cd farming-bot/coinbot && PYTHONPATH=/app/farming-bot/coinbot python main.py; elif [ "$BOT_TYPE" = "airfarm" ]; then cd farming-bot/airfarm && PYTHONPATH=/app/farming-bot/airfarm python main.py; else python main.py; fi
