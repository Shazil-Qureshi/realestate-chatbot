# 24 · Portfolio, CV and LinkedIn text

| | |
|---|---|
| **Task** | 4.4 Final report, portfolio and LinkedIn text |
| **Date** | 25 November 2026 |
| **Use** | Copy from here. Every number is checked against the repository. |

Links used throughout:

- Live demo — <https://shazil-qureshi.github.io/realestate-chatbot/>
- Code — <https://github.com/Shazil-Qureshi/realestate-chatbot>

---

## 1. CV entry

Replaces the current chatbot entry. Keeps the project name plain, with no
status word.

```
AI Real Estate Customer Support Chatbot
Python, FastAPI, Gemini API, embeddings, ChromaDB, n8n, Docker, Render, GitHub Pages
• Built a RAG chatbot answering property and customer questions from a company knowledge
  base, grounding every answer in retrieved documents, naming its sources, and declining
  rather than guessing when the documents do not cover a question.
• Fixed a retrieval failure where meaning-based search could not honour a hard constraint:
  the correct listing ranked last of nine results. Added per-listing metadata and an
  area-restricted second search, backed by a regression test.
• Added lead capture with consent and server-side validation, routed through an n8n
  workflow to Google Sheets with Gmail alerts, and queued to disk when the workflow is down.
• Deployed the FastAPI backend as a Docker service on Render and the site on GitHub Pages,
  with per-visitor and service-wide rate limiting and 110 automated tests.
```

**One-line version**, for a skills summary or a cover letter:

```
A RAG chatbot that answers from a company's own documents, shows its sources, says
"I don't know" when it should, and routes real enquiries to a human — deployed, public
and covered by 110 tests.
```

---

## 2. Portfolio / GitHub profile description

**Short, for a project card:**

```
A customer support chatbot for an estate agency that answers only from the company's own
documents. It shows which documents it used, refuses to invent what it does not know, and
hands real enquiries to a person. FastAPI, Gemini, ChromaDB and n8n, deployed on Render and
GitHub Pages, with 110 automated tests.
```

**Longer, for a portfolio page:**

```
An AI customer support chatbot for a fictional estate agency in Islamabad and Rawalpindi.

Nine company documents become 56 searchable pieces. Every answer is built only from the
pieces retrieved for that question, with its sources shown, so any claim can be checked.
When the documents do not cover something, it says so and offers to pass the question to a
person — and when a visitor agrees to share contact details, those details are validated and
sent through an n8n workflow into Google Sheets with an email alert to the agent.

The part worth reading about is a defect that stayed open for a week. Asked for a
three-bedroom house in a particular area, the chatbot said it had no information. It was
not hallucinating; it was wrong more quietly. The one property in that area ranked as the
*least* relevant of nine results, because "three bedroom" outweighed the area name in a
meaning-based search. Two fixes were needed: storing each listing's area as a fact and
searching it directly, and then correcting a rule in the chatbot's own instructions that
had forbidden it from offering a near match at all. The model had been obeying correctly;
the instruction was wrong.

Built with Python, FastAPI, the Gemini API, ChromaDB and n8n. Deployed as a Docker service
on Render with the site on GitHub Pages. 110 automated tests, 19 of which call the real
model, because those are the only ones that catch an answer that is fluent, confident and
wrong.
```

---

## 3. LinkedIn post

Two approaches. Pick one — do not post both.

### Option A — lead with the defect (recommended)

Technical readers stop for a specific bug. "Excited to announce" is scrolled past.

```
A chatbot I built told a customer it had no information. It was wrong — and not in the way
people expect.

The question: "Do you have 3-bedroom houses in DHA?"

There is no 3-bedroom house in DHA in the data. But there IS one house in DHA, with four
bedrooms. The useful answer is "no 3-bedroom there, but here's the one that exists." The
chatbot said it had nothing.

It took two fixes, and I was wrong about both of them at first.

1. I assumed retrieval needed to look harder. Then I measured: the correct listing came
back as the LEAST relevant of nine results — below a page about booking viewings. The
words "three bedroom" outweighed "DHA". Searching by meaning cannot express "must be in
DHA", so no amount of widening the search would have found it. Listings now carry their
area as a plain fact, and a question naming an area triggers a second search restricted
to it.

2. With the listing finally retrieved, the chatbot STILL said it had no information. Its
own instructions told it: "if nothing matches, say nothing matches rather than offering
the closest thing." I wrote that rule to stop it offering properties in the wrong city.
It was right about cities and wrong about bedroom counts.

The model had been obeying correctly the whole time. The bug was in my instruction.

A retrieval problem turned out to be a prompt problem wearing a disguise — and the
component that looked broken was the one following orders.

It's live, the code is public, and the full write-up including everything still open is in
the repo.

Live demo: https://shazil-qureshi.github.io/realestate-chatbot/
Code: https://github.com/Shazil-Qureshi/realestate-chatbot

#AI #RAG #Python #FastAPI #LLM
```

### Option B — lead with the project

For a broader audience.

```
I built an AI customer support chatbot that answers only from a company's own documents.

Most chatbot demos answer anything you ask. This one is built to do the opposite where it
matters: if the documents do not cover your question, it says so and offers to put you
through to a person. Every answer shows the documents it came from, so you can check it.

What's in it:
→ 9 company documents, searchable, with every answer grounded in retrieved text
→ Sources shown with each reply
→ Lead capture with consent, validated and routed to Google Sheets with an email alert
→ Rate limiting, so one busy afternoon cannot drain a free API quota
→ 110 automated tests, including ones that call the real model

Python, FastAPI, Gemini, ChromaDB, n8n, Docker. Deployed on Render and GitHub Pages.

The repository includes the things that went wrong: a retrieval bug that stayed open for a
week, a deployment that shipped an empty search index while reporting success, and the
limitations still open today.

Live demo: https://shazil-qureshi.github.io/realestate-chatbot/
Code: https://github.com/Shazil-Qureshi/realestate-chatbot

#AI #RAG #Python #FastAPI #MachineLearning
```

### Before posting

| Check | Why |
|---|---|
| Wake the demo first | The free tier sleeps. The first visitor after a quiet spell waits about a minute, and a post drives a burst of first visitors |
| Say the company is fictional if anyone asks | The site states it, but a comment thread may not |
| Watch the rate limit | 500 questions a day across all visitors. A post that lands well can reach that |

---

## 4. A note on the writing

These drafts are mine, not yours. They are written plainly and avoid the usual
launch-post habits, but they will not sound like you.

If you edit one before posting, keep the edit — I can learn your voice from it,
so future drafts start closer to how you actually write.
