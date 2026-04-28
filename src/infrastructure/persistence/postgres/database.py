from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine

from src.core.config import settings
from src.core.logging import get_logger

logger = get_logger(__name__)


engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

# Create session factory
async_session_maker = async_sessionmaker(
    engine,
    expire_on_commit=False,
)


async def check_db_connection() -> bool:
    """
    Verify database connectivity.

    Returns True if connection is successful, False otherwise.
    """
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database connection check failed: {e}")
        return False


async def close_db_connections() -> None:
    """Close all database connections."""
    await engine.dispose()
    logger.info("Database connections closed")