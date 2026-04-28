"""WebSocket route — real-time scribe transcription via Deepgram proxy."""

from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from src.core.logging import get_logger
from src.dependencies.ai import get_fast_llm_service, get_tiny_llm_service
from src.dependencies.auth import WsCurrentUserIdDep
from src.infrastructure.persistence.postgres.database import async_session_maker
from src.infrastructure.persistence.postgres.repos.sessions_repo import SessionsRepository
from src.modules.sessions.service import SessionService

logger = get_logger(__name__)

router = APIRouter()


@router.websocket("/ws/scribe/{session_id}")
async def scribe_websocket(
    websocket: WebSocket,
    session_id: UUID,
    user_id: WsCurrentUserIdDep,
):
    """
    Real-time scribe WebSocket.

    * Authenticated via ``?token=`` (handled by ``WsCurrentUserIdDep``).
    * Delegates to ``SessionService.handle_transcription_stream``.
    """
    await websocket.accept()

    try:
        async with async_session_maker() as db:
            repo = SessionsRepository(db)
            service = SessionService(
                repo=repo,
                tiny_llm=get_tiny_llm_service(),
                fast_llm=get_fast_llm_service(),
            )
            await service.handle_transcription_stream(
                websocket=websocket,
                session_id=session_id,
                user_id=UUID(user_id),
            )

    except WebSocketDisconnect:
        logger.info(f"Client disconnected from session {session_id}")

    except Exception as e:
        logger.error(f"Scribe WS error for session {session_id}: {e}", exc_info=True)
        try:
            await websocket.close(code=1011)
        except Exception:
            pass
