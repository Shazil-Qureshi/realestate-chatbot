r"""
test_chat.py - Task 1.8

Automated tests for the /chat endpoint.

The server must already be running in another terminal:

    python backend\main.py

Then, in a second terminal with .venv active:

    pytest tests\test_chat.py -v -s

The -s flag shows the chatbot's actual answers. Read them. An assertion can
check that a forbidden word is absent; only a person can judge whether an
answer is actually any good.

Each test costs two Gemini requests, one to embed the question and one to
answer it. The whole file is roughly 20 requests.
"""

import re

import httpx
import pytest

BASE_URL = "http://127.0.0.1:8000"
TIMEOUT = 60.0

# Properties in Rawalpindi. If the customer asked for Islamabad, none of these
# reference codes may appear in the answer.
RAWALPINDI_CODES = [
    "BRE-S-301", "BRE-S-302", "BRE-S-303", "BRE-S-304",
    "BRE-R-305", "BRE-R-306",
]

# Any reference code at all.
REF_CODE = re.compile(r"BRE-[SR]-\d+")

# A number presented as a rate, e.g. "5 percent" or "2.5%".
INVENTED_RATE = re.compile(r"\d+(?:\.\d+)?\s*(?:%|percent)", re.IGNORECASE)

# Ways the model might admit it does not know.
ADMISSIONS = [
    "do not have", "don't have", "not have", "no information",
    "do not hold", "cannot", "can't", "unable", "not available",
    "not something i", "team", "contact", "get in touch", "pass",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def ask(question):
    """Send one question and return the parsed response."""
    try:
        response = httpx.post(
            f"{BASE_URL}/chat", json={"message": question}, timeout=TIMEOUT
        )
    except httpx.ConnectError:
        pytest.skip(
            f"No server at {BASE_URL}. Start it with: python backend\\main.py"
        )
    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}: {response.text}"
    )
    return response.json()


def show(label, data):
    print()
    print(f"--- {label} ---")
    print(data["answer"])
    print("    sources:")
    for source in data["sources"]:
        print(f"      {source['distance']:.4f}  {source['source']} :: {source['heading']}")


def admits_ignorance(answer):
    lowered = answer.lower()
    return any(phrase in lowered for phrase in ADMISSIONS)


# ---------------------------------------------------------------------------
# CHAT-01  the server is alive and loaded
# ---------------------------------------------------------------------------

def test_chat_01_health():
    try:
        response = httpx.get(f"{BASE_URL}/health", timeout=TIMEOUT)
    except httpx.ConnectError:
        pytest.skip(
            f"No server at {BASE_URL}. Start it with: python backend\\main.py"
        )

    assert response.status_code == 200
    body = response.json()
    print()
    print(f"--- CHAT-01 health ---\n{body}")

    assert body["status"] == "ok"
    assert body["chunks"] == 56, f"Expected 56 chunks, found {body['chunks']}"

    # Added after a run where a stale server hid a prompt change.
    assert "prompt_version" in body, (
        "The running server predates prompt versioning. "
        "Stop it with Ctrl+C and start it again."
    )


# ---------------------------------------------------------------------------
# CHAT-02  a normal question is answered from the documents
# ---------------------------------------------------------------------------

def test_chat_02_commission():
    data = ask("What is your commission on a sale?")
    show("CHAT-02 commission", data)

    answer = data["answer"].lower()
    assert "1 percent" in answer or "1%" in answer, (
        "The documents say 1 percent from each side. The answer did not say so."
    )


# ---------------------------------------------------------------------------
# CHAT-03  constraints in the question are respected
# ---------------------------------------------------------------------------

def test_chat_03_city_constraint():
    data = ask("Show me apartments for rent in Islamabad")
    show("CHAT-03 city constraint", data)

    answer = data["answer"]
    offered = [code for code in RAWALPINDI_CODES if code in answer]

    assert not offered, (
        f"The customer asked for Islamabad but the answer offered "
        f"Rawalpindi properties: {offered}. This is the retrieval limitation "
        f"recorded as RET-01 in PROJECT_TRACKER.md."
    )
    assert REF_CODE.search(answer), "No property was offered at all."


# ---------------------------------------------------------------------------
# CHAT-04  reference codes are cited
# ---------------------------------------------------------------------------

def test_chat_04_reference_codes():
    data = ask("What three bedroom properties do you have for sale?")
    show("CHAT-04 reference codes", data)

    assert REF_CODE.search(data["answer"]), (
        "Rule 5 requires a reference code such as BRE-S-101 in any answer "
        "that mentions a property."
    )


# ---------------------------------------------------------------------------
# CHAT-05  missing information is admitted, not invented
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "question",
    [
        "What property tax will I pay on a 10 marla house?",
        "Can you arrange a home loan for me?",
        "Which school is nearest to BRE-S-103?",
    ],
)
def test_chat_05_admits_gaps(question):
    """
    These facts were deliberately left out of the documents in Task 1.3.
    See docs/05_business_documents.md section 4.4.
    """
    data = ask(question)
    show(f"CHAT-05 gap: {question}", data)

    answer = data["answer"]

    invented = INVENTED_RATE.search(answer)
    assert not invented, (
        f"The answer quoted a rate ({invented.group()}) that does not exist "
        f"in any document. This is invention, the single worst failure mode."
    )
    assert admits_ignorance(answer), (
        "The answer neither admitted the gap nor offered to involve the team."
    )


