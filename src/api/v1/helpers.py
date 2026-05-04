from fastapi import Response

from src.core.config import settings
from src.schemas.api.auth import AuthResponse


def handle_auth_result(
    response: Response,
    token: str,
    onboarding_pending: bool = False,
) -> AuthResponse:
    is_prod = settings.ENVIRONMENT == "production"
    response.set_cookie(
        key="session",
        value=token,
        httponly=True,
        samesite="none" if is_prod else "lax",
        secure=is_prod,
        max_age=settings.SESSION_EXPIRY_SECONDS,
    )
    return AuthResponse(
        session_token=token,
        onboarding_pending=onboarding_pending,
    )
