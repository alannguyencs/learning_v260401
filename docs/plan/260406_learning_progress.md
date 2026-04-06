# Learning Progress Tab

**Feature**: Add a "Learning Progress" tab to the dashboard showing per-lesson progress cards grouped by book
**Plan Created:** 2026-04-06
**Status:** Plan
**Reference**:
- [Discussion — Learning Progress Tab](../discussion/260406_learning_progress_tab.md)
- [Abstract — Dashboard](../abstract/dashboard.md)
- [Technical — Dashboard](../technical/dashboard.md)
- [Technical — Learning Progress](../technical/learning_progress.md)
- [Technical — Revision Scheduling](../technical/revision_scheduling.md)

---

## Problem Statement

1. The `/dashboard` page currently only shows an Activity Log — a chronological table of raw events (LEARNT CHAPTER, SKIP, ANSWER, ROUND CREATED).
2. There is no way for users to see a high-level summary of their learning progress: how far through each lesson, which revision round they're on, quiz accuracy, or recall strength.
3. The data already exists across `user_chapter_progress`, `lesson_revision_rounds`, `quiz_answer_log`, and `user_quiz_recall` — it just needs to be aggregated and presented.

---

## Proposed Solution

Add a tab switcher to the Dashboard page with two tabs: "Activity Log" (existing) and "Learning Progress" (new). The Learning Progress tab displays per-lesson progress cards grouped by book, with 4 metrics per lesson:

1. **Chapters** — progress bar showing `learnt / total` chapters
2. **Revision** — current round status (e.g., "R0 open · 8/9 answered")
3. **Accuracy** — correct / total answers with percentage
4. **Recall** — average forgetting rate across quizzes in the lesson

A new API endpoint `GET /api/dashboard/learning-progress` aggregates data from existing tables. No new database tables or migrations needed.

---

## Current Implementation Analysis

### What Exists (keep as-is)

| Component | File | Status |
|-----------|------|--------|
| Activity log CRUD | `backend/src/crud/crud_dashboard.py` | Keep — `get_activity_log()` and `log_quiz_answer()` unchanged |
| Activity log endpoint | `backend/src/api/dashboard.py` | Keep — `GET /api/dashboard/activity-log` unchanged |
| Activity log schema | `backend/src/api/dashboard.py` | Keep — `ActivityLogEntry` unchanged |
| Dashboard route | `frontend/src/App.js` | Keep — `/dashboard` route unchanged |
| API service | `frontend/src/services/api.js` | Keep — `getActivityLog()` unchanged |
| All data model tables | `user_chapter_progress`, `chapters`, `lessons`, `books`, `lesson_revision_rounds`, `quiz_answer_log`, `user_quiz_recall`, `chapter_quizzes` | Keep — no schema changes |

### What Changes

| Component | Current | Proposed |
|-----------|---------|----------|
| `DashboardPage.jsx` | Single view: activity log table | Tab switcher with "Activity Log" and "Learning Progress" tabs |
| `backend/src/api/dashboard.py` | One endpoint | Add `GET /api/dashboard/learning-progress` |
| `backend/src/crud/crud_dashboard.py` | Activity log queries only | Add `get_learning_progress()` aggregation query |
| `frontend/src/services/api.js` | `getActivityLog()` only | Add `getLearningProgress()` |

---

## Implementation Plan

### Key Workflow

#### To Delete
None.

#### To Update
None.

#### To Add New

**New workflow**: Learning Progress data flow

```
User clicks "Learning Progress" tab on /dashboard
  │
  ▼
Frontend calls GET /api/dashboard/learning-progress
  │
  ▼
crud_dashboard.get_learning_progress(db, username)
  │
  ├── Query 1: chapters progress per lesson
  │     JOIN lessons, chapters, user_chapter_progress
  │     → lesson_id, total_chapters, learnt_chapters
  │
  ├── Query 2: latest revision round per lesson
  │     lesson_revision_rounds (latest by round_num per lesson)
  │     → lesson_id, round_num, status, quizzes_in_round, quizzes_answered
  │
  ├── Query 3: quiz accuracy per lesson
  │     quiz_answer_log aggregated
  │     → lesson_id, total_answers, correct_answers
  │
  ├── Query 4: average recall per lesson
  │     user_quiz_recall JOIN chapter_quizzes JOIN chapters
  │     → lesson_id, avg_forgetting_rate
  │
  └── Combine into per-lesson records, grouped by book
        → List[BookProgress] response
```

### Database Schema

#### To Delete
None.

#### To Update
None.

#### To Add New
None — all data is in existing tables.

### CRUD

#### To Delete
None.

#### To Update
None.

#### To Add New

**File**: `backend/src/crud/crud_dashboard.py`

`get_learning_progress(db: Session, username: str) -> list[dict]`

Single SQL query using CTEs to aggregate 4 metrics per lesson:

