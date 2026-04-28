from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.infrastructure.persistence.postgres.models import Clinic, User


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        stmt = (
            select(User)
            .options(selectinload(User.clinic))
            .where(User.id == user_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_user(self, user: User, data: dict) -> User:
        for key, value in data.items():
            setattr(user, key, value)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def update_clinic(self, clinic: Clinic, data: dict) -> Clinic:
        for key, value in data.items():
            setattr(clinic, key, value)
        await self.session.commit()
        await self.session.refresh(clinic)
        return clinic
