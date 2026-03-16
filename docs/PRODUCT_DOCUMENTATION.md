# QTC Product Documentation

## 1. Executive Summary

QTC is an AI-assisted quote-to-cash platform for small construction, drafting, architecture, and design businesses. The product is built to reduce administrative work across the full customer lifecycle, starting with lead capture and ending with contract signing, invoicing, and payment tracking.

The core product idea is simple: a small business owner should be able to run operational workflows from a single system instead of juggling phone notes, spreadsheets, PDFs, email threads, contract templates, invoice tools, and payment links.

QTC combines:

- A chat-first AI workflow layer
- Structured operational records for leads, contracts, and invoices
- Contract template generation and manual editing
- Digital signature workflow
- Payment-link-based invoice sending
- A dashboard and settings layer for business operations and branding

The current codebase represents an MVP-to-beta stage product with a working full-stack implementation across frontend, backend, Firestore, cloud storage, and AI-powered document generation.

## 2. Product Vision

The long-term vision for QTC is to become the operating system for small project-based service firms, especially those in residential construction and design.

Today, many of these firms are owner-led and operationally fragmented. The owner is often acting as salesperson, estimator, project coordinator, contract manager, invoice sender, and collections follow-up. That creates avoidable delays, missed revenue, inconsistent documentation, and a poor customer handoff between stages.

QTC is designed to centralize and automate those steps in a single environment where AI helps the operator move from raw customer input to clean business output.

The target end-state is:

Customer inquiry -> qualified lead -> structured project record -> generated contract -> approved signature -> milestone invoices -> payment visibility -> project completion.

## 3. Problem Statement

Small construction and design businesses usually face the same operational issues:

- Lead details are captured informally by phone, text, or memory.
- Quotes are discussed verbally and not stored in structured form.
- Contracts are manually assembled from old templates.
- Branding and company information are inconsistently applied.
- Signature collection is slow and fragmented.
- Invoices are created manually and often late.
- Payment status is tracked across separate tools.
- Owners do not have one place to see pipeline, contracts, and revenue.

These are not edge-case issues. They are the default operating model for many small firms. QTC exists to reduce this operational drag.

## 4. Ideal Customer Profile

QTC is best suited for small, service-based firms that sell project work with proposals, contracts, and milestone billing.

Primary customer segments:

- ADU designers
- Residential drafting firms
- Interior design studios
- Remodel contractors
- Permit expediters and plan providers
- Home addition and renovation specialists

Typical business profile:

- 1 to 15 employees
- Owner-led operations
- High-value but relatively low-volume projects
- Heavy use of templates and repeated contract structures
- Limited admin staff or none at all
- Need for clear client communication and fast document turnaround

## 5. Product Positioning

QTC is not just a CRM, not just a contract tool, and not just an invoicing tool. It is positioned as a workflow system that unifies all three around an AI interaction layer.

The product differentiators are:

- Chat-first workflow execution
- AI-assisted lead extraction and contract generation
- Contract generation tied directly to customer data
- Built-in e-sign flow rather than external routing only
- Invoice creation tied to contract and milestone logic
- Company branding embedded into generated documents

## 6. Core User Journey

The most important end-to-end journey in QTC is the operational path from first customer conversation to signed contract and invoice generation.

### Stage 1: Lead Capture

The user captures a new lead through either:

- Structured lead entry via the Leads page
- Chat-driven action flow through the Chat page
- AI parsing from freeform text or voice-transcribed input

The system converts customer information into a structured lead record with fields such as:

- customer_name
- phone
- email
- city or address context
- project_type
- quote_amount
- notes
- status

This converts unstructured inquiry data into an operational object that can drive later workflows.

### Stage 2: Contract Generation

From a lead, the user can generate a contract using a selected template such as:

- ADU Legalization
- Construction and Remodeling
- Home Addition
- Electrical Permit

The contract generation flow combines:

- Lead/customer data
- Company profile data
- Template content stored in cloud storage
- AI-based placeholder completion or HTML rendering logic

