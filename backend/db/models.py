from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class Lead(BaseModel):
    id: str | None = None
    org_id: str
    customer_name: str
    phone: str
    email: str
    city: str
    project_type: Literal["ADU", "Kitchen", "Addition", "Permit", "Other"]
    quote_amount: float = 0.0
    status: Literal["lead", "proposal", "active", "done"] = "lead"
    notes: str = ""
    created_at: datetime | None = None


class Contract(BaseModel):
    id: str | None = None
    lead_id: str
    template_name: str
    content: str
    status: Literal["draft", "sent", "signed"] = "draft"
    signed_at: datetime | None = None
    storage_path: str = ""
    created_at: datetime | None = None


class Invoice(BaseModel):
    id: str | None = None
    contract_id: str
    lead_id: str
    milestone_name: str
    amount: float
    due_date: str
    status: Literal["draft", "sent", "paid"] = "draft"
    stripe_link: str = ""
    created_at: datetime | None = None


class Message(BaseModel):
    id: str | None = None
    session_id: str
    project_id: str
    role: Literal["user", "assistant"]
    content: str
    created_at: datetime | None = None
