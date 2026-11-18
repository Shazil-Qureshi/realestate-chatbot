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
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
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
PROMPT_VERSION = "2026-11-16c (9 rules, completeness rule 8)"

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

3. Respect every constraint in the question. If the customer names a city, a
   budget, a number of bedrooms or a property type, only mention properties
   that match all of them. The extracts may include properties that do not
   match - ignore those. If nothing in the extracts matches, say nothing
   matches rather than offering the closest thing.

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

import chromadb  # noqa: E402
from google import genai  # noqa: E402
from google.genai import types  # noqa: E402

from leads import LeadIn, handle_lead  # noqa: E402

gemini = genai.Client(api_key=API_KEY)

db = chromadb.PersistentClient(path=str(DB_DIR))
try:
    collection = db.get_collection(name=COLLECTION_NAME)
except Exception:
    fail(
        f"Collection '{COLLECTION_NAME}' not found. "
        "Run 'python backend\\ingest.py' first."
    )

CHUNK_COUNT = collection.count()
if CHUNK_COUNT == 0:
    fail("The collection is empty. Run 'python backend\\ingest.py' first.")

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


@app.get("/health")
def health():
    """Confirm the server is running and the knowledge base is loaded."""
    return {
        "status": "ok",
        "prompt_version": PROMPT_VERSION,
        "chunks": CHUNK_COUNT,
        "chat_model": CHAT_MODEL,
        "embedding_model": EMBED_MODEL,
        # Says where leads go without revealing the webhook address itself.
        "leads_go_to": "n8n" if N8N_WEBHOOK_URL else "local file (n8n not set up)",
    }


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """
    Answer one question.

    Three steps: turn the question into numbers, find the closest chunks,
    then ask Gemini to answer using only those chunks.
    """
    question = request.message.strip()

    if not question:
        raise HTTPException(status_code=400, detail="The message is empty.")
    if len(question) > MAX_QUESTION_CHARS:
        raise HTTPException(
            status_code=400,
            detail=f"The message is too long. Limit is {MAX_QUESTION_CHARS} characters.",
        )

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
        found = collection.query(
            query_embeddings=[question_vector], n_results=TOP_K
        )
    except Exception as error:
        raise HTTPException(
            status_code=503, detail=f"Could not search the knowledge base: {error}"
        )

    documents = found.get("documents", [[]])[0]
    metadatas = found.get("metadatas", [[]])[0]
    distances = found.get("distances", [[]])[0]

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
def lead(request: LeadIn):
    """
    Accept a visitor's contact details (FR-08 to FR-10, FR-13).

    FastAPI checks the request against LeadIn before this runs, and answers
    a bad one with HTTP 422 and the reason, e.g. a phone number of "abc".
    A valid lead is sent to n8n, or kept on disk if n8n can't take it, so the
    visitor is always told it was received and no lead is ever lost.
    """
    return handle_lead(request, N8N_WEBHOOK_URL)


# ---------------------------------------------------------------------------
# Run the server when this file is executed directly
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    print()
    print("=" * 68)
    print("  Bella Real Estate Assistant")
    print("=" * 68)
    print(f"  Knowledge base: {CHUNK_COUNT} chunks")
    print(f"  Chat model:     {CHAT_MODEL}")
    print(f"  Prompt version: {PROMPT_VERSION}")
    print(f"  Leads go to:    {'n8n' if N8N_WEBHOOK_URL else 'backend/leads/pending.jsonl (n8n not set up)'}")
    print(f"  Allowed origins: {ALLOWED_ORIGINS or DEFAULT_ORIGINS}")
    print()
    print("  Open http://127.0.0.1:8000/docs to try it.")
    print("  Press Ctrl+C to stop.")
    print("=" * 68)
    print()

    uvicorn.run(app, host="127.0.0.1", port=8000)
