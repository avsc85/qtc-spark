from __future__ import annotations

from google.cloud.firestore import SERVER_TIMESTAMP
from google.cloud.firestore_v1.async_document import DocumentSnapshot as AsyncDocumentSnapshot

from .client import get_db
from .models import Lead

COLLECTION = "leads"


def _doc_to_lead(doc: AsyncDocumentSnapshot) -> Lead:
    data = doc.to_dict() or {}
    data["id"] = doc.id
    # DatetimeWithNanoseconds is already a datetime subclass — accepted as-is by Pydantic
    return Lead(**data)


async def create_lead(data: Lead) -> Lead:
    """Insert a new lead document and return it with its generated id."""
    db = get_db()
    ref = db.collection(COLLECTION).document()
    payload = data.model_dump(exclude={"id", "created_at"})
    payload["created_at"] = SERVER_TIMESTAMP
    await ref.set(payload)
    snapshot = await ref.get()
    return _doc_to_lead(snapshot)


async def get_lead(lead_id: str) -> Lead | None:
    """Fetch a single lead by id. Returns None if not found."""
    db = get_db()
    snapshot = await db.collection(COLLECTION).document(lead_id).get()
    if not snapshot.exists:
        return None
    return _doc_to_lead(snapshot)


async def update_lead(lead_id: str, updates: dict) -> Lead:
    """Partially update a lead. Returns the updated document."""
    updates.pop("id", None)
    updates.pop("created_at", None)
    db = get_db()
    ref = db.collection(COLLECTION).document(lead_id)
    await ref.update(updates)
    snapshot = await ref.get()
    return _doc_to_lead(snapshot)


async def delete_lead(lead_id: str) -> None:
    """Hard-delete a lead document."""
    db = get_db()
    await db.collection(COLLECTION).document(lead_id).delete()


async def list_leads(org_id: str, status: str | None = None) -> list[Lead]:
    """List leads for an org, optionally filtered by status."""
    db = get_db()
    query = db.collection(COLLECTION).where("org_id", "==", org_id)
    if status is not None:
        query = query.where("status", "==", status)
    docs = query.stream()
    return [_doc_to_lead(doc) async for doc in docs]
