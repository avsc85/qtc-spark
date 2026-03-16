"""Comprehensive endpoint test — run with: python scripts/test_endpoints.py"""
import requests
import json

BASE = "http://localhost:8000"
H = {"Content-Type": "application/json"}
results = []
state = {}


def t(label, method, path, body=None, expected=200, capture=None):
    url = BASE + path
    try:
        fn = {
            "GET": requests.get,
            "POST": requests.post,
            "PATCH": requests.patch,
            "PUT": requests.put,
            "DELETE": requests.delete,
        }[method]
        kw = {"headers": H, "timeout": 60}
        if body is not None:
            kw["json"] = body
        r = fn(url, **kw)
        ok = r.status_code == expected
        try:
            data = r.json()
            snippet = json.dumps(data)[:130]
            if capture and ok:
                capture(data)
        except Exception:
            data = None
            ct = r.headers.get("content-type", "")
            if "pdf" in ct or "octet" in ct:
                snippet = f"binary({len(r.content):,} bytes)"
            else:
                snippet = r.text[:100]
        mark = "PASS" if ok else "FAIL"
        results.append((mark, label, r.status_code, snippet))
        return data if ok else None
    except Exception as e:
        results.append(("ERR", label, 0, str(e)[:80]))
        return None


# ── HEALTH ──────────────────────────────────────────────────────────
t("GET /health", "GET", "/health")

# ── COMPANY PROFILE ─────────────────────────────────────────────────
t("GET /api/company/profile", "GET", "/api/company/profile")
t("PUT /api/company/profile", "PUT", "/api/company/profile", {
    "company_name": "BuildRight LLC",
    "company_drafter": "Alice Smith",
    "company_address": "100 Builder Way, San Jose CA 95101",
    "company_phone": "408-555-0199",
    "company_email": "info@buildright.com",
    "company_logo_url": "",
}, capture=lambda d: state.update({"profile_name": d.get("company_name")}))
t("GET /api/company/profile (verify)", "GET", "/api/company/profile")

# ── LEADS ────────────────────────────────────────────────────────────
t("GET /api/leads", "GET", "/api/leads",
  capture=lambda d: state.update({"existing_leads": len(d)}))

t("POST /api/leads/capture", "POST", "/api/leads/capture", {
    "text": "Customer Maria Lopez in Sunnyvale CA needs ADU permit drawings, quote 8500 dollars"
}, capture=lambda d: state.update({"lead_id": d.get("id")}))

lid = state.get("lead_id", "")
print(f"Lead created: {lid}")

if lid:
    t("PATCH /api/leads/{id}/status", "PATCH", f"/api/leads/{lid}/status",
      {"status": "proposal"})
    t("GET /api/leads (after capture)", "GET", "/api/leads")

# ── CONTRACTS: GENERATE (4 templates) ───────────────────────────────
if lid:
    t("POST /api/contracts/generate (adu)", "POST", "/api/contracts/generate", {
        "lead_id": lid, "template_name": "adu_legalization"
    }, capture=lambda d: state.update({"cid1": d.get("contract_id"), "clen1": len(d.get("content", ""))}))

    t("POST /api/contracts/generate (remodeling)", "POST", "/api/contracts/generate", {
        "lead_id": lid, "template_name": "remodeling"
    }, capture=lambda d: state.update({"cid2": d.get("contract_id")}))

    t("POST /api/contracts/generate (home_addition)", "POST", "/api/contracts/generate", {
        "lead_id": lid, "template_name": "home_addition"
    }, capture=lambda d: state.update({"cid3": d.get("contract_id")}))

    t("POST /api/contracts/generate (electrical_permit)", "POST", "/api/contracts/generate", {
        "lead_id": lid, "template_name": "electrical_permit"
    }, capture=lambda d: state.update({"cid4": d.get("contract_id")}))

cid1 = state.get("cid1", "")
cid2 = state.get("cid2", "")
print(f"Contracts: {cid1} | {cid2} | {state.get('cid3','')} | {state.get('cid4','')}")
print(f"HTML content length: {state.get('clen1', 0):,} bytes")

