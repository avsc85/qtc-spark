from __future__ import annotations

from google.cloud.firestore import SERVER_TIMESTAMP
from google.cloud.firestore_v1.async_document import DocumentSnapshot as AsyncDocumentSnapshot

from .client import get_db
from .models import Contract

COLLECTION = "contracts"


def _doc_to_contract(doc: AsyncDocumentSnapshot) -> Contract:
    data = doc.to_dict() or {}
    data["id"] = doc.id
    # DatetimeWithNanoseconds is already a datetime subclass — accepted as-is by Pydantic
    return Contract(**data)


async def create_contract(data: Contract) -> Contract:
    """Insert a new contract and return it with its generated id."""
    db = get_db()
    ref = db.collection(COLLECTION).document()
    payload = data.model_dump(exclude={"id", "created_at"})
    payload["created_at"] = SERVER_TIMESTAMP
    await ref.set(payload)
    snapshot = await ref.get()
    return _doc_to_contract(snapshot)


async def get_contract(contract_id: str) -> Contract | None:
    """Fetch a single contract by id. Returns None if not found."""
    db = get_db()
    snapshot = await db.collection(COLLECTION).document(contract_id).get()
    if not snapshot.exists:
        return None
    return _doc_to_contract(snapshot)


async def update_contract(contract_id: str, updates: dict) -> Contract:
    """Partially update a contract. Returns the updated document."""
    updates.pop("id", None)
    updates.pop("created_at", None)
    db = get_db()
    ref = db.collection(COLLECTION).document(contract_id)
    await ref.update(updates)
    snapshot = await ref.get()
    return _doc_to_contract(snapshot)


async def delete_contract(contract_id: str) -> None:
    """Hard-delete a contract document."""
    db = get_db()
    await db.collection(COLLECTION).document(contract_id).delete()


async def list_contracts(lead_id: str, status: str | None = None) -> list[Contract]:
    """List contracts for a lead, optionally filtered by status."""
    db = get_db()
    query = db.collection(COLLECTION).where("lead_id", "==", lead_id)
    if status is not None:
        query = query.where("status", "==", status)
    docs = query.stream()
    return [_doc_to_contract(doc) async for doc in docs]
