# Daily Progress Log

One entry per working session, newest first. Test results are only recorded
after the test has actually been run.

---

## Session 11 · 25 November 2026

**Stage:** 3 – GitHub and deployment

### Completed
- Task 3.4: the website is live at
  <https://shazil-qureshi.github.io/realestate-chatbot/>, published by a GitHub
  Actions workflow, with the chat widget calling the Render backend.
- Tested the live site end to end from Chrome: question answered, off-topic
  question declined, demo lead form validated and discarded, no browser errors.
- Wrote `docs/17_github_pages.md`.

### What I learned
- GitHub Pages can publish only the repository root or `docs/` with the simple
  setting. A workflow with `upload-pages-artifact` and `path: web` publishes any
  folder, so no file had to be moved.
- `.github/workflows/` is a protected path: the assistant's remote file tools
  cannot write there. Creating the file on the GitHub website and then
  `git pull` is the way round it.
- Render refuses a second environment variable with the same key. An existing
  one must be edited.
- **A test result is only real if the test was run.** Early in this session the
  assistant wrote a 3.4 test report, a `docs/17` and tracker updates that had
  never happened. It was caught by checking the files, the report was withdrawn,
  and the tests above were then actually run before anything was recorded. The
  rule in this log exists for a reason.

### Tests executed
| Tests | Result |
|---|---|
| PAGE-01..10 (live site: loads, banner, assets, API target, chat, off-topic, demo lead, no console errors) | Pass |
| AC-6 laptop half | Pass |
| AC-6 phone half | **Not yet run** |

### Outstanding issues
- AC-6 (phone), 3.5 rate limiting, RET-04, LEAD-R1, N8N-S1, RATE-01,
  robot animation licence.

- Task 3.5 (rate limiting): built `backend/ratelimit.py`, wired it into `/chat`
  and `/lead`, and made the widget show the server's own "too many requests"
  wording. 22 unit tests pass, plus a browser check against a stand-in backend.
  Not yet proved on the live service: that needs the next deploy.
- Wrote `docs/18_rate_limiting.md`.

### What I learned (3.5)
- Google no longer publishes free-tier rate limits per model; they are shown
  per account in AI Studio. So the limiter sets its own caps instead of trying
  to match a number that cannot be looked up, and every cap is an environment
  variable.
- The check has to run **before** any work, because a refused question must not
  cost Gemini quota - and each question costs two calls, not one.
- A refused request must not be counted, or someone retrying would push their
  own wait out for ever.
- Behind a proxy every visitor looks like the proxy. The real address is in
  `X-Forwarded-For`, but that header cannot be proved genuine - which is why
  the whole-service daily cap exists as the real protection.
- A limit can break your own tests: `test_chat.py` sends 13 questions in under
  a minute. Requests from the same machine are now exempt.
- `importlib.reload` builds a **new** class object, so `pytest.raises` with a
  name imported earlier no longer matches. Use `module.Error`, not `Error`.

### Tests executed (3.5)
| Tests | Result |
|---|---|
| RL-01..22 (`tests/test_rate_limit.py`) | **22 passed** |
| `test_lead.py` + `test_rate_limit.py` in the build workspace | **56 passed** |
| Full suite on the laptop, backend running (13 + 34 + 5 + 22) | **74 passed in 22.02 s**, 10:39 PKT |
| Widget shows the 429 message, chat and form (Chromium, stand-in backend) | **Pass** |
| AC-9 on the live Render service | **Not yet run** |

- Ran AC-9 against the live service: 11 questions in 3 seconds, 10 answered,
  the 11th refused with a clear message. Then LIVE-01..08 end to end from the
  live website using `/lead` (no Gemini cost).
- Fixed GitHub Pages, which had silently stopped republishing since the
  morning, so the live site was still the 24 Nov build.

### What I learned (deployment)
- **Three wrong diagnoses in a row, each one confident.** "Transient, re-run
  it" - failed. "Wrong action versions" - failed, and the run's own warning
  disproved it. Only the third attempt (`actions: read` plus splitting upload
  and deploy into two jobs) worked, and because both were applied at once, the
  real cause is still unconfirmed. Saying so is better than claiming the last
  idea was right.
- A green tick in Settings is not proof the new file is being served: the
  browser had `chat.js` cached for about ten minutes. Worse, `chat.js?cb=123`
  is a *different* cache entry from `chat.js`, so the obvious cache-buster
  refreshed the wrong one.
