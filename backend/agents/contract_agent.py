import json
import os
import re
from datetime import date
from pathlib import Path

from dotenv import load_dotenv
from fastapi import HTTPException
from google.cloud.firestore import SERVER_TIMESTAMP
from google.cloud.storage.blob import Blob
from openai import AsyncOpenAI

from db.firestore_client import get_db
from db.storage_client import get_bucket

load_dotenv()

_client: AsyncOpenAI | None = None


def _get_openai() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _client


async def get_template(template_name: str) -> str:
    """Download a contract template from GCS. Returns content as string."""
    import asyncio
    from functools import partial

    path = f"templates/{template_name}.txt"

    def _download() -> bytes | None:
        blob: Blob = get_bucket().blob(path)
        if not blob.exists():
            return None
        return blob.download_as_bytes()

    loop = asyncio.get_running_loop()
    data = await loop.run_in_executor(None, _download)

    if data is None:
        raise HTTPException(status_code=404, detail=f"Template '{template_name}' not found in GCS")

    return data.decode("utf-8")


def _extract_city_from_address(address: str) -> str:
    """Extract city from 'Street, City, State ZIP' formatted address."""
    parts = [p.strip() for p in address.split(",")]
    # "123 Main St, San Jose, CA 95101" → parts[1] = "San Jose"
    if len(parts) >= 3:
        return parts[1]
    # "San Jose, CA" → parts[0] = "San Jose"
    if len(parts) == 2:
        return parts[0]
    return parts[0] if parts else ""


def render_html_contract(
    template_name: str,
    lead_data: dict,
    company_profile: dict | None = None,
) -> str:
    """Render a contract as HTML by filling {{tokens}} in the base HTML template.
    Returns a complete HTML document string ready for PDF generation or iframe display."""
    from agents.template_scopes import TEMPLATE_SCOPES

    profile = company_profile or {}
    scope_config = TEMPLATE_SCOPES.get(template_name, TEMPLATE_SCOPES["adu_legalization"])

    # Derive milestone amounts (equal thirds of quote_amount)
    try:
        raw = str(lead_data.get("quote_amount", "0")).replace("$", "").replace(",", "")
        total = float(raw)
        share = round(total / 3, 2)
        remainder = round(total - share * 2, 2)
        m1_amt = f"${share:,.2f}"
        m2_amt = f"${share:,.2f}"
        m3_amt = f"${remainder:,.2f}"
        quote_fmt = f"${total:,.2f}"
    except (ValueError, TypeError):
        m1_amt = m2_amt = m3_amt = "[TO BE DETERMINED]"
        quote_fmt = str(lead_data.get("quote_amount", "[TO BE DETERMINED]"))

    # Company profile fields
    company_name = profile.get("company_name") or "[Company Name]"
    company_name_short = re.sub(r"\s*inc\.?\s*$", "", company_name, flags=re.IGNORECASE).strip() or company_name
    drafter_name = profile.get("company_drafter") or "[Drafter Name]"
    company_address = profile.get("company_address") or "[Company Address]"
    company_phone = profile.get("company_phone") or "[Phone]"
    company_email = profile.get("company_email") or "[Email]"

    # Logo HTML
    logo_url = profile.get("company_logo_url", "")
    logo_img_html = f'<img src="{logo_url}" alt="" class="logo-img"/>' if logo_url else ""

    # Scope items HTML
    scope_items_html = "\n      ".join(
        f"<li class=\"scope-item\">{item}</li>"
        for item in scope_config["scope"]
    )

    # Milestone descriptions from scope config
    m_descs = scope_config["milestone_descriptions"]

    # Customer fields
    customer_name = lead_data.get("customer_name") or "[Customer Name]"
    customer_signatory = lead_data.get("customer_signatory") or customer_name
    customer_address = lead_data.get("customer_address") or lead_data.get("city") or "[Customer Address]"
    project_location = lead_data.get("project_location") or lead_data.get("city") or "[Project Location]"

    token_map = {
        "company_name": company_name,
        "company_name_short": company_name_short,
        "logo_img_html": logo_img_html,
        "agreement_date": date.today().strftime("%B %d, %Y"),
        "customer_name": customer_name,
        "customer_signatory": customer_signatory,
        "customer_address": customer_address,
        "drafter_name": drafter_name,
        "company_address": company_address,
        "company_phone": company_phone,
        "company_email": company_email,
        "project_location": project_location,
        "scope_type_description": scope_config["description"],
        "scope_items_html": scope_items_html,
        "quote_amount": quote_fmt,
        "milestone_1_label": "Milestone 1",
        "milestone_1_description": m_descs[0] if len(m_descs) > 0 else "",
        "milestone_1_amount": m1_amt,
        "milestone_2_label": "Milestone 2",
        "milestone_2_description": m_descs[1] if len(m_descs) > 1 else "",
        "milestone_2_amount": m2_amt,
        "milestone_3_label": "Milestone 3",
        "milestone_3_description": m_descs[2] if len(m_descs) > 2 else "",
        "milestone_3_amount": m3_amt,
        "optional_services": lead_data.get("optional_services") or "None",
        # Drafter date/place — filled at contract generation time
        "drafter_date": date.today().strftime("%B %d, %Y"),
        "drafter_place": _extract_city_from_address(company_address),
        # Customer date/place — intentionally left as {{}} placeholders so signing_agent
        # can inject the actual values (city from geolocation, date from signing timestamp)
    }

    # Load base HTML template from local file system
    template_path = Path(__file__).parent.parent / "templates" / "base_contract.html"
    html = template_path.read_text(encoding="utf-8")

    # Replace all {{token}} placeholders
    for key, value in token_map.items():
        html = html.replace(f"{{{{{key}}}}}", str(value) if value is not None else "")

    return html


