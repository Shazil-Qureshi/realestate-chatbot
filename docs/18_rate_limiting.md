# 18 · Rate limiting

| | |
|---|---|
| **Task** | 3.5 CORS and rate limiting |
| **Date** | 25 November 2026 |
| **Requirements** | NFR-04, AC-9 |
| **Status** | **Completed** 25 Nov. AC-9 passed against the live service. Two follow-ups below: the live website is still serving the old `chat.js`, and the `Retry-After` CORS fix needs the next deploy. |

CORS, the other half of 3.5, was already in place and was verified in use
during 3.4. See [17](17_github_pages.md).

## Terms

| Term | What it is |
|---|---|
| **Rate limit** | A cap on how many requests something may make in a period. |
| **429** | The HTTP code for "too many requests". |
| **Retry-After** | A header saying how many seconds to wait. |
| **Sliding window** | Counting the requests in the last N seconds, continuously, rather than resetting the count at a fixed moment. |
| **Quota** | What Google allows this Gemini key per day. Running out stops the demo answering. |

## Why the demo needs this

The backend is public, so anyone can send it requests. Two risks:

1. **The Gemini free-tier quota.** Every `/chat` question costs **two** Gemini
   calls: one to turn the question into numbers (embedding) and one to write
   the answer. A few hundred questions could stop the demo working for the
   rest of the day.
2. **The demo contact form.** Even in demo mode it does validation work and
   fills the log.

### What the quota actually is

Unknown, and deliberately not guessed. Google's rate-limit page no longer
lists free-tier numbers per model; it says they are shown per account at
<https://aistudio.google.com/rate-limit>. This closes **RATE-01** as far as
design goes: the limiter does not try to match Google's numbers. It sets its
own conservative caps, and every one is adjustable from an environment
variable, so once the real number is read from AI Studio the caps can be
tuned without changing any code.

## The limits

In `backend/ratelimit.py`. All defaults, all overridable.

| Setting | Default | What it protects |
|---|---|---|
| `RATE_CHAT_PER_MINUTE` | 10 per visitor | One person flooding the demo. A human asking questions sends one every few seconds at most. |
| `RATE_CHAT_PER_DAY` | 100 per visitor | A slow drip from one visitor all day |
| `RATE_CHAT_TOTAL_PER_DAY` | 500 for everyone | **The Gemini quota.** 500 questions = about 1,000 Gemini calls. |
| `RATE_LEAD_PER_MINUTE` | 5 per visitor | Form spam |
| `RATE_LEAD_PER_DAY` | 20 per visitor | Form spam over a day |
| `RATE_LIMIT_ENABLED` | `true` | Set `false` to turn it all off |

A setting that is missing, empty, not a number, or zero or less falls back to
the default (RL-19). A typo must never silently remove a limit.

## How the counting works

A **sliding window**. For each visitor the times of recent requests are kept.
To check "10 per minute", every time older than 60 seconds is dropped and what
is left is counted. If that is already 10, the request is refused, and because
the oldest kept time is known the answer can say exactly how many seconds to
wait.

Two deliberate choices:

- **A refused request is not recorded** (RL-06). If refusals counted, someone
  retrying every second would push their own wait out for ever.
- **A fixed reset was rejected.** With a reset at the top of each minute, a
  visitor refused at 10:59:59 would get a full fresh allowance one second
  later, and could send twice the limit across the boundary.

## The gate order, and why

`/chat` passes three gates, in this order:

1. **Whole service, per day.** If the demo's day is spent, nothing else
   matters, and a refusal should not use up the visitor's own allowance.
2. **This visitor, per minute.**
3. **This visitor, per day.**

The check runs **before any work is done** — before the embedding call. A
refused request must not cost quota, which is the whole point.

## Who counts as one visitor

Render sits in front of the app, so the address the app sees is Render's own.
Every visitor would look like one person. The visitor's real address is the
first entry of the `X-Forwarded-For` header, which Render sets.

**Written down on purpose:** the app cannot prove that header is genuine.
Someone could set it to a different value on each request and look like many
visitors, getting around the per-visitor gates. That is exactly why
`RATE_CHAT_TOTAL_PER_DAY` exists: it counts every request whatever address it
claims, so the Gemini quota is protected even then.

### Requests from the same machine are not counted

`127.0.0.1` and `::1` are exempt. On Render a real visitor never looks like
this, because Render always fills in `X-Forwarded-For`; loopback means the
request came from inside the machine. Without this, `tests/test_chat.py` would
fail: it sends 13 questions in well under a minute, more than the public
per-minute limit, and 13 tests would fail for the wrong reason. The exemption
gives an outsider nothing that faking any other address did not already give
them, and the whole-service gate still counts those requests.

## What the visitor sees (AC-9)

The server answers 429 with a `Retry-After` header and a plain-language
message, and the widget shows the server's own wording rather than a generic
line:

| Situation | Message |
|---|---|
| Too fast | "Too many questions too quickly. Please wait 23 seconds and try again." |
| Visitor's day spent | "You have reached this demo's daily limit of 100 questions. Please try again tomorrow." |
| Whole demo's day spent | "This free demo has answered as many questions as it can today. Please try again tomorrow." |
| Form too fast | "Too many form submissions. Please wait 12 seconds and try again." |

`/health` now also reports the limits in force, so what is actually running
can be checked without guessing.

## No new package

