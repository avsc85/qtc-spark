# QTC CI/CD Pipeline Documentation

**Complete Guide to Automated Deployment**

---

## Overview

The QTC project includes two CI/CD options that automatically build, test, and deploy your application on every push:

1. **Google Cloud Build** (Recommended for GCP)
2. **GitHub Actions** (Recommended if using GitHub)

Choose one based on your preference. Both achieve the same result.

---

## Architecture

```
GitHub/GCP Push
    ↓
[CI/CD Trigger]
    ↓
[Tests]
    ├ Python: pytest
    ├ Frontend: npm lint + build
    ↓
[Build Docker Images]
    ├ Backend: Dockerfile
    ├ Frontend: Dockerfile.frontend
    ↓
[Push to Container Registry]
    ├ gcr.io/project/qtc-backend:sha
    ├ gcr.io/project/qtc-frontend:sha
    ↓
[Deploy to Cloud Run]
    ├ qtc-backend service
    ├ qtc-frontend service
    ↓
[Smoke Tests]
    ├ GET /health (backend)
    ├ GET / (frontend)
    ↓
[Notification]
    └ Email/Slack (success/failure)
```

---

## Option 1: Google Cloud Build

### Setup (5 minutes)

#### Step 1: Connect Your Repository

```bash
# For GitHub:
gcloud builds connect \
  --repository-name=your-repo-name \
  --repository-owner=your-github-username \
  --region=us-central1

# For GitLab/Bitbucket:
# Use Cloud Source Repositories instead
gcloud source repos create qtc-app
```

#### Step 2: Create Build Trigger

```bash
gcloud builds triggers create github \
  --name=qtc-deploy \
  --repo-name=your-repo-name \
  --repo-owner=your-github-username \
  --branch-pattern="^main$" \
  --build-config=cloudbuild.yaml \
  --region=us-central1
```

#### Step 3: Verify (Optional)

```bash
# List triggers
gcloud builds triggers list

# Manual trigger for testing
gcloud builds submit --config=cloudbuild.yaml
```

### How It Works

**On every push to `main` branch:**

1. Cloud Build reads `cloudbuild.yaml`
2. Runs build steps in sequence:
   - Build backend Docker image
   - Push to Container Registry
   - Build frontend Docker image
   - Push to Container Registry
   - Deploy backend to Cloud Run
   - Deploy frontend to Cloud Run
   - Run smoke tests
3. Notifies on success/failure

### Monitor Builds

```bash
# View recent builds
gcloud builds list --limit=10

# View specific build
gcloud builds log <BUILD_ID> --stream

# View build details
gcloud builds describe <BUILD_ID>
```

### Check Build Dashboard

https://console.cloud.google.com/cloud-build/builds

---

## Option 2: GitHub Actions

### Setup (8 minutes)

#### Step 1: Add GitHub Secrets

In your GitHub repo: **Settings → Secrets and variables → Actions**

Add these secrets:

| Secret Name | Value |
|-------------|-------|
| `GCP_PROJECT_ID` | Your GCP project ID |
| `GCP_SA_KEY` | Service account JSON key |

#### Step 2: Create Service Account Key

```bash
# Create a service account key
gcloud iam service-accounts keys create sa-key.json \
  --iam-account=qtc-backend-sa@$GCP_PROJECT_ID.iam.gserviceaccount.com

# Display the key (copy entire JSON)
cat sa-key.json

# In GitHub:
# 1. Go to Settings → Secrets and variables → Actions
# 2. Click "New repository secret"
# 3. Name: GCP_SA_KEY
# 4. Value: Paste entire sa-key.json contents
# 5. Click "Add secret"

# Delete local key file
rm sa-key.json
```

#### Step 3: Grant Extra Permissions

```bash
# Allow Cloud Run deployment
gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
  --member="serviceAccount:qtc-backend-sa@$GCP_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/run.admin"
```

#### Step 4: Test Workflow