Generated contracts are saved as draft records and can then be:

- Reviewed
- Edited with AI instructions
- Edited manually by a human
- Downloaded
- Sent for signature

### Stage 3: Signature Flow

When a draft contract is approved, the user can send it for signing.

The system:

- Creates a unique signing token
- Stores it in Firestore
- Builds a signing URL
- Emails the signer
- Exposes a public signing route for the customer

The customer can open the signing page, review the contract, and sign using multiple signature modes. Once complete, the system updates the contract and can move the linked lead forward into the active state.

### Stage 4: Invoice Generation and Payment Sending

Invoices are created from contracts. The platform derives milestone invoices based on contract template/payment structure and stores invoices in Firestore.

The user can:

- Review invoices
- Send an invoice
- Generate payment links
- Track status

This allows the system to continue downstream from contract execution into revenue collection.

## 7. Product Modules

The QTC application is organized into a small set of major modules.

### 7.1 Dashboard

The dashboard provides a quick business overview with operational metrics such as:

- Total leads
- Signed contracts
- Unpaid invoices
- Revenue collected

It also shows recent leads and recent invoices, making it the top-level operational entry point after login.

### 7.2 Leads Module

The Leads page is the structured CRM-lite layer of the product. It is intentionally simple and operational rather than sales-enterprise oriented.

Current capabilities include:

- Fetching real leads from backend storage
- Capturing new leads from natural language input
- Viewing lead details
- Generating contracts from a lead
- Opening lead-specific chat context
- Deleting leads

Lead deletion is important because it also removes related downstream records from backend storage where appropriate.

### 7.3 Contracts Module

The Contracts page is one of the most important product surfaces because it bridges customer/project data to legal and commercial documentation.

Current capabilities include:

- Listing contracts from Firestore
- Generating contracts from leads and templates
- AI-based edit flow
- Manual human edit flow
- Sending contracts for signing
- Downloading contract text
- Deleting contracts and related dependent records

The manual edit flow is critical because contract workflows require both automation and precise human control.

### 7.4 Invoices Module

The Invoices page manages downstream billing operations tied to contracts and milestones.

Current capabilities include:

- Listing invoices
- Creating invoices from contract context
- Sending invoices with payment links
- Tracking invoice status
- Updating invoice fields through backend support

### 7.5 Chat Module

The Chat page is the AI-native interaction layer of the product. This is strategically important because it represents how operators can use the system without clicking through multiple rigid forms.

Current chat capabilities include:

- Streaming chat responses via SSE
- Storing and retrieving session history
- Parsing structured action blocks
- Executing backend actions such as lead creation and contract generation
- Maintaining lead-scoped sessions

This gives the product a conversational control plane instead of relying solely on form-based flows.

### 7.6 Templates Module

The Templates page presents available contract types and helps the user understand which template to choose. Templates exist as operational document definitions rather than just static marketing assets.

The current system supports template-aware contract generation using text templates stored in cloud storage and HTML rendering patterns for branded output.

### 7.7 Company Settings Module

The Settings page allows each business to maintain its own company profile and branding, including:

- Company name
- Drafter/signatory name
- Address
- Phone number
- Email
- Logo upload

This information is used in generated contracts and document rendering, allowing the product to feel business-specific rather than generic.

### 7.8 E-Sign Module

The public signature page is customer-facing. It provides:

- Contract review
- Signature capture
- Agreement checkbox flow
- Signature submission
- Completion state

This is a meaningful part of the product because it directly touches the client and finalizes the sales-to-project transition.

## 8. AI Capabilities

AI is not ornamental in QTC. It is embedded into operational steps.

### 8.1 Lead Extraction

AI extracts structured data from freeform user input such as notes from a phone call or text summary. This reduces manual entry and makes chat-based intake viable.

### 8.2 Contract Generation

AI fills contract templates using lead data and company data. The goal is to preserve legal structure while replacing placeholders accurately and quickly.

### 8.3 Contract Editing

