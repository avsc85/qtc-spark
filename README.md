# Quote to Cash (QTC) Application - Project Structure

## Overview
This project is organized into a clean, production-ready directory structure with clear separation between backend, frontend, documentation, and infrastructure code.

---

## Directory Structure

```
QTC app/
├── backend/                          # Backend FastAPI application
│   ├── main.py                      # Entry point for FastAPI server
│   ├── requirements.txt              # Python dependencies
│   ├── Dockerfile                   # Backend container configuration
│   ├── .dockerignore                # Docker build optimization
│   ├── agents/                      # AI agent implementations
│   │   ├── chat_agent.py
│   │   ├── contract_agent.py
│   │   ├── invoice_agent.py
│   │   ├── lead_agent.py
│   │   ├── signing_agent.py
│   │   ├── template_agent.py
│   │   └── action_parser.py
│   ├── db/                          # Database clients and models
│   │   ├── client.py
│   │   ├── contracts.py
│   │   ├── firebase_auth.py
│   │   ├── firestore_client.py
│   │   ├── invoices.py
│   │   ├── leads.py
│   │   ├── messages.py
│   │   ├── models.py
│   │   └── storage_client.py
│   ├── routes/                      # API route handlers
│   │   ├── chat.py
│   │   ├── contracts.py
│   │   ├── invoices.py
│   │   ├── leads.py
│   │   ├── signing.py
│   │   └── webhooks.py
│   ├── templates/                   # Email and document templates
│   ├── terraform/                   # Infrastructure as Code
│   │   ├── main.tf                 # GCP resource definitions
│   │   ├── variables.tf            # Terraform variables
│   │   ├── terraform.tfvars.example # Configuration template
│   │   └── backend.tf.example      # State backend configuration
│   ├── setup-gcp.sh                # Automated GCP project setup
│   ├── deploy.sh                   # Manual deployment script
│   ├── .env.production.example     # Environment variables template
│   ├── clear_contracts.py          # Utility: Clear contracts database
│   ├── test_endpoints.py           # Utility: Test API endpoints
│   └── upload_templates.py         # Utility: Upload templates to storage
│
├── frontend/                        # React + Vite frontend application
│   ├── qtc-spark/                  # Main React application
│   │   ├── src/                    # React source code
│   │   │   ├── main.tsx            # React entry point
│   │   │   ├── App.tsx             # App component
│   │   │   ├── components/         # React components
│   │   │   ├── pages/              # Page components
│   │   │   ├── hooks/              # Custom React hooks
│   │   │   ├── lib/                # Utility libraries
│   │   │   └── context/            # React context providers
│   │   ├── public/                 # Static assets
│   │   ├── package.json            # Node.js dependencies
│   │   ├── vite.config.ts          # Vite configuration
│   │   ├── tsconfig.json           # TypeScript configuration
│   │   └── tailwind.config.ts      # Tailwind CSS configuration
│   └── Dockerfile.frontend         # Frontend container configuration
│
├── docs/                           # Documentation
│   ├── PRD.md                     # Product Requirements Document
│   ├── PRODUCT_DOCUMENTATION.md   # Technical documentation (32 sections)
│   ├── FEATURE_COMPARISON_ANALYSIS.md  # Feature gap analysis
│   ├── FIXES_NEEDED_DOCUMENT.md   # Roadmap for improvements
│   ├── DEPLOYMENT_QUICKSTART.md   # 30-minute deployment guide
│   ├── DEPLOYMENT_GCP_GUIDE.md    # Comprehensive GCP deployment guide
│   ├── DEPLOYMENT_SYSTEM_SUMMARY.md  # Executive summary
│   ├── DEPLOYMENT_CHECKLIST.md    # Production sign-off checklist
│   ├── CICD_GUIDE.md              # CI/CD pipeline documentation
│   ├── day2.md                    # Development notes - Day 2
│   ├── day3_lead_agent.md         # Development notes - Lead agent
│   ├── day4_contract_agent.md     # Development notes - Contract agent
│   ├── day5_invoice_agent.md      # Development notes - Invoice agent
│   ├── day6_chat_agent.md         # Development notes - Chat agent
│   ├── adu_legalization.txt       # Sample document
│   ├── electrical_permit.txt      # Sample document
│   ├── home_addition.txt          # Sample document
│   └── remodeling.txt             # Sample document
│
├── .github/                        # GitHub configuration
│   └── workflows/
│       └── deploy-gcp.yml         # GitHub Actions CI/CD pipeline
│
├── .gitignore                      # Git ignore rules
├── .env                           # Local environment variables (DO NOT COMMIT)
├── .env.example                   # Environment template
├── cloudbuild.yaml                # Google Cloud Build CI/CD configuration
├── README.md                       # This file
└── __pycache__/                   # Python cache (git ignored)

```

---

## Key Directories Explained

### `/backend`
The FastAPI application backend including:
- **API Routes**: REST endpoints for leads, contracts, invoices, chat, signing, and webhooks
- **AI Agents**: Specialized agents for different business processes
- **Database**: Firebase/Firestore client and data models
- **Infrastructure**: Terraform code for GCP deployment
- **Deployment**: Docker, setup scripts, and deployment automation

### `/frontend`
The React/Vite web application including:
- **Components**: Reusable React UI components
- **Pages**: Full page implementations (Dashboard, Leads, Contracts, Invoices, Chat, Templates, E-Sign)
- **State Management**: Context API for authentication and UI state
- **Configuration**: Vite, TypeScript, Tailwind CSS, ESLint