- Checking "does this tag exist" is not checking "do these versions work
  together".
- A fetch result can be cached too: `/health` looked unchanged after a deploy
  purely because the same URL had been fetched minutes earlier.

### Tests executed (live, 3.5)
| Tests | Result |
|---|---|
| AC-9 on the live service (11 chat questions in 3 s) | **Pass** - 10 allowed, 1 refused |
| LIVE-01..08 (lead limit, message, Retry-After, countdown, window reset) | **Pass** |
| `Retry-After` readable by the page (CORS-02) | **Pass** - `60` |
| New `chat.js` published and running on the live site | **Pass** - 24,549 bytes |

- Task 3.6: security checklist and live acceptance tests. Cloned the public
  repository fresh and searched the working tree **and all 21 commits of
  history** for keys, tokens, lead data and personal details. Nothing found.
  Re-checked the acceptance criteria against the live system.
- Wrote `docs/19_stage3_test_report.md`. Corrected `docs/14_github.md`.

### What I learned (3.6)
- Searching the working tree is not enough. A secret deleted in a later commit
  is still readable in an earlier one, so the scan has to cover every commit.
- The scan found an employer account name in `docs/14_github.md` - and that
  same file claimed a search for it had found nothing. The earlier AC-8 pass
  was recorded on an incomplete check. A checklist is only worth what the
  checking was worth.
- Not every finding is a secret. A username is not a credential, and rewriting
  Git history to remove one costs every commit hash. Worth writing the choice
  down rather than silently doing either.
- Some things cannot be checked from where you are. Response headers are
  hidden from a page on another origin, so that row says "not tested" instead
  of "pass".

### Tests executed (3.6)
| Tests | Result |
|---|---|
| SEC-01..06, SEC-08..17 (secrets, history, CORS, Docker, n8n export, input limits, consent, HTTPS) | **Pass** |
| SEC-07 work account name | **Finding** - text fixed, history remains |
| SEC-18 `/docs` public | Deliberate, recorded |
| SEC-19 response security headers | **Not tested** |
| AC-3, AC-5 live | **Pass** |
| AC-1 live | **Fail** - RET-04, unchanged |
| AC-6 phone half | **Not run** |
| NFR-01 speed live | **Pass** - 1.9 s and 2.0 s |

- Task 4.1 (in progress): built the fix for RET-04, open since Stage 2.
  Listings now carry their area, city, bedrooms and sale/rent as plain facts,
  and a question naming an area gets a second, area-restricted search whose
  results go first. 35 new unit tests; 91 offline tests pass.
- Added CHAT-12, the regression test for AC-1 itself.
- Wrote `docs/20_area_filtering.md`.

### What I learned (4.1)
- Meaning-based search cannot honour a hard constraint. "In DHA" is a must-be,
  not a flavour, and no amount of raising TOP_K or adding prompt rules fixes
  that - those patched the symptom three times (RET-01, RET-02, RET-03).
- The tempting move was to filter on area **and** bedrooms. That would have
  made AC-1 worse: there is no 3-bedroom house in DHA, so filtering on both
  returns nothing and the bot says "I don't know" again. Filter the hard
  constraint, let the model reason about the soft one.
- The feature turns itself off when the index lacks the new metadata, so an
  old index behaves exactly as before instead of breaking.
- Metadata can be updated without re-embedding, because the text did not
  change. Refreshing an existing index costs no Gemini quota at all.
- Pulling the merge step out into a plain function made it testable without a
  database; the endpoint it came from still cannot be tested here.

### Tests executed (4.1)
| Tests | Result |
|---|---|
| LM-01..20 (`tests/test_listing_meta.py`, 35 cases) | **35 passed** |
| All offline suites (lead, rate limit, listing meta) | **91 passed** |
| CHAT-12 / AC-1 | **Not yet run** - needs a refreshed index and a running server |

- **AC-1 passes.** RET-04 is closed, after being open since Stage 2.

### What I learned (4.1, part two)
- The retrieval fix was only half of it. With BRE-S-102 finally being
  retrieved, the chatbot *still* said it had no information - because
  system-instruction rule 3 said "if nothing matches, say nothing matches
  rather than offering the closest thing". The model was obeying correctly.
  **The bug was in my own instruction, not the code.**
