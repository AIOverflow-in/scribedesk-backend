from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field
from sqlalchemy import inspect as sa_inspect

from src.infrastructure.persistence.postgres.models import Session
from src.schemas.api.reports import ReportMetadata
from src.utils.formatters import calculate_age


def _session_to_dict(session: Session) -> dict:
    """Extract only column attributes from a SQLAlchemy model to avoid triggering lazy loads."""
    return {
        c.key: getattr(session, c.key)
        for c in sa_inspect(session).mapper.column_attrs
    }


# --- Request ---

class CreateSessionRequest(BaseModel):
    patient_id: Optional[UUID] = None


class UpdateSessionRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    patient_id: Optional[UUID] = None
    clinical_summary: Optional[str] = None


# --- Response ---

class SessionListItem(BaseModel):
    id: UUID
    patient_id: Optional[UUID] = None
    patient_name: Optional[str] = None
    patient_gender: Optional[str] = None
    patient_age: Optional[int] = None
    title: str
    description: Optional[str] = None
    status: str
    total_audio_seconds: int
    current_segment_start: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

    @classmethod
    def from_session(cls, session: Session) -> "SessionListItem":
        resp = cls.model_validate(_session_to_dict(session))
        loaded = sa_inspect(session).unloaded
        if "patient" not in loaded and session.patient:
            resp.patient_name = session.patient.full_name
            resp.patient_gender = session.patient.gender
            resp.patient_age = calculate_age(session.patient.date_of_birth)
        return resp


class SessionResponse(SessionListItem):
    clinical_summary: Optional[str] = None
    last_summarized_transcript_id: Optional[UUID] = None
    reports: list[ReportMetadata] = []

    @classmethod
    def from_session(cls, session: Session) -> "SessionResponse":
        resp = cls.model_validate(_session_to_dict(session))
        loaded = sa_inspect(session).unloaded
        if "patient" not in loaded and session.patient:
            resp.patient_name = session.patient.full_name
            resp.patient_gender = session.patient.gender
            resp.patient_age = calculate_age(session.patient.date_of_birth)
        if "reports" not in loaded and session.reports:
            resp.reports = [
                ReportMetadata(
                    id=r.id,
                    title=r.title,
                    template_name=r.template.name if r.template else "Unknown",
                    created_at=r.created_at,
                )
                for r in session.reports
            ]
        return resp


class SessionTimelineResponse(BaseModel):
    id: UUID
    session_id: UUID
    type: str
    event_type: Optional[str] = None
    content: Optional[str] = None
    speaker_id: Optional[int] = None
    relative_seconds: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True
