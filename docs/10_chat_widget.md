# Task 2.2 · Chat Widget

| | |
|---|---|
| **Task** | 2.2 Chat widget connected to `/chat` |
| **Status** | Completed 17 November 2026. End-to-end with the real backend passed (W-20..22). |
| **Files** | `web/chat.js`, `web/chat.css`, `web/index.html`, `web/assets/robot.js`, `web/vendor/` (player, downloaded on the project machine), `backend/main.py` (default CORS origins) |

## Objective

Let a visitor ask questions on the website itself, and see the answer together
with the documents it came from.

## How it works

```
visitor types → chat.js → POST http://127.0.0.1:8000/chat {"message": "..."}
                                       ↓
              answer + sources ← FastAPI backend (Task 1.7)
```

The widget is the same request you sent by hand from `/docs` in Task 1.7, sent
by JavaScript instead of by you.

## Technical concepts

| Term | What it means | Where |
|---|---|---|
| **`fetch`** | The browser's built-in way to call a web address from JavaScript | `send()` in `chat.js` |
| **CORS** | The browser refuses to give a page a reply from another address unless that server lists the page's address as allowed | `ALLOWED_ORIGINS` / `DEFAULT_ORIGINS` in `main.py` |
| **Origin** | Scheme + host + port. `http://localhost:5500` and `http://127.0.0.1:5500` are *different* origins, even though they are the same machine | Why both are now in `DEFAULT_ORIGINS` |
| **Preflight** | Before a JSON `POST` to another origin, the browser first sends an `OPTIONS` request to ask permission | Handled automatically by FastAPI's `CORSMiddleware` |
| **XSS** | Cross-site scripting: getting a page to run code it was never meant to run, usually by smuggling HTML into text it displays | Prevented by never using `innerHTML` |
| **`aria-live`** | Tells screen readers to announce new content in a region | The message log |

## Decisions and why

**Replies are never inserted as HTML.** The model's text is untrusted. It is
produced by a language model from documents and a visitor's question, either of
which could contain markup. `chat.js` builds every element with
`createElement` and `textContent`, and handles only two formats itself:
`**bold**` and `- ` bullet lines. W-09 proves a reply containing
`<img onerror>` and `<script>` is displayed as text and runs nothing.

**Sources are shown.** Under each answer, a collapsed "Sources" list names the
document sections it was built from, with duplicates removed. For a portfolio
reviewer this is the clearest evidence that the answer was retrieved rather
than invented.

**Errors explain what to do.** A visitor sees one of four messages: the server
can't be reached (with the command to start it), the message was rejected (the
backend's own reason), too many requests, or the assistant couldn't answer.
Server internals, such as the exception text in a 503, are never shown.

**The backend address lives in one place.** `API_URL` at the top of
`chat.js`, overridable with `window.BELLA_API_URL`. Stage 3 changes that one
value to the Render address (Hugging Face became paid; see `docs/16_render.md`).

**Suggested questions.** Three buttons in the opening message, because an empty
box makes people guess what the assistant can do.

**Keyboard and screen readers.** Opening the panel moves focus to the input.
Enter sends and Shift+Enter adds a line. Escape closes the panel and returns
focus to the launcher. On phones the panel fills the screen.

## Backend change

`main.py` previously fell back to allowing only `http://localhost:5500` when
`ALLOWED_ORIGINS` was empty. A page opened at `http://127.0.0.1:5500`, the
same machine under another name, would have had every request blocked by the
browser, with only a vague network error on screen. The fallback is now both
addresses (`DEFAULT_ORIGINS`). If `ALLOWED_ORIGINS` in `backend/.env` is set,
that list is used instead, unchanged.

## Testing

### Browser tests against a stand-in backend

Run in Chromium through Playwright. The page was served over HTTP on port 5500.
Requests to `http://127.0.0.1:8000/chat` were intercepted and answered by the
test with realistic replies, including CORS headers, so the browser's real CORS
checks applied. This tests the widget in isolation; it does **not** test the
real backend, which W-20 onward do.

