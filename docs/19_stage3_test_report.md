# 19 · Stage 3 Test Report and Security Checklist

| | |
|---|---|
| **Task** | 3.6 Live tests and security checklist |
| **Date** | 25 November 2026 |
| **Scope** | The deployed system: website on GitHub Pages, backend on Render, and the public repository. |
| **Rule** | A result is written down only after the test was actually run. Anything not run says so. |

## Summary

| | Count |
|---|---|
| Security checks run | 19 |
| Passed | 17 |
| Findings | 1 (SEC-07, minor, privacy not security) |
| Not verifiable from here | 1 (SEC-19) |
| Acceptance criteria re-checked live | 6 |
| Passed | 5 |
| **Failed** | **1, AC-1 (RET-04, known since 2.5)** |

No secret of any kind is in the public repository, in the working tree or in
any of its 21 commits of history.

## Where the tests ran

| Where | What |
|---|---|
| Fresh anonymous clone of the public repository | SEC-01 to SEC-12 |
| The live website, in Chrome, calling the live Render backend | SEC-13 to SEC-19, AC-1, AC-3, AC-5, NFR-01 |
| Earlier in Stage 3, recorded in [16](16_render.md), [17](17_github_pages.md), [18](18_rate_limiting.md) | AC-2, AC-9, AC-10 |

## Security checklist

The repository was cloned fresh, without signing in, and both the working tree
and **every commit in history** were searched. History matters: a secret
removed in a later commit is still readable in an earlier one.

| ID | Check | Result |
|---|---|---|
| SEC-01 | No Gemini API key, old `AIza` or new `AQ.Ab` format | **Pass** - no match in the tree or in history |
| SEC-02 | No Google OAuth client secret (`GOCSPX-`), access token (`ya29.`), private key block, AWS key, GitHub or Slack token, or `Bearer` literal | **Pass** - no match in the tree or in history |
| SEC-03 | No `.env` committed; only `.env.example`, holding placeholders | **Pass** - `GEMINI_API_KEY= your_gemini_api_key_here` |
| SEC-04 | No lead data or vector database ever committed | **Pass** - no `leads/`, `.jsonl`, `chroma` or `.sqlite` file has ever been added in any commit |
| SEC-05 | `.gitignore` covers `.env`, `backend/leads/`, `chroma_db/`, caches, test output | **Pass** |
| SEC-06 | No personal Gmail address anywhere | **Pass** - no match in the tree or in history |
| SEC-07 | No work or employer account identifier | **Finding** - see below |
| SEC-08 | No code prints or logs a secret | **Pass** - the only line naming `GEMINI_API_KEY` in a `print` reports that it is *missing* |
| SEC-09 | The real n8n webhook address is not in the repository, and `/health` does not reveal it | **Pass** - only `https://n8n.example/webhook` in tests; `/health` returns a description such as "nowhere (demo mode: checked, then discarded)" |
| SEC-10 | CORS is an explicit allow-list, not a wildcard | **Pass** - `allow_origins` is a named list; no `*` |
| SEC-11 | The Docker image does not contain the API key | **Pass** - mounted with `RUN --mount=type=secret` for one build step; only the embedding *model name* is an `ENV` |
| SEC-12 | The n8n workflow export carries no credentials or private identifiers | **Pass** - no `credentials` block; Google Sheet id is `""`; `sendTo` is `REPLACE_WITH_YOUR_EMAIL@example.com` |
| SEC-13 | Malformed input does not leak internals | **Pass** - broken JSON returns a 422 validation message; no traceback, file path or line number |
| SEC-14 | Question length is capped before Gemini is called | **Pass** - 5,000 characters rejected with "The message is too long. Limit is 1000 characters." (400), costing no quota |
| SEC-15 | Consent is enforced on the server, not only in the widget | **Pass** - `consent: false` rejected with "Details can only be sent once you have agreed to share them." (422) |
| SEC-16 | The honeypot field behaves correctly | **Pass** - a filled honeypot returns a normal "received", which is the point: a bot must not learn it was caught. It is discarded, covered by the unit tests |
| SEC-17 | HTTPS end to end, no mixed content | **Pass** - page `https:`, API `https:`, no `http://` resource on the page |
| SEC-18 | The API documentation page `/docs` is reachable by anyone | **Deliberate** - see below |
| SEC-19 | HTTP response security headers | **Not verified** - see below |

### SEC-07: the work account name (minor, privacy not security)

The scan found an employer GitHub account name written into
`docs/14_github.md`, in the paragraph recording the push-403 incident.

This is **not a credential**. Nothing can be signed in to with it. But it is an
internal identifier sitting in a public portfolio repository, and it links this
repository to an employer account for no benefit.

