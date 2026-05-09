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
            return StreamChunk(type="status", status_message=data.get("msg"))
        elif name == "artifact_update":
            return StreamChunk(
                type="metadata",
                metadata_type=data.get("type"),
                data=data.get("data"),
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
            tool_name=name,
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
            data={"result": str(output) if output else None},
        )

    @staticmethod
    def _handle_tool_error(event: dict) -> Optional[StreamChunk]:
        name = event.get("name")
        return StreamChunk(
            type="error",
            status_message=f"{name} failed",
            tool_name=name,
        )
