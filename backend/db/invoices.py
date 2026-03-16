from __future__ import annotations

from google.cloud.firestore import SERVER_TIMESTAMP
from google.cloud.firestore_v1.async_document import DocumentSnapshot as AsyncDocumentSnapshot

from .client import get_db
from .models import Invoice

COLLECTION = "invoices"


def _doc_to_invoice(doc: AsyncDocumentSnapshot) -> Invoice:
    data = doc.to_dict() or {}
    data["id"] = doc.id
    # DatetimeWithNanoseconds is already a datetime subclass — accepted as-is by Pydantic
    return Invoice(**data)


async def create_invoice(data: Invoice) -> Invoice:
    """Insert a new invoice and return it with its generated id."""
    db = get_db()
    ref = db.collection(COLLECTION).document()
    payload = data.model_dump(exclude={"id", "created_at"})
    payload["created_at"] = SERVER_TIMESTAMP
    await ref.set(payload)
    snapshot = await ref.get()
    return _doc_to_invoice(snapshot)


async def get_invoice(invoice_id: str) -> Invoice | None:
    """Fetch a single invoice by id. Returns None if not found."""
    db = get_db()
    snapshot = await db.collection(COLLECTION).document(invoice_id).get()
    if not snapshot.exists:
        return None
    return _doc_to_invoice(snapshot)


async def update_invoice(invoice_id: str, updates: dict) -> Invoice:
    """Partially update an invoice. Returns the updated document."""
    updates.pop("id", None)
    updates.pop("created_at", None)
    db = get_db()
    ref = db.collection(COLLECTION).document(invoice_id)
    await ref.update(updates)
    snapshot = await ref.get()
    return _doc_to_invoice(snapshot)


async def delete_invoice(invoice_id: str) -> None:
    """Hard-delete an invoice document."""
    db = get_db()
    await db.collection(COLLECTION).document(invoice_id).delete()


async def list_invoices_by_lead(lead_id: str, status: str | None = None) -> list[Invoice]:
    """List all invoices for a lead, optionally filtered by status."""
    db = get_db()
    query = db.collection(COLLECTION).where("lead_id", "==", lead_id)
    if status is not None:
        query = query.where("status", "==", status)
    docs = query.stream()
    return [_doc_to_invoice(doc) async for doc in docs]


async def list_invoices_by_contract(contract_id: str, status: str | None = None) -> list[Invoice]:
    """List all invoices for a contract, optionally filtered by status."""
    db = get_db()
    query = db.collection(COLLECTION).where("contract_id", "==", contract_id)
    if status is not None:
        query = query.where("status", "==", status)
    docs = query.stream()
    return [_doc_to_invoice(doc) async for doc in docs]
