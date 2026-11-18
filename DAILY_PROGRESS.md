# Daily Progress Log

One entry per working session, newest first. Test results are only recorded
after the test has actually been run.

---

## Session 9 · 18 November 2026

**Stage:** 3 – GitHub and deployment

### Completed
- Task 3.1: the project is on GitHub at
  <https://github.com/Shazil-Qureshi/realestate-chatbot> (public), first commit
  `34e6139`, 54 files.

### What I learned
- Every commit carries an email address, and on a public repository anyone can
  read it. GitHub's private noreply address avoids that.
- Check what will be committed **before** committing. Removing a secret
  afterwards doesn't remove it from the history.
- Windows remembers Git logins. A saved work account can be used for a
  personal repository without asking. Putting the username in the remote
  address picks the right account.
- A "file written" message isn't proof. Four files on the laptop turned out
  to be out of date, so I checked by reading the size back.

### Tests executed
| Tests | Result |
|---|---|
| GIT-01..05 | Pass |
| AC-8 / API-05 (fresh public clone: no key, no lead data, no private email) | Pass |
| CHAT-01 re-run after `test_chat.py` was updated | Pass |

### Outstanding issues
- RET-04 (AC-1), LEAD-R1, N8N-S1, ING-06, RATE-01, robot animation licence.

### Next task
- 3.2: Dockerfile for the backend.

### Progress
18 of 28 tasks completed.

---

## Session 8 · 17–18 November 2026

**Stage:** 2 – Website and lead capture

### Completed
- Task 2.3 `/lead` endpoint: consent required, honeypot, fallback file.
  35 tests pass on the project machine.
- Task 2.4 n8n workflow: n8n 2.47.7 on the laptop (Node 24; Node 26 isn't
  supported). Webhook → Google Sheets row → reply to backend → Gmail alert.
  Google OAuth set up in a new Cloud project in Testing mode.
- Tested the whole path: a lead from the website reaches the sheet and the inbox
  (AC-4), and a lead sent while n8n is down is kept in `pending.jsonl` while the
  chat keeps answering (AC-7).

### What I learned
- An automation tool should run on an account you control. A workplace n8n
  account belonging to someone else was ruled out.
- Google shows a client secret only once, and allows two per client.
- Sheets can quietly turn `0300…` into a number and drop the 0. "RAW" format
  keeps it as typed.
- A fallback is only half a design. Saving a lead during an outage is done.
  Re-sending it afterwards isn't yet.
- With four terminal tabs open, check which one you're in before pressing
  Ctrl+C.

### Tests executed
| Tests | Result |
|---|---|
| LEAD-01..23, API-01..05 | Pass |
| N8N-01..04 | Pass |
| AC-4 (website → sheet + email) | Pass, 17 Nov |
| AC-7 (n8n down → lead kept) | Pass, 18 Nov, lead `7c15a05c05a2` |

### Outstanding issues
- Pending leads are not re-sent automatically (LEAD-R1).
- Webhook needs a secret before it goes public. Google tokens expire every
  7 days in Testing mode (N8N-S1).
- Owner tidy-ups:
  - delete the old Google client secret
  - delete `data/listings/03_rawalpindi.md`
  - ING-06
  - RATE-01
  - Lottie licence

- Task 2.5 Day 2 tests: ran the acceptance criteria in the real widget,
  checked the phone layout at 375 px, and wrote `docs/13_stage2_test_report.md`
  and a run guide in the README.

### Task 2.5 results (18 Nov)
| Tests | Result |
|---|---|
| Full suite `pytest tests -v` | **48 passed** in 71 s |
| AC-2, AC-3, AC-5 in the real widget | Pass |
| NFR-07 fictional notice, NFR-08 at 375 px | Pass |
| AC-1 "3-bedroom houses in DHA?" | **Fail**: logged as RET-04 |

- Fixed UI-01: phone text fields were 15.2 px, so iPhone zoomed in on tap.
  They're now 16 px. The first fix didn't apply because a later CSS rule won.
  The re-test caught it.