```sql
WITH chapter_progress AS (
    SELECT c.lesson_id,
           COUNT(c.id) AS total_chapters,
           COUNT(ucp.id) AS learnt_chapters
    FROM chapters c
    JOIN lessons l ON l.id = c.lesson_id
    LEFT JOIN user_chapter_progress ucp
        ON ucp.chapter_id = c.id AND ucp.username = :username
    GROUP BY c.lesson_id
),
latest_round AS (
    SELECT DISTINCT ON (lesson_id)
           lesson_id, round_num, status, quizzes_in_round, quizzes_answered
    FROM lesson_revision_rounds
    WHERE username = :username
    ORDER BY lesson_id, round_num DESC
),
quiz_accuracy AS (
    SELECT lesson_id,
           COUNT(*) AS total_answers,
           SUM(CASE WHEN is_correct THEN 1 ELSE 0 END) AS correct_answers
    FROM quiz_answer_log
    WHERE username = :username
    GROUP BY lesson_id
),
avg_recall AS (
    SELECT c.lesson_id,
           ROUND(AVG(uqr.forgetting_rate)::numeric, 2) AS avg_forgetting_rate
    FROM user_quiz_recall uqr
    JOIN chapter_quizzes cq ON cq.id = uqr.quiz_id
    JOIN chapters c ON c.id = cq.chapter_id
    WHERE uqr.username = :username
    GROUP BY c.lesson_id
)
SELECT l.id AS lesson_id,
       l.book_id,
       b.title AS book_title,
       l.lesson_index,
       l.title AS lesson_title,
       COALESCE(cp.total_chapters, 0) AS total_chapters,
       COALESCE(cp.learnt_chapters, 0) AS learnt_chapters,
       lr.round_num,
       lr.status AS round_status,
       lr.quizzes_in_round,
       lr.quizzes_answered AS round_quizzes_answered,
       COALESCE(qa.total_answers, 0) AS total_answers,
       COALESCE(qa.correct_answers, 0) AS correct_answers,
       ar.avg_forgetting_rate
FROM lessons l
JOIN books b ON b.book_id = l.book_id
LEFT JOIN chapter_progress cp ON cp.lesson_id = l.id
LEFT JOIN latest_round lr ON lr.lesson_id = l.id
LEFT JOIN quiz_accuracy qa ON qa.lesson_id = l.id
LEFT JOIN avg_recall ar ON ar.lesson_id = l.id
ORDER BY l.book_id, l.lesson_index;
```

Returns a list of dicts, one per lesson, with all metrics needed by the frontend.

### Services

#### To Delete
None.

#### To Update
None.

#### To Add New
None — the CRUD query is a direct aggregation; no business logic or orchestration needed.

### API Endpoints

#### To Delete
None.

#### To Update
None.

#### To Add New

**File**: `backend/src/api/dashboard.py`

| Method | Path | Auth | Response | Status |
|--------|------|------|----------|--------|
| GET | `/api/dashboard/learning-progress` | Session cookie | `List[LessonProgressEntry]` | 200 |

**`LessonProgressEntry` schema** (new Pydantic model in `backend/src/api/dashboard.py`):

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

Nullable fields: `round_num`, `round_status`, `quizzes_in_round`, `round_quizzes_answered`, `avg_forgetting_rate` (null when no data exists for that metric).

### Testing

#### To Delete
None.

#### To Update
None.

#### To Add New

**File**: `backend/tests/test_learning_progress_api.py`

| Test | Description |
|------|-------------|
| `test_learning_progress_unauthenticated` | Returns 401 without session |
| `test_learning_progress_empty` | Returns list with lessons but zero progress when user has no activity |
| `test_learning_progress_with_chapter_learnt` | `learnt_chapters` = 1 after marking one chapter |
| `test_learning_progress_with_quiz_answers` | `total_answers` and `correct_answers` reflect quiz_answer_log data |
| `test_learning_progress_with_revision_round` | `round_num`, `round_status`, `quizzes_in_round` populated |
| `test_learning_progress_with_recall` | `avg_forgetting_rate` computed from user_quiz_recall |
| `test_learning_progress_grouped_by_book` | Lessons ordered by book_id then lesson_index |

Final step: run pre-commit loop.

1. Run `source venv/bin/activate && pre-commit run --all-files`.
2. Fix any issues (e.g., lint errors, line count violations).
3. Re-run pre-commit again — Prettier may reformat the fixes and push files back over the line limit (max 300 lines per frontend file). If so, fix again (e.g., extract components to separate files to reduce line count durably).
4. Repeat until pre-commit passes cleanly on a full re-run with no new failures.

### Frontend

#### To Delete
None.

#### To Update

**`frontend/src/pages/DashboardPage.jsx`** — Refactor to add tab switching:

