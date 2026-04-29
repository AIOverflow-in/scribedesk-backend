from typing import Annotated, Optional

from fastapi import Depends, HTTPException, Query, Request, status
from fastapi.exceptions import WebSocketException as FastAPIWebSocketException
from redis.asyncio import Redis

from src.dependencies.db import get_redis
from src.dependencies.infra import get_session_manager
from src.infrastructure.persistence.redis.sessions import SessionManager


# --- HTTP auth (cookie-based) ---

async def get_current_user_id(
    request: Request,
    redis: Redis = Depends(get_redis),
) -> str:
    """Reads the session cookie and resolves the authenticated user ID."""
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


# --- WebSocket auth (token via query param) ---

async def get_ws_current_user_id(
    token: str = Query(...),
    session_manager: SessionManager = Depends(get_session_manager),
) -> str:
    """
    Authenticate a WebSocket connection via ``?token=``.

    Raises ``WebSocketException`` (code 4001) if invalid or expired.
    """
    session = await session_manager.get_session(token)
    if not session:
        raise FastAPIWebSocketException(
            code=status.WS_1008_POLICY_VIOLATION,
            reason="Invalid or expired session",
        )
    return session["user_id"]


WsCurrentUserIdDep = Annotated[str, Depends(get_ws_current_user_id)]
