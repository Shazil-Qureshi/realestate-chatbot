# Project Tracker

Last updated: 16 November 2026 (10:40 PKT)

Status values: Not Started · In Progress · Completed · Blocked

## Stage 0 – Planning

| ID | Task | Description | Status | Files | Tested | Documented |
|---|---|---|---|---|---|---|
| 0.1 | Verify services | Check current Gemini model names and free tier | Completed | `backend/.env.example` | n/a | Yes (`01`) |
| 0.2 | Project structure | Create folders and base files | Completed | whole repo | n/a | Yes (`01`) |
| 0.3 | Project overview | Architecture, concepts, risks | Completed | `docs/01_project_overview.md` | n/a | Yes |
| 0.4 | Tracking files | Tracker and daily progress log | Completed | `PROJECT_TRACKER.md`, `DAILY_PROGRESS.md` | n/a | Yes |

## Stage 1 – Backend and AI knowledge base (Day 1)

| ID | Task | Description | Status | Files | Tested | Documented |
|---|---|---|---|---|---|---|
| 1.1 | Environment setup | Python 3.14.10, VS Code, virtual environment | Completed | `backend/check_env.py`, `docs/04_environment_setup.md` | Pass (ENV-01..05, 13 Nov) | Yes |
| 1.2 | Requirements document | 16 functional + 10 non-functional requirements, 10 acceptance criteria | Completed | `docs/02_requirements.md` | Reviewed 13 Nov | Yes |
| 1.3 | Business documents | 9 documents, 17 properties, deliberate gaps for "I don't know" testing | Completed | `data/`, `docs/05_business_documents.md` | Reviewed 14 Nov | Yes |
| 1.4 | Install dependencies | 7 packages installed (98 with dependencies); versions frozen to a lock file | Completed | `backend/requirements.txt`, `backend/requirements.lock.txt`, `docs/04_environment_setup.md` | Pass (DEP-01..05, 16 Nov) | Yes |
| 1.5 | Gemini API key | Key created, usable models discovered from the account, first real chat + embedding call | Completed | `backend/.env`, `backend/test_gemini.py`, `docs/06_gemini_api.md` | Pass (API-01..04, 16 Nov) · API-05 in Stage 3 | Yes |
| 1.6 | Document ingestion | 9 documents chunked into 56 pieces, embedded and stored in ChromaDB | Completed | `backend/ingest.py`, `docs/07_ingestion.md` | Pass (ING-01..05, 16 Nov) · ING-06 pending | Yes |
| 1.7 | `/chat` endpoint | Retrieve 5 chunks and answer with sources, grounded by a 7-rule system instruction | Completed | `backend/main.py`, `docs/08_chat_endpoint.md` | Pass (CHAT-01, CHAT-02, 16 Nov) · rest in 1.8 | Yes |
| 1.8 | Day 1 tests | 13 automated checks: normal, constrained, unknown, off-topic, incomplete, long and invalid questions | Completed | `tests/test_chat.py` | **Pass 13/13** (16 Nov, 12:12) | Yes |

## Stage 2 – Website and lead capture (Day 2)

| ID | Task | Status |
|---|---|---|
| 2.1 | Landing page | Completed (16 Nov) — `web/index.html`, `web/style.css`, `docs/09_website.md`; WEB-01..03, 05..10 Pass (contrast, focus, skip link, `<main>` fixed in review); WEB-04 at 2.2 |
| 2.2 | Chat widget connected to `/chat` — `web/chat.js`, `web/chat.css`, `docs/10_chat_widget.md`; robot avatar; W-01..23, R-01..12, S-01..05 Pass; end-to-end verified 17 Nov | Completed |
| 2.3 | `/lead` endpoint with consent — `backend/leads.py`, `docs/11_leads.md`; 35 tests Pass on project machine incl. API-01..05 against real server; browser→server run folded into 2.4 (AC-4) | Completed |
| 2.4 | n8n workflow: lead → Google Sheets → email — `n8n/`, `docs/12_n8n_workflow.md`; N8N-01..04, AC-4 (website → sheet + email) and AC-7 (n8n down → lead kept in `pending.jsonl`) Pass, 18 Nov | Completed |
| 2.5 | Day 2 tests and documentation — `docs/13_stage2_test_report.md`, README run guide; 48/48 automated tests Pass (18 Nov); AC-2, 3, 4, 5, 7 Pass; **AC-1 Fail (RET-04)**; NFR-08 at 375 px Pass after fix UI-01 | Completed |

## Stage 3 – GitHub and deployment (Day 3)

| ID | Task | Status |
|---|---|---|
| 3.1 | Git and GitHub repository — <https://github.com/Shazil-Qureshi/realestate-chatbot> (public), `docs/14_github.md`; private commit email; GIT-01..05 and AC-8 Pass (18 Nov, commit `34e6139`) | Completed |
| 3.2 | Dockerfile — builds on Render with the 56-chunk index inside (DOCK-01..06 Pass, 24 Nov); `docs/15_docker.md` | Completed |
| 3.3 | Backend hosting on Render free — live at https://realestate-chatbot-4707.onrender.com; /health, /chat, /lead (demo) and wake-after-sleep (DOCK-07, AC-10) Pass, 24 Nov; `docs/16_render.md` | Completed |
| 3.4 | Website on GitHub Pages — live at <https://shazil-qureshi.github.io/realestate-chatbot/>, widget calls the Render backend; PAGE-01..10 Pass (25 Nov); `docs/17_github_pages.md` | Completed |
| 3.5 | CORS and rate limiting — CORS verified live in 3.4; rate limiting with no new package, RL-01..22 Pass, 74 tests green, **AC-9 Pass on the live service** (10 allowed, 11th refused, 25 Nov); `docs/18_rate_limiting.md` | Completed |
| 3.6 | Live tests and security checklist — SEC-01..19 (17 Pass, 1 finding, 1 not verifiable), live AC re-check; no secret in the tree or in 21 commits of history; `docs/19_stage3_test_report.md` | Completed |

