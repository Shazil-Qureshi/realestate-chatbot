r"""
main.py - Tasks 1.7 and 2.3

The backend web server. It exposes three addresses:

    GET  /health   is the server alive, and how many chunks are loaded
    POST /chat     ask a question, get an answer plus its sources
    POST /lead     a visitor's contact details, sent on to n8n (see leads.py)

Start it with:

    python backend\main.py

Then open http://127.0.0.1:8000/docs in a browser. FastAPI builds an
interactive test page for you automatically - you can type a question
and see the answer without writing any frontend code.

Stop it with Ctrl+C.
"""

import os
import sys
import threading
import time
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

BACKEND_DIR = Path(__file__).resolve().parent
DB_DIR = BACKEND_DIR / "chroma_db"
COLLECTION_NAME = "bella_real_estate"

# How many chunks to retrieve per question.
#
# Started at 5, raised to 8 on 16 Nov 2026 after Task 1.8.
#
# 5 was chosen because Task 1.6 showed vector search cannot apply a hard
# filter: "apartment for rent in Islamabad" ranked a Rawalpindi property
# first. Retrieving extra chunks lets the language model do the filtering.
#
# Then CHAT-04 asked "what three bedroom properties do you have for sale?"
# Two exist - BRE-S-103 in Islamabad and BRE-S-302 in Rawalpindi. Only
# BRE-S-103 was retrieved, so only BRE-S-103 was offered. The answer was
# accurate and incomplete, which no test was checking for.
#
# Retrieval runs locally in ChromaDB and costs no extra API call, so a
# higher number is cheap. It is not free: more extracts means more input
# tokens and more irrelevant material for the model to filter out.
# CHAT-11 measures whether 8 is enough.
TOP_K = 8

# How many of the TOP_K places may be given to listings in an area the
# question names. The rest still come from ordinary meaning-based search.
AREA_SLOTS = 4

# Which area names the stored listings can be filtered by. Built from the
# index at startup, so it is whatever is actually in the data. If the index
# was built before Task 4.1 it has no area metadata, this stays empty, and
# retrieval behaves exactly as it did before.
AREA_VOCABULARY: set[str] = set()

# Questions longer than this are rejected rather than sent to the API.
MAX_QUESTION_CHARS = 1000

load_dotenv(BACKEND_DIR / ".env", override=True)

API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
CHAT_MODEL = os.getenv("GEMINI_CHAT_MODEL", "").strip()
EMBED_MODEL = os.getenv("GEMINI_EMBEDDING_MODEL", "").strip()

# Which websites are allowed to call this server from a browser.
# Where accepted leads are sent (Task 2.4). Empty until n8n is set up; until
# then leads are kept in backend/leads/pending.jsonl instead (see leads.py).
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "").strip()

# Demo mode for leads (Task 3.3). The public live site has no n8n it can
# reach, so there the form checks the details and then keeps nothing.
# Set LEADS_DEMO_MODE=true on Render; leave it unset on the laptop.
LEADS_DEMO_MODE = os.getenv("LEADS_DEMO_MODE", "").strip().lower() in ("1", "true", "yes")

if LEADS_DEMO_MODE:
    LEADS_GO_TO = "nowhere (demo mode: checked, then discarded)"
elif N8N_WEBHOOK_URL:
    LEADS_GO_TO = "n8n"
else:
    LEADS_GO_TO = "local file (n8n not set up)"

ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", "").split(",")
    if origin.strip()
]

# Used when ALLOWED_ORIGINS is empty. A browser treats localhost and
# 127.0.0.1 as different sites, so a page opened at one is refused by a
# server that only lists the other. Both are listed.
DEFAULT_ORIGINS = ["http://localhost:5500", "http://127.0.0.1:5500"]

# ---------------------------------------------------------------------------
# The instruction that keeps the chatbot honest
# ---------------------------------------------------------------------------

# Bump this whenever SYSTEM_INSTRUCTION changes. /health reports it, so a
# test run can prove which rules the running server is actually using.
PROMPT_VERSION = "2026-11-25a (10 rules, near matches rule 10)"

