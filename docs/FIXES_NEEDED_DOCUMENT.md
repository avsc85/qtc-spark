# QTC System: Requirements vs Implementation - ACTION DOCUMENT

**Date:** March 15, 2026  
**Status:** System operational but incomplete vs. check.md vision  
**Overall Completion:** 70%

---

## 🟢 WHAT DOESN'T NEED FIXING (Already Working)

### Core Business Workflows ✅

| Feature | Status | Where It Works | Notes |
|---------|--------|----------------|-------|
| **Lead Data Capture** | ✅ Complete | ChatPage → LeadsPage | AI extracts structure from text input, saves to Firestore |
| **Contract Generation** | ✅ Complete | ContractsPage → generate contract | GPT-4o fills templates, stores HTML + text versions |
| **Contract Storage** | ✅ Complete | Firestore contracts collection | Properly org-scoped with multi-tenancy |
| **Contract Download** | ✅ Complete | ContractsPage detail modal | Users can download generated contracts |
| **Digital Signature** | ✅ Complete | Public /sign/{token} route | Customer signs via public link, PDF generated + stored |
| **Invoice Creation** | ✅ Complete | InvoicesPage from contract | 3-milestone structure auto-generated |
| **Invoice Sending** | ✅ Complete | InvoicesPage send action | Creates Stripe payment link, emails customer |
| **Payment Recording** | ✅ Complete | Stripe webhook handler | On payment, invoice marked as "paid" in Firestore |
| **Dashboard Metrics** | ✅ Complete | DashboardPage | Shows 4 key stats (leads, contracts, invoices, revenue) |
| **Company Profile** | ✅ Complete | SettingsPage | Store name, logo, branding info |
| **Manual Contract Edit** | ✅ Complete | ContractsPage edit manually | Direct textarea edit of contract content |
| **AI Contract Edit** | ✅ Complete | ContractsPage edit with AI | GPT-4o updates based on instruction |
| **Chat Messaging** | ✅ Complete | ChatPage | SSE streaming, history, session persistence |
| **Chat Action Blocks** | ✅ Complete | routes/chat.py execute_action | Parse ACTION blocks and run backend ops |

### Database & Infrastructure ✅

| Component | Status | Works | Notes |
|-----------|--------|-------|-------|
| **Firestore Multi-Tenancy** | ✅ Complete | All collections org-scoped | org_id on every record ensures isolation |
| **Lead Deletion** | ✅ Complete | Cascades to contracts/invoices | All dependent records removed |
| **Contract Deletion** | ✅ Complete | Cascades to invoices/tokens | Cleanup handles orphaned signing tokens |
| **GCS Template Storage** | ✅ Complete | 4 templates available | adu_legalization, remodeling, electrical, home_addition |
| **GCS Logo Upload** | ✅ Complete | SettingsPage upload | Logos stored and served via API |
| **Firebase Auth** | ✅ Complete | Login/logout flow | Works in production; can be disabled for dev |

### API Endpoints ✅

**All of these work correctly:**
- `POST /api/leads/capture` — Create lead from text
- `GET /api/leads` — List org leads
- `DELETE /api/leads/{id}` — Delete with cascade
- `POST /api/contracts/generate` — Generate contract
- `GET /api/contracts` — List contracts
- `PATCH /api/contracts/{id}` — AI edit
- `PATCH /api/contracts/{id}/content` — Manual edit
- `DELETE /api/contracts/{id}` — Delete with cascade
- `POST /api/contracts/{id}/send-for-signing` — Initiate e-sign
- `GET /api/sign/{token}` — Public signing page
- `POST /api/sign/{token}/complete` — Submit signature
- `POST /api/invoices` — Create invoice
- `GET /api/invoices` — List invoices
- `POST /api/invoices/{id}/send` — Send with payment link
- `POST /api/webhooks/stripe` — Payment webhook
- `POST /api/chat` — Stream chat response
- `GET /api/chat/history/{session_id}` — Get messages
- `POST /api/chat/action` — Execute ACTION

