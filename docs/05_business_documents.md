# 05 · Business Documents (Knowledge Base)

| | |
|---|---|
| **Project** | AI Real Estate Customer Support Chatbot |
| **Phase** | Stage 1 – Backend and AI knowledge base |
| **Task** | 1.3 Business documents |
| **Last updated** | 14 November 2026 |
| **Status** | Completed |

## 1. Objective

Write the fictional company content that the chatbot will answer from. These
files are the chatbot's entire knowledge. Nothing the bot says will be better
than what is written here.

## 2. Technical concepts

| Term | What it means | Why it matters here | Example |
|---|---|---|---|
| **Knowledge base** | The set of documents the chatbot is allowed to answer from. | In RAG, the AI is forbidden from using outside knowledge, so anything missing here cannot be answered. | `data/listings/01_islamabad_for_sale.md` |
| **Chunk-friendly structure** | Writing in short, self-contained sections with headings. | The ingestion script splits documents into pieces. A piece that begins mid-sentence, or that mixes two properties, retrieves badly. | Each property starts with `## BRE-S-101` and holds all its own details. |
| **Self-contained fact** | A section that makes sense on its own, without the sections around it. | A retrieved chunk is read without its neighbours, so "it costs 2 crore" is useless if "it" was named three paragraphs earlier. | Every listing repeats the area and property type instead of saying "the same area". |
| **Deliberate gap** | A fact intentionally left out of the documents. | Needed to test FR-04: the chatbot must say "I don't know" rather than invent an answer. | No property tax rates appear anywhere. |
| **Grounding data** | Specific, checkable details: numbers, codes, names. | Vague content produces vague answers. Specific content lets us verify whether an answer was retrieved or invented. | `PKR 5.75 crore`, `BRE-S-102`, `DHA Phase 2 Sector J` |

Why this task sets a ceiling: if a document says "we have some nice houses in
good areas", no amount of AI quality turns that into a useful answer. If it
says "BRE-S-102, 10 marla, DHA Phase 2, 4 bedrooms, PKR 5.75 crore", the AI can
answer precisely and we can check it.

## 3. Tools and technologies

Plain Markdown text files. No code runs in this task.

## 4. Implementation details

### 4.1 The fictional company

Bella Real Estate, a residential agency in Islamabad and Rawalpindi, founded
2014. Head office in F-11 Markaz, branch in Bahria Town Phase 7. Residential
property only.

Every file states or implies that the company is fictional, and
`01_about_bella_real_estate.md` says so explicitly so the chatbot can answer
honestly if a visitor asks whether this is a real business (NFR-07).

### 4.2 Files written

| File | Contents |
|---|---|
| `data/company_info/01_about_bella_real_estate.md` | Company background, offices, hours, team, areas covered, what we do not handle |
| `data/company_info/02_services_and_fees.md` | Services, commission rates, payment terms, documentation support |
| `data/company_info/03_viewing_process.md` | Booking a viewing, making an offer, renting process, cancellations |
| `data/listings/01_islamabad_for_sale.md` | 6 properties for sale in Islamabad |
| `data/listings/02_islamabad_for_rent.md` | 5 properties for rent in Islamabad |
| `data/listings/03_rawalpindi.md` | 6 properties in Rawalpindi, sale and rent |
| `data/faqs/01_buying_faqs.md` | 8 buying questions |
| `data/faqs/02_renting_faqs.md` | 8 renting questions |
| `data/faqs/03_general_faqs.md` | 8 general questions |

Total: 9 documents, 17 properties, roughly 2,450 words.

### 4.3 Writing rules followed

1. Every property has a reference code (`BRE-S-101`) so answers can cite one.
2. Every property repeats its own area, type, size, price and status, so a
   retrieved chunk makes sense alone.
3. Prices are specific numbers in PKR, never ranges like "affordable".
4. Sections are short, so one chunk tends to hold one complete idea.
5. Three properties have a status other than "Available" (`Under offer`,
   `Rented`), so the chatbot has something non-obvious to report.

### 4.4 Deliberate gaps

These are **not** in the documents, on purpose. They are the test material for
FR-04 ("I don't know") and must stay absent:

| Missing information | Test question it enables |
|---|---|
| Property tax rates | "What property tax will I pay on a 10 marla house?" |
| Bank loans and mortgage rates | "Can you arrange a home loan?" |
| Whether pets are allowed | "Are pets allowed in BRE-R-204?" |
| Nearby schools and hospitals | "Which school is near BRE-S-103?" |
| Plot dimensions in feet | "What are the dimensions of BRE-S-101 in feet?" |
| Any city other than Islamabad and Rawalpindi | "Do you have anything in Lahore?" |

The last one is different: the documents *do* say we operate only in Islamabad
and Rawalpindi, so the chatbot should answer that directly rather than saying it
does not know. That contrast is useful for testing.

## 5. Files created or modified

The nine files in section 4.2, plus `docs/05_business_documents.md` and
`PROJECT_TRACKER.md`.

## 6. Instructions

The files are already written into `data/`. To review them, open the `data`
folder in VS Code. To add a property later, copy an existing block, change the
reference code and details, then rerun the ingestion script from Task 1.6.

## 7. Testing procedure

Documents are reviewed, not executed. The review checks:

1. Does every property have a unique reference code?
2. Does every property state its own area, size, price and status?
3. Are there any vague claims that cannot be checked?
4. Are the deliberate gaps genuinely absent from all nine files?

## 8. Test results

| Check | Method | Result |
|---|---|---|
| 17 unique reference codes, no duplicates | Counted codes across the three listing files | Pass |
| Every listing states area, size, price/rent and status | Read each listing block | Pass |
| No vague pricing language | Searched for "affordable", "cheap", "reasonable" | Pass, none present |
| Deliberate gaps absent | Searched all 9 files for "tax", "loan", "mortgage", "pet", "school" | Pass, no matches |
| Fictional notice present | Read `01_about_bella_real_estate.md` | Pass |

These checks were run on the written files on 14 November 2026. No application
code exists yet, so nothing else could be executed.

## 9. Problems encountered

Deciding how much to write. Too little gives the chatbot nothing to retrieve;
too much makes the free-tier embedding step slow and costly. Nine documents of
roughly 250 words each is enough to demonstrate retrieval while staying well
inside free limits.

## 10. Solutions

Settled on 17 properties across three files, plus three company documents and
three FAQ files. This produces enough chunks for retrieval to be meaningful
without approaching any quota.

## 11. Evidence

- [ ] Screenshot: `data/` folder expanded in VS Code showing all 9 files
- [ ] Screenshot: one listing file open

## 12. Completion status

Completed on 14 November 2026.

## 13. Next steps

Task 1.4: install the Python packages and pin them in
`backend/requirements.txt`, checking that each version works with Python 3.14.


## Amendment — 16 November 2026

`03_rawalpindi.md` has been split into `03_rawalpindi_for_sale.md` and
`04_rawalpindi_for_rent.md`.

Reason: it was the only listing file that mixed sales and rentals under one
title, and that inconsistency caused a real retrieval failure (RET-03, see
`docs/07_ingestion.md`). The Islamabad files were already split by transaction
type; Rawalpindi now matches them.

Content is unchanged — the same six properties, the same figures. Only the
file boundary and the two title lines are new.
