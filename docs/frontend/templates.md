# Templates Module

## Overview

Templates define the structure for generated reports. Two kinds:

- **System templates** (`is_system: true`) — seeded by the backend, visible to all users, read-only
- **User templates** (`is_system: false`) — created by the current user, editable/deletable

**Base path:** `/api/v1`

---

## Routes

### `GET /api/v1/templates`

List all templates available to the user (system templates + user's own custom templates).

**Response `200`:**
```json
[
  {
    "id": "uuid",
    "name": "SOAP Note",
    "root_type": "notes",
    "sub_type": "soap",
    "content": "## Subjective\n[chief_complaint]...",
    "is_system": true,
    "user_id": null,
    "created_at": "...",
    "updated_at": "..."
  }
]
```

---

### `POST /api/v1/templates`

Create a custom template.

**Request body:**
```json
{
  "name": "My Custom Template",
  "root_type": "notes",
  "content": "## Section\n[placeholder]..."
}
```

`root_type` must be one of: `"notes"`, `"letters"`, `"prescription"`.

**Response `201`:** The created `TemplateResponse` with `is_system: false` and your `user_id`.

---

### `GET /api/v1/templates/{template_id}`

Get a single template by ID (system or user).

---

### `PATCH /api/v1/templates/{template_id}`

Update your own template. **Cannot update system templates** (returns `403`).

**Request body** (all optional):
```json
{
  "name": "Renamed Template",
  "content": "## Updated content..."
}
```

---

### `DELETE /api/v1/templates/{template_id}`

Delete your own template. **Cannot delete system templates** (returns `403`).

**Response `200`:**
```json
{ "status": "success" }
```

---

## Schemas

### `TemplateResponse`

| Field       | Type      | Notes                        |
|-------------|-----------|------------------------------|
| `id`        | UUID      |                              |
| `name`      | string    | Template display name        |
| `root_type` | string    | `"notes"`, `"letters"`, `"prescription"` |
| `sub_type`  | string?   | Set by system templates only |
| `content`   | string    | Template body with placeholders |
| `is_system` | bool      | `true` = seeded, read-only   |
| `user_id`   | UUID?     | Owner; `null` for system     |
| `created_at`| datetime  |                              |
| `updated_at`| datetime  |                              |

---

## Frontend Integration

- Show system + user templates in a single list; visually distinguish system templates (lock icon, no edit/delete button)
- Use the template `id` when creating a report (`POST /reports` takes `template_id`)
- The `content` field uses bracket placeholders like `[patient_name]`, `[chief_complaint]` — the backend LLM fills these during report generation

---

## Seeded System Templates

| Name                   | root_type      |
|------------------------|----------------|
| SOAP Note              | `notes`        |
| Progress Note          | `notes`        |
| History & Physical     | `notes`        |
| Discharge Summary      | `notes`        |
| Consultation Note      | `notes`        |
| Referral Letter        | `letters`      |
| Discharge Letter       | `letters`      |
| Patient Summary Letter | `letters`      |
| Sick Note              | `letters`      |
| Prescription           | `prescription` |

---

## Dependencies

- `CurrentUserIdDep` — auth from session cookie
- `TemplateServiceDep` — injects `TemplateService`

---

## File Locations

| File                          | Role                              |
|-------------------------------|-----------------------------------|
| `src/api/v1/templates.py`     | Routes                            |
| `src/modules/templates/service.py` | Business logic                |
| `src/schemas/api/templates.py` | Request/response schemas          |
| `src/content/templates/clinical.py` | 5 note templates             |
| `src/content/templates/letters.py`  | 4 letter templates            |
| `src/content/templates/prescriptions.py` | 1 prescription template |
| `src/seeders/templates_seeder.py` | DB seeder script              |
