# Task 1.7 · The `/chat` Endpoint

| | |
|---|---|
| **Task** | 1.7 `/chat` endpoint |
| **Status** | Completed 16 Nov 2026 — server runs, CHAT-01 and CHAT-02 verified. Remaining cases run by Task 1.8. |
| **Files** | `backend/main.py` |

## Objective

Turn the searchable knowledge base from Task 1.6 into something a website can
talk to: a web address that accepts a question and returns an answer with its
sources.

## What happens when a question arrives

```
question
   ↓  embed with gemini-embedding-2
numbers
   ↓  search ChromaDB, take the 5 closest chunks
extracts
   ↓  send extracts + question + rules to gemini-3.5-flash-lite
answer + sources
```

The language model never sees the knowledge base. It only ever sees five
extracts chosen by the search, plus the question. That is what "grounded"
means, and it is why the chatbot cannot invent a property that does not exist.

## Technical concepts

| Term | What it means | Why it is here |
|---|---|---|
| **API endpoint** | A web address a program can call | `/chat` and `/health` |
| **FastAPI** | A Python library that turns functions into endpoints | The whole server is two functions |
| **uvicorn** | The program that actually listens on a port | FastAPI describes, uvicorn serves |
| **POST** | An HTTP request that sends data | The question travels in the request body |
| **JSON** | A text format for structured data | `{"message": "..."}` in, `{"answer": "...", "sources": [...]}` out |
| **Pydantic model** | A declared shape for that data | Rejects a malformed request before your code runs |
| **CORS** | The browser rule that a page may only call servers that permit it | Without it the website in Stage 2 is blocked |
| **System instruction** | Standing rules given to the model, separate from the question | Where the anti-invention rules live |
| **Temperature** | How much randomness the model is allowed | Set to 0.2 — near-deterministic, because a support bot should not be creative |
| **Port** | The numbered door on your machine the server listens at | 8000 |

## Why `TOP_K = 5` and not 3

Task 1.6 ended with a real finding: searching for *"apartment for rent in
Islamabad"* returned a **Rawalpindi** property as the top result.

Vector search compares overall meaning and has no way to express "must be
Islamabad". The fix is not better embeddings — it is retrieving more material
and letting the language model apply the filter, because the model *can* read
the word "Rawalpindi" and exclude it.

So the endpoint retrieves five chunks and rule 3 of the system instruction
tells the model to respect every constraint in the question and to ignore
extracts that do not match.

Whether that is sufficient is a question for Task 1.8, not an assumption.

## The system instruction

Seven rules, each one preventing a specific failure:

| Rule | Prevents |
|---|---|
| 1. Answer only from the extracts | Answering from general knowledge about Pakistani property |
| 2. Say so when the answer is absent | Inventing a plausible-sounding fact |
| 3. Respect every constraint | The Rawalpindi problem above |
| 4. Never invent a price, code, size or status | The most damaging kind of error for an estate agency |
| 5. Always cite the reference code | Lets the customer follow up precisely |
| 6. Decline off-topic questions politely | Requirement FR-06 |
| 7. Be brief and warm | A support bot, not a brochure |

Rules 2 and 4 are the reason Task 1.3 deliberately left gaps in the business
documents. Those gaps are the test material for Task 1.8: a chatbot that
answers a question it has no information about has failed, however confident it
sounds.

## No distance threshold yet

An obvious addition is to reject chunks above some distance as irrelevant. That
requires a number, and there is no honest basis for one yet — the only measured
distances are 0.1865 to 0.2029, all from a question that *did* have good
matches.

Task 1.8 will ask deliberately off-topic questions and record what distances
they produce. A threshold set from that data is a measurement. A threshold
picked now would be a guess. The endpoint returns every distance in its
response specifically so that data can be collected.

## Instructions

```powershell
python backend\main.py
```

Then open <http://127.0.0.1:8000/docs> in a browser.

FastAPI generates that page automatically from the code. Click **POST /chat**,
then **Try it out**, replace the message text, and click **Execute**. You will
see the exact request sent and the exact response, with no frontend written.

Stop the server with `Ctrl+C`.

## Testing procedure

| Test ID | Objective | Input | Expected result |
|---|---|---|---|
| CHAT-01 | Server starts and the knowledge base loads | `GET /health` | `{"status":"ok","chunks":56,...}` |
| CHAT-02 | A normal question is answered from documents | "What is your commission on a sale?" | States 1% from each side, matching `02_services_and_fees.md` |
| CHAT-03 | Constraints are respected | "Show me apartments for rent in Islamabad" | Only Islamabad properties mentioned; the Rawalpindi listing retrieved by the search is not offered |
| CHAT-04 | Reference codes are cited | any property question | Answer contains a code such as `BRE-R-201` |
| CHAT-05 | Missing information is admitted | a question about a deliberate gap from `docs/05_business_documents.md` | Says it does not have that information; offers the team. Does **not** invent an answer |
| CHAT-06 | Off-topic questions are declined | "What is the capital of France?" | Politely declines and redirects |
| CHAT-07 | Empty message rejected | `{"message": ""}` | HTTP 400 |
| CHAT-08 | Over-long message rejected | 1,001 characters | HTTP 400 |
| CHAT-09 | Sources are returned | any question | `sources` lists 5 entries with file and distance |