SYSTEM_INSTRUCTION = """\
You are the customer support assistant for Bella Real Estate, an estate agency
with offices in Islamabad and Rawalpindi, Pakistan.

You will be given extracts from the company's own documents. Follow these rules
without exception.

1. Answer ONLY using the extracts provided. They are your single source of
   truth. Do not use any other knowledge about property, prices or Pakistan.

2. If the extracts do not contain the answer, say so plainly. Say that you do
   not have that information and offer to pass the question to the team. Never
   guess, never estimate, and never fill a gap with something plausible.

3. Respect every constraint in the question, and never present a property as
   matching when it does not. The extracts may include properties that do not
   match; do not pass those off as matches.

   A PLACE is a hard constraint. A city, or an area such as DHA, F-11 or
   Bahria Town, is what the customer actually came for. Never offer a
   property in a different place as an alternative, and never let one drift
   into the answer. Someone asking about DHA does not want Bahria Town.

4. Never invent a price, a reference code, a size, or an availability status.
   Quote them exactly as written in the extracts or do not mention them.

5. When you mention a property, include its reference code, for example
   BRE-R-201, so the customer can ask about it again.

6. If the question is not about Bella Real Estate, property, or renting and
   buying homes, politely say that you can only help with questions about
   Bella Real Estate, and invite them to ask one.

7. Be brief and warm. Write plainly, as a helpful person would, not as a
   brochure. Brevity means short sentences, never fewer properties.

8. When a customer asks what is available, list EVERY property in the extracts
   that matches all of their criteria, not just the first or the best one. One
   short line per property is enough. A customer shown one option will assume
   it is the only one. If the extracts contain several matches, say how many.

9. Bella Real Estate operates only in Islamabad and Rawalpindi. If a customer
   asks about any other city, answer directly that the company does not
   operate there. Do not say you lack the information. Where the company works
   is a fact about the company, not a gap in your extracts.

10. INSIDE the place the customer named, a near match is useful and "I do not
    have that information" is not. If the extracts contain properties in that
    place, but none meets every other detail the customer asked for - the
    number of bedrooms, the size, the price - then say plainly that none
    matches, and offer what is there, making clear how each one differs.

    For example, asked for a three-bedroom house in an area where the only
    property has four bedrooms: the right answer is that there is no
    three-bedroom house in that area, and that the one available has four.
    The wrong answer is that you have no information. You do have it, and the
    customer can use it.

    This applies only within the place the customer named. Never reach into
    another city or area for a near match - rule 3 still holds. And this is
    not permission to guess: everything you say still comes from the extracts.
"""

# ---------------------------------------------------------------------------
# Connections, opened once when the server starts
# ---------------------------------------------------------------------------


def fail(message):
    print(f"[FAIL] {message}", file=sys.stderr)
    sys.exit(1)


if not API_KEY:
    fail("GEMINI_API_KEY is empty. Complete Task 1.5 first.")
if not CHAT_MODEL:
    fail("GEMINI_CHAT_MODEL is empty. Complete Task 1.5 first.")
if not EMBED_MODEL:
    fail("GEMINI_EMBEDDING_MODEL is empty. Complete Task 1.5 first.")
if not DB_DIR.exists():
    fail(f"No database at {DB_DIR}. Run 'python backend\\ingest.py' first.")

from leads import LeadIn, handle_lead  # noqa: E402
import ratelimit  # noqa: E402
import listing_meta  # noqa: E402

# Loading ChromaDB and the Gemini library is the slow part of starting up.
# On the laptop it takes seconds. On Render's free server (a tenth of a CPU)
# it can take minutes, and Render gives up if the web port stays closed that
# long. So when Render starts the server, the port opens first and this
# loading happens in the background: /health says "starting" until it is
# done, and /chat waits for it. On the laptop (python backend\\main.py) it
# still loads first, so the startup banner can show the chunk count.

gemini = None
types = None
collection = None
CHUNK_COUNT = None
LOAD_ERROR = None
READY = threading.Event()


def load_knowledge():
    """Open the Gemini client and the vector database. Sets READY when done."""
    global gemini, types, collection, CHUNK_COUNT, LOAD_ERROR, AREA_VOCABULARY
    started = time.monotonic()
    try:
        print("[startup] loading ChromaDB and Gemini libraries...", flush=True)
        import chromadb
        from google import genai
        from google.genai import types as genai_types

        types = genai_types
        gemini = genai.Client(api_key=API_KEY)
        db = chromadb.PersistentClient(path=str(DB_DIR))
        try:
            collection = db.get_collection(name=COLLECTION_NAME)
        except Exception:
            raise RuntimeError(
                f"Collection '{COLLECTION_NAME}' not found. "
                "Run 'python backend\\ingest.py' first."
            )
        CHUNK_COUNT = collection.count()
        if CHUNK_COUNT == 0:
            raise RuntimeError("The collection is empty. Run 'python backend\\ingest.py' first.")
        print(
            f"[startup] ready: {CHUNK_COUNT} chunks, "
            f"loaded in {time.monotonic() - started:.1f} s",
            flush=True,
        )
    except Exception as error:  # noqa: BLE001 - reported through /health
        LOAD_ERROR = str(error)
        print(f"[startup] FAILED after {time.monotonic() - started:.1f} s: {error}", flush=True)
    finally:
        try:
            stored = collection.get(include=["metadatas"])
            AREA_VOCABULARY = {
                meta.get("area_key")
                for meta in (stored.get("metadatas") or [])
                if meta and meta.get("area_key")
            }
        except Exception:
            # Not fatal: without a vocabulary the chatbot simply falls back to
            # plain meaning-based search, which is what it did before 4.1.
            AREA_VOCABULARY = set()

        READY.set()


