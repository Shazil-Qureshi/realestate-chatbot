# AI Real Estate Customer Support Chatbot

An AI chatbot for a fictional real estate company. It answers customer questions
from the company's own documents (RAG), shows its sources, says "I don't know"
when the documents don't cover a question, and captures leads into Google Sheets
through n8n.

> Status: in development. This is a portfolio demo. The company and all of its
> data are fictional.

## Tech stack

Python, FastAPI, Google Gemini API, ChromaDB, HTML/CSS/JavaScript, n8n,
Google Sheets, Docker, Hugging Face Spaces, GitHub Pages.

## Run it on your own computer (Windows)

You need Python 3.14, Node.js 24 (only for n8n), a free Gemini API key from
Google AI Studio, and four PowerShell windows. Full details are in
[`docs/04_environment_setup.md`](docs/04_environment_setup.md).

**Once, to set up:**

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r backend\requirements.txt
copy backend\.env.example backend\.env     # then put your own key in backend\.env
python backend\test_gemini.py              # lists the models your key can use
python backend\ingest.py                   # reads data\ and builds the search index
```

`backend\.env` holds your key. It is listed in `.gitignore`. Never commit it
or show it on screen.

**Every time.** One window each, all from the project folder:

| Window | Command | Check it worked |
|---|---|---|
| 1 Backend | `.venv\Scripts\activate` then `python backend\main.py` | Banner, then `Uvicorn running on http://127.0.0.1:8000` |
| 2 Website | `python -m http.server 5500 --directory web` | <http://localhost:5500> opens |
| 3 n8n (optional) | `npx n8n` | <http://localhost:5678> opens. Setup: [`n8n/README.md`](n8n/README.md) |
| 4 Tests | `.venv\Scripts\activate` then `pytest tests -v` | All pass |

Without n8n the chatbot still works, and leads are saved to
`backend\leads\pending.jsonl`.

## Live demo

The backend runs on Render's free tier (see [`docs/16_render.md`](docs/16_render.md)).
It sleeps after 15 minutes without visitors, so the first answer after a quiet
spell can take about a minute.

On the live demo, the contact form checks a visitor's details and then
discards them (`LEADS_DEMO_MODE=true`). The full lead flow to Google Sheets
and email runs with n8n on the developer's laptop.

## Documentation

See the [`docs/`](docs/) folder, starting with
[`01_project_overview.md`](docs/01_project_overview.md) and the
[`PROJECT_TRACKER.md`](PROJECT_TRACKER.md) and [`DAILY_PROGRESS.md`](DAILY_PROGRESS.md).

## Author

Qazi Shazil Qureshi

## Important: the embedding model is locked in

`GEMINI_EMBEDDING_MODEL` in `backend/.env` must not change once documents have
been ingested. Google's embedding models use incompatible embedding spaces, so
a chunk stored by one model cannot be searched using another.

To change it: delete `backend/chroma_db/`, update `.env`, and run
`python backend/ingest.py` again.

The chat model (`GEMINI_CHAT_MODEL`) has no such restriction and can be swapped
at any time.
