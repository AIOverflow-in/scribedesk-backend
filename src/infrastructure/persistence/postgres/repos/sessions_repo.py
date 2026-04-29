from __future__ import annotations

from typing import Optional
from typing import Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.infrastructure.persistence.postgres.models import Report, Session, SessionTimeline


class SessionsRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, session_id: UUID, user_id: UUID) -> Optional[Session]:
        stmt = (
            select(Session)
            .options(
                selectinload(Session.patient),
                selectinload(Session.reports).selectinload(Report.template),
            )
            .where(Session.id == session_id, Session.user_id == user_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_user(
        self,
        user_id: UUID,
        page: int = 1,
        page_size: int = 20,
        patient_id: Optional[UUID] = None,
    ) -> tuple[list[Session], int]:
        filters = [Session.user_id == user_id]
        if patient_id is not None:
            filters.append(Session.patient_id == patient_id)
        base = select(Session).options(selectinload(Session.patient)).where(*filters).order_by(Session.created_at.desc())

        count_stmt = select(func.count()).select_from(base.subquery())
        total = await self.session.scalar(count_stmt) or 0

        offset = (page - 1) * page_size
        stmt = base.offset(offset).limit(page_size)
        result = await self.session.execute(stmt)
        items = list(result.scalars().all())

        return items, total

    async def get_timeline(self, session_id: UUID) -> list[SessionTimeline]:
        stmt = (
            select(SessionTimeline)
            .where(SessionTimeline.session_id == session_id)
            .order_by(SessionTimeline.relative_seconds.asc(), SessionTimeline.created_at.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def delete(self, session: Session) -> None:
        await self.session.delete(session)
        await self.session.commit()

    async def create(self, session: Session) -> Session:
        self.session.add(session)
        await self.session.commit()
        await self.session.refresh(session)
        return session

    async def update(self, session: Session, data: dict) -> Session:
        for key, value in data.items():
            setattr(session, key, value)
        await self.session.commit()
        await self.session.refresh(session)
        return session

    async def add_timeline_entry(self, entry: SessionTimeline) -> SessionTimeline:
        self.session.add(entry)
        await self.session.commit()
        await self.session.refresh(entry)
        return entry

    async def get_transcripts_since(
        self,
        session_id: UUID,
        after_id: UUID | None = None,
        limit: int | None = None,
    ) -> tuple[list[str], UUID | None]:
        """
        Get transcript text entries after a given timeline ID.

        If ``after_id`` is ``None``, returns all transcripts for the session.
        ``limit`` caps how many entries to return (useful for title generation).
        Returns ``(texts, max_id)`` where ``max_id`` is the last transcript ID.
        """
        stmt = (
            select(SessionTimeline)
            .where(
                SessionTimeline.session_id == session_id,
                SessionTimeline.type == "transcript",
            )
            .order_by(SessionTimeline.created_at.asc())
        )

        if after_id is not None:
            from sqlalchemy import and_
            stmt = stmt.where(SessionTimeline.id > after_id)

        if limit is not None:
            stmt = stmt.limit(limit)

        result = await self.session.execute(stmt)
        entries = list(result.scalars().all())

        texts = [e.content for e in entries if e.content]
        max_id = entries[-1].id if entries else None

        return texts, max_id
