"""
Delete ALL contracts, their invoices, and signing tokens from Firestore.
Also removes signed PDF files from GCS contracts/ folder.

Usage:
    python scripts/clear_contracts.py            # dry run (lists what will be deleted)
    python scripts/clear_contracts.py --confirm  # actually deletes

WARNING: This is irreversible. Run without --confirm first to review.
"""
import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

import argparse
from google.cloud import firestore, storage


BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "qtc-documents-zheight")


async def clear_all(confirm: bool) -> None:
    db = firestore.AsyncClient(
        project=os.getenv("FIRESTORE_PROJECT_ID", "quotetocash"),
        database=os.getenv("FIRESTORE_DATABASE", "qtc-database"),
    )
    gcs = storage.Client()
    bucket = gcs.bucket(BUCKET_NAME)

    action = "Deleting" if confirm else "DRY RUN — would delete"

    # ── Contracts ─────────────────────────────────────────
    contract_ids: list[str] = []
    async for doc in db.collection("contracts").stream():
        contract_ids.append(doc.id)
        print(f"  {action}: contract/{doc.id}")
        if confirm:
            await doc.reference.delete()

    print(f"\n  Total contracts: {len(contract_ids)}")

    # ── Invoices linked to those contracts ────────────────
    invoice_count = 0
    for cid in contract_ids:
        async for doc in db.collection("invoices").where("contract_id", "==", cid).stream():
            invoice_count += 1
            print(f"  {action}: invoice/{doc.id}  (contract={cid[:8]}…)")
            if confirm:
                await doc.reference.delete()

    # Also catch orphaned invoices with no valid contract
    async for doc in db.collection("invoices").stream():
        data = doc.to_dict() or {}
        if data.get("contract_id") not in contract_ids:
            invoice_count += 1
            print(f"  {action}: orphaned invoice/{doc.id}")
            if confirm:
                await doc.reference.delete()

    print(f"  Total invoices: {invoice_count}")

    # ── Signing tokens ────────────────────────────────────
    token_count = 0
    for cid in contract_ids:
        async for doc in db.collection("signing_tokens").where("contract_id", "==", cid).stream():
            token_count += 1
            print(f"  {action}: signing_token/{doc.id}")
            if confirm:
                await doc.reference.delete()

    print(f"  Total signing tokens: {token_count}")

    # ── GCS signed PDFs ───────────────────────────────────
    gcs_count = 0
    for blob in bucket.list_blobs(prefix="contracts/"):
        gcs_count += 1
        print(f"  {action}: gs://{BUCKET_NAME}/{blob.name}")
        if confirm:
            blob.delete()

    print(f"  Total GCS contract files: {gcs_count}")

    if not confirm:
        print(
            f"\nDRY RUN complete. Re-run with --confirm to permanently delete "
            f"{len(contract_ids)} contracts, {invoice_count} invoices, "
            f"{token_count} tokens, {gcs_count} GCS files."
        )
    else:
        print(
            f"\nCleanup complete. Deleted {len(contract_ids)} contracts, "
            f"{invoice_count} invoices, {token_count} tokens, {gcs_count} GCS files."
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Clear all contracts from Firestore + GCS.")
    parser.add_argument("--confirm", action="store_true", help="Actually delete (default is dry run)")
    args = parser.parse_args()

    if args.confirm:
        print("WARNING: DELETING all contracts, invoices, signing tokens, and GCS PDFs...\n")
    else:
        print("DRY RUN — listing what would be deleted (pass --confirm to actually delete)\n")

    asyncio.run(clear_all(confirm=args.confirm))
