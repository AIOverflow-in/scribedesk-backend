# ScribeDesk API Design & Flow

## 1. Core Endpoints

### `GET /api/scribe/sessions/{id}`
Returns session metadata and header data.
* **Response**: `id`, `title`, `description`, `total_audio_seconds`, `status`, `patient: {id, name, age, gender}`, `clinical_summary`, `reports: [{id, title, root_type, created_at}]`.

### `GET /api/scribe/sessions/{id}/timeline`
Returns the sequential log of events and transcripts.
* **Response**: List of `session_timeline` items.
* **Usage**: Used to render the "Transcript" tab.

### `POST /api/reports`
Generates a report using an LLM.
* **Payload**: `session_id`, `template_id`, `additional_context`, `prescriptions: []`.
* **Flow**: Fetches transcripts -> Sends to LLM with template -> Saves to `reports` table -> Returns full report object.

---

## 2. The Scribe Flow (WebSocket Proxy)

We use a **Backend Proxy** model. The Frontend connects to our Backend, and our Backend connects to Deepgram.

### URL: `ws://backend/ws/scribe/{session_id}`

#### A. Session Initiation (`started` / `resumed`)
1. **Frontend**: Opens WebSocket.
2. **Backend**: 
   * Verifies session exists.
   * If `total_audio_seconds == 0`: Logs `event: started` to timeline.
   * Else: Logs `event: resumed` to timeline.
   * Sets `current_segment_start = now()`.
   * **Sends `READY_PACKET`**: `{"type": "ready", "accumulated_seconds": session.total_audio_seconds}`.
   * Opens connection to Deepgram WS.

#### B. Streaming & Chunking
1. **Frontend**: Streams raw audio bytes.
2. **Backend**: Forwards bytes to Deepgram.
3. **Deepgram**: Returns `is_final: true` transcript segments.
4. **Backend Buffer**: Collects segments until ~70 words.
5. **Timeline Save**:
   * `elapsed = now() - current_segment_start`
   * `relative_seconds = total_audio_seconds + elapsed`
   * Saves transcript to `session_timeline` with `relative_seconds`.
   * **Pushes to Frontend**: `{"type": "transcript", "content": "...", "timestamp": 360}`.

#### C. Termination (`stopped`)
1. **Frontend**: Closes WebSocket (User clicks Stop).
2. **Backend `on_disconnect`**:
   * `elapsed = now() - current_segment_start`.
   * `session.total_audio_seconds += elapsed`.
   * `session.current_segment_start = NULL`.
   * Logs `event: stopped` to timeline with `relative_seconds`.
   * **Triggers Background Task**: Auto-generate `title` and `description` (if it's the first stop).

---

## 3. Frontend Timer Logic

The timer in the UI must be a **Slave** to the Backend's `total_audio_seconds`.

1. **Idle State**: Timer displays `format(session.total_audio_seconds)`.
2. **On "Start/Resume"**:
   * Frontend opens WS.
   * UI shows "Connecting...".
3. **On `READY_PACKET`**:
   * Receive `accumulated_seconds`.
   * Start a Javascript `setInterval`:
     `DisplayTime = accumulated_seconds + (Date.now() - startTime)`.
4. **On "Stop"**:
   * WS Closes.
   * Frontend calls `invalidateQueries(['session', id])`.
   * The new `total_audio_seconds` is fetched, and the timer "snaps" to the exact backend value.

---

## 4. Digital Signature Logic

### `POST /api/reports/{id}/sign`
1. Checks if `is_signed` is already true.
2. Generates `SHA-256` hash of `report.content`.
3. Sets `is_signed = true`, `signed_at = now()`, and `content_hash = hash`.
4. **Enforcement**: Any `PATCH` or `DELETE` request for this report ID will now return `403 Forbidden`.