| Test ID | Check | Result |
|---|---|---|
| W-01 | Launcher visible, panel closed on load | Pass |
| W-02 | Panel opens, focus moves to the input | Pass |
| W-03 | Three suggested questions shown | Pass |
| W-04 | Request body is exactly `{"message": "..."}` | Pass |
| W-05 | Bullets and bold rendered (2 bullets, 2 bold codes, 2 paragraphs) | Pass |
| W-06 | No raw `**` left in the displayed text | Pass |
| W-07 | Duplicate sources collapsed (3 received, 2 shown) | Pass |
| W-08 | Suggestions removed after the first question | Pass |
| W-09 | HTML in a reply displayed as text; `<img onerror>` and `<script>` did not run | **Pass** |
| W-10 | 400: the backend's reason is shown | Pass |
| W-11 | 503: generic message shown, exception text not leaked | Pass |
| W-12 | Server down: explains and gives the start command | Pass |
| W-13 | Input usable again after an error | Pass |
| W-14 | Shift+Enter adds a line and does not send | Pass |
| W-15 | A blank message is not sent | Pass |
| W-16 | 1,000-character limit matches the backend | Pass |
| W-17 | Escape closes the panel, focus returns to the launcher | Pass |
| W-18 | Phone (390 × 844): panel fills the screen, no horizontal scroll | Pass |
| W-19 | No JavaScript errors | Pass |

**First run: 17 of 19.** Both failures were faults in the test, not the
widget:

- **W-05** counted every `<li>` in the reply bubble, which included the two
  items in the Sources list, so it found 4 bullets instead of 2. It now counts
  only the answer's own list.
- **W-19** counted the browser's console messages for the 400, 503 and refused
  connection that W-10 to W-12 caused on purpose. It now counts only
  JavaScript errors (`pageerror`).

Recorded because a failing test is evidence about the test as well as about
the code, and "fixed the test until it passed" needs its reason written down.

### End-to-end on the project machine

| Test ID | Check | Result |
|---|---|---|
| WEB-04 | Page served at `http://localhost:5500` | **Pass** |
| W-20 | A real question returns a real answer in the widget | **Pass**: "We have 2 apartments for rent in Islamabad", BRE-R-202 and BRE-R-204, Rawalpindi correctly excluded |
| W-21 | The Sources list names real files under `data/listings/` or `data/faqs/` | **Pass**, but revealed the problem below |
| W-22 | With the backend stopped, the widget shows the "can't be reached" message | **Pass** |

## Known limitations

- **No conversation memory.** Each question is answered on its own. "How much
  is the second one?" after a list will not work. Recorded as a possible
  Stage 4 improvement.
- **Localhost only.** Until Stage 3 the widget works only on the machine
  running the backend.
- **The answer formatter is deliberately minimal.** Only bold and bullets.
  Numbered lists or headings from the model appear as plain lines.

## Robot avatar — added 16 November 2026

The project owner supplied two Lottie animations and asked for the better one
to be used.

### Comparison

Both files were unpacked and inspected. Neither could be *played* in the build
environment (no network access to a player), so the choice rests on the files'
contents, and the visual result is checked on the project machine (W-23).

| | AI Robot Vector Art | Bot Hello Message |
|---|---|---|
| Download size | **4.8 KB** | 18 KB |
| Frame rate | **30 fps** | 100 fps |
| Moving parts | 10 (eyes, face, head, ears, body, hands) | 44 |
| Text drawn into it | **None** | "Hey!!" and "How can I help buddy", as outlined shapes |
| Loops | **Seamlessly**: all 9 animated properties end where they start | Set to play once |
| Works with the light player | **Yes**: no expressions, effects, masks or mattes | Not checked |

**Chosen: AI Robot.** The second file's greeting is drawn, not typed. It can't
be edited, translated or read by a screen reader, it repeats the greeting the
widget already gives in real text, and "buddy" is the wrong register for an
estate agency. Its 100 fps rate also costs more than three times the rendering
work of the robot, on every phone, for as long as the page is open.

### Behaviour

| Where | Behaviour | Why |
|---|---|---|
| Launcher button | Loops | Draws the eye to the one part of the page that talks back |
| Panel header | Still; moves only while an answer is being fetched | Motion that reports something happening, rather than decoration |
| Panel open | Launcher robot paused | It is hidden, so animating it wastes battery |
| Reduced motion requested | Never moves | Respects the visitor's system setting |
| Player missing | Robot hidden, chat unchanged | The avatar is optional; the chat must not depend on it |

The robot is `aria-hidden`. The button's accessible name stays "Ask a
question".

### Files

- `web/assets/robot.js` holds the animation as `window.BELLA_ROBOT`. Stored as
  a script rather than a `.json` file so it loads without `fetch()`, which also
  works when the page is opened directly from disk.
- `web/vendor/lottie_light.min.js` is lottie-web 5.12.2, MIT licence, the
  light build (SVG only, no expressions, which the robot does not need). It is
  **downloaded on the project machine** (see `web/vendor/README.md`) rather than
  loaded from a CDN at run time: no verified integrity hash was available, and
  a local copy keeps the site self-contained for GitHub Pages.

### Licence

The animation's licence has not been verified. It must be confirmed on the
LottieFiles page it was downloaded from before the site is published in
Stage 3.