AI can apply narrow editing commands to existing contracts. This supports fast revision workflows such as changing price, adjusting milestones, or adding clauses.

### 8.4 Chat Action Execution

AI-generated chat outputs can emit structured action blocks. The frontend parses them, and the backend executes them against real business data.

This creates a loop where conversation can directly trigger system changes.

## 9. Document Generation System

Document generation in QTC exists in two parallel forms.

### 9.1 Text Template Generation

The backend retrieves template text files from cloud storage under template-specific keys. These templates are then filled using customer and company data, primarily through AI generation logic.

### 9.2 HTML Contract Rendering

The system also includes a branded HTML contract renderer built from a base HTML contract file. This renderer supports:

- Company branding
- Styled layout
- Scope sections
- Milestone sections
- Signature-ready presentation
- PDF-friendly output behavior

This is important because it suggests the product is moving beyond plain text contracts toward more polished document output suitable for client-facing delivery and PDF workflows.

## 10. Data Model Overview

The current platform revolves around a small set of core entities.

### Lead

A lead represents an incoming customer/project opportunity.

Important fields include:

- id
- org_id
- customer_name
- phone
- email
- city
- project_type
- quote_amount
- status
- notes
- created_at

### Contract

A contract represents a generated project agreement tied to a lead.

Important fields include:

- id
- lead_id
- template_name
- content
- status
- org_id
- quote_amount
- signed_at
- storage_path
- created_at

### Invoice

An invoice represents a milestone or payable amount tied to a contract.

Important fields include:

- id
- contract_id
- lead_id
- milestone_name
- amount
- due_date
- status
- stripe_link
- created_at

### Company Profile

A company profile stores brand and legal identity data for the organization.

Important fields include:

- company_name
- company_drafter
- company_address
- company_phone
- company_email
- company_logo_url
- org_id

### Signing Token

Signing tokens support secure public document signing.

Important fields include:

- token
- contract_id
- org_id
- signer_email
- signer_name
- expires_at
- used
- signed_at

### Chat Session and Messages

Chat state is persisted so users can continue operational conversations over time.

Important fields include:

- session_id
- project_id
- role
- content
- updated_at
- created_at

## 11. Backend Architecture

The backend is a FastAPI application that exposes authenticated API routes under `/api` plus public signing routes.

Primary backend route groups include:

- leads
- contracts
- invoices
- chat
- signing
- company
- webhooks

The backend is responsible for:

- Authentication and org scoping
- Firestore persistence
- Template retrieval from cloud storage
- AI calls to OpenAI
- Signing workflow
- Logo upload and asset serving
- Invoice and payment-link orchestration

## 12. Frontend Architecture

The frontend is a React application built with Vite, TypeScript, Tailwind, shadcn/ui, and related UI tooling.

The main frontend routes are:

- /login
- /
- /leads
- /contracts
- /invoices
- /templates
- /chat
- /settings
- /sign/:token

The frontend is designed as a lightweight operational app rather than a complex admin suite. Most of the value comes from fast workflows, direct calls to the backend API, and immediate interaction between records and actions.

## 13. Authentication and Multi-Tenancy Model

QTC uses Firebase authentication patterns with a backend verification layer. In local development, auth can be disabled for testing. In production, user identity is expected to define the organization scope.

The practical tenancy model is org-based isolation using `org_id` on data records. This is essential because all business data, contracts, invoices, branding, and chat history must remain isolated per company.

## 14. Infrastructure and Services

The product currently depends on several external systems.

### Firestore

Used as the primary operational database for:

- leads
- contracts
- invoices
- signing tokens
- messages
- chat sessions
- company profiles

### Google Cloud Storage

Used for:

- contract templates
- signed PDFs
- uploaded company logos

### OpenAI

Used for:

- lead extraction
- contract generation
- AI-based contract edits
- conversational chat workflows

### Stripe

Used for invoice payment links and payment collection workflows.

### SMTP Email

Used for sending signing requests and confirmation emails.

## 15. Current Implemented Capabilities

