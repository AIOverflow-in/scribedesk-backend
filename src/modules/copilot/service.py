import asyncio
import time
import uuid
from typing import AsyncGenerator, Optional

from src.agent.graph import agent_app
from src.content.prompts.chat import ChatPrompts
from src.core.logging import get_logger
from src.dependencies.ai import get_fast_llm_service
from src.infrastructure.persistence.postgres.repos.ai_conversations_repo import AIConversationsRepository
from src.infrastructure.persistence.postgres.repos.patients_repo import PatientsRepository
from src.infrastructure.persistence.postgres.repos.sessions_repo import SessionsRepository
from src.infrastructure.persistence.redis.pubsub import PubSubManager
from src.modules.copilot.builder import ChatStateBuilder
from src.modules.copilot.handlers import ChatEventHandler
from src.modules.copilot.helpers import format_chunk
from src.schemas.api.chat import ChatSummary, ConversationResponse, MessageItem, StreamChunk
from src.schemas.features.copilot import ChatTitleResponse, PatientInfo, SessionInfo

logger = get_logger(__name__)


class ChatService:
    def __init__(
        self,
        ai_conversations_repo: AIConversationsRepository,
        sessions_repo: SessionsRepository,
        patients_repo: PatientsRepository,
        pubsub_manager: PubSubManager,
    ):
        self.ai_conversations_repo = ai_conversations_repo
        self.sessions_repo = sessions_repo
        self.patients_repo = patients_repo
        self.pubsub_manager = pubsub_manager
        self.llm_service = get_fast_llm_service()

    # --- Main stream ---

    async def chat_stream(
        self,
        user_id: uuid.UUID,
        conversation_id: Optional[uuid.UUID],
        message: str,
        session_id: Optional[uuid.UUID] = None,
        patient_id: Optional[uuid.UUID] = None,
    ) -> AsyncGenerator[str, None]:
        start_time = time.time()
        is_new = conversation_id is None

        try:
            conversation = await self._resolve_conversation(
                user_id, conversation_id, session_id, patient_id,
            )

            if is_new:
                yield format_chunk(StreamChunk(
                    type="metadata",
                    metadata_type="conversation_created",
                    data={"conversation_id": str(conversation.id)},
                ))

            await self._save_user_message(conversation.id, message)

            history = await self.ai_conversations_repo.get_messages(conversation.id)
            session_context, patient_context = await self._load_context(conversation, user_id)

            state = await ChatStateBuilder.build_state(
                user_id=str(user_id),
                conversation_id=str(conversation.id),
                history_messages=history[:-1] if len(history) > 1 else [],
                current_message=history[-1] if history else None,
                session_context=session_context.model_dump() if session_context else None,
                patient_context=patient_context.model_dump() if patient_context else None,
            )

            full_response, citations = "", None

            async for event in agent_app.astream_events(state, version="v2"):
                chunk = ChatEventHandler.handle_event(event)
                if not chunk:
                    continue
                yield format_chunk(chunk)
                if chunk.content:
                    full_response += chunk.content
                elif chunk.type == "metadata" and chunk.metadata_type == "citations":
                    citations = chunk.data

            if full_response:
                artifacts = {"citations": citations} if citations else None
                await self.ai_conversations_repo.add_message(
                    conversation_id=conversation.id,
                    role="assistant",
                    content=full_response,
                    input_method="text",
                    artifacts=artifacts,
                )
                await self.ai_conversations_repo.update_timestamp(conversation.id)

            if is_new:
                asyncio.create_task(
                    self._generate_and_notify_title(user_id, conversation.id, message),
                )

            yield format_chunk(StreamChunk(type="done"))

            duration = (time.time() - start_time) * 1000
            logger.info(f"Chat done user={user_id} conv={conversation.id} in {duration:.0f}ms")

        except Exception as e:
            logger.error(f"Chat stream error user={user_id}: {e}", exc_info=True)
            yield format_chunk(StreamChunk(type="error", error=str(e)))

    # --- Conversation CRUD ---

    async def list_conversations(
        self,
        user_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
        session_id: Optional[uuid.UUID] = None,
    ) -> tuple[list[ChatSummary], int]:
        conversations, total = await self.ai_conversations_repo.list_conversations(
            user_id=user_id, page=page, page_size=page_size, session_id=session_id,
        )
        return [ChatSummary.model_validate(c) for c in conversations], total

    async def get_conversation(
        self,
        user_id: uuid.UUID,
        conversation_id: uuid.UUID,
    ) -> Optional[ConversationResponse]:
        conversation = await self.ai_conversations_repo.get_conversation(
            conversation_id, user_id,
        )
        if not conversation:
            return None

        messages = await self.ai_conversations_repo.get_messages(conversation.id)
        return ConversationResponse(
            **{k: getattr(conversation, k) for k in
               ["id", "title", "is_title_generated", "session_id", "patient_id",
                "created_at", "updated_at"]},
            messages=[MessageItem.model_validate(m) for m in messages],
        )

    async def delete_conversation(
        self,
        user_id: uuid.UUID,
        conversation_id: uuid.UUID,
    ) -> bool:
        return await self.ai_conversations_repo.delete_conversation(
            conversation_id, user_id,
        )

    # --- Internal pipeline steps ---

    async def _resolve_conversation(
        self,
        user_id: uuid.UUID,
        conversation_id: Optional[uuid.UUID],
        session_id: Optional[uuid.UUID],
        patient_id: Optional[uuid.UUID],
    ):
        if conversation_id:
            conversation = await self.ai_conversations_repo.get_conversation(
                conversation_id, user_id,
            )
            if not conversation:
                raise ValueError("Conversation not found")
            return conversation

        resolved_patient_id = patient_id
        if session_id and not resolved_patient_id:
            session = await self.sessions_repo.get_by_id(session_id, user_id)
            if session and session.patient_id:
                resolved_patient_id = session.patient_id

        return await self.ai_conversations_repo.create_conversation(
            user_id=user_id, session_id=session_id, patient_id=resolved_patient_id,
        )

    async def _save_user_message(
        self,
        conversation_id: uuid.UUID,
        message: str,
    ) -> None:
        await self.ai_conversations_repo.add_message(
            conversation_id=conversation_id, role="user",
            content=message, input_method="text",
        )
        await self.ai_conversations_repo.update_timestamp(conversation_id)

    async def _load_context(
        self,
        conversation,
        user_id: uuid.UUID,
    ) -> tuple[Optional[SessionInfo], Optional[PatientInfo]]:
        if conversation.session_id:
            session = await self.sessions_repo.get_by_id(
                conversation.session_id, user_id,
            )
            if not session:
                return None, None
            return SessionInfo(
                title=session.title,
                status=session.status,
                clinical_summary=session.clinical_summary,
            ), PatientInfo.model_validate(session.patient) if session.patient else None

        if conversation.patient_id:
            patient = await self.patients_repo.get_by_id(
                conversation.patient_id, user_id,
            )
            if not patient:
                return None, None
            return None, PatientInfo.model_validate(patient)

        return None, None

    async def _generate_and_notify_title(
        self,
        user_id: uuid.UUID,
        conversation_id: uuid.UUID,
        first_message: str,
    ) -> None:
        try:
            prompt = ChatPrompts.TITLE_FROM_MESSAGE.format(message=first_message)
            response: ChatTitleResponse = await self.llm_service.generate_structured(
                system="You are a medical assistant.",
                user=prompt,
                schema=ChatTitleResponse,
            )
            title = response.title.strip()
            await self.ai_conversations_repo.update_title(conversation_id, title)
            await self.pubsub_manager.publish(
                user_id=str(user_id),
                event_type="chat_title_generated",
                data={"conv_id": str(conversation_id), "title": title},
            )
            logger.info(f"Title generated '{title}' for conversation {conversation_id}")
        except Exception as e:
            logger.error(f"Title generation failed for conversation {conversation_id}: {e}")
