r"""
test_lead.py - Tasks 2.3 and 3.3, unit tests for backend/leads.py

No server, no API key and no network needed. Run from the project folder:

    pytest tests\test_lead.py -v

Nothing here talks to n8n. A stand-in "send" function plays n8n's part, so
each test decides whether n8n accepts, rejects or is unreachable.
"""

import json
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))
from leads import LeadIn, build_record, forward_lead, handle_lead  # noqa: E402

GOOD = {
    "name": "Ayesha Khan",
    "phone": "0300 1234567",
    "email": "ayesha@example.com",
    "property_ref": "bre-r-202",
    "message": "Can I view it on Saturday?",
    "consent": True,
}


def lead(**changes):
    data = dict(GOOD)
    data.update(changes)
    return LeadIn(**data)


def error_text(**changes):
    with pytest.raises(ValidationError) as caught:
        lead(**changes)
    return str(caught.value)


# --- LEAD-01..08: what is accepted and how it is cleaned --------------------

def test_lead_01_valid_lead_is_accepted():
    assert lead().name == "Ayesha Khan"


@pytest.mark.parametrize("typed, stored", [
    ("0300 1234567", "03001234567"),
    ("0300-1234567", "03001234567"),
    ("+92 300 1234567", "+923001234567"),
    ("(051) 111-2222", "0511112222"),
])
def test_lead_02_phone_formats_are_normalised(typed, stored):
    assert lead(phone=typed).phone == stored


def test_lead_03_name_whitespace_collapsed():
    assert lead(name="  Ayesha    Khan ").name == "Ayesha Khan"


def test_lead_04_urdu_name_accepted():
    assert lead(name="عائشہ خان").name == "عائشہ خان"


def test_lead_05_property_ref_uppercased():
    assert lead(property_ref="bre-r-202").property_ref == "BRE-R-202"


def test_lead_06_optional_fields_may_be_blank():
    entry = lead(email="", property_ref="  ", message="")
    assert entry.email is None and entry.property_ref is None and entry.message is None


# --- LEAD-07..14: what is rejected (FR-09, AC-5) ----------------------------

def test_lead_07_empty_name_rejected():
    assert "Enter your name" in error_text(name="   ")


def test_lead_08_phone_abc_rejected():
    """AC-5 names this exact case."""
    assert "10 to 15 digits" in error_text(phone="abc")


@pytest.mark.parametrize("phone", ["12345", "0300 12345678901234", "0300 123 456x"])
def test_lead_09_implausible_phones_rejected(phone):
    assert "10 to 15 digits" in error_text(phone=phone)


def test_lead_10_name_of_only_digits_rejected():
    assert "letters" in error_text(name="12345")


def test_lead_11_bad_email_rejected():
    assert "email address" in error_text(email="ayesha.example.com")


def test_lead_12_bad_property_ref_rejected():
    assert "BRE-R-202" in error_text(property_ref="flat 2")


def test_lead_13_long_message_rejected():
    assert "500 characters" in error_text(message="x" * 501)


@pytest.mark.parametrize("consent", [False])
def test_lead_14_no_consent_rejected(consent):
    """FR-08: details are only accepted after the visitor has agreed."""
    assert "agreed" in error_text(consent=consent)


def test_lead_15_missing_consent_rejected():
    data = dict(GOOD)
    del data["consent"]
    with pytest.raises(ValidationError):
        LeadIn(**data)


# --- LEAD-16..21: forwarding, and never losing a lead (FR-10, NFR-05) -------

def test_lead_16_record_has_the_sheet_columns():
    record = build_record(lead())
    assert list(record) == ["lead_id", "received_at", "name", "phone", "email",
                            "property_ref", "message", "source"]
    assert record["received_at"].endswith("+00:00")


