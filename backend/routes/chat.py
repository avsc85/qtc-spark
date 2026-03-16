from collections.abc import AsyncGenerator
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from agents.chat_agent import get_conversation_history, stream_chat
from agents.contract_agent import generate_contract, get_template, save_contract
from agents.invoice_agent import create_invoices, create_stripe_payment_link, extract_payment_schedule, send_invoice_email
from agents.lead_agent import save_lead
from db.firebase_auth import verify_token
from db.firestore_client import get_db

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    session_id: str
    project_id: str = ""


class ActionRequest(BaseModel):
    action: str
    data: dict = {}


async def _sse_generator(
    message: str,
    session_id: str,
    project_id: str,
    org_id: str,
) -> AsyncGenerator[str, None]:
    """Wrap stream_chat output as Server-Sent Events."""
    async for chunk in stream_chat(message, session_id, project_id, org_id):
        yield f"data: {chunk}\n\n"
    yield "data: [DONE]\n\n"


@router.post("/chat")
async def chat(
    body: ChatRequest,
    token: dict = Depends(verify_token),
) -> StreamingResponse:
    """
    Stream a GPT-4o chat response as Server-Sent Events.
    The frontend reads chunks in real time and watches for ACTION blocks.
    """
    org_id: str = token["uid"]
    return StreamingResponse(
        _sse_generator(body.message, body.session_id, body.project_id, org_id),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/chat/history/{session_id}")
async def chat_history(
    session_id: str,
    _token: dict = Depends(verify_token),
) -> list[dict]:
    """Return the last 50 messages for a session in chronological order."""
    return await get_conversation_history(session_id, limit=50)


@router.post("/chat/action")
async def execute_action(
    body: ActionRequest,
    token: dict = Depends(verify_token),
) -> dict:
    """
    Execute a structured action detected from a chat response ACTION block.
    Called by the frontend after parsing an ACTION: {...} line from the stream.
    """
    org_id: str = token["uid"]
    db = get_db()
    action = body.action
    data = body.data

    # --- create_lead ---
    if action == "create_lead":
        lead = await save_lead(data, org_id)
        return {"action": action, "result": lead}

    # --- generate_contract ---
    if action == "generate_contract":
        lead_id: str = data.get("lead_id", "")
        template_name: str = data.get("template_name", "adu_legalization")

        lead_snap = await db.collection("leads").document(lead_id).get()
        if not lead_snap.exists:
            raise HTTPException(status_code=404, detail=f"Lead {lead_id} not found")
        lead_data = lead_snap.to_dict() or {}
        lead_data["id"] = lead_id

        template_text = await get_template(template_name)
        content = await generate_contract(lead_data, template_text)
        contract = await save_contract(lead_id, template_name, content, org_id)
        return {"action": action, "result": contract}

    # --- send_invoice ---
    if action == "send_invoice":
        invoice_id: str = data.get("invoice_id", "")
        if not invoice_id:
            raise HTTPException(status_code=400, detail="invoice_id is required")

        ref = db.collection("invoices").document(invoice_id)
        snap = await ref.get()
        if not snap.exists:
            raise HTTPException(status_code=404, detail=f"Invoice {invoice_id} not found")
        invoice = snap.to_dict() or {}

        stripe_link = await create_stripe_payment_link(
            invoice_id=invoice_id,
            amount=float(invoice.get("amount", 0)),
            description=invoice.get("milestone_name", "Invoice"),
        )
        await ref.update({"stripe_link": stripe_link, "status": "sent"})
        return {"action": action, "result": {"invoice_id": invoice_id, "stripe_link": stripe_link}}

    # --- get_leads ---
    if action == "get_leads":
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
        return {"action": action, "result": leads}

    # --- get_invoices ---
    if action == "get_invoices":
        docs = db.collection("invoices").where("org_id", "==", org_id).stream()
        invoices = []
        async for doc in docs:
            inv = doc.to_dict() or {}
            inv["id"] = doc.id
            if hasattr(inv.get("created_at"), "isoformat"):
                inv["created_at"] = inv["created_at"].isoformat()
            else:
                inv.pop("created_at", None)
            invoices.append(inv)
        return {"action": action, "result": invoices}

    # --- get_contracts ---
    if action == "get_contracts":
        docs = db.collection("contracts").where("org_id", "==", org_id).stream()
        contracts = []
        async for doc in docs:
            c = doc.to_dict() or {}
            c["id"] = doc.id
            for field in ("created_at", "signed_at"):
                val = c.get(field)
                if val is not None and hasattr(val, "isoformat"):
                    c[field] = val.isoformat()
                else:
                    c.pop(field, None)
            # Exclude large HTML content from chat summaries
            c.pop("content", None)
            contracts.append(c)
        contracts.sort(key=lambda c: c.get("created_at") or "", reverse=True)
        return {"action": action, "result": contracts}

    # --- create_invoices_from_contract ---
    if action == "create_invoices_from_contract":
        contract_id: str = data.get("contract_id", "")
        if not contract_id:
            raise HTTPException(status_code=400, detail="contract_id is required")

        contract_snap = await db.collection("contracts").document(contract_id).get()
        if not contract_snap.exists:
            raise HTTPException(status_code=404, detail=f"Contract {contract_id} not found")
        contract_data = contract_snap.to_dict() or {}

        # Check if invoices already exist (idempotent)
        has_invoices = False
        async for _ in db.collection("invoices").where("contract_id", "==", contract_id).limit(1).stream():
            has_invoices = True
            break
        if has_invoices:
            return {"action": action, "result": {"message": "Invoices already exist for this contract"}}

        quote_amount = float(contract_data.get("quote_amount") or 0)
        template_name = contract_data.get("template_name", "adu_legalization")
        milestones = extract_payment_schedule(template_name, quote_amount)
        invoice_ids = await create_invoices(
            contract_id=contract_id,
            lead_id=contract_data.get("lead_id", ""),
            org_id=org_id,
            milestones=milestones,
        )
        return {"action": action, "result": {"invoice_ids": invoice_ids, "count": len(invoice_ids)}}

    return {"action": action, "result": None, "error": f"Unknown action: {action}"}


@router.get("/chat/sessions")
async def list_chat_sessions(
    token: dict = Depends(verify_token),
) -> list[dict]:
    """Return all chat sessions for the org, most recent first."""
    org_id: str = token["uid"]
    db = get_db()
    query: Any = db.collection("chat_sessions").where("org_id", "==", org_id)
    docs = query.stream()
    sessions = []
    async for doc in docs:
        s = doc.to_dict() or {}
        val = s.get("updated_at")
        if val is not None and hasattr(val, "isoformat"):
            s["updated_at"] = val.isoformat()
        sessions.append(s)
    sessions.sort(key=lambda s: s.get("updated_at") or "", reverse=True)
    return sessions
