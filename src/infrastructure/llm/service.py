from typing import Type, AsyncGenerator, List, Union, TypeVar, Optional
from pydantic import BaseModel
from langchain_core.messages import SystemMessage, HumanMessage, BaseMessage
from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import Runnable
from src.utils.timer import measure_time
from src.core.logging import get_logger

logger = get_logger(__name__)

T = TypeVar("T", bound=BaseModel)

class LLMService:
    """
    Lean wrapper for LLM operations.
    Handles message preparation, timing, and resilient execution.
    """

    def __init__(
        self, 
        model: BaseChatModel,
        fallback_model: Optional[BaseChatModel] = None,
        max_retries: int = 3
    ):
        self.model = model
        self.fallback_model = fallback_model
        self.max_retries = max_retries

    def _prepare_messages(self, system: str, user: Union[str, List[BaseMessage]]) -> List[BaseMessage]:
        """Converts inputs into LangChain's required List[BaseMessage] format."""
        messages: List[BaseMessage] = [SystemMessage(content=system)]
        if isinstance(user, str):
            messages.append(HumanMessage(content=user))
        elif isinstance(user, list):
            messages.extend(user)
        return messages

    def _build_runnable(self, schema: Optional[Type[T]] = None) -> Runnable:
        """
        Internal helper to construct a resilient chain.
        Applies structured output, retries, and fallbacks in the correct order.
        """
        # 1. Apply schema if provided (must be done on raw model)
        primary = self.model.with_structured_output(schema) if schema else self.model
        
        # 2. Add native retry for transient errors
        runnable = primary.with_retry(stop_after_attempt=self.max_retries)

        # 3. Add fallback model if configured
        if self.fallback_model:
            fallback = self.fallback_model.with_structured_output(schema) if schema else self.fallback_model
            runnable = runnable.with_fallbacks([
                fallback.with_retry(stop_after_attempt=self.max_retries)
            ])
            
        return runnable

    @measure_time("LLM Generate Text")
    async def generate_text(self, system: str, user: Union[str, List[BaseMessage]]) -> str:
        """Standard text generation with resilience."""
        messages = self._prepare_messages(system, user)
        runnable = self._build_runnable()
        response = await runnable.ainvoke(messages)
        return response.content

    @measure_time("LLM Structured Output")
    async def generate_structured(
        self,
        system: str,
        user: Union[str, List[BaseMessage]],
        schema: Type[T]
    ) -> T:
        """Force Pydantic output with resilience."""
        messages = self._prepare_messages(system, user)
        runnable = self._build_runnable(schema=schema)
        return await runnable.ainvoke(messages)

    async def stream_text(
        self,
        system: str,
        user: Union[str, List[BaseMessage]]
    ) -> AsyncGenerator[str, None]:
        """
        Stream text chunks.
        Note: Retries are disabled for streams to avoid duplicate partial output.
        Fallbacks are still supported for connection failures.
        """
        messages = self._prepare_messages(system, user)
        
        runnable = self.model
        if self.fallback_model:
            runnable = runnable.with_fallbacks([self.fallback_model])
            
        async for chunk in runnable.astream(messages):
            if chunk.content:
                yield chunk.content