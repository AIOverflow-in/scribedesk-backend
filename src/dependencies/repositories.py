"""Postgres repository dependencies for FastAPI routes."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.dependencies.db import get_db_session
from src.infrastructure.persistence.postgres.repos.auth_repo import AuthRepository
from src.infrastructure.persistence.postgres.repos.patients_repo import PatientsRepository


async def get_auth_repo(
    session: AsyncSession = Depends(get_db_session),
) -> AuthRepository:
    return AuthRepository(session=session)


async def get_patients_repo(
    session: AsyncSession = Depends(get_db_session),
) -> PatientsRepository:
    return PatientsRepository(session=session)


AuthRepositoryDep = Annotated[AuthRepository, Depends(get_auth_repo)]
PatientsRepositoryDep = Annotated[PatientsRepository, Depends(get_patients_repo)]
