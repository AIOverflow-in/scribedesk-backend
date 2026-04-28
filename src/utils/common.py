from datetime import datetime
from typing import Any


def serialize_for_json(value: Any) -> Any:
    """
    Safely serialize values for JSON logging.

    Handles datetime objects and objects with __dict__ attribute.
    """
    if isinstance(value, datetime):
        iso = value.isoformat()
        return iso.replace("+00:00", "Z").replace("-00:00", "Z")
    if hasattr(value, "__dict__"):
        return str(value)
    return value