# How long /chat waits for a server that is still starting.
STARTUP_WAIT_SECONDS = 120

if __name__ != "__main__":
    # Started by uvicorn (Render, tests): open the port now, load meanwhile.
    threading.Thread(target=load_knowledge, daemon=True).start()

# ---------------------------------------------------------------------------
# The web application
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Bella Real Estate Assistant",
    description="A retrieval-augmented chatbot answering from company documents.",
    version="1.0.0",
)

# A browser refuses to let a page on one address call a server on another,
# unless the server says that address is allowed. That is CORS.
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS or DEFAULT_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
    # A browser hides every response header from the page's JavaScript unless
    # the server names it here. Retry-After is sent with a 429, and the widget
    # could not read it until this was added (found while testing AC-9 live).
    expose_headers=["Retry-After"],
)


class ChatRequest(BaseModel):
    message: str = Field(..., description="The customer's question.")


class Source(BaseModel):
    heading: str
    source: str
    distance: float


class ChatResponse(BaseModel):
    answer: str
    sources: list[Source]


def refuse_if_over_limit(check, http_request: Request) -> None:
    """
    Run one of the rate-limit gates and turn a refusal into HTTP 429.

    429 is the "too many requests" code. The Retry-After header tells
    well-behaved clients how long to wait; the detail text is what the
    visitor actually reads in the chat window (AC-9).
    """
    try:
        check(ratelimit.visitor_key(http_request))
    except ratelimit.RateLimited as limited:
        raise HTTPException(
            status_code=429,
            detail=limited.message,
            headers={"Retry-After": str(limited.retry_after)},
        )


@app.get("/health")
def health():
    """Confirm the server is running and the knowledge base is loaded."""
    if LOAD_ERROR:
        raise HTTPException(status_code=503, detail=f"Startup failed: {LOAD_ERROR}")
    return {
        "status": "ok" if READY.is_set() else "starting",
        "prompt_version": PROMPT_VERSION,
        "chunks": CHUNK_COUNT,
        "chat_model": CHAT_MODEL,
        "embedding_model": EMBED_MODEL,
        # Says where leads go without revealing the webhook address itself.
        "leads_go_to": LEADS_GO_TO,
        "leads_demo": LEADS_DEMO_MODE,
        "rate_limits": ratelimit.settings_summary(),
        "area_filtering": len(AREA_VOCABULARY),
    }


