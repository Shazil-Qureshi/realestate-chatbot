# Task 1.6 · Document Ingestion

| | |
|---|---|
| **Task** | 1.6 Document ingestion |
| **Status** | Completed 16 Nov 2026 — 56 chunks stored and searchable. ING-06 pending. |
| **Files** | `backend/ingest.py`, `backend/chroma_db/` (generated, not committed) |

## Objective

Turn 9 Markdown documents into something a computer can search by **meaning**
rather than by keyword, and store the result so the chatbot can look things up
in milliseconds.

## What this task actually does

```
data/*.md  →  chunks  →  embeddings  →  ChromaDB
 (words)      (pieces)   (numbers)      (searchable)
```

Four steps, and each one has a reason.

### 1. Chunking

A chunk is a small piece of a document. The chatbot never reads a whole file.
It retrieves two or three chunks and answers from those alone.

That means **every chunk has to make sense on its own.** A chunk reading
"It has three bedrooms and costs 185,000 rupees a month" is useless, because
nothing in it says which property "it" is.

This project splits at Markdown `## ` headings, because the business documents
were written in Task 1.3 with exactly that structure — one heading per
property, per service, per FAQ. Every chunk is then prefixed with its document
title and heading:

```
Islamabad Properties For Rent - BRE-R-201

Two bedroom apartment in F-11 Markaz, 1,100 square feet,
185,000 PKR per month, available now.
```

The prefix is what makes the chunk self-contained. This is why the document
structure from Task 1.3 mattered: good chunking is mostly a reward for having
written the source documents well.

Sections longer than 1,200 characters are split again at blank lines, never
mid-sentence, with the same prefix repeated on each piece. No section in this
project needed it — the largest chunk is 526 characters.

### 2. Embedding

An embedding is a list of numbers describing the *meaning* of a piece of text.
`gemini-embedding-2` returns 3,072 numbers per chunk.

Texts with similar meaning get similar numbers. That is the whole trick: it
makes "a flat to rent in Islamabad" find a chunk about an apartment in F-11,
even though the words "flat" and "apartment" never match.

### 3. Storing

ChromaDB keeps the numbers together with the original text and some metadata
(which file it came from, which heading). Searching compares the question's
numbers against every stored chunk's numbers and returns the closest.

The collection is configured with **cosine** distance rather than Chroma's
default. Cosine compares the *direction* of two lists of numbers; the default
compares the straight-line distance between their end points. For text meaning,
direction is the right measure.

### 4. Verifying

The script finishes by embedding a real question and searching for it, then
printing the top three matches with their distances. Saving data and *finding*
data are different claims, and only the second one matters.

## Technical concepts

| Term | What it means | Why it matters here |
|---|---|---|
| **Chunk** | A small, self-contained piece of a document | The unit the chatbot actually reads |
| **Embedding** | A list of numbers representing meaning | Lets the search match ideas, not words |
| **Dimension** | How many numbers are in one embedding | 3,072 for `gemini-embedding-2` |
| **Vector database** | A database that searches by closeness of numbers | ChromaDB |
| **Collection** | One named group of chunks inside it | `bella_real_estate` |
| **Cosine distance** | Compares direction of two vectors | Lower = closer in meaning |
| **Metadata** | Extra facts stored beside each chunk | Lets the answer cite its source file |
| **Idempotent** | Running twice gives the same result as running once | Chunk IDs are deterministic, so re-running never duplicates |

## The trap that shaped this script

The obvious way to save quota is to send all 56 chunks in one request. Google's
own embeddings documentation rules that out:

> With `gemini-embedding-2`, multiple inputs in one request produce a single
> aggregated embedding unless each is wrapped in its own `Content` object.

So a batched call would have returned **one** embedding representing all 56
chunks blended together. The code would not have crashed. It would have stored
nonsense, every search would have returned near-random results, and the cause
would have been invisible — there is no error message for "your embeddings are
meaningless".

`ingest.py` therefore sends **one chunk per request**: 56 requests instead of 1.
Slower, and unambiguously correct.

This was found by reading the API documentation before writing the code rather
than after debugging it. Worth remembering: an API that silently accepts the
wrong input is more dangerous than one that rejects it.

