# 17 · Website on GitHub Pages

| | |
|---|---|
| **Task** | 3.4 Publish the website and point the widget at the live backend |
| **Date** | 25 November 2026 |
| **Requirements** | FR-15 (public live demo), AC-6 |
| **Status** | **Completed** 25 Nov. Live at <https://shazil-qureshi.github.io/realestate-chatbot/>, calling the Render backend. AC-6 is half checked: laptop Pass, phone still to do. |

## Terms

| Term | What it is |
|---|---|
| **GitHub Pages** | Free website hosting that serves files straight from a GitHub repository. It serves static files only: HTML, CSS, JavaScript and images. It cannot run Python, which is why the backend lives on Render. |
| **GitHub Actions** | GitHub's built-in automation. A **workflow** is a YAML file in `.github/workflows/` that GitHub runs when something happens, for example a push to `main`. |
| **Artifact** | A bundle of files one workflow step hands to the next. Here the `web` folder is packed into an artifact and the deploy step publishes it. |
| **Origin** | Scheme + host, for example `https://shazil-qureshi.github.io`. A browser treats two different origins as two different sites. |
| **CORS** | The browser rule that a page may not read a reply from another origin unless that server lists the page's origin as allowed. |

## Why a workflow was needed

The simple setting (Pages → *Deploy from a branch*) can publish only the
repository root or a folder named `docs/`. Our website is in `web/`, and `docs/`
already holds this documentation. Renaming either would break other things.

A workflow solves it: it takes the `web` folder and publishes **that** as the
site root, so `web/index.html` becomes the home page and `web/chat.js` stays at
`chat.js` next to it. No file had to move.

## The workflow

`.github/workflows/pages.yml`:

```yaml
name: Publish website to GitHub Pages

on:
  push:
    branches: [main]
    paths: ["web/**", ".github/workflows/pages.yml"]
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: pages
  cancel-in-progress: false

jobs:
  publish:
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deploy.outputs.page_url }}
    steps:
      - uses: actions/checkout@v7
      - uses: actions/configure-pages@v6
      - uses: actions/upload-pages-artifact@v5
        with:
          path: web
      - id: deploy
        uses: actions/deploy-pages@v5
```

Line by line:

| Part | What it does |
|---|---|
| `paths:` | The site is rebuilt only when something in `web/` or the workflow itself changes. A backend-only commit does not trigger a pointless rebuild. |
| `workflow_dispatch` | Adds a **Run workflow** button, so the site can be republished by hand without a commit. |
| `permissions` | The least the job needs: read the code, write Pages, and prove its identity to the Pages service. |
| `concurrency` | Two pushes close together cannot publish on top of each other. `cancel-in-progress: false` lets a running publish finish. |
| `path: web` | The part that makes `web/` the site root. |

The action versions were checked against the live repositories on 24 November
2026 (`checkout` v7, `configure-pages` v6, `upload-pages-artifact` v5,
`deploy-pages` v5) rather than copied from memory.

## The one change to the website

The widget used to always call `http://127.0.0.1:8000`. It now switches by
hostname, added to `web/index.html` just before `chat.js`:

```html
<script>
  // On GitHub Pages there is no local backend, so use the Render one.
  // Anywhere else (a laptop, a local web server) keeps the local
  // backend on port 8000.
  if (location.hostname.endsWith("github.io")) {
    window.BELLA_API_URL = "https://realestate-chatbot-4707.onrender.com";
  }
</script>
```

`chat.js` already read `window.BELLA_API_URL` if it was set, so nothing else
changed. Local development is untouched: on `localhost` the condition is false
and the widget still talks to the local backend.

## CORS

The Render service already had `ALLOWED_ORIGINS` set to

```
https://shazil-qureshi.github.io,http://localhost:5500,http://127.0.0.1:5500
```

so the browser accepted the replies and no change was needed. This was checked
on the Render dashboard, and confirmed in use: the live chat worked and the
browser console logged no CORS error.

A trap worth remembering: Render refuses a second environment variable with the
same key ("Duplicate key … is not allowed"). An existing variable has to be
edited, not added again.

## Tests executed

Run on 25 November 2026, about 10:20–10:25 PKT, in Chrome on the project
laptop, driven from the live public URL. The backend was already awake.

| ID | Check | Result |
|---|---|---|
| PAGE-01 | The public URL loads | **Pass** — title "Bella Real Estate — Islamabad & Rawalpindi" |
| PAGE-02 | The fictional-company banner is shown | **Pass** — "Demo website — Bella Real Estate is a fictional company created for a software demonstration. No real property is offered." |
| PAGE-03 | Page assets load from the published site | **Pass** — `vendor/lottie_light.min.js`, `assets/robot.js`, `chat.js` |
| PAGE-04 | The widget points at Render | **Pass** — `window.BELLA_API_URL` is `https://realestate-chatbot-4707.onrender.com` |
| PAGE-05 | The chat panel opens | **Pass** — greeting, three suggestion chips, "Talk to a person", Send |
| PAGE-06 | A real question is answered from the documents | **Pass** — "What are your fees for buying a property?" → 1 percent buyer commission, 3–5 percent combined extra costs; "Documents checked (8)" |
| PAGE-07 | Off-topic question declined (AC-2 regression) | **Pass** — "Do you sell cars?" → "I can only help with questions about Bella Real Estate, property, or renting and buying homes." |
| PAGE-08 | "Talk to a person" shows the demo notice | **Pass** — "it checks your details, then throws them away. Nothing is stored or sent." with **Try the form** / **Not now** |
| PAGE-09 | A lead is validated and discarded (demo mode) | **Pass** — fictional lead (Zara Mahmood, 0300 1234567, `zara.mahmood@example.com`, BRE-R-202) → "Your details passed every check, and have now been discarded: this live demo keeps nothing." |
| PAGE-10 | No browser errors | **Pass** — page reloaded with console capture on, one question asked: no errors, no CORS message |

Answers came back in about 2 seconds, well inside NFR-01's 10 seconds. That is
with the service already awake; a first request after 15 minutes of sleep takes
up to about a minute, which the widget covers with its "Waking up…" message
(tested in 3.3).

## Acceptance criteria

| ID | Criterion | Result |
|---|---|---|
| AC-6 | The live demo answers questions from a public URL on both a laptop and a phone | **Half done.** Laptop: Pass (above). Phone: **not yet run.** |
| FR-15 | Public live demo | **Pass** — website and backend both public |

AC-6 stays open until the site is opened on a real phone. The 375 px checks in
2.5 were done in a desktop browser shrunk to phone size, which is not the same
as a phone.

## Problems met

| Problem | Fix |
|---|---|
| Pages could not serve `web/` with the simple branch setting | Published with an Actions workflow instead |
| `.github/workflows/pages.yml` could not be written to the laptop by the assistant's remote file tools — that path is protected | Created through the GitHub website ("Add file → Create new file"), then `git pull` on the laptop |
| Adding `ALLOWED_ORIGINS` on Render failed with "Duplicate key" | It already existed and was already correct; the duplicate row was cancelled |

## Open items after 3.4

| ID | Item |
|---|---|
| AC-6 | Open the live site on a phone and ask one question |
| 3.5 | Rate limiting still to do. The CORS half of 3.5 is already in place and now verified in use. |
| RET-04, LEAD-R1, N8N-S1, RATE-01 | Unchanged |