Based on the present codebase, the product currently supports a substantial MVP feature set.

Implemented capabilities include:

- Real lead listing and creation
- AI-based lead capture from freeform text
- Real contract listing and generation
- Contract editing with AI
- Contract editing manually by a human
- Contract deletion
- Lead deletion with backend cleanup of related data
- Sending contracts for signature
- Public signature page and signing completion flow
- Invoice creation from contract context
- Invoice sending via payment link creation
- Dashboard metrics and recents
- Template catalog UI
- Company profile and logo storage
- Chat history, sessions, streaming, and action execution

## 16. Product Strengths

The strongest aspects of the product today are:

- Clear vertical focus on construction and drafting workflows
- Strong operational flow from lead to revenue
- Practical use of AI instead of novelty use
- Working contract generation and signing story
- Company branding support for real business use
- Small enough product surface to ship quickly and iterate

## 17. Product Risks and Gaps

The product is promising, but there are still meaningful risks and unfinished areas.

### Operational Risks

- Financial workflows require high trust and auditability.
- Contract generation quality must be consistently correct.
- Payment and signature flows must be resilient and explainable.

### Product Risks

- Chat workflows may feel powerful but can become opaque if the system acts without enough visibility.
- Template coverage may be too narrow for broader construction segments.
- Some users will prefer traditional forms over chat-first interactions.

### Technical Gaps

- More robust invoice lifecycle and reconciliation may still be needed.
- Production-grade audit logs and permissioning are not yet fully visible in the current codebase.
- Public document output and PDF generation strategy should be standardized further.
- Some development-stage warnings and performance optimizations remain open.

## 18. Why This Product Matters

QTC matters because it targets a very real gap in the market: businesses that are too operationally complex for manual workflows but too small to adopt heavy enterprise systems.

This class of business often does not need a full ERP. It needs a faster way to capture work, formalize it, and get paid without losing control of customer interactions.

QTC addresses that with a focused vertical workflow instead of a generic back-office stack.

## 19. Recommended Near-Term Roadmap

The highest-value next steps for the product are:

1. Strengthen auditability for contract changes, signatures, and invoice events.
2. Improve template management so businesses can own and customize more of their legal language.
3. Expand invoice lifecycle states, reminders, and collections workflows.
4. Add richer payment reconciliation and status syncing.
5. Add role-based access for teams beyond a single owner/operator model.
6. Improve PDF and branded document output consistency across all template types.
7. Expand analytics across pipeline, conversion, and revenue forecasting.

## 20. One-Sentence Summary

QTC is an AI-assisted quote-to-cash operating system for small construction and design businesses that turns customer conversations into structured leads, branded contracts, signed agreements, invoices, and payment visibility in a single workflow.

---

# TECHNICAL DEEPER DIVE

## 21. API Reference Overview

All backend API endpoints are prefixed with `/api` and grouped by resource domain.

### Core Endpoints Structure

```
POST   /api/leads/capture              Create a new lead from text/data
GET    /api/leads                       List all leads for org
PATCH  /api/leads/{lead_id}/status      Update lead status
DELETE /api/leads/{lead_id}             Delete lead + cascade

POST   /api/contracts/generate          Generate contract from lead + template
GET    /api/contracts                   List all contracts for org
GET    /api/contracts/{contract_id}     Get contract details
PATCH  /api/contracts/{contract_id}     AI-edit contract
PATCH  /api/contracts/{contract_id}/content   Manual-edit contract
PATCH  /api/contracts/{contract_id}/status    Update status
POST   /api/contracts/{contract_id}/send-for-signing   Initiate signature
DELETE /api/contracts/{contract_id}     Delete contract + cascade
POST   /api/contracts/generate-from-reference   Generate from DOCX

POST   /api/invoices                    Create invoice from contract
GET    /api/invoices                    List all invoices for org
PATCH  /api/invoices/{invoice_id}       Update invoice
POST   /api/invoices/{invoice_id}/send  Send invoice + create payment link

POST   /api/chat                        New chat session
GET    /api/chat/history                Session message history
POST   /api/chat/message                Send message + stream response
GET    /api/chat/sessions               List sessions

GET    /api/sign/{token}                Public signature page
POST   /api/sign/{token}/complete       Submit signature

GET    /api/company/profile             Get org company profile
PUT    /api/company/profile             Update company profile
POST   /api/company/logo                Upload company logo
GET    /api/company/logo                Serve company logo

GET    /health                          Service health check
```

