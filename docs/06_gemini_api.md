# Task 1.5 · Gemini API Key and First Call

| | |
|---|---|
| **Task** | 1.5 Gemini API key |
| **Status** | Completed 16 Nov 2026 — API-01..04 Pass. API-05 deferred to Stage 3. |
| **Files** | `backend/.env`, `backend/.env.example`, `backend/test_gemini.py` |

## Objective

Get an API key from Google AI Studio, store it so it never reaches GitHub,
and prove with a real call that both halves of the project work: the model
that **writes answers** and the model that **creates embeddings**.

## Technical concepts

| Term | What it means | Why we need it | Where it shows up |
|---|---|---|---|
| **API** | A way for your program to ask a service to do something, over the internet. | Gemini runs on Google's computers, not yours. | `client.models.generate_content(...)` |
| **API key** | A long secret string that proves the request is yours. | Without it the request is rejected. Anyone who has it can spend your quota. | `GEMINI_API_KEY` in `backend/.env` |
| **Environment variable** | A value stored outside the code and read at run time. | The code can be public while the key stays private. | `os.getenv("GEMINI_API_KEY")` |
| **`.env` file** | A plain text file holding environment variables for one project. | Keeps every secret in one place that Git ignores. | `backend/.env` |
| **`.env.example`** | The same file with the values removed. | Tells the next person which variables exist, without leaking any. | `backend/.env.example` |
| **Embedding** | A list of numbers that represents the meaning of a piece of text. | Two texts with similar meaning get similar numbers. That is how the chatbot finds the right document. | `result.embeddings[0].values` |
| **Dimension** | How many numbers are in one embedding. | Every chunk in the database must use the same model, so the dimensions match. | A 768-number or 3072-number vector |
| **Quota** | How much you are allowed to use per minute and per day on the free tier. | Exceeding it returns an error instead of an answer. | Visible in AI Studio |

## Why the model names are not written into the code

An earlier version of `backend/.env.example` contained two specific model
names. Google renames and retires Gemini models often, and a name that was
correct on one date can stop working weeks later. Publishing a name that has
not been checked against a live account is a guess.

So the project does the opposite. `backend/test_gemini.py` asks Google, using
your key, **which models your account can actually use**, and prints them. You
then copy the names it reports into `backend/.env`.

Two benefits:

1. The names come from a real response, not from documentation that may be out
   of date.
2. When Google renames something next year, the fix is one line in `.env`.
   No code changes, no redeployment of the Docker image.

## Security rules for this task

| Rule | Reason |
|---|---|
| The key goes only in `backend/.env` | `.gitignore` already excludes `.env`, so Git will never see it |
| Never paste the key into a `.py` file | Those files are committed to GitHub |
| Never paste the key into a chat, screenshot, or forum post | A key in a screenshot is a key that is public |
| `test_gemini.py` prints only the key's **length**, never its text | A screenshot of the output is safe to share |
| If a key is ever exposed, delete it in AI Studio and make a new one | Revoking takes seconds; a stolen key can drain quota for weeks |

## Security incident, 16 November 2026

Recorded because the project's own rules require it, and because the process
worked.

| | |
|---|---|
| **What happened** | The first API key was captured in a screenshot of `backend/.env` and shared outside the machine. The file had also been attached as context to a VS Code chat extension. |
| **Exposure** | The key was readable to anyone who saw the image. |
| **Detected** | Within minutes, before the key had been used for anything. |
| **Action taken** | Key deleted in AI Studio and a replacement generated. |
| **Damage** | None. No billing was attached to the account, and the key was revoked before use. |
| **Process change** | Screenshots are taken of the terminal, never of `.env`. `test_gemini.py` prints only the key's character count for exactly this reason, which is enough to prove the key loaded and to catch a half-pasted key. |

## Instructions

### 1. Create the key

Go to <https://aistudio.google.com> and sign in with a Google account, then
choose **Get API key** → **Create API key**. Copy it. The page may not show it
again in full.

