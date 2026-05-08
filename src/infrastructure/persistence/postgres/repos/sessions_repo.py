from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.logging import get_logger
from src.infrastructure.persistence.postgres.models import Patient, Report, Session, SessionTimeline

logger = get_logger(__name__)


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
        search: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[list[Session], int]:
        filters = [Session.user_id == user_id]
        if patient_id is not None:
            filters.append(Session.patient_id == patient_id)

        base = select(Session).options(selectinload(Session.patient))

        need_patient_join = search is not None or sort_by == "patient_name"
        if need_patient_join:
            patient_alias = (
                select(Patient)
                .where(Patient.user_id == user_id)
                .subquery()
            )
            base = base.outerjoin(patient_alias, Session.patient_id == patient_alias.c.id)

        if search:
            search = search.strip()
            pattern = f"%{search}%"
            filters.append(
                or_(
                    Session.title.ilike(pattern),
                    patient_alias.c.first_name.ilike(pattern),
                    patient_alias.c.last_name.ilike(pattern),
                    func.concat(
                        func.coalesce(patient_alias.c.first_name, ""), " ",
                        func.coalesce(patient_alias.c.last_name, ""),
                    ).ilike(pattern),
                )
            )

        count_stmt = select(func.count()).select_from(Session).where(*filters)
        total = await self.session.scalar(count_stmt) or 0

        base = base.where(*filters)

        if sort_by == "patient_name":
            sort_col = func.concat(
                func.coalesce(patient_alias.c.first_name, ""), " ",
                func.coalesce(patient_alias.c.last_name, ""),
            )
            base = base.order_by(sort_col.asc() if sort_order == "asc" else sort_col.desc())
        elif sort_by == "title":
            base = base.order_by(Session.title.asc() if sort_order == "asc" else Session.title.desc())
        else:
            base = base.order_by(Session.created_at.asc() if sort_order == "asc" else Session.created_at.desc())

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

        Uses the ``created_at`` of the checkpoint transcript (not UUID
        ordering) so that newly inserted entries are never missed.

        If ``after_id`` is ``None``, returns all transcripts for the session.
        ``limit`` caps how many entries to return (useful for title generation).
        Returns ``(texts, max_id)`` where ``max_id`` is the last transcript ID.
        """
        after_ts = None
        if after_id is not None:
            checkpoint = await self.session.get(SessionTimeline, after_id)
            if checkpoint is not None and checkpoint.created_at is not None:
                after_ts = checkpoint.created_at
                logger.info(
                    f"[TRANSCRIPTS_SINCE] checkpoint_id={after_id} "
                    f"checkpoint_created_at={after_ts} "
                    f"looking_for > {after_ts}"
                )

        stmt = (
            select(SessionTimeline)
            .where(
                SessionTimeline.session_id == session_id,
                SessionTimeline.type == "transcript",
            )
            .order_by(SessionTimeline.created_at.asc())
        )

        if after_ts is not None:
            stmt = stmt.where(SessionTimeline.created_at > after_ts)

        if limit is not None:
            stmt = stmt.limit(limit)

        result = await self.session.execute(stmt)
        entries = list(result.scalars().all())

        if after_ts is not None:
            logger.info(
                f"[TRANSCRIPTS_SINCE] found={len(entries)} entries "
                f"first_created_at={entries[0].created_at if entries else 'N/A'} "
                f"last_created_at={entries[-1].created_at if entries else 'N/A'}"
            )
        else:
            logger.info(
                f"[TRANSCRIPTS_SINCE] first call, found={len(entries)} entries"
            )

        texts = [e.content for e in entries if e.content]
        max_id = entries[-1].id if entries else None

        return texts, max_id