### Tests

The player is not available in the build environment, so R-03 to R-12 used a
test stand-in that records every call the widget makes. They prove the widget
controls the animation correctly; they do **not** prove how it looks.

| Test ID | Check | Result |
|---|---|---|
| R-01 | Without the player: robot hidden, button reads "Ask a question" | Pass |
| R-02 | Without the player: chat still answers, no JavaScript errors | Pass |
| R-03 | Two animations created, looping, not autoplaying | Pass |
| R-04 | Each copy gets its own animation data | Pass |
| R-05 | On load: launcher plays, header rests on frame 0 | Pass |
| R-06 | Opening the panel pauses the launcher robot | Pass |
| R-07 | Header robot moves while an answer is fetched | Pass |
| R-08 | Header robot rests when the answer arrives | Pass |
| R-09 | Closing the panel resumes the launcher robot | Pass |
| R-10 | Launcher stays compact (56 px tall), no JavaScript errors | Pass |
| R-11 | Reduced motion: `play()` is never called | Pass |
| R-12 | Phone: launcher fits the screen, no horizontal scroll | Pass |
| W-23 | The real robot renders and animates with the real player | **Pass**, see below |

### W-23: the real player — 16 November 2026, 17:38 PKT

`lottie_light.min.js` was downloaded on the project machine (168,236 bytes),
copied back to the build environment, and checked: it identifies itself as
lottie-web **5.12.2** and parses as JavaScript. The page was then run in
Chromium with the real player and the real animation, at 2× pixel density.

| Check | Result |
|---|---|
| Player loads, `lottie.version` = 5.12.2 | Pass |
| Robot drawn into the launcher (22 SVG paths) | Pass |
| Launcher robot changes between 0 s, 0.7 s and 1.5 s, so it is animating, not frozen | Pass |
| Header robot is identical across 0.6 s while idle | Pass |
| Header robot changes while an answer is being fetched | Pass |
| No JavaScript errors | Pass |

Screenshots show a white robot with a dark visor and cyan eyes, centred in its
disc and not cropped, with the head and arms moving between frames.

This is the first test of the robot against the genuine player. R-03 to R-12
proved the widget's *control* of the animation with a stand-in; W-23 proves the
animation itself renders.

## End-to-end run and the Sources fix — 17 November 2026

W-20 to W-22 were run on the project machine with the real backend, the real
page and the real robot. All passed.

### Problem found in W-21

The answer to "Show me apartments for rent in Islamabad" listed BRE-R-202 and
BRE-R-204, which was correct. But "Sources (8)" underneath listed every extract
the search returned, including **BRE-S-104** (for sale) and **BRE-R-305**
(Rawalpindi), which the answer had correctly left out.

The data was accurate, the label wasn't. "Sources" claims the answer was built
from those documents, and a reviewer would read a Rawalpindi listing under an
Islamabad answer as the bot getting it wrong. `TOP_K = 8` made this worse:
retrieving more so the model can filter (RET-01) also means showing more that
it filtered out.

### Fix

`renderSources()` in `web/chat.js` now reads the reference codes in the answer:

| Answer contains | Shown | Label |
|---|---|---|
| Reference codes that match extracts | Only those extracts | **Sources** |
| No reference codes (fees, viewings) | Every extract checked | **Documents checked** |
| Codes that match no extract | Every extract checked | **Documents checked** |

The third row is a safety net. It can't hide the evidence when the model quotes
a code the search didn't return.

### Tests

Run with the eight sources from the project machine's screenshot.

| Test ID | Check | Result |
|---|---|---|
| S-01 | Rental answer shows "Sources (2)": exactly BRE-R-202 and BRE-R-204 | Pass |
| S-02 | No Rawalpindi or for-sale entry among the shown sources | Pass, on the second attempt (see below) |
| S-03 | Answer with no codes: "Documents checked (2)" | Pass |
| S-04 | Code matching no extract: falls back to "Documents checked (3)" | Pass |
| S-05 | No JavaScript errors | Pass |

**S-01 failed on the first run, and S-02 passed for the wrong reason.** Both
read the list with `inner_text()`, which returns only *visible* text, and the
Sources list starts collapsed. S-01 therefore saw two empty strings. S-02 found
no Rawalpindi entry because it could read no entries at all. It would have
passed on the old, broken widget too.

Re-run with `text_content()`, which reads text whether or not it is displayed:
`['BRE-R-202 — …', 'BRE-R-204 — …']`. Both now pass on real evidence.

A test that can't see its subject passes for the wrong reason. A check that
something is absent proves nothing unless the test can be shown to see what's
present.