### Authentication

All endpoints except `/api/sign/{token}` and `/health` require Firebase Bearer token authentication passed as:

```
Authorization: Bearer {firebase_id_token}
```

The backend verifies this token (or skips in local dev with `DISABLE_AUTH=true`) and extracts the `org_id` from the token claims, scoping all database queries and writes to that organization.

### Response Format

All API responses use JSON with the following patterns:

**Success (2xx):**
```json
{
  "id": "...",
  "data": { ... },
  "created_at": "2024-01-15T10:30:00Z"
}
```

**Error (4xx/5xx):**
```json
{
  "detail": "Descriptive error message",
  "status_code": 400
}
```

## 22. Contract Generation Pipeline

Contract generation is one of the most important product pipelines. It orchestrates multiple systems to produce a legal document from customer data.

### Generation Flow

1. **Input Capture**
   - User selects a lead and a template
   - User can optionally customize quote amount

2. **Data Aggregation**
   - Fetch lead record from Firestore
   - Fetch company profile from Firestore
   - Validate template exists in GCS

3. **AI Completion**
   - Call OpenAI GPT-4o with contract template + customer data
   - Ask AI to fill placeholders and generate complete contract content
   - Return completed content string

4. **HTML Rendering (Optional)**
   - Take completed contract content
   - Combine with HTML base template
   - Apply company branding, logo, styling
   - Produce browser-ready/PDF-ready HTML

5. **Persistence**
   - Save contract record to Firestore with fields:
     - `contract_id` (UUID)
     - `lead_id`
     - `template_name`
     - `html_content`
     - `text_content`
     - `status` → "draft"
     - `org_id`
     - `quote_amount`
     - `created_at`

6. **Return to UI**
   - Frontend displays contract in contract detail modal
   - User can review, edit (AI or manual), or send for signing

### Template System

Templates exist in GCS at `gs://qtc-documents-zheight/templates/{template_name}.txt`

Available templates:
- `adu_legalization.txt` - ADU legalization and permitting
- `remodeling.txt` - General construction/remodeling contracts
- `home_addition.txt` - Residential addition projects
- `electrical_permit.txt` - Electrical design and permits

Each template includes:
- Legal language (scope of work, terms, exclusions)
- Placeholder tokens (Customer Name, Date, Price, Milestones, etc.)
- Formatting hints for AI parsing

### AI Directive

The contract agent sends templates to OpenAI with the instruction:

> "You are a contract generation assistant. Use the provided template and customer data to produce a complete, legally-sound contract. Replace all {{placeholder}} tokens with actual values. Maintain the exact structure and legal language of the template. Return only the completed contract text, no explanations."

GPT-4o is responsible for:
- Understanding customer context
- Filling financial/date/name placeholders accurately
- Preserving legal and structural integrity
- Handling edge cases (e.g., multiple projects, variable pricing)

## 23. Signature Workflow

The signature workflow enables customers to digitally sign contracts without requiring external e-signature tools.

### Signature Token Flow

1. **Token Creation**
   - User clicks "Send for Signing" on contract
   - Backend generates:
     - Unique signing token (UUID or secure hash)
     - Expiration datetime (default 30 days)
     - Signer email address
     - Signer name
   - Store in Firestore `signing_tokens` collection with fields:
     - `token` (primary key)
     - `contract_id` (lookup)
     - `org_id` (multi-tenant safety)
     - `signer_email`
     - `signer_name`
     - `expires_at`
     - `used` (boolean)
     - `signed_at` (null until signed)

