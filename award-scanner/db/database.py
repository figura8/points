"""Database helpers for SQLite-backed award storage."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Generator

from config import settings

SCHEMA_PATH = Path(__file__).with_name("schema.sql")


def _utc_now() -> str:
    """Return current UTC timestamp in ISO format."""
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def get_db() -> Generator[sqlite3.Connection, None, None]:
    """Yield a SQLite connection with row dict-like access."""
    conn = sqlite3.connect(settings.database_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    """Initialize SQLite schema from schema.sql."""
    Path(settings.database_path).parent.mkdir(parents=True, exist_ok=True)
    with get_db() as conn:
        conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))


def upsert_awards(records: list[dict[str, Any]]) -> int:
    """Insert or refresh award rows and return number of processed records."""
    if not records:
        return 0

    now = _utc_now()
    sql = """
    INSERT INTO awards (
        source, airline, origin, destination, departure_date, cabin,
        program, miles_cost, taxes_fees, seats, currency,
        last_seen_at, created_at, is_active
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
    ON CONFLICT(source, airline, origin, destination, departure_date, cabin, program, miles_cost, taxes_fees)
    DO UPDATE SET
        seats = excluded.seats,
        currency = excluded.currency,
        last_seen_at = excluded.last_seen_at,
        is_active = 1
    """

    values = [
        (
            row["source"],
            row["airline"],
            row["origin"],
            row["destination"],
            row["departure_date"],
            row["cabin"],
            row["program"],
            int(row["miles_cost"]),
            float(row.get("taxes_fees", 0)),
            int(row.get("seats", 1)),
            row.get("currency", "USD"),
            now,
            now,
        )
        for row in records
    ]

    with get_db() as conn:
        conn.executemany(sql, values)
    return len(records)


def mark_inactive(source: str, origin: str, destination: str, departure_date: str) -> int:
    """Mark route-date awards as inactive before a fresh crawl."""
    with get_db() as conn:
        cur = conn.execute(
            """
            UPDATE awards
            SET is_active = 0
            WHERE source = ? AND origin = ? AND destination = ? AND departure_date = ?
            """,
            (source, origin, destination, departure_date),
        )
        return cur.rowcount


def search_availability(
    origin: str | None = None,
    destination: str | None = None,
    departure_date: str | None = None,
    cabin: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """Search active award availability with optional filters."""
    query = ["SELECT * FROM awards WHERE is_active = 1"]
    params: list[Any] = []

    if origin:
        query.append("AND origin = ?")
        params.append(origin.upper())
    if destination:
        query.append("AND destination = ?")
        params.append(destination.upper())
    if departure_date:
        query.append("AND departure_date = ?")
        params.append(departure_date)
    if cabin:
        query.append("AND cabin = ?")
        params.append(cabin.lower())

    query.append("ORDER BY departure_date ASC, miles_cost ASC")
    query.append("LIMIT ?")
    params.append(max(1, min(limit, 1000)))

    with get_db() as conn:
        rows = conn.execute(" ".join(query), params).fetchall()
    return [dict(row) for row in rows]


def get_new_awards(since_iso: str, limit: int = 100) -> list[dict[str, Any]]:
    """Return active awards first seen after a given timestamp."""
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT * FROM awards
            WHERE is_active = 1 AND created_at >= ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (since_iso, max(1, min(limit, 1000))),
        ).fetchall()
    return [dict(row) for row in rows]
