#!/bin/sh
set -e

if command -v koyeb >/dev/null 2>&1; then
  echo "Koyeb CLI already installed."
  koyeb --version
  exit 0
fi

echo "Installing Koyeb CLI..."
curl -fsSL https://app.koyeb.com/install.sh | bash

echo "Koyeb CLI installed. Add ~/.koyeb/bin to your PATH if needed."
echo "Then run: koyeb login"