2. **Email Dispatch**
   - Render signing email with:
     - Recipient name
     - Contract preview text
     - Clickable signing link: `https://app.qtc.dev/sign/{token}`
   - Send via SMTP (Gmail configured)

3. **Public Signing Page**
   - Customer clicks link from email
   - Frontend loads `/sign/{token}` (public route, no auth)
   - Page displays:
     - Contract content (full text or HTML-rendered)
     - Signature options: draw, type, upload image
     - Agreement checkbox
     - Submit button

4. **Signature Capture**
   - Customer draws/types/uploads signature
   - Ticks agreement checkbox
   - Clicks submit

5. **Backend Processing**
   - Validate token exists and not expired
   - Validate token not already used
   - Generate PDF from contract (HTML + signature image overlay)
   - Upload PDF to GCS at `gs://qtc-documents-zheight/signed/{contract_id}.pdf`
   - Update contract record:
     - `status` → "signed"
     - `signed_at` → current timestamp
     - `storage_path` → GCS path
   - Mark signing token as used
   - Send confirmation email to customer

6. **Post-Signature**
   - Update lead status to "active" (if appropriate)
   - Enable invoice creation workflow
   - Notify user in dashboard/email

## 24. Invoice Lifecycle

Invoices are milestone-based and tied directly to contracts.

### Invoice Creation

When a user creates invoices from a contract:

1. Fetch contract to get `template_name` and `quote_amount`
2. Reference template scope config (from `template_scopes.py`)
3. Calculate milestone amounts based on payment structure (default: 3 equal milestones)
   - Milestone 1: 33% (due at contract signature)
   - Milestone 2: 33% (due at 50% project completion)
   - Milestone 3: 34% (due at project completion)
4. Create 3 invoice records in Firestore:
   - `invoice_id` (UUID)
   - `contract_id`
   - `lead_id`
   - `milestone_name` (e.g., "Design - Phase 1")
   - `amount` (calculated)
   - `due_date` (calculated: now + 30 days, +60 days, +90 days)
   - `status` → "draft"
   - `org_id`
5. Return invoice list to UI

### Invoice Sending

When user sends an invoice:

1. Fetch invoice and contract details
2. Create Stripe payment link:
   - Amount in cents
   - Customer email
   - Metadata: invoice_id, contract_id, company name
3. Send email to customer with:
   - Invoice summary
   - Amount due
   - Payment link
   - Due date
4. Update invoice:
   - `status` → "sent"
   - `stripe_link` → payment URL
   - `sent_at` → current timestamp

### Payment Tracking

Stripe webhooks notify the backend when:
- Payment succeeded
- Payment failed
- Customer dispute opened

The webhook endpoint updates invoice status accordingly.

## 25. Chat and Action Execution

The Chat module is the conversational interface to the system.

### Session Model

Each chat conversation is a session with:
- `session_id` (UUID)
- `project_id` (optional lead_id context)
- `org_id` (multi-tenant)
- `created_at`
- `updated_at`

### Message Flow

1. User types message into chat input
2. Frontend sends POST to `/api/chat/message`
3. Backend:
   - Fetches session history
   - Constructs prompt with system role + history + user message
   - Calls OpenAI with chat completion
   - Streams response token-by-token via Server-Sent Events (SSE)
4. Frontend receives stream and renders tokens in real-time
5. Backend includes `ACTION` blocks in response

### Action Blocks

The chat agent can emit structured action blocks in responses:

```
Chat: Based on your request, I've created a new lead:

ACTION
{
  "type": "create_lead",
  "lead_id": "lead_612abc",
  "customer_name": "John Smith",
  "quote_amount": 5000
}
END_ACTION

The lead is now ready for contract generation.
```

Frontend parses these blocks and:
- Extracts action metadata
- Offers button to confirm/execute action
- Calls backend action endpoint upon click
- Updates UI with result

Supported actions:
- `create_lead`
- `generate_contract`
- `send_invoice`
- `create_invoice`
- `get_contract`
- `list_leads`
- `list_invoices`

## 26. Database Schema Details

