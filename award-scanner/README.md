# Award Scanner (Minimal Scaffold)

A deliberately minimal award flight scanner scaffold inspired by tools like Seats.aero.

This version focuses on:
- A working SQLite database layer
- A working FastAPI backend
- A basic crawl queue model
- Safe mock data (no fragile live scraping)

## Current status

- ✅ DB schema and DB helper methods are implemented.
- ✅ Queue generation and job status helpers are implemented.
- ✅ FastAPI endpoints are implemented (`/health`, `/awards`, `/routes`).
- ⚠️ Live scraping is **not** implemented yet.
- ⚠️ Scheduler, email alerts, and frontend are intentionally minimal.

## Folder structure

```text
award-scanner/
├── requirements.txt
├── config.py
├── .env.example
├── .gitignore
├── db/
│   ├── __init__.py
│   ├── schema.sql
│   └── database.py
├── crawler/
│   ├── __init__.py
│   ├── united.py
│   ├── parser.py
│   └── queue.py
├── api/
│   ├── __init__.py
│   └── main.py
├── alerts/
│   ├── __init__.py
│   └── email_alert.py
├── frontend/
│   └── index.html
├── scheduler.py
└── data/
    └── .gitkeep
```

## Installation

```bash
cd award-scanner
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## Initialize the database

Option A (quick one-liner):
```bash
python -c "from db.database import init_db; init_db(); print('DB initialized')"
```

Option B (implicitly on API startup):
- Starting the API runs `init_db()` automatically.

## Run the FastAPI server

```bash
uvicorn api.main:app --reload
```

Then visit:
- `http://localhost:8000/health`
- `http://localhost:8000/awards`
- `http://localhost:8000/routes`

## Notes on live scraping

`crawler/united.py` currently returns mock normalized award rows.

It intentionally does **not** include guessed airline internal endpoints.
When you are ready to add live crawling, verify endpoint URLs, payloads, and headers manually in browser DevTools first.

## Air Canada quick test

If you want to test Aeroplan/AC instead of United:

1. Add `AIR_CANADA_*` values to `.env` (copy from a working browser cURL).
2. Run:

```bash
python seed_air_canada.py
```

The script will fetch AC award rows and upsert them into the same SQLite DB.