### `/docs`
Comprehensive documentation:
- **Architecture & Design**: PRD, product documentation
- **Feature Analysis**: Comparison and roadmap documents
- **Deployment Guides**: Quick start, detailed guides, checklists
- **Development Notes**: Day-by-day progress documentation
- **Sample Data**: Example legal documents

### `/.github/workflows`
GitHub Actions automation for CI/CD

### Root Level
- `cloudbuild.yaml` - Google Cloud Build configuration
- `requirements.txt` - Python dependencies (backend)
- Environment files and configuration templates

---

## Getting Started

### 1. **Local Development**

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # or .venv\Scripts\Activate.ps1 on Windows
pip install -r requirements.txt
python main.py

# Frontend (new terminal)
cd frontend/qtc-spark
npm install
npm run dev
```

### 2. **Production Deployment (GCP)**

```bash
# Step 1: Run automated GCP setup (5 min)
cd backend
chmod +x setup-gcp.sh
./setup-gcp.sh your-gcp-project-id

# Step 2: Add API secrets to Secret Manager (5 min)
# Follow instructions in docs/DEPLOYMENT_QUICKSTART.md

# Step 3: Deploy infrastructure (5 min)
cd terraform
terraform init
terraform plan
terraform apply

# Result: Application live on Google Cloud!
```

### 3. **CI/CD Pipeline**

Two options available:

**Option A: Google Cloud Build** (recommended for GCP-native deployment)
```bash
# All files in place, just trigger:
gcloud builds submit
```

**Option B: GitHub Actions** (if using GitHub)
```bash
# Add secrets to GitHub repository
# Automatic deployment on push to main branch
git push origin main
```

---

## Important Files

| File | Purpose |
|------|---------|
| `backend/main.py` | Backend entry point - starts FastAPI server |
| `backend/Dockerfile` | Containerize backend for Cloud Run |
| `frontend/qtc-spark/package.json` | Frontend dependencies |
| `frontend/Dockerfile.frontend` | Containerize frontend for Cloud Run |
| `backend/requirements.txt` | Python package dependencies |
| `backend/terraform/main.tf` | Complete GCP infrastructure definition |
| `cloudbuild.yaml` | Google Cloud Build CI/CD pipeline |
| `.github/workflows/deploy-gcp.yml` | GitHub Actions CI/CD pipeline |
| `docs/DEPLOYMENT_QUICKSTART.md` | Quick deployment guide |

---

## Environment Variables

### Backend (.env file)
```
FIREBASE_PROJECT_ID=your-project
FIREBASE_PRIVATE_KEY=your-key
OPENAI_API_KEY=your-key
STRIPE_API_KEY=your-key
STRIPE_WEBHOOK_SECRET=your-secret
```

Copy `.env.example` to `.env` and fill in your values.

### Frontend
Configuration in `frontend/qtc-spark/src/lib/api.ts`

---

## Database

**Firestore (Firebase)** - NoSQL database for:
- Leads data
- Contracts data
- Invoices data
- Chat messages
- User data

**Cloud Storage** - Document storage for:
- Contract templates
- Generated documents
- User-uploaded files

---

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Service health check |
| `/leads` | GET/POST | Lead management |
| `/contracts` | GET/POST | Contract management |
| `/invoices` | GET/POST | Invoice management |
| `/chat` | POST | Chat with AI agent |
| `/signing` | POST | E-signature document |
| `/webhooks/stripe` | POST | Stripe payment webhooks |

---

## Deployment Architecture

```
┌─────────────────────────────────────┐
│         Frontend (Cloud Run)         │
│        React + Vite (256MB)         │
│    Serves static files on :8080    │
└──────────────┬──────────────────────┘
               │
               │ HTTPS
               │
┌──────────────▼──────────────────────┐
│         Backend (Cloud Run)          │
│       FastAPI (512MB, 1 vCPU)       │
│    Listens on :8000                 │
└──────────────┬──────────────────────┘
               │
      ┌────────┼────────┐
      │        │        │
      ▼        ▼        ▼
  ┌───────┐┌────────┐┌─────────┐
  │Firestore│GCS Bucket│Secret Mgr│
  │Database ││Templates ││API Keys  │
  └────────┘└────────┘└─────────┘
```

---

## Security

- **API Keys**: Stored in Google Secret Manager (never in code)
- **Service Accounts**: Least-privilege IAM roles
- **Secrets**: Never committed to git (see `.gitignore`)
- **HTTPS**: Enforced in production
- **Authentication**: Firebase Auth with JWT tokens

---

## Monitoring & Logging

- **Cloud Logging**: Automatic logs for all Cloud Run services
- **Health Checks**: `/health` endpoints monitored automatically
- **Performance**: Cloud Run auto-scaling based on traffic

---

## Cost Estimation

- Backend: ~$18/month
- Frontend: ~$9/month
- Database: ~$1/month
- Storage: ~$4/month
- **Total: ~$32/month** (covered by GCP free tier)

---

## Next Steps

1. ✅ **Folder Structure**: Complete
2. 📋 **Read**: `docs/DEPLOYMENT_QUICKSTART.md` for 30-min deployment guide
3. 🚀 **Deploy**: Run `backend/setup-gcp.sh` to start GCP setup
4. ✔️ **Verify**: Test deployed application with provided test script

---

## Support

For detailed deployment instructions, see:
- Quick start: `docs/DEPLOYMENT_QUICKSTART.md`
- Full guide: `docs/DEPLOYMENT_GCP_GUIDE.md`
- CI/CD setup: `docs/CICD_GUIDE.md`
- Verification: `docs/DEPLOYMENT_CHECKLIST.md`
