"""Request tracing, context injection, timing, and error logging."""

import time
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from src.core.context import request_id_ctx
from src.core.logging import get_logger

logger = get_logger(__name__)


# --- Middleware ---

class RequestContextMiddleware(BaseHTTPMiddleware):
    """
    Attaches a trace ID to every request, injects response headers,
    and logs completion with timing and user context.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.perf_counter()

        trace_id = uuid.uuid4().hex
        token = request_id_ctx.set(trace_id)

        try:
            response = await call_next(request)

            duration = (time.perf_counter() - start_time) * 1000

            response.headers["X-Trace-ID"] = trace_id
            response.headers["X-Process-Time"] = f"{duration:.2f}"

            user_id = getattr(request.state, "user_id", None)
            logger.info(
                "Request finished",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": round(duration, 2),
                    "client": request.client.host if request.client else None,
                    "user_id": user_id,
                },
            )
            return response

        except Exception as e:
            duration = (time.perf_counter() - start_time) * 1000
            user_id = getattr(request.state, "user_id", None)
            logger.error(
                "Request failed",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": round(duration, 2),
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "user_id": user_id,
                },
                exc_info=True,
            )
            raise

        finally:
            request_id_ctx.reset(token)