- Lesson: a full test suite passing doesn't mean every requirement passes.
  None of the 48 tests asked an area + bedrooms question.

### Next task
- Stage 3, Task 3.1: Git and GitHub repository. Check that `.env` and lead
  data can't be committed (API-05, AC-8).

### Progress
17 of 28 tasks completed.

---

## Session 7 · 16–17 November 2026

**Stage:** 2 – Website and lead capture

### Completed
- Task 2.1 Landing page: reviewed the existing draft, checked all 27 card figures
  against `data/`, and fixed four accessibility failures (price contrast 2.42 → 4.61,
  keyboard focus, skip link, `<main>`).
- Task 2.2 Chat widget: `web/chat.js` and `web/chat.css`, connected to `/chat`,
  verified end to end with the real backend.
- Robot avatar: compared the two supplied Lottie files and chose AI Robot (4.8 KB,
  30 fps, no drawn-in text, loops seamlessly). Rendered with lottie-web 5.12.2,
  downloaded into `web/vendor/`.
- Sources list now shows only the extracts the answer actually used.

### What I learned
- Text from a language model is untrusted, so the widget never inserts it as HTML.
- `localhost` and `127.0.0.1` are different origins to a browser, even though
  they're the same machine.
- A label can be wrong when the data is right. "Sources (8)" was accurate data
  under a misleading name.
- A test that can't see what it's checking passes for the wrong reason.
  `inner_text()` reads only visible text, so a collapsed list looked empty.
- A test stand-in proves the wiring. Only the real thing proves the result.

### Tests executed
| Tests | Result |
|---|---|
| WEB-01..10 | Pass |
| W-01..23 | Pass |
| R-01..12 | Pass |
| S-01..05 | Pass |

### Correction
- I wrote that `web/index.html` was "not written by me". It was written earlier
  in this same conversation, in a turn that had dropped out of view. Corrected in
  `docs/09_website.md`.

### Outstanding issues
- Confirm the robot animation's licence on LottieFiles before Stage 3.
- ING-06, RATE-01, and deleting `data/listings/03_rawalpindi.md` are still open.
- No conversation memory: follow-up questions like "the second one" won't work.

### Next task
- 2.3: `/lead` endpoint. Collect a visitor's details, only with their consent.

### Progress
14 of 28 tasks completed.

---

## Session 6 · 16 November 2026 (midday)

**Stage:** 1 – Backend and AI knowledge base — **completed**

### Completed
- Task 1.6 Ingestion: 56 chunks embedded and stored in ChromaDB.
- Task 1.7 `/chat` endpoint: retrieval plus a 9-rule system instruction.
- Task 1.8 Tests: 13 automated checks in `tests/test_chat.py`, all passing.
- Built `backend/search_debug.py` to show where every chunk ranks for a question.

### What I learned
- Vector search matches meaning and can't apply hard filters. "Apartment for
  rent in Islamabad" ranked a Rawalpindi property first.
- An answer can be accurate and still incomplete. That's a quiet failure,
  because nobody sees the property that was never mentioned.
- A test that checks for the presence of something can't catch an absence.
- A green test can pass on a bad answer. CHAT-10 passed on "I do not have that
  information" until the answers were read, not just counted.
- Document structure shapes retrieval. One file without "For Sale" in its
  title quietly lowered the ranking of its listings.
- Two defects can be stacked. Fixing the data got BRE-S-302 retrieved. The
  prompt still let the model drop it, because it asked for brevity and never
  for completeness.
- Restart the server after changing the prompt. One failed run was a stale
  server, not a bad fix.

### Files created or updated
- `backend/ingest.py`, `backend/main.py`, `backend/search_debug.py`
- `tests/test_chat.py`
- `data/listings/03_rawalpindi_for_sale.md`, `04_rawalpindi_for_rent.md`
  (split from `03_rawalpindi.md`)
