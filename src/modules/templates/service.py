from uuid import UUID, uuid4

from src.core.exceptions import ForbiddenException, NotFoundException
from src.infrastructure.persistence.postgres.models import Template
from src.infrastructure.persistence.postgres.repos.templates_repo import TemplatesRepository


class TemplateService:
    def __init__(self, repo: TemplatesRepository):
        self.repo = repo

    async def list(self, user_id: UUID) -> list[Template]:
        return await self.repo.list_for_user(user_id)

    async def get(self, template_id: UUID) -> Template:
        template = await self.repo.get_by_id(template_id)
        if not template:
            raise NotFoundException("Template not found")
        return template

    async def create(self, user_id: UUID, data: dict) -> Template:
        template = Template(
            id=uuid4(),
            user_id=user_id,
            is_system=False,
            name=data["name"],
            root_type=data["root_type"],
            content=data["content"],
        )
        return await self.repo.create(template)

    async def update(self, template_id: UUID, user_id: UUID, data: dict) -> Template:
        template = await self.get(template_id)

        if template.is_system or template.user_id != user_id:
            raise ForbiddenException("You can only edit your own templates")

        return await self.repo.update(template, data)

    async def delete(self, template_id: UUID, user_id: UUID) -> None:
        template = await self.get(template_id)

        if template.is_system or template.user_id != user_id:
            raise ForbiddenException("You can only delete your own templates")

        await self.repo.delete(template)
