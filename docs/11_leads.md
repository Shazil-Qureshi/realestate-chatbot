# Task 2.3 · Lead Capture

| | |
|---|---|
| **Task** | 2.3 `/lead` endpoint with consent |
| **Status** | Completed 17 November 2026. 35 tests pass on the project machine, including all 5 against the real server. |
| **Files** | `backend/leads.py` (new), `backend/main.py` (`/lead` route), `web/chat.js`, `web/chat.css`, `.gitignore`, `tests/test_lead.py`, `tests/test_lead_api.py` |

## Objective

Let a visitor who wants a person, rather than the bot, leave a name and phone
number. Only with their agreement, only if the details are plausible, and
without ever losing an enquiry.

## Requirements covered

| Req | Requirement | How |
|---|---|---|
| FR-07 | Offer to pass the customer to a person | "Talk to a person" above the chat input, always available |
| FR-08 | Ask for details only after the customer agrees | The bot asks first. The form appears only after "Yes, share my details", and the backend rejects any lead without `consent: true` |
| FR-09 | Validate: non-empty name, plausible phone | `LeadIn` in `leads.py`; same rules repeated in the browser for instant feedback |
| FR-10 | Send each accepted lead to n8n | `forward_lead()`, active once `N8N_WEBHOOK_URL` is set in Task 2.4 |
| FR-13 | Tell the customer their details were received | Thank-you message with a reference number |
| NFR-05 | Chat keeps working when n8n is down | Leads never touch `/chat`; a failed forward is saved to disk, not raised as an error |
| NFR-09 | Lead data not committed or shown to others | `backend/leads/` in `.gitignore`; replies and console output carry only the lead ID |
| AC-5 | Empty name or phone "abc" rejected with a clear message | LEAD-07, LEAD-08, L-06, L-07, API-02, API-03 |

## How a lead travels

```
"Talk to a person" → bot asks → "Yes, share my details" → form
        ↓ POST /lead {name, phone, email, property_ref, message, consent: true}
   LeadIn checks it ──bad──→ 422 with the reason, shown in the form
        ↓ good
   handle_lead() ─── hidden field filled? ──→ reply "received", keep nothing (bot)
        ↓
   forward_lead() ─── N8N_WEBHOOK_URL set and n8n answers 2xx ──→ in n8n
        └──────────── otherwise ──→ appended to backend/leads/pending.jsonl
        ↓
   {"status": "received", "lead_id": "d8fab71b5951"} → thank-you message
```

## Decisions and why

**Two steps, ask then form.** FR-08 says details are asked for only after
agreement. A form that appears on its own is asking. The bot asks in words,
and the "Yes" click is the agreement. The widget sets `consent: true` only on
that path, and the backend refuses a lead without it, so the rule doesn't
depend on the browser behaving.

**No lead is ever lost.** Until Task 2.4 there is no n8n. Later, n8n may be
asleep, misconfigured or down. In every one of those cases the lead is
appended to `backend/leads/pending.jsonl` and the visitor is still told it was
received, which is true. The file is the safety net and the to-do list for
anything n8n missed.

**Personal details stay in two places only:** n8n (and from there the sheet)
or the pending file. The visitor's reply contains a 12-character ID. The
console says `[lead d8fab71b5951] saved to pending.jsonl: no N8N_WEBHOOK_URL
set` and never a name or number. `/health` says whether leads go to n8n, but
never publishes the webhook address.

**Phone numbers are normalised, not reformatted.** `0300-1234567`,
`+92 300 1234567` and `(051) 111-2222` are all accepted. Spaces, dashes, dots
and brackets are removed, and a leading `+` is kept. The rule is 10 to 15
digits: wide enough for Pakistani mobiles and landlines and for international
numbers, narrow enough to reject "abc" and "12345".

**Names accept any script.** `عائشہ خان` is valid. A name must contain at
least one letter, so "12345" isn't one.

**A hidden "website" field catches simple bots.** People never see it, and it
is skipped by Tab and hidden from screen readers. Bots fill in every field. A
lead with it filled gets the normal success reply, so the bot learns nothing,
and nothing is kept.

**The thank-you message is honest.** Bella Real Estate is fictional, so it
says no agent will call and that the details went to the owner of the demo
site. A portfolio visitor who leaves a real number deserves to know.

**Validation lives in `leads.py`, apart from `main.py`.** That file needs
only Pydantic, so its tests run without the knowledge base, a Gemini key or a
server.

## Tests

### Unit tests: `tests/test_lead.py` (30 checks)

Run in the build environment: `30 passed in 0.55s`.