## Test results

Run 16 November 2026, 11:06 PKT, through the `/docs` page.

| Test ID | Result | Evidence |
|---|---|---|
| CHAT-01 | **Pass** | Server started, reported `Knowledge base: 56 chunks`, uvicorn listening on 127.0.0.1:8000. |
| CHAT-02 | **Pass, verified against source** | Answer: *"our commission is 1 percent of the sale price from the buyer and 1 percent from the seller. This is the standard rate across Islamabad and Rawalpindi."* Checked against `data/company_info/02_services_and_fees.md`, which reads: *"Commission is 1 percent of the sale price from the buyer and 1 percent from the seller. This is the standard rate across Islamabad and Rawalpindi."* Near-verbatim. Retrieved from the right two documents at distances 0.2311 and 0.2509. |
| CHAT-03..10 | Not yet run | Automated in `tests/test_chat.py` under Task 1.8. |

Checking CHAT-02 against the source file is the point. An answer that *sounds*
right proves nothing; this one was traced back to the sentence it came from.

## Problem encountered

| # | Problem | Cause | Fix |
|---|---|---|---|
| 1 | `422 Unprocessable Content`, `"msg": "JSON decode error"`, `"ctx": {"error": "Expecting value"}` | The whole request body in `/docs` was replaced with plain text instead of only the text inside the quotes. The server received `What is your commission on a sale?` rather than `{"message": "..."}`. | Send the full JSON object. Nothing in the code was wrong — FastAPI rejected the request against the `ChatRequest` model before `chat()` ran, which is the Pydantic validation working as designed. |

Worth remembering how to read that error: `"loc": ["body", 0]` says the problem
is in the request body at character 0, and `Expecting value` means the first
character was not something JSON can begin with. A 4xx code means the request
was wrong; a 5xx means the server was.

## Known risks

- **Quota.** Every question costs two API calls, one to embed and one to
  answer. Testing nine cases is roughly 18 calls.
- **Rule-following is not guaranteed.** A system instruction is a strong
  influence, not a hard constraint. CHAT-03 and CHAT-05 exist precisely because
  the model may ignore rules 3 and 2. If it does, the fix is a stricter prompt
  or metadata filtering, and that will be recorded rather than hidden.
- **`temperature=0.2`** is passed to `GenerateContentConfig`. If the installed
  SDK rejects that field, the server raises a `TypeError` on the first question
  and the fix is to delete that one line.

## Task 1.8 run — 16 November 2026, 11:36 PKT

`pytest tests/test_chat.py -v -s` → **12 passed in 15.82s.**

| Test ID | Result | Note |
|---|---|---|
| CHAT-01 | Pass | 56 chunks reported |
| CHAT-02 | Pass | Verified against `02_services_and_fees.md` |
| CHAT-03 | Pass | No Rawalpindi reference code offered for an Islamabad question |
| CHAT-04 | Pass | Reference code cited |
| CHAT-05 (×3) | Pass | No invented rate for property tax, home loans or nearby schools |
| CHAT-06 | Pass | Did not answer the capital of France |
| CHAT-07 | Pass | Empty message → HTTP 400 |
| CHAT-08 | Pass | 1,001 characters → HTTP 400 |
| CHAT-09 | Pass | 5 sources returned, best distance 0.1036 |
| CHAT-10 | **Pass, but the answer was wrong** | See below |

### CHAT-03 outcome: the Rawalpindi problem did not recur

RET-01 recorded that vector search ranked a Rawalpindi property first for an
Islamabad question. Retrieving 5 chunks and instructing the model to respect
constraints (`TOP_K = 5`, rule 3) was the chosen mitigation. CHAT-03 passed, so
the mitigation held on this question. RET-01 moves from open to mitigated, not
to solved — one passing question is not proof for all questions.

### CHAT-10: a test that passed on a bad answer

Question: *"Do you have any properties in Lahore?"*

Answer: *"I do not have that information, as we only have offices in Islamabad
and Rawalpindi."*

The original assertion checked only that "Islamabad" or "Rawalpindi" appeared
somewhere in the answer. It did, so the test went green — on an answer that
opens by claiming ignorance of something the company knows perfectly well.

**Why it happened.** The retrieved extracts for that question were two
Rawalpindi listings, a buying FAQ, the viewing process and an Islamabad rental.
The chunk from `01_about_bella_real_estate.md` naming the two offices was *not*
retrieved. So the extracts genuinely contained nothing about Lahore, and rule 2
("say so plainly") fired correctly. The office fact came from the first line of
the system instruction, not from any extract.

Correct reasoning, unhelpful answer.

**Two fixes applied:**

1. **Rule 8 added to the system instruction.** Where the company operates is a
   fact about the company, not a gap in the extracts, so a question about any
   other city is answered directly rather than hedged.
2. **CHAT-10 tightened.** It now fails if the answer contains a hedge such as
   "I do not have that information", regardless of which cities it names.

### The lesson

