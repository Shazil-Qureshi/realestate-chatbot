#!/bin/sh
# start.sh - Task 3.2. Runs every time the container starts.

cd "$(dirname "$0")"

# Safety net for NFR-06. The index is built into the image, so normally
# this is skipped without loading anything: on a slow free server, even
# opening the database takes a long time, and Render gives up if the web
# port isn't open soon. Only if the index is missing is it rebuilt (that
# makes Gemini calls). If the rebuild fails, the server starts anyway and
# /health reports the problem.
if [ -f chroma_db/chroma.sqlite3 ]; then
    echo "[start] search index found in the image - skipping ingest"
else
    echo "[start] no search index - building it now"
    python ingest.py --delay 1 || echo "[start] ingest.py did not finish - starting the server anyway"
fi

# 0.0.0.0 means "accept connections from outside the container", not just
# from inside it. 127.0.0.1 would make the server unreachable.
# $PORT is set by the host (Render); 7860 is only the fallback.
exec uvicorn main:app --host 0.0.0.0 --port "${PORT:-7860}"
