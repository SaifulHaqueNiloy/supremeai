#!/usr/bin/env bash
# Smart Build Script for SupremeAI Frontend (Self-Healing) v2.0
# Fixed: Added proper error handling, admin build support, and environment detection

set -e  # Exit on any error

echo "==========================================="
echo "🚀 Starting Smart Build for Frontend..."
echo "==========================================="

# Detect build mode from environment
BUILD_MODE="${VITE_PORTAL_TYPE:-user}"
echo "📋 Build Mode: $BUILD_MODE"

echo "📦 Installing pnpm..."
npm install -g pnpm@9

echo "📦 Attempting to install monorepo dependencies..."
pnpm install --no-frozen-lockfile
EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
    echo "⚠️ Dependency installation failed with exit code $EXIT_CODE!"
    echo "🧹 Possible corrupted cache detected. Clearing node_modules..."
    
    # Remove node_modules at root and inside frontend
    rm -rf node_modules
    rm -rf frontend/node_modules
    
    # Remove pnpm store cache if it exists locally
    pnpm store prune || true
    
    echo "🔄 Retrying clean installation..."
    pnpm install --no-frozen-lockfile
    
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install dependencies after retry. Exiting."
        exit 1
    fi
else
    echo "✅ Frontend dependencies installed successfully."
fi

echo "🏗️ Building frontend ($BUILD_MODE mode)..."
cd frontend

# Build based on portal type
if [ "$BUILD_MODE" = "admin" ]; then
    echo "🔧 Building Admin Portal..."
    pnpm run build:admin
else
    echo "🎨 Building User Portal..."
    pnpm run build:user
fi

echo "✅ Frontend build finished successfully!"
echo "📁 Output directory: $(ls -la dist-*/ 2>/dev/null || ls -la dist/ 2>/dev/null || echo 'dist-user')"
