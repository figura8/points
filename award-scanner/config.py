"""Runtime configuration for the award scanner project."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    """Application settings loaded from environment variables."""

    database_path: str = os.getenv("DATABASE_PATH", "./data/awards.db")
    cors_origins: list[str] = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000,http://localhost:8000",
    ).split(",")


settings = Settings()
