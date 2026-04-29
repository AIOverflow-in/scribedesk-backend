# Reports Module

## Overview

Generate clinical documents (SOAP notes, prescriptions, referral letters, etc.) from session transcripts using templates. The LLM (fast_llm) fills template placeholders with context from the session transcripts, clinical summary, patient info, and doctor info.

**Base path:** `/api/v1`

---

## Routes

### `POST /api/v1/reports`

Generate a new report.

**Request body:**
```json
{
  "session_id": "uuid",
  "template_id": "uuid",
  "additional_context": "Patient also mentioned mild headache (optional, max 2000 chars)"
}
```

**Response `201`:**
```json
{
  "id": "uuid",
  "session_id": "uuid",
  "template_id": "uuid",
  "title": "SOAP Note",
  "content": "## Subjective\nPatient presents for follow-up...\n\n## Objective\n...",
  "report_metadata": null,
  "is_signed": false,
  "signed_at": null,
  "content_hash": null,
  "created_at": "...",
  "updated_at": "..."
}
```

The report is generated server-side by the LLM and saved to the DB.

---

### `GET /api/v1/reports/{report_id}`

Get a single report.

**Response `200`:** `ReportResponse`.

---

## Schemas

### `CreateReportRequest`

| Field                | Type   | Notes |
|----------------------|--------|-------|
| `session_id`         | UUID   | Required — which session's transcripts to use |
| `template_id`        | UUID   | Required — which template to use |
| `additional_context` | string? | Extra instructions for the LLM (max 2000 chars) |

### `ReportResponse`

| Field            | Type      | Notes |
|------------------|-----------|-------|
| `id`             | UUID      |       |
| `session_id`     | UUID      |       |
| `template_id`    | UUID      |       |
| `title`          | string    | Copied from template name at generation time |
| `content`        | string    | Markdown — the generated report body |
| `report_metadata`| dict?     | Extensible metadata field |
| `is_signed`      | bool      | Default `false` |
| `signed_at`      | datetime? | Timestamp of signing |
| `content_hash`   | string?   | SHA-256 hash of content (for signature verification) |
| `created_at`     | datetime  |       |
| `updated_at`     | datetime  |       |

### `ReportMetadata`

Lightweight schema embedded in `SessionResponse.reports[]`:

| Field           | Type     | Notes |
|-----------------|----------|-------|
| `id`            | UUID     |       |
| `title`         | string   | Template name |
| `template_name` | string   | Resolved from template relation |
| `created_at`    | datetime |       |

---

## How Report Generation Works

When `POST /reports` is called:

1. **Validate session** — exists and belongs to the user
2. **Validate template** — exists (system or user)
3. **Build context:**
   - **Transcripts** — all transcripts from the session (not just first N, unlike title gen)
   - **Clinical summary** — the session's `clinical_summary` field
   - **Patient info** — name, age, gender, blood group (from linked patient)
   - **Doctor info** — name, email, speciality, clinic address (from user + clinic)
   - **Additional context** — optional doctor-provided notes
4. **LLM generation** — calls `fast_llm` with the prompt:
   ```
   Template: {template content with placeholders}
   Transcripts: {all transcripts}
   Clinical Summary: {clinical_summary}
   Patient Info: {patient details}
   Doctor Info: {doctor details}
   Additional Context: {doctor notes}
   ```
5. **Save** — creates a `Report` row in the DB

The LLM is instructed to:
- Follow the template structure
- Fill placeholders like `[patient_name]`, `[chief_complaint]` from transcripts
- Output clean Markdown
- Make reasonable clinical inferences if info is missing
- Keep medical terminology accurate

---

## Frontend Integration

### Flow

1. From the session detail view, show the `reports[]` list
2. User picks a template → `POST /reports` with `session_id` + `template_id`
3. Poll or wait for response → render `content` as Markdown
4. Display in a report viewer

### Displaying Reports

The `content` field is Markdown. Use a Markdown renderer (e.g., `marked`, `react-markdown`) to display.

### Future: Signing

The `is_signed`, `signed_at`, and `content_hash` fields are ready for a digital signature feature. The flow would be:
1. User reviews the report
2. Click "Sign" → backend hashes content, stores hash, sets `is_signed = true` + `signed_at`
3. Signed reports are locked from editing

---

## Dependencies

- `CurrentUserIdDep` — auth from session cookie
- `ReportServiceDep` — injects `ReportService`

---

## File Locations

| File                          | Role |
|-------------------------------|------|
| `src/api/v1/reports.py`       | Routes |
| `src/modules/reports/service.py` | Business logic + context builder |
| `src/modules/reports/ai.py`   | LLM report generation helper |
| `src/schemas/api/reports.py`  | Request/response schemas |
| `src/content/prompts/reports.py` | `ReportPrompts` (prompt template) |