```bash
# Actually, just push to main and it triggers automatically!
git add .
git commit -m "Deploy to GCP"
git push origin main
```

### How It Works

**On every push to `main` branch:**

1. GitHub Actions reads `.github/workflows/deploy-gcp.yml`
2. Runs jobs in parallel/sequence:
   - **test job:** Runs Python tests, lints frontend
   - **build-and-deploy job:** (only if test passed)
     - Builds Docker images
     - Pushes to GCR
     - Deploys to Cloud Run
     - Runs smoke tests
3. Shows status in PR / commit

### Monitor Workflow

**In GitHub:**

1. Go to your repo → **Actions** tab
2. Click workflow name to see details
3. Click job to expand logs
4. Click step to see full output

**Example URL:**
```
https://github.com/YOUR-USERNAME/qtc-app/actions
```

---

## How to Use (Both Options)

### Normal Development Flow

```bash
# 1. Make changes locally
nano agents/chat_agent.py

# 2. Test locally
python -m pytest

# 3. Commit and push
git add .
git commit -m "Add intent parsing to chat"
git push origin main

# 4. CD pipeline runs automatically ✨
#    - Tests run
#    - Images build
#    - Services deploy
#    - Smoke tests pass
#    - Live in production!
```

### Deployment from PR

```bash
# Create feature branch
git checkout -b feature/payment-reconciliation

# Make changes
# Commit and push
git push origin feature/payment-reconciliation

# Create PR on GitHub
# CI tests run automatically

# Merge to main when ready
# CD pipeline deploys to production
```

### Manual Deployment (If Needed)

#### Cloud Build:
```bash
gcloud builds submit \
  --config=cloudbuild.yaml \
  --region=us-central1
```

#### GitHub Actions:
```bash
# Unfortunately, can't trigger manually from command line
# Use GitHub UI: Actions → Workflow Name → Run workflow → Main branch
```

---

## Monitoring & Debugging

### View Logs

#### Cloud Build:
```bash
# Real-time logs
gcloud builds log BUILD_ID --stream

# Last 10 builds
gcloud builds list --limit=10

# Filter by status
gcloud builds list --filter="status=FAILURE"
```

#### GitHub Actions:
```bash
# All output visible in GitHub UI
# Repo → Actions → Workflow Run → Job Details
```

### Common Issues & Solutions

#### Build Fails - "Docker image not found"
**Solution:** Verify Docker images built successfully
```bash
# Check gcr.io registry
gcloud container images list

# Check if images pushed
gcloud container images list-tags gcr.io/$PROJECT_ID/qtc-backend
```

#### Deployment Fails - "Service account permission denied"
**Solution:** Verify service account has correct roles
```bash
gcloud projects get-iam-policy $GCP_PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:qtc-backend-sa*"
```

#### Smoke Tests Fail - "Health check timeout"
**Solution:** Check if service is actually running
```bash
gcloud run describe qtc-backend --region us-central1

# Check recent logs
gcloud run services logs read qtc-backend \
  --region us-central1 \
  --limit=50
```

---

## Advanced Configuration

### Skip Deployment (Only Test)

Add label to commit message:
```
git commit -m "Fix: lint error [skip-deploy]"
```

Then modify workflow to check for this label.

### Deploy to Multiple Regions

Edit `cloudbuild.yaml` to deploy to multiple regions:

```yaml
  - name: 'gcr.io/cloud-builders/run'
    args: ['deploy', 'qtc-backend', '--image', '$BACKEND_IMAGE', '--region', 'us-central1']
  
  - name: 'gcr.io/cloud-builders/run'
    args: ['deploy', 'qtc-backend', '--image', '$BACKEND_IMAGE', '--region', 'europe-west1']
```

### Scheduled Deployments

For GitHub Actions, add schedule:

```yaml
on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM UTC
```

### Notifications

#### Cloud Build → Slack:
```bash
gcloud builds update-github-iam-bindings
# Then use Cloud Build → Webhooks → Slack
```