- Add `activeTab` state (`"activity"` | `"progress"`), default `"activity"`
- Extract existing activity log table into a conditional block under `activeTab === "activity"`
- Add tab switcher UI at the top: two buttons/links styled as tabs
  - Active tab: `text-white border-b-2 border-blue-500`
  - Inactive tab: `text-gray-400 hover:text-gray-200`
- When `activeTab === "progress"`, render the `LearningProgressView` component

**`frontend/src/services/api.js`** — Add `getLearningProgress()`:

```js
getLearningProgress: async () => {
  const response = await api.get("/api/dashboard/learning-progress");
  return response.data;
},
```

#### To Add New

**`frontend/src/components/LearningProgressView.jsx`** — New component:

- Fetches `getLearningProgress()` on mount
- Groups lessons by `book_id` / `book_title`
- Renders book section headers with book title
- Under each book, renders a lesson card for each lesson:

**Lesson card layout** (dark theme, matches existing `bg-gray-800` style):

```
┌─────────────────────────────────────────────────┐
│ Lesson 1: 20 Quantum Cheat Codes...             │
│                                                 │
│ Chapters   ████████░░░░░░░░░░  1/5  (20%)      │
│ Revision   R0 open · 8/9 answered               │
│ Accuracy   4/8 correct (50%)                    │
│ Recall     avg 0.87                             │
└─────────────────────────────────────────────────┘
```

- **Chapters progress bar**: `bg-gray-700` track, `bg-green-500` fill, width = `(learnt/total) * 100%`
- **Revision**: `round_num` + `round_status` + answered/total. Show "No revision yet" if null.
- **Accuracy**: `correct_answers / total_answers (percentage%)`. Show "No quizzes yet" if `total_answers = 0`.
- **Recall**: `avg_forgetting_rate` rounded to 2 decimals. Colour: green (`< 0.5`), yellow (`0.5–1.0`), red (`> 1.0`). Show "—" if null.
- **Not started state**: If `learnt_chapters = 0` and no round/answers, show muted "Not started" card.
- **Empty state**: If API returns empty list, show "No lessons available yet" with link to `/slides`.
- Loading and error states handled same as `DashboardPage`.

**`frontend/src/pages/SlidePage.jsx`** — Update the "Activity Log" link text to "Dashboard" (since the page now has two tabs, not just the log).

### Documentation

#### Abstract (`docs/abstract/`)

**Update `docs/abstract/dashboard.md`**:
- **Problem**: Add sentence about lacking high-level progress summary.
- **Solution**: Add paragraph about Learning Progress tab with per-lesson cards.
- **User Flow**: Add steps 5–7 for clicking Learning Progress tab and viewing cards.
- **Scope**: Add "Learning Progress tab with per-lesson metrics (chapters, revision, accuracy, recall)".
- **Acceptance Criteria**: Add criteria for tab switcher, card metrics, empty state.

**Update `docs/abstract/index.md`**:
- Update Dashboard description from "chronological log of all study interactions" to "Activity log and per-lesson learning progress".

#### Technical (`docs/technical/`)

**Update `docs/technical/dashboard.md`**:
- **Architecture**: Add `GET /api/dashboard/learning-progress` flow diagram.
- **Data Model**: Add `LessonProgressEntry` response schema.
- **API Layer**: Add new endpoint table row.
- **CRUD Layer**: Add `get_learning_progress()` function description.
- **Frontend**: Add `LearningProgressView` component description and tab switcher.

### Chrome Claude Extension Execution

After implementation is complete, execute the Chrome Claude Extension E2E tests defined in `docs/chrome_test/learning_progress.md`.

---

## Dependencies

- Existing tables: `books`, `lessons`, `chapters`, `user_chapter_progress`, `user_lesson_count`, `lesson_revision_rounds`, `quiz_answer_log`, `user_quiz_recall`, `chapter_quizzes`
- Existing dashboard page and route (`/dashboard`)
- Authentication system (session cookies)

## Open Questions

None — all data exists, no new tables needed, design confirmed in discussion.

---

## Change Request — 2026-04-06

**What changed:** Redesigned Learning Progress from per-lesson cards to per-book cards.

Each book card now contains:
1. A **lesson table** (columns: Lesson, Current Revision, Accuracy %)
2. An **accuracy trendline** (SVG chart) computed from a sliding window over the book's 119 most recent answers

**Trendline algorithm:**
- Fetch 119 most recent answers for the book (skips excluded)
- Create 20 windows of 100 data points each (sliding by 1)
- Each data point = correct answers per 100

**Backend:** `get_learning_progress` CRUD rewritten to return `List[BookProgressEntry]` with nested lessons and `accuracy_trend` list. Trendline computed in Python.

**Frontend:** `LearningProgressView.jsx` rewritten — book cards with HTML table + pure SVG trendline chart. No charting library.

**API schema:** `LessonProgressEntry` (flat) → `BookProgressEntry` (nested with trendline).
