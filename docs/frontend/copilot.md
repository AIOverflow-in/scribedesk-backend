# Copilot (AI Chat) Module

## Overview

AI-powered medical chat with an LLM agent. Supports standalone chats, session-linked chats, and patient-linked chats. The agent can search medical web sources and fetch patient history via tools.

**Base path:** `/api/v1/chats`

---

## Schemas

### `POST /api/v1/chats/messages` — Request
```json
{
  "conversation_id": null,
  "message": "What is the recommended dosage for Amoxicillin?",
  "session_id": "uuid-or-null",
  "patient_id": "uuid-or-null"
}
```

| Field | When to send |
|---|---|
| `conversation_id: null` | First message of a new chat |
| `conversation_id: "uuid"` | Subsequent messages in an existing chat |
| `session_id` | Chat opened from the session detail page |
| `patient_id` | Standalone chat about a specific patient (optional) |

If both `session_id` and `patient_id` are provided, `patient_id` is derived from the session.

### Response — SSE Stream

The response is a **Server-Sent Events** stream. Each line is:

```
data: {"type":"...","content":"...","status_message":"...","tool_name":"...","metadata_type":"...","data":{...}}\n\n
```

### Event Types

| `type` | When | Fields |
|---|---|---|
| `metadata` | First event for a new chat | `metadata_type: "conversation_created"`, `data.conversation_id` |
| `status` | Tool emits progress | `status_message: "Searching for 'query'..."` |
| `tool_call` | Tool starts or ends | `tool_name`, `status_message`, `data.result` (on end) |
| `metadata` | Search tool found results | `metadata_type: "citations"`, `data` with items array |
| `content` | LLM token stream | `content: "text chunk"` (accumulate across events) |
| `error` | Something failed | `error: "error message"` |
| `done` | Stream complete | no extra fields |

**Example stream (new conversation):**
```
data: {"type":"metadata","metadata_type":"conversation_created","data":{"conversation_id":"550e8400-e29b-41d4-a716-446655440000"}}

data: {"type":"tool_call","status_message":"Fetching Patient History...","tool_name":"get_patient_history"}

data: {"type":"tool_call","status_message":"Completed Get Patient History","tool_name":"get_patient_history","data":{"result":"..."}}

data: {"type":"status","status_message":"Searching for 'Amoxicillin dosage 500mg'..."}

data: {"type":"metadata","metadata_type":"citations","data":{"count":3,"items":[...]}}

data: {"type":"content","content":"Based on standard medical guidelines, the recommended"}

data: {"type":"content","content":" dosage of Amoxicillin for adults is 500mg every 8 hours"}

data: {"type":"content","content":" or 875mg every 12 hours depending on the severity."}

data: {"type":"done"}
```

**Frontend flow:**
1. Check if first event has `metadata_type: "conversation_created"` — store the `conversation_id`
2. Accumulate all `content` events into the displayed message
3. Show tool status indicators from `tool_call` events
4. On `done`, stop reading — the message is complete
5. If `error` arrives, show error state

---

## Routes

### `POST /api/v1/chats/messages`

Send a message and stream the AI response.

**Request:** JSON body (see schemas above)

**Response:** SSE stream (see event types above)

**Errors:** 500 (wrapped in SSE `error` event)

---

### `GET /api/v1/chats`

List conversations for the current user. Supports pagination and optional session filter (for session detail page dropdown).

**Query params:**

| Param | Type | Default |
|---|---|---|
| `page` | int | 1 |
| `page_size` | int | 20 |
| `session_id` | uuid (optional) | — |

**Response:**
```json
{
  "items": [
    {
      "id": "uuid",
      "title": "Amoxicillin dosage inquiry",
      "is_title_generated": true,
      "created_at": "2026-05-08T10:00:00Z",
      "updated_at": "2026-05-08T10:05:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20
}
```

`title` starts as `"New Chat"` and is replaced in real-time once generated (see Title Updation below).

---

### `GET /api/v1/chats/{conversation_id}`

Get a single conversation with all its messages.

**Response:**
```json
{
  "id": "uuid",
  "title": "Amoxicillin dosage inquiry",
  "is_title_generated": true,
  "session_id": null,
  "patient_id": null,
  "created_at": "2026-05-08T10:00:00Z",
  "updated_at": "2026-05-08T10:05:00Z",
  "messages": [
    {
      "id": "uuid",
      "role": "user",
      "content": "What is the recommended dosage for Amoxicillin?",
      "artifacts": null,
      "created_at": "2026-05-08T10:00:00Z"
    },
    {
      "id": "uuid",
      "role": "assistant",
      "content": "Based on standard medical guidelines...",
      "artifacts": {
        "citations": {
          "count": 3,
          "items": [...]
        }
      },
      "created_at": "2026-05-08T10:00:05Z"
    }
  ]
}
```