### Firestore Collections

**`organizations/{org_id}/leads`**
- `id`, `customer_name`, `phone`, `email`, `city`, `project_type`, `quote_amount`, `status`, `notes`, `created_at`, `org_id`

**`organizations/{org_id}/contracts`**
- `id`, `lead_id`, `template_name`, `content`, `html_content`, `status`, `quote_amount`, `signed_at`, `storage_path`, `created_at`, `org_id`

**`organizations/{org_id}/invoices`**
- `id`, `contract_id`, `lead_id`, `milestone_name`, `amount`, `due_date`, `status`, `stripe_link`, `sent_at`, `paid_at`, `org_id`

**`organizations/{org_id}/signing_tokens`**
- `token`, `contract_id`, `signer_name`, `signer_email`, `expires_at`, `used`, `signed_at`, `org_id`

**`organizations/{org_id}/chat_sessions`**
- `session_id`, `project_id`, `created_at`, `updated_at`, `org_id`

**`organizations/{org_id}/chat_messages`**
- `message_id`, `session_id`, `role` (user/assistant), `content`, `created_at`

**`organizations/{org_id}/company_profile`**
- `company_name`, `company_drafter`, `company_address`, `company_phone`, `company_email`, `company_logo_url`, `org_id`

### Firestore Design Pattern

All collections follow an org-scoped pattern for multi-tenancy:
```
organizations/{org_id}/{resource_type}/{resource_id}
```

This ensures:
- No org can see another's data
- Queries are org-scoped by default
- Deletion cascades remain within org

## 27. Frontend Component Architecture

### Page Structure

Each major page is a React component backed by API calls and local state management (React hooks).

**Key Pages:**
- `LoginPage.tsx` - Firebase auth or dev bypass
- `DashboardPage.tsx` - Stats + recent records
- `LeadsPage.tsx` - Lead list, capture, detail drawer
- `ContractsPage.tsx` - Contract list, generate, edit (AI/manual), send, delete
- `InvoicesPage.tsx` - Invoice list, create, send with payment link
- `ChatPage.tsx` - Streaming chat with action execution
- `TemplatesPage.tsx` - Template catalog and product orientation
- `SettingsPage.tsx` - Company profile, logo upload
- `ESignPage.tsx` - Public signature capture (no auth)

### State Management

The frontend uses React hooks for state:
- `useState` for component-local UI state
- Custom hooks like `useToast` for notifications
- API client methods for async data operations
- Manual refetch + optimistic updates for mutations

### Component Design

Core reusable components from shadcn/ui:
- Button, Input, Label, Form
- Card, Dialog, Drawer
- Table, Badge, Select
- Alert, Toast notifications

Styled with Tailwind CSS and postcss.

## 28. Backend File Structure

```
.
├── main.py                          # FastAPI app entry, middleware, router includes
├── requirements.txt                 # Python dependencies
├── agents/                          # AI agent modules
│   ├── contract_agent.py           # Contract generation + editing
│   ├── chat_agent.py               # Chat conversational logic
│   ├── lead_agent.py               # Lead extraction from text
│   ├── invoice_agent.py            # Invoice creation + payment
│   ├── signing_agent.py            # Signing workflow + email
│   ├── template_agent.py           # Template-based generation
│   ├── template_scopes.py          # Template config (milestones, scope items)
│   ├── action_parser.py            # Parse ACTION blocks from chat
│   └── pdf_generator.py            # HTML to PDF conversion
├── routes/                         # API endpoints
│   ├── leads.py                   # GET/POST/PATCH leads, DELETE lead
│   ├── contracts.py               # GET/POST/PATCH contracts, DELETE contract
│   ├── invoices.py                # GET/POST invoices, send
│   ├── chat.py                    # Chat history, sessions, streaming
│   ├── signing.py                 # Public sign endpoint, token validation
│   ├── company.py                 # Company profile, logo upload
│   └── webhooks.py                # Stripe webhook handler
├── db/                            # Database + cloud clients
│   ├── firestore_client.py       # Firestore async operations
│   ├── storage_client.py         # GCS operations
│   ├── firebase_auth.py          # Firebase token verification
│   ├── models.py                 # Pydantic models for API
│   └── [resource_db].py          # leads.py, contracts.py, etc.
└── templates/                     # HTML templates
    ├── base_contract.html        # HTML contract base template
    └── *.txt                     # Text contract templates (GCS)
```

