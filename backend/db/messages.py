from __future__ import annotations

from google.cloud.firestore import SERVER_TIMESTAMP
from google.cloud.firestore_v1.async_document import DocumentSnapshot as AsyncDocumentSnapshot

from .client import get_db
from .models import Message

COLLECTION = "messages"


def _doc_to_message(doc: AsyncDocumentSnapshot) -> Message:
    data = doc.to_dict() or {}
    data["id"] = doc.id
    # DatetimeWithNanoseconds is already a datetime subclass — accepted as-is by Pydantic
    return Message(**data)


async def create_message(data: Message) -> Message:
    """Insert a new message and return it with its generated id."""
    db = get_db()
    ref = db.collection(COLLECTION).document()
    payload = data.model_dump(exclude={"id", "created_at"})
    payload["created_at"] = SERVER_TIMESTAMP
    await ref.set(payload)
    snapshot = await ref.get()
    return _doc_to_message(snapshot)


async def get_message(message_id: str) -> Message | None:
    """Fetch a single message by id. Returns None if not found."""
    db = get_db()
    snapshot = await db.collection(COLLECTION).document(message_id).get()
    if not snapshot.exists:
        return None
    return _doc_to_message(snapshot)


async def delete_message(message_id: str) -> None:
    """Hard-delete a message document."""
    db = get_db()
    await db.collection(COLLECTION).document(message_id).delete()


async def list_messages(session_id: str) -> list[Message]:
    """List all messages in a session, ordered by created_at ascending."""
    db = get_db()
    docs = (
        db.collection(COLLECTION)
        .where("session_id", "==", session_id)
        .order_by("created_at")
        .stream()
    )
    return [_doc_to_message(doc) async for doc in docs]


async def delete_session_messages(session_id: str) -> None:
    """Delete all messages belonging to a session."""
    db = get_db()
    docs = db.collection(COLLECTION).where("session_id", "==", session_id).stream()
    async for doc in docs:
        await doc.reference.delete()
