# Deepgram Streaming Reliability — Diagnosis for AI Agent

## Problem

Deepgram's real-time `nova-3-medical` streaming API drops 20–60s chunks of audio (zero `is_final` events) through the full browser→FastAPI→Deepgram pipeline. The standalone test `test_deepgram_mic.py` works perfectly with identical model/config, ruling out Deepgram-side issues. Audio amplitude is valid during gaps (`max_amp > 1000`), chunks arrive every ~100ms, and no Deepgram connection errors are logged.

## Architecture & Code

### Entry Point: `websockets.py`

```python
@router.websocket("/ws/scribe/{session_id}")
async def scribe_websocket(websocket, session_id, user_id):
    await websocket.accept()
    async with async_session_maker() as db:          # ← DB session lives entire WS lifetime
        repo = SessionsRepository(db)
        service = SessionService(repo=repo, ...)
        await service.handle_transcription_stream(
            websocket=websocket,
            session_id=session_id,
            user_id=UUID(user_id),
        )
```

**Critical detail:** `db` is created once at the top and used by both `prepare_start` and `prepare_stop` (called 60s+ apart). SQLAlchemy async sessions `autobegin` a transaction on first use. This idle transaction stays open during streaming, causing `server_default=func.now()` to return the transaction's start time, not the actual insert time (see timestamp bug below).

### Deepgram Proxy: `deepgram.py`

```python
class DeepgramTranscriptionSession:
    def __init__(self, on_flush, on_intermediate=None, buffer_size=5):
        self._buffer: list[str] = []
        self._lock = threading.Lock()
        self._connection = None
        self._loop = None

    def _handle_message(self, message) -> None:
        if not (hasattr(message, "channel") and hasattr(message.channel, "alternatives")):
            return
        transcript = message.channel.alternatives[0].transcript
        is_final = getattr(message, "is_final", False)
        if not transcript or not is_final:
            return                              # ← Ignores interim (non-final) results

        logger.info(f"[FRAGMENT] {transcript}")
        chunk_to_flush = None
        with self._lock:
            self._buffer.append(transcript)
            if len(self._buffer) >= self._buffer_size:
                chunk_to_flush = " ".join(self._buffer)
                self._buffer.clear()

        if self._on_intermediate:
            asyncio.run_coroutine_threadsafe(   # ← Schedules on event loop (can be delayed)
                self._on_intermediate(transcript), self._loop)

        if chunk_to_flush:
            asyncio.run_coroutine_threadsafe(
                self._on_flush(chunk_to_flush), self._loop)

    def send_audio(self, data: bytes) -> None:
        if self._connection:
            self._connection.send_media(data)    # ← CALLED FROM EVENT LOOP (synchronous!)

    def __enter__(self):
        self._loop = asyncio.get_running_loop()
        client = DGClient(api_key=settings.DEEPGRAM_API_KEY)
        self._connection_cm = client.listen.v1.connect(
            model="nova-3-medical", encoding="linear16",
            sample_rate=16000, channels=1,
            smart_format=True, punctuate=True,
        )
        self._connection = self._connection_cm.__enter__()
        self._connection.on(EventType.OPEN, ...)
        self._connection.on(EventType.MESSAGE, self._handle_message)
        self._connection.on(EventType.CLOSE, ...)
        self._connection.on(EventType.ERROR, ...)

        def _listen():
            self._connection.start_listening()   # ← Blocks in daemon thread
        threading.Thread(target=_listen, daemon=True).start()

    def __exit__(self, *args):
        if self._connection_cm:
            self._connection_cm.__exit__(*args)
```

### Streaming Orchestration: `service.py` (`handle_transcription_stream`)

```python
async def handle_transcription_stream(self, websocket, session_id, user_id):
    accumulated, _ = await self.prepare_start(session_id, user_id)
    await websocket.send_json({"type": "ready", "accumulated_seconds": accumulated})

    segment_start = datetime.now(timezone.utc)
    batch_start_ts = None

    def _relative_seconds() -> int:
        return accumulated + int((datetime.now(timezone.utc) - segment_start).total_seconds())

    async def on_intermediate(text):
        ts = _relative_seconds()
        if batch_start_ts is None:
            batch_start_ts = ts
        await websocket.send_json({"type": "transcript_fragment", "text": text, "timestamp": ts})

    async def on_flush(text):
        ts = batch_start_ts if batch_start_ts is not None else _relative_seconds()
        batch_start_ts = None
        async with async_session_maker() as db:    # ← Fresh session for transcript rows
            entry = SessionTimeline(..., created_at=datetime.now(timezone.utc))
            repo = SessionsRepository(db)
            await repo.add_timeline_entry(entry)
        if not ws_closed:
            await websocket.send_json({"type": "transcript", "text": text, "timestamp": ts})

    ws_closed = False
    with self.deepgram.create_session(on_flush=on_flush, on_intermediate=on_intermediate) as dg_session:
        try:
            while True:
                data = await websocket.receive_bytes()
                dg_session.send_audio(data)          # ← SYNCHRONOUS call in event loop!
        except WebSocketDisconnect:
            ws_closed = True

    await dg_session.flush_remaining()
    elapsed, is_first_stop = await self.prepare_stop(session_id, user_id)  # ← Uses shared repo session
```