---

## 🔴 WHAT NEEDS FIXING (Gaps vs. check.md)

### Priority 1: CRITICAL (Must Have) ⚠️

#### 1.1 Conversational Command Parsing
**Status:** ❌ Not implemented  
**Impact:** HIGH - Users must click UI instead of using chat  
**Complexity:** Moderate  
**Effort:** 3-4 days

**What's Missing:**
User types: "Change contract ABC price to $8,500"  
Expected: Parse intent → update contract → confirm  
Actual: No parsing → generic response or ignored

**What Needs to Be Built:**
1. Add intent classification layer to chat_agent.py
   - Detect: edit_contract, edit_invoice, send_action
   - Extract entities: contract_id, field_name, new_value
2. Map intent → backend action
3. Validate before executing
4. Return confirmation message

**Files to Modify:**
- `agents/chat_agent.py` — Add intent parser + entity extractor
- `agents/action_parser.py` — Expand action types
- `routes/chat.py` — Handle new action types

**Example Implementation Needed:**
```python
# In chat_agent.py, add:
async def parse_user_intent(message: str, context: dict) -> dict:
    """
    Use GPT to classify intent and extract entities.
    Returns: { intent: str, entities: {}, action: dict }
    """
    # Classify: edit_contract, send_invoice, list_unpaid, etc.
    # Extract: contract_id, price, date, etc.
    # Return actionable structure
```

**Success Criteria:**
- [ ] User: "Change contract price to $8,000" → contract updated
- [ ] User: "Send first milestone invoice" → invoice sent with confirmation
- [ ] User: "What's overdue?" → list unpaid invoices (see 1.4 below)

---

#### 1.2 Real-Time Chat Notifications on Events
**Status:** ❌ Not implemented  
**Impact:** HIGH - Chat doesn't reflect business state changes  
**Complexity:** Moderate-High  
**Effort:** 3-4 days

**What's Missing:**
- Payment arrives → no announcement in chat
- Contract signed → no confirmation
- Invoice sent → no log entry in chat history

**What Needs to Be Built:**
1. Firestore real-time listeners on key collections
   - Invoices (on paid status change)
   - Contracts (on signed)
   - Chat_sessions (for updates)
2. When event detected → emit system message to chat
3. Send SSE notification to frontend
4. Both channels update (chat + dashboard)

**Files to Modify/Create:**
- `agents/chat_agent.py` — Add `listen_for_events()` function
- `routes/chat.py` — Setup real-time listener on session
- `qtc-spark/src/pages/ChatPage.tsx` — Listen for event messages

**What the Flow Should Look Like:**
```
Stripe webhook fires:
  → Updates invoice status to "paid"
  → Firestore listener detects change
  → Emits event to chat: "Payment received: $2,400 from Shelly"
  → Frontend receives via SSE
  → Displays in chat history
  → Dashboard auto-updates
```

**Success Criteria:**
- [ ] Contract signed → system message in chat within 1s
- [ ] Payment processed → payment confirmation in chat
- [ ] Invoice sent → confirmation logged in chat history

---

#### 1.3 Automatic Workflow Triggers
**Status:** ❌ Not implemented  
**Impact:** HIGH - Manual coordination instead of automation  
**Complexity:** High  
**Effort:** 4-5 days

**What's Missing:**
- Contract signed → invoices NOT auto-created
- All invoices paid → lead status NOT auto-updated to "Complete"
- Invoice sent → customer NOT auto-notified

**What Needs to Be Built:**
1. Cloud Function or Firestore trigger on contract.status = "signed"
   - Auto-create 3 invoices
   - Emit chat notification
2. Cloud Function on invoice.status = "paid" (all for contract)
   - Update lead status to "complete"
   - Archive contract
3. Cloud Function on invoice sent
   - Log to chat history

**Alternative (No Cloud Functions):**
- Use Firestore transaction hooks in routes
- Check state after updates
- Trigger follow-up operations synchronously

