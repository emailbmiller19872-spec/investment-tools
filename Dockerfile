FROM python:3.10-slim

# 1. Install build tools for lru-dict
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# 2. Set the working directory
WORKDIR /app

# 3. FIX THE MODULE ERROR: This tells Python to look in /app for 'utils'
ENV PYTHONPATH="/app"

# 4. Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy all your files
COPY . .

# 6. Start the app
CMD ["python", "main.py"]
