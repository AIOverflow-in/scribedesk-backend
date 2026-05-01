"""Patient CRUD routes."""

from typing import Literal, Optional
from uuid import UUID
from fastapi import APIRouter, Query

from src.dependencies.auth import CurrentUserIdDep
from src.dependencies.services import PatientServiceDep
from src.schemas.api.common import PaginatedResponse, StatusResponse
from src.schemas.api.patients import (
    CreatePatientRequest,
    PatientResponse,
    UpdatePatientRequest,
)

router = APIRouter()


@router.get("/patients", response_model=PaginatedResponse[PatientResponse])
async def list_patients(
    user_id: CurrentUserIdDep,
    service: PatientServiceDep,
    page: int = 1,
    page_size: int = 20,
    search: Optional[str] = Query(None, description="Search by name or email"),
    sort_by: Literal["created_at", "name", "email"] = Query("created_at"),
    sort_order: Literal["asc", "desc"] = Query("desc"),
):
    """List patients with pagination, search, and sorting."""
    items, total = await service.list(
        user_id=user_id,
        page=page,
        page_size=page_size,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    return PaginatedResponse(
        items=[PatientResponse.model_validate(p) for p in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/patients", response_model=PatientResponse, status_code=201)
async def create_patient(
    request: CreatePatientRequest,
    user_id: CurrentUserIdDep,
    service: PatientServiceDep,
):
    """Add a new patient."""
    patient = await service.create(
        user_id=user_id,
        data=request.model_dump(),
    )

    return PatientResponse.model_validate(patient)


@router.get("/patients/{patient_id}", response_model=PatientResponse)
async def get_patient(
    patient_id: str,
    user_id: CurrentUserIdDep,
    service: PatientServiceDep,
):
    """Get a single patient by ID."""

    patient = await service.get(
        patient_id=UUID(patient_id),
        user_id=user_id,
    )

    return PatientResponse.model_validate(patient)


@router.patch("/patients/{patient_id}", response_model=PatientResponse)
async def update_patient(
    patient_id: str,
    request: UpdatePatientRequest,
    user_id: CurrentUserIdDep,
    service: PatientServiceDep,
):
    """Update a patient's details."""

    patient = await service.update(
        patient_id=UUID(patient_id),
        user_id=user_id,
        data=request.model_dump(exclude_unset=True),
    )

    return PatientResponse.model_validate(patient)


@router.delete("/patients/{patient_id}", response_model=StatusResponse)
async def delete_patient(
    patient_id: str,
    user_id: CurrentUserIdDep,
    service: PatientServiceDep,
):
    """Delete a patient."""

    await service.delete(
        patient_id=UUID(patient_id),
        user_id=user_id,
    )

    return StatusResponse(status="success")
