from typing import Optional
from uuid import UUID, uuid4

from src.core.exceptions import NotFoundException
from src.infrastructure.persistence.postgres.models import Patient
from src.infrastructure.persistence.postgres.repos.patients_repo import PatientsRepository


class PatientService:
    def __init__(self, repo: PatientsRepository):
        self.repo = repo

    async def create(self, user_id: UUID, data: dict) -> Patient:
        patient = Patient(
            id=uuid4(),
            user_id=user_id,
            first_name=data["first_name"],
            last_name=data.get("last_name"),
            identifier=data.get("identifier"),
            date_of_birth=data.get("date_of_birth"),
            gender=data.get("gender"),
            email=data.get("email"),
            blood_group=data.get("blood_group"),
        )
        return await self.repo.create(patient)

    async def get(self, patient_id: UUID, user_id: UUID) -> Patient:
        patient = await self.repo.get_by_id(patient_id, user_id)
        if not patient:
            raise NotFoundException("Patient not found")
        return patient

    async def list(
        self,
        user_id: UUID,
        page: int,
        page_size: int,
        search: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[list[Patient], int]:
        return await self.repo.list_by_user(
            user_id,
            page,
            page_size,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
        )

    async def update(self, patient_id: UUID, user_id: UUID, data: dict) -> Patient:
        patient = await self.get(patient_id, user_id)
        return await self.repo.update(patient, data)

    async def delete(self, patient_id: UUID, user_id: UUID) -> None:
        patient = await self.get(patient_id, user_id)
        await self.repo.delete(patient)