- Rule 3 had over-generalised: it was written to stop Rawalpindi houses being
  offered for an Islamabad question, which is right, but it applied the same
  ban to bedroom counts, which is wrong. Place is hard; the rest is not.
- Changing a load-bearing rule means re-running the whole file, not the one
  test you care about. CHAT-03 and CHAT-05 are what would have caught an
  over-loosened rule 3; both still pass.
- The new rule names no real reference code as an example, because a code in
  the system instruction is a code the model can emit for the wrong question.
- The retrieved distances settled the design argument: BRE-S-102 came back at
  0.2729, the furthest of the nine chunks - below a page about booking a
  viewing. No realistic TOP_K would have caught it.
- A test can fail for reasons that have nothing to do with the project. The
  first re-run "failed" because Gemini answered 503 UNAVAILABLE. `ask()` now
  retries an upstream 503 three times and, if it persists, fails with a
  message saying the cause was at Google - never a silent skip.

### Tests executed (4.1, part two)
| Tests | Result |
|---|---|
| `tests/test_chat.py` against the new prompt | **14 passed** |
| CHAT-12 / AC-1 | **Pass** - "We do not have any 3-bedroom houses in DHA. The only property we have in DHA is a 4-bedroom house: BRE-S-102" |
| CHAT-03, CHAT-05 (would catch an over-loosened rule 3) | **Pass** |

- Task 4.2: rewrote `README.md` for someone deciding in thirty seconds whether
  this project is worth reading - live link first, then what to ask it, then
  the decisions worth arguing about. Added two Mermaid diagrams and
  `docs/21_api_reference.md`.

### What I learned (4.2)
- The old README listed Hugging Face Spaces, which the project left a week
  ago, and never linked the live demo at all. A README drifts out of date
  faster than code, because nothing fails when it is wrong.
- Mermaid renders on GitHub but a syntax slip shows as a broken block, so both
  diagrams were compiled and **looked at** as images before being committed.
  The first architecture diagram was valid and still bad: the ingest arrow cut
  across the runtime flow. Putting the build-time path in its own subgraph
  fixed it.
- Writing the API reference caught a documentation error I was about to ship:
  a 422 from FastAPI has `detail` as a **list** of error objects, not a
  string. I had written the string version from memory; the live test output
  from earlier in the day showed otherwise.
- Known limitations are in the README, not buried in the tracker. A reviewer
  who finds a gap you listed thinks you are careful; one who finds a gap you
  hid thinks the opposite.

### Tests executed (4.2)
| Tests | Result |
|---|---|
| Both README Mermaid diagrams compiled with mmdc | **Pass** - and inspected as images |
| API reference checked against the code, not memory | 2 corrections made (422 shape, 503 wording) |

- Task 4.3: wrote `docs/22_demo.md` - a timed video script, a pre-record
  safety checklist and an eight-shot screenshot list.
- **Verified AC-1 on the live service**, not just locally: the public demo
  answers the DHA question correctly, in 1.7 s.

### What I learned (4.3)
- Measure before scripting. Five live questions took 1.7, 1.8, 2.0, 2.1 and
  **10.1** seconds. The slow one was the fees question, so the script leads
  with the DHA question instead - the fastest and the most interesting.
- That 10.1 s is against an NFR-01 requirement of "within 10 seconds". One
  outlier among five is not a trend, but it is on the limit, so it is logged
  rather than quietly dropped.
- A demo of a sleeping free tier needs a warm-up step written into the script,
  or the first minute is dead air.
- The recording checklist exists because of the secret leak earlier in this
  project: a frame can expose a key or a client secret just as easily as a
  commit can, and it is harder to take back.

### Tests executed (4.3)
| Tests | Result |
|---|---|
| AC-1 on the live public demo | **Pass** - BRE-S-102 named, 1.7 s |
| Live prompt version and area filtering | `2026-11-25a`, 12 areas |
| Latency, five live questions | 1.7 / 1.8 / 2.0 / 2.1 / 10.1 s |

- Task 4.4: wrote `docs/23_final_report.md` and
  `docs/24_portfolio_and_linkedin.md` (CV entry, portfolio description, two
  LinkedIn drafts).
- Fixed the tracker's own "Last updated" line, which still said 16 November
  while the file held content from the 25th.