**Files to Modify:**
- `routes/contracts.py` — After signing, create invoices + notify
- `routes/invoices.py` — After all paid, update lead
- `routes/signing.py` — After completion, trigger workflow

**Success Criteria:**
- [ ] Contract signed → 3 invoices exist 5 seconds later
- [ ] Last invoice paid → lead marked "complete"
- [ ] Workflow logged in chat without user action

---

#### 1.4 Dashboard Query & Analytics
**Status:** ⚠️ Partial  
**Impact:** MEDIUM - Users can see data but cannot query it  
**Complexity:** Moderate  
**Effort:** 2-3 days

**What's Missing:**
- Chat command: "Show unpaid invoices" → doesn't work
- Chat command: "What's my Q1 revenue?" → doesn't work
- Dashboard has no filter/search UI
- No analytics or trend data

**What Needs to Be Built:**
1. Add query builder to chat_agent
   - Parse: "unpaid", "this month", "by customer", etc.
   - Build Firestore query
   - Format as table for display
2. Add analytics functions
   - Calculate monthly revenue
   - Count by status
   - Average contract value
3. Frontend dashboard page improvements
   - Add filters (date range, status, template)
   - Add charts (revenue over time)
   - Add export (CSV)

**Files to Modify/Create:**
- `agents/analytics_agent.py` (NEW) — Query builder + aggregation
- `routes/analytics.py` (NEW) — Analytics endpoints
- `routes/chat.py` — Route to analytics_agent
- `qtc-spark/src/pages/DashboardPage.tsx` — Add filters + charts
- `qtc-spark/src/lib/api.ts` — Add analytics API methods

**Success Criteria:**
- [ ] User: "Show unpaid invoices" → table in chat
- [ ] User: "Revenue this month" → summary in chat
- [ ] Dashboard has date filter
- [ ] Dashboard shows 90-day revenue trend

---

### Priority 2: IMPORTANT (Should Have) ⚠️

#### 2.1 SMS Notification Support
**Status:** ❌ Not implemented  
**Impact:** MEDIUM - Email only; no SMS  
**Complexity:** Low  
**Effort:** 1-2 days

**What's Missing:**
- check.md mentions "email or SMS"
- Currently only email (via SMTP)

**What Needs to Be Built:**
1. Add Twilio integration (SMS provider)
2. Add SMS template for signing/invoice notifications
3. Add user preference for SMS vs. email
4. Modify signing + invoice send routes to support SMS

**Files to Modify:**
- `agents/signing_agent.py` — Add SMS option
- `agents/invoice_agent.py` — Add SMS option
- `routes/company.py` — Store SMS preference
- `.env` — Add TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_NUMBER

**Success Criteria:**
- [ ] User preference: receive signing link via SMS
- [ ] Invoice sent via SMS (short link + amount)
- [ ] SMS delivery logged in invoice record

---

#### 2.2 Advanced Contract Editing in Chat
**Status:** ⚠️ Partial  
**Impact:** MEDIUM - Can edit via UI; not via chat  
**Complexity:** Moderate  
**Effort:** 2-3 days

**What's Missing:**
- Current: "Edit with AI" dialog → edit form → save
- Desired: "Alter scope to add electrical work" → AI handles in conversation

**What Needs to Be Built:**
1. Detect "edit contract" intent in chat
2. Parse target contract + changes
3. Call GPT with: "Current contract + requested changes"
4. Generate new version
5. Show diff in chat (old→new)
6. User confirms or requests more changes

**Files to Modify:**
- `agents/chat_agent.py` — Edit intent handling
- `agents/contract_agent.py` — Diff generation
- `routes/chat.py` — Execute edit action
- `qtc-spark/src/pages/ChatPage.tsx` — Display diffs

**Success Criteria:**
- [ ] User: "Add $2,000 to phase 2 scope" → contract updated
- [ ] System shows: "Changed amount from $X to $Y"
- [ ] Multiple edits possible in single conversation

---

#### 2.3 Payment Reconciliation Enhancement
**Status:** ⚠️ Partial  
**Impact:** MEDIUM - Records updates; no customer matching  
**Complexity:** Moderate  
**Effort:** 2-3 days

