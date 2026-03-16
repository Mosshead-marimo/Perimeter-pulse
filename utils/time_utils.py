"""
Time Utilities
Provides standardized time handling for logs and analysis
"""

from datetime import datetime, time


BUSINESS_START = time(9, 0)
BUSINESS_END = time(18, 0)


def parse_iso(timestamp: str) -> datetime | None:
    """
    Safely parse ISO-8601 timestamp
    """
    try:
        return datetime.fromisoformat(timestamp)
    except Exception:
        return None


def is_off_hours(dt: datetime) -> bool:
    """
    Check if a timestamp falls outside business hours
    """
    if not dt:
        return False
    return dt.time() < BUSINESS_START or dt.time() > BUSINESS_END


def current_utc() -> str:
    """
    Returns current UTC time in ISO format
    """
    return datetime.utcnow().isoformat()
