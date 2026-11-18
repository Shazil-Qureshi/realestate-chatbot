# 15 · Docker Image for the Backend

| | |
|---|---|
| **Task** | 3.2 Dockerfile |
| **Date** | 18 November 2026 |
| **Files** | `Dockerfile`, `backend/start.sh`, `.dockerignore`, `.gitattributes`; `backend/ingest.py` (small change) |
| **Requirements** | NFR-06 (index rebuilt automatically), NFR-03 (no secrets in the image) |
| **Status** | Files written and checked by reading. **The image has not been built yet.** First build happens on Hugging Face in Task 3.3. |

## Terms

| Term | What it is | Example here |
|---|---|---|
| **Docker image** | A packaged, ready-to-run copy of a program with everything it needs: Linux, Python, packages, code. | Python 3.14 + the 98 locked packages + `backend/` + `data/` + the search index |
| **Container** | An image while it is running. | What Hugging Face starts when someone opens the Space |
| **Dockerfile** | The recipe for building an image, step by step. | `Dockerfile` at the project root |
| **`.dockerignore`** | Like `.gitignore`, for Docker: what must not go into the image. | `.env`, lead data, the laptop's index |
| **Build secret** | A secret handed to one build step and never stored in the image. | `GEMINI_API_KEY` while the index is built |
| **Port** | A numbered door on a computer that a server listens behind. | Hugging Face sends visitors to 7860 |

## Hugging Face rules this follows

Checked on 18 November 2026 against the
[Docker Spaces documentation](https://huggingface.co/docs/hub/spaces-sdks-docker):

- The Space's `README.md` needs `sdk: docker`. The default port is **7860**
  (`app_port` can change it). This is set up in 3.3.
- The container runs as **user ID 1000**. Create that user and use
  `COPY --chown=user`.
- **Secrets** reach the build as a mounted file (`/run/secrets/<NAME>`) and the
  running container as environment variables. **Variables** reach the build as
  `ARG`.
- **Disk is not kept across restarts** unless a paid storage bucket is attached.

## Key decision: build the search index inside the image

NFR-06 says the chatbot must work after a restart with no manual step. The
running container's disk is wiped on every restart, so there were two
options:

| Option | Embedding calls | Problem |
|---|---|---|
| Build the index each time the container **starts** | 56 on every restart | Uses free-tier quota on every restart. A restart while the quota is used up gives a chatbot with no knowledge. |
| Build the index while the **image is built** (chosen) | 56 per build, 0 per restart | The build needs the key, given as a build secret. |

Hugging Face rebuilds the image only when the Space's files change.
Restarts reuse the image, index included.

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

## Settings the Space will need (Task 3.3)

| Name | Kind | Value |
|---|---|---|
| `GEMINI_API_KEY` | **Secret** | Your key. Typed into Hugging Face's settings page by you, never into a file. |
| `GEMINI_EMBEDDING_MODEL` | Variable | `gemini-embedding-2`. **Must match** what built the index. |
| `GEMINI_CHAT_MODEL` | Variable | `gemini-3.5-flash-lite` |
| `ALLOWED_ORIGINS` | Variable | The GitHub Pages address, set in 3.4/3.5 |
| `N8N_WEBHOOK_URL` | (left empty for now) | n8n runs on the laptop, which the internet can't reach. See below. |

## Known limits

- **Leads from the live demo** go to `pending.jsonl` inside the container, and
  that file is lost on restart. The laptop's n8n can't be reached from
  Hugging Face. Recorded as N8N-S1. It needs a decision in 3.3: hosted n8n,
  or the live demo saying plainly that leads aren't kept.
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
| DOCK-04 | Image builds on Hugging Face | Not yet run (3.3) |
| DOCK-05 | Build log shows 56 chunks stored | Not yet run (3.3) |
| DOCK-06 | `/health` on the Space: `status: ok`, 56 chunks | Not yet run (3.3) |
| DOCK-07 | After a restart: still 56 chunks, no new embedding calls in the log | Not yet run (3.3), proves NFR-06 / AC-10 |
| DOCK-08 | Image contains no `.env` or lead data | Not yet run (3.3) |

Docker couldn't be run in the build workspace (no Docker engine). Installing
Docker Desktop on the laptop isn't needed just for this. Hugging Face's own
build is the first real build, and its log shows every step.
