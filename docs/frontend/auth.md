# Auth Module

## Overview

Cookie-based session auth using Redis. No JWT. Token exchange happens via a `session` cookie (HttpOnly, SameSite=Lax) set by the backend on login/register and cleared on logout.

**Base path:** `/api/v1/auth`

---

## Routes

### `POST /api/v1/auth/register`

Create a new account.

**Request body:**
```json
{
  "email": "doctor@clinic.com",
  "password": "securepass123",
  "profile": {
    "first_name": "John",
    "last_name": "Doe",
    "dob": "1985-06-15",
    "gender": "Male",
    "speciality": "Cardiology"
  },
  "clinic": {
    "name": "Heart Care Clinic",
    "street": "123 Main St",
    "city": "Boston",
    "state": "MA",
    "pincode": "02101",
    "country": "US"
  }
}
```

- `profile` — doctor's personal info (last_name, dob, gender, speciality optional)
- `clinic` — clinic details (street, city, state, pincode optional; name + country required)
- Country is a 2-letter ISO code (e.g., `"US"`, `"IN"`)

**Response `200` / `201`:**
```json
{
  "status": "success",
  "session_token": "a1b2c3d4e5f6..."
}
```

Also sets the `session` cookie.

**Errors:** `409` (email already exists)

---

### `POST /api/v1/auth/login`

Authenticate with email + password.

**Request body:**
```json
{
  "email": "doctor@clinic.com",
  "password": "securepass123"
}
```

**Response `200`:**
```json
{
  "status": "success",
  "session_token": "a1b2c3d4e5f6..."
}
```

Also sets the `session` cookie.

**Errors:** `401` (invalid email or password)

---

### `POST /api/v1/auth/logout`

Revoke the current session. Reads the `session` cookie and deletes it from Redis + clears the cookie.

**Request body:** none (cookie read automatically)

**Response `200`:**
```json
{
  "status": "success"
}
```

---

## Cookie Configuration

| Property   | Value                |
|------------|----------------------|
| Name       | `session`            |
| HttpOnly   | `true`               |
| SameSite   | `lax`                |
| Max-Age    | `SESSION_EXPIRY_SECONDS` (default 86400 = 24h) |

All authenticated routes read this cookie via the `get_current_user_id` dependency.

---

## Session Management (Redis)

- Tokens are hex strings generated via `secrets.token_urlsafe(48)`
- Stored in Redis under `session:{token}` as `{"user_id": "...", "role": "doctor"}`
- **Sliding TTL:** every request refreshes the 24h expiry
- On logout, the key is deleted from Redis

---

## Frontend Integration

- Call `/login` with credentials, the backend sets the `session` cookie
- Subsequent API calls automatically include the cookie (works in same-origin setups)
- For cross-origin (localhost:5173 → localhost:8000), ensure `credentials: "include"` on fetch/axios and the CORS `allow_origins` includes the frontend origin
- **Swagger UI:** The "Authorize" button does not appear because cookie auth is not a standard OpenAPI security scheme. Use the login endpoint directly — the cookie will be set in the browser context. For programmatic use/cURL, capture the `Set-Cookie` header manually.

---

## Dependencies

- `AuthServiceDep` — injects the auth service (repo + session manager)
- `CurrentUserIdDep` — reads the cookie, returns `str(uuid)` — used on all protected routes
- `WsCurrentUserIdDep` — reads `?token=` query param, returns `str(uuid)` — used on WebSocket routes

---

## File Locations

| File                          | Role                              |
|-------------------------------|-----------------------------------|
| `src/api/v1/auth.py`          | Routes                            |
| `src/modules/auth/service.py` | Business logic (register/login/logout) |
| `src/dependencies/auth.py`    | Auth deps (HTTP + WS)             |
| `src/schemas/api/auth.py`     | Request/response schemas          |
| `src/infrastructure/persistence/redis/sessions.py` | SessionManager |
| `src/api/v1/helpers.py`       | `handle_auth_result` (cookie setter) |
