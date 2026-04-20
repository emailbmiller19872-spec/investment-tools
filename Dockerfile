# Use Python 3.10
FROM python:3.10-slim

# 1. Install Google Chrome and tools needed for Selenium
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    lsb-release \
    libgconf-2-4 \
    libnss3 \
    libxss1 \
    libasound2 \
    fonts-liberation \
    libatk-bridge2.0-0 \
    libgtk-3-0 \
    --no-install-recommends \
    && wget -q -O - https://google.com | apt-key add - \
    && echo "deb [arch=amd64] http://google.com stable main" >> /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# 2. Set the working directory
WORKDIR /app

# 3. Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copy all your project files
COPY . .

# 5. THE FIX: Force Python to find 'utils' in any folder
ENV PYTHONPATH="/app:/app/coinbot:/app/airfarm"
ENV PYTHONUNBUFFERED=1

# 6. Start the bot
CMD ["python", "main.py"]
