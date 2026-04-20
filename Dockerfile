# Use Python 3.10 on Bullseye (more stable for Chrome)
FROM python:3.10-bullseye

# 1. Install Google Chrome
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && wget -q -O - https://google.com | apt-key add - \
    && sh -c 'echo "deb [arch=amd64] http://google.com stable main" >> /etc/apt/sources.list.d/google-chrome.list' \
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

# 5. THE FIX: Force Python to find 'utils' and keep logs visible
ENV PYTHONPATH="/app:/app/coinbot:/app/airfarm"
ENV PYTHONUNBUFFERED=1

# 6. Start the bot
CMD ["python", "main.py"]
