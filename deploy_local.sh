#!/bin/bash
# Local deployment script for Autonomous Airdrop Bot
# This script helps you deploy the bots locally using Docker Compose

set -e

echo "=========================================="
echo "  Autonomous Airdrop Bot - Local Deployment"
echo "=========================================="
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ .env file not found!"
    echo "Please run 'python setup_bot.py' first to create the .env file."
    exit 1
fi

# Check if data/wallets.enc exists
if [ ! -f data/wallets.enc ]; then
    echo "❌ Encrypted wallet store not found at data/wallets.enc"
    echo "Please run 'python generate_wallets.py' to generate your wallets."
    exit 1
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p data logs

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Build Docker images
echo "🔨 Building Docker images..."
docker-compose build

# Start the bots
echo "🚀 Starting the bots..."
docker-compose up -d

echo ""
echo "=========================================="
echo "  Deployment Complete!"
echo "=========================================="
echo ""
echo "To view logs:"
echo "  docker-compose logs -f"
echo ""
echo "To stop the bots:"
echo "  docker-compose down"
echo ""
echo "To restart the bots:"
echo "  docker-compose restart"
echo ""
echo "To check status:"
echo "  docker-compose ps"
echo ""
