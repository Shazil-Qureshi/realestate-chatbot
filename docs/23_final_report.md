# 23 · Final report

| | |
|---|---|
| **Project** | AI Real Estate Customer Support Chatbot |
| **Author** | Qazi Shazil Qureshi |
| **Period** | 13 – 25 November 2026 |
| **Repository** | <https://github.com/Shazil-Qureshi/realestate-chatbot> |
| **Live demo** | <https://shazil-qureshi.github.io/realestate-chatbot/> |
| **Status at this report** | 27 of 27 applicable tasks complete. **All 10 acceptance criteria pass.** Demo recording outstanding. |

## 1. What the project set out to do

Build a customer support chatbot for an estate agency that answers from the
company's own documents rather than from a language model's memory, shows where
each answer came from, refuses to invent what it does not know, and hands real
enquiries to a human.

The agency, Bella Real Estate, is fictional. Its nine documents — 17
properties, fee schedules, viewing procedures and FAQs — were written for this
project, with deliberate gaps so that "I don't know" could be tested properly.

## 2. What was built

| Part | Detail |
|---|---|
| Knowledge base | 9 documents → 56 searchable pieces, embedded with `gemini-embedding-2`, stored in ChromaDB with cosine distance |
| Backend | FastAPI with three endpoints: `/health`, `/chat`, `/lead`. Answers with `gemini-3.5-flash-lite` under a 10-rule system instruction |
| Website | Plain HTML, CSS and JavaScript. No framework, no build step. Chat widget with sources, consent flow and a contact form |
| Lead capture | Validated server-side, sent through n8n to Google Sheets with a Gmail alert; queued to disk if n8n is unreachable |
| Hosting | Docker image on Render (backend), GitHub Pages via GitHub Actions (website). Both free tiers |
| Protection | Per-visitor and whole-service rate limits, CORS allow-list, input length cap, honeypot field |
| Tests | 110 automated tests, 19 of which call the real model and the real server |
| Documentation | 23 documents written as the work happened, including every defect and wrong turn |

## 3. Results against the acceptance criteria

| ID | Criterion | Result |
|---|---|---|
| AC-1 | "3-bedroom houses in DHA?" answered from the listings, source named | **Pass** — after two fixes in Task 4.1. Verified on the live service |
| AC-2 | "Do you sell cars?" politely declined | **Pass** |
| AC-3 | A plausible but absent fact gets "I don't know", not a guess | **Pass** |
| AC-4 | Consent leads to a Google Sheets row and an email | **Pass** — on the real path, locally |
| AC-5 | Empty name or phone "abc" rejected clearly | **Pass** |
| AC-6 | The live demo works from a public URL on a laptop **and a phone** | **Pass** — laptop verified here; phone verified by the project owner, 26 Nov |
| AC-7 | A broken webhook still allows normal chat | **Pass** — lead queued, chat unaffected |
| AC-8 | No API key findable in the public repository | **Pass** — tree *and* all 21 commits of history searched |
| AC-9 | Exceeding the rate limit gives a clear message | **Pass** — verified live |
| AC-10 | Restarting the hosted backend needs no manual step | **Pass** |

**All ten pass.**

AC-6 was the last to close, on 26 November, when the site was opened on a real
phone and answered a question. It had deliberately been left open until then:
the earlier 375-pixel checks were done in a desktop browser reduced to phone
size, which is not the same thing and was never accepted as the phone half.

## 4. The defect worth writing about

**RET-04** was open from 18 to 25 November and is the most instructive thing in
this project.

Asked *"Do you have 3-bedroom houses in DHA?"*, the chatbot said it had no
information. That was not a hallucination and not a crash. It was wrong in a
quieter way: the data contains exactly one DHA property, BRE-S-102, and the
useful answer is *"there is no 3-bedroom house in DHA; the one there has four."*

**First wrong assumption: that more retrieval would fix it.** RET-01, RET-02
and RET-03 were the same weakness, each patched by raising `TOP_K` or adding a
prompt rule. When BRE-S-102 was finally measured it came back at a distance of
**0.2729 — the furthest of nine pieces**, below a page about booking viewings.
The words "three bedroom" outweighed "DHA". No realistic `TOP_K` would have
caught it, because meaning-based search cannot express *must be*.

The fix was to give each listing its area as a plain fact and run a second,
area-restricted search when a question names an area. One deliberate decision:
**bedrooms are not filtered**. Filtering on both would return nothing, and the
chatbot would say "I don't know" again.

