"""Application service dependencies for FastAPI routes."""

from typing import Annotated

from fastapi import Depends

from src.dependencies.ai import FastLLMDep, TinyLLMDep
from src.dependencies.infra import SessionManagerDep
from src.dependencies.repositories import (
    AuthRepositoryDep,
    PatientsRepositoryDep,
    ReportsRepositoryDep,
    SessionsRepositoryDep,
    TemplatesRepositoryDep,
    UserRepositoryDep,
)
from src.modules.auth.service import AuthService
from src.modules.patients.service import PatientService
from src.modules.reports.service import ReportService
from src.modules.sessions.service import SessionService
from src.modules.templates.service import TemplateService
from src.modules.users.service import UserService


async def get_auth_service(
    auth_repo: AuthRepositoryDep,
    session_manager: SessionManagerDep,
) -> AuthService:
    return AuthService(auth_repo=auth_repo, session_manager=session_manager)


async def get_patient_service(patients_repo: PatientsRepositoryDep) -> PatientService:
    return PatientService(repo=patients_repo)


async def get_session_service(
    sessions_repo: SessionsRepositoryDep,
    tiny_llm: TinyLLMDep,
    fast_llm: FastLLMDep,
) -> SessionService:
    return SessionService(repo=sessions_repo, tiny_llm=tiny_llm, fast_llm=fast_llm)


async def get_template_service(templates_repo: TemplatesRepositoryDep) -> TemplateService:
    return TemplateService(repo=templates_repo)


async def get_user_service(user_repo: UserRepositoryDep) -> UserService:
    return UserService(repo=user_repo)


async def get_report_service(
    reports_repo: ReportsRepositoryDep,
    sessions_repo: SessionsRepositoryDep,
    templates_repo: TemplatesRepositoryDep,
    user_repo: UserRepositoryDep,
    fast_llm: FastLLMDep,
) -> ReportService:
    return ReportService(
        reports_repo=reports_repo,
        sessions_repo=sessions_repo,
        templates_repo=templates_repo,
        user_repo=user_repo,
        fast_llm=fast_llm,
    )


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
PatientServiceDep = Annotated[PatientService, Depends(get_patient_service)]
SessionServiceDep = Annotated[SessionService, Depends(get_session_service)]
TemplateServiceDep = Annotated[TemplateService, Depends(get_template_service)]
UserServiceDep = Annotated[UserService, Depends(get_user_service)]
ReportServiceDep = Annotated[ReportService, Depends(get_report_service)]
