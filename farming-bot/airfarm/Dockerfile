FROM python:3.10-slim

# Install build tools for lru-dict
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    postgresql-client \
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

# Start the app
CMD ["python", "main.py"]
