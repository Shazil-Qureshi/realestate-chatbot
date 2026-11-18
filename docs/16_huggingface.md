# 16 · Backend on Hugging Face Spaces

| | |
|---|---|
| **Task** | 3.3 Backend on Hugging Face Spaces |
| **Date** | 18 November 2026 |
| **Requirements** | FR-15 (public live demo), NFR-02 (free tier), NFR-03, NFR-06, NFR-09, AC-10 |
| **Status** | In progress: demo mode built and tested; Space not created yet |

## Terms

| Term | What it is |
|---|---|
| **Space** | A small app hosted by Hugging Face. Each Space is its own Git repository. Hugging Face builds it with our `Dockerfile` and runs it on a free CPU machine. |
| **Secret** | A setting Hugging Face keeps hidden, even from people who can see the Space's files. Used for the API key. |
| **Variable** | A visible setting, for things that aren't secret (model names, demo mode). |
| **Access token** | A password-like key for pushing code to Hugging Face from the command line. Made on Hugging Face, typed only into Git's sign-in box, never into a file. |

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

Set with `LEADS_DEMO_MODE=true` on Hugging Face only. On the laptop it's left
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

## Setting up the Space

*(Filled in as the steps are done.)*

## Live tests

| Test ID | Check | Result |
|---|---|---|
| DOCK-04 | Image builds on Hugging Face | Not yet run |
| DOCK-05 | Build log: 56 chunks stored | Not yet run |
| DOCK-06 | `/health`: ok, 56 chunks, `leads_demo: true` | Not yet run |
| DOCK-07 | After a restart: 56 chunks, no new embedding calls (AC-10) | Not yet run |
| DOCK-08 | No `.env` or lead data in the Space files | Not yet run |
| HF-01 | `/chat` answers from the public address | Not yet run |
