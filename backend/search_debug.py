r"""
search_debug.py - a diagnostic tool, not part of the application

Shows exactly how the vector search ranks every chunk for a question,
without involving the language model at all.

Use it when an answer is missing something and you need to know whether
the chunk was retrieved and ignored, or never retrieved at all.

    python backend\search_debug.py "three bedroom properties for sale"

    python backend\search_debug.py "three bedroom properties for sale" --find BRE-S-302

    python backend\search_debug.py "..." --top 20

Costs one Gemini request per run (embedding the question). The search
itself runs locally and is free.
"""

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent
DB_DIR = BACKEND_DIR / "chroma_db"
COLLECTION_NAME = "bella_real_estate"

load_dotenv(BACKEND_DIR / ".env", override=True)

API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
EMBED_MODEL = os.getenv("GEMINI_EMBEDDING_MODEL", "").strip()

if not API_KEY or not EMBED_MODEL:
    print("[FAIL] GEMINI_API_KEY or GEMINI_EMBEDDING_MODEL missing from backend/.env")
    sys.exit(1)

if not DB_DIR.exists():
    print(f"[FAIL] No database at {DB_DIR}. Run 'python backend\\ingest.py' first.")
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Inspect vector search rankings.")
    parser.add_argument("question", help="the question to search with")
    parser.add_argument("--top", type=int, default=15,
                        help="how many ranks to print (default 15)")
    parser.add_argument("--find", action="append", default=[],
                        help="a reference code to locate at any rank; repeatable")
    args = parser.parse_args()

    import chromadb
    from google import genai

    db = chromadb.PersistentClient(path=str(DB_DIR))
    collection = db.get_collection(name=COLLECTION_NAME)
    total = collection.count()

    client = genai.Client(api_key=API_KEY)
    embedded = client.models.embed_content(
        model=EMBED_MODEL, contents=args.question
    )
    vector = list(embedded.embeddings[0].values)

    # Ask for everything, so a chunk's true rank is visible however low it is.
    results = collection.query(query_embeddings=[vector], n_results=total)

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    print()
    print("=" * 76)
    print(f'  Question: "{args.question}"')
    print(f"  {total} chunks in the collection")
    print("=" * 76)
    print()

    for rank, (meta, dist) in enumerate(zip(metadatas, distances), start=1):
        if rank > args.top:
            break
        heading = meta.get("heading") or meta.get("title") or ""
        source = (meta.get("source") or "").replace("data/", "")
        print(f"  {rank:>3}.  {dist:.4f}  {source:<34} {heading[:60]}")

    if args.top < total:
        print(f"       ... {total - args.top} more")

    # Where did a specific property end up?
    for wanted in args.find:
        print()
        hit = None
        for rank, (doc, meta, dist) in enumerate(
            zip(documents, metadatas, distances), start=1
        ):
            heading = meta.get("heading") or ""
            if wanted in heading or wanted in doc:
                hit = (rank, dist, meta)
                break

        if hit is None:
            print(f"  [FAIL] {wanted} is not in the collection at all.")
            continue

        rank, dist, meta = hit
        print(f"  {wanted} is at rank {rank} of {total}, distance {dist:.4f}")
        print(f"         {meta.get('source')} :: {meta.get('heading')}")

        if rank <= 8:
            print("         Within the current TOP_K of 8. It WAS retrieved.")
            print("         So the system instruction dropped it, not the search.")
        elif rank <= 16:
            print("         Just outside TOP_K. Raising TOP_K would reach it,")
            print("         at the cost of sending more irrelevant extracts.")
        else:
            print("         Far outside TOP_K. Raising it is not a sensible fix.")
            print("         The chunk text or metadata filtering is the real answer.")

    print()


if __name__ == "__main__":
    main()
