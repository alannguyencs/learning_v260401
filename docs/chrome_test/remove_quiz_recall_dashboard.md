# Chrome E2E Tests — Remove Quiz & Recall Dashboard (Auth Smoke)

## Remarks

- **Port**: Frontend runs on `http://localhost:3000`, backend on `http://localhost:8000`.
- **Goal**: After all quiz/recall dashboard files are deleted, verify that authentication still works end-to-end and the app does not crash.
- **Sign-in flow**: Navigate to `http://localhost:3000/login`, enter username and password, click Login.
- **Sign-out flow**: Click Logout button (available once logged in).
- **Cleanup**: No test data created by these tests; auth state is reset on each sign-out.

---

## Database Pre-Interaction

No additional seed data required. Tests use existing user account created during initial setup.

**Cleanup**: No cleanup SQL needed — these tests only verify auth behavior and do not mutate application data.

---

## Pre-requisite

Before running any test, ensure you are **signed out** (no session cookie). Navigate to `http://localhost:3000/login` and confirm the login form is displayed.

---

## Test 1 — Login with valid credentials

**Test name**: Valid login redirects to app
**User**: existing user (e.g., `alan`)
**Steps**:
- [ ] Navigate to `http://localhost:3000/login`
- [ ] Verify the login form is displayed with username and password fields
- [ ] Enter valid username and password
- [ ] Click the Login button
- [ ] Verify no crash or 500 error occurs
- [ ] Verify the user is redirected away from `/login`

**Expected UI state**: Login form disappears; user lands on the post-login landing page (no error page).
**Error handling**: If a crash or blank white screen appears, flag immediately — likely an import error from a deleted file.
**Report**: IN QUEUE
- Improvement Proposals:
  + good to have - post-login landing page - add a clear home/landing page after login instead of a redirect to a removed route

---

## Test 2 — Login with invalid credentials

**Test name**: Invalid credentials show error message
**User**: existing user
**Steps**:
- [ ] Navigate to `http://localhost:3000/login`
- [ ] Enter an incorrect password for a valid username
- [ ] Click the Login button
- [ ] Verify an error message is displayed (e.g., "Invalid credentials")
- [ ] Verify the user stays on `/login`

**Expected UI state**: Error message visible below the form; form fields remain editable.
**Error handling**: If the app crashes instead of showing an error, flag immediately.
**Report**: IN QUEUE
- Improvement Proposals:
  + good to have - specific error messages - distinguish between "user not found" and "wrong password"

---

## Test 3 — Unauthenticated access redirects to login

**Test name**: Protected routes redirect to login when not authenticated
**User**: unauthenticated
**Steps**:
- [ ] Ensure user is signed out (clear cookies or use incognito)
- [ ] Navigate directly to `http://localhost:3000/`
- [ ] Verify the user is redirected to `/login`
- [ ] Verify the login form is displayed

**Expected UI state**: Login page displayed; no crash or blank screen.
**Error handling**: If a blank screen or JS error appears, flag immediately — likely broken ProtectedRoute due to removed imports.
**Report**: IN QUEUE
- Improvement Proposals:
  + good to have - redirect preservation - after login, redirect user to the originally requested URL

---

## Test 4 — Session persists across page refresh

**Test name**: Authenticated session survives page reload
**User**: existing user
**Steps**:
- [ ] Sign in with valid credentials
- [ ] Verify successful login (no crash)
- [ ] Refresh the browser page (`Cmd+R` / `F5`)
- [ ] Verify the user remains on the authenticated page (not redirected to `/login`)

**Expected UI state**: User stays logged in; no flash of the login page.
**Error handling**: If the session is lost on refresh, flag immediately — likely an AuthContext issue.
**Report**: IN QUEUE
- Improvement Proposals:
  + good to have - session expiry indicator - show user when their session is about to expire

---

## Test 5 — Logout clears session

**Test name**: Logout redirects to login and clears authentication
**User**: existing user
**Steps**:
- [ ] Sign in with valid credentials
- [ ] Click the Logout button (or trigger logout flow)
- [ ] Verify the user is redirected to `/login`
- [ ] Attempt to navigate back to the protected area (e.g., `http://localhost:3000/`)
- [ ] Verify the user is redirected back to `/login` (session is truly cleared)

**Expected UI state**: Login form displayed after logout; protected routes not accessible.
**Error handling**: If the session is not cleared after logout, flag immediately.
**Report**: IN QUEUE
- Improvement Proposals:
  + good to have - logout confirmation - show brief "You have been logged out" message before redirecting