def test_lead_17_accepted_by_n8n(tmp_path):
    sent = []
    result = forward_lead(build_record(lead()), "https://n8n.example/webhook",
                          send=lambda url, rec: sent.append((url, rec)) or 200,
                          pending_path=tmp_path / "pending.jsonl")
    assert result == "n8n"
    assert sent[0][0] == "https://n8n.example/webhook"
    assert not (tmp_path / "pending.jsonl").exists()


@pytest.mark.parametrize("behaviour", ["no url", "500", "unreachable"])
def test_lead_18_kept_on_disk_when_n8n_cannot_take_it(tmp_path, behaviour):
    def send(url, record):
        if behaviour == "unreachable":
            raise ConnectionError("refused")
        return 500

    path = tmp_path / "pending.jsonl"
    record = build_record(lead())
    url = "" if behaviour == "no url" else "https://n8n.example/webhook"
    assert forward_lead(record, url, send=send, pending_path=path) == "pending"

    saved = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    assert saved == [record]


def test_lead_19_pending_file_appends(tmp_path):
    path = tmp_path / "pending.jsonl"
    for _ in range(3):
        forward_lead(build_record(lead()), "", pending_path=path)
    assert len(path.read_text(encoding="utf-8").splitlines()) == 3


def test_lead_20_reply_contains_no_personal_details(tmp_path):
    reply = handle_lead(lead(), "", pending_path=tmp_path / "p.jsonl")
    assert reply["status"] == "received"
    text = json.dumps(reply)
    for detail in ["Ayesha", "03001234567", "ayesha@example.com"]:
        assert detail not in text


def test_lead_21_console_never_shows_personal_details(tmp_path, capsys):
    handle_lead(lead(), "", pending_path=tmp_path / "p.jsonl")
    handle_lead(lead(), "https://n8n.example/webhook",
                send=lambda u, r: 200, pending_path=tmp_path / "p.jsonl")
    printed = capsys.readouterr().out
    assert "lead " in printed
    for detail in ["Ayesha", "03001234567", "ayesha@example.com"]:
        assert detail not in printed


def test_lead_22_hidden_field_filled_means_bot(tmp_path):
    sent = []
    path = tmp_path / "p.jsonl"
    reply = handle_lead(lead(website="http://spam.example"), "https://n8n.example/webhook",
                        send=lambda u, r: sent.append(r) or 200, pending_path=path)
    assert reply["status"] == "received"      # the bot can't tell
    assert sent == [] and not path.exists()   # but nothing was kept


def test_lead_23_pending_file_is_gitignored():
    """NFR-09: leads must never be committed."""
    ignore = (Path(__file__).resolve().parent.parent / ".gitignore").read_text(encoding="utf-8")
    assert "backend/leads/" in ignore


# --- LEAD-24..26: demo mode for the public live site (Task 3.3) -------------

def test_lead_24_demo_mode_keeps_nothing(tmp_path):
    sent = []
    path = tmp_path / "p.jsonl"
    reply = handle_lead(lead(), "https://n8n.example/webhook",
                        send=lambda u, r: sent.append(r) or 200,
                        pending_path=path, demo=True)
    assert reply["status"] == "received" and reply["demo"] is True
    assert sent == [], "demo mode must not send anything to n8n"
    assert not path.exists(), "demo mode must not write the fallback file"


def test_lead_25_demo_mode_reply_and_console_have_no_personal_details(tmp_path, capsys):
    reply = handle_lead(lead(), "", pending_path=tmp_path / "p.jsonl", demo=True)
    printed = capsys.readouterr().out
    assert "demo mode" in printed
    for detail in ["Ayesha", "03001234567", "ayesha@example.com"]:
        assert detail not in json.dumps(reply)
        assert detail not in printed


def test_lead_26_demo_mode_still_validates():
    """Bad details are still refused in demo mode: validation runs first."""
    assert "10 to 15 digits" in error_text(phone="abc")


def test_lead_27_normal_mode_reply_has_no_demo_flag(tmp_path):
    reply = handle_lead(lead(), "", pending_path=tmp_path / "p.jsonl")
    assert "demo" not in reply