**What's Missing:**
- Webhook matches by invoice_id only
- No fallback if customer pays wrong amount
- No handling of partial payments
- No overpayment tracking

**What Needs to Be Built:**
1. Improve webhook logic:
   - Check customer email matches
   - Handle partial payments (create credit)
   - Handle overpayment (refund or future credit)
2. Add reconciliation UI in dashboard
   - Show unmatched payments
   - Manual match interface
3. Add dispute handling
   - Log in invoice notes
   - Notify user in chat

**Files to Modify:**
- `routes/webhooks.py` — Enhanced payment matching
- `routes/invoices.py` — Add partial payment logic
- `qtc-spark/src/pages/InvoicesPage.tsx` — Show reconciliation status

**Success Criteria:**
- [ ] Partial payment tracked (amount + remainder)
- [ ] Overpayment creates credit for next invoice
- [ ] Customer email verified on payment
- [ ] Unmatched payments shown in dashboard

---

### Priority 3: NICE TO HAVE (Could Have) 💡

#### 3.1 Project Status Auto-Transitions
**Status:** ❌ Not implemented  
**Impact:** LOW - Would reduce manual status updates  
**Complexity:** Low  
**Effort:** 1-2 days

**What's Missing:**
- Manual status updates only
- No workflow state machine

**What to Add:**
- Lead: pending → quoted → active (on contract signed) → complete (on last invoice paid)
- Contract: draft → approved → signed → invoiced → paid
- Invoice: draft → sent → paid → archived

---

#### 3.2 PDF Export & Branded Documents
**Status:** ⚠️ Partial  
**Impact:** MEDIUM - PDFs generated; not optimized  
**Complexity:** Moderate  
**Effort:** 2-3 days

**What's Missing:**
- PDF generation works but uses basic HTML→PDF
- No brand consistency check
- No multi-page handling for long contracts
- Download filename hardcoded

**What to Improve:**
- Use reportlab or better PDF engine
- Include company logo in PDF header/footer
- Page breaks for long contracts
- Filename: {company}_{contract_type}_{date}.pdf

---

#### 3.3 Audit Logging
**Status:** ❌ Not implemented  
**Impact:** MEDIUM - No change tracking  
**Complexity:** Moderate  
**Effort:** 3-4 days

**What's Missing:**
- No log of who changed what, when
- No contract version history
- No invoice payment tracking (audit trail)

**What to Add:**
- Audit collection in Firestore
- Log on: contract create/edit, signature, payment
- Dashboard audit view
- Export audit report

---

#### 3.4 Role-Based Access Control
**Status:** ❌ Not implemented  
**Impact:** LOW - Single owner model works for MVP  
**Complexity:** High  
**Effort:** 5-7 days

**What's Missing:**
- No team member support
- No permission levels
- All users = admin

**What to Add (Future):**
- User roles: owner, drafter, accountant, viewer
- Permission matrix
- Firestore security rules per role

---

## 📋 IMPLEMENTATION ROADMAP

### Phase 1: Core Fixes (Week 1) — **MUST DO**
**Effort:** 7-8 days | **Impact:** High

1. ✅ **Conversational Command Parsing** (3-4 days)
   - Intent detection
   - State mutating actions
   
2. ✅ **Real-Time Chat Events** (3-4 days)
   - Firestore listeners
   - SSE push to chat
   
3. ✅ **Workflow Automation** (2 days, parallel)
   - Auto-create invoices on sign
   - Auto-update lead status

**Blockers:** None | **Dependencies:** None

---

### Phase 2: UX Polish (Week 2) — **SHOULD DO**
**Effort:** 5-6 days | **Impact:** Medium

1. ✅ **Dashboard Analytics** (2-3 days)
   - Query builder
   - Filters + charts
   
2. ✅ **Advanced Chat Editing** (2-3 days)
   - Diff display
   - Multi-turn editing
   
3. ✅ **SMS Support** (1 day, parallel)
   - Twilio integration

