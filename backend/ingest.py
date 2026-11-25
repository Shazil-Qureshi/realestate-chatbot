r"""
ingest.py - Task 1.6

Reads every Markdown file in data/, splits each into self-contained chunks,
turns each chunk into an embedding with Gemini, and stores them in ChromaDB.

Run a dry run FIRST. It does all the chunking and prints what it found,
without calling the API or spending any quota:

    python backend\ingest.py --dry-run

When the numbers look right, run it for real:

    python backend\ingest.py

Safe to run again. Chunks already stored are skipped, so a run that stops
half way can be resumed without paying for the same embeddings twice.

Options:
    --dry-run        chunk and report only, no API calls, no database writes
    --rebuild        delete the collection first and start clean
    --delay SECONDS  pause between API calls (default 0.5)
"""

import argparse
import os
import re
import statistics
import sys
import time
from pathlib import Path

import listing_meta

# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

# A chunk longer than this gets split again at a blank line.
# 1200 characters is roughly 200 words - about one property listing.
MAX_CHUNK_CHARS = 1200

# A chunk shorter than this is almost certainly a stray heading, not content.
MIN_CHUNK_CHARS = 40

COLLECTION_NAME = "bella_real_estate"

BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BACKEND_DIR.parent
DATA_DIR = PROJECT_DIR / "data"
DB_DIR = BACKEND_DIR / "chroma_db"

PASS = "[PASS]"
FAIL = "[FAIL]"
INFO = "      "


def ok(message):
    print(f"{PASS} {message}")


def bad(message, fix=""):
    print(f"{FAIL} {message}")
    if fix:
        print(f"{INFO} Fix: {fix}")


def info(message):
    print(f"{INFO} {message}")


# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------