## 29. Deployment and Environment Configuration

### Environment Variables

**Required for production:**
```
GOOGLE_APPLICATION_CREDENTIALS    # GCS/Firestore service account JSON path
GCS_BUCKET_NAME                   # GCS bucket (default: qtc-documents-zheight)
OPENAI_API_KEY                    # OpenAI API key
STRIPE_API_KEY                    # Stripe secret key
STRIPE_WEBHOOK_SECRET             # Stripe webhook signing secret
FIREBASE_PROJECT_ID               # Firebase project ID
SMTP_USERNAME                     # Gmail account for signing emails
SMTP_PASSWORD                     # Gmail app password
DISABLE_AUTH                      # Set to "false" for production
```

**Optional:**
```
PORT                              # Backend port (default: 8000)
FRONTEND_URL                      # CORS origin for frontend
```

### Running Backend

```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn main:app --reload --port 8000

# Run production
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:8000
```

### Running Frontend

```bash
cd qtc-spark

# Install dependencies
bun install  # or npm install / yarn install

# Development
npm run dev -- --port 8080

# Production build
npm run build
npm run preview  # local testing of optimized build
```

## 30. Testing and Quality Assurance

### Manual Testing Checklist

- **Lead Capture:** Text → structured lead record
- **Contract Generation:** Lead + template → HTML contract
- **AI Edit:** Original contract → GPT rephrasing → updated contract
- **Manual Edit:** Contract → human textarea input → saved contract
- **Signature:** Public link → customer signature → PDF saved to GCS
- **Invoice Creation:** Contract → 3 milestone invoices
- **Invoice Payment:** Send invoice → customer clicks Stripe link → payment processed
- **Delete Operations:** Delete lead → related contracts/invoices cleaned up
- **Chat Actions:** Chat message with ACTION block → execute backend action

### Frontend Build Validation

```bash
cd qtc-spark
npm run build    # TypeScript compilation
npm run lint     # ESLint checks
```

Currently: Zero TypeScript errors, only bundle-size warnings (acceptable).

## 31. Performance Considerations

### Database Queries

- All Firestore queries include `.where('org_id', '==', org_id)` for security and performance
- Indexes are recommended on:
  - `(org_id, status)` for filtering by status
  - `(org_id, created_at)` for recency queries
  - `(lead_id, org_id)` for backref queries

### API Response Times

Target SLAs:
- Lead creation: < 2s (includes AI extraction)
- Contract generation: < 5s (includes AI completion)
- Contract edit (AI): < 8s (includes GPT call)
- Signature completion: < 3s (includes PDF generation)

### Frontend Optimization

- Code-splitting by route via Vite
- Lazy loading of modals/dialogs
- Optimistic UI updates for mutations
- SSE streaming for chat (no polling)

## 32. Security Considerations

### Access Control

- All authenticated routes verify Firebase token
- All data mutations check `org_id` ownership
- Public signing route validates token expiration
- Email verification for payment links (Stripe handles)

### Data Protection

- Sensitive fields (STRIPE_API_KEY, etc.) in environment only
- PDF files stored in private GCS bucket
- Signing tokens expire after 30 days
- Deleted records cascade safely without data orphans

### Production Hardening (Recommended)

- Enable HTTPS only
- Implement rate limiting on public endpoints
- Add request logging and monitoring
- Enable Firestore backup policies
- Use VPC and private endpoints for cloud services
- Implement audit logs for all contract and invoice changes

---

**Documentation Last Updated:** March 15, 2026  
**Product Version:** 1.0 MVP+  
**Status:** Operationally functional, in active development