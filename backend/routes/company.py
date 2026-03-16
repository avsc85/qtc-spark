"""Company profile — stores drafter/company info in Firestore for use in contracts."""
import asyncio
import os

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile
from pydantic import BaseModel

from db.firebase_auth import verify_token
from db.firestore_client import get_db
from db.storage_client import get_bucket

router = APIRouter()

DEFAULTS = {
    "company_name": "",
    "company_drafter": "",
    "company_address": "",
    "company_phone": "",
    "company_email": "",
    "company_logo_url": "",
}

_ALLOWED_TYPES = {
    "image/png": "png",
    "image/jpeg": "jpg",
    "image/jpg": "jpg",
    "image/webp": "webp",
    "image/svg+xml": "svg",
}


class CompanyProfile(BaseModel):
    company_name: str = ""
    company_drafter: str = ""
    company_address: str = ""
    company_phone: str = ""
    company_email: str = ""
    company_logo_url: str = ""
    drafter_signature: str = ""  # base64 data URL — saved once, auto-injected into PDFs


@router.get("/company/profile")
async def get_company_profile(token: dict = Depends(verify_token)) -> dict:
    org_id: str = token["uid"]
    db = get_db()
    snap = await db.collection("company_profiles").document(org_id).get()
    if not snap.exists:
        return {**DEFAULTS, "org_id": org_id}
    profile = snap.to_dict() or {}
    profile["org_id"] = org_id
    return profile


@router.put("/company/profile")
async def save_company_profile(
    body: CompanyProfile,
    token: dict = Depends(verify_token),
) -> dict:
    org_id: str = token["uid"]
    db = get_db()
    payload = body.model_dump()
    payload["org_id"] = org_id
    await db.collection("company_profiles").document(org_id).set(payload, merge=True)
    return payload


@router.post("/company/logo")
async def upload_company_logo(
    file: UploadFile = File(...),
    token: dict = Depends(verify_token),
) -> dict:
    """Upload a company logo (PNG/JPG/WebP/SVG) to GCS.
    Stores it at logos/{org_id}.{ext} and returns the serve URL.
    The URL is also auto-saved to the company profile."""
    org_id: str = token["uid"]
    content_type = file.content_type or ""

    if content_type not in _ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{content_type}'. Use PNG, JPG, WebP, or SVG.",
        )

    ext = _ALLOWED_TYPES[content_type]
    gcs_path = f"logos/{org_id}.{ext}"
    file_bytes = await file.read()

    # Upload to GCS (sync in executor)
    def _upload() -> None:
        blob = get_bucket().blob(gcs_path)
        blob.upload_from_string(file_bytes, content_type=content_type)

    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, _upload)

    # Build the serve URL — routes through our API so no GCS ACL needed
    app_base = os.getenv("APP_BASE_URL", "http://localhost:8000")
    logo_url = f"{app_base}/api/company/logo/{org_id}"

    # Auto-save logo_url into the Firestore company profile
    db = get_db()
    await db.collection("company_profiles").document(org_id).set(
        {"company_logo_url": logo_url}, merge=True
    )

    return {"logo_url": logo_url}


@router.get("/company/logo/{org_id}")
async def serve_company_logo(org_id: str) -> Response:
    """Serve the stored company logo directly from GCS.
    No auth required — logos are branding assets used in PDFs and emails."""

    def _fetch() -> tuple[bytes | None, str]:
        bucket = get_bucket()
        for ext, ct in [("png", "image/png"), ("jpg", "image/jpeg"),
                         ("webp", "image/webp"), ("svg", "image/svg+xml")]:
            blob = bucket.blob(f"logos/{org_id}.{ext}")
            if blob.exists():
                return blob.download_as_bytes(), ct
        return None, ""

    loop = asyncio.get_running_loop()
    data, content_type = await loop.run_in_executor(None, _fetch)

    if data is None:
        raise HTTPException(status_code=404, detail="Logo not found")

    return Response(
        content=data,
        media_type=content_type,
        headers={"Cache-Control": "public, max-age=86400"},
    )


async def get_profile_for_org(org_id: str) -> dict:
    """Internal helper — fetch company profile dict for use in contract generation."""
    db = get_db()
    snap = await db.collection("company_profiles").document(org_id).get()
    if snap.exists:
        return snap.to_dict() or {}
    return {**DEFAULTS}