- `docs/07_ingestion.md`, `docs/08_chat_endpoint.md`, `docs/05_business_documents.md`

### Problems fixed
- Missing `MSVCP140.dll` (C++ runtime) → installed the Visual C++ Redistributable.
- 422 in `/docs` → the request body must be JSON, not plain text.
- CHAT-10 hedge → added a rule about operating cities and tightened the test.
- CHAT-11 omission → split the Rawalpindi file, raised `TOP_K` to 8, and added
  a completeness rule.

### Tests executed
| Test | Result |
|---|---|
| ING-01..05 | Pass |
| CHAT-01..11 (13 checks) | Pass — 13/13 at 12:12 |

### Outstanding issues
- ING-06: re-run ingestion to confirm no duplicates.
- RET-03: BRE-S-302 retrieved at rank 8 of 8. Mitigated, not solved.
- Delete the now-empty `data/listings/03_rawalpindi.md`.
- RATE-01: free-tier limits still to be read from AI Studio.
- n8n hosting choice due at the start of Stage 2.

### Next task
- Stage 2, Task 2.1: landing page for Bella Real Estate.

### Progress
12 of 28 tasks completed. Stage 1 complete.

## Session 5 · 16 November 2026 (late morning)

**Stage:** 1 – Backend and AI knowledge base

### Completed
- Task 1.5 Gemini API key. Key created, stored in `backend/.env`, and verified
  with a real chat call and a real embedding call.
- Chose `gemini-3.5-flash-lite` for chat and `gemini-embedding-2` for
  embeddings, picked from the list the account itself reported.
- Wrote `backend/ingest.py` and verified its chunking with a dry run.

### What I learned
- A check that only ever passes proves nothing. The API check failed correctly
  when the key was missing, then passed when it was there. Both runs mattered.
- Google does not publish free-tier rate limits per model. They depend on the
  account and have to be read in AI Studio. Any blog quoting exact numbers is
  quoting somebody else's account.
- Sending several texts to `gemini-embedding-2` in one request returns **one
  blended embedding**, not one per text. That would not have raised an error.
  It would have stored meaningless numbers and quietly ruined every search.
- Good chunking is mostly a reward for having written the source documents
  well. The `##` headings from Task 1.3 are exactly why 17 properties became
  17 clean chunks.

### Files created or updated
- `backend/ingest.py` (new)
- `docs/06_gemini_api.md` (results, model rationale, security incident)
- `docs/07_ingestion.md` (new)
- `backend/.env.example`, `README.md`, `PROJECT_TRACKER.md`

### Tests executed
| Test ID | Objective | Result |
|---|---|---|
| API-01 | `.env` found and key read | Pass |
| API-02 | Key accepted by Google | Pass |
| API-03 | Real question answered | Pass — `gemini-3.5-flash-lite` replied `working` |
| API-04 | Real embedding returned | Pass — 3,072 numbers |
| ING-01 | Chunking produces sensible pieces | Pass — 56 chunks, largest 526 characters |
| ING-02 | Chunk IDs unique | Pass |
| ING-03 | Every document read | Pass — all 9 files produced chunks |

### Security incident
- The first API key was captured in a screenshot of `backend/.env` and shared
  outside the machine. Detected within minutes, before the key had been used.
  Key revoked in AI Studio and replaced. No billing was attached, so no damage.
- Process change: screenshots are taken of the terminal, never of `.env`.
  `test_gemini.py` prints only the key's character count for this reason.

### Outstanding issues
- RATE-01: free-tier limits for this account still unread. Needed before the
  live ingestion run, which fires 57 requests.
- API-05: confirming `.env` stays out of Git happens in Stage 3.
- n8n hosting choice still deferred to Stage 2.

### Next task
- Finish 1.6: run `python backend\ingest.py` for real and record
  ING-04, ING-05 and ING-06.

### Progress
9 of 28 tasks completed.

## Session 4 · 16 November 2026

