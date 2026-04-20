FROM python:3.10-slim

# 1. Install compiler tools (keeps the lru-dict fix)
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# 2. Set the working directory
WORKDIR /app

# 3. CRITICAL: Add the current directory to Python's search path
ENV PYTHONPATH="/app"

# 4. Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy your code
COPY . .

# 6. Run the app
CMD ["python", "main.py"]