**Second wrong assumption: that fixing retrieval would fix the answer.** With
BRE-S-102 now retrieved, the chatbot *still* said it had no information — because
rule 3 of its own system instruction said:

> "If nothing in the extracts matches, say nothing matches rather than offering
> the closest thing."

**The model was obeying correctly. The instruction was wrong.** Rule 3 existed
to stop Rawalpindi houses being offered for an Islamabad question, which is
right, but it treated every constraint as hard when only *place* is. Rule 3 was
narrowed to place, and rule 10 was added for near matches inside a named place.

Two lessons sit behind one defect: a retrieval problem can be a prompt problem
wearing a disguise, and the component that looks broken may be the one following
orders.

## 5. Other defects found and fixed

| ID | Problem | Fix |
|---|---|---|
| UI-01 | Form fields at 15.2 px made iPhone Safari zoom on tap | 16 px below 480 px wide. The first attempt had no effect — a later rule won on specificity |
| — | A Docker build "succeeded" and shipped an index with **zero** pieces | `ingest.py` stops after 3 failures and exits non-zero, printing the cause at the end of the build log |
| — | Deploys failed their health check | The server opens its port first and loads in the background; `/health` answers `"starting"` |
| — | Hugging Face Docker Spaces turned out to be paid | Moved to Render. Pricing is now checked *before* a hosting choice, not after |
| PAGES-01 | GitHub Pages silently stopped republishing | `actions: read` plus splitting upload and deploy into two jobs. Both applied together, so the exact cause is **unconfirmed** and recorded as such |
| CORS-02 | `Retry-After` was invisible to the page | `expose_headers`. Found only by testing live |
| SEC-07 | An employer account name sat in a public document — which also claimed a search for it had found nothing | Removed; the false claim corrected. It remains in Git history, and that is recorded rather than hidden |

**A security incident also occurred.** A Google OAuth client secret was pasted
into a form and screenshotted. It was rotated, the old secrets deleted, and the
incident written up in `docs/16_render.md` without reproducing the secret.

## 6. What is still open

| ID | Item | Why it matters |
|---|---|---|
| NFR-01 | One live answer took 10.1 s against a 10 s requirement; four others took 1.7–2.1 s | An outlier, not a trend, but on the limit |
| LEAD-R1 | Queued leads are not re-sent | A lead saved during an outage needs manual recovery |
| N8N-S1 | The lead webhook has no shared secret | Not publicly reachable, but unauthenticated |
| SEC-19 | Response security headers never verified | Recorded as untested, not as passing |
| SEC-07 | Employer account name remains in Git history | Rewriting history changes every commit hash — a judgement call, not an oversight |
| RATE-01 | Rate limits are conservative guesses | Google no longer publishes per-model free-tier numbers |
| RET-01/02/03 | Mitigated, not structurally fixed | The area fix addresses the cause for areas; cities and other constraints still rely on prompt rules |

## 7. What I would do differently

**Check what a platform costs before building on it.** Two days of Docker work
were aimed at Hugging Face Spaces, which had become paid in July 2026. Nothing
was wasted — the image moved to Render — but the question should have come first.

**Treat "the version exists" and "the versions work together" as different
questions.** The GitHub Pages workflow was built from the newest major tag of
each action. The tags existed; the combination did not work. Three failed runs
and two confident wrong diagnoses followed.

**Distrust a passing build more than a failing one.** The deployment that
shipped an empty index exited 0 and looked fine. The failing ones were easy.

**Write the limitation down the moment it is known.** Everything in section 6
was known before it was asked about. A gap you listed reads as care; the same
gap discovered by someone else reads as the opposite.

**Verify, do not predict.** At one point in this project a test report was
written for a test that had never been run. It was caught by checking the files.
Everything in this report traces to an execution recorded in
`DAILY_PROGRESS.md`.

## 8. Conclusion

The chatbot does what it set out to do: it answers from the company's documents,
shows its sources, declines what it cannot support, and passes real enquiries to
a person. It is deployed, public, rate limited, and covered by 110 tests.

The part I would point a reviewer at is not the feature list. It is RET-04 — a
defect that stayed open for a week, resisted two plausible explanations, and
turned out to be two separate faults in two different layers, one of them in an
instruction I had written myself.

---

*Fictional company, fictional data, no real customer information at any point.*
