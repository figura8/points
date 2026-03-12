"""Email alert placeholders for future implementation."""

from __future__ import annotations

from typing import Any


def send_email_alert(to_email: str, awards: list[dict[str, Any]]) -> None:
    """Stubbed email sender for new award alerts."""
    # TODO: Add SMTP/provider integration and retry handling.
    print(f"[stub] Would send {len(awards)} alerts to {to_email}")
