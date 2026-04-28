"""Context variables for request-scoped data (trace ID, user ID)."""

from contextvars import ContextVar
from typing import Optional

request_id_ctx: ContextVar[str] = ContextVar("request_id", default="")
user_id_ctx: ContextVar[Optional[str]] = ContextVar("user_id", default=None)


# --- Trace ID ---

def get_trace_id() -> str:
    """Get the current request's trace ID."""
    return request_id_ctx.get("system")


def set_trace_id(trace_id: str) -> None:
    """Set the trace ID for the current request context."""
    request_id_ctx.set(trace_id)


# --- User ID ---

def get_user_id() -> Optional[str]:
    """Get the current authenticated user ID (if set)."""
    return user_id_ctx.get()


def set_user_id(user_id: Optional[str]) -> None:
    """Set the user ID for the current request context."""
    user_id_ctx.set(user_id)