#### GitHub Actions → Slack:
Use "Slack Notify" action in workflow

---

## Security Best Practices

### 1. Service Account Permissions
```bash
# Use least-privilege principle
# Backend needs:
- Run.admin (deploy)
- Datastore.user (Firestore)
- Storage.objectAdmin (GCS)
- Secretmanager.secretAccessor (Secrets)

# Frontend needs:
- Run.admin (deploy)
```

### 2. Image Security
```bash
# Scan images for vulnerabilities
gcloud container images scan IMAGE_URL

# Use image signing
gcloud beta container binauthz attestations create ...
```

### 3. Secret Rotation
```bash
# Rotate API keys monthly
# Update in Secret Manager first
gcloud secrets versions add openai-api-key --data-file=-

# Services auto-pick up new versions
```

### 4. Audit Resources
```bash
# View all deployments and who made them
gcloud run deployments list --region us-central1 --filter="serviceRuntime:..."
```

---

## Rollback Instructions

### Manual Rollback

```bash
# List previous revisions
gcloud run revisions list \
  --service=qtc-backend \
  --region=us-central1

# Rollback to specific revision
gcloud run services update-traffic qtc-backend \
  --revisions=REVISION-NAME=100 \
  --region=us-central1

# Or use stable tag
gcloud run deploy qtc-backend \
  --image=gcr.io/$PROJECT_ID/qtc-backend:previous-known-good \
  --region=us-central1
```

### Automated Rollback (Cloud Run)

Set traffic rules to automatically serve previous revision if health checks fail:

```bash
gcloud run deploy qtc-backend \
  --image=$NEW_IMAGE \
  --region=us-central1 \
  --no-traffic  # Don't route traffic initially

# Test new revision
curl https://qtc-backend-REVISION.run.app/health

# If good, route traffic
gcloud run services update-traffic qtc-backend \
  --revisions=REVISION-NAME=100 \
  --region=us-central1
```

---

## Performance Optimization

### Cache Docker Layers

In `cloudbuild.yaml`:
```yaml
- name: 'gcr.io/cloud-builders/docker'
  args: 
    - 'build'
    - '-t'
    - '$BACKEND_IMAGE'
    - '--cache-from'
    - '$BACKEND_IMAGE:latest'
    - '-f'
    - 'Dockerfile'
    - '.'
```

### Parallel Jobs

GitHub Actions runs jobs in parallel:
```yaml
strategy:
  matrix:
    include:
      - service: backend
        dockerfile: Dockerfile
```

### Stage Deployments

Use traffic splitting for canary deployments:

```bash
# Deploy new version with 10% traffic
gcloud run deploy qtc-backend \
  --image=$NEW_IMAGE \
  --region=us-central1

# Then update traffic gradually
gcloud run services update-traffic qtc-backend \
  --to-revisions LATEST=10,SECOND-LATEST=90
```

---

## Cost Optimization

| Item | Cost | Notes |
|------|------|-------|
| Cloud Build | $0.003/min | Free: 120 min/day |
| GitHub Actions | $0.008/min | Free: 2000 min/month |
| Container Registry | $0.10/GB/month | ~$2-5/month typical |

**Savings Tips:**
- Use `--no-cache-from` to save space
- Delete old images: `gcloud container images delete IMAGE_URL`
- Batch deployments (deploy once, not multiple times)

---

## Troubleshooting Checklist

- [ ] Service account has correct roles
- [ ] Secrets added to Secret Manager
- [ ] Dockerfile builds locally
- [ ] Environment variables correct
- [ ] Firestore database exists
- [ ] GCS bucket accessible
- [ ] Health endpoint responds
- [ ] Logs show no errors

See full troubleshooting in [DEPLOYMENT_GCP_GUIDE.md](DEPLOYMENT_GCP_GUIDE.md#troubleshooting)

---

**Last Updated:** March 16, 2026  
**Tested With:** Cloud Build + GitHub Actions
