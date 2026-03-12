"""Parser utilities for converting raw crawler payloads to normalized records."""

from __future__ import annotations

from typing import Any


def normalize_cabin(raw_cabin: str | None) -> str:
    """Normalize cabin labels to a small canonical set."""
    if not raw_cabin:
        return "unknown"

    text = raw_cabin.strip().lower()
    if "first" in text:
        return "first"
    if "business" in text or text in {"j", "c"}:
        return "business"
    if "premium" in text:
        return "premium_economy"
    if "economy" in text or text in {"coach", "y"}:
        return "economy"
    return "unknown"


def parse_united_response(raw: Any) -> list[dict[str, Any]]:
    """Defensively parse possibly-changing United response structures."""
    if not isinstance(raw, dict):
        return []

    candidates = raw.get("awards") or raw.get("results") or raw.get("data") or []
    if not isinstance(candidates, list):
        return []

    parsed: list[dict[str, Any]] = []
    for item in candidates:
        if not isinstance(item, dict):
            continue

        origin = str(item.get("origin", "")).upper()
        destination = str(item.get("destination", "")).upper()
        departure_date = str(item.get("departure_date") or item.get("date") or "")
        miles_cost = item.get("miles_cost") or item.get("miles")

        if not (origin and destination and departure_date and miles_cost):
            continue

        parsed.append(
            {
                "source": "united",
                "airline": str(item.get("airline", "UA")),
                "origin": origin,
                "destination": destination,
                "departure_date": departure_date,
                "cabin": normalize_cabin(item.get("cabin")),
                "program": str(item.get("program", "MileagePlus")),
                "miles_cost": int(miles_cost),
                "taxes_fees": float(item.get("taxes_fees", 0)),
                "seats": int(item.get("seats", 1)),
                "currency": str(item.get("currency", "USD")),
            }
        )

    return parsed
