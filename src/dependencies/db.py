from typing import AsyncGenerator

import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.persistence.postgres.database import async_session_maker
from src.infrastructure.persistence.redis.client import get_redis_client


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency for Postgres database session.
    Automatically handles commit/rollback and cleanup.
    """
    async with async_session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_redis() -> AsyncGenerator[aioredis.Redis, None]:
    """
    FastAPI dependency for Redis client.
    """
    redis_client = get_redis_client()
    yield redis_client