### 2. Create `backend/.env`

In VS Code, in the `backend` folder, create a new file named exactly `.env`
(the name begins with a dot and has no other extension). Copy the whole
contents of `backend/.env.example` into it, then paste your key after
`GEMINI_API_KEY=`.

Leave `GEMINI_CHAT_MODEL` and `GEMINI_EMBEDDING_MODEL` empty for now.

There must be no spaces around the `=` and no quotation marks:

```
GEMINI_API_KEY=AIza...
```

### 3. Run the check, first pass

```powershell
python backend\test_gemini.py
```

Steps 1 and 2 should pass and print two lists of model names. Steps 3 and 4
will report `[SKIP]`, because the two model names are still empty. That is the
expected result of the first run.

### 4. Fill in the two model names

Copy one name from each printed list into `backend/.env`. Prefer a lightweight
or "flash" model for chat: it is faster and uses less of the free quota.

### 5. Run the check, second pass

```powershell
python backend\test_gemini.py
```

All four steps should now pass, and step 4 should report how many numbers are
in one embedding.

### 6. Record the free-tier limits

In AI Studio, find the rate limits shown for your account and write the
requests-per-minute and requests-per-day figures into the table below. This
closes an item that has been open since Task 0.1.

## Testing procedure

| Test ID | Objective | Input | Expected result |
|---|---|---|---|
| API-01 | `.env` is found and the key is read | `python backend\test_gemini.py` | `[PASS] GEMINI_API_KEY loaded (N characters)` |
| API-02 | The key is valid | same run | `[PASS] Key accepted. N models visible to this key.` |
| API-03 | A real question returns a real answer | same run, after step 4 | `[PASS] <model> replied: working` |
| API-04 | A real embedding is returned | same run, after step 4 | `[PASS] <model> returned a vector of N numbers` |
| API-05 | The key is not in Git | `git status` after Stage 3 begins | `.env` does not appear in the list |

## Test results

Run on the project machine, 16 November 2026.

| Test ID | Objective | Result | Evidence |
|---|---|---|---|
| API-01 | `.env` is found and the key is read | **Pass** | 10:21 PKT. First run at 10:15 correctly reported `[FAIL] GEMINI_API_KEY is empty`, which confirmed the check works before it confirmed the key works. |
| API-02 | The key is valid | **Pass** | Google returned the model list for this key. |
| API-03 | A real question returns a real answer | **Pass** | 10:27 PKT. `gemini-3.5-flash-lite replied: working` |
| API-04 | A real embedding is returned | **Pass** | 10:27 PKT. `gemini-embedding-2 returned a vector of 3072 numbers`, beginning `[-0.0139, 0.0235, 0.0086]` |
| API-05 | The key is not in Git | Not yet run | Checked in Stage 3. |

## Models available to this account

Reported by `test_gemini.py` on 16 November 2026. This is the account's own
answer, not a figure copied from documentation.

**Can answer questions:** `gemini-3.5-flash`, `gemini-3.5-flash-lite`,
`gemini-3.6-flash`, `gemini-3.7-flash`, `gemini-3.8-flash`, `gemini-4-argon`,
`gemini-4-carbon`, `gemini-4-hydrogen`, `gemini-omni-flash-preview`,
`gemini-nano-banana-2.1`, three `antigravity-preview-*` entries and three
`deep-research-*preview*` entries.

**Can create embeddings:** `gemini-embedding-001`, `gemini-embedding-2`.

### Known limitation of the listing

The script groups models by name when the SDK does not expose a
`supported_actions` field. That fallback is imperfect: `gemini-nano-banana-2.1`
is an image model and was placed in the chat list because its name contains no
embedding keyword. The list is a starting point for choosing, not a guarantee
that every entry suits every purpose.

## Models chosen, and why

