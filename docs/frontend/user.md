# User Module

## Overview

Read/update the authenticated user's profile and clinic details. All routes require the `session` cookie.

**Base path:** `/api/v1/users`

---

## Routes

### `GET /api/v1/users/me`

Get the full profile with clinic details.

**Response `200`:**
```json
{
  "id": "uuid",
  "email": "doctor@clinic.com",
  "first_name": "John",
  "last_name": "Doe",
  "dob": "1985-06-15",
  "gender": "Male",
  "speciality": "Cardiology",
  "signature_url": null,
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-01-01T00:00:00Z",
  "clinic": {
    "name": "Heart Care Clinic",
    "street": "123 Main St",
    "city": "Boston",
    "state": "MA",
    "pincode": "02101",
    "country": "US",
    "logo_url": null
  }
}
```

`clinic` is `null` if not set up (should never happen since register creates one).

---

### `PATCH /api/v1/users/me`

Update personal profile fields.

**Request body** (all fields optional):
```json
{
  "first_name": "Johnny",
  "last_name": "Doe",
  "dob": "1985-06-15",
  "gender": "Male",
  "speciality": "Neurology"
}
```

Gender must match: `^(Male|Female|Other|Prefer not to say)$`

**Response:** Same as `GET /me`.

---

### `PATCH /api/v1/users/me/clinic`

Update clinic details.

**Request body** (all fields optional):
```json
{
  "name": "Heart Care Clinic",
  "street": "456 Oak Ave",
  "city": "Boston",
  "state": "MA",
  "pincode": "02101",
  "country": "US"
}
```

Country is a 2-letter ISO code if provided.

**Response:** Same as `GET /me`.

---

## Frontend Integration

Display the clinic info block alongside the profile. Use `PATCH /me/clinic` for a separate "Clinic Settings" form and `PATCH /me` for the personal profile form.

The response is always the full `UserProfileResponse`, so you can update local state with the returned data.

---

## Dependencies

- `CurrentUserIdDep` — auth from session cookie
- `UserServiceDep` — injects `UserService`

---

## File Locations

| File                          | Role                              |
|-------------------------------|-----------------------------------|
| `src/api/v1/users.py`         | Routes                            |
| `src/modules/users/service.py` | Business logic                    |
| `src/schemas/api/user.py`     | Request/response schemas          |
