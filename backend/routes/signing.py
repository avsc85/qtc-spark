"""
Public e-signing endpoints — no Firebase auth required.
These URLs are shared with customers via email.
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from agents.signing_agent import (
    generate_signed_pdf,
    mark_token_used,
    send_signed_confirmation_email,
    store_signed_pdf,
    validate_signing_token,
)
from db.firestore_client import get_db

router = APIRouter()


class SignRequest(BaseModel):
    signer_name: str
    agreed: bool          # customer must explicitly agree
    signature_image: str | None = None  # base64 data URL (draw/type/upload)
    signer_place: str | None = None     # city/location from browser geolocation


@router.get("/sign/{token}")
async def get_contract_for_signing(token: str) -> dict:
    """
    Public endpoint — returns the contract text for a given signing token.
    Pre-injects the drafter signature into the HTML so the customer can see
    the company has already signed before they add their own signature.
    """
    token_doc = await validate_signing_token(token)
    contract_id: str = token_doc["contract_id"]
    org_id: str = token_doc.get("org_id", "")

    db = get_db()
    contract_snap = await db.collection("contracts").document(contract_id).get()
    if not contract_snap.exists:
        raise HTTPException(status_code=404, detail="Contract not found")

    contract = contract_snap.to_dict() or {}
    content: str = contract.get("content", "")

    # Pre-inject drafter signature into the second sig-line so customer sees it
    is_html = content.strip().startswith("<!DOCTYPE") or content.strip().startswith("<html")
    if is_html and org_id:
        try:
            profile_snap = await db.collection("company_profiles").document(org_id).get()
            drafter_sig = (profile_snap.to_dict() or {}).get("drafter_signature") or ""
            if drafter_sig:
                SIG_LINE = '<div class="sig-line"></div>'
                def _sig_img(data_url: str) -> str:
                    return (
                        f'<div class="sig-line" style="border:none;height:2.2rem;display:flex;'
                        f'align-items:flex-end;padding-bottom:2px;">'
                        f'<img src="{data_url}" alt="Signature" '
                        f'style="max-height:2rem;max-width:100%;object-fit:contain;display:block;" /></div>'
                    )
                # Inject only into the SECOND sig-line (drafter position)
                # Replace first occurrence with a temporary sentinel, inject drafter into second, restore sentinel
                SENTINEL = "<!-- __CUSTOMER_SIG_LINE__ -->"
                content = content.replace(SIG_LINE, SENTINEL, 1)
                content = content.replace(SIG_LINE, _sig_img(drafter_sig), 1)
                content = content.replace(SENTINEL, SIG_LINE, 1)
        except Exception:
            pass  # non-fatal — customer still sees the contract without drafter sig

    # Replace unfilled customer placeholders with blank so they render cleanly in the iframe
    content = content.replace("{{customer_date}}", "").replace("{{customer_place}}", "")

    return {
        "contract_id": contract_id,
        "contract_content": content,
        "customer_name": token_doc.get("signer_name") or token_doc.get("signer_email", ""),
        "expires_at": token_doc.get("expires_at", ""),
    }


@router.post("/sign/{token}")
async def submit_signature(token: str, body: SignRequest, request: Request) -> dict:
    """
    Public endpoint — customer submits their signature.
    Steps:
      1. Validate token
      2. Require explicit agreement
      3. Record signature metadata (name, timestamp, IP)
      4. Generate signed PDF
      5. Store PDF in GCS
      6. Update contract: status=signed, signed_at, storage_path
      7. Update linked lead: status=active
      8. Send confirmation emails to both parties
    """
    if not body.agreed:
        raise HTTPException(status_code=400, detail="You must agree to sign the contract")

    # Validate token (raises 400/410 if invalid/used/expired)
    token_doc = await validate_signing_token(token)
    contract_id: str = token_doc["contract_id"]
    signer_email: str = token_doc.get("signer_email", "")
    org_id: str = token_doc.get("org_id", "")

    db = get_db()

    # Fetch contract
    contract_ref = db.collection("contracts").document(contract_id)
    contract_snap = await contract_ref.get()
    if not contract_snap.exists:
        raise HTTPException(status_code=404, detail="Contract not found")
    contract = contract_snap.to_dict() or {}

    # Capture signing metadata (ESIGN Act audit trail)
    ip_address: str = request.client.host if request.client else "unknown"
    user_agent: str = request.headers.get("user-agent", "unknown")
    from datetime import datetime, timezone
    signed_at: str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    # Fetch drafter signature from company profile (stored once in Settings)
    drafter_signature: str | None = None
    try:
        profile_snap = await db.collection("company_profiles").document(org_id).get()
        drafter_signature = (profile_snap.to_dict() or {}).get("drafter_signature") or None
    except Exception:
        pass

    # Generate signed PDF — signatures injected into template placeholders
    pdf_bytes = await generate_signed_pdf(
        contract_content=contract.get("content", ""),
        signer_name=body.signer_name,
        signed_at=signed_at,
        signature_image=body.signature_image,
        drafter_signature=drafter_signature,
        signer_place=body.signer_place,
    )

    # Upload PDF to GCS
    storage_path = await store_signed_pdf(contract_id, pdf_bytes)

    # Mark token used (records name, IP, user-agent)
    await mark_token_used(token, body.signer_name, ip_address, user_agent)

    # Update contract: signed — full audit record stored
    await contract_ref.update(
        {
            "status": "signed",
            "signed_at": signed_at,
            "storage_path": storage_path,
            "signer_name": body.signer_name,
            "signer_ip": ip_address,
            "signer_user_agent": user_agent,
        }
    )

    # Promote linked lead to active
    lead_id: str = contract.get("lead_id", "")
    if lead_id:
        try:
            await db.collection("leads").document(lead_id).update({"status": "active"})
        except Exception:
            pass  # not fatal

    # Auto-create invoices if none exist yet for this contract
    try:
        from agents.invoice_agent import create_invoices, extract_payment_schedule
        has_invoices = False
        async for _ in db.collection("invoices").where("contract_id", "==", contract_id).limit(1).stream():
            has_invoices = True
            break
        if not has_invoices:
            template_name: str = contract.get("template_name", "adu_legalization")
            quote_amount: float = float(contract.get("quote_amount") or 0)
            milestones = extract_payment_schedule(template_name, quote_amount)
            await create_invoices(contract_id, lead_id, org_id, milestones)
    except Exception as e:
        print(f"Warning: auto-invoice creation failed — {e}")

    # Fetch org owner email to notify them
    org_email = ""
    try:
        org_snap = await db.collection("users").document(org_id).get()
        org_email = (org_snap.to_dict() or {}).get("email", "")
    except Exception:
        pass

    # Send confirmation emails (fire and forget — don't fail signing if email fails)
    try:
        await send_signed_confirmation_email(signer_email, org_email, body.signer_name)
    except Exception as e:
        print(f"Warning: confirmation email failed — {e}")

    return {
        "status": "signed",
        "contract_id": contract_id,
        "signer_name": body.signer_name,
        "signed_at": signed_at,
        "storage_path": storage_path,
    }
