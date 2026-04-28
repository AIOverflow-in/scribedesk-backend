from datetime import datetime
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# --- Request ---

class CreateTemplateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    root_type: Literal["notes", "letters", "prescription"]
    content: str = Field(..., min_length=1)


class UpdateTemplateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    content: Optional[str] = None


# --- Response ---

class TemplateResponse(BaseModel):
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
