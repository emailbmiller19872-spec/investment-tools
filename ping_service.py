#!/usr/bin/env python3
"""
Keep-Alive Ping Service for Render Free Tier
Pings your Render service every 10 minutes to prevent spin-down
"""

import os
import time
import logging
import requests
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Get service URL from environment or use default
SERVICE_URL = os.getenv('RENDER_SERVICE_URL', 'https://coinbot.onrender.com')
PING_INTERVAL = int(os.getenv('PING_INTERVAL_MINUTES', 10))  # Ping every 10 minutes

def ping_service():
    """Ping the health check endpoint"""
    try:
        health_url = f"{SERVICE_URL}/healthz"
        response = requests.get(health_url, timeout=30)

        if response.status_code == 200:
            data = response.json()
            logger.info(f"✓ Ping successful | Status: {data.get('bot_status')} | Claims: {data.get('claims_today')}")
            return True
        else:
            logger.warning(f"✗ Ping failed: HTTP {response.status_code}")
            return False

    except requests.exceptions.RequestException as e:
        logger.error(f"✗ Ping error: {e}")
        return False

def main():
    logger.info(f"Starting ping service for {SERVICE_URL}")
    logger.info(f"Ping interval: {PING_INTERVAL} minutes")
    logger.info("Press Ctrl+C to stop")

    # Convert minutes to seconds
    interval_seconds = PING_INTERVAL * 60

    try:
        while True:
            ping_service()
            logger.info(f"Sleeping for {PING_INTERVAL} minutes...")
            time.sleep(interval_seconds)
    except KeyboardInterrupt:
        logger.info("Ping service stopped")

if __name__ == "__main__":
    main()
