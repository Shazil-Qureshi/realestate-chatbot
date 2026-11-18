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
| 3.2 | Dockerfile — `Dockerfile`, `backend/start.sh`, `.dockerignore`, `.gitattributes`, `docs/15_docker.md`; index built into the image (NFR-06); DOCK-01..03 Pass; first real build in 3.3 (DOCK-04..08) | In Progress |
| 3.3 | Backend on Hugging Face Spaces — decided: live leads in demo mode (checked, then discarded); `LEADS_DEMO_MODE`, LEAD-24..27 Pass here; Space setup in progress | In Progress |
| 3.4 | Website on GitHub Pages (Actions workflow) | Not Started |
| 3.5 | CORS and rate limiting | Not Started |
| 3.6 | Live tests and security checklist | Not Started |

## Stage 4 – Finalisation and portfolio (Day 4)

| ID | Task | Status |
|---|---|---|
| 4.1 | Full system test and fixes | Not Started |
| 4.2 | README, diagrams, API documentation | Not Started |
| 4.3 | Demo video script and screenshots | Not Started |
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
| RATE-01 | Free-tier requests-per-minute and per-day for this account | 1.5 | Open — Google does not publish them; must be read from AI Studio before the live ingestion run |
| RET-04 | AC-1 fails: "3-bedroom houses in DHA?" misses BRE-S-102 (the only DHA listing); bedroom words outrank the area | 2.5 | Open — metadata filtering (area, bedrooms, sale/rent) in Stage 4; add a regression test |
| LEAD-R1 | Leads saved to `pending.jsonl` during an n8n outage are not re-sent automatically | 2.4 | Open — resend script or manual step in Stage 3 |
| N8N-S1 | Webhook has no secret; Google tokens expire every 7 days in Testing mode | 2.4 | Open — secret header and hosting decided in Stage 3 |

**Progress: 18 of 28 tasks completed.** Stages 1 and 2 complete (AC-1 open as RET-04). Stage 3: 3.1 done, 3.2 next.

Session history is kept in [`DAILY_PROGRESS.md`](DAILY_PROGRESS.md).