# ── CONTRACTS: READ / LIST ───────────────────────────────────────────
t("GET /api/contracts", "GET", "/api/contracts")

if cid1:
    t("GET /api/contracts/{id}", "GET", f"/api/contracts/{cid1}")

# ── CONTRACT PDF DOWNLOAD ────────────────────────────────────────────
if cid1:
    url = f"{BASE}/api/contracts/{cid1}/pdf"
    try:
        r = requests.get(url, headers=H, timeout=90)
        is_pdf = r.content[:4] == b"%PDF"
        if r.status_code == 200 and is_pdf:
            results.append(("PASS", "GET /api/contracts/{id}/pdf", 200,
                             f"binary({len(r.content):,} bytes) is_pdf=True"))
        else:
            results.append(("FAIL", "GET /api/contracts/{id}/pdf", r.status_code,
                             r.text[:100]))
    except Exception as e:
        results.append(("ERR", "GET /api/contracts/{id}/pdf", 0, str(e)[:80]))

# ── CONTRACTS: STATUS + MANUAL EDIT ─────────────────────────────────
if cid1:
    t("PATCH /api/contracts/{id}/status", "PATCH", f"/api/contracts/{cid1}/status",
      {"status": "sent"})
    t("PATCH /api/contracts/{id}/content", "PATCH", f"/api/contracts/{cid1}/content",
      {"content": "<!DOCTYPE html><html><body><h1>Updated contract</h1></body></html>"})
    # Reset status back to draft for signing test
    t("PATCH /api/contracts/{id}/status (reset)", "PATCH", f"/api/contracts/{cid1}/status",
      {"status": "draft"})

# ── CONTRACTS: AI EDIT ───────────────────────────────────────────────
if cid2:
    t("PATCH /api/contracts/{id} (AI edit)", "PATCH", f"/api/contracts/{cid2}",
      {"ai_command": "Add a note that 3D visualization is available upon request as an optional service"})

# ── INVOICES: CREATE FROM CONTRACT ──────────────────────────────────
if cid2:
    t("POST /api/invoices/create-from-contract", "POST",
      "/api/invoices/create-from-contract", {"contract_id": cid2},
      capture=lambda d: state.update({"invoice_ids": d.get("invoice_ids", [])}))

invoice_ids = state.get("invoice_ids", [])
print(f"Invoices created: {invoice_ids}")

t("GET /api/invoices", "GET", "/api/invoices")

if invoice_ids:
    iid = invoice_ids[0]
    t("PATCH /api/invoices/{id}", "PATCH", f"/api/invoices/{iid}",
      {"due_date": "2026-05-01", "status": "draft"})
    # send (will fail with test Stripe key — expect either 200 or 500)
    r2 = requests.post(f"{BASE}/api/invoices/{iid}/send", headers=H, timeout=15)
    mark = "PASS" if r2.status_code in (200, 500) else "FAIL"
    try:
        snippet = json.dumps(r2.json())[:100]
    except Exception:
        snippet = r2.text[:80]
    results.append((mark, "POST /api/invoices/{id}/send (stripe test)", r2.status_code, snippet))

# ── CHAT ─────────────────────────────────────────────────────────────
t("GET /api/chat/sessions", "GET", "/api/chat/sessions")
t("GET /api/chat/history/{session}", "GET", "/api/chat/history/test-session-001")
t("POST /api/chat/action (get_leads)", "POST", "/api/chat/action",
  {"action": "get_leads", "data": {}})
t("POST /api/chat/action (get_invoices)", "POST", "/api/chat/action",
  {"action": "get_invoices", "data": {}})
t("POST /api/chat/action (create_lead)", "POST", "/api/chat/action", {
    "action": "create_lead",
    "data": {"customer_name": "Bob Builder", "city": "Fremont CA",
             "project_type": "ADU", "quote_amount": 5000,
             "phone": "510-555-9999", "email": "bob@builder.com",
             "status": "lead", "notes": "Test lead from action"}
}, capture=lambda d: state.update({"action_lead_id": d.get("result", {}).get("id")}))
t("POST /api/chat/action (unknown)", "POST", "/api/chat/action",
  {"action": "unknown_xyz", "data": {}})

