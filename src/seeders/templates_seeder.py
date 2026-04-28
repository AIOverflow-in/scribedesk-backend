"""
System Templates Seeder.

Creates default clinical documentation, letter, and prescription templates.

Usage:
    python -m src.seeders.templates_seeder
"""

import asyncio
import textwrap
import uuid

from sqlalchemy import select

from src.content.templates import ClinicalTemplates, LetterTemplates, PrescriptionTemplates
from src.infrastructure.persistence.postgres.database import async_session_maker
from src.infrastructure.persistence.postgres.models import Template


async def delete_existing_system_templates(session):
    result = await session.execute(select(Template).where(Template.is_system == True))
    existing = result.scalars().all()

    if existing:
        for template in existing:
            await session.delete(template)
        await session.flush()
        print(f"Deleted {len(existing)} existing system templates")


async def seed_templates():
    async with async_session_maker() as session:
        await delete_existing_system_templates(session)

        template_data = [
            *ClinicalTemplates.all(),
            *LetterTemplates.all(),
            *PrescriptionTemplates.all(),
        ]

        templates = [
            Template(
                id=uuid.uuid4(),
                name=t["name"],
                root_type=t["root_type"],
                sub_type=t.get("sub_type"),
                content=textwrap.dedent(t["content"]).strip(),
                is_system=True,
                user_id=None,
            )
            for t in template_data
        ]

        session.add_all(templates)
        await session.flush()
        await session.commit()

        print(f"SUCCESS: Created {len(templates)} system templates")
        for t in templates:
            print(f"  - {t.name} ({t.root_type})")


def main():
    print("=" * 50)
    print("System Templates Seeder")
    print("=" * 50)
    asyncio.run(seed_templates())


if __name__ == "__main__":
    main()
