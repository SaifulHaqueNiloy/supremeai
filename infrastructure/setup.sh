#!/bin/bash
# SupremAI Infrastructure Setup Script
# Creates required GCP resources for simulator and reverse engineering features.

set -e

PROJECT_ID="${GCP_PROJECT_ID:-supremeai-459910}"
REGION="${GCP_REGION:-us-central1}"

echo "=== SupremAI Infrastructure Setup ==="
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo ""

# 1. Create Pub/Sub topic for reverse engineering jobs
echo "Creating Pub/Sub topic..."
gcloud pubsub topics create reverse-engineering-jobs --project "$PROJECT_ID" || true

# 2. Create Pub/Sub subscription for reverse-engineering service (push)
echo ""
echo "Creating push subscription..."
gcloud pubsub subscriptions create reverse-engineering-jobs-push \
  --topic=reverse-engineering-jobs \
  --project="$PROJECT_ID" \
  --push-endpoint="https://reverse-engineering-${PROJECT_ID}-uc.a.run.app/pubsub/push" \
  --push-auth-service-account="reverse-engineering@${PROJECT_ID}.iam.gserviceaccount.com" || true

# 3. Create Firestore database (if not exists)
echo ""
echo "Enabling Firestore..."
gcloud services enable firestore.googleapis.com --project "$PROJECT_ID" || true

# 4. Create Firestore database in native mode
echo "Creating Firestore database..."
gcloud firestore databases create --region="$REGION" --project "$PROJECT_ID" || true

# 5. Create service account for reverse-engineering service (optional)
echo ""
echo "Creating service account for reverse-engineering..."
gcloud iam service-accounts create reverse-engineering \
  --display-name="Reverse Engineering Service" \
  --project="$PROJECT_ID" || true

# Grant permissions
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:reverse-engineering@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/datastore.user" || true

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:reverse-engineering@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/pubsub.subscriber" || true

# 6. Build and push simulator-runtime image
echo ""
echo "Building simulator-runtime Docker image..."
cd simulator-runtime
docker build -t "gcr.io/${PROJECT_ID}/simulator-runtime:latest" .
docker push "gcr.io/${PROJECT_ID}/simulator-runtime:latest"
cd ..

# 7. Deploy reverse-engineering service to Cloud Run
echo ""
echo "Deploying reverse-engineering service to Cloud Run..."
gcloud run deploy reverse-engineering \
  --source=reverse-engineering \
  --region="$REGION" \
  --allow-unauthenticated \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=$PROJECT_ID" \
  --project="$PROJECT_ID" || true

# 8. Deploy simulator-runtime service to Cloud Run (optional - can be on-demand)
echo ""
echo "Deploying simulator-runtime service template..."
gcloud run deploy simulator-runtime \
  --image="gcr.io/${PROJECT_ID}/simulator-runtime:latest" \
  --region="$REGION" \
  --allow-unauthenticated \
  --set-min-instances=0 \
  --set-max-instances=10 \
  --project="$PROJECT_ID" || true

echo ""
echo "=== Infrastructure Setup Complete ==="
echo ""
echo "Next steps:"
echo "1. Ensure Spring Boot backend has GCP_PROJECT_ID=$PROJECT_ID in its environment."
echo "2. Deploy Spring Boot backend to Cloud Run with permissions to:"
echo "   - Pub/Sub (publisher)"
echo "   - Cloud Run Admin (to deploy simulator instances)"
echo "   - Firestore (read/write)"
echo "3. Test:"
echo "   - Generate an app via /api/generate"
echo "   - Go to Admin -> Simulator and click 'Live Preview'"
