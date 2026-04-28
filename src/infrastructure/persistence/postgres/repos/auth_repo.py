from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.persistence.postgres.models import Clinic, User


class AuthRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_email(self, email: str) -> Optional[User]:
        stmt = select(User).where(User.email == email)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_user(self, user: User, clinic: Clinic) -> User:
        self.session.add(user)
        self.session.add(clinic)
        await self.session.commit()
        await self.session.refresh(user)
        return user
