import asyncio
import os
import smtplib
from datetime import date, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from functools import partial

import stripe
from dotenv import load_dotenv
from google.cloud.firestore import SERVER_TIMESTAMP

from db.firestore_client import get_db

load_dotenv()


def extract_payment_schedule(template_name: str, quote_amount: float) -> list[dict]:
    """
    Build the payment schedule from the template definition and quote amount.
    Uses the same 3-milestone structure defined in template_scopes.py.
    Returns a list of milestone dicts: [{milestone_name, amount, due_date}].
    """
    from agents.template_scopes import TEMPLATE_SCOPES

    scope = TEMPLATE_SCOPES.get(template_name, TEMPLATE_SCOPES["adu_legalization"])
    descriptions = scope["milestone_descriptions"]

    labels = ["Contract Signing", "City Submission", "Permit Approval"]
    today = date.today()
    due_offsets = [0, 30, 90]  # days from today

    third = round(quote_amount / 3, 2)
    remainder = round(quote_amount - third * 2, 2)
    amounts = [third, third, remainder]

    milestones = []
    for i, label in enumerate(labels):
        name = f"{label} — {descriptions[i]}" if i < len(descriptions) else label
        milestones.append({
            "milestone_name": name,
            "amount": amounts[i],
            "due_date": (today + timedelta(days=due_offsets[i])).isoformat(),
        })
    return milestones


async def create_invoices(
    contract_id: str,
    lead_id: str,
    org_id: str,
    milestones: list[dict],
) -> list[str]:
    """
    Create one Firestore invoice document per milestone.
    Returns a list of created document IDs.
    """
    db = get_db()
    ids: list[str] = []
    for milestone in milestones:
        ref = db.collection("invoices").document()
        await ref.set(
            {
                "contract_id": contract_id,
                "lead_id": lead_id,
                "org_id": org_id,
                "milestone_name": milestone["milestone_name"],
                "amount": float(milestone["amount"]),
                "due_date": milestone["due_date"],
                "status": "draft",
                "stripe_link": None,
                "created_at": SERVER_TIMESTAMP,
            }
        )
        ids.append(ref.id)
    return ids


async def create_stripe_payment_link(
    invoice_id: str,
    amount: float,
    description: str,
) -> str:
    """
    Create a Stripe Payment Link for a single invoice milestone.
    Returns the payment link URL.
    """
    stripe.api_key = os.getenv("STRIPE_KEY")

    price = stripe.Price.create(
        unit_amount=int(amount * 100),  # cents
        currency="usd",
        product_data={"name": description},
    )

    link = stripe.PaymentLink.create(
        line_items=[{"price": price.id, "quantity": 1}],
        metadata={"invoice_id": invoice_id},
    )

    return link.url


def _send_invoice_email_sync(
    to: str,
    customer_name: str,
    milestone_name: str,
    amount: float,
    payment_url: str,
    company_name: str,
) -> None:
    """Send an invoice notification email with the Stripe payment link. Runs synchronously."""
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_password = os.getenv("SMTP_PASSWORD", "")
    from_name = os.getenv("SMTP_FROM_NAME", company_name or "QTC Platform")

    subject = f"Invoice from {company_name or 'Your Contractor'} — ${amount:,.2f} due"
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:auto;">
      <h2 style="color:#1a1a1a;">Invoice from {company_name}</h2>
      <p>Hi {customer_name},</p>
      <p>An invoice has been issued for the following milestone:</p>
      <div style="background:#f5f5f5;border-left:4px solid #1A2E44;padding:12px 16px;margin:16px 0;border-radius:4px;">
        <strong>{milestone_name}</strong><br>
        <span style="font-size:1.4rem;font-weight:bold;color:#1A2E44;">${amount:,.2f}</span>
      </div>
      <p style="text-align:center;margin:28px 0;">
        <a href="{payment_url}"
           style="background:#1A2E44;color:#fff;padding:14px 28px;
                  border-radius:6px;text-decoration:none;font-weight:bold;display:inline-block;">
          Pay Now
        </a>
      </p>
      <p style="font-size:12px;color:#999;">
        This is a secure payment link. Click the button above to pay online.
      </p>
    </div>
    """
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{from_name} <{smtp_user}>"
    msg["To"] = to
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.ehlo()
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.sendmail(smtp_user, to, msg.as_string())


async def send_invoice_email(
    customer_email: str,
    customer_name: str,
    milestone_name: str,
    amount: float,
    payment_url: str,
    company_name: str = "",
) -> None:
    """Send an invoice email asynchronously (runs SMTP in thread pool)."""
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(
        None,
        partial(
            _send_invoice_email_sync,
            customer_email, customer_name, milestone_name, amount, payment_url, company_name,
        ),
    )
