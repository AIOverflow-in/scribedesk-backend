# Auth Module

## Overview

Cookie-based session auth using Redis. No JWT. The backend sets an HttpOnly `session` cookie on login/register and clears it on logout.

**Base path:** `/api/v1/auth`

---

## Routes

### `POST /api/v1/auth/register`

Create a new account with email + password.

**Request body:**
```json
{
  "email": "doctor@clinic.com",
  "password": "securepass123",
  "profile": {
    "first_name": "John",
    "last_name": "Doe",
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

- `profile` — doctor's personal info (`last_name`, `gender`, `speciality` optional)
- `clinic` — clinic details (`street`, `city`, `state`, `pincode` optional; `name` + `country` required)
- Country is always a 2-letter ISO code (e.g. `"US"`, `"IN"`)

**Response `200`:**
```json
{
  "status": "success",
  "session_token": "a1b2c3d4e5f6...",
  "onboarding_pending": false
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
  "session_token": "a1b2c3d4e5f6...",
  "onboarding_pending": false
}
```

**Errors:** `401` (invalid email or password)

---

### `POST /api/v1/auth/google`

Sign in or sign up with Google. Uses **popup mode** (no redirect callback needed on frontend).

**Frontend flow:**
1. User clicks "Continue with Google"
2. Google Identity Services popup opens
3. User picks account + consents
4. Popup closes, Google JS returns an `idToken` to your callback
5. Frontend sends this token to this route

**Request body:**
```json
{
  "idToken": "eyJhbGciOiJSUzI1NiIs..."
}
```

**Response `200` (existing user):**
```json
{
  "status": "success",
  "session_token": "a1b2c3d4e5f6...",
  "onboarding_pending": false
}
```

**Response `200` (new user — redirect to onboarding):**
```json
{
  "status": "success",
  "session_token": "a1b2c3d4e5f6...",
  "onboarding_pending": true
}
```

**Errors:**
- `409` — An account with this email already uses email/password. Tell user to sign in with password, then link Google in settings.

---

### `POST /api/v1/auth/onboarding`

Complete onboarding after Google signup — save personal profile and create clinic. **Requires auth** (user already has a session from `/google`).

**Request body:**
```json
{
  "profile": {
    "first_name": "John",
    "last_name": "Doe",
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

**Response `200`:**
```json
{
  "status": "success",
  "session_token": null,
  "onboarding_pending": false
}
```

Frontend checks `onboarding_pending: false` → redirect to dashboard. No new session token needed (existing session stays active).

---

### `POST /api/v1/auth/providers/connect`

Link an OAuth provider (Google, Apple, Microsoft) from settings. **Requires auth.**

**Request body:**
```json
{
  "provider": "google",
  "token": "eyJhbGciOiJSUzI1NiIs..."
}
```

- `provider` — one of `google`, `apple`, `microsoft`
- `token` — the OAuth idToken from the provider (frontend acquires this via popup first)

**Response `200`:**
```json
{
  "status": "success"
}
```

**Errors:** `409` (already linked)

---

### `GET /api/v1/auth/providers`

List all OAuth providers linked to the current account. **Requires auth.**

**Response `200`:**
```json
{
  "status": "success",
  "providers": [
    {
      "id": "uuid",
      "provider": "email",
      "email": "doctor@clinic.com",
      "is_primary": true,
      "linked_at": "2026-05-04T12:00:00Z",
      "last_used_at": "2026-05-04T14:30:00Z"
    },
    {
      "id": "uuid",
      "provider": "google",
      "email": "doctor@gmail.com",
      "is_primary": false,
      "linked_at": "2026-05-04T13:00:00Z",
      "last_used_at": null
    }
  ]
}
```

Use this to determine what to show in settings:
- `provider: "email"` — **never shown** in connected accounts (it's implicit)
- Any other provider — show as connected with disconnect option
- If a provider is NOT in the list → show "Connect"

---

### `DELETE /api/v1/auth/providers/{provider_id}`

Disconnect an OAuth provider. **Requires auth.**

**Response `200`:**
```json
{
  "status": "success"
}
```

**Errors:**
- `404` — provider not found
- `400` — cannot disconnect `email` provider
- `400` — cannot disconnect your only login method (set a password first)

**Settings disconnect rule:**
- `count(providers) > 1` → allow disconnect of any OAuth provider
- `count(providers) = 1` → **hide all disconnect buttons** (user would be locked out)
- `provider === "email"` → never show disconnect for this (it's not shown at all)

---

### `POST /api/v1/auth/set-password`

Set or change password. **Requires auth.** For Google-only users — allows them to later disconnect Google.

**Request body:**
```json
{
  "password": "newpassword123",
  "confirm_password": "newpassword123"
}
```

**Response `200`:**
```json
{
  "status": "success"
}
```

---

### `POST /api/v1/auth/logout`

Revoke current session. Reads `session` cookie, deletes it from Redis + clears the cookie.

**Request body:** none

**Response `200`:**
```json
{
  "status": "success"
}
```

---

## Auth Flow Summary

| Scenario | Route | Response |
|----------|-------|----------|
| New user, email/pass | `POST /register` | session token, `onboarding_pending: false` |
| Existing user, email/pass | `POST /login` | session token, `onboarding_pending: false` |
| New user, Google signup | `POST /google` | session token, `onboarding_pending: true` → redirect to `/onboarding` |
| Existing Google user | `POST /google` | session token, `onboarding_pending: false` |
| Email exists, clicks Google | `POST /google` | `409` — must sign in with password first, then link in settings |
| Google user, no password | `POST /onboarding` | `onboarding_pending: false` → redirect to dashboard |
| Link Google in settings | `POST /providers/connect` | `{ status: "success" }` |
| Disconnect in settings | `DELETE /providers/{id}` | `{ status: "success" }` |
| Set password (Google-only) | `POST /set-password` | `{ status: "success" }` |
| Logout | `POST /logout` | `{ status: "success" }` |

---

## Cookie Configuration

| Property | Value |
|----------|-------|
| Name | `session` |
| HttpOnly | `true` |
| SameSite | `lax` |
| Max-Age | `SESSION_EXPIRY_SECONDS` (default 86400 = 24h) |

All authenticated routes read this cookie via the `get_current_user_id` dependency.

---

## Session Management (Redis)

- Tokens are hex strings generated via `secrets.token_hex(32)`
- Stored in Redis under `session:{token}` as `{"user_id": "...", "role": "doctor"}`
- **Sliding TTL:** every request refreshes the 24h expiry
- On logout, the key is deleted from Redis

---

## Frontend Integration

- Call `/login` or `/google` — the backend sets the `session` cookie automatically
- Subsequent API calls include the cookie automatically (same-origin)
- For cross-origin (e.g. localhost:5173 → localhost:8000), use `credentials: "include"` on fetch/axios, and ensure CORS `allow_origins` includes your frontend origin
- **Google popup:** use Google Identity Services (`google.accounts.oauth2.initTokenClient`) — sends the `idToken` to your callback JS, NOT a redirect URI
- After `/google` returns `onboarding_pending: true`, redirect to `/onboarding` page (no password field shown — user signed in with Google)
- On the onboarding page, call `GET /users/me` to prefill name/email, then submit profile + clinic to `POST /onboarding`

### Settings page logic

Fetch `GET /auth/providers` and render:

| User has | Show in settings |
|----------|------------------|
| email only | Nothing in "Connected Accounts". Password section shows "Change Password" |
| google only | Google: connected + **no disconnect**. "Set Password" option shown |
| email + google | Google: connected + **disconnect allowed**. Password: "Change Password" |
| (any) provider not linked | Show "Connect" button for that provider |

---

## File Locations

| File | Role |
|------|------|
| `src/api/v1/auth.py` | Routes |
| `src/modules/auth/service.py` | Business logic |
| `src/schemas/api/auth.py` | Request/response schemas |
| `src/dependencies/auth.py` | Auth deps (HTTP + WS) |
| `src/dependencies/services.py` | Service DI wiring |
| `src/infrastructure/external/google_oauth.py` | Google ID token verification |
| `src/infrastructure/persistence/redis/sessions.py` | SessionManager |
| `src/infrastructure/persistence/postgres/repos/auth_repo.py` | Auth DB operations |
| `src/api/v1/helpers.py` | `handle_auth_result` (cookie setter) |
