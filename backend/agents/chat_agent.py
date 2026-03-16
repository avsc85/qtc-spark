import asyncio
import os
from collections.abc import AsyncGenerator

from dotenv import load_dotenv
from google.cloud.firestore import SERVER_TIMESTAMP
from openai import AsyncOpenAI

from db.firestore_client import get_db

load_dotenv()

_client: AsyncOpenAI | None = None


def _get_openai() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _client


async def get_conversation_history(session_id: str, limit: int = 10) -> list[dict]:
    """
    Fetch the last `limit` messages for a session in chronological order.
    Returns list of {role, content} dicts ready for the OpenAI messages array.
    """
    db = get_db()
    docs = db.collection("messages").where("session_id", "==", session_id).stream()
    messages = []
    async for doc in docs:
        data = doc.to_dict() or {}
        messages.append(
            {
                "role": data.get("role", "user"),
                "content": data.get("content", ""),
                "created_at": data.get("created_at"),
            }
        )

    def _ts_key(val: object) -> float:
        if val is None:
            return 0.0
        if hasattr(val, "timestamp"):
            return val.timestamp()
        try:
            from datetime import datetime as _dt
            return _dt.fromisoformat(str(val)).timestamp()
        except Exception:
            return 0.0

    messages.sort(key=lambda m: _ts_key(m.get("created_at")), reverse=True)
    messages = messages[:limit]
    for m in messages:
        m.pop("created_at", None)

    messages.reverse()  # chronological order for GPT
    return messages


async def save_message(
    session_id: str,
    project_id: str,
    role: str,
    content: str,
    org_id: str,
) -> None:
    """Persist a single chat message to Firestore and update session record."""
    db = get_db()
    ref = db.collection("messages").document()
    await ref.set(
        {
            "session_id": session_id,
            "project_id": project_id,
            "role": role,
            "content": content,
            "org_id": org_id,
            "created_at": SERVER_TIMESTAMP,
        }
    )
    # Upsert session metadata so the sessions list stays current
    await db.collection("chat_sessions").document(session_id).set(
        {
            "session_id": session_id,
            "project_id": project_id,
            "org_id": org_id,
            "updated_at": SERVER_TIMESTAMP,
            "last_preview": content[:120],
        },
        merge=True,
    )


def build_system_prompt(project_id: str, lead_data: dict | None = None) -> str:
    """Return the system prompt that gives the chat agent its persona and action vocabulary."""
    prompt = (
        "You are an AI operations assistant for a construction and design business. "
        "You help the owner manage their full workflow: leads, quotes, contracts, invoices, and payments. "
        f"Active project ID: {project_id}\n\n"
    )

    if lead_data:
        prompt += (
            "CURRENT PROJECT CONTEXT (already on file — do NOT ask the user for this information again):\n"
            f"  Customer Name: {lead_data.get('customer_name', '')}\n"
            f"  Email: {lead_data.get('email', '')}\n"
            f"  Phone: {lead_data.get('phone', '')}\n"
            f"  City: {lead_data.get('city', '')}\n"
            f"  Project Type: {lead_data.get('project_type', '')}\n"
            f"  Quote Amount: ${lead_data.get('quote_amount', '')}\n"
            f"  Status: {lead_data.get('status', '')}\n"
            f"  Notes: {lead_data.get('notes', '')}\n\n"
        )

    prompt += (
        "You can take these actions when the user requests them. "
        "When taking an action, end your response with a JSON block on its own line like this:\n"
        'ACTION: {"action": "action_name", "data": {...}}\n\n'
        "Available actions:\n"
        "- create_lead: data needs customer_name, city, project_type, quote_amount\n"
        "- generate_contract: data needs lead_id, template_name\n"
        "- send_invoice: data needs invoice_id\n"
        "- get_leads: no data needed\n"
        "- get_invoices: no data needed — list all invoices (filter by status if needed)\n"
        "- get_contracts: no data needed — list all contracts with status\n"
        "- create_invoices_from_contract: data needs contract_id — auto-creates 3 milestone invoices\n\n"
        "Rules:\n"
        "- Be concise and direct\n"
        "- Always confirm before taking financial actions\n"
        "- The ACTION line must be the very last line of your response and must not appear in the main text\n"
        "- NEVER write ACTION JSON inside the conversational text — only as the standalone last line\n"
        "- If you are not taking an action, do NOT include an ACTION block\n"
        "- Do NOT ask for information that is already in the project context above\n"
        "- Speak like a helpful business assistant, not a robot"
    )
    return prompt


async def stream_chat(
    message: str,
    session_id: str,
    project_id: str,
    org_id: str,
) -> AsyncGenerator[str, None]:
    """
    Stream a GPT-4o response for the given user message.
    - Loads conversation history from Firestore
    - Saves user message to Firestore (fire and forget)
    - Yields response text chunks as they arrive
    - Saves complete assistant response to Firestore when stream finishes
    """
    # Fetch lead context so GPT won't re-ask for info already on file
    lead_data: dict | None = None
    if project_id:
        db = get_db()
        snap = await db.collection("leads").document(project_id).get()
        if snap.exists:
            lead_data = snap.to_dict()

    history = await get_conversation_history(session_id)

    messages = [
        {"role": "system", "content": build_system_prompt(project_id, lead_data)},
        *history,
        {"role": "user", "content": message},
    ]

    # Save user message — fire and forget, don't block streaming
    asyncio.create_task(
        save_message(session_id, project_id, "user", message, org_id)
    )

    stream = await _get_openai().chat.completions.create(
        model="gpt-4o",
        messages=messages,
        stream=True,
    )

    full_response = []

    async for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            full_response.append(delta)
            yield delta

    # Save complete assistant response after stream ends
    complete_response = "".join(full_response)
    await save_message(session_id, project_id, "assistant", complete_response, org_id)
