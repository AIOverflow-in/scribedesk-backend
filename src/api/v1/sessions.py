"""Session CRUD routes — create, list, get, update, timeline."""

from uuid import UUID

from fastapi import APIRouter

from src.dependencies.auth import CurrentUserIdDep
from src.dependencies.services import SessionServiceDep
from src.schemas.api.common import PaginatedResponse
from src.schemas.api.sessions import (
    CreateSessionRequest,
    SessionResponse,
    SessionTimelineResponse,
    UpdateSessionRequest,
)

router = APIRouter()


@router.get("/sessions", response_model=PaginatedResponse[SessionResponse])
async def list_sessions(
    user_id: CurrentUserIdDep,
    service: SessionServiceDep,
    page: int = 1,
    page_size: int = 20,
):
    """List sessions with pagination."""
    items, total = await service.list(
        user_id=user_id,
        page=page,
        page_size=page_size,
    )

    return PaginatedResponse(
        items=[SessionResponse.from_session(s) for s in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/sessions", response_model=SessionResponse, status_code=201)
async def create_session(
    request: CreateSessionRequest,
    user_id: CurrentUserIdDep,
    service: SessionServiceDep,
):
    """Create a new blank session."""
    session = await service.create(
        user_id=user_id,
        patient_id=request.patient_id,
    )

    return SessionResponse.from_session(session)


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: UUID,
    user_id: CurrentUserIdDep,
    service: SessionServiceDep,
):
    """Get a single session by ID with patient info."""
    session = await service.get(
        session_id=session_id,
        user_id=user_id,
    )

    return SessionResponse.from_session(session)


@router.patch("/sessions/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: UUID,
    request: UpdateSessionRequest,
    user_id: CurrentUserIdDep,
    service: SessionServiceDep,
):
    """Update session metadata (title, description, patient, summary)."""
    session = await service.update(
        session_id=session_id,
        user_id=user_id,
        data=request.model_dump(exclude_unset=True),
    )

    return SessionResponse.from_session(session)


@router.get("/sessions/{session_id}/timeline", response_model=list[SessionTimelineResponse])
async def get_timeline(
    session_id: UUID,
    user_id: CurrentUserIdDep,
    service: SessionServiceDep,
):
    """Get the full timeline (events + transcripts) for a session."""
    entries = await service.get_timeline(
        session_id=session_id,
        user_id=user_id,
    )

    return [SessionTimelineResponse.model_validate(e) for e in entries]
