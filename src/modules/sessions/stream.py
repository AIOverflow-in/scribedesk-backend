"""Scribe transcription stream — WebSocket audio pipeline."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi import WebSocket, WebSocketDisconnect

from src.core.config import settings
from src.core.exceptions import NotFoundException
from src.core.logging import get_logger
from src.infrastructure.external.deepgram import DeepgramClient
from src.infrastructure.persistence.postgres.database import async_session_maker
from src.infrastructure.persistence.postgres.models import Session, SessionTimeline
from src.infrastructure.persistence.postgres.repos.sessions_repo import SessionsRepository

logger = get_logger(__name__)


class ScribeStreamService:
    """Manages the real-time Deepgram transcription stream for a single WS connection."""

    def __init__(
        self,
        repo: SessionsRepository,
        deepgram_client: DeepgramClient | None = None,
    ):
        self.repo = repo
        self.deepgram = deepgram_client or DeepgramClient()

    # --- Internal helpers ---

    async def _get_session(self, session_id: UUID, user_id: UUID) -> Session:
        session = await self.repo.get_by_id(session_id, user_id)
        if not session:
            raise NotFoundException("Session not found")
        return session

    # --- Session event lifecycle ---

    async def prepare_start(self, session_id: UUID, user_id: UUID) -> tuple[int, str]:
        """Called on WS connect. Logs started/resumed event, sets segment start."""
        session = await self._get_session(session_id, user_id)

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

    async def prepare_stop(self, session_id: UUID, user_id: UUID) -> tuple[int, bool]:
        """Called on WS disconnect. Finalises timing, logs stopped event."""
        session = await self._get_session(session_id, user_id)

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

        return elapsed, is_first_stop

    # --- Transcript persistence ---

    async def add_transcript(
        self,
        session_id: UUID,
        user_id: UUID,
        text: str,
        relative_seconds: int,
    ) -> SessionTimeline:
        """Save a single transcript chunk to the DB."""
        session = await self._get_session(session_id, user_id)

        entry = SessionTimeline(
            id=uuid4(),
            session_id=session.id,
            type="transcript",
            content=text,
            relative_seconds=relative_seconds,
            created_at=datetime.now(timezone.utc),
        )
        return await self.repo.add_timeline_entry(entry)

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
           (``transcript_partial``) without persisting.
        4. On every Nth flush: saves the accumulated text to the DB
           and sends a ``transcript_chunk`` message to the frontend.
        5. On disconnect: finalises timing.
        """
        accumulated, _ = await self.prepare_start(session_id, user_id)

        await websocket.send_json({
            "type": "ready",
            "accumulated_seconds": accumulated,
        })

        segment_start = datetime.now(timezone.utc)
        ctx = {
            "accumulated": accumulated,
            "segment_start": segment_start,
            "batch_start_ts": None,
            "ws_closed": False,
            "last_deepgram_at": datetime.now(timezone.utc),
            "notified_idle": False,
        }

        with self.deepgram.create_session(
            on_flush=lambda text: self._on_flush(ctx, websocket, session_id, text),
            on_intermediate=lambda text: self._on_intermediate(ctx, websocket, text),
        ) as dg_session:
            try:
                while True:
                    data = await websocket.receive_bytes()
                    await asyncio.to_thread(dg_session.send_audio, data)

                    now = datetime.now(timezone.utc)
                    idle = (now - ctx["last_deepgram_at"]).total_seconds()
                    if idle >= settings.SCRIBE_IDLE_TIMEOUT_SECONDS and not ctx["notified_idle"]:
                        ctx["notified_idle"] = True
                        logger.info(
                            f"Session {session_id} idle for {idle:.0f}s — flushing and closing"
                        )
                        await websocket.send_json({
                            "type": "idle_timeout",
                            "idle_seconds": int(idle),
                        })
                        break
            except WebSocketDisconnect:
                ctx["ws_closed"] = True
                logger.info(f"Client disconnected from session {session_id}")
            except Exception as e:
                logger.error(f"Transcription error for session {session_id}: {e}", exc_info=True)
                raise

        await dg_session.flush_remaining()
        elapsed, is_first_stop = await self.prepare_stop(session_id, user_id)

        logger.info("Scribe session segment ended", extra={
            "session_id": str(session_id),
            "elapsed_seconds": elapsed,
            "is_first_stop": is_first_stop,
        })

    # --- Internal helpers ---

    @staticmethod
    def _relative_seconds(ctx: dict) -> int:
        elapsed = int((datetime.now(timezone.utc) - ctx["segment_start"]).total_seconds())
        return ctx["accumulated"] + elapsed

    async def _on_intermediate(self, ctx: dict, websocket: WebSocket, text: str) -> None:
        ts = self._relative_seconds(ctx)
        if ctx["batch_start_ts"] is None:
            ctx["batch_start_ts"] = ts
        ctx["last_deepgram_at"] = datetime.now(timezone.utc)
        await websocket.send_json({
            "type": "transcript_partial",
            "text": text,
            "timestamp": ts,
        })

    async def _on_flush(self, ctx: dict, websocket: WebSocket, session_id: UUID, text: str) -> None:
        ts = ctx["batch_start_ts"] if ctx["batch_start_ts"] is not None else self._relative_seconds(ctx)
        ctx["batch_start_ts"] = None

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

        if not ctx["ws_closed"]:
            await websocket.send_json({
                "type": "transcript_chunk",
                "text": text,
                "timestamp": ts,
            })
        logger.info(f"[FLUSH DB] {text[:60]}...")

