from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from src.core.logging import get_logger

logger = get_logger(__name__)


# --- Custom Exception Classes ---

class AppException(Exception):
    """Base exception for application-specific errors."""

    def __init__(
        self,
        message: str,
        code: str = "APP_ERROR",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class NotFoundException(AppException):
    """Resource not found."""

    def __init__(self, message: str = "Resource not found", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, code="NOT_FOUND", status_code=status.HTTP_404_NOT_FOUND, details=details)


class BadRequestException(AppException):
    """Bad request — invalid input or business logic violation."""

    def __init__(self, message: str = "Bad request", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, code="BAD_REQUEST", status_code=status.HTTP_400_BAD_REQUEST, details=details)


class UnauthorizedException(AppException):
    """Unauthorized — authentication required."""

    def __init__(self, message: str = "Unauthorized", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, code="UNAUTHORIZED", status_code=status.HTTP_401_UNAUTHORIZED, details=details)


class ForbiddenException(AppException):
    """Forbidden — insufficient permissions."""

    def __init__(self, message: str = "Forbidden", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, code="FORBIDDEN", status_code=status.HTTP_403_FORBIDDEN, details=details)


class ConflictException(AppException):
    """Conflict — resource already exists or state conflict."""

    def __init__(self, message: str = "Conflict", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, code="CONFLICT", status_code=status.HTTP_409_CONFLICT, details=details)


class RateLimitException(AppException):
    """Rate limit exceeded."""

    def __init__(self, message: str = "Rate limit exceeded", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, code="RATE_LIMIT_EXCEEDED", status_code=status.HTTP_429_TOO_MANY_REQUESTS, details=details)


class UsageLimitException(AppException):
    """Usage quota exceeded — user needs to upgrade plan."""

    def __init__(self, message: str = "Usage limit exceeded", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, code="USAGE_LIMIT_EXCEEDED", status_code=status.HTTP_403_FORBIDDEN, details=details)


class GoogleOAuthException(AppException):
    """Google OAuth token verification failed."""

    def __init__(self, message: str = "Google authentication failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, code="GOOGLE_OAUTH_ERROR", status_code=status.HTTP_401_UNAUTHORIZED, details=details)


# --- Exception Handlers ---

async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle FastAPI request validation errors (422)."""
    errors = exc.errors()
    logger.warning(
        f"Validation error: {request.method} {request.url.path}",
        extra={"validation_errors": errors, "error_count": len(errors), "body": exc.body if hasattr(exc, "body") else None},
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"code": "VALIDATION_ERROR", "message": "Request validation failed", "errors": errors},
    )


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Handle application-specific exceptions with structured error response."""
    logger.error(
        f"Application error: {request.method} {request.url.path}",
        extra={"error_code": exc.code, "error_message": exc.message, "error_details": exc.details},
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.code, "message": exc.message, "details": exc.details if exc.details else None},
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all for unhandled exceptions. Returns 500 without exposing internals."""
    logger.error(
        f"Unhandled exception: {request.method} {request.url.path}",
        extra={"error_type": type(exc).__name__, "error_message": str(exc)},
        exc_info=True,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"code": "INTERNAL_SERVER_ERROR", "message": "An unexpected error occurred. Please try again later."},
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle FastAPI HTTPExceptions with consistent format."""
    logger.warning(
        f"HTTP exception: {request.method} {request.url.path}",
        extra={"status_code": exc.status_code, "detail": exc.detail},
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": "HTTP_ERROR", "message": exc.detail},
    )


def setup_exception_handlers(app: "FastAPI") -> None:
    """Register all exception handlers on the FastAPI app."""

    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
