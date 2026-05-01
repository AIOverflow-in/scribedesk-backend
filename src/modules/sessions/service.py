"""Session service — REST operations and WebSocket lifecycle."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from fastapi import WebSocket, WebSocketDisconnect

from src.core.exceptions import NotFoundException
from src.core.logging import get_logger
from src.infrastructure.external.deepgram import DeepgramClient
from src.infrastructure.llm.service import LLMService
from src.infrastructure.persistence.postgres.database import async_session_maker
from src.infrastructure.persistence.postgres.models import Session, SessionTimeline
from src.infrastructure.persistence.postgres.repos.sessions_repo import SessionsRepository
from src.modules.sessions.ai import generate_summary, generate_title

logger = get_logger(__name__)


class SessionService:
    def __init__(
        self,
        repo: SessionsRepository,
        deepgram_client: DeepgramClient | None = None,
        tiny_llm: LLMService | None = None,
        fast_llm: LLMService | None = None,
    ):
        self.repo = repo
        self.deepgram = deepgram_client or DeepgramClient()
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

    # --- WebSocket lifecycle ---

    async def prepare_start(self, session_id: UUID, user_id: UUID) -> tuple[int, str]:
        """
        Called on WS connect.

        Logs a ``started`` / ``resumed`` timeline event and sets
        ``current_segment_start`` for live time calculation.

        Returns ``(accumulated_seconds, event_type)``.
        The frontend uses ``accumulated_seconds`` to initialise its timer.
        """
        session = await self.get(session_id, user_id)

        is_first = session.total_audio_seconds == 0
        event_type = "started" if is_first else "resumed"
        accumulated = session.total_audio_seconds

        entry = SessionTimeline(
            id=uuid4(),
            session_id=session.id,
            type="event",
            event_type=event_type,
            content=f"Transcript {event_type} {datetime.now(timezone.utc).strftime('%H:%M:%S')}",
            relative_seconds=accumulated,
            created_at=datetime.now(timezone.utc),
        )
        await self.repo.add_timeline_entry(entry)
        await self.repo.update(session, {"current_segment_start": datetime.now(timezone.utc)})

        return accumulated, event_type

    async def add_transcript(
        self,
        session_id: UUID,
        user_id: UUID,
        text: str,
        relative_seconds: int,
    ) -> SessionTimeline:
        """Save a transcript chunk flushed from the Deepgram buffer."""
        session = await self.get(session_id, user_id)

        entry = SessionTimeline(
            id=uuid4(),
            session_id=session.id,
            type="transcript",
            content=text,
            relative_seconds=relative_seconds,
            created_at=datetime.now(timezone.utc),
        )
        return await self.repo.add_timeline_entry(entry)

    async def prepare_stop(self, session_id: UUID, user_id: UUID) -> tuple[int, bool]:
        """
        Called on WS disconnect.

        Finalises the current segment: updates ``total_audio_seconds``,
        clears ``current_segment_start``, logs a ``stopped`` event.

        On first stop: generates title + summary synchronously.
        On subsequent stops: updates summary incrementally.

        Returns ``(elapsed_seconds, is_first_stop)``.
        """
        session = await self.get(session_id, user_id)

        if session.current_segment_start is None:
            return 0, False

        now = datetime.now(timezone.utc)
        elapsed = int((now - session.current_segment_start).total_seconds())
        new_total = session.total_audio_seconds + elapsed
        is_first_stop = session.total_audio_seconds == 0

        entry = SessionTimeline(
            id=uuid4(),
            session_id=session.id,
            type="event",
            event_type="stopped",
            content=f"Transcript stopped {now.strftime('%H:%M:%S')}",
            relative_seconds=new_total,
            created_at=datetime.now(timezone.utc),
        )
        await self.repo.add_timeline_entry(entry)

        await self.repo.update(session, {
            "total_audio_seconds": new_total,
            "current_segment_start": None,
        })

        if is_first_stop:
            logger.info(f"First stop — generating title and summary for {session_id}")

            results = await asyncio.gather(
                generate_title(self.repo, self.tiny_llm, session_id, user_id),
                generate_summary(self.repo, self.fast_llm, session_id, user_id),
                return_exceptions=True,
            )

            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    label = "Title" if i == 0 else "Summary"
                    logger.error(f"{label} generation failed: {result}")
        else:
            logger.info(f"Updating summary for session {session_id}")
            try:
                await generate_summary(self.repo, self.fast_llm, session_id, user_id)
            except Exception as e:
                logger.error(f"Summary update failed: {e}")

        return elapsed, is_first_stop

    # --- Full transcription stream ---

    async def handle_transcription_stream(
        self,
        websocket: WebSocket,
        session_id: UUID,
        user_id: UUID,
    ) -> None:
        """
        Run the full real-time transcription flow for one WS connection.

        1. Logs ``started`` / ``resumed`` and sends a ``ready`` packet.
        2. Opens a Deepgram session and pipes incoming audio.
        3. Forwards each ``is_final`` fragment to the frontend live
           (``transcript_fragment``) without persisting.
        4. On every Nth flush: saves the accumulated text to the DB
           and sends a ``transcript`` message to the frontend.
        5. On disconnect: finalises timing, generates title/summary.
        """
        accumulated, _ = await self.prepare_start(session_id, user_id)

        await websocket.send_json({
            "type": "ready",
            "accumulated_seconds": accumulated,
        })

        segment_start = datetime.now(timezone.utc)

        def _relative_seconds() -> int:
            elapsed = int((datetime.now(timezone.utc) - segment_start).total_seconds())
            return accumulated + elapsed

        batch_start_ts: int | None = None

        async def on_intermediate(text: str) -> None:
            """Live preview — sent to frontend only, not persisted."""
            nonlocal batch_start_ts
            ts = _relative_seconds()
            if batch_start_ts is None:
                batch_start_ts = ts
            msg = {
                "type": "transcript_fragment",
                "text": text,
                "timestamp": ts,
            }
            await websocket.send_json(msg)

        async def on_flush(text: str) -> None:
            """Persist accumulated text and notify frontend."""
            nonlocal batch_start_ts
            ts = batch_start_ts if batch_start_ts is not None else _relative_seconds()
            batch_start_ts = None

            async with async_session_maker() as db:
                entry = SessionTimeline(
                    id=uuid4(),
                    session_id=session_id,
                    type="transcript",
                    content=text,
                    relative_seconds=ts,
                    created_at=datetime.now(timezone.utc),
                )
                repo = SessionsRepository(db)
                await repo.add_timeline_entry(entry)

            if not ws_closed:
                msg = {
                    "type": "transcript",
                    "text": text,
                    "timestamp": ts,
                }
                await websocket.send_json(msg)
            logger.info(f"[FLUSH DB] {text[:60]}...")

        ws_closed = False

        with self.deepgram.create_session(
            on_flush=on_flush,
            on_intermediate=on_intermediate,
        ) as dg_session:
            try:
                while True:
                    data = await websocket.receive_bytes()
                    await asyncio.to_thread(dg_session.send_audio, data)
            except WebSocketDisconnect:
                ws_closed = True
                logger.info(f"Client disconnected from session {session_id}")
            except Exception as e:
                logger.error(f"Transcription error for session {session_id}: {e}", exc_info=True)
                raise

        # Final flush — skip sending to frontend if WS already closed
        await dg_session.flush_remaining()
        elapsed, is_first_stop = await self.prepare_stop(session_id, user_id)

        logger.info("Scribe session segment ended", extra={
            "session_id": str(session_id),
            "elapsed_seconds": elapsed,
            "is_first_stop": is_first_stop,
        })
