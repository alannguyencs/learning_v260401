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
         per-lesson: lesson_title, latest round, accuracy
         per-book: sliding-window accuracy trendline (20 points from 119 answers)
    → List[BookProgressEntry] ordered by book_id
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

### `BookProgressEntry` response schema

```json
{
  "book_id": "themitmonk",
  "book_title": "theMITmonk",
  "lessons": [
    {
      "lesson_title": "20 Quantum Cheat Codes...",
      "round_num": 1,
      "round_status": "open",
      "total_answers": 29,
      "correct_answers": 13
    }
  ],
  "accuracy_trend": [65, 63, 62, 60, 58, ...]
}
```

`accuracy_trend` is a list of up to 20 integers (0–100), each representing correct answers per 100 in a sliding window. Empty list if fewer than 100 answers exist for the book.

## Algorithms

### Accuracy Trendline (sliding window)

1. Fetch the 119 most recent `quiz_answer_log` rows for the book (non-skip, ordered by `answered_at DESC`).
2. Reverse to chronological order.
3. Create 20 windows of 100 answers each:
   - Window 1: answers[0..99]
   - Window 2: answers[1..100]
   - ...
   - Window 20: answers[19..118]
4. For each window, count correct answers → that count is the data point (out of 100).
5. If fewer than 100 answers exist, return empty list.
6. If between 100 and 118 answers exist, return fewer than 20 points (one point per extra answer beyond 99).

## API Layer

**File**: `backend/src/api/dashboard.py`

```
GET /api/dashboard/activity-log
Auth: session cookie
Response 200: List[ActivityLogEntry]
Response 401: not authenticated

GET /api/dashboard/learning-progress
Auth: session cookie
Response 200: List[BookProgressEntry]
Response 401: not authenticated
```

Registered in `api_router.py` with prefix `/api` and tag `dashboard`.

## CRUD Layer

**File**: `backend/src/crud/crud_dashboard.py`

### `log_quiz_answer(db, username, quiz_id, lesson_id, round_num, is_correct) -> None`

Inserts one row into `quiz_answer_log`. Called from `slides.py` after every non-skip quiz response.

### `get_activity_log(db, username) -> list[dict]`

Executes a UNION of four queries. Returns rows sorted by `event_time ASC`.

### `get_learning_progress(db, username) -> list[dict]`

Returns per-book data with nested lessons and accuracy trendline:
1. Query per-lesson metrics (latest round, accuracy) grouped by book
2. Query 119 most recent answers per book for trendline computation
3. Compute sliding window trendline in Python
4. Group into book-level dicts with `lessons` list and `accuracy_trend` list

## Frontend

**`frontend/src/pages/DashboardPage.jsx`**
- Tab switcher with "Activity Log" and "Learning Progress" tabs
- `activeTab` state defaults to `"activity"`
- Activity Log tab: unchanged behaviour
- Learning Progress tab: renders `LearningProgressView` component

**`frontend/src/components/LearningProgressView.jsx`**
- Fetches `GET /api/dashboard/learning-progress` on mount
- Renders one card per book
- Each card contains:
  - Book title header
  - Lesson table with columns: Lesson, Revision, Accuracy
  - SVG trendline chart below the table (pure SVG, no charting library)
- Empty state with link to `/slides`

**`frontend/src/services/api.js`** — `getLearningProgress()` calls `GET /api/dashboard/learning-progress`.

## Testing

**File**: `backend/tests/test_learning_progress_api.py`

| Test | Description |
|------|-------------|
| `test_learning_progress_unauthenticated` | Returns 401 without session |
| `test_learning_progress_empty` | Returns books with empty lessons when no activity |
| `test_learning_progress_with_lesson_data` | Lesson row has round_num, accuracy |
| `test_learning_progress_accuracy_trend_empty` | accuracy_trend is [] when < 100 answers |
| `test_learning_progress_grouped_by_book` | One entry per book |

**File**: `backend/tests/test_dashboard_api.py` — existing activity log tests unchanged.