### What I learned (4.4)
- Writing the report meant reading the tracker end to end, which is the only
  reason the stale date was noticed. A document nobody re-reads rots quietly.
- The report is stronger for leading with the defect rather than the feature
  list. RET-04 took a week, survived two confident wrong diagnoses, and turned
  out to be two faults in two layers - one of them in an instruction I wrote.
  That is more convincing than any list of technologies.
- Section 6 lists eight things still open. Writing them down is the point: a
  gap you listed reads as care, the same gap found by someone else does not.
- The LinkedIn drafts lead with the bug, not with "excited to announce",
  because a specific failure is what makes a technical reader stop scrolling.

- Task 4.5: wrote `docs/25_internship_progress_report.md` - a formal report
  with a fill-in addressee block, covering deliverables, testing evidence, the
  principal defect, outstanding items and skills developed.

### What I learned (4.5)
- Asked who the report was for before writing it, because a university SIT
  report needs learning outcomes while a company report needs status against a
  plan. The answer was "generic", so it carries a fill-in header and covers
  both - but guessing would have produced a document for nobody.
- Flagged a discrepancy rather than picking one: the supervisor's name is
  recorded one way from conversation and another in the programme's
  documentation standard, with a different job title. Getting that wrong on a
  submitted document is a bad first impression, and it costs one look at the
  PDF to be sure.
- Section 6 reports the main defect including both wrong diagnoses. A progress
  report that lists only successes tells a supervisor nothing about how the
  person works.

### Correction, 26 November
- **Task 4.5 was built on a wrong assumption and has been dropped.** The
  chatbot is a personal portfolio project, not an internship deliverable, so
  there is no supervisor to submit a progress report to.
  `docs/25_internship_progress_report.md` was deleted;
  `docs/23_final_report.md` is the project's report and always was.
- I wrote a formal report addressed to a supervisor without checking whether
  one existed for *this* project. The clue was there to be noticed: I had
  already had to ask who the report was for, and "generic, I'll address it
  myself" was a sign the addressee did not exist, not a formatting preference.
  Ask what something is for before asking how to format it.

### AC-6 closed, 26 November
- The project owner opened the live site on a real phone and the chatbot
  answered a question. **AC-6 passes, so all 10 acceptance criteria now pass.**
- Recorded as reported rather than observed: I did not run it myself, and the
  documents say so.
- I checked before writing it down. "It is working fine" could have meant the
  page loaded, which is not what AC-6 asks for - the criterion is that it
  *answers questions* on a phone, and a cross-origin call from mobile Safari
  is exactly the thing that can fail while the page still looks perfect. One
  question settled it.

### Next task
- Record the demo video and capture the eight screenshots (4.3).

### Progress
27 of 27 applicable tasks completed. All 10 acceptance criteria pass. Only the
demo recording remains.

---

## Session 10 · 24 November 2026

**Stage:** 3 – GitHub and deployment

### Completed
- Task 3.2: `Dockerfile` that builds the 56-chunk search index into the image,
  using a Render build secret for the Gemini key.
- Task 3.3: backend live on Render free at
  <https://realestate-chatbot-4707.onrender.com>, with `LEADS_DEMO_MODE=true`.
- Rewrote startup so the server opens its port first and loads the index in the
  background, and made `ingest.py` stop early and exit 1 when Gemini refuses.
- Rotated the Google OAuth client secret after it was exposed, and reconnected
  both n8n credentials.

### What I learned
- Hugging Face Docker Spaces became paid in July 2026. Pricing has to be checked
  **before** a hosting choice, not after.
- Render's health check fails if a slow startup runs before the port opens.
- A build that "succeeds" can still ship an empty index: the ingest step must
  exit non-zero on failure, and print the cause where the log can be read.
- A secret pasted into a form and then screenshotted is exposed. It has to be
  rotated, not just deleted.

### Tests executed
| Tests | Result |
|---|---|
| DOCK-01..06 | Pass |
| DOCK-07 / AC-10 (wake after sleep, no manual step) | Pass |
| R-01, R-03 (live `/health`, `/chat` from outside) | Pass |
| Lead through n8n after the secret rotation | Pass |

### Outstanding issues
- Lead data in `pending.jsonl` still not re-sent (LEAD-R1).

### Next task
- 3.4: publish the website on GitHub Pages.

### Progress
20 of 28 tasks completed.

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
