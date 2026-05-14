#!/bin/bash
#
# SupremeAI Google Cloud & Firebase Hosting Deployment Script
# Deploys Spring Boot backend to Cloud Run and dashboard to Firebase Hosting
#
# Prerequisites:
# - gcloud CLI installed and authenticated
# - Firebase CLI installed and authenticated
# - Project ID configured (default: supremeai-a)
#

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# --- Configuration ---
FIREBASE_PROJECT="${FIREBASE_PROJECT_ID:-supremeai-a}"
GCP_PROJECT="${GCP_PROJECT_ID:-supremeai-a}"
REGION="${GCP_REGION:-us-central1}"
BACKEND_SERVICE="supremeai-backend"
SERVICE_ACCOUNT="supremeai-backend@${GCP_PROJECT}.iam.gserviceaccount.com"

log_info "=== SupremeAI Deployment Started ==="
log_info "Firebase Project: $FIREBASE_PROJECT"
log_info "GCP Project: $GCP_PROJECT"
log_info "Region: $REGION"
log_info ""

# --- Pre-flight Checks ---
command -v gcloud >/dev/null 2>&1 || { log_error "gcloud CLI not found. Install: https://cloud.google.com/sdk/docs/install"; exit 1; }
command -v firebase >/dev/null 2>&1 || { log_error "Firebase CLI not found. Install: npm install -g firebase-tools"; exit 1; }
command -v node >/dev/null 2>&1 || { log_error "Node.js not found. Install Node.js 18+"; exit 1; }

log_info "✅ Pre-flight checks passed"

# --- Step 1: Build Backend JAR ---
log_info ""
log_info "=== Step 1: Building Spring Boot Backend ==="
./gradlew clean build -x test
if [ $? -ne 0 ]; then
    log_error "Backend build failed"
    exit 1
fi
log_info "✅ Backend JAR built successfully"

# --- Step 2: Build Dashboard ---
log_info ""
log_info "=== Step 2: Building Admin Dashboard ==="
cd dashboard

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    log_info "Installing dashboard dependencies..."
    npm ci
fi

# Source environment variables if .env exists
if [ -f ".env" ]; then
    log_info "Loading environment variables from .env"
    set -a
    source .env
    set +a
fi

# Build with environment variables
export VITE_FIREBASE_API_KEY="${VITE_FIREBASE_API_KEY}"
export VITE_FIREBASE_AUTH_DOMAIN="${VITE_FIREBASE_AUTH_DOMAIN:-supremeai-a.firebaseapp.com}"
export VITE_FIREBASE_PROJECT_ID="${VITE_FIREBASE_PROJECT_ID:-supremeai-a}"
export VITE_FIREBASE_STORAGE_BUCKET="${VITE_FIREBASE_STORAGE_BUCKET}"
export VITE_FIREBASE_MESSAGING_SENDER_ID="${VITE_FIREBASE_MESSAGING_SENDER_ID}"
export VITE_FIREBASE_APP_ID="${VITE_FIREBASE_APP_ID}"
export VITE_API_URL="${VITE_API_URL:-}"

npm run build

