# Task 2.4 · n8n Workflow: Lead → Google Sheets → Email

| | |
|---|---|
| **Task** | 2.4 n8n workflow |
| **Status** | In Progress. n8n 2.47.7 running on the project machine; workflow file written; Google connection being set up. |
| **Requirements** | FR-10 (send to n8n), FR-11 (row in Google Sheets), FR-12 (email the agent), AC-4, AC-7, NFR-05 |

## Decision: where n8n runs

**Decided 17 November 2026: on the project machine (laptop) for now.** Public
hosting will be revisited in Stage 3.

### Options considered

Prices checked on 17 November 2026, not assumed.

| Option | Cost | For | Against |
|---|---|---|---|
| **Laptop (chosen)** | Free | Owned outright; fastest to build and test; nothing to expire | Not reachable from the internet, so the deployed site can't use it until Stage 3 |
| n8n Cloud | 14-day free trial, then about €24/month (Starter) | Easiest; online | Stops after 14 days unless paid. n8n no longer has a free Cloud plan. |
| Own Hugging Face Space | Free | Online beside the backend | More setup; free Spaces sleep and lose data on restart without an external database |
| A workplace n8n account belonging to someone else | — | Already connected to the build tools | Not the project owner's to use for personal work; runs live client workflows; the demo would die when access ends; visitors' details would land in another organisation's system |

The last option was ruled out on ownership and privacy grounds, not
technical ones. Inspecting it was read-only, and nothing was created or
changed there.

### Why the laptop is enough for now

`backend/leads.py` already copes with n8n being absent: leads go to
`backend/leads/pending.jsonl` and visitors are still told they were received
(NFR-05). Running n8n locally lets the whole flow be built, tested end to end
and recorded for the demo video. The workflow is exported into the project as
a file (`n8n/bella-lead-workflow.json`), so it is version-controlled and
portable to any n8n instance in Stage 3.

## Installation

### Node.js version: a trap avoided

n8n requires **Node.js 20.19 to 24.x inclusive** (n8n documentation). On 17
November 2026, nodejs.org lists **Node 26** as its newest LTS, which is
outside that range. Installing the default "LTS" download would give an
unsupported version.

**Use Node 24, latest v24.22.3** (released 10 November 2026). It's the same
lesson as Task 1.1, where the newest Python was not the right Python.

### Steps

1. Check for an existing Node: `node --version`. Any version from v20.19 to
   v24.x is fine; skip to step 3.
2. Otherwise install
   `https://nodejs.org/dist/v24.22.3/node-v24.22.3-x64.msi`, then open a
   **new** PowerShell window.
3. Start n8n: `npx n8n`. The first run downloads n8n and takes several
   minutes.
4. Open `http://localhost:5678` and create the local owner account. It's
   stored only on this machine, in `%USERPROFILE%\.n8n`.

### Installation result — 17 November 2026

The first attempt failed with `node : The term 'node' is not recognized`. A
check of `C:\Program Files` showed a `nodejs` folder, so Node was installed.
The PowerShell window had been opened before the install and held the old
`PATH`. The fix was refreshing `PATH` in that window rather than reinstalling.

n8n then started: **version 2.47.7**, editor at `http://localhost:5678`.

Warning shown at start-up, recorded for Stage 3: *"Running n8n outside a
container is deprecated. Future versions will require running n8n via the
official Docker image."* Fine for local development. Any public n8n must use
Docker, which Stage 3 uses anyway.

## The workflow

File: `n8n/bella-lead-workflow.json`. Set-up and test steps:
`n8n/README.md`.

Node parameters were taken from n8n's own type definitions (Webhook 2.1,
Google Sheets 4.7, Respond to Webhook 1.5, Gmail 2.2), not written from
memory.

```
Receive lead ──▶ Add row to Leads sheet ──▶ Tell backend it is saved ──▶ Email the agent
```

| Decision | Reason |
|---|---|
| Respond **after** the sheet write | The backend treats only a 2xx as "forwarded". If Sheets fails, the webhook returns an error, and `leads.py` keeps the lead in `pending.jsonl`. A lead can't be acknowledged without being stored somewhere. |
| Email **last** | An email failure must not undo or block a stored lead |
| `cellFormat: RAW` | Google's default (`USER_ENTERED`) would store `03001234567` as the number `3001234567`, dropping the 0. It would also evaluate a name beginning with `=` as a formula (spreadsheet formula injection). RAW stores the text as sent. |
| Plain-text email | Visitor-typed text goes into the email. Plain text can't be turned into HTML or links. |
| Gmail reads values from the webhook, not the sheet step | The sheet step's output depends on the sheet. The webhook body is exactly what the backend sent. |

## Google connection