## Why `--dry-run` exists

The free-tier rate limits for this account are still unknown (see
`docs/06_gemini_api.md`). Running a script that fires an unknown number of API
requests into an unknown quota is how a project loses a day.

`--dry-run` does all the chunking and reporting with **no API calls and no
database writes**. It answers "how many requests will this cost?" before
spending anything.

## Instructions

```powershell
python backend\ingest.py --dry-run
```

Check the chunk count and read the sample chunk it prints. Then:

```powershell
python backend\ingest.py
```

The script is safe to re-run. Chunks already stored are detected and skipped,
so a run interrupted half way can be resumed without paying for the same
embeddings twice. Use `--rebuild` to delete everything and start clean, which
is required if `GEMINI_EMBEDDING_MODEL` ever changes.

## Testing procedure

| Test ID | Objective | Input | Expected result |
|---|---|---|---|
| ING-01 | Chunking produces sensible pieces | `--dry-run` | Chunk count > 40, no chunk over 1,200 characters |
| ING-02 | Chunk IDs are unique | `--dry-run` | `[PASS] All chunk IDs are unique` |
| ING-03 | Every document is read | `--dry-run` | All 9 files listed, none with 0 chunks |
| ING-04 | Embeddings are stored | live run | `Collection now holds 56` |
| ING-05 | Search returns relevant chunks | live run | Top result for "apartment for rent in Islamabad" is a rent listing, not a buying FAQ |
| ING-06 | Re-running does not duplicate | run twice | Second run reports 0 to do, count unchanged |

## Test results

### Dry run

Executed 16 November 2026 against the real `data/` folder.

| Test ID | Result | Evidence |
|---|---|---|
| ING-01 | **Pass** | 56 chunks. Smallest 106 characters, median 276, largest 526 — all within the 1,200 limit, so no section needed splitting. |
| ING-02 | **Pass** | `[PASS] All chunk IDs are unique` |
| ING-03 | **Pass** | All 9 files produced chunks: 6, 4, 5, 8, 8, 8, 6, 5, 6. |

Chunks per file:

| File | Chunks |
|---|---|
| `data/company_info/01_about_bella_real_estate.md` | 6 |
| `data/company_info/02_services_and_fees.md` | 4 |
| `data/company_info/03_viewing_process.md` | 5 |
| `data/faqs/01_buying_faqs.md` | 8 |
| `data/faqs/02_renting_faqs.md` | 8 |
| `data/faqs/03_general_faqs.md` | 8 |
| `data/listings/01_islamabad_for_sale.md` | 6 |
| `data/listings/02_islamabad_for_rent.md` | 5 |
| `data/listings/03_rawalpindi.md` | 6 |
| **Total** | **56** |

The three listing files produced 17 chunks between them, which matches the 17
properties written in Task 1.3 exactly — one chunk per property, as intended.

### Live run

Executed 16 November 2026, 10:59 PKT, after resolving the missing C++ runtime
(see Problems below).

| Test ID | Result | Evidence |
|---|---|---|
| ING-04 | **Pass** | `56 chunks stored. Collection now holds 56.` All 56 embedded with no failures and no retries. |
| ING-05 | **Pass, with a limitation worth recording** | All three results for "apartment for rent in Islamabad" were rent listings, not buying FAQs, which is the stated criterion. But the **top result was in Rawalpindi, not Islamabad.** See below. |
| ING-06 | Not yet run | Requires a second run to confirm nothing duplicates. |

### What the search actually returned

Query: *apartment for rent in Islamabad*

| Rank | Result | City | Distance |
|---|---|---|---|
| 1 | BRE-R-306, 2 bed apartment, Bahria Town Phase 8 | **Rawalpindi** | 0.1865 |
| 2 | BRE-R-204, 2 bed apartment, Gulberg Greens | Islamabad | 0.1942 |
| 3 | BRE-R-202, 3 bed apartment, E-11/4 | Islamabad | 0.2029 |

Every result is an apartment, and every result is for rent. The *kind* of thing
was matched correctly. The **city was not**, and the wrong city ranked first.

### Why, and what it means for Task 1.7