def retrieve(question, question_vector):
    """
    Find the chunks to answer from.

    Meaning-based search alone cannot honour a hard constraint like an area:
    asking for "3-bedroom houses in DHA" fills the results with 3-bedroom
    listings from everywhere and pushes the only DHA house out (RET-04).

    So when the question names an area the data knows about, a second search
    is run that is restricted to that area, and those chunks are placed first.
    Nothing is thrown away: the ordinary results fill the remaining places.

    Note what is deliberately NOT filtered: the number of bedrooms. Filtering
    on both area and bedrooms would return nothing for "3-bedroom in DHA" -
    there is no such listing - and the chatbot would again say it has no
    information. Returning the area's listings lets it give the useful answer:
    there is no 3-bedroom house in DHA, the nearest is BRE-S-102 with 4.
    """
    found = collection.query(query_embeddings=[question_vector], n_results=TOP_K)

    ids = (found.get("ids") or [[]])[0]
    documents = (found.get("documents") or [[]])[0]
    metadatas = (found.get("metadatas") or [[]])[0]
    distances = (found.get("distances") or [[]])[0]

    areas = listing_meta.areas_in_question(question, AREA_VOCABULARY)
    if not areas:
        return documents, metadatas, distances

    area = areas[0]
    try:
        extra = collection.query(
            query_embeddings=[question_vector],
            n_results=AREA_SLOTS,
            where={"area_key": area},
        )
    except Exception:
        # A filter failure must never cost the visitor an answer.
        return documents, metadatas, distances

    extra_ids = (extra.get("ids") or [[]])[0]
    if not extra_ids:
        return documents, metadatas, distances

    merged = listing_meta.merge_hits(
        {"ids": ids, "documents": documents,
         "metadatas": metadatas, "distances": distances},
        {"ids": extra_ids,
         "documents": (extra.get("documents") or [[]])[0],
         "metadatas": (extra.get("metadatas") or [[]])[0],
         "distances": (extra.get("distances") or [[]])[0]},
        TOP_K,
    )

    print(f"[retrieve] area '{area}' matched {len(extra_ids)} listing(s); "
          f"{len(merged['ids'])} chunks sent to the model", flush=True)
    return merged["documents"], merged["metadatas"], merged["distances"]


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, http_request: Request):
    """
    Answer one question.

    Three steps: turn the question into numbers, find the closest chunks,
    then ask Gemini to answer using only those chunks.

    The rate-limit check comes first, before any work is done: each question
    costs two Gemini calls (one to embed it, one to answer it), so a refused
    request must not spend any of the free-tier quota.
    """
    refuse_if_over_limit(ratelimit.check_chat, http_request)

    question = request.message.strip()

    if not question:
        raise HTTPException(status_code=400, detail="The message is empty.")
    if len(question) > MAX_QUESTION_CHARS:
        raise HTTPException(
            status_code=400,
            detail=f"The message is too long. Limit is {MAX_QUESTION_CHARS} characters.",
        )

    # A server that has only just started may still be loading.
    if not READY.wait(timeout=STARTUP_WAIT_SECONDS):
        raise HTTPException(
            status_code=503,
            detail="The assistant is still starting. Try again in a minute.",
        )
    if LOAD_ERROR:
        raise HTTPException(status_code=503, detail="The assistant failed to start.")

    # --- 1. Turn the question into an embedding ---------------------------
    try:
        embedded = gemini.models.embed_content(
            model=EMBED_MODEL, contents=question
        )
        question_vector = list(embedded.embeddings[0].values)
    except Exception as error:
        raise HTTPException(
            status_code=503, detail=f"Could not reach the embedding service: {error}"
        )

    # --- 2. Find the closest chunks ---------------------------------------
    try:
        documents, metadatas, distances = retrieve(question, question_vector)
    except Exception as error:
        raise HTTPException(
            status_code=503, detail=f"Could not search the knowledge base: {error}"
        )

    if not documents:
        return ChatResponse(
            answer=(
                "I do not have any information on that yet. "
                "I can pass your question to the Bella Real Estate team if you like."
            ),
            sources=[],
        )

    # --- 3. Ask Gemini to answer from those chunks only -------------------
    extracts = "\n\n---\n\n".join(
        f"[Extract {index}]\n{text}" for index, text in enumerate(documents, start=1)
    )

    prompt = (
        f"Extracts from the company's documents:\n\n{extracts}\n\n"
        f"---\n\nCustomer's question: {question}"
    )

    try:
        reply = gemini.models.generate_content(
            model=CHAT_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0.2,
                max_output_tokens=600,
            ),
        )
        answer = (reply.text or "").strip()
    except Exception as error:
        raise HTTPException(
            status_code=503, detail=f"Could not reach the language model: {error}"
        )

    if not answer:
        answer = (
            "Sorry, I could not produce an answer to that. "
            "Please try rephrasing your question."
        )

    sources = [
        Source(
            heading=str(meta.get("heading") or meta.get("title") or ""),
            source=str(meta.get("source") or ""),
            distance=round(float(dist), 4),
        )
        for meta, dist in zip(metadatas, distances)
    ]

    return ChatResponse(answer=answer, sources=sources)


@app.post("/lead")
def lead(request: LeadIn, http_request: Request):
    """
    Accept a visitor's contact details (FR-08 to FR-10, FR-13).

    FastAPI checks the request against LeadIn before this runs, and answers
    a bad one with HTTP 422 and the reason, e.g. a phone number of "abc".
    A valid lead is sent to n8n, or kept on disk if n8n can't take it, so the
    visitor is always told it was received and no lead is ever lost.
    """
    refuse_if_over_limit(ratelimit.check_lead, http_request)

    return handle_lead(request, N8N_WEBHOOK_URL, demo=LEADS_DEMO_MODE)


# ---------------------------------------------------------------------------
# Run the server when this file is executed directly
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    load_knowledge()
    if LOAD_ERROR:
        fail(LOAD_ERROR)

    print()
    print("=" * 68)
    print("  Bella Real Estate Assistant")
    print("=" * 68)
    print(f"  Knowledge base: {CHUNK_COUNT} chunks")
    print(f"  Chat model:     {CHAT_MODEL}")
    print(f"  Prompt version: {PROMPT_VERSION}")
    print(f"  Leads go to:    {LEADS_GO_TO}")
    print(f"  Allowed origins: {ALLOWED_ORIGINS or DEFAULT_ORIGINS}")
    print(f"  Rate limits:     {ratelimit.settings_summary()}")
    print(f"  Area filtering:  {len(AREA_VOCABULARY)} areas "
          f"({', '.join(sorted(AREA_VOCABULARY)) if AREA_VOCABULARY else 'none - run ingest.py'})")
    print()
    print("  Open http://127.0.0.1:8000/docs to try it.")
    print("  Press Ctrl+C to stop.")
    print("=" * 68)
    print()

    uvicorn.run(app, host="127.0.0.1", port=8000)
