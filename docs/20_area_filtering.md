# 20 · Area filtering: the fix for RET-04

| | |
|---|---|
| **Task** | 4.1 Full system test and fixes |
| **Date** | 25 November 2026 |
| **Requirements** | AC-1, FR-02; closes RET-04, and the root cause behind RET-01, RET-02 and RET-03 |
| **Status** | **Complete.** AC-1 passes, RET-04 closed. 35 unit tests plus 14 chat tests, all green. |

## The problem, stated exactly

Asked *"Do you have 3-bedroom houses in DHA?"* the chatbot answered:

> I do not have that information in my extracts. Would you like me to pass
> your question to the team?

Nothing false, nothing invented. But the data **does** contain a DHA property:
**BRE-S-102**, a 4-bedroom house in DHA Phase 2, and it is the only one. The
answer a person wants is:

> There is no 3-bedroom house in DHA. The nearest is BRE-S-102, a 4-bedroom
> house in DHA Phase 2.

The chatbot could not say that, because BRE-S-102 was never put in front of it.

## Why meaning-based search cannot fix this by itself

A vector search compares overall meaning. The words "3 bedroom" carry a lot of
that meaning, so the eight closest chunks were 3-bedroom listings from F-11,
E-11, Bahria Town and so on. The one DHA house — which is about DHA, but about
*four* bedrooms — came ninth or later and was dropped.

This is the same weakness recorded as RET-01 (city ignored), RET-02 (a needed
chunk missing) and RET-03 (recall). Each was patched by raising `TOP_K` or
adding a prompt rule. Those helped the specific question in front of us and
left the cause alone.

**The cause: "in DHA" is a hard constraint, not a flavour.** A person asking
for DHA does not want a close-enough area. Similarity cannot express "must
be", so something other than similarity has to carry it.

## The fix

Each listing chunk now stores a few plain facts alongside its text, and a
question that names an area gets a second, area-restricted search.

### 1. Facts on each listing (`backend/listing_meta.py`)

The data was already tidy, which made this reliable:

```
## BRE-S-102 — 10 Marla House, DHA Phase 2, Islamabad
- Type: House, for sale
- Bedrooms: 4
```

becomes

| Field | Value |
|---|---|
| `ref` | `BRE-S-102` |
| `city` | `islamabad` |
| `area` | `DHA Phase 2` |
| `area_key` | `dha` |
| `bedrooms` | `4` |
| `deal` | `sale` |
| `kind` | `house` |

All 17 listings parse, every one yielding an area key, a city, a bedroom count
and sale-or-rent (LM-01, LM-02). Company pages and FAQs are untouched: the
parser only recognises a `BRE-x-nnn — …` heading and returns nothing for
anything else (LM-04).

Area names are normalised so that what a visitor types matches what the data
says: `F-11/3` → `f-11`, `Satellite Town, Block B` → `satellite town`,
`Gulberg Greens` → `gulberg`, and `Defence` → `dha`, because people say both.

### 2. A second search when the question names an area

`retrieve()` in `backend/main.py`:

1. The ordinary meaning-based search runs, as before.
2. If the question names an area **that the data actually has**, a second
   search runs restricted to that area.
3. The area's chunks are placed first, and the ordinary results fill the
   remaining places up to `TOP_K`. Nothing is discarded except to stay within
   the limit, and a chunk found by both is kept once.

The vocabulary of areas is read from the stored listings at startup, not
written by hand here, so it is whatever is in the data.

### 3. The decision that makes AC-1 work: bedrooms are *not* filtered

The obvious move is to filter on everything the question says — area **and**
bedrooms. That would be wrong here. There is no 3-bedroom house in DHA, so a
filter on both returns **nothing**, and the chatbot goes straight back to "I
do not have that information".

Filtering on the area alone returns the DHA listings, and the model can then
do what a person would: see that none has 3 bedrooms and offer the closest.
The hard constraint is enforced; the soft one is left to the model to reason
about from the text.

### 4. Failing safe

If the index was built before this change it has no area metadata, the
vocabulary is empty, no area is ever matched, and retrieval behaves exactly as
it did before (LM-10). A failure in the filtered search is caught and the
ordinary results are returned. The visitor never loses an answer because of
this feature.

`/health` reports `area_filtering` as the number of areas known, so whether a
running server has the metadata can be checked without guessing.

## Updating an existing index costs nothing

The chunk text did not change, so the embeddings did not change. Only the
metadata is new. `ingest.py` now compares the stored metadata with the current
metadata and rewrites only what differs, using `collection.update`.

**No Gemini request is made, so refreshing an existing index is free** and does
not touch the free-tier quota (LM-18, LM-19, LM-20).

```powershell
python backend\ingest.py
```

Expect: `56 chunks already stored, 0 to go` followed by
`Metadata refreshed on 17 chunks (17 of them property listings). No embeddings were needed.`

The Docker image builds its index from scratch, so Render picks the metadata
up on the next deploy with no change to the Dockerfile.

## Tests executed

`pytest tests/test_listing_meta.py -v`, 25 November 2026, in the build
workspace. No server, no API key, no network.