**Blockers:** Phase 1 tasks | **Dependencies:** Chat streaming works

---

### Phase 3: Business Logic (Week 3) — **COULD DO**
**Effort:** 5-6 days | **Impact:** Low-Medium

1. ✅ **Payment Reconciliation** (2-3 days)
   - Partial payments
   - Overpayment handling
   
2. ✅ **PDF Improvements** (2-3 days)
   - Brand consistency
   - Better formatting
   
3. ✅ **Status Auto-Transitions** (1 day, parallel)
   - Workflow state machine

---

## 🎯 DECISION MATRIX

| Fix | Priority | Effort | Impact | ROI | Recommendation |
|-----|----------|--------|--------|-----|-----------------|
| Conversational Commands | P1 | 3-4d | HIGH | 10x | **DO NOW** |
| Real-Time Events | P1 | 3-4d | HIGH | 9x | **DO NOW** |
| Workflow Auto-Triggers | P1 | 2d | HIGH | 8x | **DO NOW** |
| Dashboard Analytics | P2 | 2-3d | MEDIUM | 6x | **DO NEXT** |
| Chat Editing | P2 | 2-3d | MEDIUM | 5x | **DO NEXT** |
| SMS Support | P2 | 1d | MEDIUM | 4x | **DO NEXT** |
| Payment Reconciliation | P3 | 2-3d | MEDIUM | 3x | **LATER** |
| Audit Logs | P3 | 3-4d | LOW | 2x | **LATER** |
| RBAC | P3 | 5-7d | LOW | 1x | **MUCH LATER** |

---

## ✅ CHECKLIST: WHAT TO SHIP TODAY (70% feature parity)

Current system is production-ready for:

- ✅ Small teams (1-5 people)
- ✅ Single-owner workflows
- ✅ Simple projects (leads → contract → sign → invoices → payment)
- ✅ Template-based contracts
- ✅ Manual coordination (UI clicks)
- ✅ Email notifications

**Not ready for:**
- ❌ Hands-off automation
- ❌ Multi-user teams
- ❌ Conversational-first operators
- ❌ Data-driven analytics
- ❌ High-compliance industries (audit-heavy)

---

## 📊 SUMMARY TABLE

| Category | Status | Works | Needs Work | Notes |
|----------|--------|-------|-----------|-------|
| **Lead Management** | ✅ | 100% | — | Capture, store, list, delete |
| **Contract Workflow** | ⚠️ | 90% | Chat editing | Generate, edit (UI), sign, download |
| **Invoice Management** | ⚠️ | 80% | Auto-creation | Manual create, send, track |
| **Payment Processing** | ⚠️ | 75% | Reconciliation | Webhook records, no partial handling |
| **Chat Experience** | ⚠️ | 60% | Intent parsing, events | Streaming works, actions work |
| **Dashboard** | ⚠️ | 50% | Analytics, filters | Shows data, not queryable |
| **Automation** | ❌ | 0% | All | No triggers, all manual |
| **SMS** | ❌ | 0% | All | Email only |
| **Audit Logs** | ❌ | 0% | All | No change tracking |

---

## 🚀 NEXT STEPS

**Immediate (Today):**
1. Choose: Ship as-is (70%) or add Phase 1 before launch
2. If shipping: Document limitations in roadmap
3. If Phase 1: Start today, complete in 1 week

**If doing Phase 1:**
1. Assign 3 developers
2. Day 1-2: Intent parsing (1 dev)
3. Day 2-3: Real-time events (1-2 devs)
4. Day 3-4: Auto-triggers (1 dev)
5. Day 5: Integration + testing

**Communication:**
- Users: "MVP focuses on core workflow; conversational features in v1.1"
- Investors: "70% feature parity with requirements; Phase 1 adds automation"
- Team: "Phase 1 = 5 days to 95% feature parity"

---

**Document Created:** March 15, 2026  
**Last Updated:** Current session  
**Owner:** Development team  
**Status:** Ready for implementation planning