### Session Events: `prepare_start` / `prepare_stop`

```python
async def prepare_start(self, session_id, user_id):
    session = await self.repo.get(session_id, user_id)
    accumulated = session.total_audio_seconds

    entry = SessionTimeline(
        ..., content=f"Transcript started {datetime.now(timezone.utc).strftime('%H:%M:%S')}",
        relative_seconds=accumulated,
        created_at=datetime.now(timezone.utc),       # ← Explicitly set (fix applied)
    )
    await self.repo.add_timeline_entry(entry)         # ← Uses self.repo.session
    await self.repo.update(session, {"current_segment_start": datetime.now(timezone.utc)})
    return accumulated, event_type

async def prepare_stop(self, session_id, user_id):
    session = await self.repo.get(session_id, user_id)  # ← Uses same self.repo.session
    if session.current_segment_start is None:
        return 0, False
    now = datetime.now(timezone.utc)
    elapsed = int((now - session.current_segment_start).total_seconds())
    new_total = session.total_audio_seconds + elapsed

    entry = SessionTimeline(
        ..., content=f"Transcript stopped {now.strftime('%H:%M:%S')}",
        relative_seconds=new_total,
        created_at=datetime.now(timezone.utc),         # ← Explicitly set (fix applied)
    )
    await self.repo.add_timeline_entry(entry)           # ← Uses shared session, w/ stale transaction now()
    ...
```

## Root Causes Found & Fixed

### 1. Frontend Audio Double-Resampling (FIXED)

**Code pattern (frontend, not in repo):**
```javascript
// audio-capture.ts — BEFORE fix:
const sourceRate = trackSettings.sampleRate;  // 48000 (native)
this.audioCtx = new AudioContext({ sampleRate: 16000 });
this.workletNode = new AudioWorkletNode(this.audioCtx, "pcm-encoder", {
    processorOptions: { sourceRate, targetRate: 16000 }   // ratio = 3.0!
});
```

**Problem:** `AudioContext({sampleRate: 16000})` already resamples mic 48kHz→16kHz. Worklet then re-resamples with `ratio = 48000/16000 = 3.0`, producing ~5.3kHz garbage.

**Fix:** Changed `sourceRate` to `ctxRate` (16kHz), making ratio=1.0 so the worklet is a pass-through.

**Still broken after fix:** Fragments arrive but large gaps persist.

### 2. `created_at` Timestamp Stale Transaction (FIXED)

**Problem:** `SessionTimeline` uses `server_default=func.now()` which equals PostgreSQL's transaction start time. `websockets.py` creates one `AsyncSession` for the entire WS lifetime:
```python
async with async_session_maker() as db:      # ← one session
    service = SessionService(repo=SessionsRepository(db))
    await service.handle_transcription_stream(...)   # prepare_start + prepare_stop share `db`
```

SQLAlchemy async sessions `autobegin` a transaction on first `execute()`/`add()`. After `prepare_start` commits its entries, the next `autobegin` starts a transaction at ~`08:53:17`. This transaction stays **idle** during the entire audio flow (minutes). When `prepare_stop` inserts the stopped event, `DEFAULT now()` returns `08:53:17` — not the actual stop time `08:54:43`.

**Fix:** Explicitly pass `created_at=datetime.now(timezone.utc)` on every `SessionTimeline(...)` construction to override `server_default`.

**Error in DB before fix:**
```json
{"type":"event","event_type":"stopped","content":"Transcript stopped 08:54:43","created_at":"08:53:17"}
```
`relative_seconds=87` (correct audio position), but `created_at` = transaction start = same as "started" event.

## Remaining Problem: Dropped Fragments (UNFIXED)

### The Evidence

