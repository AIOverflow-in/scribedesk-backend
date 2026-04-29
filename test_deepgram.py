import httpx
import threading
import os

from deepgram import DeepgramClient
from deepgram.core.events import EventType
from src.core.config import settings

URL = "http://stream.live.vc.bbcmedia.co.uk/bbc_world_service"

def main():
    try:
        deepgram: DeepgramClient = DeepgramClient(api_key=settings.DEEPGRAM_API_KEY)

        with deepgram.listen.v1.connect(model="nova-3") as connection:

            def on_message(message) -> None:
                if not (hasattr(message, 'channel') and hasattr(message.channel, 'alternatives')):
                    return

                transcript = message.channel.alternatives[0].transcript
                if not transcript:
                    return

                is_final = getattr(message, 'is_final', False)
                speech_final = getattr(message, 'speech_final', False)

                if is_final:
                    print(f"\n[IS FINAL]      {transcript}")
                if speech_final:
                    print(f"\n[SPEECH FINAL]  {transcript}")

            connection.on(EventType.OPEN, lambda _: print("Connection opened\n"))
            connection.on(EventType.MESSAGE, on_message)
            connection.on(EventType.CLOSE, lambda _: print("\nConnection closed"))
            connection.on(EventType.ERROR, lambda error: print(f"\nError: {error}"))

            lock_exit = threading.Lock()
            exit = False

            def listening_thread():
                try:
                    connection.start_listening()
                except Exception as e:
                    print(f"Error in listening thread: {e}")

            listen_thread = threading.Thread(target=listening_thread)
            listen_thread.start()

            def myThread():
                try:
                    with httpx.stream("GET", URL) as r:
                        for data in r.iter_bytes():
                            lock_exit.acquire()
                            if exit:
                                break
                            lock_exit.release()
                            connection.send_media(data)
                except Exception as e:
                    print(f"Error in HTTP streaming thread: {e}")

            myHttp = threading.Thread(target=myThread)
            myHttp.start()

            input("Press Enter to stop...\n")
            lock_exit.acquire()
            exit = True
            lock_exit.release()

            myHttp.join(timeout=5.0)
            listen_thread.join(timeout=5.0)
            print("Finished")

    except Exception as e:
        print(f"Could not open socket: {e}")

if __name__ == "__main__":
    main()