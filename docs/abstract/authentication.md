# Authentication

[Parent](./index.md)

**Status:** Plan

## Related Docs
- Technical: [technical/authentication.md](../technical/authentication.md)

## Problem

Users need a secure way to identify themselves so the system can store and retrieve their personal quiz history, recall data, and learning progress.

## Solution

Users log in with a username and password. After successful login, a session is created that keeps the user authenticated for subsequent interactions. All features in the application require the user to be logged in first.

## User Flow

```
User opens the application
        |
        v
Login page is displayed
        |
        v
User enters username and password
        |
        v
[Credentials valid?] --No--> Error message shown --> Re-enter credentials
        |
       Yes
        |
        v
Session created, user redirected to quiz page
```

## Scope
- Included: username/password login, session management, logout
- Not included: user registration (accounts are pre-created), password reset, social login (e.g. Google), multi-factor authentication

## Acceptance Criteria
- [ ] User can log in with a valid username and password
- [ ] Invalid credentials display a clear error message
- [ ] After login, the user remains authenticated across page refreshes
- [ ] All application pages redirect to login if the user is not authenticated

---

[Parent](./index.md)
