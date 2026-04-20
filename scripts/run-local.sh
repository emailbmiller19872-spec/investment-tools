#!/bin/sh
set -e

if [ ! -f .env ]; then
  echo ".env file missing. Copy .env.example to .env and fill in your values."
  exit 1
fi

docker build -t autonomous-airdrop-capital-builder:latest .

docker run --rm -it \
  --env-file .env \
  autonomous-airdrop-capital-builder:latest