**Stage:** 1 – Backend and AI knowledge base

### Completed
- Task 1.4 Install dependencies. 7 requested packages installed, 98 in total
  once their own dependencies were pulled in.
- Froze the exact versions into `backend/requirements.lock.txt`.
- Confirmed the three critical packages import cleanly.

### What I learned
- One `pip install` line can produce ~100 packages. The extra 91 are
  *transitive dependencies*: packages my packages need.
- A lock file is generated from a real install, never written by hand. It is
  the difference between "these versions should work" and "these versions did
  work, on this machine, on this date".
- `>` in Windows PowerShell 5.1 writes UTF-16, not plain text. A file can look
  perfect in VS Code and still be unreadable to the tool that has to parse it.
- How to verify a claim when the proof has scrolled off screen: the
  `Successfully installed` line was gone, so the install was confirmed from two
  other angles instead (the import test and the lock file contents).

### Files created or updated
- `backend/requirements.lock.txt` (new)
- `docs/04_environment_setup.md` (Task 1.4 results, versions, problems)
- `PROJECT_TRACKER.md`

### Tests executed
| Test ID | Objective | Result |
|---|---|---|
| DEP-01 | Install completes | Pass |
| DEP-02 | Packages import | Pass |
| DEP-03 | Lock file created | Pass |
| DEP-04 | Installed into `.venv`, not globally | Pass |
| DEP-05 | Lock file readable as plain text | Fail, then **Pass** after regenerating with `-Encoding ascii` |

### Problems fixed
- The Task 1.4 section of `docs/04_environment_setup.md` contained four broken
  commands: `backend\requirements.txt` had been written with a real carriage
  return instead of a backslash, so it read `backend` then jumped to a new line.
  Caused by an escaping mistake when the section was generated. All four
  corrected and the file checked for any remaining carriage returns.

### Outstanding issues
- Gemini free-tier daily request limits still unconfirmed — will be visible in
  the AI Studio account during Task 1.5.
- n8n hosting choice (Cloud trial or self-hosted) still deferred to Stage 2.
- The locked versions were resolved on Windows. Hugging Face Spaces runs Linux,
  so Stage 3 should budget for a first build that fails.

### Risk closed
- "Python 3.14 may have no wheels for `numpy` or `onnxruntime`" — did not
  happen. Both installed cleanly. The Python version choice from Task 1.1 holds.

### Next task
- 1.5: create the Gemini API key, store it in `backend/.env`, and make a first
  real API call.

### Progress
8 of 28 tasks completed.

## Session 3 · 14 November 2026

**Stage:** 1 – Backend and AI knowledge base

### Completed
- Moved the project back inside the folder Claude can write to, so files are
  saved directly again.
- Task 1.3 Business documents: 9 Markdown files describing the fictional
  Bella Real Estate, with 17 properties.

### What I learned
- The knowledge base sets a hard ceiling on answer quality. Vague documents
  produce vague answers no matter how good the AI is.
- Each section must be self-contained, because a retrieved chunk is read
  without the text around it. "It costs 2 crore" is useless on its own.
- Leaving facts out on purpose is part of the design: without gaps there is no
  way to test that the chatbot admits when it does not know something.
- A virtual environment stores absolute paths, so moving the project folder
  can break it.

### Files created or updated
- `data/company_info/` (3 files), `data/listings/` (3 files),
  `data/faqs/` (3 files)
- `docs/05_business_documents.md` (new)
- `PROJECT_TRACKER.md`, `DAILY_PROGRESS.md`

### Tests executed
| Check | Method | Result |
|---|---|---|
| 17 unique property reference codes | Counted across listing files | Pass |
| Every listing states area, size, price and status | Read each block | Pass |
| No vague pricing language | Searched for "affordable", "cheap" | Pass |
| Deliberate gaps absent from all 9 files | Searched for tax, loan, mortgage, pet, school | Pass, no matches |
| Fictional-company notice present | Read the about file | Pass |

