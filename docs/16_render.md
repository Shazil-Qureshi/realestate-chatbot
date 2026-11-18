# 16 · Backend on Render

| | |
|---|---|
| **Task** | 3.3 Backend hosting (first planned on Hugging Face Spaces) |
| **Date** | 18 November 2026 |
| **Requirements** | FR-15 (public live demo), NFR-02 (free tier), NFR-03, NFR-06, NFR-09, AC-10 |
| **Status** | In progress: demo mode and wake-up handling built and tested; Render service not created yet |

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

## Setting up Render

*(Filled in as the steps are done.)*

## Live tests

| Test ID | Check | Result |
|---|---|---|
| DOCK-04 | Image builds on Render | Not yet run |
| DOCK-05 | Build log: 56 chunks stored | Not yet run |
| DOCK-06 | `/health`: ok, 56 chunks, `leads_demo: true` | Not yet run |
| DOCK-07 | After sleeping and waking: 56 chunks, no new embedding calls (AC-10) | Not yet run |
| DOCK-08 | No `.env`, key file or lead data in the image | Not yet run |
| R-01 | `/chat` answers from the public address | Not yet run |
| R-02 | Memory stays within 512 MB | Not yet run |
