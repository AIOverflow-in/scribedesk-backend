from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from src.infrastructure.persistence.postgres.models import Session
from src.utils.formatters import calculate_age


# --- Request ---

class CreateSessionRequest(BaseModel):
    patient_id: Optional[UUID] = None


class UpdateSessionRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    patient_id: Optional[UUID] = None
    clinical_summary: Optional[str] = None


# --- Response ---

class SessionResponse(BaseModel):
    id: UUID
    user_id: UUID
    patient_id: Optional[UUID] = None
    patient_name: Optional[str] = None
    patient_gender: Optional[str] = None
    patient_age: Optional[int] = None
    title: str
    description: Optional[str] = None
    status: str
    total_audio_seconds: int
    current_segment_start: Optional[datetime] = None
    clinical_summary: Optional[str] = None
    last_summarized_transcript_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

    @classmethod
    def from_session(cls, session: Session) -> "SessionResponse":
        resp = cls.model_validate(session)
        if session.patient:
            resp.patient_name = session.patient.full_name
            resp.patient_gender = session.patient.gender
            resp.patient_age = calculate_age(session.patient.date_of_birth)
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
