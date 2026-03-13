"""Stubbed United crawler module.

This module intentionally avoids live endpoint calls until verified safely.
"""

from __future__ import annotations


def search_united(origin: str, destination: str, date: str) -> list[dict]:
    """Return mock award data in normalized shape for local development."""
    # TODO: Verify the real United endpoint, auth requirements, and payload manually in browser DevTools.
    return [
        {
            "source": "united",
            "airline": "UA",
            "origin": origin.upper(),
            "destination": destination.upper(),
            "departure_date": date,
            "cabin": "economy",
            "program": "MileagePlus",
            "miles_cost": 12500,
            "taxes_fees": 5.6,
            "seats": 2,
            "currency": "USD",
        },
        {
            "source": "united",
            "airline": "UA",
            "origin": origin.upper(),
            "destination": destination.upper(),
            "departure_date": date,
            "cabin": "business",
            "program": "MileagePlus",
            "miles_cost": 35000,
            "taxes_fees": 5.6,
            "seats": 1,
            "currency": "USD",
        },
    ]
