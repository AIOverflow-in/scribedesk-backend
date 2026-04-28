from uuid import UUID

from src.core.exceptions import NotFoundException
from src.infrastructure.persistence.postgres.models import User
from src.infrastructure.persistence.postgres.repos.user_repo import UserRepository


class UserService:
    def __init__(self, repo: UserRepository):
        self.repo = repo

    async def get_profile(self, user_id: UUID) -> User:
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise NotFoundException("User not found")
        return user

    async def update_profile(self, user_id: UUID, data: dict) -> User:
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise NotFoundException("User not found")
        return await self.repo.update_user(user, data)

    async def update_clinic(self, user_id: UUID, data: dict) -> User:
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise NotFoundException("User not found")
        if not user.clinic:
            raise NotFoundException("Clinic not found")
        return await self.repo.update_clinic(user.clinic, data)