## Stage 4 – Finalisation and portfolio (Day 4)

| ID | Task | Status |
|---|---|---|
| 4.1 | Full system test and fixes — area filtering for RET-04 **plus** system-instruction rule 10 for near matches; **AC-1 Pass**, 14/14 chat tests, 110 in total; `docs/20_area_filtering.md` | Completed |
| 4.2 | README, diagrams, API documentation — README rewritten for a reviewer with two Mermaid diagrams (both rendered and checked); `docs/21_api_reference.md` | Completed |
| 4.3 | Demo video script and screenshots — timed script with measured latencies and a pre-record safety checklist; 8-shot screenshot list; `docs/22_demo.md`. **Recording and capture are the owner's to do.** | In Progress |
| 4.4 | Final report, portfolio and LinkedIn text | Not Started |
| 4.5 | Internship progress report | Not Started |

## Open follow-ups

| ID | Item | Raised in | Status |
|---|---|---|---|
| DEP-05 | `requirements.lock.txt` encoding | 1.4 | **Closed 16 Nov** — regenerated as ASCII and verified |
| API-05 | Confirm `.env` never reaches Git | 1.5 | **Closed 18 Nov** — fresh clone of the public repository has no `.env` or key (`docs/14_github.md`) |
| ING-06 | Confirm re-running ingestion does not duplicate chunks | 1.6 | **Closed 18 Nov** — re-run: 56 already stored, 0 to go (DOCK-03) |
| RET-01 | Vector search ignores hard constraints such as city (Rawalpindi ranked above Islamabad) | 1.6 | **Mitigated** — CHAT-03 passed on 16 Nov with `TOP_K = 5` plus rule 3. One passing question is not proof for all; re-check if new listings are added. |
| RET-03 | Retrieval recall: BRE-S-302 missed for a 3-bedroom question | 1.8 | **Mitigated** — Rawalpindi file split by sale/rent, `TOP_K` 8, completeness rule 8. CHAT-11 passes, but BRE-S-302 sits at rank 8 of 8. Structural fix (metadata filtering) listed for Stage 4. |
| THR-01 | Relevance threshold | 1.8 | Measured: out-of-scope ≈ 0.44, in-scope ≤ 0.29. A 0.40 cut-off is now justifiable as a quota saving. Deferred to Stage 3; it cannot detect in-scope gaps and adds a false-rejection risk. |
| RET-02 | Retrieval can miss a chunk the answer needs (the offices chunk was absent for the Lahore question) | 1.8 | Mitigated by rule 8. A broader fix would be metadata filtering or a larger `TOP_K`. |
| RATE-01 | Free-tier requests-per-minute and per-day for this account | 1.5 | **Closed for design 25 Nov** — Google's docs no longer publish per-model free-tier numbers; they are per account at <https://aistudio.google.com/rate-limit>. The limiter no longer depends on them: it sets its own caps, all env-tunable. Still worth reading the number once to tune `RATE_CHAT_TOTAL_PER_DAY`. |
| SEC-07 | An employer GitHub account name was in `docs/14_github.md`, and that file also wrongly claimed a search for it found nothing | 3.6 | **Partly closed 25 Nov** — removed from the text and the false claim corrected. Still in that file's Git history (20 commits). Rewriting history is the owner's call. |
| SEC-19 | HTTP response security headers never verified (CORS hides them from the page; the workspace cannot reach the host) | 3.6 | Open — not tested, not a pass |
| NFR-01 | One live answer took 10.1 s against a "within 10 seconds" requirement; the other four in the same run took 1.7–2.1 s | 4.3 | Open — watch it. Median is ~2 s, so this is an outlier rather than a trend, but it is on the limit. |
| AC-6 | Live demo not yet opened on a real phone (laptop half is Pass) | 3.4 | Open — one question from a phone browser |
| PAGES-01 | GitHub Pages stopped republishing: "No artifacts named github-pages were found" while the artifact was plainly created | 3.5 | **Closed 25 Nov** — fixed by adding `actions: read` and splitting upload and deploy into two jobs. Both applied together, so which one was the cause is unconfirmed. New `chat.js` is live. |
| CORS-02 | `expose_headers=["Retry-After"]` | 3.5 | **Closed 25 Nov** — verified live: a refused request returned a readable `Retry-After: 60` |
| RET-04 | AC-1 failed: "3-bedroom houses in DHA?" missed BRE-S-102 | 2.5 | **Closed 25 Nov** — needed two fixes: area metadata + area-restricted search, and a change to system-instruction rule 3, which had forbidden near matches outright. AC-1 verified passing (CHAT-12). |
| LEAD-R1 | Leads saved to `pending.jsonl` during an n8n outage are not re-sent automatically | 2.4 | Open — resend script or manual step in Stage 3 |
| N8N-S1 | Webhook has no secret; Google tokens expire every 7 days in Testing mode | 2.4 | Open — secret header and hosting decided in Stage 3 |

**Progress: 25 of 28 tasks completed.** Stages 1–3 complete. Stage 4: 4.1 and 4.2 done; 4.3 script written, recording outstanding. AC-6 (phone) still unrun.

Session history is kept in [`DAILY_PROGRESS.md`](DAILY_PROGRESS.md).
