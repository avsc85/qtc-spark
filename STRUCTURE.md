# 📁 QTC Project Structure Reference

## Quick Navigation

### 🔧 **Backend Development**
```
backend/
├── main.py              👈 START SERVER: python main.py
├── requirements.txt     👈 INSTALL DEPS: pip install -r requirements.txt
├── agents/              👈 AI agent implementations
├── db/                  👈 Database models and clients
├── routes/              👈 API endpoints
├── Dockerfile           👈 BUILD IMAGE: docker build -t qtc-backend .
└── terraform/           👈 GCP infrastructure definition
```

### 🎨 **Frontend Development**
```
frontend/qtc-spark/
├── src/
│   ├── main.tsx         👈 ENTRY POINT
│   ├── App.tsx
│   ├── components/      👈 React UI components
│   ├── pages/           👈 Page components
│   └── lib/             👈 Utilities & API client
├── package.json         👈 INSTALL DEPS: npm install
├── vite.config.ts       👈 Build configuration
└── Dockerfile.frontend  👈 BUILD IMAGE
```

### 📚 **Documentation**
```
docs/
├── DEPLOYMENT_QUICKSTART.md     ⭐ START HERE (30 min setup)
├── DEPLOYMENT_GCP_GUIDE.md      📖 DETAILED GUIDE
├── CICD_GUIDE.md                🔄 CI/CD PIPELINES
├── PRODUCT_DOCUMENTATION.md     📋 FEATURE DOCUMENTATION
└── DEPLOYMENT_CHECKLIST.md      ✅ PRODUCTION SIGN-OFF
```

### 🚀 **Deployment**
```
Root Level:
├── cloudbuild.yaml              👈 Google Cloud Build config
└── .github/workflows/
   └── deploy-gcp.yml            👈 GitHub Actions config

Backend:
├── setup-gcp.sh                 👈 RUN FIRST: ./setup-gcp.sh PROJECT_ID
├── deploy.sh                    👈 MANUAL DEPLOY: ./deploy.sh PROJECT_ID
└── terraform/
   ├── main.tf                   👈 Infrastructure
   ├── variables.tf
   └── terraform.tfvars.example  👈 COPY & CONFIGURE
```

---

## 🎯 Common Tasks

### 1️⃣ **Start Development Server**

**Backend (Terminal 1):**
```bash
cd backend
python main.py
# Server on http://localhost:8000
```

**Frontend (Terminal 2):**
```bash
cd frontend/qtc-spark
npm run dev
# Dev server on http://localhost:5173
```

### 2️⃣ **Deploy to GCP** (First Time)

```bash
cd backend
chmod +x setup-gcp.sh
./setup-gcp.sh your-gcp-project-id

# Then follow: docs/DEPLOYMENT_QUICKSTART.md
```

### 3️⃣ **Docker Build & Test**

```bash
# Backend
cd backend
docker build -t qtc-backend:latest .
docker run -p 8000:8000 qtc-backend:latest

# Frontend
cd frontend
docker build -t qtc-frontend:latest -f Dockerfile.frontend .
docker run -p 8080:8080 qtc-frontend:latest
```

### 4️⃣ **Deploy Manually to Production**

```bash
cd backend
./deploy.sh your-gcp-project-id
```

### 5️⃣ **Enable CI/CD Automation**

**Option A: Cloud Build**
```bash
gcloud builds submit
```

**Option B: GitHub Actions**
- Add secrets to GitHub repo
- Push to main → Auto-deploy

---

## 📊 Directory Functions

| Directory | Purpose | Tools |
|-----------|---------|-------|
| `backend/` | FastAPI server, agents, DB | Python, FastAPI, Firestore |
| `frontend/qtc-spark/` | React web app | React, TypeScript, Vite |
| `docs/` | All documentation | Markdown |
| `.github/workflows/` | GitHub CI/CD | GitHub Actions |
| `backend/terraform/` | Infrastructure as Code | Terraform, GCP |

---

## 🔑 Key Files to Know

| File | What to Use It For |
|------|--------------------|
| `backend/main.py` | Start backend server |
| `backend/requirements.txt` | Install Python packages |
| `frontend/qtc-spark/package.json` | Install Node packages |
| `backend/Dockerfile` | Build backend container |
| `docs/DEPLOYMENT_QUICKSTART.md` | Quick deployment (30 min) |
| `backend/setup-gcp.sh` | Automated GCP setup |
| `backend/terraform/main.tf` | All GCP resources defined |
| `cloudbuild.yaml` | Automated GCP deployment |

---

## ✅ Verification Checklist

After organizing, verify:

- [ ] `backend/` has all Python source files
- [ ] `frontend/qtc-spark/` has `package.json` and `src/`
- [ ] `docs/` has all markdown files
- [ ] `.github/workflows/deploy-gcp.yml` exists
- [ ] `cloudbuild.yaml` is at root level
- [ ] No Python files at root level
- [ ] No markdown files at root level (except README.md)
- [ ] `backend/terraform/` has `.tf` files
- [ ] All necessary config files are `.example` files

---

## 🚀 Quick Start Paths

### Path 1: Local Development Only
```
→ Install requirements
→ Run backend: python main.py
→ Run frontend: npm run dev
→ Edit code
→ Test in browser http://localhost:5173
```

### Path 2: Production Deployment (Recommended)
```
→ Read: docs/DEPLOYMENT_QUICKSTART.md
→ Run: backend/setup-gcp.sh
→ Configure: backend/terraform/terraform.tfvars
→ Deploy: terraform apply
→ Test: Check Cloud Run URLs
```

### Path 3: CI/CD Automation
```
→ Run: backend/setup-gcp.sh
→ Configure: backend/terraform/terraform.tfvars
→ Deploy: terraform apply
→ Choose: Cloud Build OR GitHub Actions
→ Push: git push origin main
→ Auto-deploy on every push!
```

---

## 📝 Configuration Files

### Backend Environment
```
.env (local)
.env.example (template)
backend/.env.production.example (production)
```

### Frontend Configuration
```
frontend/qtc-spark/vite.config.ts
frontend/qtc-spark/tsconfig.json
frontend/qtc-spark/tailwind.config.ts
```

### Deployment Configuration
```
backend/terraform/terraform.tfvars (configure here)
backend/terraform/terraform.tfvars.example (template)
cloudbuild.yaml (GCP)
.github/workflows/deploy-gcp.yml (GitHub)
```

---

## 🔗 Important Links

- **GCP Quick Start**: `docs/DEPLOYMENT_QUICKSTART.md`
- **Full Deployment**: `docs/DEPLOYMENT_GCP_GUIDE.md`
- **CI/CD Setup**: `docs/CICD_GUIDE.md`
- **Features Docs**: `docs/PRODUCT_DOCUMENTATION.md`

---

## 💡 Tips

1. **Always read** `docs/DEPLOYMENT_QUICKSTART.md` before deploying
2. **Never commit** `.env` file (contains secrets)
3. **Copy and modify** `.example` files for your environment
4. **Use `setup-gcp.sh`** for first-time GCP setup
5. **Follow** `docs/DEPLOYMENT_CHECKLIST.md` before production

---

**Last Updated**: March 16, 2026  
**Status**: ✅ Production Ready
