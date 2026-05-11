from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional, Sequence
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.infrastructure.persistence.postgres.models import AIMessage, AIConversation


class AIConversationsRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    # --- Conversation CRUD ---

    async def create_conversation(
        self,
        user_id: UUID,
        session_id: Optional[UUID] = None,
        patient_id: Optional[UUID] = None,
    ) -> AIConversation:
        conv = AIConversation(
            user_id=user_id,
            session_id=session_id,
            patient_id=patient_id,
        )
        self.session.add(conv)
        await self.session.commit()
        await self.session.refresh(conv)
        return conv

    async def get_conversation(
        self,
        conversation_id: UUID,
        user_id: UUID,
    ) -> Optional[AIConversation]:
        stmt = (
            select(AIConversation)
            .options(selectinload(AIConversation.messages))
            .where(
                AIConversation.id == conversation_id,
                AIConversation.user_id == user_id,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_conversations(
        self,
        user_id: UUID,
        page: int = 1,
        page_size: int = 20,
        session_id: Optional[UUID] = None,
    ) -> tuple[list[AIConversation], int]:
        filters = [AIConversation.user_id == user_id]
        if session_id is not None:
            filters.append(AIConversation.session_id == session_id)

        count_stmt = (
            select(func.count())
            .select_from(AIConversation)
            .where(*filters)
        )
        total = await self.session.scalar(count_stmt) or 0

        stmt = (
            select(AIConversation)
            .where(*filters)
            .order_by(AIConversation.updated_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await self.session.execute(stmt)
        items = list(result.scalars().all())

        return items, total

    async def update_title(
        self,
        conversation_id: UUID,
        title: str,
    ) -> None:
        stmt = select(AIConversation).where(AIConversation.id == conversation_id)
        result = await self.session.execute(stmt)
        conv = result.scalar_one_or_none()
        if conv:
            conv.title = title
            conv.is_title_generated = True
            conv.updated_at = datetime.now(timezone.utc)
            await self.session.commit()

    async def update_timestamp(self, conversation_id: UUID) -> None:
        stmt = select(AIConversation).where(AIConversation.id == conversation_id)
        result = await self.session.execute(stmt)
        conv = result.scalar_one_or_none()
        if conv:
            conv.updated_at = datetime.now(timezone.utc)
            await self.session.commit()

    async def delete_conversation(
        self,
        conversation_id: UUID,
        user_id: UUID,
    ) -> bool:
        stmt = select(AIConversation).where(
            AIConversation.id == conversation_id,
            AIConversation.user_id == user_id,
        )
        result = await self.session.execute(stmt)
        conv = result.scalar_one_or_none()
        if not conv:
            return False
        await self.session.delete(conv)
        await self.session.commit()
        return True

    # --- Message CRUD ---

    async def add_message(
        self,
        conversation_id: UUID,
        role: str,
        content: str,
        artifacts: Optional[dict] = None,
        input_method: str = "text",
    ) -> AIMessage:
        msg = AIMessage(
            conversation_id=conversation_id,
            role=role,
            content=content,
            artifacts=artifacts,
            input_method=input_method,
        )
        self.session.add(msg)
        await self.session.commit()
        await self.session.refresh(msg)
        return msg

    async def get_messages(
        self,
        conversation_id: UUID,
    ) -> Sequence[AIMessage]:
        stmt = (
            select(AIMessage)
            .where(AIMessage.conversation_id == conversation_id)
            .order_by(AIMessage.created_at.asc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
