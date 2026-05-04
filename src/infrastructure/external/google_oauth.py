"""Google OAuth access token verification via userinfo endpoint."""

from httpx import AsyncClient

from src.core.config import settings
from src.core.exceptions import GoogleOAuthException
from src.schemas.features.auth import GoogleUserInfo


async def verify_google_token(token: str) -> GoogleUserInfo:
    """Verify a Google access token and return user profile."""
    async with AsyncClient() as client:
        resp = await client.get(
            settings.GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {token}"},
        )

    if resp.status_code != 200:
        raise GoogleOAuthException("Invalid Google access token")

    return GoogleUserInfo(**resp.json())
