# Auth Providers Design (v1)

## Schema

### `users` table (modified)

```
password_hash  →  REMOVED (moved to user_auth_providers)
```

No other changes. `users` holds only identity/profile.

### `user_auth_providers` table (new)

```
id                UUID          PK
user_id           UUID          FK → users.id
provider          VARCHAR(20)   'email' | 'google' | 'apple' | 'microsoft'
provider_user_id  VARCHAR(255)  Google's `sub`, Apple's `user_id`, etc. NULL for 'email'
email             VARCHAR(255)  Email used for THIS provider (can differ from users.email)
password_hash     VARCHAR(255)  Only for provider='email', NULL for OAuth
is_primary        BOOLEAN       First method they signed up with
linked_at         TIMESTAMP     When this method was linked
last_used_at      TIMESTAMP     Updated on every login via this method

UNIQUE(provider, provider_user_id)   — for OAuth lookups
INDEX(user_id)                        — for settings page queries
```

## Package to install

```
google-auth==2.38.0
```

Used server-side to verify Google's ID token signature. That's it — no frontend JS library needed on the backend.

## Flow: Google sign-in (popup mode, no callback URL)

```
1. User clicks "Continue with Google" on frontend
2. Google's Identity Services popup opens, user picks account + consents
3. Popup closes, Google JS library returns an idToken to frontend JS callback
4. Frontend sends: POST /api/auth/google  { idToken: "eyJ..." }
5. Backend:
   a. Verify idToken using google.auth.id_token.verify_oauth2_token()
   b. Extract { sub (google user id), email, name, picture }
   c. Lookup: user_auth_providers WHERE provider='google' AND provider_user_id = sub
        → Found:     update last_used_at, create session, return token
        → Not found:
            Lookup: user_auth_providers WHERE provider='email' AND email = info.email
              → Found:  return 409 { code: "PROVIDER_MISMATCH", message: "Account exists with email/password. Sign in first, then link Google in settings." }
              → Neither: create user + user_auth_providers row (google), create session, return token + onboarding_pending: true
```

## Flow: Existing auth routes changes

### Register (POST /api/auth/register)

- No change to the route itself
- Backend no longer stores `password_hash` on `User` model
- Instead, inserts `user_auth_providers` row with `provider='email'`, `password_hash`, `is_primary=true`

### Login (POST /api/auth/login)

- Finds user by email
- Looks up the `user_auth_providers` row where `provider='email'`
- Verifies password against `password_hash` in that row (not on User model)
- Updates `last_used_at`
- Creates Redis session

## Routes: new

| Method | Path | Purpose |
|--------|------|---------|
| POST | /api/auth/google | Google sign in / sign up |
| POST | /api/auth/providers/connect/google | Link Google from settings (for existing email users) |
| DELETE | /api/auth/providers/{provider_id} | Disconnect an OAuth provider |
| POST | /api/auth/set-password | Set a password (for Google-only users who want to disconnect) |

## Routes: modified

| Method | Path | Change |
|--------|------|--------|
| POST | /api/auth/register | Writes provider row instead of user.password_hash |
| POST | /api/auth/login | Reads password_hash from provider row |

## Files that change

| File | What |
|------|------|
| `src/infrastructure/persistence/postgres/models.py` | Add `UserAuthProvider` model, remove `password_hash` from `User` |
| `src/infrastructure/persistence/postgres/repos/auth_repo.py` | Add methods for provider CRUD |
| `src/infrastructure/external/google_oauth.py` | Google token verification logic |
| `src/modules/auth/service.py` | Refactor login/register to use providers, add google_login, link/disconnect, set_password |
| `src/api/v1/auth.py` | Add Google route, link/disconnect/set-password routes |
| `src/schemas/api/auth.py` | Add GoogleLoginRequest, ConnectProviderRequest, SetPasswordRequest schemas |
| `src/core/security.py` | (minor) password_hash is no longer on User |

## Settings page logic

| User has | Settings shows |
|----------|----------------|
| email only | Nothing in "Connected Accounts". Password section shows "Change Password" |
| google only | Google: connected, **no disconnect**. "Set Password" option shown |
| email + google | Google: connected + **disconnect allowed**. Password: "Change Password" |
| google only tries disconnect | Block. "Set a password first before disconnecting Google." |
