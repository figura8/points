"""FastAPI app exposing basic award availability endpoints."""

from __future__ import annotations

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from db.database import init_db, search_availability
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Award Scanner API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    """Ensure database schema exists when API starts."""
    init_db()


@app.get("/health")
def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/awards")
def get_awards(
    origin: str | None = Query(default=None, min_length=3, max_length=3),
    destination: str | None = Query(default=None, min_length=3, max_length=3),
    departure_date: str | None = None,
    cabin: str | None = None,
    limit: int = Query(default=100, ge=1, le=1000),
) -> list[dict]:
    """Search active awards with optional filters."""
    return search_availability(origin, destination, departure_date, cabin, limit)


@app.get("/routes")
def get_routes() -> list[dict[str, str]]:
    """Return distinct active routes currently in the database."""
    awards = search_availability(limit=1000)
    unique = {(row["origin"], row["destination"]) for row in awards}
    return [{"origin": origin, "destination": destination} for origin, destination in sorted(unique)]

# alla fine del file, dopo tutti gli endpoint:
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
