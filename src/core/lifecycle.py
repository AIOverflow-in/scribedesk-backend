"""Application lifecycle — startup initialisation and shutdown cleanup."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.core.config import settings
from src.core.logging import get_logger, setup_logging
from src.core.middleware import RequestContextMiddleware

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: configure logging, register middleware. Shutdown: cleanup."""
    setup_logging()

    logger.info(f"{settings.PROJECT_NAME} starting up...")
    logger.info(f"Environment: {settings.ENVIRONMENT} | Debug: {settings.DEBUG}")

    app.add_middleware(RequestContextMiddleware)

    logger.info("Startup complete. API server ready.")

    yield

    logger.info(f"{settings.PROJECT_NAME} shutdown complete")