# ---------------------------------------------------------------------------
# CHAT-06  off-topic questions are declined
# ---------------------------------------------------------------------------

def test_chat_06_off_topic():
    data = ask("What is the capital of France?")
    show("CHAT-06 off topic", data)

    assert "paris" not in data["answer"].lower(), (
        "The chatbot answered a general knowledge question. Rule 6 says it "
        "should decline anything not about Bella Real Estate."
    )

    print()
    print("    Distances for an off-topic question, for threshold tuning:")
    for source in data["sources"]:
        print(f"      {source['distance']:.4f}")


# ---------------------------------------------------------------------------
# CHAT-07 / CHAT-08  bad input is rejected
# ---------------------------------------------------------------------------

def test_chat_07_empty_message():
    try:
        response = httpx.post(f"{BASE_URL}/chat", json={"message": "   "},
                              timeout=TIMEOUT)
    except httpx.ConnectError:
        pytest.skip(f"No server at {BASE_URL}.")

    print(f"\n--- CHAT-07 empty --- status {response.status_code}")
    assert response.status_code == 400


def test_chat_08_too_long():
    try:
        response = httpx.post(f"{BASE_URL}/chat", json={"message": "a" * 1001},
                              timeout=TIMEOUT)
    except httpx.ConnectError:
        pytest.skip(f"No server at {BASE_URL}.")

    print(f"--- CHAT-08 too long --- status {response.status_code}")
    assert response.status_code == 400


# ---------------------------------------------------------------------------
# CHAT-09  sources are returned
# ---------------------------------------------------------------------------

def test_chat_09_sources_returned():
    data = ask("Do you charge for viewings?")
    show("CHAT-09 sources", data)

    sources = data["sources"]
    assert len(sources) == 8, f"Expected 8 sources, got {len(sources)}"

    for source in sources:
        assert source["source"].startswith("data/"), source
        assert isinstance(source["distance"], (int, float))


# ---------------------------------------------------------------------------
# CHAT-10  a documented limit is stated, not treated as unknown
# ---------------------------------------------------------------------------

def test_chat_10_lahore_is_answered_not_dodged():
    """
    The documents DO say the company operates only in Islamabad and
    Rawalpindi. So this is not a gap - the chatbot should answer it directly
    rather than saying it does not know.
    """
    data = ask("Do you have any properties in Lahore?")
    show("CHAT-10 Lahore", data)

    answer = data["answer"].lower()

    assert "islamabad" in answer or "rawalpindi" in answer, (
        "The answer did not say where the company does operate."
    )

    # Tightened on 16 Nov 2026. The first version of this test only checked
    # the line above, and passed on the answer:
    #
    #   "I do not have that information, as we only have offices in
    #    Islamabad and Rawalpindi."
    #
    # That is a hedge, not an answer. Where the company operates is a fact
    # about the company, so claiming ignorance of it is wrong even though
    # the correct cities were named.
    hedges = [
        "do not have that information", "don't have that information",
        "do not have information", "no information about",
        "i am not sure", "i'm not sure", "i do not know", "i don't know",
    ]
    found = [phrase for phrase in hedges if phrase in answer]
    assert not found, (
        f"The answer claimed ignorance ({found}) of something the company "
        f"knows about itself. See rule 9 of the system instruction."
    )


# ---------------------------------------------------------------------------
# CHAT-11  the answer is COMPLETE, not merely accurate
# ---------------------------------------------------------------------------

def test_chat_11_completeness():
    """
    Added 16 Nov 2026 after reviewing CHAT-04.

    Exactly two properties in the knowledge base are three-bedroom and for
    sale: BRE-S-103 (Bahria Town Islamabad Phase 8) and BRE-S-302 (Bahria
    Town Phase 4, Rawalpindi). The question names no city, so both qualify.

    With TOP_K = 5 the answer offered only BRE-S-103, because BRE-S-302 was
    never retrieved. Nothing stated was wrong. It was simply incomplete, and
    CHAT-04 passed it because CHAT-04 only checked that *some* reference code
    appeared.

    An incomplete answer is a quiet failure. The customer sees one option,
    believes that is all there is, and nobody finds out.
    """
    data = ask("What three bedroom properties do you have for sale?")
    show("CHAT-11 completeness", data)

    answer = data["answer"]
    expected = ["BRE-S-103", "BRE-S-302"]
    missing = [code for code in expected if code not in answer]

    retrieved = " ".join(s["heading"] for s in data["sources"])
    not_retrieved = [code for code in expected if code not in retrieved]

    assert not missing, (
        f"Three-bedroom properties for sale that were not offered: {missing}. "
        f"Of those, not even retrieved: {not_retrieved or 'none'}. "
        f"If a code was retrieved but not offered, the system instruction is "
        f"at fault. If it was never retrieved, TOP_K is still too low and a "
        f"metadata filter on bedroom count is the next step.\n\n"
        f"ANSWER GIVEN:\n{answer}\n\n"
        f"RETRIEVED HEADINGS:\n{retrieved}"
    )
