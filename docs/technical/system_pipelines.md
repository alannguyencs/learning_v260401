# System Pipelines

[Parent](./index.md) | [Next: Authentication >](./authentication.md)

## Login Pipeline — [details](./authentication.md)

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
create_access_token(90d expiry, HS256 JWT)
  │
  ▼
Set-Cookie (HttpOnly, access_token)
  │
  ▼
Navigate to /
```

## Session Restore Pipeline — [details](./authentication.md)

```
Page load / refresh
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
  │
  ▼
authenticated? ──No──> Redirect to /login
      │
     Yes
      │
      ▼
Render protected page
```

---

[Parent](./index.md) | [Next: Authentication >](./authentication.md)
