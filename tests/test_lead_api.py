r"""
test_lead_api.py - Task 2.3, tests against the real running server

Needs the backend running in another terminal:

    python backend\main.py

Then:

    pytest tests\test_lead_api.py -v -s

These send real requests to /lead. One test sends a valid lead, named
"Automated Test", which is stored like any other: in n8n once that is set up,
or in backend/leads/pending.jsonl until then. Delete it from there if you like.
Uses no Gemini quota.
"""

import httpx
import pytest

BASE_URL = "http://127.0.0.1:8000"

VALID = {
    "name": "Automated Test",
    "phone": "0300 0000000",
    "email": "",
    "property_ref": "BRE-R-202",
    "message": "Sent by tests/test_lead_api.py",
    "consent": True,
}


def post(**changes):
    body = dict(VALID)
    body.update(changes)
    try:
        return httpx.post(f"{BASE_URL}/lead", json=body, timeout=15)
    except httpx.ConnectError:
        pytest.skip(f"No server at {BASE_URL}. Start it with: python backend\\main.py")


def messages(response):
    return [problem["msg"] for problem in response.json()["detail"]]


def test_api_01_health_reports_lead_destination():
    try:
        body = httpx.get(f"{BASE_URL}/health", timeout=15).json()
    except httpx.ConnectError:
        pytest.skip(f"No server at {BASE_URL}.")
    print(f"\n  leads go to: {body.get('leads_go_to')}")
    assert "leads_go_to" in body, "Restart the server: it is running code from before Task 2.3."
    assert "http" not in body["leads_go_to"], "The webhook address must not be published."


def test_api_02_phone_abc_rejected():
    """AC-5."""
    response = post(phone="abc")
    print(f"\n  {response.status_code} {messages(response)}")
    assert response.status_code == 422
    assert any("10 to 15 digits" in m for m in messages(response))


def test_api_03_empty_name_rejected():
    """AC-5."""
    response = post(name="  ")
    print(f"\n  {response.status_code} {messages(response)}")
    assert response.status_code == 422
    assert any("Enter your name" in m for m in messages(response))


def test_api_04_no_consent_rejected():
    """FR-08."""
    response = post(consent=False)
    assert response.status_code == 422
    assert any("agreed" in m for m in messages(response))


def test_api_05_valid_lead_received():
    """FR-13. The reply holds an ID and nothing personal (NFR-09)."""
    response = post()
    print(f"\n  {response.status_code} {response.json()}")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "received" and len(body["lead_id"]) == 12
    assert "Automated" not in response.text and "0300" not in response.text
