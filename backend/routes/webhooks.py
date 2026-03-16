import os
from datetime import datetime, timezone

import stripe
from dotenv import load_dotenv
from fastapi import APIRouter, Header, HTTPException, Request

from db.firestore_client import get_db

load_dotenv()

router = APIRouter()


@router.post("/webhooks/stripe")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(..., alias="stripe-signature"),
) -> dict:
    payload = await request.body()
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")

    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=stripe_signature,
            secret=webhook_secret,
        )
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid Stripe signature")

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        invoice_id: str = session.get("metadata", {}).get("invoice_id", "")

        if invoice_id:
            db = get_db()
            paid_at = datetime.now(timezone.utc).isoformat()
            inv_ref = db.collection("invoices").document(invoice_id)
            await inv_ref.update({"status": "paid", "paid_at": paid_at})
            print(f"Invoice {invoice_id} marked as paid")

            # Check if all invoices for the same contract are now paid → mark lead complete
            try:
                inv_snap = await inv_ref.get()
                inv_data = inv_snap.to_dict() or {}
                contract_id: str = inv_data.get("contract_id", "")
                lead_id: str = inv_data.get("lead_id", "")
                if contract_id and lead_id:
                    all_paid = True
                    async for sibling in db.collection("invoices").where("contract_id", "==", contract_id).stream():
                        if (sibling.to_dict() or {}).get("status") != "paid":
                            all_paid = False
                            break
                    if all_paid:
                        await db.collection("leads").document(lead_id).update({"status": "done"})
                        print(f"Lead {lead_id} marked as done — all invoices paid")
            except Exception as e:
                print(f"Warning: lead completion check failed — {e}")

    return {"status": "ok"}
