#!/bin/sh
# start.sh - Task 3.2. Runs every time the container starts.

cd "$(dirname "$0")"

# Safety net for NFR-06. The index was built into the image, so this
# normally finds every chunk already stored and adds nothing. It only does
# real work if the index is missing. If it fails (for example, the Gemini
# quota is used up), the server still starts and /health shows the chunk
# count.
python ingest.py --delay 1 || echo "[start] ingest.py did not finish - starting the server anyway"

# 0.0.0.0 means "accept connections from outside the container", not just
# from inside it. 127.0.0.1 would make the server unreachable.
# $PORT is set by the host (Render); 7860 is only the fallback.
exec uvicorn main:app --host 0.0.0.0 --port "${PORT:-7860}"
