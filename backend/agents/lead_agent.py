import json
import os
import tempfile

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


async def transcribe_audio(audio_bytes: bytes) -> str:
    """Transcribe audio bytes using OpenAI Whisper. Returns transcript string."""
    with tempfile.NamedTemporaryFile(suffix=".m4a", delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name
    try:
        with open(tmp_path, "rb") as f:
            transcript = await _get_openai().audio.transcriptions.create(
                model="whisper-1",
                file=f,
                response_format="text",
            )
    finally:
        os.remove(tmp_path)
    return transcript


async def extract_lead_data(text: str) -> dict:
    """Use GPT-4o to extract structured lead fields from free-form text."""
    response = await _get_openai().chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a data extraction assistant for a construction business. "
                    "Extract customer info from the text. "
                    "Return ONLY a valid JSON object with these exact fields: "
                    "customer_name (string or null), "
                    "phone (string or null), "
                    "email (string or null), "
                    "city (string or null), "
                    "project_type (must be exactly one of: ADU, Kitchen, Addition, Permit, Other), "
                    "quote_amount (number or null), "
                    "notes (brief summary string). "
                    "No explanation. JSON only."
                ),
            },
            {"role": "user", "content": text},
        ],
        response_format={"type": "json_object"},
    )
    return json.loads(response.choices[0].message.content)


async def save_lead(data: dict, org_id: str) -> dict:
    """Save extracted lead data to Firestore. Returns saved data including generated id."""
    db = get_db()
    ref = db.collection("leads").document()
    payload = {
        **data,
        "org_id": org_id,
        "status": "lead",
        "created_at": SERVER_TIMESTAMP,
    }
    await ref.set(payload)
    snapshot = await ref.get()
    saved = snapshot.to_dict() or {}
    saved["id"] = ref.id
    # Convert Firestore timestamp to string for JSON serialisation
    if hasattr(saved.get("created_at"), "isoformat"):
        saved["created_at"] = saved["created_at"].isoformat()
    else:
        saved.pop("created_at", None)
    return saved