A green test suite means every assertion held. It does not mean the system is
good. This assertion was written by the same person who wrote the system
instruction, and it checked for the thing he expected to go wrong rather than
reading what came back.

This is the reason `pytest` is run with `-s` on this project: so the answers
are printed and read, not just counted.

## Review of the full output — 16 November 2026, 11:44 PKT

Re-run after rule 8. 12 passed again, and CHAT-10 now answers properly:

> "Bella Real Estate operates only in Islamabad and Rawalpindi, so we do not
> operate in Lahore."

No hedge. Rule 8 worked.

### Answers verified against source documents

Not accepted because they sounded right. Each traced back to the file it came
from.

| Test | Claim in the answer | Source line | Verdict |
|---|---|---|---|
| CHAT-02 | 1 percent from buyer, 1 percent from seller | `02_services_and_fees.md` | Exact |
| CHAT-03 | BRE-R-202: 3 bed, furnished, E-11/4, PKR 145,000/month | `02_islamabad_for_rent.md` | Exact |
| CHAT-03 | BRE-R-204: 2 bed, unfurnished, Gulberg Greens, PKR 78,000/month | `02_islamabad_for_rent.md` | Exact |
| CHAT-04 | BRE-S-103, 3 bed, PKR 2.35 crore, furnished option PKR 2.65 crore | `01_islamabad_for_sale.md` Features line | Exact |
| CHAT-09 | Viewings free, no registration fee | `02_services_and_fees.md` | Exact |

The furnished-option price was checked specifically because an optional
second price is exactly the sort of plausible detail a model invents. It did
not. It is in the Features line verbatim.

### CHAT-03 was better than the test required

Retrieved eight-at-the-time-five chunks: BRE-R-202, BRE-R-204, BRE-R-203
(an upper portion), BRE-S-104 (for *sale*) and BRE-R-201 (a house).

Offered: only BRE-R-202 and BRE-R-204.

It correctly excluded a house, an upper portion and a for-sale property from a
question asking for *apartments for rent*. Rule 3 is doing real work, not just
passing a city check.

### CHAT-04: accurate but incomplete

Question: *"What three bedroom properties do you have for sale?"*

Answer: BRE-S-103 only.

Two properties qualify:

| Code | Bedrooms | Location | Offered? |
|---|---|---|---|
| BRE-S-103 | 3 | Bahria Town Islamabad, Phase 8 | Yes |
| BRE-S-302 | 3 | Bahria Town Phase 4, Rawalpindi | **No** |

BRE-S-302 was never retrieved — it was not among the five chunks the search
returned, so the model never saw it and could not have mentioned it.

**Nothing in the answer was wrong.** This is a different failure mode from
everything found so far, and a worse one commercially: a customer asks what
is available, is shown one option, and concludes that is all there is. No
error appears anywhere.

CHAT-04 passed because it only asserted that *a* reference code appeared. A
test that checks for the presence of something will never catch an absence.

**Response:**

1. `TOP_K` raised from 5 to 8. Retrieval happens locally in ChromaDB and costs
   no extra API call, so a larger number is cheap — though not free, since
   more extracts means more input tokens and more irrelevant material to
   filter.
2. **CHAT-11 added**, asserting that both BRE-S-103 and BRE-S-302 appear. Its
   failure message distinguishes the two possible causes: a code that was
   retrieved but not offered means the system instruction is at fault; a code
   never retrieved means `TOP_K` is still too low and a metadata filter on
   bedroom count is the next step.

Whether 8 is enough is a measurement, not an assumption. CHAT-11 takes it.

## Relevance threshold: now measurable

`docs/08` previously recorded that no honest basis existed for a distance
threshold. The test run provides one.

| Question | Nature | Best distance |
|---|---|---|
| "Do you charge for viewings?" | in scope, answer exists | **0.1036** |
| "Show me apartments for rent in Islamabad" | in scope, answer exists | 0.1856 |
| "What is your commission on a sale?" | in scope, answer exists | 0.2311 |
| "Do you have properties in Lahore?" | in scope, answer exists | 0.2722 |
| "What three bedroom properties for sale?" | in scope, answer exists | 0.2918 |
| "What property tax will I pay?" | **in scope, deliberate gap** | 0.2931 |
| "What is the capital of France?" | **out of scope** | **0.4419** |

Two conclusions, both from measurement rather than guesswork:

1. **A threshold near 0.40 would reliably separate out-of-scope questions**
   from everything else. The gap between 0.2931 and 0.4419 is wide and clean.
2. **No threshold can separate a deliberate gap from an answerable question.**
   Property tax scored 0.2931 — squarely inside the normal range — because the
   search correctly returned 10-marla house listings, which are genuinely
   similar to a question about tax on a 10-marla house. They simply do not
   contain the answer. Only reading the extracts reveals that, which is
   rule 2's job, and rule 2 is already doing it.

So a threshold would be a quota optimisation — skipping the chat API call
entirely for obvious nonsense — not a correctness improvement. Recorded as an
option for Stage 3 hardening, not implemented now, because it adds a way to
wrongly reject a real question in exchange for saving one API call.
