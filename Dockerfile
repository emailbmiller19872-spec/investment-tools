FROM python:3.10-bullseye

# 1. Install Google Chrome with the CORRECT key link
RUN apt-get update && apt-get install -y wget gnupg \
    && wget -q -O - https://google.com | apt-key add - \
    && echo "deb [arch=amd64] http://google.com stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# 2. Set the working directory
WORKDIR /app

# 3. Install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copy everything
COPY . .

# 5. Fix the paths for utils
ENV PYTHONPATH="/app:/app/coinbot:/app/airfarm"
ENV PYTHONUNBUFFERED=1

# 6. Run the bot
CMD ["python", "main.py"]
