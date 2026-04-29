# Scribe Module (Sessions + WebSocket)

## Overview

The core scribe feature. Sessions hold the metadata and transcription state for a single consultation. Real-time transcription flows through a WebSocket that proxies audio to Deepgram, buffers transcripts, and persists them to the session timeline.

On first stop, the LLM generates a title and clinical summary concurrently. On subsequent stops, only the summary is updated incrementally.

---

## Terminology

| Term                    | Meaning |
|-------------------------|---------|
| **Session**             | A single consultation with metadata (title, status, patient link, audio duration) |
| **Timeline Entry**      | Either an `event` (started/stopped/resumed) or a `transcript` (spoken text chunk) |
| **Segment**             | A continuous audio recording from WS connect to disconnect |
| **Total Audio Seconds** | Cumulative across all segments |
| **Current Segment Start** | Timestamp; used for live time calculation during streaming |

---

## Routes

### `GET /api/v1/sessions`

List sessions with pagination.

**Query params:** `page`, `page_size` (default 1, 20)

**Response `200`:**
```json
{
  "items": [
    {
      "id": "uuid",
      "user_id": "uuid",
      "patient_id": "uuid",
      "patient_name": "Jane Smith",
      "patient_gender": "Female",
      "patient_age": 34,
      "title": "Follow-up: Hypertension",
      "description": null,
      "status": "active",
      "total_audio_seconds": 0,
      "current_segment_start": null,
      "clinical_summary": null,
      "last_summarized_transcript_id": null,
      "reports": [],
      "created_at": "...",
      "updated_at": "..."
    }
  ],
  "total": 5,
  "page": 1,
  "page_size": 20
}
```

---

### `POST /api/v1/sessions`

Create a new session.

**Request body:**
```json
{
  "patient_id": "uuid or null"
}
```

Creates a session in `"active"` status with title `"Untitled Session"`.

**Response `201`:** `SessionResponse`.

---

### `GET /api/v1/sessions/{session_id}`

Get a single session with patient info and associated reports.

**Response `200`:** `SessionResponse` including `reports` array.

---

### `PATCH /api/v1/sessions/{session_id}`

Update session metadata.

**Request body** (all optional):
```json
{
  "title": "Follow-up: Hypertension",
  "description": "Patient reports good adherence",
  "patient_id": "uuid",
  "clinical_summary": "## Reason for Visit..."
}
```

**Response `200`:** Updated `SessionResponse`.

---

### `GET /api/v1/sessions/{session_id}/timeline`

Get all timeline entries (events + transcripts) for a session, newest first.

**Response `200`:**
```json
[
  {
    "id": "uuid",
    "session_id": "uuid",
    "type": "event",
    "event_type": "started",
    "content": "Transcript started 14:30",
    "speaker_id": null,
    "relative_seconds": 0,
    "created_at": "..."
  },
  {
    "id": "uuid",
    "session_id": "uuid",
    "type": "transcript",
    "event_type": null,
    "content": "Patient is here for a follow-up on hypertension...",
    "speaker_id": null,
    "relative_seconds": 45,
    "created_at": "..."
  }
]
```

Timeline entries are:
- **`type: "event"`** — lifecycle markers: `started`, `resumed`, `stopped`
- **`type: "transcript"`** — flushed transcript chunks (default flush every 5 `is_final` events)

---

## WebSocket — `ws://localhost:8000/api/v1/ws/scribe/{session_id}`

### Authentication

Pass the session token as a query parameter:
```
ws://localhost:8000/api/v1/ws/scribe/{session_id}?token=a1b2c3d4e5f6...
```

Token is the same hex token returned by login/register.

### Protocol

#### 1. Ready packet (server → client)

On connect, the server logs a `started`/`resumed` event and sends:

```json
{
  "type": "ready",
  "accumulated_seconds": 0
}
```

The frontend should use `accumulated_seconds` as the initial timer value.

#### 2. Audio streaming (client → server)

Send raw PCM audio bytes (16kHz, 16-bit, mono, linear16).

```javascript
websocket.send(audioBlob);
```

#### 3. Transcript chunks (server → client)

Whenever Deepgram emits 5 `is_final` events, the buffer flushes and the server sends:

```json
{
  "type": "transcript",
  "text": "Patient reports that they have been taking their medication...",
  "timestamp": 145
}
```

`timestamp` = `accumulated_seconds + elapsed_since_segment_start`.

#### 4. Live time calculation

While streaming, the total time is NOT written to the DB yet. The frontend should compute:
```
current_total = session.total_audio_seconds + (now - session.current_segment_start)
```
After the WS disconnects, `total_audio_seconds` is finalised and `current_segment_start` is cleared.

#### 5. Disconnect (client closes or network drops)

