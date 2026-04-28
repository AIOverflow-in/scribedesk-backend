from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


# --- Request ---

class CreateReportRequest(BaseModel):
    session_id: UUID
    template_id: UUID
    additional_context: Optional[str] = Field(None, max_length=2000)


# --- Response ---

class ReportResponse(BaseModel):
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


class ReportMetadata(BaseModel):
    """Lightweight report info for embedding in session responses."""
    id: UUID
    title: str
    template_name: str
    created_at: datetime
