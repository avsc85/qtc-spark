import os

import firebase_admin
from fastapi import Header, HTTPException
from firebase_admin import auth

# Initialize Firebase app using ADC (no JSON key file)
if not firebase_admin._apps:
    firebase_admin.initialize_app()

_DISABLE_AUTH = os.getenv("DISABLE_AUTH", "").lower() in ("1", "true", "yes")


async def verify_token(authorization: str = Header(default="")) -> dict:
    """
    FastAPI dependency. Extracts and verifies a Firebase Bearer token.
    Returns the decoded token dict (contains uid, email, etc.).
    Raises HTTP 401 if the token is missing or invalid.
    Set DISABLE_AUTH=true in .env to skip verification for local testing.
    """
    if _DISABLE_AUTH:
        return {"uid": "local-test-user", "email": "test@localhost"}

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header format")

    token = authorization.removeprefix("Bearer ")

    try:
        decoded = auth.verify_id_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return decoded
