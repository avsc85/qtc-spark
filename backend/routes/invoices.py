from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from google.cloud.exceptions import NotFound
from pydantic import BaseModel

from agents.invoice_agent import create_invoices, create_stripe_payment_link, extract_payment_schedule, send_invoice_email
from db.firebase_auth import verify_token
from db.firestore_client import get_db

router = APIRouter()


class CreateFromContractRequest(BaseModel):
    contract_id: str


class InvoiceUpdate(BaseModel):
    status: str | None = None
    due_date: str | None = None
    amount: float | None = None


def _serialize(doc: dict) -> dict:
    """Convert Firestore timestamps to ISO strings."""
    for field in ("created_at",):
        val = doc.get(field)
        if val is not None and hasattr(val, "isoformat"):
            doc[field] = val.isoformat()
    return doc


@router.post("/invoices/create-from-contract")
async def create_from_contract(
    body: CreateFromContractRequest,
    token: dict = Depends(verify_token),
) -> dict:
    org_id: str = token["uid"]
    db = get_db()

    # Fetch contract
    contract_snap = await db.collection("contracts").document(body.contract_id).get()
    if not contract_snap.exists:
        raise HTTPException(status_code=404, detail="Contract not found")
    contract = contract_snap.to_dict() or {}

    # Build payment schedule from template definition + quote amount (no GPT needed)
    quote_amount = float(contract.get("quote_amount") or 0)
    template_name = contract.get("template_name", "adu_legalization")
    milestones = extract_payment_schedule(template_name, quote_amount)  # sync — no await

    # Create one invoice per milestone
    invoice_ids = await create_invoices(
        contract_id=body.contract_id,
        lead_id=contract.get("lead_id", ""),
        org_id=org_id,
        milestones=milestones,
    )

    return {
        "invoice_ids": invoice_ids,
        "count": len(invoice_ids),
        "milestones": milestones,
    }


@router.post("/invoices/{invoice_id}/send")
async def send_invoice(
    invoice_id: str,
    token: dict = Depends(verify_token),
) -> dict:
    org_id: str = token["uid"]
    db = get_db()
    ref = db.collection("invoices").document(invoice_id)

    snap = await ref.get()
    if not snap.exists:
        raise HTTPException(status_code=404, detail="Invoice not found")
    invoice = snap.to_dict() or {}

    if invoice.get("org_id") != org_id:
        raise HTTPException(status_code=403, detail="Forbidden")

    stripe_link = await create_stripe_payment_link(
        invoice_id=invoice_id,
        amount=float(invoice.get("amount", 0)),
        description=invoice.get("milestone_name", "Invoice"),
    )

    await ref.update({"stripe_link": stripe_link, "status": "sent"})

    # Email the customer the payment link (fire and forget)
    try:
        lead_id: str = invoice.get("lead_id", "")
        if lead_id:
            lead_snap = await db.collection("leads").document(lead_id).get()
            if lead_snap.exists:
                lead = lead_snap.to_dict() or {}
                customer_email: str = lead.get("email", "")
                customer_name: str = lead.get("customer_name", "Customer")
                if customer_email:
                    # Fetch company name for the email branding
                    from routes.company import get_profile_for_org
                    profile = await get_profile_for_org(org_id)
                    company_name: str = profile.get("company_name", "")
                    await send_invoice_email(
                        customer_email=customer_email,
                        customer_name=customer_name,
                        milestone_name=invoice.get("milestone_name", "Invoice"),
                        amount=float(invoice.get("amount", 0)),
                        payment_url=stripe_link,
                        company_name=company_name,
                    )
    except Exception as e:
        print(f"Warning: invoice email failed — {e}")

    return {"invoice_id": invoice_id, "stripe_link": stripe_link, "status": "sent"}


@router.get("/invoices")
async def list_invoices(
    token: dict = Depends(verify_token),
    contract_id: str | None = None,
    status: str | None = None,
) -> list[dict]:
    org_id: str = token["uid"]
    db = get_db()

    query: Any = db.collection("invoices").where("org_id", "==", org_id)
    if contract_id:
        query = query.where("contract_id", "==", contract_id)
    if status:
        query = query.where("status", "==", status)

    docs = query.stream()
    invoices = []
    async for doc in docs:
        inv = doc.to_dict() or {}
        inv["id"] = doc.id
        invoices.append(_serialize(inv))
    invoices.sort(key=lambda inv: inv.get("created_at") or "")
    return invoices


@router.patch("/invoices/{invoice_id}")
async def update_invoice(
    invoice_id: str,
    body: InvoiceUpdate,
    _token: dict = Depends(verify_token),
) -> dict:
    db = get_db()
    ref = db.collection("invoices").document(invoice_id)

    # Build update dict from only provided fields
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    try:
        await ref.update(updates)
    except NotFound:
        raise HTTPException(status_code=404, detail="Invoice not found")

    snap = await ref.get()
    result = snap.to_dict() or {}
    result["id"] = invoice_id
    return _serialize(result)
