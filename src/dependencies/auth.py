from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from redis.asyncio import Redis

from src.dependencies.db import get_redis
from src.infrastructure.persistence.redis.sessions import SessionManager


async def get_current_user_id(
    request: Request,
    redis: Redis = Depends(get_redis),
) -> str:
    """
    Reads the session cookie and resolves the authenticated user ID.

    Raises 401 if the cookie is missing or the session is expired/invalid.
    """
    token = request.cookies.get("session")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    manager = SessionManager(redis)
    session = await manager.get_session(token)

    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session",
        )

    request.state.user_id = session["user_id"]
    return session["user_id"]


CurrentUserIdDep = Annotated[str, Depends(get_current_user_id)]
