"""
Upload all 4 contract templates to GCS.

Usage:
    python scripts/upload_templates.py

Requires GCS_BUCKET_NAME env var and ADC (gcloud auth application-default login).
"""
import os
import sys
from pathlib import Path

# Allow imports from project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from google.cloud import storage

TEMPLATES = [
    "adu_legalization",
    "remodeling",
    "home_addition",
    "electrical_permit",
]

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "qtc-documents-zheight")


def upload_templates() -> None:
    client = storage.Client()
    bucket = client.bucket(BUCKET_NAME)

    for name in TEMPLATES:
        local_path = TEMPLATES_DIR / f"{name}.txt"
        if not local_path.exists():
            print(f"  MISSING locally: {local_path}")
            continue

        gcs_path = f"templates/{name}.txt"
        blob = bucket.blob(gcs_path)
        blob.upload_from_filename(str(local_path), content_type="text/plain; charset=utf-8")
        print(f"  OK Uploaded: gs://{BUCKET_NAME}/{gcs_path}")

    # Remove old .docx templates if they exist
    print("\nCleaning up old .docx templates from GCS...")
    for name in TEMPLATES:
        docx_path = f"templates/{name}.docx"
        blob = bucket.blob(docx_path)
        if blob.exists():
            blob.delete()
            print(f"  Deleted old: gs://{BUCKET_NAME}/{docx_path}")

    print("\nDone. Templates are live in GCS.")


if __name__ == "__main__":
    print(f"Uploading templates to gs://{BUCKET_NAME}/templates/\n")
    upload_templates()
