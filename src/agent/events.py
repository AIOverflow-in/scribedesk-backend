from typing import Any

from langchain_core.callbacks.manager import adispatch_custom_event
from langchain_core.runnables import RunnableConfig


class EventEmitter:
    def __init__(self, config: RunnableConfig):
        self.config = config

    async def emit_status(self, message: str):
        await adispatch_custom_event(
            "status_update",
            {"msg": message},
            config=self.config,
        )

    async def emit_artifact(self, type_: str, data: Any):
        await adispatch_custom_event(
            "artifact_update",
            {"type": type_, "data": data},
            config=self.config,
        )
