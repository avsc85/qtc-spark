"""
Built-in e-signing agent.
No third-party signing service — uses:
  - UUID tokens stored in Firestore (signing_tokens collection)
  - Python stdlib smtplib for email (Gmail SMTP or any SMTP)
  - reportlab for signed PDF generation
  - GCS for signed PDF storage
"""

import asyncio
import io
import os
import smtplib
import uuid
from datetime import datetime, timedelta, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from functools import partial

from dotenv import load_dotenv
from fastapi import HTTPException
from google.cloud.firestore import SERVER_TIMESTAMP
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from db.firestore_client import get_db
from db.storage_client import get_bucket

load_dotenv()

TOKEN_EXPIRY_HOURS = 72  # signing link valid for 3 days


# ---------------------------------------------------------------------------
# Token management
# ---------------------------------------------------------------------------

async def create_signing_token(contract_id: str, org_id: str, signer_email: str, signer_name: str = "") -> str:
    """
    Generate a UUID signing token, store in Firestore, return the token string.
    Token expires in TOKEN_EXPIRY_HOURS hours.
    """
    token = str(uuid.uuid4())
    expires_at = (datetime.now(timezone.utc) + timedelta(hours=TOKEN_EXPIRY_HOURS)).isoformat()

    db = get_db()
    await db.collection("signing_tokens").document(token).set(
        {
            "token": token,
            "contract_id": contract_id,
            "org_id": org_id,
            "signer_email": signer_email,
            "signer_name": signer_name,
            "expires_at": expires_at,
            "signed_at": None,
            "ip_address": None,
            "used": False,
            "created_at": SERVER_TIMESTAMP,
        }
    )
    return token


async def validate_signing_token(token: str) -> dict:
    """
    Fetch and validate a signing token.
    Returns the token document dict.
    Raises HTTP 400/410 if invalid, used, or expired.
    """
    db = get_db()
    snap = await db.collection("signing_tokens").document(token).get()

    if not snap.exists:
        raise HTTPException(status_code=400, detail="Invalid signing link")

    doc = snap.to_dict() or {}

    if doc.get("used"):
        raise HTTPException(status_code=410, detail="This contract has already been signed")

    expires_at = doc.get("expires_at", "")
    if expires_at:
        expiry = datetime.fromisoformat(expires_at)
        if datetime.now(timezone.utc) > expiry:
            raise HTTPException(status_code=410, detail="Signing link has expired")

    return doc


async def mark_token_used(token: str, signer_name: str, ip_address: str, user_agent: str = "") -> None:
    """Mark a signing token as used and record full signer audit metadata."""
    db = get_db()
    await db.collection("signing_tokens").document(token).update(
        {
            "used": True,
            "signed_at": datetime.now(timezone.utc).isoformat(),
            "signer_name": signer_name,
            "ip_address": ip_address,
            "user_agent": user_agent,
        }
    )


# ---------------------------------------------------------------------------
# PDF generation
# ---------------------------------------------------------------------------

