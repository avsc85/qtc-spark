import asyncio
import os
from functools import partial

from dotenv import load_dotenv
from google.cloud import storage

load_dotenv()

_client: storage.Client | None = None


def _get_client() -> storage.Client:
    """Return a lazy singleton GCS client using ADC."""
    global _client
    if _client is None:
        _client = storage.Client()
    return _client


def get_bucket() -> storage.Bucket:
    """Return the configured GCS bucket."""
    bucket_name = os.getenv("GCS_BUCKET_NAME")
    return _get_client().bucket(bucket_name)


async def upload_file(content: bytes, path: str) -> str:
    """Upload bytes to GCS at the given path. Returns the GCS object path."""
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, partial(_sync_upload, content, path))
    return path


async def download_file(path: str) -> bytes:
    """Download a file from GCS by path. Returns raw bytes."""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, partial(_sync_download, path))


def _sync_upload(content: bytes, path: str) -> None:
    blob = get_bucket().blob(path)
    blob.upload_from_string(content)


def _sync_download(path: str) -> bytes:
    blob = get_bucket().blob(path)
    return blob.download_as_bytes()
