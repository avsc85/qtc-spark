import os
from typing import Literal

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from google.cloud.exceptions import NotFound
from pydantic import BaseModel

from agents.contract_agent import edit_contract, render_html_contract, save_contract
from routes.company import get_profile_for_org
from agents.signing_agent import create_signing_token, send_signing_request_email
from agents.template_agent import generate_from_reference
from db.firebase_auth import verify_token
from db.firestore_client import get_db

router = APIRouter()


class GenerateRequest(BaseModel):
    lead_id: str
    template_name: str


class EditRequest(BaseModel):
    ai_command: str


class ManualEditRequest(BaseModel):
    content: str


class StatusUpdate(BaseModel):
    status: Literal["draft", "sent", "signed"]


class SendForSigningRequest(BaseModel):
    signer_email: str
    signer_name: str


def _serialize(doc: dict) -> dict:
    """Convert Firestore timestamps to ISO strings for JSON responses."""
    for field in ("created_at", "signed_at"):
        val = doc.get(field)
        if val is not None and hasattr(val, "isoformat"):
            doc[field] = val.isoformat()
    return doc


def _clean_unsigned_placeholders(html: str) -> str:
    """Replace customer date/place placeholders with blank for unsigned contract rendering."""
    return html.replace("{{customer_date}}", "").replace("{{customer_place}}", "")


@router.get("/contracts")
async def list_contracts(token: dict = Depends(verify_token)) -> list[dict]:
    """Return all contracts for the authenticated org, newest first."""
    org_id: str = token["uid"]
    db = get_db()
    docs = db.collection("contracts").where("org_id", "==", org_id).stream()
    contracts = []
    async for doc in docs:
        c = doc.to_dict() or {}
        c["id"] = doc.id
        contracts.append(_serialize(c))
    contracts.sort(key=lambda c: c.get("created_at") or "", reverse=True)
    return contracts


@router.post("/contracts/generate")
async def generate_contract_endpoint(
    body: GenerateRequest,
    token: dict = Depends(verify_token),
) -> dict:
    org_id: str = token["uid"]
    db = get_db()

    # Fetch lead
    lead_snap = await db.collection("leads").document(body.lead_id).get()
    if not lead_snap.exists:
        raise HTTPException(status_code=404, detail="Lead not found")
    lead_data = lead_snap.to_dict() or {}
    lead_data["id"] = lead_snap.id

    # Render HTML contract (no GPT — direct token replacement)
    company_profile = await get_profile_for_org(org_id)
    html_content = render_html_contract(body.template_name, lead_data, company_profile)
    raw_amount = str(lead_data.get("quote_amount", "0")).replace("$", "").replace(",", "")
    quote_amount = float(raw_amount) if raw_amount else 0.0
    contract = await save_contract(body.lead_id, body.template_name, html_content, org_id, quote_amount)

    return {
        "contract_id": contract["id"],
        "content": contract["content"],
        "status": contract["status"],
    }


@router.get("/contracts/{contract_id}/pdf")
async def download_contract_pdf(
    contract_id: str,
    token: dict = Depends(verify_token),
) -> Response:
    """Generate and download a PDF of the contract (unsigned preview)."""
    from agents.pdf_generator import html_to_pdf

    org_id: str = token["uid"]
    db = get_db()
    snap = await db.collection("contracts").document(contract_id).get()
    if not snap.exists:
        raise HTTPException(status_code=404, detail="Contract not found")

    contract = snap.to_dict() or {}
    if contract.get("org_id") != org_id:
        raise HTTPException(status_code=403, detail="Forbidden")

    html_content: str = contract.get("content", "")
    if not html_content:
        raise HTTPException(status_code=400, detail="Contract has no content")

    # Replace unfilled customer placeholders so they render as blank in PDF preview
    html_content = _clean_unsigned_placeholders(html_content)

    pdf_bytes = await html_to_pdf(html_content)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="contract-{contract_id}.pdf"'},
    )


