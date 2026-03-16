#!/bin/bash

# QTC Deploy Script - Build and push Docker images to GCP
# Requires: gcloud, docker, and authentication with GCP

set -e

GCP_PROJECT_ID=${1:-$(gcloud config get-value project)}
REGION="us-central1"
BACKEND_IMAGE="gcr.io/$GCP_PROJECT_ID/qtc-backend"
FRONTEND_IMAGE="gcr.io/$GCP_PROJECT_ID/qtc-frontend"
TAG="${2:-latest}"

if [ -z "$GCP_PROJECT_ID" ]; then
    echo "Error: GCP_PROJECT_ID not set"
    echo "Usage: $0 [GCP_PROJECT_ID] [TAG]"
    exit 1
fi

echo "Building and deploying to GCP..."
echo "Project: $GCP_PROJECT_ID"
echo "Tag: $TAG"
echo ""

# Configure Docker authentication
echo "Configuring Docker authentication..."
gcloud auth configure-docker gcr.io

# Build backend
echo "Building backend image..."
docker build -t "$BACKEND_IMAGE:$TAG" \
             -t "$BACKEND_IMAGE:latest" \
             -f Dockerfile .

# Push backend
echo "Pushing backend image..."
docker push "$BACKEND_IMAGE:$TAG"
docker push "$BACKEND_IMAGE:latest"

# Build frontend
echo "Building frontend image..."
docker build -t "$FRONTEND_IMAGE:$TAG" \
             -t "$FRONTEND_IMAGE:latest" \
             -f Dockerfile.frontend .

# Push frontend
echo "Pushing frontend image..."
docker push "$FRONTEND_IMAGE:$TAG"
docker push "$FRONTEND_IMAGE:latest"

# Deploy backend
echo "Deploying backend to Cloud Run..."
gcloud run deploy qtc-backend \
  --image "$BACKEND_IMAGE:$TAG" \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --timeout 3600 \
  --service-account "qtc-backend-sa@$GCP_PROJECT_ID.iam.gserviceaccount.com" \
  --set-env-vars "DISABLE_AUTH=false"

# Deploy frontend
echo "Deploying frontend to Cloud Run..."
gcloud run deploy qtc-frontend \
  --image "$FRONTEND_IMAGE:$TAG" \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated \
  --memory 256Mi \
  --cpu 1 \
  --timeout 3600 \
  --service-account "qtc-frontend-sa@$GCP_PROJECT_ID.iam.gserviceaccount.com"

# Get service URLs
echo ""
echo "Services deployed successfully!"
echo ""
echo "Service URLs:"
gcloud run services describe qtc-backend --region $REGION --format='value(status.url)' | xargs echo "Backend:"
gcloud run services describe qtc-frontend --region $REGION --format='value(status.url)' | xargs echo "Frontend:"

echo ""
echo "Testing endpoints..."
BACKEND_URL=$(gcloud run services describe qtc-backend --region $REGION --format='value(status.url)')
FRONTEND_URL=$(gcloud run services describe qtc-frontend --region $REGION --format='value(status.url)')

echo "Testing $BACKEND_URL/health"
curl -f "$BACKEND_URL/health" && echo "✓ Backend healthy" || echo "✗ Backend check failed"

echo "Testing $FRONTEND_URL"
curl -f "$FRONTEND_URL/" > /dev/null && echo "✓ Frontend responsive" || echo "✗ Frontend check failed"

echo ""
echo "Deployment complete! 🎉"