Self-hosted n8n needs its own Google OAuth client (n8n documentation, "Google
OAuth2 single service"). Recorded constraints:

- **External app in Testing mode.** Only listed test users can sign in, and
  consent expires **every 7 days**, so the credentials must be reconnected
  weekly. Publishing the app would need Google's verification for the Gmail
  sending scope, which isn't proportionate for a demo.
- **The Client Secret is a credential.** It lives only in n8n's local store
  (`%USERPROFILE%\.n8n`), never in this repository.
- **A personal Google account is used, not a work one**, consistent with the
  hosting decision.

## Known risks

- **No authentication on the webhook yet.** Anyone who can reach
  `localhost:5678` could post a fake lead. On a laptop that's only this
  machine. Before any public deployment in Stage 3, the webhook must require
  a secret header, sent by the backend.
- **Weekly reconnection**, as above. If it lapses, Sheets fails, the webhook
  returns an error, and leads collect in `pending.jsonl` until reconnected.
  Nothing is lost, but nothing is emailed either.

## Set-up record — 17 November 2026

Google Cloud project `bella-n8n`, with the Sheets, Drive and Gmail APIs
enabled. External consent screen in Testing. One Web-application OAuth client,
redirect URI `http://localhost:5678/rest/oauth2-credential/callback`.

Problems met during set-up:

| Problem | Cause | Fix |
|---|---|---|
| "Connect to Google Sheets" in the node didn't lead to the ID and secret fields | The node's shortcut button in this n8n version | Created the credential from **+ → Credential → Google Sheets OAuth2 API** instead |
| The original client secret couldn't be copied | Google shows a secret in full only when it's created | **+ Add secret** on the client. Google allows two, so the same secret serves both the Sheets and Gmail credentials |
| Column boxes empty after choosing the sheet | Choosing a sheet reloads its columns and clears imported mappings | Eight expressions re-entered (`{{ $json.body.<column> }}`) |
| Cell Format reset to "Let Google Sheets format" | Same reload | Set to **"Let n8n format"**, n8n's name for `RAW`. N8N-03 confirms the leading 0 survives. |
| The build assistant's Chrome couldn't help | It was signed in to a different Google account, which has no access to the project | Nothing changed there. The sign-up prompt was not accepted, and the steps were done by hand in Edge. |

Follow-up: delete the unused original client secret (`****DwRc`) now that
both credentials use the new one.

## Test results

| Test ID | Check | Result |
|---|---|---|
| N8N-01 | Workflow imports with no errors | **Pass**: 4 nodes, connected in order |
| N8N-02 | Test lead → `ok: true` returned | **Pass**: `ok: True`, `lead_id: test00000001` |
| N8N-03 | Row appears, phone keeps its leading 0 | **Pass**: row 2, every column correct, phone `03001234567` |
| N8N-04 | Alert email arrives | **Pass**: received, confirmed by the project owner, 16:37 PKT |
| AC-4 | Lead submitted through the website form → row + email | **Pass**, see below |
| AC-7 | n8n unreachable → chat still works, lead kept in `pending.jsonl` | **Pass**, see below |

## AC-4: end to end through the website — 17 November 2026

A test lead was submitted through the real chat widget at
`http://localhost:5500` (Talk to a person → Yes → form) with fictional details.
The widget replied "Your details have been received (reference
`593762d3b99e`)".

Evidence, read on 18 November:

| Source | Shows |
|---|---|
| Leads sheet, row 3 | `593762d3b99e`, "Website Test", `03007654321`, `BRE-R-202`, the test note, source `website chat`. Every field correct, leading 0 kept. |
| n8n → Executions | Production runs at 16:52:47 and 16:59:59, both **Succeeded** (about 4.4–4.9 s), all four nodes green including **Email the agent**. The 16:34:36 run is the manual PowerShell test. |

A second website lead (row 4) was submitted by the project owner and also
arrived. Its phone was stored without a leading 0. Rows 2 and 3 show RAW
storage keeps a leading 0 when one is sent, so this reflects what was typed,
not a storage fault. Ten digits passes the 10–15 digit rule.

Evidence came from n8n's Executions list and the sheet rather than the backend
console: those are the systems of record, and the console only says what the
backend *tried*.

**Process note.** An attempt to read the backend console through desktop
control opened two empty PowerShell windows instead of focusing the existing
one, and the build assistant couldn't close them. They were left for the
owner to close. Desktop control is limited to looking and clicking for
terminals and to looking only for browsers, so it isn't a reliable way to read
terminal output here.

## AC-7: n8n down — 18 November 2026

This checks NFR-05: if n8n is unavailable, the chat keeps working and no lead
is lost.

The test plan said to point the webhook at a wrong address. Stopping n8n
instead (Ctrl+C in its window) gives the same result: nothing answers at the
webhook address. It is also closer to what really happens when the laptop's
n8n isn't running.

Steps, with n8n stopped and the backend and website running:

| Step | Result |
|---|---|
| `/health` | `status: ok`, `leads_go_to: n8n` (backend still configured for n8n) |
| Chat: "How do I book a viewing?" | Full answer (steps, hours, bring your CNIC), 8 documents checked |
| Lead through the widget (fictional: "Outage Test", `0300 1112233`, `BRE-R-204`) | Widget replied "Your details have been received (reference `7c15a05c05a2`)" |
| Backend console | `[lead 7c15a05c05a2] saved to pending.jsonl: n8n unreachable (ConnectError)`, then `POST /lead 200 OK` |
| `backend/leads/` on disk | `pending.jsonl` (461 bytes), last written 10:33 PKT, matching the test. Contents not opened. |

The visitor sees the same thank-you message whether the lead went to n8n or
to the fallback file. That is intended: the lead is safe either way, and
an outage is the owner's problem to fix, not the visitor's.

**Known limit.** Leads in `pending.jsonl` are **not re-sent automatically**
when n8n comes back. Lead `7c15a05c05a2` is in the file, not in the sheet.
Resending pending leads (by hand or with a small script) is recorded for
Stage 3.
