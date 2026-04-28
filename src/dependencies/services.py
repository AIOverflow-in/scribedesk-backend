"""Application service dependencies for FastAPI routes."""

from typing import Annotated

from fastapi import Depends

from src.dependencies.infra import SessionManagerDep
from src.dependencies.repositories import AuthRepositoryDep
from src.infrastructure.persistence.postgres.repos.auth_repo import AuthRepository
from src.infrastructure.persistence.redis.sessions import SessionManager
from src.modules.auth.service import AuthService


async def get_auth_service(
    auth_repo: AuthRepositoryDep,
    session_manager: SessionManagerDep,
) -> AuthService:
    return AuthService(
        auth_repo=auth_repo,
        session_manager=session_manager,
    )


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
