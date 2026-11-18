# 13 · Stage 2 Test Report

| | |
|---|---|
| **Task** | 2.5 Day 2 tests and documentation |
| **Date** | 18 November 2026 |
| **Scope** | Everything built in Stage 2: website, chat widget, `/lead`, n8n workflow. Stage 1 chat tests re-run as a regression check. |
| **Rule** | A result is written down only after the test was actually run. Anything not run says so. |

## Summary

| | Count |
|---|---|
| Acceptance criteria in Stage 2 scope (AC-1 to AC-5, AC-7) | 6 |
| Passed | 5 |
| **Failed** | **1, AC-1 (see RET-04)** |
| Defects found in 2.5 | 2: one fixed (UI-01), one open (RET-04) |
| Automated regression suite | **48 / 48 pass** |

Stage 2 works end to end: website → chat → lead → Google Sheet → email, and
leads survive an n8n outage. One acceptance criterion fails because of a
retrieval weakness already known from Stage 1. It is open and not hidden.

## Where each test ran

| Where | What | Why it counts |
|---|---|---|
| Project laptop, real backend, real Gemini, real n8n | CHAT, API, AC-1..5, AC-7, N8N, W-20..23 | The real system |
| Build workspace, headless Chromium, stand-in backend | W-01..19, L-01..17, R, S, 375 px check | Proves the page's own behaviour. Stand-ins run the real `leads.py` validation where it matters. |

## Acceptance criteria

| ID | Criterion | How it was run (18 Nov unless stated) | Result |
|---|---|---|---|
| AC-1 | "Do you have 3-bedroom houses in DHA?" → answer from the listings, source named | Typed into the real widget | **Fail**, see RET-04 |
| AC-2 | "Do you sell cars?" → polite decline | Real widget | **Pass**: "I can only help with questions about Bella Real Estate, property, or renting and buying homes." |
| AC-3 | "What is your Karachi office address?" → no invented address | Real widget | **Pass**: "Bella Real Estate operates only in Islamabad and Rawalpindi. We do not operate in Karachi." Grounded in the documents, no address invented. |
| AC-4 | Consent → row in Google Sheets + email | Real widget → real n8n, 17 Nov | **Pass** ([12](12_n8n_workflow.md)) |
| AC-5 | Empty name / phone "abc" rejected clearly | Real widget, real backend | **Pass**: "Enter your name." and "Enter a phone number with 10 to 15 digits, for example 0300 1234567."; form stays open, nothing sent. Server side: API-02, API-03. |
| AC-7 | n8n unreachable → chat still works, lead kept | Real system, n8n stopped | **Pass**: lead `7c15a05c05a2` → `pending.jsonl` ([12](12_n8n_workflow.md)) |

AC-6 and AC-8 to AC-10 need the public deployment. They belong to Stage 3.

## AC-1 failure: what happened

The data has **no** 3-bedroom house in DHA. The only DHA listing is
**BRE-S-102**, a 4-bedroom, 10 marla house in DHA Phase 2. The right answer is
"No 3-bedroom house in DHA. The nearest is BRE-S-102 (4 bedrooms)."

The chatbot said: *"I do not have that information in my extracts. Would you
like me to pass your question to the team?"* That isn't false, and it invents
nothing. But it can't mention BRE-S-102, because BRE-S-102 never reached it.

Checked through `/chat` directly:

| Question | BRE-S-102 retrieved? |
|---|---|
| "Do you have houses in DHA?" | Yes, rank 7 of 8. The answer names it correctly. |
| "Do you have 3-bedroom houses in DHA?" | **No.** The 8 results are 3-bedroom listings elsewhere (BRE-R-305, BRE-R-202, BRE-S-103 …). |

**Cause.** Vector search matches on overall meaning. Adding "3-bedroom" pulls
in every 3-bedroom listing, and they push the one DHA house out of the top 8.
This is the same weakness as RET-01 and RET-03 from Stage 1.

**Fix (not done in 2.5).** Filter by area before ranking, using metadata
(city, area, bedrooms, sale/rent) stored with each listing chunk. That is
already planned for Stage 4. Raising `TOP_K` again would hide the problem for
this one question without fixing it.

Logged as **RET-04**. AC-1 stays **Fail** until it passes on a re-run.

## Non-functional requirements checked in Stage 2