def slugify(text):
    """Turn any text into something safe to use inside an ID."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")[:60]


def split_long_section(body):
    """
    Split a section that is over MAX_CHUNK_CHARS.

    Splits at blank lines so sentences are never cut in half, and packs
    paragraphs together until adding one more would cross the limit.
    """
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", body) if p.strip()]
    pieces = []
    current = ""

    for paragraph in paragraphs:
        if not current:
            current = paragraph
        elif len(current) + len(paragraph) + 2 <= MAX_CHUNK_CHARS:
            current = current + "\n\n" + paragraph
        else:
            pieces.append(current)
            current = paragraph

    if current:
        pieces.append(current)

    return pieces


def refresh_metadata(collection, all_chunks, existing_ids):
    """
    Bring stored chunks' metadata up to date without re-embedding anything.

    Task 4.1 added facts to each listing chunk (area, bedrooms, sale or rent).
    An index built before that has the right text and the right embeddings but
    none of those facts, and because this script skips chunks it has already
    stored, they would never arrive.

    The text has not changed, so the embeddings have not changed either. Only
    the metadata needs replacing, and `collection.update` does that on its
    own. **No Gemini request is made here, so this costs nothing.**
    """
    wanted = {c["id"]: c["metadata"] for c in all_chunks if c["id"] in existing_ids}
    if not wanted:
        return

    try:
        stored = collection.get(ids=list(wanted), include=["metadatas"])
    except Exception as error:
        info(f"Could not read stored metadata, leaving it alone ({error})")
        return

    stale_ids, stale_metas = [], []
    for chunk_id, current in zip(stored.get("ids", []), stored.get("metadatas", [])):
        if (current or {}) != wanted[chunk_id]:
            stale_ids.append(chunk_id)
            stale_metas.append(wanted[chunk_id])

    if not stale_ids:
        info("Stored metadata is already up to date")
        return

    try:
        collection.update(ids=stale_ids, metadatas=stale_metas)
    except Exception as error:
        bad(f"Could not update metadata: {error}")
        return

    listings = sum(1 for m in stale_metas if m.get("is_listing"))
    ok(f"Metadata refreshed on {len(stale_ids)} chunks "
       f"({listings} of them property listings). No embeddings were needed.")


def listing_metadata(base, section_heading, body):
    """
    Add the plain facts of a property listing to a chunk's metadata.

    Company pages and FAQs are left exactly as they were: parse_listing only
    recognises a "BRE-x-nnn - ..." heading, and returns None for anything
    else. ChromaDB only stores simple values, so the area keys are joined
    into one string and `area_key` holds the one used for filtering.
    """
    facts = listing_meta.parse_listing(section_heading, body)
    if not facts:
        return base

    merged = dict(base)
    keys = facts.pop("area_keys", "")
    merged.update(facts)
    merged["area_keys"] = keys
    # The field questions are filtered on. Every listing in this data set has
    # exactly one area key; if one ever had two, the first is the primary.
    merged["area_key"] = keys.split(",")[0] if keys else ""
    return merged


def chunk_markdown_file(path):
    """
    Split one Markdown file into self-contained chunks.

    The split happens at '## ' headings, because in this project every
    property, service and FAQ already lives under its own heading.

    Every chunk is prefixed with the document title and its heading. That
    prefix is what makes a chunk make sense on its own - the retrieval step
    pulls out one chunk with no surrounding text, so the chunk has to carry
    its own context.
    """
    raw = path.read_text(encoding="utf-8")
    lines = raw.splitlines()

    # The first '# ' line is the document title.
    title = path.stem
    for line in lines:
        if line.startswith("# "):
            title = line[2:].strip()
            break

    # Walk the file and collect (heading, body) pairs.
    sections = []
    heading = None
    body_lines = []

    for line in lines:
        if line.startswith("## "):
            if heading is not None:
                sections.append((heading, "\n".join(body_lines).strip()))
            heading = line[3:].strip()
            body_lines = []
        elif heading is not None:
            body_lines.append(line)

    if heading is not None:
        sections.append((heading, "\n".join(body_lines).strip()))

    # A file with no '## ' headings becomes one chunk.
    if not sections:
        whole = "\n".join(
            line for line in lines if not line.startswith("# ")
        ).strip()
        if whole:
            sections = [("", whole)]

    relative = path.relative_to(PROJECT_DIR).as_posix()
    chunks = []

    for section_index, (section_heading, body) in enumerate(sections):
        if not body:
            continue

        pieces = (
            [body] if len(body) <= MAX_CHUNK_CHARS else split_long_section(body)
        )

        for part_index, piece in enumerate(pieces):
            if section_heading:
                header = f"{title} - {section_heading}"
            else:
                header = title

            text = f"{header}\n\n{piece}"

            if len(text) < MIN_CHUNK_CHARS:
                continue

            chunk_id = f"{slugify(relative)}--{section_index:02d}-{part_index:02d}"

            chunks.append(
                {
                    "id": chunk_id,
                    "text": text,
                    "metadata": listing_metadata(
                        {
                            "source": relative,
                            "title": title,
                            "heading": section_heading,
                            "part": part_index,
                        },
                        section_heading,
                        piece,
                    ),
                }
            )

    return chunks


def collect_chunks():
    """Chunk every Markdown file under data/, sorted so runs are repeatable."""
    files = sorted(DATA_DIR.rglob("*.md"))
    if not files:
        bad(
            f"No .md files found under {DATA_DIR}",
            "Check that the data folder still contains the 9 business documents.",
        )
        sys.exit(1)

    all_chunks = []
    per_file = []

    for path in files:
        chunks = chunk_markdown_file(path)
        per_file.append((path.relative_to(PROJECT_DIR).as_posix(), len(chunks)))
        all_chunks.extend(chunks)

    return all_chunks, per_file


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def report(all_chunks, per_file):
    print()
    print("Chunks per file:")
    for name, count in per_file:
        print(f"        {count:>3}  {name}")

    sizes = [len(c["text"]) for c in all_chunks]
    words = sum(len(c["text"].split()) for c in all_chunks)

    print()
    info(f"Files:            {len(per_file)}")
    info(f"Chunks:           {len(all_chunks)}")
    info(f"Words total:      {words}")
    info(f"Smallest chunk:   {min(sizes)} characters")
    info(f"Median chunk:     {int(statistics.median(sizes))} characters")
    info(f"Largest chunk:    {max(sizes)} characters")
    info(f"API requests needed: {len(all_chunks)} (one per chunk)")

    print()
    print("-" * 68)
    print("First chunk, exactly as it will be sent to Gemini:")
    print("-" * 68)
    print(all_chunks[0]["text"])
    print("-" * 68)

    duplicate_ids = len(all_chunks) - len({c["id"] for c in all_chunks})
    if duplicate_ids:
        bad(f"{duplicate_ids} duplicate chunk IDs - this would overwrite data")
        sys.exit(1)
    ok("All chunk IDs are unique")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Ingest documents into ChromaDB.")
    parser.add_argument("--dry-run", action="store_true",
                        help="chunk and report only; no API calls")
    parser.add_argument("--rebuild", action="store_true",
                        help="delete the collection first")
    parser.add_argument("--delay", type=float, default=0.5,
                        help="seconds to pause between API calls")
    args = parser.parse_args()

    print()
    print("=" * 68)
    print("  Document ingestion - Task 1.6")
    print("=" * 68)
    print()
    print("[1/4] Reading and chunking documents")
    print()
    info(f"Data folder: {DATA_DIR}")

    all_chunks, per_file = collect_chunks()
    ok(f"{len(all_chunks)} chunks built from {len(per_file)} files")
    report(all_chunks, per_file)

    if args.dry_run:
        print()
        print("=" * 68)
        print("  Dry run. Nothing was sent to Gemini and nothing was stored.")
        print("  Run without --dry-run when the numbers above look right.")
        print("=" * 68)
        print()
        return

    # -----------------------------------------------------------------------
    # Load settings
    # -----------------------------------------------------------------------

    print()
    print("[2/4] Loading settings")
    print()

    from dotenv import load_dotenv

    # On your laptop the settings come from backend/.env. In the Docker
    # container (Render) there is no .env file: the settings arrive as
    # environment variables instead, so a missing file is not an error.
    env_path = BACKEND_DIR / ".env"
    if env_path.exists():
        load_dotenv(env_path, override=True)
        info("Settings read from backend/.env")
    else:
        info("No backend/.env - using environment variables (Docker / Render)")

    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    embed_model = os.getenv("GEMINI_EMBEDDING_MODEL", "").strip()

    if not api_key:
        bad("GEMINI_API_KEY is empty", "Complete Task 1.5 first.")
        sys.exit(1)
    if not embed_model:
        bad("GEMINI_EMBEDDING_MODEL is empty", "Complete Task 1.5 first.")
        sys.exit(1)

    ok(f"Key loaded ({len(api_key)} characters)")
    ok(f"Embedding model: {embed_model}")

    # -----------------------------------------------------------------------
    # Open the database
    # -----------------------------------------------------------------------

    print()
    print("[3/4] Opening the vector database")
    print()

    import chromadb
    from google import genai

    DB_DIR.mkdir(parents=True, exist_ok=True)
    db = chromadb.PersistentClient(path=str(DB_DIR))

    if args.rebuild:
        try:
            db.delete_collection(name=COLLECTION_NAME)
            info("Existing collection deleted (--rebuild)")
        except Exception:
            info("No existing collection to delete")

    # "cosine" compares the direction of two vectors rather than the distance
    # between their end points, which is the right measure for text meaning.
    try:
        collection = db.get_or_create_collection(
            name=COLLECTION_NAME,
            configuration={"hnsw": {"space": "cosine"}},
        )
    except TypeError:
        # Older ChromaDB versions used a different keyword for the same thing.
        collection = db.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

    ok(f"Collection '{COLLECTION_NAME}' open at {DB_DIR}")

    try:
        existing_ids = set(collection.get(include=[])["ids"])
    except Exception:
        existing_ids = set()

    todo = [c for c in all_chunks if c["id"] not in existing_ids]

    if existing_ids:
        info(f"{len(existing_ids)} chunks already stored, {len(todo)} to go")
        refresh_metadata(collection, all_chunks, existing_ids)

    if not todo:
        ok("Everything is already ingested. Nothing to do.")
        if not verify(collection, api_key, embed_model):
            sys.exit(1)
        return

    # -----------------------------------------------------------------------
    # Embed and store
    # -----------------------------------------------------------------------

    print()
    print(f"[4/4] Embedding {len(todo)} chunks")
    print()
    info("One chunk per request. See docs/07_ingestion.md for why.")
    info(f"Estimated time: about {int(len(todo) * (args.delay + 0.6))} seconds")
    print()

    client = genai.Client(api_key=api_key)
    stored = 0
    failed = []

    for index, chunk in enumerate(todo, start=1):
        vector = embed_one(client, embed_model, chunk["text"])

        if vector is None:
            failed.append(chunk["id"])
            print(f"      {index:>3}/{len(todo)}  FAILED  {chunk['id']}")
            # If the first three all fail, the problem is the key, the model
            # or the quota, not one chunk. Stop now instead of spending
            # minutes failing the other 53.
            if stored == 0 and len(failed) >= 3:
                print()
                bad("Gemini refused the first 3 chunks - stopping early")
                bad(f"Gemini's error: {LAST_ERROR}")
                sys.exit(1)
            continue

        collection.upsert(
            ids=[chunk["id"]],
            documents=[chunk["text"]],
            embeddings=[vector],
            metadatas=[chunk["metadata"]],
        )
        stored += 1

        if index == 1 or index % 10 == 0 or index == len(todo):
            print(f"      {index:>3}/{len(todo)}  stored  {chunk['id']}")

        time.sleep(args.delay)

    print()
    total = collection.count()
    if failed:
        bad(f"{len(failed)} chunks failed")
        for chunk_id in failed:
            info(chunk_id)
        info("Run the command again - stored chunks are skipped automatically.")
    ok(f"{stored} chunks stored. Collection now holds {total}.")

    # A partial or empty index must stop here with an error. Exiting
    # "successfully" let a Docker build carry on with an empty index
    # (Render deploy d2adb64, 19 Nov 2026).
    if failed or total < len(all_chunks):
        if LAST_ERROR:
            bad(f"Gemini's last error: {LAST_ERROR}")
        bad(f"Index incomplete: {total} of {len(all_chunks)} chunks stored")
        sys.exit(1)
    if not verify(collection, api_key, embed_model):
        sys.exit(1)


# The last error Gemini returned, printed at the end so it is easy to find
# in a long build log.
LAST_ERROR = None


def embed_one(client, model, text, attempts=3):
    """
    Embed one piece of text and return its list of numbers.

    One chunk per request, deliberately. Passing a list of texts to
    gemini-embedding-2 returns ONE combined embedding for all of them,
    not one per item - which would silently destroy retrieval.
    """
    for attempt in range(1, attempts + 1):
        try:
            result = client.models.embed_content(model=model, contents=text)
            return list(result.embeddings[0].values)
        except Exception as error:
            global LAST_ERROR
            LAST_ERROR = str(error)[:500]
            if attempt == attempts:
                print(f"{INFO} giving up after {attempts} tries: {error}")
                return None
            wait = 5 * attempt
            print(f"{INFO} error ({error}); retrying in {wait}s")
            time.sleep(wait)
    return None


def verify(collection, api_key, embed_model):
    """Prove the database actually answers a question, not just that it saved."""
    print()
    print("-" * 68)
    print("Verification: searching for 'apartment for rent in Islamabad'")
    print("-" * 68)

    from google import genai

    client = genai.Client(api_key=api_key)
    query_vector = embed_one(client, embed_model, "apartment for rent in Islamabad")

    if query_vector is None:
        bad("Could not embed the test question")
        return False

    results = collection.query(query_embeddings=[query_vector], n_results=3)

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    if not documents:
        bad("The search returned nothing")
        return False

    for rank, (doc, meta, dist) in enumerate(
        zip(documents, metadatas, distances), start=1
    ):
        first_line = doc.splitlines()[0]
        print(f"  {rank}. {first_line}")
        print(f"     source: {meta.get('source')}   distance: {dist:.4f}")

    print("-" * 68)
    ok("Search works. Lower distance means a closer match.")
    print()
    return True


if __name__ == "__main__":
    main()
