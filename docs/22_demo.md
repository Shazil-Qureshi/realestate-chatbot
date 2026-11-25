# 22 · Demo video script and screenshots

| | |
|---|---|
| **Task** | 4.3 Demo video script and screenshots |
| **Date** | 25 November 2026 |
| **Target** | One video of about 2 minutes 45 seconds, and eight screenshots |
| **Audience** | A recruiter or engineer who will give this ninety seconds before deciding whether to keep watching |

## Before you press record

| Step | Why |
|---|---|
| **Wake the backend.** Open the live site and ask one question. Wait for the answer. | The free tier sleeps after 15 minutes. A cold start is about a minute of nothing happening, which is fatal on camera. |
| Ask a second question a moment later | Confirms it is properly warm, not half awake |
| Close every other tab; hide the bookmarks bar | Nothing of yours should be readable in the frame |
| Use a clean browser window at 1920 × 1080 | Matches the screenshots and reads well when scaled down |
| Check the taskbar | Notification badges and message previews are the most common accidental leak |
| **Have `backend\.env` closed, and never open a terminal that prints it** | The key must not appear in a single frame |

**If you record the n8n or Google Sheets part**, check the frame for: the
Google client secret, your own Gmail address, the webhook URL, and any real
person's details. Use the fictional test leads only.

## Timing you can rely on

Measured against the live service on 25 November 2026, five questions:

| Question | Time |
|---|---|
| "Do you have 3-bedroom houses in DHA?" | 1.7 s |
| "Do you sell cars?" | 1.8 s |
| "How do I book a viewing?" | 2.0 s |
| "What is your Karachi office address?" | 2.1 s |
| "What are your fees for buying a property?" | **10.1 s** |

Typical is about two seconds. The fees question was measurably slower once, so
**do not open with it on camera.** Lead with the DHA question, which is both
the fastest and the most interesting.

---

## The script

Times are cumulative. Narration is written to be read aloud at a normal pace —
say it in your own words rather than reciting it.

### 0:00 – 0:15 · What it is

**On screen:** the live site, top of the page, the demo banner visible.

> "This is a customer support chatbot for an estate agency. The agency is
> fictional, but everything behind it is real: it answers from the company's
> own documents, and it will tell you when it doesn't know something."

*Click the chat bubble.*

### 0:15 – 0:45 · It answers from documents, and shows them

**On screen:** type *"How do I book a viewing?"*

> "Every answer is built only from the company's own documents. It isn't
> recalling anything from training — it searched nine documents, picked the
> closest pieces, and answered from those."

*Expand the sources line.*

> "And it shows which ones. If an answer looks wrong, you can check it."

### 0:45 – 1:25 · The part worth watching

**On screen:** type *"Do you have 3-bedroom houses in DHA?"*

> "Now the interesting one. There is no three-bedroom house in DHA. A weak
> chatbot says 'I don't know'. A bad one invents a listing."

*Let the answer appear.*

> "It says there's no three-bedroom house in DHA, and then offers the one
> property that is in DHA — BRE-S-102, four bedrooms — with its reference code
> so you can ask about it.
>
> That took two fixes. Search by meaning alone couldn't find it: that listing
> scored as the *least* relevant of nine pieces, because the words
> 'three bedroom' outweighed 'DHA'. So listings now carry their area as a
> fact, and a question naming an area gets a second search restricted to it.
>
> And then it still said 'I don't know' — because its own instructions told it
> never to offer a near match. The model was right; the instruction was wrong."

### 1:25 – 1:45 · It refuses rather than invents

**On screen:** type *"What is your Karachi office address?"*

> "The agency only works in Islamabad and Rawalpindi. It doesn't invent an
> address, and it doesn't hide behind 'I don't have that information' either —
> where the company operates is a fact about the company."

*Optional, if time allows: "Do you sell cars?" for the off-topic refusal.*

### 1:45 – 2:15 · Handing over to a human

**On screen:** click **Talk to a person**, then **Try the form**.

> "When it can't help, it offers a person. It asks for consent before taking
> any details, and validates them."

*Type a bad phone number on purpose. Let the error show.* Then fill it in
properly and submit.

> "On the live demo the details are checked and then thrown away — nothing is
> stored. Running locally, this goes through an n8n workflow into Google
> Sheets and emails the agent."

*Optional cut to a Google Sheets row and the email alert.*

### 2:15 – 2:45 · What's behind it

**On screen:** the README's architecture diagram, then scroll the test output.

> "Website on GitHub Pages, FastAPI backend in Docker on Render, Gemini for
> the language work, ChromaDB for search, n8n for the lead workflow.
>
> A hundred and ten automated tests, including ones that call the real model —
> those are the only ones that catch an answer that's fluent, confident and
> wrong.
>
> The repository has twenty-two documents covering what was built, what broke,
> and what's still open."

*End on the live URL.*

---

## Screenshots

Save as PNG into `docs/images/`. Capture at 1920 × 1080 with **Win + Shift + S**.

| # | File | Shows | Must be in frame |
|---|---|---|---|
| 1 | `01-website.png` | The site with the chat bubble closed | The "fictional company" banner |
| 2 | `02-answer-with-sources.png` | An answered question, sources expanded | The sources list, legible |
| 3 | `03-dha-near-match.png` | **The DHA answer** | "no 3-bedroom", BRE-S-102, 4 bedrooms |
| 4 | `04-refusal.png` | The Karachi answer | The full refusal sentence |
| 5 | `05-lead-form.png` | The form with a validation error showing | The error text under the field |
| 6 | `06-thank-you.png` | The demo thank-you | The "discarded" wording |
| 7 | `07-n8n-workflow.png` | The n8n workflow canvas | All nodes — **no credentials panel open** |
| 8 | `08-google-sheet.png` | A sheet with test leads | Fictional names only |

**Screenshot 3 is the one to put in the README.** It is the only one that shows
something most chatbot demos get wrong.

Once captured, add to the README under the live-demo link:

```markdown
![The chatbot answering a question it cannot match exactly](docs/images/03-dha-near-match.png)
```

## A note on honesty in the demo

Everything in the script is behaviour the system actually has. Nothing is
staged, re-enacted or edited to look better than it is:

- The DHA answer is quoted from a live run on 25 November.
- The timings were measured, not estimated — including the slow one.
- The lead form genuinely discards details on the live demo, and the script
  says so rather than implying leads are stored.

If a question behaves differently on the day, change the script rather than
the take. A demo that shows one thing while the live site does another is
worse than no demo.
