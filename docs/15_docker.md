# 15 · Docker Image for the Backend

| | |
|---|---|
| **Task** | 3.2 Dockerfile |
| **Date** | 18 November 2026 |
| **Files** | `Dockerfile`, `backend/start.sh`, `.dockerignore`, `.gitattributes`; `backend/ingest.py` (small change) |
| **Requirements** | NFR-06 (index rebuilt automatically), NFR-03 (no secrets in the image) |
| **Status** | Files written and checked by reading. **The image has not been built yet.** First build happens on Render in Task 3.3. |

## Terms

| Term | What it is | Example here |
|---|---|---|
| **Docker image** | A packaged, ready-to-run copy of a program with everything it needs: Linux, Python, packages, code. | Python 3.14 + the 98 locked packages + `backend/` + `data/` + the search index |
| **Container** | An image while it is running. | What Render starts when someone opens the site |
| **Dockerfile** | The recipe for building an image, step by step. | `Dockerfile` at the project root |
| **`.dockerignore`** | Like `.gitignore`, for Docker: what must not go into the image. | `.env`, lead data, the laptop's index |
| **Build secret** | A secret handed to one build step and never stored in the image. | `GEMINI_API_KEY` while the index is built |
| **Port** | A numbered door on a computer that a server listens behind. | Render tells the server which port to use in `$PORT` |

## Change of host: Render, not Hugging Face (18 Nov)

This file was written for Hugging Face Spaces. When the Space was being
created, Hugging Face said **Docker Spaces now need a paid plan**. Forum
reports date the change to July 2026, with no announcement. The technical
docs had been checked but not current pricing. That was a mistake, and pricing
is now checked before any hosting choice.