| ID | Check | Result |
|---|---|---|
| LM-01 | Every listing in `data/` is recognised | **Pass** — 17 of 17 |
| LM-02 | Every listing yields area, city, bedrooms and sale/rent | **Pass** |
| LM-03 | The DHA case: exactly one DHA listing, BRE-S-102, 4 bedrooms, none with 3 | **Pass** |
| LM-04 | Company pages and FAQs get no listing metadata | **Pass** |
| LM-05 | Eight real area names normalise correctly | **Pass** |
| LM-06 | "Satellite Town" is not shortened to "satellite" | **Pass** |
| LM-07 | "Defence" is understood as DHA | **Pass** |
| LM-08 | Bedroom counts read from questions, nonsense ignored | **Pass** |
| LM-09 | Only areas present in the data are recognised | **Pass** |
| LM-10 | An index with no area metadata behaves as before | **Pass** |
| LM-11 | Buying or renting is read from the question | **Pass** |
| LM-12 | Area matches are placed first | **Pass** |
| LM-13 | Ordinary results fill the rest | **Pass** |
| LM-14 | A chunk found by both searches is kept once | **Pass** |
| LM-15 | `TOP_K` is respected | **Pass** |
| LM-16 | Documents, metadata and distances stay lined up | **Pass** |
| LM-17 | An empty area result leaves ordinary search untouched | **Pass** |
| LM-18 | An old index is upgraded with no embedding call | **Pass** |
| LM-19 | Running the refresh twice writes nothing | **Pass** |
| LM-20 | Only changed chunks are written | **Pass** |

**35 tests pass** (the table lists the distinct checks; several run over
multiple cases). With the other offline suites: **91 passed**.

## AC-1 passes

Run 25 November 2026, 21:57 PKT, against a backend on port 8001 reporting
`prompt version: 2026-11-25a (10 rules, near matches rule 10)` and
`area filtering: 12 areas`. The chatbot answered:

> Hello! We do not have any 3-bedroom houses in DHA.
>
> The only property we have in DHA is a 4-bedroom house:
> - BRE-S-102 (10 Marla House, DHA Phase 2, Islamabad)

**`tests/test_chat.py`: 14 passed.** AC-1 is **Pass** and RET-04 is closed.

### The retrieved chunks prove why this needed fixing

Lower numbers are closer in meaning:

```
0.2729  BRE-S-102 - DHA Phase 2            <- placed first by the area search
0.2364  BRE-R-305 - Bahria Town Phase 7
0.2415  BRE-R-202 - 3 Bedroom Apartment, E-11/4
0.2424  BRE-S-103 - Bahria Town Islamabad
0.2426  Booking a viewing
0.2566  BRE-S-302 - Bahria Town Phase 4
0.2590  BRE-R-203 - G-11/3
0.2615  BRE-S-106 - G-13/1
```

The one listing the customer actually wanted is the **furthest away of the
nine**. It is not a near miss that a slightly larger `TOP_K` would have
caught: by meaning alone it ranks below a page about booking a viewing.
That is the case for carrying facts alongside the text, in one screenful.

## It took two fixes, not one

Storing the area and searching by it was only half the job.

With retrieval fixed, BRE-S-102 *was* being retrieved - and the chatbot still
said "I do not have that information in my extracts". It was obeying
**rule 3** of its own system instruction, written in Stage 1:

> "If nothing in the extracts matches, say nothing matches rather than
> offering the closest thing."

The model was right and the instruction was wrong. Rule 3 existed for a good
reason - to stop Rawalpindi houses being offered to someone asking about
Islamabad - but it treated **every** constraint as hard, when only **place**
really is.

| Rule | Change |
|---|---|
| 3 | Keeps place (city or area) as a hard constraint, and says so more sharply: never offer a property in another place, never let one drift into the answer. The blanket ban on near matches is gone. |
| 10 (new) | Inside the place the customer named, if nothing meets every other detail, say so plainly and offer what *is* there, making clear how it differs. Explicitly not permission to guess, and explicitly not permission to cross into another area. |

Prompt version `2026-11-16c` → `2026-11-25a (10 rules, near matches rule 10)`.

Rule 3 is load-bearing, so the whole file was re-run rather than just CHAT-12:
**CHAT-03** (an Islamabad request must never return Rawalpindi codes) and
**CHAT-05** (genuine gaps are still admitted) both still pass. The rewording
loosened what it was meant to loosen and nothing else.

The new rule deliberately contains **no real reference code** as an example,
even though that would have made it more concrete. A reference code sitting in
the system instruction is a code the model can emit for an unrelated question,
which is exactly what rule 4 forbids.

## A false failure worth recording

The first re-run reported CHAT-12 as failed. The cause was not this project:

```
503 UNAVAILABLE - This model is currently experiencing high demand.
```

The request never reached Gemini, so nothing about the fix was tested, and the
failure looked identical to a broken answer.

`ask()` in `tests/test_chat.py` now retries an upstream 503 up to three times
with a growing pause. It is never skipped and never swallowed: if the model is
still refusing after the last try, the test **fails** and says plainly that the
cause was at Google, so nobody mistakes an outage for a defect here.

## Still to do

| Item | Why |
|---|---|
| Live | Deploy, then ask the live demo the DHA question |
| Full suite | `pytest tests -v` - expect 110 |