async def generate_contract(
    lead_data: dict,
    template_text: str,
    company_profile: dict | None = None,
) -> str:
    """Use GPT-4o to fill a contract template with lead data and company profile.
    Returns completed contract text with all {{placeholders}} replaced."""
    # Merge company profile into the data context so GPT can fill {{company_*}} tokens
    merged = {**(company_profile or {}), **lead_data}

    # Derive milestone amounts (equal thirds) if not explicitly provided
    try:
        total = float(str(merged.get("quote_amount", "0")).replace("$", "").replace(",", ""))
        share = round(total / 3, 2)
        remainder = round(total - share * 2, 2)
        merged.setdefault("milestone_1_amount", f"${share:,.2f}")
        merged.setdefault("milestone_2_amount", f"${share:,.2f}")
        merged.setdefault("milestone_3_amount", f"${remainder:,.2f}")
    except (ValueError, TypeError):
        merged.setdefault("milestone_1_amount", "{{milestone_1_amount}}")
        merged.setdefault("milestone_2_amount", "{{milestone_2_amount}}")
        merged.setdefault("milestone_3_amount", "{{milestone_3_amount}}")

    # Default optional fields
    merged.setdefault("optional_services", "None")
    merged.setdefault("customer_signatory", merged.get("customer_name", ""))
    merged.setdefault("customer_address", merged.get("city", ""))
    merged.setdefault("project_location", merged.get("city", ""))
    merged.setdefault("agreement_date", date.today().strftime("%B %d, %Y"))
    merged.setdefault("signature_date", "___________________")

    response = await _get_openai().chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a professional contract drafting assistant. "
                    "Replace every {{placeholder}} in the template with the matching value "
                    "from the data provided. Rules:\n"
                    "- Keep ALL legal text (Terms 1-25) 100% unchanged word-for-word.\n"
                    "- Keep the Scope of Work items exactly as written in the template.\n"
                    "- Replace {{company_name}}, {{company_drafter}}, {{company_address}}, "
                    "{{company_phone}}, {{company_email}} from company profile data.\n"
                    "- Replace {{customer_name}}, {{customer_signatory}}, {{customer_address}}, "
                    "{{project_location}}, {{quote_amount}}, {{milestone_*_amount}}, "
                    "{{agreement_date}}, {{signature_date}} from customer data.\n"
                    "- If a value is unknown, write [TO BE COMPLETED].\n"
                    "- Return ONLY the completed contract text. No preamble, no markdown."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Template:\n{template_text}\n\n"
                    f"Data:\n{json.dumps(merged, indent=2, default=str)}"
                ),
            },
        ],
    )
    return response.choices[0].message.content.strip()


async def edit_contract(current_content: str, ai_command: str) -> str:
    """Apply an AI edit command to an existing contract. Returns updated contract text."""
    response = await _get_openai().chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a contract editing assistant. Apply only the requested change "
                    "to the contract. Do not change anything else. Return only the complete "
                    "updated contract text. Nothing else."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Contract:\n{current_content}\n\n"
                    f"Edit instruction: {ai_command}"
                ),
            },
        ],
    )
    return response.choices[0].message.content.strip()


async def save_contract(
    lead_id: str,
    template_name: str,
    content: str,
    org_id: str,
    quote_amount: float = 0.0,
) -> dict:
    """Save a contract to Firestore. Returns saved document with id."""
    db = get_db()
    ref = db.collection("contracts").document()
    payload = {
        "lead_id": lead_id,
        "template_name": template_name,
        "content": content,
        "status": "draft",
        "org_id": org_id,
        "quote_amount": quote_amount,
        "signed_at": None,
        "storage_path": "",
        "created_at": SERVER_TIMESTAMP,
    }
    await ref.set(payload)
    snapshot = await ref.get()
    saved = snapshot.to_dict() or {}
    saved["id"] = ref.id
    if hasattr(saved.get("created_at"), "isoformat"):
        saved["created_at"] = saved["created_at"].isoformat()
    else:
        saved.pop("created_at", None)
    return saved