Semantic search compares overall meaning. "2 Bedroom Apartment, Bahria Town
Phase 8, Rawalpindi" and "apartment for rent in Islamabad" are very close in
meaning — both describe a rental apartment in a Pakistani city — and the city
name is a small part of that overall meaning. Vector search has no concept of a
hard filter; it has no way to express "must be Islamabad".

The three distances confirm it: 0.1865, 0.1942, 0.2029 are tightly clustered.
The model is saying these are all about equally relevant, because to it they
nearly are.

**This is not a bug and it is not fixed by better embeddings.** It is what
vector search is. Three standard responses exist:

1. Retrieve more chunks than needed and let the language model do the filtering.
   It can read "Rawalpindi" and exclude it.
2. Store the city as metadata at ingestion and filter on it before searching.
   Requires detecting the city in the question too.
3. Combine keyword matching with vector search (hybrid search).

**Task 1.7 uses option 1:** retrieve 5 chunks rather than 3, and instruct the
model explicitly to respect constraints such as city, budget and bedroom count,
and never to offer a property that does not match. Option 2 is recorded as a
possible improvement if testing in Task 1.8 shows option 1 is not enough.

Finding this now, from a real search on real data, is the reason the script
ends by searching rather than by reporting that it saved successfully.

## Problems encountered

| # | Problem | Cause | Fix |
|---|---|---|---|
| 1 | `ImportError: DLL load failed while importing chromadb_rust_bindings` when creating the ChromaDB client. The dry run was unaffected. | ChromaDB's search engine is compiled Rust, not Python. The `.pyd` file was present and intact (63 MB), but it depends on `MSVCP140.dll`, the Microsoft C++ runtime, which was not installed on this machine. Windows reports a missing *dependency* with the same message it uses for a missing *file*. | Confirmed with `Test-Path C:\Windows\System32\MSVCP140.dll` returning `False`, then installed the Visual C++ Redistributable from `https://aka.ms/vc14/vc_redist.x64.exe` and opened a new terminal. |

### Lesson: DEP-02 gave false confidence

Task 1.4's test DEP-02 ran `import chromadb` and printed `imports OK`. It
passed again *while this failure was happening*, because ChromaDB loads its
Rust engine lazily — only when a client is created, not on import.

An import test proves a package is installed. It does not prove it runs. A
useful smoke test has to exercise the thing, not just name it. This is recorded
against DEP-02 in `docs/04_environment_setup.md` and the check is replaced in
Task 1.8.

## Known risks

- **Quota.** 56 embedding requests plus 1 for the verification search. If the
  per-minute limit is below roughly 60, the default `--delay 0.5` may be too
  fast. Raise it with `--delay 2` if requests start failing.
- **Model lock-in.** These 56 embeddings are only searchable by
  `gemini-embedding-2`. Changing `GEMINI_EMBEDDING_MODEL` requires
  `--rebuild` and 56 fresh requests.
- **Chunk count is small.** 56 chunks is a modest knowledge base. It is enough
  to demonstrate RAG properly, but retrieval quality on edge-case questions
  will be limited by coverage, not by the model. Task 1.8 tests for this
  deliberately using the gaps recorded in `docs/05_business_documents.md`.

## RET-03: the document structure was the bug — 16 November 2026

CHAT-11 failed with `TOP_K = 8`:

```
not offered: ['BRE-S-302']
Of those, not even retrieved: ['BRE-S-302']
```

Raising `TOP_K` from 5 to 8 did not reach it. Before raising it further, the
titles of the three listing files were compared:

| File | Title line |
|---|---|
| `01_islamabad_for_sale.md` | `# Properties For Sale — Islamabad` |
| `02_islamabad_for_rent.md` | `# Properties For Rent — Islamabad` |
| `03_rawalpindi.md` | `# Properties — Rawalpindi` |

`ingest.py` stamps every chunk with its document title, so the two competing
properties were embedded as:

```
Properties For Sale — Islamabad - BRE-S-103 — 5 Marla House, Bahria Town...
Properties — Rawalpindi - BRE-S-302 — 5 Marla House, Bahria Town Phase 4...
```

