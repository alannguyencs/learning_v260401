# Testing Context

[< Prev: Dashboard](./dashboard.md) | [Parent](./index.md)

## Base URLs

- **Frontend:** `http://localhost:3999`
- **Backend:** `http://localhost:8999`
- **API Docs:** `http://localhost:8999/docs`

## Test Users

| Role    | Username | Password     | Notes                          |
|---------|----------|--------------|--------------------------------|
| student | `alan`   | _(see .env)_ | Primary user; owns all content |

> The password is stored in the local Postgres `users` table. There is no default seeded password — the account is created manually or via the sign-up flow.

## Sign-in Procedure

1. Navigate to `http://localhost:3999/login`
2. Enter **Username** and **Password** in the login form
3. Click **Login**
4. → Redirected to `/slides` on success

## Sign-out Procedure

1. Click the logout button (or navigate directly to `http://localhost:3999/login`)
2. The session cookie is cleared; the user is shown the login page

## Database

- **Engine:** PostgreSQL
- **Host:** `127.0.0.1:5432`
- **Database name:** `learning_v2604`
- **DB user:** `alan` (no password in local environment)

## General Test Notes

- All Chrome E2E tests are run against the **local** running instance (not staging/production).
- Start the application before running tests: `bash start_app.sh` from the project root.
- Each test spec includes its own **Database Pre-Interaction** section with seed SQL and cleanup DELETE statements. Run these against the local Postgres DB (e.g., via `psql -U alan learning_v2604`) before each test session.
- Screenshots are saved under `data/chrome_test_images/{test_spec_slug}/`.

---

[< Prev: Dashboard](./dashboard.md) | [Parent](./index.md)