Everything uses Python's standard library. `requirements.lock.txt` is
unchanged, so the Docker image and the build are unaffected.

## Tests executed

`pytest tests/test_rate_limit.py -v`, run 25 November 2026 in the build
workspace. Time is passed into each check instead of really waiting, so a
24-hour window is tested instantly and the result is the same every run.

| ID | Check | Result |
|---|---|---|
| RL-01 | Requests below the limit are allowed | **Pass** |
| RL-02 | The one over the limit is refused | **Pass** |
| RL-03 | The refusal says how long to wait, counted from the oldest request | **Pass** |
| RL-04 | Allowed again once the window has passed | **Pass** |
| RL-05 | Visitors are counted separately | **Pass** |
| RL-06 | A refused request is not counted | **Pass** |
| RL-07 | `remaining()` reports without recording | **Pass** |
| RL-08 | Tracked addresses are capped, memory cannot grow without limit | **Pass** |
| RL-09 | `/chat` refuses after the per-minute limit, with a clear message | **Pass** |
| RL-10 | `/chat` refuses after the per-day limit, even when slowly paced | **Pass** |
| RL-11 | The whole-service cap stops a visitor never seen before | **Pass** |
| RL-12 | Form limits are separate from chat limits | **Pass** |
| RL-13 | The visitor is read from the first `X-Forwarded-For` entry | **Pass** |
| RL-14 | Falls back to the direct address when there is no header | **Pass** |
| RL-15 | No address at all does not crash | **Pass** |
| RL-16 | A blank header is ignored | **Pass** |
| RL-17 | `RATE_LIMIT_ENABLED=false` lets everything through | **Pass** |
| RL-18 | A number from the environment replaces the default | **Pass** |
| RL-19 | A nonsense setting falls back to the default | **Pass** |
| RL-20 | Local requests are not limited | **Pass** |
| RL-21 | Local requests do not use up the whole-service cap | **Pass** |
| RL-22 | An outside address is still limited | **Pass** |

**22 passed** in the build workspace (with `tests/test_lead.py`: 56 passed).

### Full suite on the project laptop

`pytest tests -v` with the real backend running, 25 November 2026, 10:39 PKT:

**74 passed in 22.02 s** — 13 chat + 34 lead + 5 lead API + 22 rate limit.

This run also confirmed RL-20 in practice rather than only in isolation: the 13
`test_chat.py` questions were sent to a backend with rate limiting switched on
(the startup banner listed the limits), and all 13 passed. Without the
same-machine exemption the per-minute limit of 10 would have refused the last
three.

### Browser check of the message

A stand-in backend that always answers 429 was put in front of the real
widget, served from a local web server, and driven with Chromium.

| Check | Result |
|---|---|
| The chat shows the server's own wording | **Pass** — "Too many questions too quickly. Please wait 23 seconds and try again." |
| The contact form shows it too | **Pass** — same text above the form, form stays open |

The browser console logs "Failed to load resource: 429" on each refusal. That
is the browser noting the HTTP status, not a fault in the page.

## AC-9 on the live service

Run 25 November 2026, 10:46 PKT, from the live website
(<https://shazil-qureshi.github.io/realestate-chatbot/>) against the live
Render backend, after confirming the deploy carried the new code: `/health`
reported
`"rate_limits":{"enabled":true,"chat_per_minute":10,...}`.

Eleven questions were sent from the page in 3 seconds.

| Check | Result |
|---|---|
| Questions allowed | **10** |
| Questions refused with 429 | **1** |
| Any other status | none |
| The refusal message | **"Too many questions too quickly. Please wait 60 seconds and try again."** |
| A visitor asking through the widget while limited | sees a clear "too many questions" message |

**AC-9: Pass.**

### Two things this test found

**1. `Retry-After` could not be read by the page.** The server sends the
header, but a browser hides every response header from JavaScript unless the
server names it in `Access-Control-Expose-Headers`. `expose_headers=["Retry-After"]`
has been added to the CORS settings. Nothing was broken by this: the widget
reads the message text, not the header. It is only now that the header is
usable at all, for example to show a countdown later. **Not yet verified on the
live service** - that needs the next deploy.

**2. The live website was still serving the old `web/chat.js`.** The new file
is in the repository (commit `c75bf1b`), but GitHub Pages had not republished
it, so the widget showed its older fallback wording - "Too many questions in a
short time. Wait a minute, then try again." - instead of the server's exact
one. Both are clear, so AC-9 still passes, but the improvement is not visible
to visitors until Pages republishes.

## Not yet done

| Item | Why |
|---|---|
| GitHub Pages serving the new `chat.js` | The Actions run needs checking; until then visitors see the older 429 wording |
| `expose_headers=["Retry-After"]` verified live | Needs the next deploy |
| Tuning `RATE_CHAT_TOTAL_PER_DAY` to the real quota | Needs the number from <https://aistudio.google.com/rate-limit> (RATE-01) |

## Files changed

| File | Change |
|---|---|
| `backend/ratelimit.py` | New |
| `backend/main.py` | Imports it; `/chat` and `/lead` check before doing work; `/health` reports the limits; startup banner shows them |
| `web/chat.js` | Shows the server's 429 wording, in the chat and on the form |
| `backend/.env.example` | The new settings, with a note on where to read the real quota |
| `tests/test_rate_limit.py` | New, 22 tests |
