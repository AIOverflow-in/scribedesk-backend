from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class PatientDb(BaseModel):
    id: UUID
    user_id: UUID
    full_name: str
    email: Optional[str] = None
    identifier: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    blood_group: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SessionDb(BaseModel):
    id: UUID
    user_id: UUID
    patient_id: Optional[UUID] = None
    title: str
    description: Optional[str] = None
    status: str
    total_audio_seconds: int
    current_segment_start: Optional[datetime] = None
    clinical_summary: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SessionTimelineDb(BaseModel):
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


class TemplateDb(BaseModel):
    id: UUID
    name: str
    root_type: str
    sub_type: Optional[str] = None
    content: str
    is_system: bool
    user_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ReportDb(BaseModel):
    id: UUID
    session_id: UUID
    template_id: UUID
    title: str
    content: str
    report_metadata: Optional[dict] = None
    is_signed: bool
    signed_at: Optional[datetime] = None
    content_hash: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