### Outstanding issues
- The `.venv` was created at the old path and the project has since moved. It
  must be deleted and recreated before installing packages in Task 1.4.
- Free-tier daily request limits still unconfirmed; visible in Task 1.5.
- n8n hosting choice still open, due in Stage 2.

### Next task
Task 1.4: install Python packages and pin them in `backend/requirements.txt`.

### Progress
7 of 28 tasks completed.

---

## Session 2 · 13 November 2026 (afternoon)

**Stage:** 1 – Backend and AI knowledge base

### Completed
- Task 1.1 Environment setup: Python 3.14.10 installed, `.venv` created and
  activated, pip 26.3 inside the environment, all 8 checks passing.
- Task 1.2 Requirements: 16 functional requirements, 10 non-functional
  requirements, an out-of-scope list and 10 acceptance criteria.

### What I learned
- Windows ships a fake `python` command (an App execution alias) that only
  opens the Microsoft Store. The honest test for a real install is `py --version`.
- The newest Python is not the safest choice. Packages need time to publish
  pre-built wheels, so the second-newest series is the sensible default.
- A Python series in security-only mode stops shipping Windows installers
  (3.13.18 is source-only).
- pip's output shows where a package landed. If the path is not inside `.venv`,
  the virtual environment was not active.
- Requirements should be written so each one is testable, with an ID that a
  test case can point back to.

### Files created or updated
- `backend/check_env.py` (run successfully)
- `docs/04_environment_setup.md` (real test results recorded)
- `docs/02_requirements.md` (new)
- `PROJECT_TRACKER.md`, `DAILY_PROGRESS.md`

### Tests executed
| Test ID | Input | Actual result | Status |
|---|---|---|---|
| ENV-01 | `python --version` | First `Python was not found`; after install `Python 3.14.10` | Pass after fix |
| ENV-02 | `check_env.py` | `C:\Program Files\Git\cmd\git.EXE` | Pass |
| ENV-03 | `.venv\Scripts\Activate.ps1` | Prompt showed `(.venv)` | Pass |
| ENV-04 | `python backend\check_env.py` | 8 PASS lines, "All checks passed." | Pass |
| ENV-05 | Script run before activation | `[FAIL] No virtual environment is active` | Pass |

### Outstanding issues
- The project folder sits outside the folder Claude can write to, so files are
  being delivered as text to paste in.
- Free-tier daily request limits still unconfirmed; will be visible in Google
  AI Studio during Task 1.5.
- n8n hosting choice (Cloud trial or self-hosted) still open, due in Stage 2.

### Next task
Task 1.3: write the fictional Bella Real Estate documents into `data/`.

### Progress
6 of 28 tasks completed.

---

## Session 1 · 13 November 2026

**Stage:** 0 – Planning, and start of Stage 1

### Completed
- Checked current Gemini model names and free-tier availability.
- Created the project folder structure and base files.
- Wrote the project overview (architecture, concepts, risks).
- Created the project tracker and this progress log.
- Prepared Task 1.1: environment check script and setup guide.

### What I learned
- What RAG is and why a chatbot needs it.
- How the website, backend, vector database, Gemini and n8n talk to each other.
- What a virtual environment is and why each project gets its own.

### Files created or updated
- `README.md`, `.gitignore`, `LICENSE`, `backend/.env.example`
- `PROJECT_TRACKER.md`, `DAILY_PROGRESS.md`
- `docs/01_project_overview.md`, `docs/04_environment_setup.md`
- `backend/check_env.py`

### Tests executed
| Test ID | Result |
|---|---|
| ENV-01 to ENV-05 | Not yet run on my computer |

### Outstanding issues
- Free-tier daily request limits not yet confirmed.
- n8n hosting choice (Cloud trial or self-hosted) to be made in Stage 2.

### Next task
- Finish 1.1: run `check_env.py` and record the results.
- Then 1.2: requirements document.

### Progress
4 of 28 tasks completed.
