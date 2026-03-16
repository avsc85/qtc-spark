import base64
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from google.cloud.exceptions import NotFound
from pydantic import BaseModel

from agents.lead_agent import extract_lead_data, save_lead, transcribe_audio
from db.firebase_auth import verify_token
from db.firestore_client import get_db

router = APIRouter()


class CaptureRequest(BaseModel):
    text: str | None = None
    audio_base64: str | None = None


class StatusUpdate(BaseModel):
    status: Literal["lead", "proposal", "active", "done"]


@router.post("/leads/capture")
async def capture_lead(
    body: CaptureRequest,
    token: dict = Depends(verify_token),
) -> dict:
    org_id: str = token["uid"]

    text = body.text

    if body.audio_base64:
        audio_bytes = base64.b64decode(body.audio_base64)
        text = await transcribe_audio(audio_bytes)

    if not text:
        raise HTTPException(status_code=400, detail="Provide text or audio")

    data = await extract_lead_data(text)
    lead = await save_lead(data, org_id)
    return lead


@router.get("/leads")
async def list_leads(token: dict = Depends(verify_token)) -> list[dict]:
    org_id: str = token["uid"]
    db = get_db()
    docs = db.collection("leads").where("org_id", "==", org_id).stream()
    leads = []
    async for doc in docs:
        lead = doc.to_dict() or {}
        lead["id"] = doc.id
        if hasattr(lead.get("created_at"), "isoformat"):
            lead["created_at"] = lead["created_at"].isoformat()
        else:
            lead.pop("created_at", None)
        leads.append(lead)
    leads.sort(key=lambda lead: lead.get("created_at") or "", reverse=True)
    return leads


@router.patch("/leads/{lead_id}/status")
async def update_lead_status(
    lead_id: str,
    body: StatusUpdate,
    _token: dict = Depends(verify_token),
) -> dict:
    db = get_db()
    ref = db.collection("leads").document(lead_id)
    try:
        await ref.update({"status": body.status})
    except NotFound:
        raise HTTPException(status_code=404, detail="Lead not found")
    snapshot = await ref.get()
    lead = snapshot.to_dict() or {}
    lead["id"] = ref.id
    if hasattr(lead.get("created_at"), "isoformat"):
        lead["created_at"] = lead["created_at"].isoformat()
    else:
        lead.pop("created_at", None)
    return lead


@router.delete("/leads/{lead_id}")
async def delete_lead(
    lead_id: str,
    token: dict = Depends(verify_token),
) -> dict:
    """Delete a lead and related contracts, invoices, and signing tokens for the same org."""
    org_id: str = token["uid"]
    db = get_db()

    lead_ref = db.collection("leads").document(lead_id)
    lead_snap = await lead_ref.get()
    if not lead_snap.exists:
        raise HTTPException(status_code=404, detail="Lead not found")

    lead = lead_snap.to_dict() or {}
    if lead.get("org_id") != org_id:
        raise HTTPException(status_code=403, detail="Forbidden")

    contract_ids: list[str] = []
    contract_docs = db.collection("contracts").where("lead_id", "==", lead_id).stream()
    async for contract_doc in contract_docs:
        contract = contract_doc.to_dict() or {}
        if contract.get("org_id") != org_id:
            continue

        contract_ids.append(contract_doc.id)

        # Delete signing tokens related to this contract
        token_docs = db.collection("signing_tokens").where("contract_id", "==", contract_doc.id).stream()
        async for token_doc in token_docs:
            signing = token_doc.to_dict() or {}
            if signing.get("org_id") == org_id:
                await token_doc.reference.delete()

        await contract_doc.reference.delete()

    # Delete all invoices tied to the lead
    invoice_docs = db.collection("invoices").where("lead_id", "==", lead_id).stream()
    async for invoice_doc in invoice_docs:
        invoice = invoice_doc.to_dict() or {}
        if invoice.get("org_id") == org_id:
            await invoice_doc.reference.delete()

    await lead_ref.delete()
    return {"ok": True, "deleted_lead_id": lead_id, "deleted_contract_ids": contract_ids}
