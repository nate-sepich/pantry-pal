#!/usr/bin/env bash
set -e

echo "\n=== PantryPal Environment Setup ===\n"

# Backend (API) setup
echo "Setting up Python backend..."
cd api
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "\nBackend dependencies installed.\n"

# Expo (UI) setup
echo "Setting up Expo (React Native) UI..."
cd ../expo/ppal
if [ -f "package.json" ]; then
  npm install
else
  echo "Warning: package.json not found in expo/ppal. Skipping UI setup."
fi

echo "\nExpo dependencies installed.\n"

echo "\nSetup complete!"