# Copy build artifacts to public/admin for Firebase Hosting
log_info "Copying dashboard build to public/admin/"
rm -rf ../public/admin/*
cp -r dist/* ../public/admin/
cd ..

if [ ! -f "public/admin/index.html" ]; then
    log_error "Dashboard build failed - index.html not found"
    exit 1
fi
log_info "✅ Dashboard built and staged for Firebase Hosting"

# --- Step 3: Build & Push Docker Image ---
log_info ""
log_info "=== Step 3: Building & Pushing Docker Image to GCR ==="

# Build & Push using Cloud Build (No local Docker required)
log_info "Building & Pushing Docker image using Cloud Build..."
gcloud builds submit --tag "gcr.io/${GCP_PROJECT}/${BACKEND_SERVICE}:latest" --project "$GCP_PROJECT" .

log_info "✅ Docker image built and pushed to gcr.io/${GCP_PROJECT}/${BACKEND_SERVICE}:latest"

# --- Step 4: Deploy Backend to Cloud Run ---
log_info ""
log_info "=== Step 4: Deploying to Cloud Run ==="

# Check if service exists
if gcloud run services describe "$BACKEND_SERVICE" --region "$REGION" --project "$GCP_PROJECT" >/dev/null 2>&1; then
    log_info "Updating existing Cloud Run service..."
    ACTION="--update-traffic=latest=100"
else
    log_info "Creating new Cloud Run service..."
    ACTION="--no-traffic"
fi

# Deploy
gcloud run deploy "$BACKEND_SERVICE" \
  --image "gcr.io/${GCP_PROJECT}/${BACKEND_SERVICE}:latest" \
  --region "$REGION" \
  --allow-unauthenticated \
  --set-env-vars="SPRING_PROFILES_ACTIVE=cloud,FIREBASE_PROJECT_ID=$GCP_PROJECT,REDIS_MOCK_ONLINE=true" \
  --cpu 2 \
  --memory 2Gi \
  --min-instances 1 \
  --max-instances 10 \
  --timeout 300 \
  --project "$GCP_PROJECT"

if [ $? -ne 0 ]; then
    log_error "Cloud Run deployment failed"
    exit 1
fi

# Get service URL
BACKEND_URL=$(gcloud run services describe "$BACKEND_SERVICE" --region "$REGION" --format='value(status.url)' --project "$GCP_PROJECT")
log_info "✅ Backend deployed to: $BACKEND_URL"

# --- Step 5: Deploy Dashboard to Firebase Hosting ---
log_info ""
log_info "=== Step 5: Deploying Dashboard to Firebase Hosting ==="

# Authenticate with Firebase
firebase projects:list | grep "$FIREBASE_PROJECT" >/dev/null 2>&1 || {
    log_error "Firebase project '$FIREBASE_PROJECT' not found or not authenticated"
    log_info "Run: firebase login && firebase use $FIREBASE_PROJECT"
    exit 1
}

# Deploy to Firebase Hosting
log_info "Deploying to Firebase Hosting (project: $FIREBASE_PROJECT)..."
firebase deploy \
  --project "$FIREBASE_PROJECT" \
  --only hosting

if [ $? -ne 0 ]; then
    log_error "Firebase Hosting deployment failed"
    exit 1
fi

HOSTING_URL="https://$FIREBASE_PROJECT.web.app"
log_info "✅ Dashboard deployed to Firebase Hosting: $HOSTING_URL"

# --- Step 6: (Optional) Deploy Cloud Functions ---
log_info ""
read -p "Do you want to deploy Firebase Cloud Functions? (y/N): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    log_info "=== Step 6: Deploying Cloud Functions ==="
    cd functions

    if [ ! -d "node_modules" ]; then
        log_info "Installing function dependencies..."
        npm ci
    fi

    firebase deploy --only functions --project "$FIREBASE_PROJECT"
    cd ..

    if [ $? -eq 0 ]; then
        log_info "✅ Cloud Functions deployed"
    else
        log_warn "Cloud Functions deployment failed (this may be optional)"
    fi
fi

# --- Summary ---
log_info ""
log_info "=========================================="
log_info "  Deployment Complete!"
log_info "=========================================="
log_info ""
log_info "Services deployed:"
log_info "  📦 Backend (Cloud Run):   $BACKEND_URL"
log_info "  🌐 Dashboard (Hosting):   $HOSTING_URL"
log_info ""
log_info "Next steps:"
log_info "  1. Verify Firebase Auth is configured: $BACKEND_URL/api/auth/status"
log_info "  2. Test login at: $HOSTING_URL/admin/"
log_info "  3. Update API URL in dashboard if using custom domain"
log_info ""
log_info "To view logs:"
log_info "  gcloud logging read 'resource.type=cloud_run_revision AND resource.labels.service_name=$BACKEND_SERVICE' --limit 50"
log_info ""
log_info "To rollback:"
log_info "  gcloud run services revert $BACKEND_SERVICE --region $REGION"
log_info "=========================================="
