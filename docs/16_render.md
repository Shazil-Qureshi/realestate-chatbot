# 16 · Backend on Render

| | |
|---|---|
| **Task** | 3.3 Backend hosting (first planned on Hugging Face Spaces) |
| **Date** | 18 November 2026 |
| **Requirements** | FR-15 (public live demo), NFR-02 (free tier), NFR-03, NFR-06, NFR-09, AC-10 |
| **Status** | **Completed** 24 Nov. Live at <https://realestate-chatbot-4707.onrender.com>; wakes after sleep with no manual step (AC-10). |

## Terms

| Term | What it is |
|---|---|
| **Web service** | Render's name for a server it runs for you. Ours is built from the `Dockerfile` in the GitHub repository. |
| **Spin down / cold start** | A free service is put to sleep after 15 minutes without visitors. The next request wakes it, which takes about a minute. |
| **Environment variable** | A setting given to the running server, such as the model name. |
| **Secret File** | A file Render keeps hidden and hands to the build. It's how the API key reaches the step that builds the search index. |
| **Auto-deploy** | Render rebuilds and redeploys whenever new commits reach `main` on GitHub. |

## Why Render, not Hugging Face

Hugging Face was the plan in the project overview. On 18 November, creating
the Space showed **"Gradio and Docker Spaces require a paid plan"**. Forum
reports date this to July 2026
([forum](https://discuss.huggingface.co/t/docker-sdk-now-marked-as-paid-when-creating-a-new-space/177580)).
Only static Spaces stay free. A paid plan breaks NFR-02.

Options compared on 18 November 2026:

| Option | Card needed | Catch |
|---|---|---|
| **Render free (chosen)** | No | Sleeps after 15 min; about 1 min to wake; 512 MB memory |
| Railway free | No | $5 credit for the first month, then $1/month, so the demo would pause part-way through each month |
| Koyeb, Fly.io, Google Cloud Run | Yes | A card is needed, even when usage is free |
| Hugging Face Docker Space | Yes (PRO) | Paid since July 2026 |

Sources:
- [Render free tier](https://render.com/docs/free)
- [Render Docker secrets](https://render.com/docs/docker-secrets)
- [SnapDeploy "State of Free Hosting 2026"](https://snapdeploy.dev/state-of-free-hosting), rows verified September 2026

**Lesson:** check a host's current **pricing**, not only its technical
documentation, before choosing it. Free tiers change without notice.

## The 1-minute wake-up

A visitor who arrives after a quiet spell would otherwise see "can't be
reached". `web/chat.js` now handles it:

- After **6 seconds** without an answer, the waiting message changes to
  *"Waking up the assistant. The free server sleeps when no one has visited
  for a while, so this first answer can take up to a minute."*
- If the server isn't awake yet (no connection, or a 502/503/504 page from
  the host that isn't our own JSON), it **tries again every 5 seconds for up
  to 90 seconds**.
- **Our own errors are never retried.** They always carry `"detail"`. That
  way, a real failure never costs extra Gemini calls.
- The page also asks `/health` when it loads, for demo mode, which starts
  waking the server before the visitor even types.

| Test ID | Check (stand-in server, real widget) | Result |
|---|---|---|
| WAKE-01 | Asleep 3 times, then a 502 page twice, then answers | **Pass**: 6 attempts, wake-up message shown, answer displayed |
| WAKE-02 | Awake | **Pass**: 1 attempt, no wake-up message |
| WAKE-03 | Our own 503 (Gemini unavailable) | **Pass**: 1 attempt, not retried, error shown |
| WAKE-04 | A plain 500 | **Pass**: 1 attempt, not retried |
| WAKE-05 | Never wakes (limit shortened for the test) | **Pass**: gives up, says "can't be reached right now. Try again in a minute." |
| — | Send button usable again afterwards, no JavaScript errors, in all 5 | **Pass** |

## Decision: leads on the live site (18 Nov)

Hugging Face can't reach the n8n on the project laptop, and hosted n8n isn't
free (NFR-02). The owner chose **demo mode** for the live site:

- The chat works fully.
- "Talk to a person" says, **before** anything is typed, that this is a live
  demo and nothing will be kept. The button reads **"Try the form"**.
- The form checks the details exactly as normal (name, phone, consent), then
  the server **discards** them: not stored, not sent, not printed.
- The final message says the details passed every check and were discarded,
  and explains what the full setup would do.
- The full lead flow (Google Sheets + email) is shown with the laptop setup
  (AC-4, AC-7, `docs/12_n8n_workflow.md`).

Set with `LEADS_DEMO_MODE=true` on Render only. On the laptop it's left
empty, so nothing changes there. `/health` reports `"leads_demo": true/false`.

### How it was built

| File | Change |
|---|---|
| `backend/leads.py` | `handle_lead(..., demo=False)`. In demo mode it returns `{"status": "received", "lead_id": …, "demo": true}` and keeps nothing. The bot trap still runs first. |
| `backend/main.py` | Reads `LEADS_DEMO_MODE`. `/health` and the startup banner say where leads go. |
| `web/chat.js` | Asks `/health` once on page load. In demo mode it changes the offer, the button label, the privacy note and the thank-you message. If `/health` can't be reached, it uses the normal wording, and the server's reply still decides the final message, so it can never claim a demo lead was kept. |
| `backend/.env.example` | Documents `LEADS_DEMO_MODE`. |

### Tests (build workspace)

| Test ID | Check | Result |
|---|---|---|
| LEAD-24 | Demo mode: nothing sent to n8n, nothing written to disk | **Pass** |
| LEAD-25 | Demo mode: no name, phone or email in the reply or the console | **Pass** |
| LEAD-26 | Demo mode still rejects bad details | **Pass** |
| LEAD-27 | Normal mode reply has no `demo` flag | **Pass** |
| — | All 34 tests in `tests/test_lead.py` | **Pass** |
| — | Mutation check: with the demo branch disabled, LEAD-24 and LEAD-25 **fail** | Confirms the tests catch it |
| W-DEMO-1 | Widget in demo mode: demo offer, "Try the form", demo privacy note, bad phone rejected, demo thank-you, no JS errors | **Pass** |
| W-DEMO-2 | Widget in normal mode: unchanged wording, reference shown | **Pass** |
| W-DEMO-3 | `/health` unreachable, server in demo mode: normal offer, but the final message correctly says "discarded" | **Pass** |

Widget tests used a stand-in server running the real `leads.py`.

## Security incident · 18 November 2026, 16:22 PKT

**What happened.** While the Render Secret File was being filled in, the
wrong value was pasted: the **Google OAuth client secret** used by n8n
(`GOCSPX-…`, ending `vydS`), with `GEMINI_API_KEY=` in front of it. A
screenshot of that form was then shared in the build conversation, so the
secret must be treated as exposed.

**What it could allow.** With the client ID, someone could pose as this
OAuth app. It doesn't give access to the Google account by itself, because a
user still has to approve the sign-in. It was replaced anyway.

**Response.**
1. Deploy stopped before it ran. The wrong Secret File was deleted, and the
   correct Gemini key was entered (not shown to anyone).
2. The Google client secret is being replaced: new secret in Google Cloud →
   n8n Sheets and Gmail credentials updated → old secrets (`…vydS`, `…DwRc`)
   deleted → one test lead to confirm. *(Status recorded below once done.)*
3. The secret itself is not written in any project file or doc.

**Lessons.**
- Two different secrets were open at the same time and looked alike in
  the clipboard. Check the start of a key before pasting: Gemini keys
  start `AIza`, Google client secrets start `GOCSPX-`.
- Screenshot settings pages **before** pasting secrets, not after.
- A secret file holds only the value. `NAME=value` is `.env` format, and it's
  wrong here.

| Step | Status |
|---|---|
| Wrong Secret File deleted, correct key entered | Done (owner, 16:26) |
| New Google client secret, n8n credentials updated | Done 24 Nov. The first attempts failed with `Client authentication failed`: the new secret hadn't reached n8n. Fixed by Disconnect → paste → Save → Sign in again, for both credentials. |
| Old secrets deleted in Google Cloud | Done 24 Nov (owner) |
| Test lead reaches sheet and email | **Pass** 24 Nov, 11:40: lead `774f1aa51e32` accepted by n8n (`pending.jsonl` unchanged). The 5 test leads sent while it was broken are safe in `pending.jsonl` (see LEAD-R1). |

## First deploys (18 November)

| Deploy | Result | Cause | Fix |
|---|---|---|---|
| 1, 16:31 | Build failed: `secret GEMINI_API_KEY: not found` | The Secret File was missing: deleted during the incident above and not re-added | Secret File added |
| 2, 16:36 | Build **succeeded** (packages and the 56-chunk index, ~15 min); start **timed out** after Render's 15-minute health-check wait | `start.sh` ran `ingest.py` before starting the web server, and that sat on "Opening the vector database". The last log line was `[3/4] Opening the vector database`. No out-of-memory events. Render's free plan shows no CPU or memory graphs, so the exact cause can't be proven: either loading ChromaDB on 0.1 CPU is extremely slow, or it hangs. | See below |

| 3, 19 Nov (`d2adb64`) | Build **succeeded**, deploy **Live**. Startup took **10.4 s** on Render, so the port-first change worked. Then `[startup] FAILED: The collection is empty` and `/health` 503 | The index built into the image was **empty**. `ingest.py` printed failures but still exited with code 0, so the build carried on. **Bug in `ingest.py`, fixed:** it now exits with an error if any chunk fails, if fewer than all chunks are stored, or if the verification search fails. Checked with stand-ins here: all embeddings refused → `Index incomplete: 0 of 56`, exit 1; all succeed → 56 stored, exit 0. The reason Gemini refused during the build is in the rows below. | — |

Also seen: the Secret File was first saved as `GEMINI_API_KEY.txt`. Render
names a secret after its file, with `.` turned into `_`, so the build was
looking for a different name.

**Fixes after deploy 2:**
1. `start.sh` no longer runs `ingest.py` when the index is already in the
   image. It checks for `chroma_db/chroma.sqlite3`, which costs nothing.
2. `main.py` opens the web port **first** and loads ChromaDB and the Gemini
   library **in the background**. `/health` answers `"status": "starting"`
   until loading is done, which satisfies Render's check, and then `"ok"`.
   `/chat` waits up to 120 s for loading. The log prints
   `[startup] ready: 56 chunks, loaded in N s`, which finally measures the
   slowness. On the laptop (`python backend\main.py`) it still loads first,
   so nothing changes there.
3. `ANONYMIZED_TELEMETRY=False` in the Dockerfile turns off ChromaDB's
   anonymous usage reporting.

| 4, 20 Nov (`9d3af95`) | Build **failed in 1 min 20 s** (the early stop worked), with the reason printed at the bottom: `400 INVALID_ARGUMENT … API key not valid` | The key stored on Render was not a working key. `AQ.Ab…` is Google's newer, valid key format, so the format wasn't the problem; the stored value was. | The laptop's working key was pasted into both the variable and the Secret File |
| 5, 24 Nov | **Live.** Index built into the image | — | — |

Lesson: when a build step fails, make it print the cause as its **last** line. Render's
log search doesn't reach build output, so anything higher up is hard to find.

## Setting up Render

*(Filled in as the steps are done.)*

## Live tests

| Test ID | Check | Result |
|---|---|---|
| DOCK-04 | Image builds on Render | **Pass** (24 Nov) |
| DOCK-05 | Index in the image: 56 chunks | **Pass**: `/health` reports `chunks: 56` |
| DOCK-06 | `/health`: ok, 56 chunks, `leads_demo: true` | **Pass** (24 Nov, 10:13) |
| DOCK-07 | After sleeping and waking: 56 chunks, no new embedding calls (AC-10) | **Pass** (24 Nov): asleep after 15+ idle minutes (Render showed "SERVICE WAKING UP" at 10:58:51); within about 75 s `/health` was `ok`, 56 chunks; "What are your fees for buying a house?" answered in 2.2 s with the correct 1 percent commission. No manual step. |
| DOCK-08 | No `.env`, key file or lead data in the image | Not yet run |
| R-01 | `/chat` answers from the public address | **Pass**: "How do I book a viewing?" answered in 2.8 s with 8 sources; "Do you sell cars?" politely declined. Called from the `localhost:5500` origin, so CORS works too. |
| R-03 | `/lead` in demo mode | **Pass**: valid lead → `received`, `demo: true`; phone `abc` → 422 with the clear message |
| R-02 | Memory stays within 512 MB | Not yet run |
