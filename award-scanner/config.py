"""Runtime configuration for the award scanner project."""

from __future__ import annotations
import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    """Application settings loaded from environment variables."""

    database_path: str = os.getenv("DATABASE_PATH", "./data/awards.db")

    cors_origins: list[str] = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000,http://localhost:8000",
    ).split(",")

    routes: list[tuple[str, str]] = [
        ("EWR", "LAX"),
        ("JFK", "LHR"),
        ("BOS", "SFO"),
    ]

    days_ahead: int = int(os.getenv("DAYS_AHEAD", "45"))
    delay_min: int = int(os.getenv("DELAY_MIN", "4"))
    delay_max: int = int(os.getenv("DELAY_MAX", "9"))

    email_from: str = os.getenv("EMAIL_FROM", "")
    email_to: str = os.getenv("EMAIL_TO", "")
    email_password: str = os.getenv("EMAIL_PASSWORD", "")

    united_bearer_token: str = os.getenv("UNITED_BEARER_TOKEN", "")
    united_cookies: str = os.getenv("UNITED_COOKIES", "")

    air_canada_api_key: str = os.getenv("AIR_CANADA_API_KEY", "")
    air_canada_access_token: str = os.getenv("AIR_CANADA_ACCESS_TOKEN", "")
    air_canada_id_token: str = os.getenv("AIR_CANADA_ID_TOKEN", "")
    air_canada_ama_session_token: str = os.getenv("AIR_CANADA_AMA_SESSION_TOKEN", "")
    air_canada_cookies: str = os.getenv("AIR_CANADA_COOKIES", "")
    air_canada_accept_language: str = os.getenv("AIR_CANADA_ACCEPT_LANGUAGE", "it-IT,it;q=0.9,en-GB;q=0.8,en;q=0.7,en-US;q=0.6")
    air_canada_referer: str = os.getenv("AIR_CANADA_REFERER", "https://www.aircanada.com/")
    air_canada_user_agent: str = os.getenv("AIR_CANADA_USER_AGENT", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36")
    air_canada_sec_ch_ua: str = os.getenv("AIR_CANADA_SEC_CH_UA", '"Chromium";v="146", "Not-A.Brand";v="24", "Google Chrome";v="146"')
    air_canada_kpsdk_cd: str = os.getenv("AIR_CANADA_KPSDK_CD", "")
    air_canada_kpsdk_ct: str = os.getenv("AIR_CANADA_KPSDK_CT", "")
    air_canada_kpsdk_v: str = os.getenv("AIR_CANADA_KPSDK_V", "")
    air_canada_ff_card_number: str = os.getenv("AIR_CANADA_FF_CARD_NUMBER", "")

settings = Settings()
