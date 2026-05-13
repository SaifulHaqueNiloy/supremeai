#!/bin/bash
# SupremeAI All-in-One Deployment Script
# Deploys backend, Python services, and sets up infrastructure.

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
PROJECT_ID="${GCP_PROJECT_ID:-supremeai-459910}"
REGION="${GCP_REGION:-us-central1}"
BACKEND_IMAGE="gcr.io/${PROJECT_ID}/supremeai-backend:latest"
REVERSE_ENG_IMAGE="gcr.io/${PROJECT_ID}/reverse-engineering:latest"
SIMULATOR_IMAGE="gcr.io/${PROJECT_ID}/simulator-runtime:latest"

# --- Checks ---
command -v gcloud >/dev/null 2>&1 || { log_error "gcloud CLI not found. Install from: https://cloud.google.com/sdk/docs/install"; exit 1; }
command -v docker >/dev/null 2>&1 || { log_error "Docker not found. Install Docker Desktop or equivalent."; exit 1; }

log_info "Starting SupremeAI deployment..."
log_info "Project: $PROJECT_ID, Region: $REGION"

# 1. Build backend JAR
log_info "Building Spring Boot backend..."
./gradlew clean build -x test

# 2. Build backend Docker image
log_info "Building backend Docker image..."
docker build -t "$BACKEND_IMAGE" .

# 3. Build reverse-engineering image
log_info "Building reverse-engineering service image..."
cd reverse-engineering
docker build -t "$REVERSE_ENG_IMAGE" .
cd ..

# 4. Build simulator-runtime image
log_info "Building simulator-runtime image..."
cd simulator-runtime
docker build -t "$SIMULATOR_IMAGE" .
cd ..

# 5. Push images to GCR
log_info "Pushing images to Google Container Registry..."
docker push "$BACKEND_IMAGE"
docker push "$REVERSE_ENG_IMAGE"
docker push "$SIMULATOR_IMAGE"

# 6. Create / update infrastructure (if script exists)
if [ -f "infrastructure/setup.sh" ]; then
    log_info "Running infrastructure setup..."
    bash infrastructure/setup.sh
fi

# 7. Deploy to Cloud Run
log_info "Deploying services to Cloud Run..."

# Backend
gcloud run deploy supremeai-backend \
  --image "$BACKEND_IMAGE" \
  --region "$REGION" \
  --allow-unauthenticated \
  --set-env-vars="GCP_PROJECT_ID=$PROJECT_ID" \
  --cpu 2 --memory 2Gi \
  --project "$PROJECT_ID" || log_warn "Backend deployment may have failed (check if already exists)"

# Reverse Engineering service
gcloud run deploy reverse-engineering \
  --image "$REVERSE_ENG_IMAGE" \
  --region "$REGION" \
  --allow-unauthenticated \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=$PROJECT_ID" \
  --service-account="reverse-engineering@${PROJECT_ID}.iam.gserviceaccount.com" \
  --project "$PROJECT_ID" || log_warn "Reverse engineering deployment may have failed"

# Simulator runtime (min instances 0 to save cost)
gcloud run deploy simulator-runtime \
  --image "$SIMULATOR_IMAGE" \
  --region "$REGION" \
  --allow-unauthenticated \
  --set-min-instances=0 \
  --set-max-instances=10 \
  --project "$PROJECT_ID" || log_warn "Simulator runtime deployment may have failed"

# 8. Create Pub/Sub push subscription (idempotent)
log_info "Configuring Pub/Sub push subscription..."
REVERSE_ENG_URL=$(gcloud run services describe reverse-engineering --region "$REGION" --format='value(status.url)' --project "$PROJECT_ID")
if [ -n "$REVERSE_ENG_URL" ]; then
    gcloud pubsub subscriptions create reverse-engineering-jobs-push \
      --topic=reverse-engineering-jobs \
      --push-endpoint="${REVERSE_ENG_URL}/pubsub/push" \
      --push-auth-service-account="reverse-engineering@${PROJECT_ID}.iam.gserviceaccount.com" \
      --project "$PROJECT_ID" || log_warn "Subscription may already exist"
else
    log_warn "Could not determine reverse-engineering service URL; skip creating subscription"
fi

log_info "Deployment complete!"
log_info "Next: Verify services are running:"
log_info "  gcloud run services list --region $REGION"
log_info ""
log_info "Test URLs:"
log_info "  Backend: https://supremeai-backend-xxxx.a.run.app/actuator/health"
log_info "  Reverse Eng: ${REVERSE_ENG_URL}/health"
log_info "  Simulator Runtime: https://simulator-runtime-xxxx.a.run.app/health"
log_info ""
log_info "Don't forget to deploy dashboard (Firebase Hosting or static):"
log_info "  cd dashboard && npm run build && firebase deploy"
