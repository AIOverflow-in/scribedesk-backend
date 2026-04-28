"""Application lifecycle — startup initialisation and shutdown cleanup."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.core.config import settings
from src.core.logging import get_logger, setup_logging
from src.core.middleware import RequestContextMiddleware
from src.infrastructure.persistence.postgres.database import check_db_connection, close_db_connections
from src.infrastructure.persistence.redis.client import init_redis, close_redis

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: init Redis + DB, register middleware. Shutdown: close connections."""

    # --- Startup ---
    setup_logging()

    logger.info(f"{settings.PROJECT_NAME} starting up...")
    logger.info(f"Environment: {settings.ENVIRONMENT} | Debug: {settings.DEBUG}")

    # Init Redis (sessions, caching)
    try:
        await init_redis()
        logger.info("Redis connection established")
    except Exception as e:
        logger.critical(f"FATAL: Redis initialization failed: {e}")

    # Check database connection
    try:
        if await check_db_connection():
            logger.info("Database connection established")
        else:
            logger.critical("FATAL: Database connection failed. The application cannot persist data.")
    except Exception as e:
        logger.critical(f"FATAL: Database connection check failed: {e}")

    app.add_middleware(RequestContextMiddleware)

    logger.info("Startup complete. API server ready.")

    yield

    # --- Shutdown ---
    logger.info("Shutting down...")

    try:
        await close_db_connections()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database connections: {e}")

    try:
        await close_redis()
        logger.info("Redis connection closed")
    except Exception as e:
        logger.error(f"Error closing Redis connection: {e}")

    logger.info(f"{settings.PROJECT_NAME} shutdown complete")