| Setting | Value | Reason |
|---|---|---|
| `GEMINI_CHAT_MODEL` | `gemini-3.5-flash-lite` | In a RAG system the retrieval step does the hard work. The model's job is to summarise text it has already been handed, which a lightweight model does well. "Lite" is the fastest and cheapest tier, which matters because a chat widget must feel instant and the free quota has to cover a whole day of testing. |
| `GEMINI_EMBEDDING_MODEL` | `gemini-embedding-2` | Google's current recommendation for new work. It accepts 8,192 input tokens against 2,048 for `gemini-embedding-001`, so no realistic chunk can overflow it. |

### Rejected and why

- **Anything containing `preview`** — `antigravity-preview-*`,
  `deep-research-*preview*`, `gemini-omni-flash-preview`. Preview models can be
  withdrawn without notice. This project is deployed publicly as a portfolio
  piece, so a model that disappears breaks a live demo during an interview.
- **`gemini-4-*`** — newest generation. Newest usually means the tightest free
  quota and the highest chance of change during the project.
- **`gemini-embedding-001`** — still supported, but text-only with a quarter of
  the input limit, and not the recommended choice for new projects.

### Confirmed embedding dimension

`gemini-embedding-2` returned **3,072 numbers** per embedding on this account,
matching the documented default. Every chunk stored in Task 1.6 will be a list
of 3,072 numbers.

### Limitation found after the models were chosen

Google's embeddings documentation states that `task_type`
(`RETRIEVAL_DOCUMENT` / `RETRIEVAL_QUERY`) is supported by
`gemini-embedding-001` but **not** by `gemini-embedding-2`. Task types let a
retrieval system embed documents and questions slightly differently, which
improves matching.

This was not known when the model was chosen. The decision stands, because
`gemini-embedding-2` is the newer and stronger base model and the project's
chunks are far too short to need the task-type distinction to work at all. If
retrieval quality proves disappointing in Task 1.8, switching to
`gemini-embedding-001` is a bounded change: edit one line in `.env`, then run
`python backend/ingest.py --rebuild`.

Recorded here rather than quietly dropped, because a decision made on partial
information should say which part was missing.

### The one decision that is expensive to reverse

Google's documentation states that the embedding spaces of `gemini-embedding-2`
and `gemini-embedding-001` are **incompatible**. A chunk embedded by one model
cannot be searched using the other.

That means changing `GEMINI_EMBEDDING_MODEL` after Task 1.6 requires deleting
`backend/chroma_db/` and re-ingesting every document. The chat model can be
swapped freely at any time; the embedding model cannot. This is recorded in the
README.

## Free-tier limits

This question has been open since Task 0.1. It now has an answer, and the
answer is that there is no general answer.

Google's official rate-limits page does not publish per-model free-tier
numbers. It states that limits depend on the account's usage tier and
"can be viewed in Google AI Studio". So any blog post quoting exact
requests-per-day figures is quoting a number that may not apply to this
account.

| Limit | Value | Where it was read |
|---|---|---|
| Requests per minute | to be read from AI Studio | AI Studio rate-limits page |
| Requests per day | to be read from AI Studio | AI Studio rate-limits page |
| Date checked | | |

**Action before Task 1.6:** read the figures from AI Studio and fill this table
in. Ingestion embeds every chunk of all 9 business documents in one run, so the
requests-per-minute figure decides whether that run needs a delay between
calls.

## Known risks

- **Quota exhaustion during testing.** Ingestion in Task 1.6 embeds every chunk
  of all 9 business documents. If that exceeds the daily limit, the rest of
  Day 1 stops until the quota resets. Mitigation: record the limits in the
  table above *before* running ingestion, and count the chunks first.
- **Embedding model lock-in.** Every chunk must be embedded by the same model
  that later embeds the user's question. Changing `GEMINI_EMBEDDING_MODEL`
  after ingestion means deleting `backend/chroma_db/` and re-ingesting. This is
  worth noting in the README.