@router.get("/contracts/{contract_id}/signed-pdf")
async def download_signed_pdf(
    contract_id: str,
    token: dict = Depends(verify_token),
) -> Response:
    """Return the signed PDF stored in GCS for a signed contract."""
    from db.storage_client import download_file

    org_id: str = token["uid"]
    db = get_db()
    snap = await db.collection("contracts").document(contract_id).get()
    if not snap.exists:
        raise HTTPException(status_code=404, detail="Contract not found")

    contract = snap.to_dict() or {}
    if contract.get("org_id") != org_id:
        raise HTTPException(status_code=403, detail="Forbidden")

    storage_path: str = contract.get("storage_path", "")
    if not storage_path:
        raise HTTPException(status_code=404, detail="No signed PDF found for this contract")

    try:
        pdf_bytes = await download_file(storage_path)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"PDF not found in storage: {e}")

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="signed-contract-{contract_id}.pdf"'},
    )


@router.patch("/contracts/{contract_id}")
async def edit_contract_endpoint(
    contract_id: str,
    body: EditRequest,
    token: dict = Depends(verify_token),
) -> dict:
    org_id: str = token["uid"]
    db = get_db()
    ref = db.collection("contracts").document(contract_id)

    snap = await ref.get()
    if not snap.exists:
        raise HTTPException(status_code=404, detail="Contract not found")

    contract = snap.to_dict() or {}
    if contract.get("org_id") != org_id:
        raise HTTPException(status_code=403, detail="Forbidden")

    current_content: str = contract.get("content", "")
    updated_content = await edit_contract(current_content, body.ai_command)

    await ref.update({"content": updated_content})
    updated_snap = await ref.get()
    result = updated_snap.to_dict() or {}
    result["id"] = contract_id
    return _serialize(result)


@router.patch("/contracts/{contract_id}/content")
async def update_contract_content_endpoint(
    contract_id: str,
    body: ManualEditRequest,
    token: dict = Depends(verify_token),
) -> dict:
    """Update contract content directly from human edits."""
    if not body.content.strip():
        raise HTTPException(status_code=400, detail="Content cannot be empty")

    org_id: str = token["uid"]
    db = get_db()
    ref = db.collection("contracts").document(contract_id)

    snap = await ref.get()
    if not snap.exists:
        raise HTTPException(status_code=404, detail="Contract not found")

    current = snap.to_dict() or {}
    if current.get("org_id") != org_id:
        raise HTTPException(status_code=403, detail="Forbidden")

    await ref.update({"content": body.content})
    updated_snap = await ref.get()
    result = updated_snap.to_dict() or {}
    result["id"] = contract_id
    return _serialize(result)


@router.get("/contracts/{contract_id}")
async def get_contract_endpoint(
    contract_id: str,
    token: dict = Depends(verify_token),
) -> dict:
    org_id: str = token["uid"]
    db = get_db()
    snap = await db.collection("contracts").document(contract_id).get()
    if not snap.exists:
        raise HTTPException(status_code=404, detail="Contract not found")
    contract = snap.to_dict() or {}
    if contract.get("org_id") != org_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    contract["id"] = contract_id
    return _serialize(contract)


@router.delete("/contracts/{contract_id}")
async def delete_contract_endpoint(
    contract_id: str,
    token: dict = Depends(verify_token),
) -> dict:
    """Delete a contract and its related invoices/signing tokens for the same org."""
    org_id: str = token["uid"]
    db = get_db()

    contract_ref = db.collection("contracts").document(contract_id)
    contract_snap = await contract_ref.get()
    if not contract_snap.exists:
        raise HTTPException(status_code=404, detail="Contract not found")

    contract = contract_snap.to_dict() or {}
    if contract.get("org_id") != org_id:
        raise HTTPException(status_code=403, detail="Forbidden")

    # Delete related invoices
    invoice_docs = db.collection("invoices").where("contract_id", "==", contract_id).stream()
    async for doc in invoice_docs:
        invoice = doc.to_dict() or {}
        if invoice.get("org_id") == org_id:
            await doc.reference.delete()

    # Delete related signing tokens
    token_docs = db.collection("signing_tokens").where("contract_id", "==", contract_id).stream()
    async for doc in token_docs:
        signing = doc.to_dict() or {}
        if signing.get("org_id") == org_id:
            await doc.reference.delete()

    await contract_ref.delete()
    return {"ok": True, "deleted_contract_id": contract_id}


