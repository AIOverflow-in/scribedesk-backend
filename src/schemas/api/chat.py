from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel


class ChatRequest(BaseModel):
    conversation_id: Optional[UUID] = None
    message: str
    session_id: Optional[UUID] = None
    patient_id: Optional[UUID] = None


class StreamChunk(BaseModel):
    type: str  # content, status, tool_call, metadata, error, done
    content: Optional[str] = None
    status_message: Optional[str] = None
    tool_name: Optional[str] = None
    metadata_type: Optional[str] = None
    data: Optional[Any] = None
    error: Optional[str] = None


class ChatSummary(BaseModel):
    id: UUID
    title: str
    is_title_generated: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MessageItem(BaseModel):
    id: UUID
    role: str
    content: str
    artifacts: Optional[Any] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationResponse(BaseModel):
    id: UUID
    title: str
    is_title_generated: bool
    session_id: Optional[UUID] = None
    patient_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    messages: list[MessageItem]

    class Config:
        from_attributes = True


class PaginatedChatResponse(BaseModel):
    items: list[ChatSummary]
    total: int
    page: int
    page_size: int
