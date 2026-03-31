# Dashboard — Technical Design

[Parent](./index.md)

## Architecture

```
GET /api/dashboard/activity-log
    → crud_dashboard.get_activity_log(db, username)
         UNION user_chapter_progress   → LEARNT CHAPTER rows
         UNION quiz_skip_log           → SKIP rows
         UNION quiz_answer_log         → ANSWER rows (+ recall_rate from user_quiz_recall)
         UNION lesson_revision_rounds  → ROUND CREATED rows
    → List[ActivityLogEntry] sorted by event_time ASC
```

Quiz answers are also written to `quiz_answer_log` from the slides respond endpoint:

```
POST /api/slides/quizzes/{id}/respond
    → ... (grading + revision unchanged)
    → crud_dashboard.log_quiz_answer()   ← NEW write path
```

## Data Model

### `quiz_answer_log`

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | Integer | PK |
| `username` | String | FK → users.username, NOT NULL |
| `quiz_id` | Integer | FK → chapter_quizzes.id, NOT NULL |
| `lesson_id` | Integer | FK → lessons.id, NOT NULL |
| `round_num` | Integer | NOT NULL |
| `is_correct` | Boolean | NOT NULL |
| `answered_at` | Timestamp | NOT NULL, DEFAULT NOW() |

Index: `idx_qal_user` on `(username, answered_at)`.

Migration: `scripts/sql/005_quiz_answer_log.sql`

### `ActivityLogEntry` response schema

```json
{
  "event_time": "2026-03-31T11:30:52",
  "action": "LEARNT CHAPTER | SKIP | ANSWER | ROUND CREATED (Rn status)",
  "book_id": "themitmonk",
  "lesson_index": 1,
  "lesson_title": "20 Quantum Cheat Codes...",
  "chapter_id": 1,
  "answer_result": "correct | wrong | null",
  "recall_rate": 1.2
}
```

`chapter_id`, `answer_result`, and `recall_rate` are `null` for ROUND CREATED rows.
`answer_result` and `recall_rate` are `null` for LEARNT CHAPTER and SKIP rows.

## API Layer

**File**: `backend/src/api/dashboard.py`

```
GET /api/dashboard/activity-log
Auth: session cookie (same as slides endpoints)
Response 200: List[ActivityLogEntry]
Response 401: not authenticated
```

Registered in `api_router.py` with prefix `/api` and tag `dashboard`.

## CRUD Layer

**File**: `backend/src/crud/crud_dashboard.py`

### `log_quiz_answer(db, username, quiz_id, lesson_id, round_num, is_correct) -> None`

Inserts one row into `quiz_answer_log`. Called from `slides.py` after every non-skip quiz response.

### `get_activity_log(db, username) -> list[dict]`

Executes a UNION of four queries across:
- `user_chapter_progress` — LEARNT CHAPTER events
- `quiz_skip_log` — SKIP events
- `quiz_answer_log` — ANSWER events, LEFT JOINed with `user_quiz_recall` for `forgetting_rate`
- `lesson_revision_rounds` — ROUND CREATED events

Returns rows sorted by `event_time ASC`. `recall_rate` is rounded to 2 decimal places.

## Frontend

**`frontend/src/pages/DashboardPage.jsx`**
- Fetches `GET /api/dashboard/activity-log` on mount
- Renders scrollable table with columns: `#`, `Date`, `Time`, `Action`, `book_id`, `lesson_index`, `lesson_title`, `chapter_id`, `answer_result`, `recall_rate`
- Action column colour-coded: LEARNT CHAPTER (green bold), SKIP (grey), ANSWER (blue), ROUND CREATED (italic muted)
- `answer_result`: "correct" green, "wrong" red, "—" grey
- Empty state: message + link to `/slides`
- Loading and error states handled

**`frontend/src/App.js`** — `/dashboard` added as a `ProtectedRoute`.

**`frontend/src/services/api.js`** — `getActivityLog()` calls `GET /api/dashboard/activity-log`.

**`frontend/src/pages/SlidePage.jsx`** — "Activity Log" link in top-right corner.

## Testing

**File**: `backend/tests/test_dashboard_api.py`

| Test | Description |
|------|-------------|
| `test_activity_log_unauthenticated` | Returns 401 without session |
| `test_activity_log_empty` | Returns `[]` when no activity exists |
| `test_learnt_chapter_appears` | LEARNT CHAPTER row present after marking chapter |
| `test_skip_appears` | SKIP row with null answer_result and recall_rate |
| `test_wrong_answer_appears` | ANSWER row with answer_result=wrong, recall_rate=1.2 |
| `test_correct_answer_appears` | ANSWER row with answer_result=correct, recall_rate<1 |
| `test_rows_ordered_by_time` | All event_times in ascending order |
| `test_round_created_appears` | ROUND CREATED row with null chapter_id |
