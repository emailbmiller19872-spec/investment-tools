# Use a Python base image
FROM python:3.10-slim

# Install the compiler tools needed to fix the lru-dict error
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your code
COPY . .

# Change this to your actual start command (e.g., python main.py)
CMD ["python", "main.py"]
