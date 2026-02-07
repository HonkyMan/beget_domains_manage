"""Helper utilities."""

from datetime import datetime


def format_datetime(dt: datetime) -> str:
    """Format datetime for display."""
    return dt.strftime("%d.%m.%Y %H:%M:%S")


def truncate(text: str, max_length: int = 50) -> str:
    """Truncate text to max length."""
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."