The owner chose **Render's free web service** instead. Render, checked on
18 November 2026 ([free tier](https://render.com/docs/free),
[Docker secrets](https://render.com/docs/docker-secrets)):

- **No card needed.** It builds from the GitHub repository with our `Dockerfile`.
- **Sleeps after 15 minutes** without visitors, and **waking takes about a
  minute**. 750 free hours a month, which is enough for one service.
- **Disk is wiped** on restart, redeploy and sleep. Free services can't have a
  persistent disk.
- **Build secrets** come from "Secret Files", mounted in a `RUN` step. Our
  user needs `uid=1000` to read the mount. Render also copies secret files into
  the build folder, so `.dockerignore` lists `GEMINI_API_KEY`.
- **Environment variables** reach the build as `ARG`s, and the running server
  as normal environment variables. `PORT` tells the server which port to use.

Only small changes were needed: `uid=1000` on the secret mount, the
`.dockerignore` line, and comments. The design below stays the same.

## Key decision: build the search index inside the image

NFR-06 says the chatbot must work after a restart with no manual step. The
running container's disk is wiped on every restart, so there were two
options:

| Option | Embedding calls | Problem |
|---|---|---|
| Build the index each time the container **starts** | 56 on every restart | Uses free-tier quota on every restart. A restart while the quota is used up gives a chatbot with no knowledge. |
| Build the index while the **image is built** (chosen) | 56 per build, 0 per restart | The build needs the key, given as a build secret. |

Render rebuilds the image only when new code is pushed. Waking from sleep and
restarts reuse the image, index included. On Render this matters even more
than on Hugging Face: the server sleeps after every 15 quiet minutes, so
indexing on start would cost 56 calls on almost every visit.

`start.sh` still runs `ingest.py` on start as a safety net. It skips every
chunk already stored, so with the index present the only call it makes is
the one verification search at the end. If the index were somehow missing,
it rebuilds it. If that fails, the server starts anyway and `/health` shows
the chunk count, so the failure is visible and not silent.

## The files

**`Dockerfile`** has four steps:
1. Install the packages from `backend/requirements.lock.txt`, the exact
   versions tested on the laptop. This is copied first so Docker can reuse
   the slow install when only code changes.
2. Copy `backend/` and `data/`.
3. Build the index, with the key mounted as a secret for this step only.
4. Start `backend/start.sh`.

**`backend/start.sh`** runs the safety-net ingest, then
`uvicorn main:app --host 0.0.0.0 --port 7860`. `0.0.0.0` means "accept
connections from outside the container". The laptop uses `127.0.0.1`, which
would make the server unreachable inside Docker.

**`.dockerignore`** keeps out:
- `backend/.env` (secrets)
- `backend/leads` (personal data)
- `backend/chroma_db`: the laptop's index. It must not be copied, because the
  image builds its own.
- `.venv`, caches, `.git`
- `docs`, `tests`, `web` and `n8n`: the server doesn't need them, and the
  website is hosted separately on GitHub Pages.

**`.gitattributes`** keeps `start.sh` and the `Dockerfile` with Linux line
endings. Windows Git would otherwise convert them, and Linux would then fail
to run the script.

**`backend/ingest.py` change.** It used to stop if `backend/.env` was
missing. In the container there is no `.env`: the settings arrive as
environment variables. It now reads `.env` when it exists, and the
environment otherwise. Checked here:

| Check | Result |
|---|---|
| No `.env`, no key | "No backend/.env - using environment variables", then "GEMINI_API_KEY is empty", stops |
| No `.env`, key set as an environment variable | "Key loaded" |
| `--dry-run` | 56 chunks, all IDs unique |
| Laptop with `.env` (18 Nov, 11:48) | **Pass**: "Settings read from backend/.env", "56 chunks already stored, 0 to go", verification search worked. Also closes ING-06. |

## Settings the server will need (Task 3.3)

| Name | Kind | Value |
|---|---|---|
| `GEMINI_API_KEY` | **Secret File** (build) and **environment variable** (running server) | Your key, typed into Render's settings page by you, never into a project file |
| `GEMINI_EMBEDDING_MODEL` | Variable | `gemini-embedding-2`. **Must match** what built the index. |
| `GEMINI_CHAT_MODEL` | Variable | `gemini-3.5-flash-lite` |
| `ALLOWED_ORIGINS` | Variable | The GitHub Pages address, set in 3.4/3.5 |
| `N8N_WEBHOOK_URL` | (left empty for now) | n8n runs on the laptop, which the internet can't reach. See below. |

## Known limits

- **Leads from the live demo:** decided in 3.3. Demo mode checks the details
  and then discards them (`docs/16_render.md`).
- **The build hasn't run yet.** Every package must have a ready-made Linux
  wheel for Python 3.14; if one doesn't, the build fails with a compile error.
  That would show in the build log in 3.3, and the fix is the
  `python:3.13-slim` base image.
- **Each build costs 56 embedding calls.** RATE-01 (free-tier limits) is still
  open.

## Tests

| Test ID | Check | Result |
|---|---|---|
| DOCK-01 | `start.sh` is valid shell | **Pass** (`sh -n`) |
| DOCK-02 | `ingest.py` works without `.env` | **Pass** (table above) |
| DOCK-03 | `ingest.py` still works with `.env` on the laptop | **Pass** (18 Nov): 56 stored, 0 to do |
| DOCK-04 | Image builds on Render | Not yet run (3.3) |
| DOCK-05 | Build log shows 56 chunks stored | Not yet run (3.3) |
| DOCK-06 | `/health` on Render: `status: ok`, 56 chunks | Not yet run (3.3) |
| DOCK-07 | After sleeping and waking: still 56 chunks, no new embedding calls in the log | Not yet run (3.3), proves NFR-06 / AC-10 |
| DOCK-08 | Image contains no `.env` or lead data | Not yet run (3.3) |

Docker couldn't be run in the build workspace (no Docker engine). Installing
Docker Desktop on the laptop isn't needed just for this. Render's own
build is the first real build, and its log shows every step.
