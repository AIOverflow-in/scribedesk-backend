"""Application service dependencies for FastAPI routes."""

from typing import Annotated

from fastapi import Depends

from src.dependencies.infra import SessionManagerDep
from src.dependencies.repositories import AuthRepositoryDep, PatientsRepositoryDep
from src.modules.auth.service import AuthService
from src.modules.patients.service import PatientService


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


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
PatientServiceDep = Annotated[PatientService, Depends(get_patient_service)]
