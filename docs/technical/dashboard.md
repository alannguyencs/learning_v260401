# Dashboard — Technical Design

[Parent](./index.md)

## Architecture

```
GET /api/dashboard/activity-log
    → crud_dashboard.get_activity_log(db, username)
         UNION user_chapter_progress   → LEARNT CHAPTER rows
         UNION quiz_skip_log           → SKIP rows
         UNION quiz_answer_log         → ANSWER rows (+ forgetting_rate from user_quiz_recall)
         UNION lesson_revision_rounds  → ROUND CREATED rows
    → List[ActivityLogEntry] sorted by event_time ASC

GET /api/dashboard/learning-progress
    → crud_dashboard.get_learning_progress(db, username)
         CTE chapter_progress   → learnt/total chapters per lesson
         CTE latest_round       → latest revision round per lesson
         CTE quiz_accuracy      → correct/total answers per lesson
         CTE avg_recall         → average forgetting_rate per lesson
    → List[LessonProgressEntry] ordered by book_id, lesson_index
```

Quiz answers are also written to `quiz_answer_log` from the slides respond endpoint:

```
POST /api/slides/quizzes/{id}/respond
    → ... (grading + revision unchanged)
    → crud_dashboard.log_quiz_answer()   ← write path
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
  "forgetting_rate": 1.2
}
```

`chapter_id`, `answer_result`, and `forgetting_rate` are `null` for ROUND CREATED rows.
`answer_result` and `forgetting_rate` are `null` for LEARNT CHAPTER and SKIP rows.

### `LessonProgressEntry` response schema

```json
{
  "lesson_id": 2,
  "book_id": "themitmonk",
  "book_title": "theMITmonk",
  "lesson_index": 1,
  "lesson_title": "20 Quantum Cheat Codes...",
  "total_chapters": 5,
  "learnt_chapters": 1,
  "round_num": 0,
  "round_status": "open",
  "quizzes_in_round": 9,
  "round_quizzes_answered": 8,
  "total_answers": 8,
  "correct_answers": 4,
  "avg_forgetting_rate": 0.87
}
```

Nullable fields: `round_num`, `round_status`, `quizzes_in_round`, `round_quizzes_answered`, `avg_forgetting_rate` (null when no data exists).

## API Layer

**File**: `backend/src/api/dashboard.py`

```
GET /api/dashboard/activity-log
Auth: session cookie
Response 200: List[ActivityLogEntry]
Response 401: not authenticated

GET /api/dashboard/learning-progress
Auth: session cookie
Response 200: List[LessonProgressEntry]
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

Returns rows sorted by `event_time ASC`. `forgetting_rate` is rounded to 2 decimal places.

### `get_learning_progress(db, username) -> list[dict]`

Single CTE-based SQL query aggregating four metrics per lesson:
- `chapter_progress` — COUNT chapters vs COUNT user_chapter_progress rows
- `latest_round` — DISTINCT ON lesson_id, ORDER BY round_num DESC
- `quiz_accuracy` — COUNT + SUM(is_correct) from quiz_answer_log
- `avg_recall` — AVG(forgetting_rate) from user_quiz_recall JOIN chapter_quizzes JOIN chapters

Returns one row per lesson, ordered by `book_id, lesson_index`.

## Frontend

**`frontend/src/pages/DashboardPage.jsx`**
- Tab switcher with "Activity Log" and "Learning Progress" tabs
- `activeTab` state defaults to `"activity"`
- Activity Log tab: unchanged behaviour (fetches and renders scrollable table)
- Learning Progress tab: renders `LearningProgressView` component

**`frontend/src/components/LearningProgressView.jsx`**
- Fetches `GET /api/dashboard/learning-progress` on mount
- Groups lessons by `book_id` / `book_title`
- Renders book section headers with book title
- Under each book, renders lesson cards with 4 metrics:
  - Chapters progress bar (green fill on gray-700 track)
  - Revision status (round_num + status + answered/total)
  - Accuracy (correct/total with percentage)
  - Recall (avg forgetting rate, colour-coded: green < 0.5, yellow 0.5-1.0, red > 1.0)
- Not started state for lessons with no progress
- Empty state with link to `/slides`

**`frontend/src/App.js`** — `/dashboard` route unchanged.

**`frontend/src/services/api.js`** — `getLearningProgress()` calls `GET /api/dashboard/learning-progress`.

**`frontend/src/pages/SlidePage.jsx`** — "Dashboard" link in top-right corner (was "Activity Log").

## Testing

**File**: `backend/tests/test_learning_progress_api.py`

| Test | Description |
|------|-------------|
| `test_learning_progress_unauthenticated` | Returns 401 without session |
| `test_learning_progress_empty` | Returns lessons with zero progress |
| `test_learning_progress_with_chapter_learnt` | learnt_chapters = 1 after marking |
| `test_learning_progress_with_quiz_answers` | total_answers and correct_answers reflect data |
| `test_learning_progress_with_revision_round` | round_num, round_status populated |
| `test_learning_progress_with_recall` | avg_forgetting_rate computed |
| `test_learning_progress_grouped_by_book` | Ordered by book_id then lesson_index |

**File**: `backend/tests/test_dashboard_api.py` — existing activity log tests unchanged.
