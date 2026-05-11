from datetime import datetime, timezone
from typing import Optional, Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.persistence.postgres.models import Clinic, User, UserAuthProvider


class AuthRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    # --- User Lookup ---

    async def get_by_email(self, email: str) -> Optional[User]:
        stmt = select(User).where(User.email == email)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        stmt = select(User).where(User.id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    # --- User & Clinic Writes ---

    async def create_user(self, user: User) -> User:
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def update_user(self, user: User, data: dict) -> User:
        for key, value in data.items():
            setattr(user, key, value)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def create_clinic(self, clinic: Clinic) -> Clinic:
        self.session.add(clinic)
        await self.session.commit()
        await self.session.refresh(clinic)
        return clinic

    # --- Provider Lookup ---

    async def get_provider(
        self,
        provider: str,
        provider_user_id: str,
    ) -> Optional[UserAuthProvider]:
        stmt = select(UserAuthProvider).where(
            UserAuthProvider.provider == provider,
            UserAuthProvider.provider_user_id == provider_user_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_email_provider(self, email: str) -> Optional[UserAuthProvider]:
        stmt = select(UserAuthProvider).where(
            UserAuthProvider.provider == "email",
            UserAuthProvider.email == email,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_provider_by_id(self, provider_id: UUID) -> Optional[UserAuthProvider]:
        stmt = select(UserAuthProvider).where(UserAuthProvider.id == provider_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_providers(self, user_id: UUID) -> Sequence[UserAuthProvider]:
        stmt = (
            select(UserAuthProvider)
            .where(UserAuthProvider.user_id == user_id)
            .order_by(UserAuthProvider.linked_at)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_oauth_provider_names(self, user_id: UUID) -> list[str]:
        stmt = (
            select(UserAuthProvider.provider)
            .where(
                UserAuthProvider.user_id == user_id,
                UserAuthProvider.provider != "email",
            )
            .distinct()
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    # --- Provider Writes ---

    async def create_provider(self, provider: UserAuthProvider) -> UserAuthProvider:
        self.session.add(provider)
        await self.session.commit()
        await self.session.refresh(provider)
        return provider

    async def update_provider_last_used(self, provider_id: UUID) -> None:
        stmt = select(UserAuthProvider).where(UserAuthProvider.id == provider_id)
        result = await self.session.execute(stmt)
        provider = result.scalar_one_or_none()
        if provider:
            provider.last_used_at = datetime.now(timezone.utc)
            await self.session.commit()

    async def update_provider_password(
        self,
        provider_id: UUID,
        password_hash: str,
    ) -> None:
        stmt = select(UserAuthProvider).where(UserAuthProvider.id == provider_id)
        result = await self.session.execute(stmt)
        provider = result.scalar_one_or_none()
        if provider:
            provider.password_hash = password_hash
            await self.session.commit()

    async def delete_provider(self, provider_id: UUID) -> None:
        stmt = select(UserAuthProvider).where(UserAuthProvider.id == provider_id)
        result = await self.session.execute(stmt)
        provider = result.scalar_one_or_none()
        if provider:
            await self.session.delete(provider)
            await self.session.commit()
