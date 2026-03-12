"""Queue helpers for crawl job generation and state transitions."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from db.database import get_db


def _today_iso() -> str:
    """Return today's date in ISO format."""
    return date.today().isoformat()


def generate_queue(routes: list[tuple[str, str]], days_ahead: int = 7, source: str = "united") -> int:
    """Create pending jobs for route/date combinations."""
    if days_ahead < 1:
        return 0

    rows: list[tuple[str, str, str, str, str, str]] = []
    today = date.today()
    for origin, destination in routes:
        for offset in range(days_ahead):
            dep = (today + timedelta(days=offset)).isoformat()
            now = _today_iso()
            rows.append((source, origin.upper(), destination.upper(), dep, now, now))

    with get_db() as conn:
        conn.executemany(
            """
            INSERT OR IGNORE INTO crawl_jobs (
                source, origin, destination, departure_date, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
        return conn.total_changes


def get_next_jobs(limit: int = 10) -> list[dict[str, Any]]:
    """Get pending jobs ordered by soonest departure date."""
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT * FROM crawl_jobs
            WHERE status = 'pending'
            ORDER BY departure_date ASC, id ASC
            LIMIT ?
            """,
            (max(1, min(limit, 100)),),
        ).fetchall()
    return [dict(row) for row in rows]


def mark_job_running(job_id: int) -> None:
    """Mark a queued job as running."""
    with get_db() as conn:
        conn.execute(
            """
            UPDATE crawl_jobs
            SET status = 'running', attempts = attempts + 1, started_at = ?, updated_at = ?
            WHERE id = ?
            """,
            (_today_iso(), _today_iso(), job_id),
        )


def mark_job_done(job_id: int) -> None:
    """Mark a running job as completed."""
    with get_db() as conn:
        conn.execute(
            """
            UPDATE crawl_jobs
            SET status = 'done', finished_at = ?, error_message = NULL, updated_at = ?
            WHERE id = ?
            """,
            (_today_iso(), _today_iso(), job_id),
        )


def mark_job_failed(job_id: int, error_message: str) -> None:
    """Mark a job failed and store an error message."""
    with get_db() as conn:
        conn.execute(
            """
            UPDATE crawl_jobs
            SET status = 'failed', finished_at = ?, error_message = ?, updated_at = ?
            WHERE id = ?
            """,
            (_today_iso(), error_message[:500], _today_iso(), job_id),
        )