Logs show audio continuously arriving but Deepgram emits zero `is_final=True` for 20–60s:
```
14:04:19  [FRAGMENT] the back pain from coming back.
14:04:19  [FLUSH DB] the back pain from coming back...
          ... 23 seconds of silence from Deepgram ...
14:04:42  [FRAGMENT] You think the physical therapy was helping?
```

During the gap: `[AUDIO HEALTH]` at 14:04:22 shows `max_amp=90`, at 14:04:52 shows `max_amp=3136` — audio IS present.

### The Critical Difference: Test Script vs. Full Pipeline

| Aspect | `test_deepgram_mic.py` (WORKS) | Full Pipeline (BROKEN) |
|--------|-------------------------------|------------------------|
| `send_media` caller | **Dedicated daemon thread** | **FastAPI event loop** (`handle_transcription_stream` while loop) |
| Thread model | 2 threads: PyAudio capture + Deepgram listener | 1 async task + 1 Deepgram listener thread |
| DB writes | None (prints to console) | `async with async_session_maker()` with fresh sessions |

**SUSPECTED ROOT CAUSE — Blocking I/O in Event Loop:**

In `service.py` line 291:
```python
while True:
    data = await websocket.receive_bytes()
    dg_session.send_audio(data)    # ← SYNCHRONOUS! Called from event loop every 100ms
```

`send_audio` → `connection.send_media(data)`. If the Deepgram SDK's `send_media` does synchronous socket writes (which it likely does in the v2/v3 hybrid model), this **blocks the entire FastAPI event loop** for the duration of the socket write. Every 100ms.

This starvation cascade:
1. Event loop blocked on `send_media` write
2. `websocket.receive_bytes()` can't execute → frontend backpressure builds
3. `asyncio.run_coroutine_threadsafe()` callbacks (`on_intermediate`, `on_flush`) can't execute → Deepgram's listener thread queues build up
4. If Deepgram SDK's internal receive buffer overflows, messages are **silently dropped** — the gaps

**Why test script works:** It calls `send_media` from a **Python thread** (not the event loop), so `send_media` never blocks anything else.

### Other Hypotheses

| # | Hypothesis | Evidence | Test |
|---|-----------|----------|------|
| H1 | **Blocking `send_media` (above)** | Only difference between working/broken pipeline | Wrap in `asyncio.to_thread` |
| H2 | `nova-3-medical` model unstable for long streams | — | Switch to `nova-3` |
| H3 | AudioWorklet still produces silent chunks despite ratio fix | 30s health-check samples only last chunk | Log every chunk's `max_amp` into a ring buffer |
| H4 | Interim results (`is_final=False`) carry words never finalized | We ignore non-final messages | Log ALL Deepgram messages at DEBUG |

## The Working Test Script

`test_deepgram_mic.py` — use this as reference for correct behavior:

```python
# Key pattern: send_media from a dedicated thread
def audio_capture_thread():
    stream = pyaudio.PyAudio().open(rate=16000, ...)
    while True:
        data = stream.read(1024)
        if len(data) > 0:
            connection.send_media(data)   # ← Called from THREAD, not event loop

# Capture runs in thread, main thread just blocks on input()
capture_thread = threading.Thread(target=audio_capture_thread, daemon=True)
capture_thread.start()
input("Press Enter to stop...")
```

## Recommended Immediate Fix

Wrap the synchronous `send_audio` call in `asyncio.to_thread` to move the blocking socket write off the event loop:

```python
# service.py — in handle_transcription_stream:
while True:
    data = await websocket.receive_bytes()
    await asyncio.to_thread(dg_session.send_audio, data)
    #                    ^^^^^^^^^^^^^^^^^^ prevents event loop starvation
```

## All Disk Files Referenced

| File | Role |
|------|------|
| `test_deepgram_mic.py` | Standalone working test — PyAudio → Deepgram directly |
| `src/api/v1/websockets.py` | FastAPI WS endpoint — instantiates shared DB session |
| `src/infrastructure/external/deepgram.py` | Deepgram proxy — threading, buffering, `send_media` caller |
| `src/modules/sessions/service.py` | WS lifecycle — `handle_transcription_stream`, `prepare_start/stop` |
| `src/infrastructure/persistence/postgres/repos/sessions_repo.py` | `add_timeline_entry`, `update` — DB operations |
| `src/core/config.py` | `DEEPGRAM_MODEL=nova-3-medical`, `DEEPGRAM_CHUNK_SIZE=5` |
