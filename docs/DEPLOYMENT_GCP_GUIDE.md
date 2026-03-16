# QTC GCP Deployment & CI/CD Guide

**Last Updated:** March 16, 2026  
**Status:** Complete deployment system ready for production

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Architecture Overview](#architecture-overview)
3. [Step-by-Step Setup](#step-by-step-setup)
4. [CI/CD Pipeline Options](#cicd-pipeline-options)
5. [Deployment Instructions](#deployment-instructions)
6. [Monitoring & Logs](#monitoring--logs)
7. [Troubleshooting](#troubleshooting)
8. [Cost Estimation](#cost-estimation)

---

## Prerequisites

### Required Software
- Google Cloud SDK (`gcloud` CLI)
- Terraform >= 1.0
- Docker (for local testing)
- Git (for CI/CD integration)
- Node.js 18+ (for frontend development)
- Python 3.11+ (for backend development)

### GCP Account Setup
1. Create a GCP project
2. Enable billing
3. Have appropriate IAM roles:
   - Editor (or custom: Cloud Run Admin, Firestore Admin, Storage Admin, Secret Manager Admin)

### API Keys / Secrets Needed
- OpenAI API key
- Stripe API key (production)
- Stripe webhook secret (production)
- Firebase project config
- Gmail SMTP credentials (optional, for email)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     End Users                                │
└────────────┬──────────────────────────────────┬──────────────┘
             │                                  │
             │ HTTPS                            │ HTTPS
             │                                  │
    ┌────────▼────────┐              ┌─────────▼─────────┐
    │   Frontend      │              │  Public Signing   │
    │  Cloud Run 🖧   │              │  (Cloud Run)      │
    │ (React + Vite)  │              │  (No Auth)        │
    └────────┬────────┘              └─────────┬─────────┘
             │                                  │
             │────────────────┬─────────────────┤
                              │
                    ┌─────────▼─────────┐
                    │    Backend        │
                    │   Cloud Run 🖧     │
                    │   (FastAPI)       │
                    └────────┬──────────┘
                             │
        ┌────────────────────┼─────────────────────┐
        │                    │                      │
    ┌───▼────┐          ┌───▼───┐          ┌──────▼─────┐
    │Firestore│         │  GCS   │          │  Secrets   │
    │ Database│         │ Bucket │          │  Manager   │
    │   📊    │         │  📦    │          │   🔐       │
    └─────────┘         └────────┘          └────────────┘
        │                     │
        │      API Calls      │
        │   (Google SDK)      │
        │                     │
  ┌─────▼──────────────────────▼──────┐
  │  Firebase Auth (Tokens)            │
  │  OpenAI (Chat, Contracts)          │
  │  Stripe (Payments)                 │
  │  Gmail (Email)                     │
  └────────────────────────────────────┘
```

### Key Components

| Component | Service | Purpose |
|-----------|---------|---------|
| **Frontend** | Cloud Run | React app served with nginx |
| **Backend** | Cloud Run | FastAPI application |
| **Database** | Firestore | NoSQL for leads, contracts, invoices |
| **Storage** | Cloud Storage (GCS) | Templates, signed PDFs, logos |
| **Secrets** | Secret Manager | API keys, credentials |
| **CI/CD** | Cloud Build OR GitHub Actions | Automated build & deploy |
| **Terraform** | Infrastructure as Code | Provision & manage resources |

---

## Step-by-Step Setup

### Phase 1: GCP Project Setup (15 minutes)

#### Step 1.1: Create GCP Project
```bash
# Set project ID
export GCP_PROJECT_ID="qtc-prod-12345"  # Change to your project

# Create project
gcloud projects create $GCP_PROJECT_ID

# Set as default
gcloud config set project $GCP_PROJECT_ID

# Enable billing (do this in GCP Console)
# Go to: https://console.cloud.google.com/billing
```

#### Step 1.2: Enable Required APIs
```bash
gcloud services enable \
  run.googleapis.com \
  firestore.googleapis.com \
  storage-api.googleapis.com \
  cloudbuild.googleapis.com \
  secretmanager.googleapis.com \
  compute.googleapis.com \
  artifactregistry.googleapis.com
```

#### Step 1.3: Create Service Accounts
```bash
# Backend service account
gcloud iam service-accounts create qtc-backend-sa \
  --display-name="QTC Backend Service Account"

# Frontend service account
gcloud iam service-accounts create qtc-frontend-sa \
  --display-name="QTC Frontend Service Account"

# Grant Cloud Run permissions
gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
  --member="serviceAccount:qtc-backend-sa@$GCP_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/run.invoker"

gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
  --member="serviceAccount:qtc-frontend-sa@$GCP_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/run.invoker"

# Grant Firestore permissions to backend
gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
  --member="serviceAccount:qtc-backend-sa@$GCP_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/datastore.user"

# Grant Storage permissions to backend
gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
  --member="serviceAccount:qtc-backend-sa@$GCP_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/storage.objectAdmin"

# Grant Secret Manager permissions
gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
  --member="serviceAccount:qtc-backend-sa@$GCP_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

---

### Phase 2: Add Secrets to Secret Manager (10 minutes)

```bash
# OpenAI API Key
echo -n "sk-your-openai-key-here" | gcloud secrets create openai-api-key \
  --replication-policy="user-managed" \
  --locations=us-central1 \
  --data-file=-

# Stripe API Key (Live)
echo -n "sk_live_your-stripe-key-here" | gcloud secrets create stripe-api-key \
  --replication-policy="user-managed" \
  --locations=us-central1 \
  --data-file=-

# Stripe Webhook Secret
echo -n "whsec_your-webhook-secret-here" | gcloud secrets create stripe-webhook-secret \
  --replication-policy="user-managed" \
  --locations=us-central1 \
  --data-file=-

# Verify secrets created
gcloud secrets list
```

---

### Phase 3: Setup Terraform (10 minutes)

#### Step 3.1: Initialize Terraform State Bucket
```bash
# Create GCS bucket for Terraform state
gsutil mb gs://qtc-terraform-state-$GCP_PROJECT_ID

# Enable versioning
gsutil versioning set on gs://qtc-terraform-state-$GCP_PROJECT_ID
```

#### Step 3.2: Configure Terraform Variables
```bash
cd terraform

# Copy and edit the variables file
cp terraform.tfvars.example terraform.tfvars

# Edit terraform.tfvars with your values:
# - project_id
# - backend/frontend service account emails
# - API keys in separate secret file or environment vars
```

#### Step 3.3: Add Sensitive Variables (Secure Method)
```bash
# Create a separate secrets file (never commit this!)
cat > terraform/terraform.tfvars.secret << 'EOF'
openai_api_key        = "sk-xxxxxxxxxxxx"
stripe_api_key        = "sk_live_xxxxxxxxxxxx"
stripe_webhook_secret = "whsec_xxxxxxxxxxxx"
EOF

# Set permissions
chmod 600 terraform/terraform.tfvars.secret

# Add to .gitignore
echo "terraform/terraform.tfvars.secret" >> ../.gitignore
```

#### Step 3.4: Initialize and Plan
```bash
# Initialize Terraform
terraform init \
  -backend-config="bucket=qtc-terraform-state-$GCP_PROJECT_ID" \
  -backend-config="prefix=prod"

# Validate configuration
terraform validate

# Create plan
terraform plan -var-file=terraform.tfvars -out=tfplan
```

---

### Phase 4: Deploy with Terraform (5 minutes)

```bash
# Review the plan output, then apply
terraform apply tfplan

# Save outputs
terraform output -json > outputs.json

# Extract service URLs
BACKEND_URL=$(terraform output -raw backend_url)
FRONTEND_URL=$(terraform output -raw frontend_url)

echo "Backend URL: $BACKEND_URL"
echo "Frontend URL: $FRONTEND_URL"
```

---

## CI/CD Pipeline Options

### Option A: Google Cloud Build (Recommended for GCP)

**Advantages:**
- Native GCP integration
- Free tier includes 120 build-minutes/day
- Automatic on push to main branch
- No external secrets needed

**Setup:**
```bash
# 1. Push code to GitHub or Cloud Source Repositories
git push origin main

# 2. Connect repository to Cloud Build
gcloud builds connect --repository-name=qtc-app \
  --repository-owner=your-github-username \
  --region=us-central1

# 3. Create Cloud Build trigger
gcloud builds triggers create github \
  --name=qtc-deploy \
  --repo-name=qtc-app \
  --repo-owner=your-github-username \
  --branch-pattern="main" \
  --build-config=cloudbuild.yaml

# 4. Verify
gcloud builds list
```

### Option B: GitHub Actions (Recommended if using GitHub)

**Advantages:**
- Works with GitHub natively
- Free for public repos, 2000 minutes/month for private
- Full control over workflow
- Test before deploy

**Setup:**
```bash
# 1. Add GitHub secrets
# Go to: Settings → Secrets and variables → Actions

# Add these secrets:
# GCP_PROJECT_ID
# GCP_SA_KEY (JSON service account key)

# 2. Service Account Key
gcloud iam service-accounts keys create sa-key.json \
  --iam-account=qtc-backend-sa@$GCP_PROJECT_ID.iam.gserviceaccount.com

# Copy contents of sa-key.json to GitHub secret GCP_SA_KEY

# 3. Push to trigger workflow
git push origin main

# 4. Monitor at: GitHub → Actions
```

---

## Deployment Instructions

### Manual Deployment (Using Cloud Build)

#### Build & Deploy Manually
```bash
gcloud builds submit --config=cloudbuild.yaml
```

#### Deploy Specific Image
```bash
# Deploy backend
gcloud run deploy qtc-backend \
  --image gcr.io/$GCP_PROJECT_ID/qtc-backend:latest \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --timeout 3600 \
  --service-account qtc-backend-sa@$GCP_PROJECT_ID.iam.gserviceaccount.com

# Deploy frontend
gcloud run deploy qtc-frontend \
  --image gcr.io/$GCP_PROJECT_ID/qtc-frontend:latest \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --memory 256Mi \
  --cpu 1 \
  --timeout 3600 \
  --service-account qtc-frontend-sa@$GCP_PROJECT_ID.iam.gserviceaccount.com
```

### Automated Rollback
```bash
# List revisions
gcloud run revisions list --service qtc-backend --region us-central1

# Rollback to previous version
gcloud run deploy qtc-backend \
  --image gcr.io/$GCP_PROJECT_ID/qtc-backend:previous-sha \
  --region us-central1
```

---

## Monitoring & Logs

### View Logs

#### Backend Logs
```bash
gcloud run services logs read qtc-backend --region us-central1 --limit 100
```

#### Frontend Logs
```bash
gcloud run services logs read qtc-frontend --region us-central1 --limit 100
```

#### Firestore Logs
```bash
gcloud logging read "resource.type=cloud_firestore_database" --limit 50
```

### Real-Time Monitoring (Cloud Console)
```
https://console.cloud.google.com/run
- Select service (qtc-backend or qtc-frontend)
- View Metrics tab for CPU, memory, request counts
- View Logs tab for detailed entries
```

### Set Up Alerts
```bash
# Create uptime check for backend
gcloud monitoring uptime-checks create backend-check \
  --display-name="QTC Backend Health" \
  --resource-type=uptime-url \
  --http-check-path=/health \
  --monitored-resource="url=https://qtc-backend-XXXXX.run.app"
```

---

## Troubleshooting

### Service Won't Start

**Check logs:**
```bash
gcloud run services logs read qtc-backend \
  --region us-central1 \
  --limit 50 \
  --level ERROR
```

**Common issues:**
- Missing environment variables → Add to Cloud Run service
- Firestore not accessible → Check service account permissions
- API key invalid → Verify in Secret Manager
- Port not 8000 → Check Dockerfile

### Deployment Failures

**Cloud Build logs:**
```bash
gcloud builds log <BUILD_ID> --stream
```

**View failed builds:**
```bash
gcloud builds list --filter="status=FAILURE" --limit 5
```

### Cannot Connect to Backend from Frontend

**Check CORS:**
Edit `main.py` to ensure CORS allows frontend origin:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://qtc-frontend-XXXXX.run.app"],
    ...
)
```

Deploy again to apply changes.

---

## Cost Estimation

### Monthly Costs Estimate (US Central 1)

| Service | Usage | Estimated Cost |
|---------|-------|-----------------|
| **Cloud Run (Backend)** | 1M requests, 512MB, 1 vCPU | $18.29 |
| **Cloud Run (Frontend)** | 500K requests, 256MB, 1 vCPU | $9.14 |
| **Firestore** | <1GB storage, <100K reads/writes | $1.06 |
| **Cloud Storage** | <10GB | $0.23 |
| **Secret Manager** | 3 secrets | $0.60 |
| **Cloud Build** | 300+ minutes (paid) | ~$1.20/100 min = $3.60 |
| **Total** | — | **~$33/month** |

**Notes:**
- Cloud Run: $0.00002400 per vCPU-second, $0.0000050 per GB-second
- Free tier: 2M requests/month per service = often covers all usage
- Scaling up 10x would be ~$300/month

---

## Next Steps

1. ✅ Complete Phase 1-4 setup above
2. ✅ Run smoke tests from Cloud Console
3. ✅ Point DNS to Cloud Run services (optional, use run.app domain)
4. ✅ Set up monitoring alerts
5. ✅ Document runbooks for incident response
6. ✅ Plan backup strategy for Firestore

---

## Files Included

- `Dockerfile` — Backend container
- `Dockerfile.frontend` — Frontend container
- `.dockerignore` — Exclude files from builds
- `cloudbuild.yaml` — GCP Cloud Build pipeline
- `.github/workflows/deploy-gcp.yml` — GitHub Actions pipeline
- `terraform/main.tf` — Infrastructure as code
- `terraform/variables.tf` — Variable definitions
- `terraform/terraform.tfvars.example` — Template for configuration

---

**Support:** For issues, check logs or contact your GCP administrator.

**Last Updated:** March 16, 2026