def _build_signed_pdf(contract_content: str, signer_name: str, signed_at: str, signature_image: str | None = None) -> bytes:
    """
    Generate a signed contract PDF using reportlab.
    Returns raw PDF bytes.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=LETTER,
        rightMargin=inch,
        leftMargin=inch,
        topMargin=inch,
        bottomMargin=inch,
    )

    styles = getSampleStyleSheet()
    body_style = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontSize=10,
        leading=16,
        spaceAfter=6,
    )
    heading_style = ParagraphStyle(
        "Heading",
        parent=styles["Heading2"],
        fontSize=12,
        spaceAfter=12,
    )
    signature_style = ParagraphStyle(
        "Signature",
        parent=styles["Normal"],
        fontSize=10,
        leading=16,
        textColor="#1a1a1a",
    )

    story = []

    # Contract body — split on newlines, render each line as a paragraph
    for line in contract_content.splitlines():
        stripped = line.strip()
        if not stripped:
            story.append(Spacer(1, 6))
        else:
            # Escape HTML special chars for reportlab
            safe = stripped.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            story.append(Paragraph(safe, body_style))

    # Signature block — only shown on signed copies
    if signed_at:
        story.append(Spacer(1, 30))
        story.append(Paragraph("─" * 80, body_style))
        story.append(Paragraph("<b>ELECTRONICALLY SIGNED</b>", heading_style))
        # Embed signature image if provided
        if signature_image:
            import base64
            from reportlab.platypus import Image as RLImage
            try:
                # Strip "data:image/...;base64," prefix
                b64 = signature_image.split(",", 1)[-1]
                img_bytes = base64.b64decode(b64)
                img_buf = io.BytesIO(img_bytes)
                sig_img = RLImage(img_buf, width=2.5 * inch, height=0.75 * inch)
                sig_img.hAlign = "LEFT"
                story.append(sig_img)
                story.append(Spacer(1, 4))
            except Exception:
                pass  # if image fails, continue without it
        story.append(Paragraph(f"Signer: <b>{signer_name}</b>", signature_style))
        story.append(Paragraph(f"Date &amp; Time: {signed_at} UTC", signature_style))
        story.append(Spacer(1, 6))
        story.append(
            Paragraph(
                "This document was signed electronically. The electronic signature is legally "
                "binding under the US ESIGN Act (15 U.S.C. § 7001) and UETA.",
                ParagraphStyle("Disclaimer", parent=styles["Normal"], fontSize=8, textColor="#666666"),
            )
        )
    else:
        story.append(Spacer(1, 30))
        story.append(
            Paragraph(
                "— Awaiting electronic signature —",
                ParagraphStyle("Pending", parent=styles["Normal"], fontSize=9, textColor="#888888"),
            )
        )

    doc.build(story)
    return buffer.getvalue()


def _inject_signatures_into_html(
    html: str,
    signer_name: str,
    signed_at: str,
    signature_image: str | None,
    drafter_signature: str | None,
    signer_place: str | None = None,
) -> str:
    """
    Inject customer + drafter signatures directly into the template sig-line placeholders.
    Also fills {{customer_date}} and {{customer_place}} with actual signing values.
    Appends a small ESIGN audit footnote at the bottom of the document.
    """
    SIG_LINE = '<div class="sig-line"></div>'

    def _sig_img(data_url: str) -> str:
        return (
            f'<div class="sig-line" style="border:none;height:2.2rem;display:flex;'
            f'align-items:flex-end;padding-bottom:2px;">'
            f'<img src="{data_url}" alt="Signature" '
            f'style="max-height:2rem;max-width:100%;object-fit:contain;display:block;" /></div>'
        )

    # Inject customer signature into FIRST sig-line
    if signature_image and SIG_LINE in html:
        html = html.replace(SIG_LINE, _sig_img(signature_image), 1)

    # Inject drafter signature into SECOND sig-line
    if drafter_signature and SIG_LINE in html:
        html = html.replace(SIG_LINE, _sig_img(drafter_signature), 1)

    # Fill customer date/place placeholders (left unresolved at contract generation time)
    try:
        customer_date = datetime.strptime(signed_at, "%Y-%m-%d %H:%M:%S").strftime("%B %d, %Y") if signed_at else ""
    except Exception:
        customer_date = signed_at or ""
    html = html.replace("{{customer_date}}", customer_date)
    html = html.replace("{{customer_place}}", signer_place or "")

    # Append a small ESIGN audit footnote (not a full block — just audit metadata)
    audit_html = (
        f'<div style="margin:0;padding:10px 48px 14px;background:#f5f5f5;'
        f'border-top:1px solid #ddd;font-family:Arial,sans-serif;font-size:8px;color:#888;">'
        f'<strong style="color:#555;">Electronic Signature Audit Record</strong> &mdash; '
        f'Signer: {signer_name} &nbsp;|&nbsp; Date &amp; Time: {signed_at} UTC &nbsp;|&nbsp; '
        f'Signed electronically under the US ESIGN Act (15 U.S.C. &sect;&nbsp;7001) and UETA.'
        f'</div>'
    )
    html = html.replace("</body>", audit_html + "</body>") if "</body>" in html else html + audit_html
    return html


async def generate_signed_pdf(
    contract_content: str,
    signer_name: str,
    signed_at: str,
    signature_image: str | None = None,
    drafter_signature: str | None = None,
    signer_place: str | None = None,
) -> bytes:
    """
    Generate signed PDF.
    HTML contracts → inject signatures into template sig-line placeholders via Playwright.
    Plain-text contracts → reportlab fallback.
    """
    is_html = (
        contract_content.strip().startswith("<!DOCTYPE")
        or contract_content.strip().startswith("<html")
    )

    if is_html:
        from agents.pdf_generator import html_to_pdf

        signed_html = _inject_signatures_into_html(
            contract_content, signer_name, signed_at, signature_image, drafter_signature, signer_place
        )
        return await html_to_pdf(signed_html)
    else:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None, partial(_build_signed_pdf, contract_content, signer_name, signed_at, signature_image)
        )


# ---------------------------------------------------------------------------
# GCS storage
# ---------------------------------------------------------------------------

async def store_signed_pdf(contract_id: str, pdf_bytes: bytes) -> str:
    """Upload signed PDF to GCS. Returns the GCS storage path."""
    path = f"signed_contracts/{contract_id}.pdf"

    def _upload() -> None:
        blob = get_bucket().blob(path)
        blob.upload_from_string(pdf_bytes, content_type="application/pdf")

    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, _upload)
    return path


# ---------------------------------------------------------------------------
# Email (stdlib smtplib — no third-party service)
# ---------------------------------------------------------------------------

def _send_email_sync(
    to: str,
    subject: str,
    html_body: str,
    pdf_bytes: bytes | None = None,
    pdf_filename: str = "contract.pdf",
) -> None:
    """Send email via SMTP with optional PDF attachment. Runs synchronously — call via run_in_executor."""
    from email.mime.application import MIMEApplication

    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_password = os.getenv("SMTP_PASSWORD", "")
    from_name = os.getenv("SMTP_FROM_NAME", "QTC Platform")

    if pdf_bytes:
        msg = MIMEMultipart("mixed")
        msg["Subject"] = subject
        msg["From"] = f"{from_name} <{smtp_user}>"
        msg["To"] = to
        html_part = MIMEMultipart("alternative")
        html_part.attach(MIMEText(html_body, "html"))
        msg.attach(html_part)
        pdf_part = MIMEApplication(pdf_bytes, _subtype="pdf")
        pdf_part.add_header("Content-Disposition", "attachment", filename=pdf_filename)
        msg.attach(pdf_part)
    else:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{from_name} <{smtp_user}>"
        msg["To"] = to
        msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.ehlo()
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.sendmail(smtp_user, to, msg.as_string())


async def send_signing_request_email(
    signer_email: str,
    signer_name: str,
    signing_url: str,
    contract_content: str,
    company_name: str = "",
) -> None:
    """Send the signing invitation email with the contract PDF attached."""
    company = company_name or os.getenv("COMPANY_NAME", "QTC Construction")
    subject = f"Your {company} Service Agreement — Please Review & Sign"
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:auto;">
      <h2 style="color:#1a1a1a;">You have a contract ready to sign</h2>
      <p>Hi {signer_name},</p>
      <p>Please review the attached service agreement from <strong>{company}</strong>
         and click the button below to sign electronically.</p>
      <p style="text-align:center;margin:32px 0;">
        <a href="{signing_url}"
           style="background:#1A2E44;color:#fff;padding:14px 28px;
                  border-radius:6px;text-decoration:none;font-weight:bold;">
          Review &amp; Sign Contract
        </a>
      </p>
      <p style="font-size:12px;color:#999;">
        The full contract is also attached as a PDF for your records.<br>
        This signing link expires in {TOKEN_EXPIRY_HOURS} hours.
      </p>
    </div>
    """
    # Generate PDF from HTML contract for attachment
    is_html = contract_content.strip().startswith("<!DOCTYPE") or contract_content.strip().startswith("<html")
    if is_html:
        from agents.pdf_generator import html_to_pdf
        pdf_bytes = await html_to_pdf(contract_content)
    else:
        pdf_bytes = await generate_signed_pdf(contract_content, signer_name="[Unsigned]", signed_at="")
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(
        None,
        partial(_send_email_sync, signer_email, subject, html, pdf_bytes, "service_agreement.pdf"),
    )


async def send_signed_confirmation_email(signer_email: str, org_email: str, signer_name: str) -> None:
    """Send confirmation email to both signer and business owner after signing."""
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:auto;">
      <h2 style="color:#16a34a;">Contract signed successfully</h2>
      <p>Hi {signer_name},</p>
      <p>Your contract has been <strong>signed and recorded</strong>.</p>
      <p>A copy has been securely stored. You will receive your project details shortly.</p>
      <p style="font-size:12px;color:#999;">
        This signature is legally binding under the US ESIGN Act.
      </p>
    </div>
    """
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, partial(_send_email_sync, signer_email, "Your contract is signed", html))
    # Also notify the business owner
    owner_html = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:auto;">
      <h2 style="color:#16a34a;">Contract signed by {signer_name}</h2>
      <p>Your client <strong>{signer_name}</strong> has signed the contract.</p>
      <p>The project status has been updated to <strong>Active</strong>.</p>
    </div>
    """
    await loop.run_in_executor(None, partial(_send_email_sync, org_email, f"Contract signed — {signer_name}", owner_html))
