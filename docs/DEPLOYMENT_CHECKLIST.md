# QTC GCP Deployment Checklist

**Date: March 16, 2026**

Complete this checklist to ensure your deployment is ready for production testing.

---

## ✅ Phase 1: Local Setup

- [ ] Docker installed: `docker --version`
- [ ] Google Cloud SDK installed: `gcloud --version`
- [ ] Terraform installed: `terraform --version`
- [ ] Git configured: `git config --global user.name "Your Name"`
- [ ] Repository cloned and up to date
- [ ] Python requirements reviewed: `cat requirements.txt`
- [ ] Frontend dependencies checked: `cd qtc-spark && npm list`

---

## ✅ Phase 2: GCP Project Setup

- [ ] GCP project created
- [ ] Billing enabled on project
- [ ] Project ID noted: `_________________`
- [ ] Set as default: `gcloud config set project [ID]`
- [ ] Required APIs enabled:
  - [ ] Cloud Run
  - [ ] Firestore
  - [ ] Cloud Storage
  - [ ] Cloud Build
  - [ ] Secret Manager
  - [ ] Compute Engine
  - [ ] Artifact Registry

---

## ✅ Phase 3: Service Accounts & IAM

- [ ] Backend service account created: `qtc-backend-sa`
- [ ] Frontend service account created: `qtc-frontend-sa`
- [ ] Service account emails noted:
  - Backend: `_________________________________`
  - Frontend: `_________________________________`
- [ ] IAM roles granted:
  - [ ] Backend: run.invoker, datastore.user, storage.objectAdmin, secretmanager.secretAccessor
  - [ ] Frontend: run.invoker
- [ ] IAM bindings verified: `gcloud projects get-iam-policy [PROJECT_ID]`

---

## ✅ Phase 4: Secrets Management

- [ ] Secrets created (gcloud secrets list):
  - [ ] `openai-api-key`
  - [ ] `stripe-api-key`
  - [ ] `stripe-webhook-secret`
- [ ] Secret values verified accessible:
  - [ ] Backend SA can read all 3 secrets
  - [ ] Frontend SA doesn't need secrets

---

## ✅ Phase 5: Terraform Setup

- [ ] Terraform state bucket created: `qtc-terraform-state-[PROJECT_ID]`
- [ ] Versioning enabled on state bucket
- [ ] Terraform files in place:
  - [ ] `terraform/main.tf`
  - [ ] `terraform/variables.tf`
  - [ ] `terraform/backend.tf` (auto-generated)
  - [ ] `terraform/terraform.tfvars` (local, not committed)
- [ ] `terraform.tfvars` configured with:
  - [ ] `project_id = "your-project-id"`
  - [ ] Backend SA email
  - [ ] Frontend SA email
  - [ ] Correct region (us-central1)
- [ ] Terraform initialized: `terraform init`
- [ ] Terraform validated: `terraform validate`
- [ ] Plan reviewed: `terraform plan`

---

## ✅ Phase 6: Docker Setup

- [ ] Docker images build locally:
  - [ ] `docker build -t qtc-backend:latest -f Dockerfile .`
  - [ ] `docker build -t qtc-frontend:latest -f Dockerfile.frontend .`
- [ ] Images tested locally:
  - [ ] Backend container starts: `docker run -p 8000:8000 qtc-backend:latest`
  - [ ] Backend health endpoint responds: `curl http://localhost:8000/health`
  - [ ] Frontend container starts: `docker run -p 8080:8080 qtc-frontend:latest`
  - [ ] Frontend responds: `curl http://localhost:8080`
- [ ] Dockerfiles optimized (multi-stage)
- [ ] `.dockerignore` excludes unnecessary files
- [ ] Container sizes reasonable:
  - [ ] Backend: < 200MB
  - [ ] Frontend: < 100MB

---

## ✅ Phase 7: Container Registry Setup

- [ ] Docker SDK authenticated: `gcloud auth configure-docker gcr.io`
- [ ] Container Registry accessible: `gcloud container images list`
- [ ] Images can be pushed:
  - [ ] `docker tag qtc-backend:latest gcr.io/[PROJECT_ID]/qtc-backend:latest`
  - [ ] `docker push gcr.io/[PROJECT_ID]/qtc-backend:latest`

---

## ✅ Phase 8: CI/CD Pipeline (Choose One)

### Option A: Cloud Build
- [ ] Build trigger created in Cloud Build
- [ ] `cloudbuild.yaml` present and valid
- [ ] Trigger configured to run on main branch push
- [ ] First test build successful: `gcloud builds submit --config=cloudbuild.yaml`
- [ ] Build logs viewable: `gcloud builds list`

### Option B: GitHub Actions
- [ ] GitHub repository connected to GCP (for GitHub Actions to access)
- [ ] `.github/workflows/deploy-gcp.yml` present
- [ ] GitHub repository secrets added:
  - [ ] `GCP_PROJECT_ID`
  - [ ] `GCP_SA_KEY` (service account JSON key)
- [ ] Service account key generated and saved securely
- [ ] First workflow run successful on test branch
- [ ] Workflow logs visible in GitHub Actions tab

---

## ✅ Phase 9: Deployment

- [ ] Infrastructure deployed via Terraform:
  ```bash
  terraform apply
  ```
  - [ ] Terraform apply completed successfully
  - [ ] Resources created in GCP Console
  - [ ] Output saved: `terraform output -json > outputs.json`

OR

- [ ] Infrastructure deployed via manual deploy script:
  ```bash
  ./deploy.sh $GCP_PROJECT_ID latest
  ```
  - [ ] Backend image pushed to GCR
  - [ ] Frontend image pushed to GCR
  - [ ] Backend deployed to Cloud Run
  - [ ] Frontend deployed to Cloud Run
  - [ ] Both services available in Cloud Run console

