#!/bin/bash
set -e

# Configuration
PROJECT_ID=$(gcloud config get-value project)
REGION="europe-west1"
SERVICE_NAME="crazystockbadges"
IMAGE="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "Deploying to project: ${PROJECT_ID}"
echo "Region: ${REGION}"
echo "Image: ${IMAGE}"

# Enable required APIs
echo "Enabling required APIs..."
gcloud services enable run.googleapis.com containerregistry.googleapis.com

# Build and push the image
echo "Building and pushing Docker image..."
gcloud builds submit --tag "${IMAGE}" .

# Deploy to Cloud Run
echo "Deploying to Cloud Run..."
gcloud run deploy "${SERVICE_NAME}" \
  --image "${IMAGE}" \
  --platform managed \
  --region "${REGION}" \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 1 \
  --timeout 600 \
  --set-env-vars "$(grep -E '^OPENROUTER_API_KEY=' .env)" \
  --set-env-vars "LOG_LEVEL=INFO"

# Get the service URL
URL=$(gcloud run services describe "${SERVICE_NAME}" --region "${REGION}" --format 'value(status.url)')
echo ""
echo "Deployed successfully!"
echo "Service URL: ${URL}"
echo ""
echo "Remember to update ALLOWED_ORIGINS if needed:"
echo "  gcloud run services update ${SERVICE_NAME} --region ${REGION} --set-env-vars ALLOWED_ORIGINS=${URL}"
