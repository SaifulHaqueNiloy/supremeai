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

poetry install --only main > poetry_install.log 2>&1
EXIT_CODE=$?

# Re-enable exit-on-error
set -e

if [ $EXIT_CODE -ne 0 ]; then
    echo "⚠️ Dependency installation failed with exit code $EXIT_CODE!"
    echo "Uploading log to dpaste..."
    cat poetry_install.log | curl -s -F "content=<-" https://dpaste.com/api/v2/
    echo "🧹 Possible corrupted cache detected. Clearing .venv and ~/.cache/pypoetry..."
    
    # Remove local virtual environment if it exists
    rm -rf .venv
    
    # Remove poetry global cache
    rm -rf ~/.cache/pypoetry
    
    echo "🔄 Retrying clean installation..."
    set +e
    poetry install --only main > poetry_install2.log 2>&1
    EXIT_CODE2=$?
    set -e
    if [ $EXIT_CODE2 -ne 0 ]; then
        echo "Second installation failed. Log:"
        cat poetry_install2.log | curl -s -F "content=<-" https://dpaste.com/api/v2/
        exit 1
    fi
else
    echo "✅ Backend dependencies installed successfully."
fi

echo "🎉 Backend build finished successfully!"