Server:
1. Logs a `stopped` event
2. Updates `total_audio_seconds` (accumulates segment duration)
3. Clears `current_segment_start`
4. **First stop ever:** generates title (tiny_llm, from first 5 transcripts) + summary (fast_llm, all transcripts) **concurrently**
5. **Subsequent stops:** updates summary incrementally (only new transcripts since `last_summarized_transcript_id`)

No close frame is sent — the frontend should handle the `onclose` event.

### State Machine

```
Created (status: "active", total_audio_seconds: 0)
  │
  ├── WS connect ──► started event ──► audio streaming
  │                                      │
  │                                      ├── buffer 5 is_final ──► transcript saved + pushed
  │                                      │
  │                                      └── WS disconnect ──► stopped event
  │                                           │
  │                                           ├── total_audio_seconds += elapsed
  │                                           ├── first stop? ──► generate title + summary
  │                                           └── not first? ──► update summary
  │
  └── WS reconnect ──► resumed event (accumulated = existing total_audio_seconds)
```

---

## Audio Format Requirements

| Property      | Value     |
|---------------|-----------|
| Encoding      | Linear16  |
| Sample rate   | 16000 Hz  |
| Channels      | 1 (mono)  |
| Source        | Browser `MediaRecorder` with `audio/webm` or similar → decode to PCM |

---

## Schemas

### `SessionResponse`

| Field                        | Type      | Notes |
|------------------------------|-----------|-------|
| `id`                         | UUID      |       |
| `user_id`                    | UUID      | Owner |
| `patient_id`                 | UUID?     | Linked patient |
| `patient_name`               | string?   | Resolved from patient relation |
| `patient_gender`             | string?   |       |
| `patient_age`                | int?      | Calculated from DOB |
| `title`                      | string    | Auto-generated on first stop |
| `description`                | string?   | Manual |
| `status`                     | string    | `"active"` only currently |
| `total_audio_seconds`        | int       | Cumulative |
| `current_segment_start`      | datetime? | Non-null while streaming |
| `clinical_summary`           | string?   | LLM-generated markdown |
| `last_summarized_transcript_id` | UUID? | Tracks incremental summary progress |
| `reports`                    | array     | List of `ReportMetadata` |
| `created_at`                 | datetime  |       |
| `updated_at`                 | datetime  |       |

### `CreateSessionRequest`

| Field        | Type   | Notes |
|--------------|--------|-------|
| `patient_id` | UUID?  | Pre-link a patient |

### `UpdateSessionRequest`

All fields optional: `title`, `description`, `patient_id`, `clinical_summary`.

### `SessionTimelineResponse`

| Field             | Type      | Notes |
|-------------------|-----------|-------|
| `id`              | UUID      |       |
| `session_id`      | UUID      |       |
| `type`            | string    | `"event"` or `"transcript"` |
| `event_type`      | string?   | `"started"`, `"stopped"`, `"resumed"` |
| `content`         | string?   | Event description or transcript text |
| `speaker_id`      | int?      | Not currently used |
| `relative_seconds`| int?      | Position in the recording timeline |
| `created_at`      | datetime  |       |

---

## Frontend Integration

### Typical Flow

1. **Create/select a session** → `POST /sessions` or `GET /sessions`
2. **Link a patient** (optional) → `PATCH /sessions/{id}` with `patient_id`
3. **Open WebSocket** → `ws://...?token={session_token}`
4. **Receive `ready`** → start the timer with `accumulated_seconds`
5. **Start microphone** → `MediaRecorder` → pipe audio chunks to WS
6. **Receive transcript chunks** → append to a live transcript UI
7. **User taps "Stop"** → close WS
8. **Poll `GET /sessions/{id}`** → wait for `title` and `clinical_summary` to appear (generated async during stop)
9. **Generate reports** → `POST /reports` with a chosen template

### Timer During Streaming

```
liveTotal = session.total_audio_seconds + (Date.now() - session.current_segment_start) / 1000
```

Use `current_segment_start` from the session response. Poll `GET /sessions/{id}` periodically while streaming to keep this accurate (or track it locally after `ready`).

---

## Dependencies

- `CurrentUserIdDep` / `WsCurrentUserIdDep` — auth
- `SessionServiceDep` — injects `SessionService`
- `get_tiny_llm_service` / `get_fast_llm_service` — LLM for title/summary

---

## File Locations

| File                                 | Role |
|--------------------------------------|------|
| `src/api/v1/sessions.py`             | REST routes |
| `src/api/v1/websockets.py`           | WebSocket route |
| `src/modules/sessions/service.py`    | Full lifecycle + WS handler |
| `src/modules/sessions/ai.py`         | Title + summary LLM helpers |
| `src/schemas/api/sessions.py`        | Request/response schemas |
| `src/schemas/features/sessions.py`   | `SessionTitleSchema` (LLM structured output) |
| `src/content/prompts/sessions.py`    | `ScribePrompts` (prompt templates) |
| `src/infrastructure/external/deepgram.py` | Deepgram proxy session |
