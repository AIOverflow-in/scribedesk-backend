"""Application service dependencies for FastAPI routes."""

from typing import Annotated

from fastapi import Depends

from src.dependencies.infra import SessionManagerDep
from src.dependencies.repositories import (
    AuthRepositoryDep,
    PatientsRepositoryDep,
    TemplatesRepositoryDep,
    UserRepositoryDep,
)
from src.modules.auth.service import AuthService
from src.modules.patients.service import PatientService
from src.modules.templates.service import TemplateService
from src.modules.users.service import UserService


async def get_auth_service(
    auth_repo: AuthRepositoryDep,
    session_manager: SessionManagerDep,
) -> AuthService:
    return AuthService(
        auth_repo=auth_repo,
        session_manager=session_manager,
    )


async def get_patient_service(
    patients_repo: PatientsRepositoryDep,
) -> PatientService:
    return PatientService(repo=patients_repo)


async def get_template_service(
    templates_repo: TemplatesRepositoryDep,
) -> TemplateService:
    return TemplateService(repo=templates_repo)


async def get_user_service(
    user_repo: UserRepositoryDep,
) -> UserService:
    return UserService(repo=user_repo)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
PatientServiceDep = Annotated[PatientService, Depends(get_patient_service)]
TemplateServiceDep = Annotated[TemplateService, Depends(get_template_service)]
UserServiceDep = Annotated[UserService, Depends(get_user_service)]
