# Scribe Live Flow — Real Scenario Trace

## Setup
- **Session ID**: `session_abc`
- **DB State**: `total_audio_seconds: 0`, `current_segment_start: NULL`

---

## Stage 1: First Start
**Wall Clock: 10:00:00 AM**

1. Doctor hits **Start** → Frontend opens WebSocket.
2. Backend `on_connect`:
   - Reads `total_audio_seconds` → `0`
   - Logs timeline event: `type: event, event_type: started, relative_seconds: 0`
   - Sets `session.current_segment_start = 10:00:00`
   - Sends `SYNC_PACKET: {"accumulated_seconds": 0}`
3. Frontend receives `0` → starts local `setInterval` timer from `00:00`.

---

## Stage 2: First Transcript Chunk
**Wall Clock: 10:01:40 AM (100s elapsed)**

1. Backend buffers ~5 `is_final` events from Deepgram → reaches threshold.
2. Calculation:
   `relative_seconds = session.total_audio_seconds (0) + (now - current_segment_start)`
   `relative_seconds = 0 + 100 = 100`
3. DB: Timeline entry `type: transcript, content: "Patient reports...", relative_seconds: 100`
4. WS push: `{"type": "transcript", "text": "...", "timestamp": 100}`
5. Frontend: shows transcript at `01:40` — local timer also at `01:40` ✅

---

## Stage 3: Stop / Pause
**Wall Clock: 10:05:00 AM (300s elapsed)**

1. Doctor hits **Stop** → Frontend closes WebSocket.
2. Backend `on_disconnect`:
   - `elapsed = 10:05:00 - 10:00:00 = 300s`
   - Logs event: `type: event, event_type: stopped, relative_seconds: 300`
   - Updates session:
     - `total_audio_seconds = 0 + 300 = 300`
     - `current_segment_start = NULL`
3. Frontend: local timer stops at `05:00`.

---

## Stage 4: The Gap (Coffee Break)
**Wall Clock: 10:05:00 AM → 10:30:00 AM**

- DB: `total_audio_seconds = 300`, `current_segment_start = NULL`
- UI: timer shows `05:00` (static), **Resume** button visible.

---

## Stage 5: Resume
**Wall Clock: 10:30:00 AM**

1. Doctor hits **Resume** → Frontend opens WebSocket.
2. Backend `on_connect`:
   - Reads `total_audio_seconds = 300`
   - Logs event: `type: event, event_type: resumed, relative_seconds: 300`
   - Sets `current_segment_start = 10:30:00`
   - Sends `SYNC_PACKET: {"accumulated_seconds": 300}`
3. Frontend receives `300` → resumes local timer from `05:00`.

---

## Stage 6: Transcript After Resume
**Wall Clock: 10:31:00 AM (60s into segment)**

1. `relative_seconds = 300 + (10:31:00 - 10:30:00) = 360`
2. DB: timeline entry `type: transcript, relative_seconds: 360`
3. WS push: `{"type": "transcript", "text": "...", "timestamp": 360}`
4. Frontend: transcript at `06:00`, local timer at `06:00` ✅

---

## Stage 7: Final Stop
**Wall Clock: 10:45:00 AM (900s into segment)**

1. Doctor hits **Stop** → WS closes.
2. Backend `on_disconnect`:
   - `elapsed = 10:45:00 - 10:30:00 = 900s`
   - Logs event: `type: event, event_type: stopped, relative_seconds: 300 + 900 = 1200`
   - Updates: `total_audio_seconds = 300 + 900 = 1200`, `current_segment_start = NULL`
   - Triggers background task: auto-generate `title` + `description` (first stop after session creation)
3. Frontend timer stops at `20:00`.

---

## Final DB State

| Session field | Value |
|---|---|
| `total_audio_seconds` | 1200 (20 min) |
| `current_segment_start` | NULL |
| `status` | `completed` |

| Timeline | Type | `relative_seconds` |
|---|---|---|
| started | event | 0 |
| Patient reports... | transcript | 100 |
| stopped | event | 300 |
| resumed | event | 300 |
| Patient mentions... | transcript | 360 |
| stopped | event | 1200 |

---

## Key Rules

1. `total_audio_seconds` is **only updated on WS disconnect** — never during streaming.
2. While WS is open: `current_relative_time = total_audio_seconds + (now - current_segment_start)`.
3. `relative_seconds` in timeline = `total_audio_seconds + elapsed_in_current_segment` at the time of the event/chunk.
4. Frontend timer = `SYNC_PACKET.accumulated_seconds + (Date.now() - ws_connected_at)`.
