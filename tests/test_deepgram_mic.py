import threading
import queue
import pyaudio
from deepgram import DeepgramClient
from deepgram.core.events import EventType
from src.core.config import settings

# ~64ms per chunk at 16kHz — small enough to stay responsive,
# large enough not to overwhelm the WebSocket with tiny packets.
CHUNK_SIZE = 1024
SAMPLE_RATE = 16000
CHANNELS = 1


def main():
    try:
        deepgram: DeepgramClient = DeepgramClient(api_key=settings.DEEPGRAM_API_KEY)

        # Gate: audio capture won't start sending until the WS is truly open.
        connection_ready = threading.Event()

        # Accumulate is_final fragments; flush the joined sentence on speech_final.
        sentence_buffer: list[str] = []

        # Pre-connection audio buffer: captures audio during WS handshake so
        # the first few seconds of speech aren't silently dropped.
        pre_buffer: queue.Queue = queue.Queue()
        buffering = True  # flipped to False once connection is ready

        with deepgram.listen.v1.connect(
            model="nova-3-medical",
            encoding="linear16",
            sample_rate=SAMPLE_RATE,
            channels=CHANNELS,
            # Wait 2 s of silence before firing speech_final.
            # Increase to 3000 if doctors pause longer mid-sentence.
            # endpointing=300,
            # Adds punctuation and capitalisation automatically.
            smart_format=True,
            punctuate=True,
        ) as connection:

            # ----------------------------------------------------------------
            # Event handlers
            # ----------------------------------------------------------------

            def on_open(_) -> None:
                print("Connection opened\n")
                connection_ready.set()

            def on_message(message) -> None:
                if not (
                    hasattr(message, "channel")
                    and hasattr(message.channel, "alternatives")
                ):
                    return

                transcript = message.channel.alternatives[0].transcript
                if not transcript:
                    return

                is_final = getattr(message, "is_final", False)
                speech_final = getattr(message, "speech_final", False)

                if is_final:
                    sentence_buffer.append(transcript)
                    print(f"  [fragment]  {transcript}")

                # if speech_final:
                #     full_utterance = " ".join(sentence_buffer).strip()
                #     sentence_buffer.clear()
                #     if full_utterance:
                #         print(f"\n[UTTERANCE]  {full_utterance}\n")
                        # → save full_utterance to DB here

            def on_close(_) -> None:
                print("\nConnection closed")

            def on_error(error) -> None:
                print(f"\nError: {error}")

            connection.on(EventType.OPEN, on_open)
            connection.on(EventType.MESSAGE, on_message)
            connection.on(EventType.CLOSE, on_close)
            connection.on(EventType.ERROR, on_error)

            # ----------------------------------------------------------------
            # Listener thread — receives messages from Deepgram
            # ----------------------------------------------------------------

            def listener_thread():
                try:
                    connection.start_listening()
                except Exception as e:
                    print(f"Error in listener thread: {e}")

            listen_thread = threading.Thread(target=listener_thread, daemon=True)
            listen_thread.start()

            # ----------------------------------------------------------------
            # Audio capture thread — reads from mic and sends to Deepgram
            # ----------------------------------------------------------------

            pyaudio_instance = pyaudio.PyAudio()
            stream = pyaudio_instance.open(
                format=pyaudio.paInt16,
                channels=CHANNELS,
                rate=SAMPLE_RATE,
                input=True,
                frames_per_buffer=CHUNK_SIZE,
            )

            def audio_capture_thread():
                nonlocal buffering

                # Capture audio immediately so nothing is lost during handshake.
                # Store in pre_buffer until the connection is ready.
                print("Buffering audio while connecting...")
                while not connection_ready.is_set():
                    try:
                        data = stream.read(CHUNK_SIZE, exception_on_overflow=False)
                        if data:
                            pre_buffer.put(data)
                    except Exception:
                        pass

                # Drain the pre-connection buffer first so we don't drop
                # the first few seconds of speech.
                print("Draining pre-connection audio buffer...")
                while not pre_buffer.empty():
                    try:
                        chunk = pre_buffer.get_nowait()
                        if len(chunk) > 0:
                            connection.send_media(chunk)
                    except queue.Empty:
                        break

                buffering = False
                print("Live transcription active. Press Enter to stop...\n")

                # Main capture loop
                try:
                    while True:
                        data = stream.read(CHUNK_SIZE, exception_on_overflow=False)
                        # Guard: never send empty bytes — causes unexpected WS closure.
                        if len(data) > 0:
                            connection.send_media(data)
                except Exception as e:
                    print(f"Error in audio thread: {e}")

            capture_thread = threading.Thread(
                target=audio_capture_thread, daemon=True
            )
            capture_thread.start()

            input("")  # block until Enter

            stream.stop_stream()
            stream.close()
            pyaudio_instance.terminate()

            capture_thread.join(timeout=5.0)
            listen_thread.join(timeout=5.0)
            print("Finished")

    except Exception as e:
        print(f"Could not open socket: {e}")


if __name__ == "__main__":
    main()