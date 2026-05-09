import json
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

from src.dependencies.auth import CurrentUserIdDep
from src.dependencies.services import ChatServiceDep
from src.schemas.api.chat import ChatRequest, PaginatedChatResponse

router = APIRouter()


@router.post("/chats/messages")
async def chat_message(
    request: ChatRequest,
    user_id: CurrentUserIdDep,
    service: ChatServiceDep,
):
    async def event_generator():
        async for chunk in service.chat_stream(
            user_id=user_id,
            conversation_id=request.conversation_id,
            message=request.message,
            session_id=request.session_id,
            patient_id=request.patient_id,
        ):
            yield chunk

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/chats")
async def list_chats(
    user_id: CurrentUserIdDep,
    service: ChatServiceDep,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session_id: Optional[UUID] = Query(None),
):
    items, total = await service.list_conversations(
        user_id=user_id,
        page=page,
        page_size=page_size,
        session_id=session_id,
    )
    return PaginatedChatResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/chats/{conversation_id}")
async def get_chat(
    conversation_id: UUID,
    user_id: CurrentUserIdDep,
    service: ChatServiceDep,
):
    result = await service.get_conversation(
        user_id=user_id,
        conversation_id=conversation_id,
    )
    if not result:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Conversation not found")
    return result


@router.delete("/chats/{conversation_id}", status_code=204)
async def delete_chat(
    conversation_id: UUID,
    user_id: CurrentUserIdDep,
    service: ChatServiceDep,
):
    await service.delete_conversation(
        user_id=user_id,
        conversation_id=conversation_id,
    )
