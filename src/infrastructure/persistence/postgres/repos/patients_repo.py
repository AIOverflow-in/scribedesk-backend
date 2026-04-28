from typing import Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.persistence.postgres.models import Patient


class PatientsRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, patient_id: UUID, user_id: UUID) -> Optional[Patient]:
        stmt = select(Patient).where(
            Patient.id == patient_id,
            Patient.user_id == user_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_user(
        self,
        user_id: UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Patient], int]:
        base = select(Patient).where(Patient.user_id == user_id).order_by(Patient.created_at.desc())

        count_stmt = select(func.count()).select_from(base.subquery())
        total = await self.session.scalar(count_stmt) or 0

        offset = (page - 1) * page_size
        stmt = base.offset(offset).limit(page_size)
        result = await self.session.execute(stmt)
        items = list(result.scalars().all())

        return items, total

    async def create(self, patient: Patient) -> Patient:
        self.session.add(patient)
        await self.session.commit()
        await self.session.refresh(patient)
        return patient

    async def update(self, patient: Patient, data: dict) -> Patient:
        for key, value in data.items():
            setattr(patient, key, value)
        await self.session.commit()
        await self.session.refresh(patient)
        return patient

    async def delete(self, patient: Patient) -> None:
        await self.session.delete(patient)
        await self.session.commit()
