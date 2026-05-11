"""Postgres repository dependencies for FastAPI routes."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.dependencies.db import get_db_session
from src.infrastructure.persistence.postgres.repos.ai_conversations_repo import AIConversationsRepository
from src.infrastructure.persistence.postgres.repos.auth_repo import AuthRepository
from src.infrastructure.persistence.postgres.repos.patients_repo import PatientsRepository
from src.infrastructure.persistence.postgres.repos.reports_repo import ReportsRepository
from src.infrastructure.persistence.postgres.repos.sessions_repo import SessionsRepository
from src.infrastructure.persistence.postgres.repos.templates_repo import TemplatesRepository
from src.infrastructure.persistence.postgres.repos.user_repo import UserRepository


async def get_auth_repo(session: AsyncSession = Depends(get_db_session)) -> AuthRepository:
    return AuthRepository(session=session)


async def get_patients_repo(session: AsyncSession = Depends(get_db_session)) -> PatientsRepository:
    return PatientsRepository(session=session)


async def get_sessions_repo(session: AsyncSession = Depends(get_db_session)) -> SessionsRepository:
    return SessionsRepository(session=session)


async def get_templates_repo(session: AsyncSession = Depends(get_db_session)) -> TemplatesRepository:
    return TemplatesRepository(session=session)


async def get_user_repo(session: AsyncSession = Depends(get_db_session)) -> UserRepository:
    return UserRepository(session=session)


async def get_reports_repo(session: AsyncSession = Depends(get_db_session)) -> ReportsRepository:
    return ReportsRepository(session=session)


async def get_ai_conversations_repo(session: AsyncSession = Depends(get_db_session)) -> AIConversationsRepository:
    return AIConversationsRepository(session=session)


AuthRepositoryDep = Annotated[AuthRepository, Depends(get_auth_repo)]
PatientsRepositoryDep = Annotated[PatientsRepository, Depends(get_patients_repo)]
SessionsRepositoryDep = Annotated[SessionsRepository, Depends(get_sessions_repo)]
TemplatesRepositoryDep = Annotated[TemplatesRepository, Depends(get_templates_repo)]
UserRepositoryDep = Annotated[UserRepository, Depends(get_user_repo)]
ReportsRepositoryDep = Annotated[ReportsRepository, Depends(get_reports_repo)]
AIConversationsRepositoryDep = Annotated[AIConversationsRepository, Depends(get_ai_conversations_repo)]
