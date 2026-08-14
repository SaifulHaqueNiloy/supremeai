#!/usr/bin/env bash
# Smart Build Script for SupremeAI Backend (Self-Healing)

echo "==========================================="
echo "🚀 Starting Smart Build for Backend..."
echo "==========================================="

# Install poetry if not available
if ! command -v poetry &> /dev/null; then
    echo "📦 Installing Poetry..."
    pip install poetry
fi

echo "📦 Attempting to install backend dependencies..."
# Disable exit-on-error temporarily to catch failures
set +e

poetry install --only main
EXIT_CODE=$?

# Re-enable exit-on-error
set -e

if [ $EXIT_CODE -ne 0 ]; then
    echo "⚠️ Dependency installation failed with exit code $EXIT_CODE!"
    echo "🧹 Possible corrupted cache detected. Clearing .venv and ~/.cache/pypoetry..."
    
    # Remove local virtual environment if it exists
    rm -rf .venv
    
    # Remove poetry global cache
    rm -rf ~/.cache/pypoetry
    
    echo "🔄 Retrying clean installation..."
    poetry install --only main
else
    echo "✅ Backend dependencies installed successfully."
fi

echo "🎉 Backend build finished successfully!"
