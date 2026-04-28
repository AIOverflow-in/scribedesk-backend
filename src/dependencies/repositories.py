"""Postgres repository dependencies for FastAPI routes."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.dependencies.db import get_db_session
from src.infrastructure.persistence.postgres.repos.auth_repo import AuthRepository


async def get_auth_repo(
    session: AsyncSession = Depends(get_db_session),
) -> AuthRepository:
    return AuthRepository(session=session)


AuthRepositoryDep = Annotated[AuthRepository, Depends(get_auth_repo)]
