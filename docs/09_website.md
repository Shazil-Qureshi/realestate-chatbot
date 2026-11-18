# Task 2.1 · Landing Page

| | |
|---|---|
| **Task** | 2.1 Landing page |
| **Status** | Completed 16 Nov 2026. Accessibility review added the same day (WEB-06..10). WEB-04 runs on the project machine when the page is first served in Task 2.2. |
| **Files** | `web/index.html`, `web/style.css` |

## Objective

A public face for Bella Real Estate: the page a visitor lands on, and the page
the chat widget (Task 2.2) will live on. Everything shown must come from the
same documents the chatbot answers from, so the website and the chatbot can
never contradict each other.

## Technical concepts

| Term | What it means | Where it shows up |
|---|---|---|
| **Static site** | Pages that are just files — no server-side code runs to produce them | The whole `web/` folder; it is why GitHub Pages can host it free |
| **HTML** | The content and structure of a page | `index.html` |
| **CSS** | The appearance: colours, spacing, layout | `style.css` |
| **Semantic tags** | `<header>`, `<section>`, `<article>`, `<footer>` instead of anonymous boxes | Screen readers and search engines read the structure |
| **Responsive layout** | One page that re-arranges itself for any screen width | `auto-fill, minmax(...)` grids; cards stack to one column on a phone |
| **Viewport meta tag** | Tells a phone not to pretend to be a desktop | Line 5 of `index.html` |
| **CSS variables** | Named values defined once (`--green-700`) and reused | The whole colour scheme is 8 lines at the top of `style.css` |
| **Sticky header** | The navigation stays visible while scrolling | `position: sticky` |

## Decisions and why

**Every figure is copied from `data/`.** The six featured cards, the fees, the
addresses, the phone numbers and the opening hours were extracted from the
Markdown files programmatically, then every string on the page was checked
against the data files again after writing. The website and the chatbot share
one source of truth. If a price changes, it changes in `data/`, and both the
page and the knowledge base (after re-ingestion) follow.

**No property photos, on purpose.** The properties are fictional. A stock
photo would be a picture of a real house pretending to be BRE-S-103, which
crosses the line from "fictional demo" into fabrication. The cards use styled
colour panels instead — green for sale, blue for rent — with the reference
code where a photo would be.

**The fictional-company notice appears twice.** A banner at the very top and a
full paragraph in the footer. `data/company_info/01` requires it, and a
portfolio project shown to employers should be unmistakably honest about what
it is.

**No frameworks, no external fonts, no CDN links.** The page is two files that
work offline. That keeps the Stage 3 GitHub Pages deployment to "upload the
folder", with nothing to break when a third-party URL changes.

**A comment marks where the chat widget goes** (`<!-- The chat widget is added
here in Task 2.2 -->`), so the next task has an explicit seam.

## How to view it

Double-clicking `web/index.html` works for this task — the page makes no
backend calls yet. But from Task 2.2 onward it must be **served**, because the
backend only accepts browser requests from `http://localhost:5500` (the CORS
list in `backend/.env`). A `file://` page has no origin the backend can allow.

So the habit starts now. From the project folder, in any terminal:

```powershell
python -m http.server 5500 --directory web
```

Then open <http://localhost:5500>. Stop it with `Ctrl+C`. This is Python's
built-in file server — nothing to install, and it is why the number 5500 has
been sitting in `.env.example` since Task 0.1.

## Testing procedure and results

| Test ID | Objective | Method | Result |
|---|---|---|---|
| WEB-01 | Page renders completely | Loaded in a real (headless Chromium) browser, full-page screenshot reviewed | **Pass** — banner, header, hero, 6 cards, fees, areas, offices, footer all present |
| WEB-02 | Every figure matches `data/` | Script checked 18 property strings + 8 company facts against the page **and** the data files | **Pass** — 26 of 26 traced |
| WEB-03 | Fictional notice visible | Screenshot review | **Pass** — top banner and footer paragraph |
| WEB-04 | Serves at `http://localhost:5500` | Run the command above on the project machine | Pending — first needed in Task 2.2 |
| WEB-05 | Usable at phone width | Rendered at 375 px; measured horizontal overflow | **Pass** — 0 px overflow, cards stack to one column |

WEB-01, 02, 03 and 05 were executed in this working session on the exact files
delivered to the project machine; the screenshots reviewed are of the real
rendered page, not a mock-up.

## Known limitations

- Six of 17 listings are shown. The page says so, and points visitors at the
  assistant for the rest — which is the point of the project.
- The nav links are same-page anchors; there are no other pages. A real agency
  site would have per-property pages. Out of scope (see `docs/02`).
- Contact details are display-only. Lead capture is Task 2.3/2.4, through the
  chat widget — not a separate form.

## Accessibility review — 16 November 2026, 16:55 PKT

A second pass, after the page was written, against the accessibility floor and
a full re-check of the figures. Run in Chromium through Playwright at 1280 px
and 390 px.

### Figures re-checked

All 27 numbers on the six property cards (prices, bedrooms, bathrooms, sizes,
the 6 kW solar array, the 2022 build year), plus phone numbers, addresses,
hours and the "6 of our 17 listings" claim, compared against `data/` again.
0 mismatches. WEB-02 holds.

### Failures found and fixed

| Test ID | Check | Before | After |
|---|---|---|---|
| WEB-06 | Price text contrast on white, minimum 4.5 : 1 | **Fail**, 2.42 : 1 | **Pass**, 4.61 : 1 |
| WEB-07 | Visible keyboard focus | **Fail**, none | **Pass**, gold outline, keyboard only |
| WEB-08 | First Tab reaches a skip link that jumps to `#main` | **Fail**, absent | **Pass** |
| WEB-09 | `<main>` landmark present | **Fail**, absent | **Pass** |
| WEB-10 | No console errors, no phone overflow after the changes | — | **Pass** |

WEB-06 is the one that mattered most. The prices used gold `#c9a227` on white
cards, which made the most important text on the page the hardest to read. A
new `--gold-700: #8d721b` keeps the same hue, darkened until it reached
4.61 : 1, and is used for `.price` and `.fee-amount`. The original gold stays
in the dark hero, where it already measured 5.38 : 1.

A `prefers-reduced-motion` rule was added ahead of Task 2.2, whose widget will
open and close.

### Deliberately not changed

**Phone numbers are not tap-to-call links.** `051-111-2222` follows the format
of real Pakistani UAN numbers. A `tel:` link on a public demo could connect a
visitor to a real business that has nothing to do with this project.
