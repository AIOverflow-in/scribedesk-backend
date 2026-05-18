"""Application lifecycle — startup initialisation and shutdown cleanup."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.core.config import settings
from src.core.logging import get_logger, setup_logging
from src.infrastructure.persistence.postgres.database import check_db_connection, close_db_connections
from src.infrastructure.persistence.redis.client import get_redis_client, init_redis, close_redis
from src.infrastructure.persistence.redis.pubsub import PubSubManager

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run startup initialisation before yielding, then shutdown cleanup after."""
    setup_logging()
    logger.info("%s starting up...  Environment: %s  Debug: %s",
                settings.PROJECT_NAME, settings.ENVIRONMENT, settings.DEBUG)

    await _init_redis()
    pubsub_manager = await _start_pubsub_listener()
    if pubsub_manager is not None:
        app.state.pubsub_manager = pubsub_manager
    await _check_database()

    logger.info("Startup complete. API server ready.")
    yield
    await _shutdown(app)


# ---------------------------------------------------------------------------
# Startup steps
# ---------------------------------------------------------------------------

async def _init_redis() -> None:
    try:
        await init_redis()
        logger.info("Redis connection established")
    except Exception as exc:
        logger.critical("FATAL: Redis initialization failed: %s", exc)


async def _start_pubsub_listener() -> PubSubManager | None:
    try:
        manager = PubSubManager(get_redis_client())
        await manager.start()
        logger.info("PubSub listener started — 1 Redis connection serves all SSE clients")
        return manager
    except Exception as exc:
        logger.critical("FATAL: PubSub listener failed to start: %s", exc)
        raise


async def _check_database() -> None:
    try:
        if await check_db_connection():
            logger.info("Database connection established")
        else:
            logger.critical("FATAL: Database connection failed. The application cannot persist data.")
    except Exception as exc:
        logger.critical("FATAL: Database connection check failed: %s", exc)


# ---------------------------------------------------------------------------
# Shutdown steps
# ---------------------------------------------------------------------------

async def _shutdown(app: FastAPI) -> None:
    logger.info("Shutting down...")

    pubsub_manager: PubSubManager | None = getattr(app.state, "pubsub_manager", None)

    steps = [
        ("Database connections", close_db_connections()),
        ("PubSub listener", pubsub_manager.stop() if pubsub_manager else None),
        ("Redis connection", close_redis()),
    ]

    for label, coroutine in steps:
        if coroutine is None:
            continue
        try:
            await coroutine
            logger.info("%s closed", label)
        except Exception as exc:
            logger.error("Error closing %s: %s", label, exc)

    logger.info("%s shutdown complete", settings.PROJECT_NAME)
