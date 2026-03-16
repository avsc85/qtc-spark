import os

from dotenv import load_dotenv
from google.cloud import firestore

load_dotenv()

_db: firestore.AsyncClient | None = None


def get_db() -> firestore.AsyncClient:
    """Return a lazy singleton async Firestore client using ADC."""
    global _db
    if _db is None:
        _db = firestore.AsyncClient(
            project=os.getenv("GCP_PROJECT_ID"),
            database=os.getenv("FIRESTORE_DATABASE", "qtc-database"),
        )
    return _db
