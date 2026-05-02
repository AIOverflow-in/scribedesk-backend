"""Session service — REST operations and pause/stop logic."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from src.core.exceptions import NotFoundException
from src.core.logging import get_logger
from src.infrastructure.llm.service import LLMService
from src.infrastructure.persistence.postgres.models import Session, SessionTimeline
from src.infrastructure.persistence.postgres.repos.sessions_repo import SessionsRepository
from src.modules.sessions.ai import generate_summary, generate_title

logger = get_logger(__name__)


class SessionService:
    def __init__(
        self,
        repo: SessionsRepository,
        tiny_llm: LLMService | None = None,
        fast_llm: LLMService | None = None,
    ):
        self.repo = repo
        self.tiny_llm = tiny_llm
        self.fast_llm = fast_llm

    # --- REST operations ---

    async def create(self, user_id: UUID, patient_id: UUID | None = None) -> Session:
        """Create a blank active session."""
        session = Session(
            id=uuid4(),
            user_id=user_id,
            patient_id=patient_id,
            title="Untitled Session",
            status="active",
        )
        return await self.repo.create(session)

    async def get(self, session_id: UUID, user_id: UUID) -> Session:
        """Get a session by ID with ownership check."""
        session = await self.repo.get_by_id(session_id, user_id)
        if not session:
            raise NotFoundException("Session not found")
        return session

    async def list(
        self,
        user_id: UUID,
        page: int,
        page_size: int,
        patient_id: Optional[UUID] = None,
        search: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[list[Session], int]:
        """Paginated session list with search and sorting."""
        return await self.repo.list_by_user(
            user_id,
            page,
            page_size,
            patient_id=patient_id,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
        )

    async def update(self, session_id: UUID, user_id: UUID, data: dict) -> Session:
        """Update session metadata (title, patient, summary, etc.)."""
        session = await self.get(session_id, user_id)
        return await self.repo.update(session, data)

    async def delete(self, session_id: UUID, user_id: UUID) -> None:
        """Delete a session with ownership check."""
        session = await self.get(session_id, user_id)
        await self.repo.delete(session)

    async def get_timeline(self, session_id: UUID, user_id: UUID) -> list[SessionTimeline]:
        """Get the full timeline (events + transcripts) for a session."""
        session = await self.get(session_id, user_id)
        return await self.repo.get_timeline(session.id)

    async def pause_session(
        self,
        session_id: UUID,
        user_id: UUID,
        with_summary: bool,
    ) -> Session:
        """
        Pause or stop a session from the REST API.

        Called after the WebSocket has already disconnected (so all audio
        is flushed and persisted).  This method handles the LLM work:

        1. Generate title + description if still at default ("Untitled Session").
        2. If ``with_summary=True``: generate / update clinical summary.
        3. Set status to ``"paused"`` or ``"completed"``.

        Returns the updated ``Session`` object.
        """
        session = await self.get(session_id, user_id)

        if session.title == "Untitled Session":
            try:
                await generate_title(self.repo, self.tiny_llm, session_id, user_id)
                session = await self.repo.get_by_id(session_id, user_id)
            except Exception as e:
                logger.error(f"Title generation failed: {e}")

        if with_summary:
            try:
                await generate_summary(self.repo, self.fast_llm, session_id, user_id)
            except Exception as e:
                logger.error(f"Summary generation failed: {e}")

            await self.repo.update(session, {"status": "completed"})
        else:
            await self.repo.update(session, {"status": "paused"})

        return await self.repo.get_by_id(session_id, user_id)
