# syntax=docker/dockerfile:1
#
# Dockerfile - Task 3.2
# The recipe Render (free web service) follows to run the backend.
# (Written for Hugging Face Spaces first; HF made Docker Spaces paid in 2026.)
# Line by line: docs/15_docker.md

# A small Linux with Python 3.14, the same Python version as the project laptop.
FROM python:3.14-slim

# Run as an ordinary user (ID 1000), not as root: safer, and every file
# below belongs to it.
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    PYTHONUNBUFFERED=1
WORKDIR $HOME/app

# 1. Packages. Copied on their own first so Docker can reuse this slow step
#    when only the code changes. The lock file gives the exact versions
#    tested on the laptop.
COPY --chown=user backend/requirements.lock.txt backend/requirements.lock.txt
RUN pip install --no-cache-dir --user -r backend/requirements.lock.txt

# 2. The code and the company documents. .dockerignore keeps out .env, the
#    local search index, lead data and everything the server doesn't need.
COPY --chown=user backend/ backend/
COPY --chown=user data/ data/

# 3. Build the search index now, while the image is being built (NFR-06).
#    The index then lives inside the image, so a restart needs no embedding
#    calls at all.
#    The API key is a build *secret*. On Render it is a "Secret File" named
#    GEMINI_API_KEY. It is mounted for this one step only (uid=1000 so our
#    user can read it) and is never stored in the image.
ARG GEMINI_EMBEDDING_MODEL
ENV GEMINI_EMBEDDING_MODEL=$GEMINI_EMBEDDING_MODEL
RUN --mount=type=secret,id=GEMINI_API_KEY,uid=1000,required=true \
    GEMINI_API_KEY="$(cat /run/secrets/GEMINI_API_KEY)" \
    python backend/ingest.py --delay 1

# 4. Start the server. Render tells it which port to use in $PORT;
#    7860 is only the fallback.
EXPOSE 7860
CMD ["sh", "backend/start.sh"]