@router.patch("/contracts/{contract_id}/status")
async def update_contract_status(
    contract_id: str,
    body: StatusUpdate,
    token: dict = Depends(verify_token),
) -> dict:
    org_id: str = token["uid"]
    db = get_db()
    ref = db.collection("contracts").document(contract_id)

    snap = await ref.get()
    if not snap.exists:
        raise HTTPException(status_code=404, detail="Contract not found")
    if (snap.to_dict() or {}).get("org_id") != org_id:
        raise HTTPException(status_code=403, detail="Forbidden")

    try:
        await ref.update({"status": body.status})
    except NotFound:
        raise HTTPException(status_code=404, detail="Contract not found")

    # If signed, promote the linked lead to "active"
    if body.status == "signed":
        lead_id: str = (snap.to_dict() or {}).get("lead_id", "")
        if lead_id:
            try:
                await db.collection("leads").document(lead_id).update({"status": "active"})
            except NotFound:
                pass  # Lead may have been deleted — not fatal

    updated_snap = await ref.get()
    result = updated_snap.to_dict() or {}
    result["id"] = contract_id
    return _serialize(result)


@router.post("/contracts/generate-from-reference")
async def generate_from_reference_endpoint(
    file: UploadFile = File(...),
    lead_id: str = Form(default=""),
    token: dict = Depends(verify_token),
) -> Response:
    """
    7-step smart contract generation from a reference DOCX or PDF.

    - Detects permit type automatically
    - Selects matching DOCX template from GCS
    - Extracts variable data via GPT-4o
    - Returns populated DOCX for download
    """
    org_id: str = token["uid"]
    db = get_db()

    # Load lead data if provided
    lead_data: dict = {}
    if lead_id:
        lead_snap = await db.collection("leads").document(lead_id).get()
        if lead_snap.exists:
            lead_data = lead_snap.to_dict() or {}
            lead_data["id"] = lead_snap.id

    file_bytes = await file.read()
    filename = file.filename or "reference.docx"

    docx_bytes, contract_id, permit_type = await generate_from_reference(
        reference_bytes=file_bytes,
        filename=filename,
        lead_data=lead_data,
        org_id=org_id,
    )

    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": f'attachment; filename="contract_{contract_id}.docx"',
            "X-Contract-Id": contract_id,
            "X-Permit-Type": permit_type,
        },
    )


@router.post("/contracts/{contract_id}/send-for-signing")
async def send_for_signing(
    contract_id: str,
    body: SendForSigningRequest,
    token: dict = Depends(verify_token),
) -> dict:
    """
    Generate a UUID signing token, email the customer a signing link,
    and update the contract status to 'sent'.
    """
    org_id: str = token["uid"]
    db = get_db()

    ref = db.collection("contracts").document(contract_id)
    snap = await ref.get()
    if not snap.exists:
        raise HTTPException(status_code=404, detail="Contract not found")

    contract = snap.to_dict() or {}
    if contract.get("org_id") != org_id:
        raise HTTPException(status_code=403, detail="Forbidden")

    if contract.get("status") == "signed":
        raise HTTPException(status_code=400, detail="Contract is already signed")

    # Fetch company profile so the email shows the correct company name
    company_profile = await get_profile_for_org(org_id)
    company_name: str = company_profile.get("company_name", "")

    # Create signing token in Firestore
    signing_token = await create_signing_token(
        contract_id=contract_id,
        org_id=org_id,
        signer_email=body.signer_email,
        signer_name=body.signer_name,
    )

    # Build signing URL — must point to the frontend (React app), not the API server
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
    signing_url = f"{frontend_url}/sign/{signing_token}"

    # Send email to customer with contract PDF attached
    await send_signing_request_email(
        signer_email=body.signer_email,
        signer_name=body.signer_name,
        signing_url=signing_url,
        contract_content=contract.get("content", ""),
        company_name=company_name,
    )

    # Update contract status to sent
    await ref.update({"status": "sent"})

    return {
        "contract_id": contract_id,
        "status": "sent",
        "signer_email": body.signer_email,
        "signing_url": signing_url,
    }
