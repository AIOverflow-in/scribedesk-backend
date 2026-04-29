"""Deepgram real-time transcription — buffered proxy session."""

import asyncio
import threading
from collections import deque
from typing import Awaitable, Callable

from deepgram import DeepgramClient as DGClient
from deepgram.core.events import EventType

from src.core.config import settings
from src.core.logging import get_logger

logger = get_logger(__name__)

BUFFER_SIZE = settings.DEEPGRAM_CHUNK_SIZE  # number of is_final segments per flush


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
            logger.debug(f"Received non-transcript message: {type(message).__name__}")
            return

        transcript = message.channel.alternatives[0].transcript
        is_final = getattr(message, "is_final", False)
        speech_final = getattr(message, "speech_final", False)

        if not transcript or not is_final:
            return

        logger.info(f"[IS FINAL] {transcript}")
        self._buffer.append(transcript)
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
        logger.info("Opening Deepgram connection...")
        client = DGClient(api_key=settings.DEEPGRAM_API_KEY)

        self._connection_cm = client.listen.v1.connect(
            model=settings.DEEPGRAM_MODEL,
            encoding="linear16",
            sample_rate=16000,
            channels=1,
        )
        logger.info("Entering Deepgram connection context...")
        self._connection = self._connection_cm.__enter__()
        logger.info("Deepgram connection established, registering handlers...")
        self._connection.on(EventType.OPEN, lambda _: logger.info("Deepgram connection opened"))
        self._connection.on(EventType.MESSAGE, self._handle_message)
        self._connection.on(EventType.CLOSE, lambda _: logger.info("Deepgram connection closed"))
        self._connection.on(EventType.ERROR, lambda e: logger.error(f"Deepgram error: {e}"))

        def _listen():
            try:
                logger.info("Deepgram listener thread started")
                self._connection.start_listening()
            except Exception as e:
                logger.error(f"Deepgram listener thread error: {e}", exc_info=True)
            finally:
                logger.info("Deepgram listener thread ended")

        threading.Thread(target=_listen, daemon=True).start()
        return self

    def __exit__(self, *args):
        self.flush_remaining()
        if self._connection_cm:
            self._connection_cm.__exit__(*args)


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
