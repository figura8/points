"""
United MileagePlus award search crawler.

IMPORTANT: The bearer token and cookies expire with each session.
To refresh them:
1. Go to united.com and search for an award flight
2. Open DevTools → Network → Fetch/XHR → click FetchFlights
3. Right-click → Copy as cURL
4. Update BEARER_TOKEN and COOKIES in your .env file
"""

from __future__ import annotations

import json
import logging
import random
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from config import settings

logger = logging.getLogger(__name__)

URL = "https://www.united.com/api/flight/FetchFlights"


def _build_referer(origin: str, destination: str, date_yyyy_mm_dd: str) -> str:
    """Build a route/date-aware referer similar to browser traffic."""
    query = urlencode(
        {
            "f": origin.upper(),
            "t": destination.upper(),
            "d": date_yyyy_mm_dd,
            "tt": 1,
            "at": 1,
            "sc": 7,
            "px": 1,
            "taxng": 1,
            "newHP": "True",
            "clm": 7,
            "st": "bestmatches",
            "tqp": "A",
        }
    )
    return f"https://www.united.com/en/it/fsr/choose-flights?{query}"


def _get_headers(origin: str, destination: str, date_yyyy_mm_dd: str) -> dict[str, str]:
    """Build request headers using token from settings/env."""
    headers = {
        "accept": "application/json",
        "accept-language": "en-IT",
        "content-type": "application/json",
        "origin": "https://www.united.com",
        "referer": _build_referer(origin, destination, date_yyyy_mm_dd),
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
    if settings.united_cookies:
        headers["cookie"] = settings.united_cookies
    return headers


def _build_payload(origin: str, destination: str, date_yyyy_mm_dd: str) -> dict:
    """Build POST payload close to the browser request shape."""
    year, month, day = date_yyyy_mm_dd.split("-")
    recent_search_key = f"{origin.upper()}{destination.upper()}{int(month)}/{int(day)}/{year}"

    return {
        "SearchTypeSelection": 1,
        "SortType": "bestmatches",
        "SortTypeDescending": False,
        "Trips": [
            {
                "Origin": origin.upper(),
                "Destination": destination.upper(),
                "DepartDate": date_yyyy_mm_dd,
                "Index": 1,
                "TripIndex": 1,
                "SearchRadiusMilesOrigin": 0,
                "SearchRadiusMilesDestination": 0,
                "DepartTimeApprox": 0,
                "SearchFiltersIn": {
                    "FareFamily": "ECONOMY",
                    "AirportsStop": None,
                    "AirportsStopToAvoid": None,
                    "ShopIndicators": {"IsTravelCreditsApplied": False},
                    "StopCountMax": None,
                    "StopCountMin": 1,
                },
                "UseFilters": True,
                "NonStopMarket": True,
            }
        ],
        "CabinPreferenceMain": "economy",
        "PaxInfoList": [{"PaxType": 1}],
        "AwardTravel": True,
        "NGRP": True,
        "CalendarLengthOfStay": 0,
        "PetCount": 0,
        "RecentSearchKey": recent_search_key,
        "CalendarFilters": {"Filters": {"PriceScheduleOptions": {"Stops": 1}}},
        "Characteristics": [
            {"Code": "SOFT_LOGGED_IN", "Value": False},
            {"Code": "UsePassedCartId", "Value": False},
        ],
        "FareType": "mixedtoggle",
        "BuildHashValue": "true",
        "CartId": "",
    }


def search_united(origin: str, destination: str, date: str) -> list[dict]:
    """Search United MileagePlus award availability."""
    payload = _build_payload(origin, destination, date)
    body = json.dumps(payload).encode("utf-8")
    req = Request(
        URL,
        data=body,
        headers=_get_headers(origin, destination, date),
        method="POST",
    )

    try:
        with urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))

        awards = parse_united_response(data, origin, destination, date)
        logger.info("%s→%s %s: %s awards found", origin, destination, date, len(awards))
        time.sleep(random.uniform(settings.delay_min, settings.delay_max))
        return awards

    except HTTPError as e:
        body_text = ""
        try:
            body_text = e.read().decode("utf-8", errors="ignore")
        except Exception:
            body_text = ""

        logger.error("HTTP %s for %s→%s %s", e.code, origin, destination, date)
        logger.error("United response body: %s", body_text[:1500])
        if e.code == 401:
            logger.error("Bearer token expired — update UNITED_BEARER_TOKEN in .env")
        return []

    except URLError as e:
        logger.error("Network error searching %s→%s %s: %s", origin, destination, date, e)
        return []

    except Exception as e:
        logger.error("Error searching %s→%s %s: %s", origin, destination, date, e)
        return []


def parse_united_response(data: dict, origin: str, destination: str, date: str) -> list[dict]:
    """Parse raw FetchFlights JSON into normalized DB-ready award records."""
    results: list[dict] = []

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

                    taxes = product.get("TaxAmount")
                    seats = product.get("SeatsRemaining")

                    results.append(
                        {
                            "source": "united",
                            "airline": carrier,
                            "origin": origin.upper(),
                            "destination": destination.upper(),
                            "departure_date": date,
                            "cabin": _normalize_cabin(
                                product.get("BookingCode", "")
                                or product.get("Description", "")
                            ),
                            "program": "MileagePlus",
                            "miles_cost": miles,
                            "taxes_fees": float(taxes) if taxes not in (None, "") else 0.0,
                            "seats": int(seats) if isinstance(seats, (int, str)) and str(seats).isdigit() else 1,
                            "currency": "USD",
                        }
                    )

    except Exception as e:
        logger.error("Error parsing United response: %s", e)

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
