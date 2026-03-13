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

settings = Settings()
