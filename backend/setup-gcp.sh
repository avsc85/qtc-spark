#!/bin/bash

# QTC GCP Deployment Setup Script
# Automates Phase 1-3 of the deployment process
# Usage: ./setup-gcp.sh <GCP_PROJECT_ID>

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check arguments
if [ -z "$1" ]; then
    echo -e "${RED}Error: GCP Project ID required${NC}"
    echo "Usage: $0 <GCP_PROJECT_ID>"
    exit 1
fi

GCP_PROJECT_ID=$1
REGION="us-central1"
APP_NAME="qtc"

echo -e "${GREEN}=== QTC GCP Deployment Setup ===${NC}"
echo "Project ID: $GCP_PROJECT_ID"
echo "Region: $REGION"
echo ""

# Phase 1: GCP Project Setup
echo -e "${YELLOW}[Phase 1] Setting up GCP Project...${NC}"

# Set default project
gcloud config set project $GCP_PROJECT_ID
echo -e "${GREEN}✓ Project set to $GCP_PROJECT_ID${NC}"

# Enable APIs
echo "Enabling required APIs..."
gcloud services enable \
  run.googleapis.com \
  firestore.googleapis.com \
  storage-api.googleapis.com \
  cloudbuild.googleapis.com \
  secretmanager.googleapis.com \
  compute.googleapis.com \
  artifactregistry.googleapis.com 2>/dev/null

echo -e "${GREEN}✓ APIs enabled${NC}"

# Phase 2: Create Service Accounts
echo ""
echo -e "${YELLOW}[Phase 2] Creating Service Accounts...${NC}"

# Check if service accounts exist
if ! gcloud iam service-accounts describe qtc-backend-sa@$GCP_PROJECT_ID.iam.gserviceaccount.com &>/dev/null; then
    gcloud iam service-accounts create qtc-backend-sa \
      --display-name="QTC Backend Service Account"
    echo -e "${GREEN}✓ Backend service account created${NC}"
else
    echo -e "${YELLOW}✓ Backend service account already exists${NC}"
fi

if ! gcloud iam service-accounts describe qtc-frontend-sa@$GCP_PROJECT_ID.iam.gserviceaccount.com &>/dev/null; then
    gcloud iam service-accounts create qtc-frontend-sa \
      --display-name="QTC Frontend Service Account"
    echo -e "${GREEN}✓ Frontend service account created${NC}"
else
    echo -e "${YELLOW}✓ Frontend service account already exists${NC}"
fi

# Grant IAM roles
echo "Granting IAM roles..."

declare -a backends=(
  "qtc-backend-sa"
  "qtc-frontend-sa"
)

declare -a roles=(
  "roles/run.invoker"
)

for service_account in "${backends[@]}"; do
    for role in "${roles[@]}"; do
        gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
          --member="serviceAccount:${service_account}@${GCP_PROJECT_ID}.iam.gserviceaccount.com" \
          --role="$role" 2>/dev/null || true
    done
done

# Backend-specific roles
gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
  --member="serviceAccount:qtc-backend-sa@${GCP_PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/datastore.user" 2>/dev/null || true

gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
  --member="serviceAccount:qtc-backend-sa@${GCP_PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/storage.objectAdmin" 2>/dev/null || true

gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
  --member="serviceAccount:qtc-backend-sa@${GCP_PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor" 2>/dev/null || true

echo -e "${GREEN}✓ IAM roles granted${NC}"

# Phase 3: Setup Terraform
echo ""
echo -e "${YELLOW}[Phase 3] Setting up Terraform...${NC}"

# Create Terraform state bucket
STATE_BUCKET="qtc-terraform-state-$GCP_PROJECT_ID"

if gsutil ls -b "gs://$STATE_BUCKET" &>/dev/null; then
    echo -e "${YELLOW}✓ Terraform state bucket already exists${NC}"
else
    gsutil mb -p $GCP_PROJECT_ID "gs://$STATE_BUCKET"
    gsutil versioning set on "gs://$STATE_BUCKET"
    echo -e "${GREEN}✓ Terraform state bucket created${NC}"
fi

# Setup Terraform backend config
cat > terraform/backend.tf << EOF
terraform {
  backend "gcs" {
    bucket  = "$STATE_BUCKET"
    prefix  = "prod"
  }
}
EOF

echo -e "${GREEN}✓ Terraform backend configured${NC}"

# Phase 4: Add Secrets Prompt
echo ""
echo -e "${YELLOW}[Phase 4] Secret Manager Setup${NC}"
echo ""
echo "You need to add the following secrets to Secret Manager:"
echo "  1. openai-api-key (format: sk-...)"
echo "  2. stripe-api-key (format: sk_live_...)"
echo "  3. stripe-webhook-secret (format: whsec_...)"
echo ""
echo "Run these commands:"
echo ""
echo "# OpenAI API Key"
echo "echo -n 'your-openai-key' | gcloud secrets create openai-api-key \\"
echo "  --replication-policy='user-managed' --locations=$REGION --data-file=-"
echo ""
echo "# Stripe API Key"
echo "echo -n 'your-stripe-key' | gcloud secrets create stripe-api-key \\"
echo "  --replication-policy='user-managed' --locations=$REGION --data-file=-"
echo ""
echo "# Stripe Webhook Secret"
echo "echo -n 'your-webhook-secret' | gcloud secrets create stripe-webhook-secret \\"
echo "  --replication-policy='user-managed' --locations=$REGION --data-file=-"
echo ""

# Summary
echo ""
echo -e "${GREEN}=== Setup Complete ===${NC}"
echo ""
echo "Next steps:"
echo "  1. Add secrets (see above)"
echo "  2. Edit terraform/terraform.tfvars with your specific values"
echo "  3. Run: cd terraform && terraform init"
echo "  4. Run: terraform plan"
echo "  5. Run: terraform apply"
echo ""
echo "Service Accounts:"
echo "  Backend: qtc-backend-sa@${GCP_PROJECT_ID}.iam.gserviceaccount.com"
echo "  Frontend: qtc-frontend-sa@${GCP_PROJECT_ID}.iam.gserviceaccount.com"
echo ""
