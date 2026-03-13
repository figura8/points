"""Air Canada Aeroplan award search crawler (experimental)."""

from __future__ import annotations

import json
import logging
import random
import time
from datetime import datetime
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from config import settings

logger = logging.getLogger(__name__)

URL = "https://akamai-gw.dbaas.aircanada.com/loyalty/dapidynamicplus/1ASIUDALAC/v2/search/air-bounds"


def _iso_date_start(date_yyyy_mm_dd: str) -> str:
    """Convert YYYY-MM-DD to API datetime format used by Air Canada payload."""
    return f"{date_yyyy_mm_dd}T00:00:00.000"


def _build_headers() -> dict[str, str]:
    """Build request headers from .env values copied from a working browser session."""
    headers = {
        "accept": "application/json",
        "accept-language": settings.air_canada_accept_language,
        "content-type": "application/json",
        "origin": "https://www.aircanada.com",
        "referer": settings.air_canada_referer,
        "sec-ch-ua": settings.air_canada_sec_ch_ua,
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "user-agent": settings.air_canada_user_agent,
        "x-api-key": settings.air_canada_api_key,
        "authorization": f"Bearer {settings.air_canada_access_token}",
        "x-custom-id-token": settings.air_canada_id_token,
        "ama-session-token": settings.air_canada_ama_session_token,
    }

    if settings.air_canada_kpsdk_cd:
        headers["x-kpsdk-cd"] = settings.air_canada_kpsdk_cd
    if settings.air_canada_kpsdk_ct:
        headers["x-kpsdk-ct"] = settings.air_canada_kpsdk_ct
    if settings.air_canada_kpsdk_v:
        headers["x-kpsdk-v"] = settings.air_canada_kpsdk_v
    if settings.air_canada_cookies:
        headers["cookie"] = settings.air_canada_cookies

    return headers


def _build_payload(origin: str, destination: str, date_yyyy_mm_dd: str) -> dict:
    """Build Air Canada reward-search payload using one-way ADT defaults."""
    return {
        "searchPreferences": {"showSoldOut": False, "showMilesPrice": True},
        "corporateCodes": ["REWARD"],
        "travelers": [{"passengerTypeCode": "ADT"}],
        "currencyCode": "CAD",
        "itineraries": [
            {
                "originLocationCode": origin.upper(),
                "destinationLocationCode": destination.upper(),
                "departureDateTime": _iso_date_start(date_yyyy_mm_dd),
                "isRequestedBound": True,
                "commercialFareFamilies": ["REWARD"],
            }
        ],
        "frequentFlyer": {
            "cardNumber": settings.air_canada_ff_card_number,
            "companyCode": "AC",
            "priorityCode": "9",
        },
    }


def search_air_canada(origin: str, destination: str, date: str) -> list[dict]:
    """Search Air Canada Aeroplan award availability."""
    payload = _build_payload(origin, destination, date)
    body = json.dumps(payload).encode("utf-8")

    req = Request(
        URL,
        data=body,
        headers=_build_headers(),
        method="POST",
    )

    try:
        with urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))

        awards = parse_air_canada_response(data, origin, destination, date)
        logger.info("%s→%s %s: %s awards found", origin, destination, date, len(awards))
        time.sleep(random.uniform(settings.delay_min, settings.delay_max))
        return awards

    except HTTPError as e:
        body_text = ""
        try:
            body_text = e.read().decode("utf-8", errors="ignore")
        except Exception:
            body_text = ""

        logger.error("HTTP %s for AC %s→%s %s", e.code, origin, destination, date)
        logger.error("Air Canada response body: %s", body_text[:1500])
        return []

    except URLError as e:
        logger.error("Network error searching AC %s→%s %s: %s", origin, destination, date, e)
        return []

    except Exception as e:
        logger.error("Error searching AC %s→%s %s: %s", origin, destination, date, e)
        return []


def _normalize_cabin(text: str) -> str:
    """Normalize cabin text to our canonical labels."""
    up = (text or "").upper()
    if "FIRST" in up:
        return "first"
    if "BUSINESS" in up:
        return "business"
    if "PREMIUM" in up:
        return "premium_economy"
    return "economy"


def _extract_offers(raw: dict) -> list[dict]:
    """Extract a flat list of offer-like dicts from varying API response shapes."""
    candidates: list[dict] = []

    for key in ("bounds", "itineraries", "offers", "results", "data"):
        block = raw.get(key)
        if isinstance(block, list):
            for item in block:
                if isinstance(item, dict):
                    if isinstance(item.get("offers"), list):
                        candidates.extend([x for x in item["offers"] if isinstance(x, dict)])
                    elif isinstance(item.get("flights"), list):
                        candidates.extend([x for x in item["flights"] if isinstance(x, dict)])
                    else:
                        candidates.append(item)
        elif isinstance(block, dict):
            if isinstance(block.get("offers"), list):
                candidates.extend([x for x in block["offers"] if isinstance(x, dict)])

    if not candidates and isinstance(raw, dict):
        candidates = [raw]

    return candidates


def parse_air_canada_response(data: dict, origin: str, destination: str, date: str) -> list[dict]:
    """Parse Air Canada API response into DB-ready award records."""
    if not isinstance(data, dict):
        return []

    rows: list[dict] = []
    offers = _extract_offers(data)

    for offer in offers:
        miles = (
            offer.get("miles")
            or offer.get("points")
            or offer.get("milesCost")
            or offer.get("miles_cost")
            or offer.get("amountMiles")
        )
        if miles in (None, ""):
            continue

        try:
            miles_cost = int(str(miles).replace(",", ""))
        except ValueError:
            continue

        taxes = (
            offer.get("taxes")
            or offer.get("taxesAndFees")
            or offer.get("taxes_fees")
            or offer.get("totalTaxes")
            or 0
        )

        cabin_text = (
            str(offer.get("cabin") or offer.get("cabinClass") or offer.get("fareFamily") or "economy")
        )

        seats = offer.get("seats") or offer.get("seatsAvailable") or offer.get("availability") or 1
        try:
            seats_val = int(seats)
        except (TypeError, ValueError):
            seats_val = 1

        rows.append(
            {
                "source": "air_canada",
                "airline": "AC",
                "origin": origin.upper(),
                "destination": destination.upper(),
                "departure_date": date,
                "cabin": _normalize_cabin(cabin_text),
                "program": "Aeroplan",
                "miles_cost": miles_cost,
                "taxes_fees": float(taxes) if taxes not in (None, "") else 0.0,
                "seats": seats_val,
                "currency": "CAD",
            }
        )

    logger.debug("AC parser extracted %s rows at %s", len(rows), datetime.utcnow().isoformat())
    return rows