---

## ✅ Phase 10: Verification & Testing

- [ ] backend service details visible: `gcloud run describe qtc-backend --region us-central1`
- [ ] Frontend service details visible: `gcloud run describe qtc-frontend --region us-central1`
- [ ] Service URLs obtained:
  - Backend: `_________________________________________`
  - Frontend: `_________________________________________`

### Backend Tests
- [ ] Health endpoint responds: `curl [BACKEND_URL]/health`
- [ ] Returns: `{"status":"ok","service":"quote-to-cash"}`
- [ ] API endpoints accessible (no auth required locally)
- [ ] Firestore connection verified (no errors in logs)
- [ ] Secrets accessible (no 403 errors in logs)

### Frontend Tests
- [ ] Homepage loads: `curl [FRONTEND_URL]`
- [ ] Returns HTML (not 404 or 500)
- [ ] API calls to backend working (check browser console for CORS errors)
- [ ] Login flow works (if auth enabled)
- [ ] Main pages load: /leads, /contracts, /invoices, /chat

### Integration Tests
- [ ] Can capture a lead via API
- [ ] Can generate a contract
- [ ] Can create an invoice
- [ ] Stripe webhook endpoint accessible
- [ ] Chat streaming works with SSE

---

## ✅ Phase 11: Monitoring & Logging

- [ ] Cloud Logging accessible: https://console.cloud.google.com/logs
- [ ] Backend logs visible: `gcloud run services logs read qtc-backend --limit 50`
- [ ] Frontend logs visible: `gcloud run services logs read qtc-frontend --limit 50`
- [ ] No ERROR level logs from startup
- [ ] Health checks passing (showing green in Cloud Run console)
- [ ] Request counts visible in metrics: https://console.cloud.google.com/run

---

## ✅ Phase 12: Security Verification

- [ ] Service accounts use least-privilege roles (not Editor)
- [ ] Secrets not in code or environment files
- [ ] Secrets never logged (check logs for "sk-" or "sk_live_")
- [ ] HTTPS enforced (Cloud Run default)
- [ ] CORS configured appropriately
- [ ] Database rules restrict to authenticated users
- [ ] Storage bucket permissions set correctly

---

## ✅ Phase 13: Cost Setup

- [ ] Billing account linked to project
- [ ] Budget alert set (recommended: $100/month):
  ```bash
  gcloud billing budgets create \
    --billing-account=[ACCOUNT_ID] \
    --display-name="QTC Budget" \
    --budget-amount=100 \
    --threshold-rule=percent=50 \
    --threshold-rule=percent=100
  ```
- [ ] Enable cost anomaly detection
- [ ] Export costs to BigQuery (optional)

---

## ✅ Phase 14: Backup & Disaster Recovery

- [ ] Firestore backup policy created
- [ ] GCS buckets protected (versioning, multi-region)
- [ ] Terraform state backed up (versioning enabled)
- [ ] Runbook created for incident response
- [ ] Recovery procedures documented

---

## ✅ Phase 15: CI/CD Testing

- [ ] Make a test code change
- [ ] Commit and push to main branch
- [ ] CI/CD pipeline triggers automatically
- [ ] Tests run successfully
- [ ] Docker images build successfully
- [ ] Deployment to Cloud Run succeeds
- [ ] Services still responding after automated deploy
- [ ] No downtime during deployment

---

## ✅ Phase 16: Documentation

- [ ] All deployment docs reviewed:
  - [ ] `DEPLOYMENT_QUICKSTART.md`
  - [ ] `DEPLOYMENT_GCP_GUIDE.md`
  - [ ] `CICD_GUIDE.md`
  - [ ] `DEPLOYMENT_SYSTEM_SUMMARY.md`
- [ ] Team trained on:
  - [ ] How to deploy
  - [ ] How to monitor
  - [ ] How to troubleshoot
  - [ ] Who to contact for issues
- [ ] Runbooks created for:
  - [ ] Manual deployment
  - [ ] Rollback procedure
  - [ ] Incident response
  - [ ] Scaling operations

---

## ✅ Phase 17: Production Sign-Off

- [ ] System performance acceptable (< 2s response times)
- [ ] No memory leaks (check Cloud Run metrics)
- [ ] No unhandled errors in logs
- [ ] All features tested end-to-end
- [ ] Security review completed
- [ ] Cost estimate reasonable
- [ ] Team confident in deployment process
- [ ] Stakeholders approved for production

---

## Final Verification

```bash
# Run this final checklist script
echo "=== QTC Production Deployment Final Checklist ==="
echo ""
echo "Project: $(gcloud config get-value project)"
echo "Region: us-central1"
echo ""

# Check services
echo "Backend Service:"
gcloud run describe qtc-backend --region us-central1 --format="table(status.url)"

echo "Frontend Service:"
gcloud run describe qtc-frontend --region us-central1 --format="table(status.url)"

echo ""
echo "Recent Logs (Backend):"
gcloud run services logs read qtc-backend --region us-central1 --limit 5

echo ""
echo "All checks complete! ✅"
```

---

## Sign-Off

- **Deployed By:** ___________________________
- **Date:** ___________________________
- **Environment:** Production / Staging / Dev
- **Approved By:** ___________________________
- **Contact Person:** ___________________________

---

**Success!** Your QTC system is now running on Google Cloud Platform with fully automated CI/CD.

Next steps:
1. Share backend & frontend URLs with your team
2. Begin QA testing
3. Setup monitoring alerts
4. Plan feature rollout schedule