| Group | IDs | Covers |
|---|---|---|
| Accepted and cleaned | LEAD-01..06 | Four phone formats normalised, whitespace in names, an Urdu name, reference upper-cased, blank optional fields |
| Rejected | LEAD-07..15 | Empty name, phone "abc", 3 implausible phones, digits-only name, bad email, bad reference, 501-character note, consent false, consent missing |
| Forwarding | LEAD-16..19 | Sheet columns; n8n accepts; n8n not set / 500 / unreachable → saved to disk; appends |
| Privacy | LEAD-20..23 | No personal detail in the reply or the console; hidden field → nothing kept; pending folder is gitignored |

**Do the tests catch real bugs?** Three deliberate breakages were made to
`leads.py`, one at a time, and the suite was run against each:

| Breakage | Caught by |
|---|---|
| Consent check removed | LEAD-14 |
| Phone accepts any text | LEAD-08, LEAD-09 |
| Name printed to the console | LEAD-21 |

All three were caught. After restoring the file: 30 passed.

### Widget tests: L-01..17

Chromium through Playwright. The stand-in backend for `/lead` ran the real
`LeadIn` validation and the real `handle_lead()`, and shaped validation errors
exactly as FastAPI does. The messages the widget displayed are the ones in
`leads.py`.

| Test ID | Check | Result |
|---|---|---|
| L-01 | "Talk to a person" visible | Pass |
| L-02 | Bot asks first; no form until the visitor agrees | Pass |
| L-03 | Button disabled while the offer is open | Pass |
| L-04 | "Not now": no form, nothing sent, button usable again | Pass |
| L-05 | Focus moves to Name; property prefilled from the last answer | Pass |
| L-06 | Empty form stopped in the browser, nothing sent | Pass |
| L-07 | Phone "abc" rejected with a clear message | Pass |
| L-08 | A rejection only the server makes (bad email) is shown in its own words | Pass |
| L-09 | Backend down: explained, form kept so nothing typed is lost | Pass |
| L-10 | Request carries `consent: true`, empty hidden field, the property | Pass |
| L-11 | Thank-you message with the reference; says no agent will call | Pass |
| L-12 | Stored once, phone normalised to `03001234567` | Pass |
| L-13 | Hidden field filled: success shown, nothing stored | Pass |
| L-14 | Cancel says nothing was sent | Pass |
| L-15 | HTML typed as a name is shown as text, not run | Pass |
| L-16 | No JavaScript errors | Pass |
| L-17 | Phone screen: form fits, no sideways scroll | Pass |

The first run stopped at L-13 because of a fault in the test. After the
visitor clicks "Yes, share my details", those words also appear in the chat as
their reply. On the second round the test clicked the first matching text, the
old reply, rather than the new button. Selectors now target the buttons
themselves. The widget was not changed.

### Real endpoint: `tests/test_lead_api.py`

FastAPI isn't installed in the build environment, so the `/lead` route itself
has not run there. These tests run on the project machine against the real
server.

| Test ID | Check | Result |
|---|---|---|
| API-01 | `/health` reports where leads go, without the webhook address | **Pass**: `local file (n8n not set up)` |
| API-02 | Phone "abc" → 422 with the clear message | **Pass**: 422, "Enter a phone number with 10 to 15 digits…" |
| API-03 | Empty name → 422 | **Pass**: 422, "Enter your name." |
| API-04 | Consent false → 422 | **Pass** |
| API-05 | Valid lead → 200, reply contains an ID and nothing personal | **Pass**: `{'status': 'received', 'lead_id': 'abb2e106ca53'}` |

### Run on the project machine — 17 November 2026, 11:37 PKT

`pytest tests/test_lead.py tests/test_lead_api.py -v -s` → **35 passed in 2.36s.**

The server's own log for the run shows the privacy rule holding on the real
code path. It recorded `GET /health 200`, three `POST /lead 422`, then
`[lead abb2e106ca53] saved to pending.jsonl: no N8N_WEBHOOK_URL set` and
`POST /lead 200`. It logged an ID and a reason, and no name or number.

FastAPI's 422 messages arrive prefixed `"Value error, "`. The widget removes
that prefix before showing them (`leadProblems()` in `chat.js`), as L-08
showed.

**Still to be shown:** the browser form submitting to the real server. The
validation it relies on is tested above and the CORS setup is the same one
`/chat` already uses, so the risk is low. It is covered by Task 2.4's
end-to-end test (AC-4), which submits through the form and checks for a new
row in Google Sheets.

## Known limitations

- **No rate limit yet.** Someone could submit many leads. Rate limiting is
  planned for Stage 3 (NFR-04, AC-9). The hidden field stops simple bots only.
- **Leads in `pending.jsonl` are not re-sent automatically** once n8n is up.
  They are kept, not lost, but forwarding them is a manual step for now.
- **On Hugging Face Spaces the disk is temporary.** A lead saved to the
  pending file there is lost when the Space restarts. That makes n8n the real
  destination in production, and Stage 3 must keep it reliable.
