# Patients Module

## Overview

CRUD for patient records. Scoped to the authenticated user — each patient is owned by one user.

**Base path:** `/api/v1`

---

## Routes

### `GET /api/v1/patients`

List patients with pagination.

**Query params:**

| Param      | Type  | Default | Description      |
|------------|-------|---------|------------------|
| `page`     | int   | 1       | Page number      |
| `page_size`| int   | 20      | Items per page   |

**Response `200`:**
```json
{
  "items": [
    {
      "id": "uuid",
      "full_name": "Jane Smith",
      "identifier": "MRN-001",
      "date_of_birth": "1990-03-20",
      "gender": "Female",
      "email": "jane@example.com",
      "blood_group": "O+",
      "created_at": "2025-01-01T00:00:00Z",
      "updated_at": "2025-01-01T00:00:00Z"
    }
  ],
  "total": 42,
  "page": 1,
  "page_size": 20
}
```

---

### `POST /api/v1/patients`

Create a new patient.

**Request body:**
```json
{
  "full_name": "Jane Smith",
  "identifier": "MRN-001",
  "date_of_birth": "1990-03-20",
  "gender": "Female",
  "email": "jane@example.com",
  "blood_group": "O+"
}
```

All fields except `full_name` are optional.

**Response `201`:** The created `PatientResponse`.

---

### `GET /api/v1/patients/{patient_id}`

Get a single patient.

**Response `200`:** `PatientResponse`.

---

### `PATCH /api/v1/patients/{patient_id}`

Update a patient. All fields optional.

**Response `200`:** Updated `PatientResponse`.

---

### `DELETE /api/v1/patients/{patient_id}`

Delete a patient.

**Response `200`:**
```json
{ "status": "success" }
```

---

## Schemas

### `PatientResponse`

| Field          | Type      | Notes              |
|----------------|-----------|--------------------|
| `id`           | UUID      |                    |
| `full_name`    | string    | Required           |
| `identifier`   | string?   | MRN / external ID  |
| `date_of_birth`| date?     | ISO format         |
| `gender`       | string?   | Free text          |
| `email`        | string?   |                    |
| `blood_group`  | string?   | e.g. "O+", "A-"    |
| `created_at`   | datetime  |                    |
| `updated_at`   | datetime  |                    |

### `CreatePatientRequest` / `UpdatePatientRequest`

Same fields as above but without `id`, `created_at`, `updated_at`. `UpdatePatientRequest` has all fields optional.

---

## Frontend Integration

Standard CRUD UI. The paginated list response uses the generic `PaginatedResponse[T]` pattern — the `items` array contains the patient objects.

Use `identifier` for external MRN linkage if your hospital system uses one.

---

## Dependencies

- `CurrentUserIdDep` — auth from session cookie
- `PatientServiceDep` — injects `PatientService`

---

## File Locations

| File                          | Role                              |
|-------------------------------|-----------------------------------|
| `src/api/v1/patients.py`      | Routes                            |
| `src/modules/patients/service.py` | Business logic                 |
| `src/schemas/api/patients.py` | Request/response schemas          |
