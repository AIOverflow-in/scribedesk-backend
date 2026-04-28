from datetime import datetime, date, timezone
from typing import Optional


def format_current_date(fmt: str = "%B %d, %Y") -> str:
    """
    Returns current date in specified format.
    Default: "January 15, 2026"
    """
    return datetime.now(timezone.utc).strftime(fmt)


def unix_to_dt(unix_timestamp: int) -> datetime:
    """Converts Unix timestamp (e.g., 1730000000) to UTC datetime."""
    return datetime.fromtimestamp(unix_timestamp, tz=timezone.utc)


def to_date(dt: Optional[datetime]) -> Optional[date]:
    """
    Extracts the date part from a datetime.
    Useful for converting DB datetime values to date for API responses.
    """
    return dt.date() if dt else None


def calculate_age(birth_date: Optional[date]) -> Optional[int]:
    """
    Calculates age from date of birth.
    Returns None if birth_date is None.
    """
    if not birth_date:
        return None
    today = date.today()
    return today.year - birth_date.year - (
        (today.month, today.day) < (birth_date.month, birth_date.day)
    )