| ID | Requirement | Evidence | Result |
|---|---|---|---|
| NFR-01 | Answer within 10 s | AC-1 question timed in the widget: 2.6 s. Every CHAT test completes within its 60 s timeout. No systematic timing run yet. | Indicative pass |
| NFR-05 | Chat works when n8n is down | AC-7 | **Pass** |
| NFR-07 | Fictional company stated | Banner "Demo website — Bella Real Estate is a fictional company…" and chat footer "This is a demo with a fictional company." Read from the live page. | **Pass** |
| NFR-08 | Widget usable at 375 px | See below | **Pass** after fix UI-01 |
| NFR-09 | Lead data not committed or shown to others | `backend/leads/` is in `.gitignore` (LEAD test). Logs show only the lead ID. The thank-you message repeats only the visitor's first name. Full repository check is in Stage 3. | Pass so far |

### NFR-08 at 375 × 667 (iPhone SE size)

| Check | Result |
|---|---|
| Sideways scroll: page, open panel, after an answer, lead form, thank-you | 0 px every time |
| Panel | Fills the screen (0–375 × 0–667) |
| Message bubbles and lead form | Inside the screen (right edge 359 px) |
| Text size in input fields | **15.2 px before the fix, 16 px after** |

**UI-01 (fixed).** iPhone Safari zooms the page into any form field with text
under 16 px when it's tapped, and the visitor has to pinch back out. The chat
box and lead form were 15.2 px. `web/chat.css` now sets them to 16 px on
screens up to 480 px wide. Desktop is unchanged (still 15.2 px). Re-run after
the fix: all fields 16 px, still 0 px sideways scroll.

The first attempt at the fix had no effect: the lead form's own rules come
later in the file and won. The selector was made more specific, and the re-run
confirmed it.

## Full regression run on the project laptop

`pytest tests -v` with the backend running.

| File | Tests | Result |
|---|---|---|
| `tests/test_chat.py` | 13 | Pass |
| `tests/test_lead.py` | 30 | Pass |
| `tests/test_lead_api.py` | 5 | Pass |
| **Total** | **48** | **48 passed in 71.14 s**, 18 Nov, 10:52 PKT |

Run on the project laptop with the real backend and real Gemini, n8n running.
API-05 sent the "Automated Test" lead as designed.

The CHAT tests passing doesn't contradict the AC-1 failure: no CHAT test asks
an area + bedrooms question. A regression test for RET-04 should be added when
it's fixed.

## Requirement traceability (Stage 1 and 2)

| Requirement | Tests | Status |
|---|---|---|
| FR-01 question through a web widget | W-02..04, W-20 | Pass |
| FR-02 retrieve relevant passages | CHAT-02..04, CHAT-11, AC-1 | Pass, **except AC-1 (RET-04)** |
| FR-03 answer only from passages | CHAT-02..05 | Pass |
| FR-04 say "I don't know" | CHAT-05, AC-3 | Pass |
| FR-05 show sources | CHAT-09, W-21, S-01..05 | Pass |
| FR-06 decline off-topic | CHAT-06, AC-2 | Pass |
| FR-07 offer a human | L-01 | Pass |
| FR-08 consent before asking for details | L-02, L-04, LEAD consent tests | Pass |
| FR-09 validate leads | AC-5, LEAD-07/08, API-02/03 | Pass |
| FR-10 send to n8n | N8N-02, AC-4 | Pass |
| FR-11 row in Google Sheets | N8N-03, AC-4 | Pass |
| FR-12 email the agent | N8N-04, AC-4 | Pass |
| FR-13 tell the customer it was received | L-11, AC-4, AC-7 | Pass |
| FR-14 website presents the agency, opens chat | WEB-01..10, W-01 | Pass |
| FR-15 public live demo | — | Stage 3 |
| FR-16 answer in the customer's language | — | Not tested ("Could") |

## Open items carried into Stage 3

| ID | Item |
|---|---|
| RET-04 | AC-1 fails: area + bedrooms question misses the only DHA listing. Fix with metadata filtering. |
| LEAD-R1 | Leads in `pending.jsonl` aren't re-sent automatically. |
| N8N-S1 | Webhook needs a secret. Google tokens expire every 7 days in Testing mode. |
| ING-06 | Re-run ingestion, expect no duplicates. |
| RATE-01 | Free-tier limits to be read from AI Studio. |
| — | Delete `data/listings/03_rawalpindi.md`. Confirm the robot animation licence. |
