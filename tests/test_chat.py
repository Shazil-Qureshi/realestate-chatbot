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

import os
import re
import time

import httpx
import pytest

# Which server to test. Defaults to the one you run with
# "python backend\\main.py"; set BELLA_TEST_URL to point somewhere else,
# which is how check_41.py tests a temporary server without disturbing it.
BASE_URL = os.environ.get("BELLA_TEST_URL", "http://127.0.0.1:8000").rstrip("/")
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

def ask(question, attempts=3):
    """
    Send one question and return the parsed response.

    Gemini sometimes answers 503 UNAVAILABLE ("experiencing high demand").
    That is an outage at Google, not a fault in this project, and on
    25 Nov 2026 it failed a run of CHAT-12 in a way that looked exactly like
    a broken answer. So a 503 is retried a few times with a growing pause.

    It is never skipped and never swallowed: if the model is still refusing
    after the last attempt, the test fails and says plainly that the cause
    was upstream, so nobody mistakes it for a defect here.
    """
    last = None
    for attempt in range(1, attempts + 1):
        try:
            response = httpx.post(
                f"{BASE_URL}/chat", json={"message": question}, timeout=TIMEOUT
            )
        except httpx.ConnectError:
            pytest.skip(
                f"No server at {BASE_URL}. Start it with: python backend\\main.py"
            )

        if response.status_code == 200:
            return response.json()

        last = response
        if response.status_code == 503 and "UNAVAILABLE" in response.text:
            if attempt < attempts:
                pause = 5 * attempt
                print(
                    f"    [Gemini busy, 503. Waiting {pause}s and trying again "
                    f"({attempt} of {attempts - 1} retries)]"
                )
                time.sleep(pause)
                continue
            pytest.fail(
                f"Gemini returned 503 UNAVAILABLE {attempts} times in a row. "
                f"This is an outage at Google, not a fault in this project. "
                f"Re-run when it recovers. Response: {last.text[:300]}"
            )
        break

    pytest.fail(f"Expected 200, got {last.status_code}: {last.text[:300]}")


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


# ---------------------------------------------------------------------------
# CHAT-12  AC-1: an area named in the question must reach that area's listings
# ---------------------------------------------------------------------------


def test_chat_12_area_constraint_ac1():
    """
    The regression test for RET-04, added in Task 4.1.

    AC-1 has failed since Stage 2. "Do you have 3-bedroom houses in DHA?"
    returned "I do not have that information in my extracts", because meaning
    based search filled all eight results with 3-bedroom listings from other
    areas and pushed the only DHA property out.

    The data has exactly one DHA property: BRE-S-102, a 4-bedroom house in
    DHA Phase 2. There is no 3-bedroom house in DHA. So the correct answer is
    not "I don't know" and not an invented listing - it is to say there is no
    3-bedroom house in DHA and name BRE-S-102 as the nearest.

    Task 4.1 stores the area with each listing and runs a second, area
    restricted search when the question names one. Bedrooms are deliberately
    NOT filtered: doing so would return nothing here and bring back the old
    unhelpful answer.

    LM-03 guards the assumption behind this test: if the data ever gains a
    3-bedroom DHA house, LM-03 fails first and this test must be rewritten.
    """
    data = ask("Do you have 3-bedroom houses in DHA?")
    show("CHAT-12 AC-1 area constraint", data)

    answer = data["answer"]
    retrieved = " ".join(
        f"{s.get('heading','')} {s.get('source','')}" for s in data["sources"]
    )

    assert "BRE-S-102" in retrieved, (
        "The only DHA listing was not even retrieved. Area filtering is not "
        "working. Check that /health reports a non-zero 'area_filtering', "
        "which means the index carries the area metadata added in Task 4.1. "
        "If it is 0, re-run: python backend\\ingest.py"
    )

    assert "BRE-S-102" in answer, (
        "BRE-S-102 was retrieved but the answer does not mention it. "
        "Retrieval is fixed; the system instruction is what needs attention. "
        f"Answer was: {answer}"
    )

    # It must not claim a 3-bedroom DHA house exists.
    other_codes = [c for c in REF_CODE.findall(answer) if c != "BRE-S-102"]
    assert not other_codes, (
        f"The answer names properties that are not in DHA: {other_codes}"
    )
