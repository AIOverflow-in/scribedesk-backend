"""Deepgram real-time transcription — buffered proxy session."""

import asyncio
from collections import deque
from typing import Awaitable, Callable

from deepgram import DeepgramClient as DGClient

from src.core.config import settings
from src.core.logging import get_logger

logger = get_logger(__name__)

BUFFER_SIZE = settings.DEEPGRAM_CHUNK_SIZE


class DeepgramTranscriptionSession:
    """
    Manages a single real-time transcription session.

    Buffers ``is_final`` events from Deepgram and flushes them to an async
    callback once the buffer reaches the configured threshold.
    """

    def __init__(
        self,
        on_flush: Callable[[str], Awaitable[None]],
        buffer_size: int = BUFFER_SIZE,
    ):
        self._on_flush = on_flush
        self._buffer_size = buffer_size
        self._buffer: deque[str] = deque()
        self._connection = None
        self._loop = asyncio.get_event_loop()

    # --- Internal ---

    def _handle_message(self, message) -> None:
        if not (
            hasattr(message, "channel")
            and hasattr(message.channel, "alternatives")
        ):
            return

        transcript = message.channel.alternatives[0].transcript
        is_final = getattr(message, "is_final", False)

        if not transcript or not is_final:
            return

        logger.debug(f"[IS FINAL] {transcript}")
        self._buffer.append(transcript)

        if len(self._buffer) >= self._buffer_size:
            self._flush()

    def _flush(self) -> None:
        if not self._buffer:
            return

        chunk = " ".join(self._buffer)
        self._buffer.clear()

        logger.info(f"Flushing transcript chunk ({self._buffer_size} segments)")

        asyncio.run_coroutine_threadsafe(
            self._on_flush(chunk),
            self._loop,
        )

    # --- Public API ---

    def send_audio(self, data: bytes) -> None:
        """Forward raw audio bytes to Deepgram."""
        if self._connection:
            self._connection.send_media(data)

    def flush_remaining(self) -> None:
        """Flush any buffered segments (call on session end)."""
        self._flush()

    # --- Context manager ---

    def __enter__(self):
        client = DGClient(api_key=settings.DEEPGRAM_API_KEY)

        options = {
            "model": settings.DEEPGRAM_MODEL,
            "encoding": "linear16",
            "sample_rate": 16000,
            "channels": 1,
        }

        self._connection = client.listen.v1.connect(options)
        self._connection.on("Open", lambda _: logger.info("Deepgram connection opened"))
        self._connection.on("Message", self._handle_message)
        self._connection.on("Close", lambda _: logger.info("Deepgram connection closed"))
        self._connection.on("Error", lambda e: logger.error(f"Deepgram error: {e}"))

        self._connection.__enter__()
        return self

    def __exit__(self, *args):
        self.flush_remaining()
        if self._connection:
            self._connection.__exit__(*args)


class DeepgramClient:
    """Factory for Deepgram transcription sessions."""

    def create_session(
        self,
        on_flush: Callable[[str], Awaitable[None]],
        buffer_size: int = BUFFER_SIZE,
    ) -> DeepgramTranscriptionSession:
        return DeepgramTranscriptionSession(
            on_flush=on_flush,
            buffer_size=buffer_size,
        )