Worse, the same document's AC-8 row claimed that a search for the work account
name "found nothing". That claim was false: the name was in that very file,
two paragraphs above the claim. The earlier AC-8 pass was therefore recorded
on an incomplete check.

**Done:** the name has been removed from the text, and the false claim has been
removed from the AC-8 row of [14](14_github.md), which now carries a correction
note.

**Still true:** the name remains in the Git history of that file, in 20 earlier
commits. Removing it from history means rewriting every commit after it
(`git filter-repo` or BFG) and force-pushing, which changes every commit hash
and breaks any existing clone. For a username that is not a credential, that
cost is not obviously worth paying. **This is the owner's decision, and it is
recorded here rather than quietly dropped.**

### SEC-18: `/docs` is public

FastAPI serves interactive API documentation at `/docs`, and it answers 200 to
anyone. For this project that is wanted: a reviewer can try the API without
installing anything, and it is part of showing the work.

What it costs: it reveals the API surface, its fields and its validation rules.
That is acceptable here because the endpoints behind it are rate limited
(Task 3.5), reject oversized input (SEC-14) and hold no private data in demo
mode. It is listed so that the choice is a choice, not an oversight.

### SEC-19: response headers were not verified

Headers such as `X-Content-Type-Options` or `Referrer-Policy` could **not** be
checked. A browser hides response headers from a page on another origin unless
the server lists them in `Access-Control-Expose-Headers`, and the build
workspace cannot reach `onrender.com` directly. So this is recorded as **not
tested**, not as a pass. For a JSON API consumed by one widget the value is
low, but the gap is real and is carried forward.

## Acceptance criteria, re-checked against the live system

| ID | Criterion | How it was run | Result |
|---|---|---|---|
| AC-1 | 3-bedroom houses in DHA, answered from the listings | Live `/chat` from the live site | **Fail**, RET-04, unchanged |
| AC-2 | Off-topic question declined | Live widget, 11:00 PKT ([18](18_rate_limiting.md)) | **Pass** - "I can only help with questions about Bella Real Estate, property, or renting and buying homes." |
| AC-3 | No invented Karachi address | Live `/chat` | **Pass** - "Bella Real Estate operates only in Islamabad and Rawalpindi. We do not operate in Karachi." 1.9 s |
| AC-5 | Empty name and phone "abc" rejected clearly | Live `/lead` | **Pass** - "Enter your name." / "Enter a phone number with 10 to 15 digits, for example 0300 1234567." |
| AC-6 | Live demo works on a laptop **and a phone** | Laptop: live, Chrome. Phone: by the project owner, 26 Nov | **Pass** - both halves |
| AC-9 | Rate limit returns a clear message | [18](18_rate_limiting.md) | **Pass** |
| AC-10 | Restart or wake needs no manual step | [16](16_render.md) | **Pass** |

AC-4 and AC-7 cannot be re-run against the live service: it runs with
`LEADS_DEMO_MODE=true`, so no lead reaches Google Sheets or Gmail. Both passed
on the real path on the project laptop in Stage 2 ([12](12_n8n_workflow.md)).

### AC-1 is still the same failure

Asked live, the chatbot answered: *"I do not have that information in my
extracts. Would you like me to pass your question to the team?"* Honest, and it
invents nothing, but it still cannot mention **BRE-S-102**, the only DHA house,
because that chunk was never retrieved. The eight sources returned were
3-bedroom listings from other areas - exactly the cause written up in
[13](13_stage2_test_report.md): the bedroom words outrank the area.

Unchanged since 2.5, fix planned for Stage 4 (metadata filtering).

### NFR-01, speed

| Question | Time |
|---|---|
| "What is your Karachi office address?" | 1.9 s |
| "Do you have 3-bedroom houses in DHA?" | 2.0 s |

Within the 10 second requirement, with the service already awake. A first
request after 15 minutes of sleep takes up to about a minute, which the widget
covers with its "Waking up..." message (tested in 3.3).

## Open items after 3.6

| ID | Item |
|---|---|
| RET-04 | AC-1: area + bedrooms question misses the only DHA listing. Metadata filtering, Stage 4 |
| RATE-01 | Read the real free-tier quota from AI Studio and tune `RATE_CHAT_TOTAL_PER_DAY` from its conservative 500 |
| SEC-07 | Decide whether to rewrite Git history to remove the work account name, or accept it |
| SEC-19 | Response security headers never verified |
| LEAD-R1 | Leads in `pending.jsonl` are not re-sent automatically |
| N8N-S1 | The n8n webhook has no shared secret; Google tokens expire every 7 days in Testing mode |
| — | Confirm the robot animation licence |