Both are 5 marla, 3 bedroom, double storey houses for sale in Bahria Town.
Nearly identical. But the Islamabad chunk contains **"For Sale" twice** — once
in the title stamp, once in its `Type:` line — while the Rawalpindi chunk
contains it once and spends the title slot on "Rawalpindi", a word the
question never used.

Six Islamabad sale listings all received that free boost. BRE-S-302 did not.

**This was never a retrieval bug.** It was a document structure problem
presenting as one. The Rawalpindi file mixed sales and rentals under a single
title, so its chunks lost a signal the Islamabad files got for free from
having been split by transaction type.

### Fix applied

`03_rawalpindi.md` split into:

| New file | Title | Properties |
|---|---|---|
| `03_rawalpindi_for_sale.md` | `# Properties For Sale — Rawalpindi` | BRE-S-301..304 |
| `04_rawalpindi_for_rent.md` | `# Properties For Rent — Rawalpindi` | BRE-R-305, BRE-R-306 |

All three listing files now follow the same pattern. Chunk count is unchanged
at 56, and all six reference codes carried over.

The old `03_rawalpindi.md` was overwritten with comment lines only. `ingest.py`
skips `# ` lines in its fallback path, so it now produces zero chunks whether
or not it is deleted. Verified by dry run.

**Re-ingestion requires `--rebuild`.** Chunk IDs are derived from file paths,
so the six chunks stored under the old path would otherwise remain in the
collection as orphans alongside their replacements.

### Why this fix and not a bigger `TOP_K`

Raising `TOP_K` treats the symptom. It also costs precision: every extra
extract is more irrelevant material for the model to filter, and on a
56-chunk collection a `TOP_K` of 16 means retrieving nearly a third of the
knowledge base for every question.

Fixing the data fixes the cause, costs 56 embedding requests once, and leaves
the three listing files consistent with each other — which is worth having in
its own right.

Task 1.3 said that good chunking is mostly a reward for having written the
source documents well. This is the bill for the one place where they were not.

### Result after `--rebuild` — 16 November 2026, 12:08 PKT

Two separate defects were stacked on top of each other.

| Run | CHAT-11 message | Meaning |
|---|---|---|
| Before the split | not offered: BRE-S-302 · not retrieved: BRE-S-302 | Search never found it |
| First re-run (rebuild had not yet run) | identical | Database still held old IDs `data-listings-03-rawalpindi-md--*`, confirmed by reading `chroma.sqlite3` directly. The fix had not been tested. |
| After `--rebuild` | not offered: BRE-S-302 · not retrieved: **none** | **Search now finds it.** The document-structure theory is confirmed. |

The remaining failure is the system instruction. Nothing in it asked for every
match, and rule 7 asked for "two or three short paragraphs at most". Given a
brevity constraint and no completeness requirement, offering one good match
and stopping was a reasonable reading of a badly written prompt.

Fix in `backend/main.py`: rule 7 now says brevity means short sentences, never
fewer properties; a new rule 8 requires every matching property in the
extracts to be listed. The former rule 8 (operating cities) is now rule 9.

No re-ingest is needed for this one — the system instruction is read when the
server starts.

### Final result — 16 November 2026, 12:12 PKT

**13 passed.** CHAT-11 answer:

> We have 2 three-bedroom properties for sale:
> - BRE-S-103: 5 Marla House, Bahria Town Islamabad, Phase 8 (PKR 2.35 crore)
> - BRE-S-302: 5 Marla House, Bahria Town Phase 4, Rawalpindi (PKR 1.85 crore)

Both prices verified against the listing files.

The 12:10 run that failed came right after the prompt change but before the
server had been restarted. The server read the old instruction at startup and
kept using it. `PROMPT_VERSION` now appears in the startup banner and in
`/health`, and CHAT-01 fails if the server predates it, so a stale server can
no longer hide a change.

**Still fragile.** BRE-S-302 was retrieved at rank 8 of 8 (distance 0.3352),
the last slot. With `TOP_K = 5` it would have been missed, and adding a few
more similar listings could push it out again. RET-03 is recorded as
**mitigated, not solved**. The structural fix is metadata filtering
(bedrooms, city, sale/rent stored per chunk and filtered before the vector
search), listed for Stage 4 if time allows.
