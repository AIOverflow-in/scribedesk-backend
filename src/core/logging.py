"""Logging configuration with JSON and text formatters."""

import datetime as dt
import json
import logging
import sys

from src.core.config import settings
from src.core.context import get_trace_id, get_user_id

# --- Helpers ---

STANDARD_KEYS = {
    "args", "asctime", "created", "exc_info", "exc_text", "filename",
    "funcName", "levelname", "levelno", "lineno", "module", "msecs",
    "message", "msg", "name", "pathname", "process", "processName",
    "relativeCreated", "stack_info", "thread", "threadName", "taskName",
}


# --- Formatters ---

class JSONFormatter(logging.Formatter):
    """Formats logs as flat JSON for production observability."""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "trace_id": get_trace_id(),
            "user_id": get_user_id(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        for key, value in record.__dict__.items():
            if key not in STANDARD_KEYS:
                log_data[key] = value
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_data, default=str)


class TextFormatter(logging.Formatter):
    """Formats logs as readable text for local development."""

    def format(self, record: logging.LogRecord) -> str:
        timestamp = self.formatTime(record, "%H:%M:%S")
        trace_id = get_trace_id() or "system"
        user_id = get_user_id()
        user_part = f"[{user_id}]" if user_id else "[--]"
        log_msg = (
            f"[{timestamp}] {record.levelname:<8} "
            f"[{trace_id[:12]}] "
            f"{user_part} "
            f"[{record.module}:{record.lineno}] "
            f"{record.getMessage()}"
        )
        extras = []
        for key, value in record.__dict__.items():
            if key not in STANDARD_KEYS:
                extras.append(f"{key}={value}")
        if extras:
            log_msg += f" | {' '.join(extras)}"
        if record.exc_info:
            log_msg += f"\n{self.formatException(record.exc_info)}"
        return log_msg


# --- Setup ---

def setup_logging() -> None:
    """Configure root logger with formatter, level, and noise suppression."""
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.WARNING)

    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)

    if settings.LOG_FORMAT.upper() == "JSON":
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(TextFormatter())

    root_logger.addHandler(handler)

    # Application logs
    logging.getLogger("src").setLevel(settings.LOG_LEVEL)

    # Framework logs
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

    # Noisy third-party
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("langchain").setLevel(logging.WARNING)
    logging.getLogger("celery").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Factory to get a configured logger instance."""
    return logging.getLogger(name)
