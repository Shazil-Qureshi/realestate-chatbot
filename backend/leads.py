"""
leads.py - Task 2.3

Everything about a lead except the web address itself: what a valid lead
looks like, how it is sent on to n8n, and where it goes if n8n can't take it.

Kept separate from main.py so it can be tested without the knowledge base,
the Gemini key or a running server.

Privacy rules this file follows (NFR-09):
- A lead's name, phone or email is never printed to the console. Only its ID.
- When n8n is unavailable, leads are kept in backend/leads/pending.jsonl,
  which .gitignore excludes, so they never reach GitHub.
- The reply to the visitor contains only an ID, never their details.
"""

import json
import re
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional

from pydantic import BaseModel, Field, field_validator

BACKEND_DIR = Path(__file__).resolve().parent
PENDING_FILE = BACKEND_DIR / "leads" / "pending.jsonl"

_write_lock = threading.Lock()


# ---------------------------------------------------------------------------
# What a valid lead looks like (FR-08, FR-09)
# ---------------------------------------------------------------------------

class LeadIn(BaseModel):
    """A lead as sent by the website. Every check has a plain-English error."""

    name: str = Field(..., description="The visitor's name.")
    phone: str = Field(..., description="A phone number with 10 to 15 digits.")
    email: Optional[str] = Field(None, description="Optional.")
    property_ref: Optional[str] = Field(None, description="e.g. BRE-R-202. Optional.")
    message: Optional[str] = Field(None, description="Optional note, up to 500 characters.")
    consent: bool = Field(..., description="Must be true: the visitor agreed to share these details.")
    # Hidden field that people never see and so never fill in. Simple bots
    # fill in every field they find. See handle_lead().
    website: Optional[str] = Field(None, description="Leave empty.")

    @field_validator("name")
    @classmethod
    def check_name(cls, value):
        cleaned = " ".join(value.split())
        if not cleaned:
            raise ValueError("Enter your name.")
        if len(cleaned) < 2 or len(cleaned) > 80:
            raise ValueError("Enter a name between 2 and 80 characters.")
        if not any(ch.isalpha() for ch in cleaned):
            raise ValueError("Enter your name using letters.")
        return cleaned

    @field_validator("phone")
    @classmethod
    def check_phone(cls, value):
        # People type numbers in many ways: 0300-1234567, +92 300 1234567,
        # (051) 111 2222. Keep a leading + and the digits; drop the rest.
        trimmed = value.strip()
        digits = re.sub(r"[\s\-().]", "", trimmed)
        if not re.fullmatch(r"\+?\d{10,15}", digits):
            raise ValueError(
                "Enter a phone number with 10 to 15 digits, for example 0300 1234567."
            )
        return digits

    @field_validator("email")
    @classmethod
    def check_email(cls, value):
        if value is None or not value.strip():
            return None
        cleaned = value.strip()
        if len(cleaned) > 254 or not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", cleaned):
            raise ValueError("Enter an email address like name@example.com, or leave it empty.")
        return cleaned

    @field_validator("property_ref")
    @classmethod
    def check_property_ref(cls, value):
        if value is None or not value.strip():
            return None
        cleaned = value.strip().upper()
        if not re.fullmatch(r"BRE-[SR]-\d{3}", cleaned):
            raise ValueError("A property reference looks like BRE-R-202, or leave it empty.")
        return cleaned

    @field_validator("message")
    @classmethod
    def check_message(cls, value):
        if value is None or not value.strip():
            return None
        cleaned = value.strip()
        if len(cleaned) > 500:
            raise ValueError("Keep the note under 500 characters.")
        return cleaned

    @field_validator("consent")
    @classmethod
    def check_consent(cls, value):
        if value is not True:
            raise ValueError("Details can only be sent once you have agreed to share them.")
        return value


# ---------------------------------------------------------------------------
# Sending a lead on
# ---------------------------------------------------------------------------

def build_record(lead: LeadIn) -> dict:
    """The exact data sent to n8n, and therefore the columns of the sheet."""
    return {
        "lead_id": uuid.uuid4().hex[:12],
        "received_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "name": lead.name,
        "phone": lead.phone,
        "email": lead.email or "",
        "property_ref": lead.property_ref or "",
        "message": lead.message or "",
        "source": "website chat",
    }


def _post_with_httpx(url: str, record: dict) -> int:
    import httpx  # imported here so tests can run without it

    response = httpx.post(url, json=record, timeout=5.0)
    return response.status_code


def save_pending(record: dict, path: Path = PENDING_FILE) -> None:
    """Keep a lead that could not be forwarded, one JSON object per line."""
    with _write_lock:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def forward_lead(
    record: dict,
    webhook_url: str,
    send: Callable[[str, dict], int] = _post_with_httpx,
    pending_path: Path = PENDING_FILE,
) -> str:
    """
    Send the lead to n8n. Never lose it.

    Returns "n8n" if n8n accepted it, or "pending" if it was saved locally
    instead because no webhook is configured, the request failed, or n8n
    answered with an error. In every case the visitor is told it was received,
    because it was: it is either in n8n or on disk (NFR-05).
    """
    if webhook_url:
        try:
            status = send(webhook_url, record)
            if 200 <= status < 300:
                return "n8n"
            reason = f"n8n answered {status}"
        except Exception as error:
            reason = f"n8n unreachable ({type(error).__name__})"
    else:
        reason = "no N8N_WEBHOOK_URL set"

    save_pending(record, pending_path)
    print(f"[lead {record['lead_id']}] saved to {pending_path.name}: {reason}")
    return "pending"


def handle_lead(
    lead: LeadIn,
    webhook_url: str,
    send: Callable[[str, dict], int] = _post_with_httpx,
    pending_path: Path = PENDING_FILE,
    demo: bool = False,
) -> dict:
    """What /lead does once the request has passed validation."""
    # A filled-in hidden field means a bot, not a person. Answer exactly as for
    # a real lead, so the bot learns nothing, but keep nothing.
    if lead.website and lead.website.strip():
        print("[lead] discarded: hidden field was filled in")
        return {"status": "received", "lead_id": uuid.uuid4().hex[:12]}

    # Demo mode (the public live site, Task 3.3). The details have already
    # passed every check, which is what the demo shows. They are then
    # dropped: not stored, not sent, not printed. "demo": True lets the
    # widget tell the visitor exactly that.
    if demo:
        print("[lead] demo mode: details were valid and have been discarded")
        return {"status": "received", "lead_id": uuid.uuid4().hex[:12], "demo": True}

    record = build_record(lead)
    destination = forward_lead(record, webhook_url, send, pending_path)
    if destination == "n8n":
        print(f"[lead {record['lead_id']}] forwarded to n8n")
    return {"status": "received", "lead_id": record["lead_id"]}
