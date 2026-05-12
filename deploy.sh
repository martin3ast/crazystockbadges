#!/bin/bash
set -e

# Configuration
PROJECT_ID="crazystockbadges"
ORG_ID="115469591228"   # hyperplane2-org
REGION="europe-west1"
SERVICE_NAME="crazystockbadges"
REPO_NAME="crazystockbadges"
IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${SERVICE_NAME}"

echo "Deploying to project: ${PROJECT_ID} (org: hyperplane2-org)"
echo "Region: ${REGION}"
echo "Image: ${IMAGE}"

# Sanity check: confirm the project still lives in the expected org
ACTUAL_PARENT=$(gcloud projects describe "${PROJECT_ID}" --format='value(parent.id)' 2>/dev/null || echo "")
if [ "${ACTUAL_PARENT}" != "${ORG_ID}" ]; then
  echo "ERROR: Project ${PROJECT_ID} is not in org ${ORG_ID}. Found parent: '${ACTUAL_PARENT}'"
  echo "Move it with: gcloud beta projects move ${PROJECT_ID} --organization=${ORG_ID}"
  exit 1
fi

# Pin gcloud to the expected project so a stray `gcloud config set project` can't redirect this deploy.
gcloud config set project "${PROJECT_ID}" --quiet

# Enable required APIs (idempotent)
echo "Enabling required APIs..."
gcloud services enable run.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com

# Ensure the Artifact Registry repo exists (idempotent)
if ! gcloud artifacts repositories describe "${REPO_NAME}" --location="${REGION}" >/dev/null 2>&1; then
  echo "Creating Artifact Registry repository ${REPO_NAME} in ${REGION}..."
  gcloud artifacts repositories create "${REPO_NAME}" \
    --repository-format=docker \
    --location="${REGION}" \
    --description="Crazy Stock Badges container images"
fi

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
