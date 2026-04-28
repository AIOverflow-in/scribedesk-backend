from fastapi import APIRouter, status

from src.infrastructure.persistence.postgres.database import check_db_connection
from src.infrastructure.persistence.redis.client import check_redis_connection

router = APIRouter(tags=["Health"])


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """
    Health check endpoint.

    Verifies connectivity to critical infrastructure (Redis, Database).
    """
    redis_healthy = await check_redis_connection()
    db_healthy = await check_db_connection()

    overall_healthy = redis_healthy and db_healthy

    return {
        "status": "healthy" if overall_healthy else "unhealthy",
        "checks": {
            "redis": "healthy" if redis_healthy else "unhealthy",
            "database": "healthy" if db_healthy else "unhealthy",
        },
    }
