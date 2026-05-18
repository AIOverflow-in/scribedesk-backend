"""External infrastructure dependencies for FastAPI routes."""

from typing import Annotated

from fastapi import Depends, Request
from redis.asyncio import Redis

from src.dependencies.db import get_redis
from src.infrastructure.external.deepgram import DeepgramClient
from src.infrastructure.persistence.redis.pubsub import PubSubManager
from src.infrastructure.persistence.redis.sessions import SessionManager

_deepgram_client: DeepgramClient | None = None


def get_session_manager(
    redis: Redis = Depends(get_redis),
) -> SessionManager:
    return SessionManager(redis_client=redis)


def get_pubsub_manager(
    request: Request,
) -> PubSubManager:
    return request.app.state.pubsub_manager


def get_deepgram_client() -> DeepgramClient:
    global _deepgram_client
    if _deepgram_client is None:
        _deepgram_client = DeepgramClient()
    return _deepgram_client


SessionManagerDep = Annotated[SessionManager, Depends(get_session_manager)]
PubSubManagerDep = Annotated[PubSubManager, Depends(get_pubsub_manager)]
DeepgramClientDep = Annotated[DeepgramClient, Depends(get_deepgram_client)]
