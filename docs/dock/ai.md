This file is a merged representation of a subset of the codebase, containing specifically included files, combined into a single document by Repomix.

# File Summary

## Purpose
This file contains a packed representation of a subset of the repository's contents that is considered the most important context.
It is designed to be easily consumable by AI systems for analysis, code review,
or other automated processes.

## File Format
The content is organized as follows:
1. This summary section
2. Repository information
3. Directory structure
4. Repository files (if enabled)
5. Multiple file entries, each consisting of:
  a. A header with the file path (## File: path/to/file)
  b. The full contents of the file in a code block

## Usage Guidelines
- This file should be treated as read-only. Any changes should be made to the
  original repository files, not this packed version.
- When processing this file, use the file path to distinguish
  between different files in the repository.
- Be aware that this file may contain sensitive information. Handle it with
  the same level of security as you would the original repository.

## Notes
- Some files may have been excluded based on .gitignore rules and Repomix's configuration
- Binary files are not included in this packed representation. Please refer to the Repository Structure section for a complete list of file paths, including binary files
- Only files matching these patterns are included: src/agent/**/*, src/modules/copilot/**/*
- Files matching patterns in .gitignore are excluded
- Files matching default ignore patterns are excluded
- Files are sorted by Git change count (files with more changes are at the bottom)

# Directory Structure
```
src/agent/edges.py
src/agent/events.py
src/agent/graph.py
src/agent/node.py
src/agent/state.py
src/agent/tools.py
src/modules/copilot/builder.py
src/modules/copilot/handlers.py
src/modules/copilot/helpers.py
src/modules/copilot/service.py
```

# Files

## File: src/agent/edges.py
```python
"""Conditional edges for the medical copilot graph."""

from typing import Literal

from langchain_core.messages import AIMessage
from langgraph.graph import END

from src.agent.state import AgentState


def should_call_tools(state: AgentState) -> Literal["tools", "__end__"]:
    """
    Conditional edge: check if the last message has tool calls.

    Routes to:
    - "tools" if the last message is an AI message with tool_calls
    - "__end__" otherwise

    This enables the tool loop:
    agent → (has tools?) → tools → agent → (no tools?) → end
    """
    messages = state["messages"]

    if messages and isinstance(messages[-1], AIMessage):
        if messages[-1].tool_calls:
            return "tools"

    return END
```

## File: src/agent/events.py
```python
"""Event emitter for custom LangChain events in agent tools."""

from typing import Any
from langchain_core.callbacks.manager import adispatch_custom_event
from langchain_core.runnables import RunnableConfig


class EventEmitter:
    """
    Emits custom events from agent tools that can be captured in LangGraph streaming.

    Usage in tools:
        @tool
        async def my_tool(query: str, config: RunnableConfig) -> str:
            emitter = EventEmitter(config)
            await emitter.emit_status("Searching...")
            await emitter.emit_artifact("citations", {"sources": [...]})
            return "response text"
    """

    def __init__(self, config: RunnableConfig):
        self.config = config

    async def emit_status(self, message: str):
        """Emits a status update message to the UI."""
        await adispatch_custom_event(
            "status_update",
            {"msg": message},
            config=self.config
        )

    async def emit_artifact(self, type_: str, data: Any):
        """Emits a structured artifact payload (citations, widgets, etc.)."""
        await adispatch_custom_event(
            "artifact_update",
            {"type": type_, "data": data},
            config=self.config
        )
```

## File: src/modules/copilot/builder.py
```python
"""State builder for LangGraph agent."""

from typing import List

from langchain_core.messages import HumanMessage, AIMessage

from src.agent.state import AgentState


class ChatStateBuilder:
    """Builds LangGraph state from database history and new input."""

    @staticmethod
    async def build_state(
        user_id: str,
        conversation_id: str,
        history_messages: List,
        current_message
    ) -> AgentState:
        """
        Build LangGraph state from conversation history and current message.

        Args:
            user_id: User ID as string
            conversation_id: Conversation ID as string
            history_messages: List of previous AIMessages (excludes current)
            current_message: The current user message we just saved (with attachments)

        Returns:
            AgentState ready for LangGraph
        """
        # Convert history messages to LangChain format
        lc_messages = ChatStateBuilder._build_langchain_history(history_messages)

        # Add current message
        if current_message:
            if current_message.attachments:
                lc_messages.append(ChatStateBuilder._build_message_with_attachments(
                    current_message.content,
                    current_message.attachments
                ))
            else:
                lc_messages.append(HumanMessage(content=current_message.content))

        return {
            "messages": lc_messages,
            "user_id": user_id,
            "conversation_id": conversation_id
        }

    @staticmethod
    def _build_langchain_history(messages: List) -> List:
        """
        Convert database AIMessages to LangChain messages with their attachments.

        Each message includes its own attachments for full context.
        """
        lc_messages = []

        for msg in messages:
            if msg.role == "user":
                # Check if this message has attachments
                if hasattr(msg, 'attachments') and msg.attachments:
                    lc_messages.append(ChatStateBuilder._build_message_with_attachments(
                        msg.content,
                        msg.attachments
                    ))
                else:
                    lc_messages.append(HumanMessage(content=msg.content))
            elif msg.role == "assistant":
                lc_messages.append(AIMessage(content=msg.content))

        return lc_messages

    @staticmethod
    def _build_message_with_attachments(text: str, attachments: List) -> HumanMessage:
        """
        Build a HumanMessage with text and attachment media.

        Args:
            text: User's text message
            attachments: List of Attachment objects with google_uri and content_type

        Returns:
            HumanMessage with content as list (text + media parts)
        """
        content = [{"type": "text", "text": text}]

        for attachment in attachments:
            if attachment.google_uri:
                content.append({
                    "type": "media",
                    "file_uri": attachment.google_uri,
                    "mime_type": attachment.content_type
                })

        return HumanMessage(content=content)
```

## File: src/modules/copilot/handlers.py
```python
from typing import Optional

from src.schemas.api.chat import StreamChunk


class ChatEventHandler:
    @staticmethod
    def handle_event(event: dict) -> Optional[StreamChunk]:
        kind = event.get("event")
        name = event.get("name")
        data = event.get("data", {})

        if kind == "on_custom_event":
            return ChatEventHandler._handle_custom_event(name, data)

        elif kind == "on_chat_model_stream":
            return ChatEventHandler._handle_llm_stream(event)

        elif kind == "on_tool_start":
            return ChatEventHandler._handle_tool_start(event)

        elif kind == "on_tool_end":
            return ChatEventHandler._handle_tool_end(event)

        elif kind == "on_tool_error":
            return ChatEventHandler._handle_tool_error(event)

        return None

    @staticmethod
    def _handle_llm_stream(event: dict) -> Optional[StreamChunk]:
        chunk = event.get("data", {}).get("chunk")

        if not chunk:
            return None

        content = getattr(chunk, "content", None)

        if not content:
            return None

        if isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    text = block.get("text")
                    if text:
                        return StreamChunk(type="content", content=text)

        elif isinstance(content, str):
            return StreamChunk(type="content", content=content)

        return None

    @staticmethod
    def _handle_custom_event(name: str, data: dict) -> Optional[StreamChunk]:
        if name == "status_update":
            return StreamChunk(
                type="status",
                status_message=data.get("msg")
            )

        elif name == "artifact_update":
            return StreamChunk(
                type="metadata",
                metadata_type=data.get("type"),
                data=data.get("data")
            )

        return None

    @staticmethod
    def _handle_tool_start(event: dict) -> Optional[StreamChunk]:
        name = event.get("name")

        if not name:
            return None

        return StreamChunk(
            type="tool_call",
            status_message=f"Using {name.replace('_', ' ').title()}...",
            tool_name=name
        )

    @staticmethod
    def _handle_tool_end(event: dict) -> Optional[StreamChunk]:
        name = event.get("name")

        if not name:
            return None

        output = event.get("data", {}).get("output")

        return StreamChunk(
            type="tool_call",
            status_message=f"Completed {name.replace('_', ' ').title()}",
            tool_name=name,
            data={"result": str(output) if output else None}
        )

    @staticmethod
    def _handle_tool_error(event: dict) -> Optional[StreamChunk]:
        name = event.get("name")

        return StreamChunk(
            type="error",
            status_message=f"{name} failed",
            tool_name=name
        )
```

## File: src/modules/copilot/helpers.py
```python
"""Utility functions for chat service."""

from src.schemas.api.chat import StreamChunk


def format_chunk(chunk: StreamChunk) -> str:
    """Format a StreamChunk as Server-Sent Events (SSE)."""
    return f"data: {chunk.model_dump_json(exclude_none=True)}\n\n"
```

## File: src/agent/graph.py
```python
"""LangGraph agent for medical copilot chat."""

from langgraph.graph import StateGraph

from src.agent.state import AgentState
from src.agent.node import agent_node
from src.agent.edges import should_call_tools
from src.agent.tools import tools_node


# Build the graph
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("agent", agent_node)
workflow.add_node("tools", tools_node)

# Set entry point
workflow.set_entry_point("agent")

# Add conditional edge from agent to either tools or end
workflow.add_conditional_edges(
    "agent",
    should_call_tools,
    {
        "tools": "tools",
        "__end__": "__end__",
    }
)

# Tools always go back to agent
workflow.add_edge("tools", "agent")

# Compile and export
agent_app = workflow.compile()
```

## File: src/agent/node.py
```python
"""Agent node for the medical copilot."""

from typing import Dict, Any

from langchain_core.messages import AIMessage, SystemMessage, ToolMessage

from src.content.prompts import ChatPrompts
from src.agent.state import AgentState
from src.agent.tools import AGENT_TOOLS
from src.dependencies.ai import get_smart_llm_service
from src.core.logging import get_logger

logger = get_logger(__name__)


async def agent_node(state: AgentState) -> Dict[str, Any]:
    """
    The main agent node that processes messages and decides whether to use tools.

    This node:
    1. Takes messages from state
    2. Adds system prompt if not present
    3. Binds tools to the model
    4. Invokes the model
    5. Returns the response

    The graph engine handles streaming via astream_events at the service layer.
    """
    messages = state["messages"]
    user_id = state.get("user_id", "")
    conversation_id = state.get("conversation_id", "")

    # Get the LLM service
    llm_service = get_smart_llm_service()

    # Build system prompt - only include citation instructions if web search was used
    system_content = ChatPrompts.COPILOT_SYSTEM
    if any(isinstance(m, ToolMessage) and m.name == "web_search" for m in messages):
        system_content += "\n\n" + ChatPrompts.CITATION_INSTRUCTIONS

    # Add or update system prompt
    if not messages or not isinstance(messages[0], SystemMessage):
        system_msg = SystemMessage(content=system_content)
        messages = [system_msg] + list(messages)
    else:
        messages[0] = SystemMessage(content=system_content)

    try:
        # Bind tools to the model
        model_with_tools = llm_service.model.bind_tools(AGENT_TOOLS)

        # Invoke the model
        response = await model_with_tools.ainvoke(messages)

        logger.info(f"Agent generated response for user={user_id}, conv={conversation_id}")

        return {"messages": [response]}

    except Exception as e:
        logger.error(f"Agent error for user={user_id}, conv={conversation_id}: {e}", exc_info=True)

        # Return a fallback message
        error_msg = AIMessage(content="I apologize, but I encountered an error. Please try again.")
        return {"messages": [error_msg]}
```

## File: src/agent/state.py
```python
"""Agent state for LangGraph chat agent."""

from typing import Annotated, List, TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph import add_messages


class AgentState(TypedDict):
    """
    The state for the medical copilot chat agent.
    """
    # Conversation history (messages list with automatic append reducer)
    messages: Annotated[List[BaseMessage], add_messages]

    # User and conversation IDs for context
    user_id: str
    conversation_id: str
```

## File: src/modules/copilot/service.py
```python
"""Chat service for AI copilot conversations."""

import time
import uuid
import asyncio
from typing import AsyncGenerator, List, Optional

from src.core.logging import get_logger
from src.infrastructure.persistence.postgres.repos.ai_conversations_repo import AIConversationsRepository
from src.infrastructure.persistence.postgres.repos.attachments_repo import AttachmentsRepository
from src.infrastructure.persistence.redis.pubsub import PubSubManager
from src.infrastructure.persistence.s3.client import S3Client
from src.dependencies.ai import get_fast_llm_service
from src.schemas.api.chat import StreamChunk, MessageAttachment
from src.schemas.features.copilot import ChatTitleResponse
from src.content.prompts.chat import ChatPrompts
from src.agent.graph import agent_app
from src.modules.copilot.builder import ChatStateBuilder
from src.modules.copilot.handlers import ChatEventHandler
from src.modules.copilot.helpers import format_chunk
from src.modules.attachments.service import AttachmentsService

logger = get_logger(__name__)


class ChatService:
    """
    Orchestrates AI chat conversations.
    Thin orchestration layer - delegates to builder, handlers, helpers.
    """

    def __init__(
        self,
        ai_conversations_repo: AIConversationsRepository,
        attachments_repo: AttachmentsRepository,
        pubsub_manager: PubSubManager,
        s3_client: S3Client,
        attachments_service: AttachmentsService,
    ):
        self.ai_conversations_repo = ai_conversations_repo
        self.attachments_repo = attachments_repo
        self.pubsub_manager = pubsub_manager
        self.s3_client = s3_client
        self.attachments_service = attachments_service
        self.llm_service = get_fast_llm_service()

    # --- Public API ---

    async def chat_stream(
        self,
        user_id: uuid.UUID,
        conversation_id: Optional[uuid.UUID],
        message: str,
        attachment_ids: List[uuid.UUID]
    ) -> AsyncGenerator[str, None]:
        """
        Stream a chat response from the AI agent.

        Args:
            user_id: User ID
            conversation_id: Existing conversation ID, or None for new chat
            message: User message text
            attachment_ids: File attachment IDs to include

        Yields:
            SSE-formatted chunks
        """
        start_time = time.time()
        is_new_conversation = conversation_id is None

        try:
            # 1. Get or create conversation
            conversation = await self._get_or_create_conversation(user_id, conversation_id)

            # 2. Emit conversation_id metadata for new conversations
            if is_new_conversation:
                yield format_chunk(StreamChunk(
                    type="metadata",
                    metadata_type="conversation_created",
                    data={"conversation_id": str(conversation.id)}
                ))

            # 3. Save user message and get message_id
            user_message = await self.ai_conversations_repo.add_message(
                conversation_id=conversation.id,
                role="user",
                content=message,
                input_method="text"
            )

            # Update conversation's updated_at timestamp
            await self.ai_conversations_repo.update_timestamp(conversation.id)

            # 4. Link attachments to the user message
            if attachment_ids:
                await self._link_attachments(attachment_ids, user_message.id)

            # 5. Fetch conversation history (includes the user message we just saved)
            history = await self.ai_conversations_repo.get_messages(conversation.id)

            # 5.5. Refresh expired Google URIs before building state
            await self._refresh_expired_google_uris(history)

            # 6. Split: previous conversation vs current message
            history_except_last = history[:-1] if len(history) > 1 else []
            current_user_message = history[-1] if history else None

            # 7. Build LangGraph state
            state = await ChatStateBuilder.build_state(
                user_id=str(user_id),
                conversation_id=str(conversation.id),
                history_messages=history_except_last,
                current_message=current_user_message
            )

            # 8. Stream agent response
            full_response = ""
            citations = None
            async for event in agent_app.astream_events(state, version="v2"):
                chunk = ChatEventHandler.handle_event(event)
                if chunk:
                    yield format_chunk(chunk)
                    if chunk.content:
                        full_response += chunk.content
                    # Accumulate citations from metadata events
                    elif chunk.type == "metadata" and chunk.metadata_type == "citations":
                        citations = chunk.data

            # 9. Save assistant message with artifacts
            if full_response:
                await self.ai_conversations_repo.add_message(
                    conversation_id=conversation.id,
                    role="assistant",
                    content=full_response,
                    input_method="text",
                    artifacts={"citations": citations} if citations else None
                )

                # Update conversation's updated_at timestamp
                await self.ai_conversations_repo.update_timestamp(conversation.id)

            # 10. Trigger title generation in background (only for new conversations)
            if is_new_conversation:
                asyncio.create_task(
                    self._generate_and_notify_title(user_id, conversation.id, message)
                )

            # 11. Send done signal
            yield format_chunk(StreamChunk(type="done"))

            duration = (time.time() - start_time) * 1000
            logger.info(f"Chat completed for user {user_id}, conv {conversation.id} in {duration:.0f}ms")

        except Exception as e:
            logger.error(f"Chat stream error for user {user_id}: {e}", exc_info=True)
            yield format_chunk(StreamChunk(type="error", error=str(e)))

    async def list_conversations(
        self,
        user_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[list, int]:
        """
        List conversations for a user with pagination.

        Returns:
            (conversations, total_count)
        """
        conversations, total = await self.ai_conversations_repo.list_conversations(
            user_id=user_id,
            page=page,
            page_size=page_size
        )

        # Format for response
        result = []
        for conv in conversations:
            result.append({
                "id": conv.id,
                "title": conv.title,
                "is_title_generated": conv.is_title_generated,
                "created_at": conv.created_at,
                "updated_at": conv.updated_at
            })

        return result, total

    async def get_conversation(
        self,
        user_id: uuid.UUID,
        conversation_id: uuid.UUID
    ) -> Optional[dict]:
        """
        Get a single conversation with messages and attachment presigned URLs.

        Returns:
            Conversation dict with messages (including attachments), or None if not found
        """
        conversation = await self.ai_conversations_repo.get_conversation(conversation_id, user_id)

        if not conversation:
            return None

        # Get messages with attachments
        messages = await self.ai_conversations_repo.get_messages(conversation.id)

        # Format messages with attachment presigned URLs and artifacts
        formatted_messages = []
        for msg in messages:
            attachment_list = []
            if msg.attachments:
                attachment_list = await self._build_message_attachments(msg.attachments)

            formatted_messages.append({
                "id": msg.id,
                "role": msg.role,
                "content": msg.content,
                "created_at": msg.created_at,
                "attachments": attachment_list,
                "artifacts": msg.artifacts
            })

        return {
            "id": conversation.id,
            "title": conversation.title,
            "is_title_generated": conversation.is_title_generated,
            "created_at": conversation.created_at,
            "updated_at": conversation.updated_at,
            "messages": formatted_messages
        }

    async def delete_conversation(
        self,
        user_id: uuid.UUID,
        conversation_id: uuid.UUID
    ) -> bool:
        """
        Delete a conversation.

        Messages cascade delete. Attachments become orphaned (message_id = NULL)
        and will be cleaned up by cron job + S3 deletion.

        Returns:
            True if deleted, False if not found
        """
        return await self.ai_conversations_repo.delete_conversation(conversation_id, user_id)

    # --- Internal Helpers ---

    async def _get_or_create_conversation(
        self,
        user_id: uuid.UUID,
        conversation_id: Optional[uuid.UUID]
    ):
        """Get existing conversation or create a new one."""
        if conversation_id:
            conversation = await self.ai_conversations_repo.get_conversation(conversation_id, user_id)
            if not conversation:
                raise ValueError("Conversation not found")
            return conversation
        else:
            return await self.ai_conversations_repo.create_conversation(user_id)

    async def _link_attachments(
        self,
        attachment_ids: List[uuid.UUID],
        message_id: uuid.UUID,
    ):
        """Link attachments to a message."""
        for attachment_id in attachment_ids:
            await self.attachments_repo.link_to_message(attachment_id, message_id)

    async def _refresh_expired_google_uris(
        self,
        messages: List
    ):
        """
        Refresh expired Google URIs for all attachments in the messages.

        Google URIs expire after 48 hours, so we refresh those older than 40 hours.
        This ensures the LLM can access attachments when building conversation history.
        """
        for msg in messages:
            if hasattr(msg, 'attachments') and msg.attachments:
                for attachment in msg.attachments:
                    if attachment.google_uri:
                        await self.attachments_service.refresh_google_uri_if_expired(attachment)

    async def _generate_and_notify_title(
        self,
        user_id: uuid.UUID,
        conversation_id: uuid.UUID,
        first_message: str
    ):
        """
        Generate title in background and notify via WebSocket.

        Runs as a background task after chat completes.
        """
        try:
            # 1. Generate title using LLM with structured output
            title = await self._generate_title(first_message)

            # 2. Update database
            await self.ai_conversations_repo.update_title(conversation_id, title)

            # 3. Publish to WebSocket
            await self.pubsub_manager.publish(
                user_id=str(user_id),
                event_type="chat_title_generated",
                data={"conv_id": str(conversation_id), "title": title}
            )

            logger.info(f"Generated and notified title '{title}' for conversation {conversation_id}")

        except Exception as e:
            logger.error(f"Failed to generate title for conversation {conversation_id}: {e}")

    async def _generate_title(
        self,
        first_message: str
    ) -> str:
        """
        Generate a title for a conversation based on the first message.

        Args:
            first_message: First user message

        Returns:
            Generated title
        """
        prompt = ChatPrompts.TITLE_FROM_MESSAGE.format(message=first_message)
        response: ChatTitleResponse = await self.llm_service.generate_structured(
            system="You are a medical assistant.",
            user=prompt,
            schema=ChatTitleResponse
        )
        return response.title.strip()

    async def _build_message_attachments(
        self,
        attachments: List
    ) -> List[MessageAttachment]:
        """
        Build MessageAttachment objects with presigned S3 URLs.

        Args:
            attachments: List of Attachment models from database

        Returns:
            List of MessageAttachment with presigned URLs
        """
        attachment_list = []

        for att in attachments:
            presigned_url = await self.s3_client.generate_presigned_url(att.s3_key)
            attachment_list.append(MessageAttachment(
                id=att.id,
                file_name=att.file_name,
                content_type=att.content_type,
                url=presigned_url
            ))

        return attachment_list
```

## File: src/agent/tools.py
```python
"""Tools for the medical copilot agent."""

from typing import Dict, Any
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig
from langgraph.prebuilt import ToolNode

from src.core.config import settings
from src.core.constants import get_medical_sites
from src.dependencies.infra import get_brave_client
from src.agent.events import EventEmitter


@tool
async def web_search(query: str, config: RunnableConfig) -> str:
    """
    Search medical websites for health information.

    Use this when the user asks about:
    - Medical conditions, diseases, or symptoms
    - Medications, treatments, or procedures
    - Health guidelines or recommendations

    Args:
        query: The search query
        config: RunnableConfig for emitting custom events

    Returns:
        Formatted search results as a string
    """
    emitter = EventEmitter(config)
    await emitter.emit_status(f"Searching for '{query}'")

    client = get_brave_client()
    sites = get_medical_sites(region=settings.DEFAULT_SEARCH_REGION, purpose="general")
    results = await client.search(query, sites=sites)

    if not results:
        return "No results found."

    # Emit citations as artifact with full metadata (all results)
    citations_data = {
        "count": len(results),
        "items": [
            {
                "id": i + 1,
                "name": r.profile_name,
                "title": r.title,
                "description": r.description,
                "url": r.url,
                "domain": r.hostname,
                "favicon": r.profile_img
            }
            for i, r in enumerate(results)
        ]
    }
    await emitter.emit_artifact("citations", citations_data)

    # Format results for LLM with index, title, url, description, and extra snippets
    formatted = []
    for i, result in enumerate(results, 1):
        # Build the result entry
        entry = f"{i}. {result.title}\n   URL: {result.url}\n   {result.description}"

        # Add extra snippets if available
        if result.extra_snippets:
            snippets_text = "\n   ".join(f"- {snippet}" for snippet in result.extra_snippets)
            entry += f"\n   Additional context:\n   {snippets_text}"

        formatted.append(entry)

    return "\n\n".join(formatted)


# Export all tools as a list
AGENT_TOOLS = [web_search]

# Create the tool execution node
tools_node = ToolNode(AGENT_TOOLS)
```
