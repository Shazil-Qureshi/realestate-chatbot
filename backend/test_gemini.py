"""
test_gemini.py - Task 1.5

Checks that your Gemini API key works, and shows you which models your
key is actually allowed to use.

Run it from the project folder with the virtual environment active:

    python backend\test_gemini.py

It never prints your API key. It only prints whether a key was found
and how long it is.

Exit code 0 means every step that ran, passed.
"""

import os
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Small helpers so every line of output looks the same
# ---------------------------------------------------------------------------

PASS = "[PASS]"
FAIL = "[FAIL]"
SKIP = "[SKIP]"
INFO = "      "

failures = []


def ok(message):
    print(f"{PASS} {message}")


def bad(message, fix=""):
    print(f"{FAIL} {message}")
    if fix:
        print(f"{INFO} Fix: {fix}")
    failures.append(message)


def skipped(message, why=""):
    print(f"{SKIP} {message}")
    if why:
        print(f"{INFO} {why}")


def info(message):
    print(f"{INFO} {message}")


# ---------------------------------------------------------------------------
# Step 1 - find and load backend/.env
# ---------------------------------------------------------------------------

print()
print("=" * 68)
print("  Gemini API check - Task 1.5")
print("=" * 68)
print()
print("[1/4] Reading backend/.env")
print()

# __file__ is this script. .parent is the backend folder.
BACKEND_DIR = Path(__file__).resolve().parent
ENV_PATH = BACKEND_DIR / ".env"

info(f"Looking for: {ENV_PATH}")

if not ENV_PATH.exists():
    bad(
        "backend/.env does not exist",
        "Copy backend/.env.example to backend/.env, then paste your key into it.",
    )
    print()
    print("Cannot continue without the file. Stopping here.")
    sys.exit(1)

ok("backend/.env found")

try:
    from dotenv import load_dotenv
except ImportError:
    bad(
        "The python-dotenv package is not installed",
        "Activate .venv, then run: pip install -r backend\\requirements.txt",
    )
    sys.exit(1)

# override=True means the file wins over anything already set in the terminal.
load_dotenv(ENV_PATH, override=True)

api_key = os.getenv("GEMINI_API_KEY", "").strip()

if not api_key:
    bad(
        "GEMINI_API_KEY is empty in backend/.env",
        "Open backend/.env and paste your key after GEMINI_API_KEY=",
    )
    sys.exit(1)

if api_key == "your_gemini_api_key_here":
    bad(
        "GEMINI_API_KEY still holds the placeholder text",
        "Replace your_gemini_api_key_here with the real key from AI Studio.",
    )
    sys.exit(1)

# Never print the key itself. Its length is enough to prove it was read.
ok(f"GEMINI_API_KEY loaded ({len(api_key)} characters)")

chat_model = os.getenv("GEMINI_CHAT_MODEL", "").strip()
embed_model = os.getenv("GEMINI_EMBEDDING_MODEL", "").strip()

# ---------------------------------------------------------------------------
# Step 2 - ask Gemini which models this key can use
# ---------------------------------------------------------------------------

print()
print("[2/4] Asking Gemini which models your key can use")
print()

try:
    from google import genai
except ImportError:
    bad(
        "The google-genai package is not installed",
        "Activate .venv, then run: pip install -r backend\\requirements.txt",
    )
    sys.exit(1)

try:
    client = genai.Client(api_key=api_key)
except Exception as error:
    bad(f"Could not create the Gemini client: {error}")
    sys.exit(1)

chat_models = []
embedding_models = []
all_models = []

try:
    for model in client.models.list():
        # model.name looks like "models/gemini-...". Strip the prefix so the
        # name can be pasted straight into .env.
        name = getattr(model, "name", "") or ""
        short = name.split("/")[-1]
        if not short:
            continue
        all_models.append(short)

        # supported_actions is not guaranteed to exist in every SDK version,
        # so fall back to the name if it is missing.
        actions = getattr(model, "supported_actions", None)
        if actions:
            if "generateContent" in actions:
                chat_models.append(short)
            if "embedContent" in actions:
                embedding_models.append(short)
        else:
            if "embedding" in short or "embed" in short:
                embedding_models.append(short)
            else:
                chat_models.append(short)

except Exception as error:
    bad(f"Could not list models: {error}")
    info("A 400 or 403 error here almost always means the API key is wrong.")
    sys.exit(1)

if not all_models:
    bad("The key worked but returned no models at all")
    sys.exit(1)

ok(f"Key accepted. {len(all_models)} models visible to this key.")

print()
info("Models that can answer questions (for GEMINI_CHAT_MODEL):")
for name in chat_models:
    print(f"        - {name}")

print()
info("Models that can create embeddings (for GEMINI_EMBEDDING_MODEL):")
for name in embedding_models:
    print(f"        - {name}")

# ---------------------------------------------------------------------------
# Step 3 - try a real question
# ---------------------------------------------------------------------------

print()
print("[3/4] Sending one real question")
print()

if not chat_model:
    skipped(
        "GEMINI_CHAT_MODEL is not set in backend/.env",
        "Pick a name from the chat list above and put it in .env, then re-run.",
    )
elif chat_model not in all_models:
    bad(
        f"GEMINI_CHAT_MODEL is set to '{chat_model}', which your key cannot use",
        "Replace it in backend/.env with one of the names listed above.",
    )
else:
    try:
        response = client.models.generate_content(
            model=chat_model,
            contents="Reply with exactly one word: working",
        )
        text = (response.text or "").strip()
        if text:
            ok(f"{chat_model} replied: {text}")
        else:
            bad(f"{chat_model} returned an empty reply")
    except Exception as error:
        bad(f"The question failed: {error}")

# ---------------------------------------------------------------------------
# Step 4 - try a real embedding
# ---------------------------------------------------------------------------

print()
print("[4/4] Creating one embedding")
print()

if not embed_model:
    skipped(
        "GEMINI_EMBEDDING_MODEL is not set in backend/.env",
        "Pick a name from the embedding list above and put it in .env, then re-run.",
    )
elif embed_model not in all_models:
    bad(
        f"GEMINI_EMBEDDING_MODEL is set to '{embed_model}', which your key cannot use",
        "Replace it in backend/.env with one of the names listed above.",
    )
else:
    try:
        result = client.models.embed_content(
            model=embed_model,
            contents="A three bedroom apartment in Islamabad",
        )
        vector = result.embeddings[0].values
        ok(f"{embed_model} returned a vector of {len(vector)} numbers")
        info(f"First 3 numbers: {[round(v, 4) for v in vector[:3]]}")
        info("That list of numbers is what ChromaDB will store and search.")
    except Exception as error:
        bad(f"The embedding failed: {error}")

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

print()
print("=" * 68)
if failures:
    print(f"  {len(failures)} check(s) failed. Fix the lines marked [FAIL] above.")
    print("=" * 68)
    print()
    sys.exit(1)

print("  All checks that ran, passed.")
print("=" * 68)
print()
