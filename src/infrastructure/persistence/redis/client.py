"""Global Redis client — connection pool lifecycle."""

from typing import Optional

import redis.asyncio as aioredis

from src.core.config import settings
from src.core.logging import get_logger

logger = get_logger(__name__)

_redis_client: Optional[aioredis.Redis] = None


async def init_redis() -> None:
    """Initialize the Redis connection pool. Call once at startup."""
    global _redis_client

    if _redis_client is not None:
        return

    try:
        _redis_client = await aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            max_connections=50,
        )
        await _redis_client.ping()
        logger.info("Connected to Redis")
    except Exception as e:
        logger.error(f"Failed to initialize Redis: {e}")
        raise


def get_redis_client() -> aioredis.Redis:
    """Get the global Redis client instance. Raises RuntimeError if not initialised."""
    global _redis_client
    if _redis_client is None:
        raise RuntimeError("Redis not initialised. Call init_redis() first.")
    return _redis_client


async def check_redis_connection() -> bool:
    """Verify Redis connectivity. Returns True if reachable."""
    try:
        client = get_redis_client()
        await client.ping()
        return True
    except Exception as e:
        logger.error(f"Redis connection check failed: {e}")
        return False


async def close_redis() -> None:
    """Close the Redis connection pool."""
    global _redis_client
    if _redis_client is not None:
        await _redis_client.aclose()
        _redis_client = None
        logger.info("Redis connection closed")
