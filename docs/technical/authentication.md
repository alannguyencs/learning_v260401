# Authentication — Technical Design

[< Prev: System Pipelines](./system_pipelines.md) | [Parent](./index.md)

## Related Docs
- Abstract: [abstract/authentication.md](../abstract/authentication.md)

## Architecture

```
+-----------+     +-------------+     +----------+
|  Frontend | --> |   Backend   | --> | Database |
|  (React)  |     |  (FastAPI)  |     | (Postgres)|
+-----------+     +-------------+     +----------+
  AuthContext       auth.py (JWT)       users table
  Login.jsx         login.py (cookie)
                    root.py (/me)
```

Two authentication mechanisms:
- **OAuth2 Bearer** (`POST /auth/token`) — returns a JWT in the response body. Used for tooling and API clients.
- **Session Cookie** (`POST /api/login/`) — sets an `HttpOnly` cookie. Used by the frontend for all requests.

All protected endpoints use `authenticate_user_from_request()`, which checks for authentication in two ways (in order):
1. Reads the `access_token` cookie (used by the frontend)
2. Falls back to the `Authorization: Bearer <token>` header (used by CLI tools and `curl`)

The first token found is decoded as a JWT and looked up against the database.

## Data Model

**`Users`**

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | Integer | PK, indexed |
| `username` | String | UNIQUE, NOT NULL |
| `hashed_password` | String | NOT NULL |
| `role` | String | nullable |

## Pipeline

### Session Restore

```
Page load
  │
  ▼
AuthContext calls GET /api/me
  │
  ▼
Read access_token cookie → decode JWT
  │
  ▼
get_user(username) from DB
  │
  ▼
Return {authenticated, user} to frontend
```

### Login

```
User submits login form
  │
  ▼
POST /api/login (username, password)
  │
  ▼
bcrypt.verify(password, hashed_password)
  │
  ▼
create_access_token(90d expiry)
  │
  ▼
Set-Cookie (HttpOnly, access_token)
  │
  ▼
Navigate to /quiz
```

### Logout

```
User clicks logout
  │
  ▼
POST /api/login/logout
  │
  ▼
Delete access_token cookie
  │
  ▼
Clear frontend auth state
```

## Backend — API Layer

| Method | Path | Auth | Request | Response | Status |
|--------|------|------|---------|----------|--------|
| POST | `/auth/token` | No | `application/x-www-form-urlencoded` (username, password) | `{access_token, token_type}` | 200 / 401 |
| POST | `/api/login/` | No | JSON `{username, password}` | `{success, message, user}` + Set-Cookie | 200 / 401 |
| POST | `/api/login/logout` | No | — | `{success, message}` + delete cookie | 200 |
| GET | `/api/me` | Cookie | — | `{authenticated, user}` | 200 (always) |

`GET /api/me` always returns 200. The frontend checks `authenticated` in the body.

## Backend — Service Layer

- **`auth.py`** — JWT utilities:
  - `authenticate_user(username, password)` — bcrypt verify, returns `Users` or `False`
  - `create_access_token(data, expires_delta=90d)` — HS256 JWT with `username` and `expire` claims
  - `get_current_user_from_token(token)` — decode JWT, fetch user from DB
  - `authenticate_user_from_request(request)` — check `access_token` cookie first, then fall back to `Authorization: Bearer` header; delegate to above
- **JWT config:** HS256, secret from `JWT_SECRET_KEY` env var, 90-day expiry, payload stores `username` and `expire` (ISO 8601).
- **Cookie config:** `HttpOnly=True`, `SameSite=Lax`, `Secure=False` (localhost), `Max-Age=7776000` (90 days), `Path=/`.

## Backend — CRUD Layer

**`crud_user.py`:**

| Function | Description |
|----------|-------------|
| `get_user_by_username(username)` | Query by username, returns `Users` or `None` |
| `get_user_by_id(user_id)` | Query by PK |
| `create_user(username, hashed_password, role)` | Insert new user |
| `update_user_password(user_id, new_hashed_password)` | Update password |
| `delete_user(user_id)` | Delete by PK |

## Frontend — Pages & Routes

| Route | Component | Auth |
|-------|-----------|------|
| `/login` | `Login.jsx` | No |
| `/quiz` | `QuizPage.jsx` | `ProtectedRoute` |
| `/dashboard` | `RecallDashboardPage.jsx` | `ProtectedRoute` |
| `/` | redirect to `/quiz` | `ProtectedRoute` |

## Frontend — Services & Hooks

- **`AuthContext.js`** — React context providing `user`, `authenticated`, `loading`, `login()`, `logout()`, `checkAuth()`.
  - On mount: calls `GET /api/me` to restore session
  - `login()`: calls `POST /api/login/`, sets state, navigates to `/quiz`
  - `logout()`: calls `POST /api/login/logout`, clears state
  - `useAuth()` hook exposes the context; throws if used outside `AuthProvider`
- **`api.js`** — axios instance with `withCredentials: true`. `baseURL` from `REACT_APP_API_URL` env var.

## Constraints & Edge Cases
- JWT secret must be set via `JWT_SECRET_KEY` env var
- `Secure=False` on cookie — must change for production HTTPS
- No token refresh mechanism; users re-authenticate after 90 days
- No registration endpoint; accounts are pre-created

## Component Checklist

- [ ] Database model — `Users` table
- [ ] POST `/auth/token` — OAuth2 bearer token endpoint
- [ ] POST `/api/login/` — cookie-based login
- [ ] POST `/api/login/logout` — cookie deletion
- [ ] GET `/api/me` — session status check
- [ ] `auth.py` — JWT creation, verification, bcrypt
- [ ] `crud_user.py` — user CRUD operations
- [ ] `AuthContext.js` — React auth state management
- [ ] `Login.jsx` — login form page
- [ ] `ProtectedRoute` — redirect unauthenticated users to `/login`

---

[< Prev: System Pipelines](./system_pipelines.md) | [Parent](./index.md)
