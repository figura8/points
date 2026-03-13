"""
United MileagePlus award search crawler.

IMPORTANT: The bearer token and cookies expire with each session.
To refresh them:
1. Go to united.com and search for an award flight
2. Open DevTools → Network → Fetch/XHR → click FetchFlights
3. Right-click → Copy as cURL
4. Update BEARER_TOKEN and COOKIES in your .env file
"""

import httpx
import random
import time
import json
import logging
from datetime import datetime
from config import settings

logger = logging.getLogger(__name__)

# --- Constants ---

URL = "https://www.united.com/api/flight/FetchFlights"

def _get_headers() -> dict:
    """Build request headers using token from settings/env."""
    return {
        "accept": "application/json",
        "accept-language": "en-IT",
        "content-type": "application/json",
        "origin": "https://www.united.com",
        "referer": "https://www.united.com/en/it/fsr/choose-flights",
        "sec-ch-ua": '"Not:A-Brand";v="99", "Google Chrome";v="145", "Chromium";v="145"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/145.0.0.0 Safari/537.36"
        ),
        "x-authorization-api": f"bearer {settings.united_bearer_token}",
    }

def _build_payload(origin: str, destination: str, date: str) -> dict:
    """
    Build the POST payload for a one-way award search.
    Date format: 'YYYY/MM/DD'
    """
    return {
        "SearchTypeSelection": 1,
        "SortType": "bestmatches",
        "SortTypeDescending": False,
        "Trips": [
            {
                "Origin": origin,
                "Destination": destination,
                "DepartDate": date,
                "Index": 1,
                "TripIndex": 1,
                "SearchRadiusMilesOrigin": "-1",
                "SearchRadiusMilesDestination": "-1",
                "DepartTimeApprox": 0,
                "UseFilters": False,
            }
        ],
        "CabinPreferenceMain": "economy",
        "PaxInfoList": [{"PaxType": 1}],
        "AwardTravel": True,
        "NGRP": True,
        "FareType": "mixedtoggle",
    }

def search_united(origin: str, destination: str, date: str) -> list[dict]:
    """
    Search United MileagePlus award availability.

    Args:
        origin: IATA code e.g. 'EWR'
        destination: IATA code e.g. 'LAX'
        date: departure date in 'YYYY-MM-DD' format

    Returns:
        List of normalized award dicts, empty list on failure.
    """
    # Convert date format from YYYY-MM-DD to YYYY/MM/DD
    formatted_date = date.replace("-", "/")

    payload = _build_payload(origin, destination, formatted_date)

    cookies = {}
    if settings.united_cookies:
        # Parse "key=value; key2=value2" cookie string
        for part in settings.united_cookies.split(";"):
            part = part.strip()
            if "=" in part:
                k, v = part.split("=", 1)
                cookies[k.strip()] = v.strip()

    try:
        with httpx.Client(timeout=30, cookies=cookies) as client:
            response = client.post(
                URL,
                headers=_get_headers(),
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        awards = parse_united_response(data, origin, destination, date)
        logger.info(f"{origin}→{destination} {date}: {len(awards)} awards found")

        # Polite delay
        time.sleep(random.uniform(settings.delay_min, settings.delay_max))
        return awards

    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP {e.response.status_code} for {origin}→{destination} {date}")
        if e.response.status_code == 401:
            logger.error("Bearer token expired — update UNITED_BEARER_TOKEN in .env")
        return []

    except Exception as e:
        logger.error(f"Error searching {origin}→{destination} {date}: {e}")
        return []


def parse_united_response(
    data: dict, origin: str, destination: str, date: str
) -> list[dict]:
    """
    Parse raw FetchFlights JSON into normalized award records.
    Defensive: returns [] if structure is unexpected.
    """
    results = []

    try:
        trips = data.get("data", {}).get("Trips", [])
        if not trips:
            return []

        for trip in trips:
            for flight in trip.get("Flights", []):
                carrier = flight.get("MarketingCarrier", "UA")

                for product in flight.get("Products", []):
                    miles_raw = product.get("MilesDisplayAmount", "")
                    if not miles_raw:
                        continue

                    try:
                        miles = int(str(miles_raw).replace(",", ""))
                    except ValueError:
                        continue

                    cabin = _normalize_cabin(
                        product.get("BookingCode", "")
                        or product.get("Description", "")
                    )

                    results.append({
                        "origin": origin,
                        "destination": destination,
                        "departure_date": date,
                        "cabin": cabin,
                        "airline": carrier,
                        "miles_cost": miles,
                        "seats_available": product.get("SeatsRemaining"),
                        "taxes_cash_usd": product.get("TaxAmount"),
                        "source_program": "united",
                    })

    except Exception as e:
        logger.error(f"Error parsing United response: {e}")

    return results


def _normalize_cabin(code: str) -> str:
    """Map booking code or description to standard cabin name."""
    code = code.upper()
    if any(x in code for x in ["FIRST", "F", "A"]):
        return "first"
    if any(x in code for x in ["BUSINESS", "J", "C", "D", "Z", "P"]):
        return "business"
    if any(x in code for x in ["PREMIUM", "W", "PE"]):
        return "premium_economy"
    return "economy"