---

### `DELETE /api/v1/chats/{conversation_id}`

Delete a conversation. Cascading deletes all messages.

**Response:** `204 No Content`

**Errors:** If not found or not owned by user, returns `404`.

---

## Events (SSE Push)

### `GET /api/v1/events`

Long-lived Server-Sent Events connection. Stays open while the tab is active. Receives push notifications for background events.

**Response stream:**
```
data: {"event_type":"chat_title_generated","data":{"conv_id":"uuid","title":"Amoxicillin dosage inquiry"},"timestamp":"2026-05-08T10:00:10Z"}

```

### Event Types

| `event_type` | When | `data` |
|---|---|---|
| `chat_title_generated` | Title generation completes | `conv_id`, `title` |

**Frontend flow:**
1. On app load, open `GET /api/v1/events` (keep-alive SSE)
2. Listen for `chat_title_generated` events
3. When received, update the conversation title everywhere:
   - Sidebar chat list
   - Session detail right panel dropdown
   - Chat header if the conversation is currently open

---

## Title Updation

Happens automatically after the first message stream completes:

1. Backend streams the full AI response
2. After `done` event, a **background task** generates a title via tiny LLM
3. Title is saved to DB
4. A `chat_title_generated` event is pushed via the `/events` SSE stream
5. Frontend receives the event and swaps `"New Chat"` with the real title everywhere

The frontend **must** show `"New Chat"` as a placeholder until the title event arrives.

---

## Session Detail Page Integration

The `GET /api/v1/sessions/{id}` response includes a `chats` field:

```json
{
  "id": "session-uuid",
  "title": "Follow-up Hypertension",
  "chats": [
    {
      "id": "uuid",
      "title": "Amoxicillin dosage inquiry",
      "is_title_generated": true,
      "created_at": "2026-05-08T10:00:00Z",
      "updated_at": "2026-05-08T10:05:00Z"
    }
  ]
}
```

- `chats` is sorted by `updated_at` descending (most recent first)
- `chats` is empty (`[]`) if no chats exist for this session
- When the user clicks the AI icon, show the most recent chat or create a new one
- When a title is generated via the `/events` SSE, update the dropdown entry in-place

---

## Agent Tools

The AI agent has access to:

| Tool | Description |
|---|---|
| `web_search` | Searches medical websites via Brave Search. Results include citations displayed in the UI. |
| `get_patient_history` | Fetches past consultation session summaries for a patient. Used when doctor asks about patient history. |

The frontend receives tool events as `tool_call` SSE chunks (start + end) so it can show loading indicators.

---

## Context & Linking Rules

| Scenario | `session_id` | `patient_id` | Context provided to agent |
|---|---|---|---|
| Chat from session page | ✓ | derived from session | Session title, status, clinical summary + patient name, DOB, gender, blood group |
| Standalone — about a patient | ✗ | ✓ | Patient name, DOB, gender, blood group |
| Standalone — general Q | ✗ | ✗ | None |
| Standalone — about a session | ✓ | ✗ | Session info only |

Patient info is automatically derived from the session's linked patient when `session_id` is set.

---

## File Locations

| File | Role |
|---|---|
| `src/api/v1/chat.py` | Chat routes |
| `src/api/v1/events.py` | SSE push events route |
| `src/modules/copilot/service.py` | Orchestration |
| `src/modules/copilot/builder.py` | State builder |
| `src/modules/copilot/handlers.py` | Event → SSE chunk |
| `src/modules/copilot/helpers.py` | SSE formatting |
| `src/schemas/api/chat.py` | API request/response schemas |
| `src/schemas/features/copilot.py` | Internal schemas (PatientInfo, SessionInfo) |
| `src/agent/graph.py` | LangGraph compiled graph |
| `src/agent/node.py` | Agent LLM node |
| `src/agent/tools.py` | Tool definitions |
| `src/agent/edges.py` | Conditional routing |
| `src/agent/state.py` | Agent state |
| `src/agent/events.py` | EventEmitter for tool status |
| `src/agent/helpers.py` | Context formatting |
| `src/content/prompts/chat.py` | System prompt, title prompt |
| `src/modules/patients/tools.py` | `get_patient_history` tool |
| `src/dependencies/services.py` | DI wiring |
| `src/dependencies/infra.py` | PubSubManager dep |
