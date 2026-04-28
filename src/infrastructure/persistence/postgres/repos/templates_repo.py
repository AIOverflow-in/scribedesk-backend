from typing import Optional
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.persistence.postgres.models import Template


class TemplatesRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, template_id: UUID) -> Optional[Template]:
        stmt = select(Template).where(Template.id == template_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_for_user(self, user_id: UUID) -> list[Template]:
        stmt = (
            select(Template)
            .where(or_(Template.is_system == True, Template.user_id == user_id))
            .order_by(Template.is_system.desc(), Template.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create(self, template: Template) -> Template:
        self.session.add(template)
        await self.session.commit()
        await self.session.refresh(template)
        return template

    async def update(self, template: Template, data: dict) -> Template:
        for key, value in data.items():
            setattr(template, key, value)
        await self.session.commit()
        await self.session.refresh(template)
        return template

    async def delete(self, template: Template) -> None:
        await self.session.delete(template)
        await self.session.commit()
