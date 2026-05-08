"""Deepgram real-time transcription — buffered proxy session."""

import asyncio
import threading
import time
from typing import Awaitable, Callable, Optional

from deepgram import DeepgramClient as DGClient
from deepgram.core.events import EventType

from src.core.config import settings
from src.core.logging import get_logger

logger = get_logger(__name__)

BUFFER_SIZE = settings.DEEPGRAM_CHUNK_SIZE
KEEPALIVE_INTERVAL = 5
KEEPALIVE_IDLE_THRESHOLD = 3


class DeepgramTranscriptionSession:
    """
    Manages a single real-time transcription session.

    Buffers ``is_final`` events from Deepgram and flushes them to an async
    callback once the buffer reaches the configured threshold.

    Each individual ``is_final`` fragment is also forwarded progressively via
    the optional ``on_intermediate`` callback so the frontend can display
    live-updating text without waiting for a full flush.

    Automatically sends KeepAlive messages to Deepgram every 5 seconds
    when no audio is being streamed.
    """

    def __init__(
        self,
        on_flush: Callable[[str], Awaitable[None]],
        on_intermediate: Optional[Callable[[str], Awaitable[None]]] = None,
        buffer_size: int = BUFFER_SIZE,
    ):
        self._on_flush = on_flush
        self._on_intermediate = on_intermediate
        self._buffer_size = buffer_size
        self._buffer: list[str] = []
        self._lock = threading.Lock()
        self._connection = None
        self._connection_cm = None
        self._loop = None
        self._last_media_at = 0.0
        self._keepalive_stop = threading.Event()

    # --- Internal ---

    def _keepalive_loop(self) -> None:
        while not self._keepalive_stop.is_set():
            self._keepalive_stop.wait(KEEPALIVE_INTERVAL)
            if self._keepalive_stop.is_set():
                break
            idle = time.time() - self._last_media_at
            if idle >= KEEPALIVE_IDLE_THRESHOLD and self._connection:
                try:
                    self._connection.send_message({"type": "KeepAlive"})
                except Exception as e:
                    logger.debug(f"KeepAlive send error: {e}")

    def _handle_message(self, message) -> None:
        try:
            if not (
                hasattr(message, "channel")
                and hasattr(message.channel, "alternatives")
            ):
                return

            transcript = message.channel.alternatives[0].transcript
            is_final = getattr(message, "is_final", False)

            if not transcript or not is_final:
                return

            chunk_to_flush: Optional[str] = None

            with self._lock:
                self._buffer.append(transcript)
                if len(self._buffer) >= self._buffer_size:
                    chunk_to_flush = " ".join(self._buffer)
                    self._buffer.clear()

            if self._on_intermediate:
                asyncio.run_coroutine_threadsafe(
                    self._on_intermediate(transcript),
                    self._loop,
                )

            if chunk_to_flush:
                logger.info(f"Flushing {self._buffer_size} segments: {chunk_to_flush[:60]}...")
                asyncio.run_coroutine_threadsafe(
                    self._on_flush(chunk_to_flush),
                    self._loop,
                )
        except Exception as e:
            logger.error(f"Deepgram message handler error: {e}", exc_info=True)

    # --- Public API ---

    def send_audio(self, data: bytes) -> None:
        """Forward raw audio bytes to Deepgram."""
        self._last_media_at = time.time()
        if self._connection:
            self._connection.send_media(data)

    async def flush_remaining(self) -> None:
        """Flush any buffered segments and wait for completion.

        Call this *after* the audio loop ends but *before* finalising session
        timing so that the stopped event doesn't race with the last flush.
        """
        with self._lock:
            if not self._buffer:
                return
            chunk = " ".join(self._buffer)
            self._buffer.clear()

        logger.info(f"Flushing final {len(chunk)} chars")
        await self._on_flush(chunk)

    # --- Context manager ---

    def __enter__(self):
        self._loop = asyncio.get_running_loop()

        client = DGClient(api_key=settings.DEEPGRAM_API_KEY)

        self._connection_cm = client.listen.v1.connect(
            model=settings.DEEPGRAM_MODEL,
            encoding="linear16",
            sample_rate=16000,
            channels=1,
            punctuate=True,
            interim_results=True,
            utterance_end_ms=1000,
        )
        self._connection = self._connection_cm.__enter__()
        self._connection.on(EventType.MESSAGE, self._handle_message)
        self._connection.on(EventType.CLOSE, lambda _: logger.info("Deepgram connection closed"))
        self._connection.on(EventType.ERROR, lambda e: logger.error(f"Deepgram error: {e}"))

        def _listen():
            try:
                self._connection.start_listening()
            except Exception as e:
                logger.error(f"Deepgram listener thread error: {e}", exc_info=True)

        threading.Thread(target=_listen, daemon=True).start()
        threading.Thread(target=self._keepalive_loop, daemon=True).start()
        return self

    def __exit__(self, *args):
        self._keepalive_stop.set()
        if self._connection_cm:
            self._connection_cm.__exit__(*args)


class DeepgramClient:
    """Factory for Deepgram transcription sessions."""

    def create_session(
        self,
        on_flush: Callable[[str], Awaitable[None]],
        on_intermediate: Optional[Callable[[str], Awaitable[None]]] = None,
        buffer_size: int = BUFFER_SIZE,
    ) -> DeepgramTranscriptionSession:
        return DeepgramTranscriptionSession(
            on_flush=on_flush,
            on_intermediate=on_intermediate,
            buffer_size=buffer_size,
        )
