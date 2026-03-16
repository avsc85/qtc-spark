# QTC GCP Deployment Quick Start

**Get QTC running on Google Cloud in 30 minutes** 

---

## Prerequisites (5 min)

```bash
# 1. Install Google Cloud SDK
# https://cloud.google.com/sdk/docs/install

# 2. Create GCP project
# https://console.cloud.google.com/projectcreate

# 3. Set your project ID
export GCP_PROJECT_ID="your-project-id-here"

# 4. Login to GCP
gcloud auth login
gcloud config set project $GCP_PROJECT_ID
```

---

## One-Command Setup (10 min)

From project root directory:

```bash
# Make script executable
chmod +x setup-gcp.sh

# Run automated setup
./setup-gcp.sh $GCP_PROJECT_ID
```

This will:
✅ Enable all required GCP APIs  
✅ Create service accounts with proper permissions  
✅ Setup Terraform state bucket  
✅ Configure backend storage

---

## Add Your Secrets (5 min)

Copy these commands, fill in your keys, and run:

```bash
# 1. OpenAI API Key (from https://platform.openai.com/api-keys)
echo -n "sk-YOUR-OPENAI-KEY-HERE" | gcloud secrets create openai-api-key \
  --replication-policy="user-managed" \
  --locations=us-central1 \
  --data-file=-

# 2. Stripe API Key (from https://dashboard.stripe.com/apikeys)
echo -n "sk_live_YOUR-STRIPE-KEY-HERE" | gcloud secrets create stripe-api-key \
  --replication-policy="user-managed" \
  --locations=us-central1 \
  --data-file=-

# 3. Stripe Webhook Secret (from https://dashboard.stripe.com/webhooks)
echo -n "whsec_YOUR-WEBHOOK-SECRET-HERE" | gcloud secrets create stripe-webhook-secret \
  --replication-policy="user-managed" \
  --locations=us-central1 \
  --data-file=-

# 4. Verify secrets created
gcloud secrets list
```

---

## Deploy with Terraform (8 min)

```bash
# 1. Edit Terraform configuration
cd terraform
cp terraform.tfvars.example terraform.tfvars
nano terraform.tfvars  # Edit with your values

# 2. Initialize Terraform
terraform init

# 3. Review deployment plan
terraform plan

# 4. Deploy! 🚀
terraform apply

# 5. Save URLs
terraform output
```

You'll get output like:
```
backend_url = "https://qtc-backend-xxxxx.run.app"
frontend_url = "https://qtc-frontend-xxxxx.run.app"
```

---

## Alternative: Manual Docker Deploy (2 min)

If you prefer to skip Terraform:

```bash
# 1. Make deploy script executable
chmod +x deploy.sh

# 2. Build and push images
./deploy.sh $GCP_PROJECT_ID latest
```

This will build Docker images and deploy them to Cloud Run.

---

## Test Your Deployment (2 min)

```bash
# Get service URLs
BACKEND=$(gcloud run services describe qtc-backend --region us-central1 \
  --format='value(status.url)')
FRONTEND=$(gcloud run services describe qtc-frontend --region us-central1 \
  --format='value(status.url)')

# Test backend
echo "Testing backend..."
curl $BACKEND/health

# Test frontend
echo "Testing frontend..."
curl $FRONTEND/

# Open in browser
echo "Backend: $BACKEND"
echo "Frontend: $FRONTEND"
```

---

## Monitor Your Deployment

### View Logs
```bash
# Backend logs
gcloud run services logs read qtc-backend --region us-central1 --limit 50

# Frontend logs
gcloud run services logs read qtc-frontend --region us-central1 --limit 50
```

### View Metrics
Go to: https://console.cloud.google.com/run  
Select service → Metrics tab

### Set Up Alerts
```bash
# Monitor uptime
gcloud monitoring uptime-checks create qtc-backend-uptime \
  --display-name="QTC Backend Health" \
  --resource-type=uptime-url \
  --http-check-path=/health \
  --monitored-resource="url=$BACKEND"
```

---

## Setup CI/CD (Optional)

### Option A: Cloud Build (Recommended)
```bash
# Connect GitHub repo
gcloud builds connect \
  --repository-name=qtc-app \
  --repository-owner=YOUR-GITHUB-USERNAME \
  --region=us-central1

# Trigger auto-deploys on every push to main
gcloud builds triggers create github \
  --name=qtc-deploy \
  --repo-name=qtc-app \
  --repo-owner=YOUR-GITHUB-USERNAME \
  --branch-pattern="main" \
  --build-config=cloudbuild.yaml
```

### Option B: GitHub Actions
```bash
# Add these secrets in GitHub repo settings:
# 1. GCP_PROJECT_ID = your project ID
# 2. GCP_SA_KEY = service account JSON key

# Create service account key
gcloud iam service-accounts keys create sa-key.json \
  --iam-account=qtc-backend-sa@$GCP_PROJECT_ID.iam.gserviceaccount.com

# Copy sa-key.json contents to GitHub secret

# Push to main branch to trigger workflow
git push origin main
```

---

## Cost Estimate

- **Backend (Cloud Run):** ~$18/month
- **Frontend (Cloud Run):** ~$9/month  
- **Firestore:** ~$1/month
- **Storage + Secrets:** ~$1/month
- **Total:** ~**$30/month** (free tier covers most)

See [DEPLOYMENT_GCP_GUIDE.md](DEPLOYMENT_GCP_GUIDE.md#cost-estimation) for detailed breakdown.

---

## Troubleshooting

### Services won't start
```bash
# Check logs
gcloud run services logs read qtc-backend --region us-central1 --limit 100

# Common issues:
# - Missing secrets: Add to Secret Manager
# - Bad environment: Check service env vars
# - Port wrong: Check container listening on 8000
```

### Deployment fails
```bash
# View Cloud Build logs
gcloud builds list --limit 5
gcloud builds log BUILD_ID --stream
```

### Cannot connect between services
```bash
# Check CORS settings in main.py
# Update to allow frontend URL
# Redeploy backend
```

---

## Next Steps

1. ✅ Run through quick start above
2. ✅ Test endpoints manually
3. ✅ Set up monitoring/alerts
4. ✅ Enable CI/CD pipeline
5. ✅ Configure custom domain (optional)
6. ✅ Setup backup strategy

---

## Full Documentation

For detailed setup, troubleshooting, and advanced configuration:  
📖 See [DEPLOYMENT_GCP_GUIDE.md](DEPLOYMENT_GCP_GUIDE.md)

---

**Need help?** Check logs with: `gcloud run services logs read qtc-backend --region us-central1`

**Update tracking:** Last tested March 16, 2026