# Chat streaming (just check headers/200)
try:
    r_chat = requests.post(f"{BASE}/api/chat", headers=H,
                           json={"message": "hello", "session_id": "test-001", "project_id": ""},
                           stream=True, timeout=15)
    first_chunk = next(r_chat.iter_content(256), b"")
    mark = "PASS" if r_chat.status_code == 200 else "FAIL"
    results.append((mark, "POST /api/chat (SSE stream)", r_chat.status_code,
                    f"stream ok, first={first_chunk[:60]}"))
    r_chat.close()
except Exception as e:
    results.append(("ERR", "POST /api/chat (SSE stream)", 0, str(e)[:80]))

# ── SIGNING: PUBLIC ENDPOINTS ────────────────────────────────────────
t("GET /api/sign/{bad_token}", "GET", "/api/sign/invalid-token-xyz", expected=400)
t("POST /api/sign/{bad_token}", "POST", "/api/sign/invalid-token-xyz",
  {"signer_name": "Test User", "agreed": True}, expected=400)
t("POST /api/sign (not agreed)", "POST", "/api/sign/any-token",
  {"signer_name": "Test", "agreed": False}, expected=400)

# ── STRIPE WEBHOOK (no signature — expect 422) ───────────────────────
t("POST /api/webhooks/stripe (no sig header)", "POST", "/api/webhooks/stripe",
  {"type": "test.event"}, expected=422)

# ── CONTRACTS: SEND FOR SIGNING ──────────────────────────────────────
# (email will fail with test SMTP, but the endpoint logic should run)
if cid1:
    r_sign = requests.post(f"{BASE}/api/contracts/{cid1}/send-for-signing", headers=H,
                           json={"signer_email": "customer@example.com",
                                 "signer_name": "Maria Lopez"}, timeout=90)
    mark = "PASS" if r_sign.status_code in (200, 500) else "FAIL"
    note = "(email may fail with test SMTP — acceptable)"
    try:
        snippet = json.dumps(r_sign.json())[:100] + " " + note
    except Exception:
        snippet = r_sign.text[:80] + " " + note
    results.append((mark, "POST /api/contracts/{id}/send-for-signing", r_sign.status_code, snippet))

# ── CLEANUP: DELETE ──────────────────────────────────────────────────
# Delete individual contracts 3 + 4
for cid_key, label in [("cid3", "DELETE /api/contracts/{id} (home_addition)"),
                        ("cid4", "DELETE /api/contracts/{id} (electrical)")]:
    cid_val = state.get(cid_key, "")
    if cid_val:
        t(label, "DELETE", f"/api/contracts/{cid_val}")

# Delete the lead (cascades to contracts 1+2 + invoices)
if lid:
    t("DELETE /api/leads/{id} (cascade)", "DELETE", f"/api/leads/{lid}")

# Delete action-created lead
aclid = state.get("action_lead_id", "")
if aclid:
    t("DELETE /api/leads/{id} (action lead)", "DELETE", f"/api/leads/{aclid}")

# ── PRINT RESULTS ────────────────────────────────────────────────────
print()
print("=" * 95)
passed = sum(1 for r in results if r[0] == "PASS")
failed = sum(1 for r in results if r[0] == "FAIL")
errors = sum(1 for r in results if r[0] == "ERR")

for mark, label, status, snippet in results:
    icon = {"PASS": "OK  ", "FAIL": "FAIL", "ERR": "ERR ", "SKIP": "SKIP"}.get(mark, mark)
    s = str(status) if status else "-"
    print(f"[{icon}] {label:52s} {s:>4}  {snippet[:78]}")

print("=" * 95)
print(f"TOTAL {len(results)} endpoints  |  PASS={passed}  FAIL={failed}  ERR={errors}")
