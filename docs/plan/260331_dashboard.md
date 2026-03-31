# Dashboard — Activity Log Page

**Feature**: A `/dashboard` page showing the user's full interaction history (chapters learnt, quizzes answered/skipped, revision rounds created) as a chronological table.
**Plan Created:** 2026-03-31
**Status:** Plan
**Reference**:
- [Abstract — Slide Stack](../abstract/slide_stack.md)
- [Technical — Slide Stack](../technical/slide_stack.md)
- [Technical — Learning Progress](../technical/learning_progress.md)
- [Technical — Revision Scheduling](../technical/revision_scheduling.md)

---

## Problem Statement

1. There is no UI to review past interactions with the system. Users cannot see what they have learnt, answered, or skipped.
2. Answered quiz events have **no timestamp** — `user_quiz_recall` stores outcome (`forgetting_rate`, `review_count`) but not `answered_at`. This makes it impossible to place answer events in chronological order alongside skip and chapter-learnt events.
3. Without an activity log, users cannot verify the spaced-repetition system is behaving correctly (e.g., confirm that quizzes only appear after their chapter is learnt).

---

## Proposed Solution

### New table: `quiz_answer_log`

A dedicated append-only log table (mirroring `quiz_skip_log`) that records each quiz answer event with a timestamp:

```
quiz_answer_log
  id            SERIAL PK
  username      VARCHAR FK → users.username
  quiz_id       INTEGER FK → chapter_quizzes.id
  lesson_id     INTEGER FK → lessons.id
  round_num     INTEGER
  is_correct    BOOLEAN
  answered_at   TIMESTAMP DEFAULT NOW()
```

### New endpoint: `GET /api/dashboard/activity-log`

Returns a unified, chronologically-ordered list of all user interactions, built from a UNION of four event sources:

| Source table | Action label |
|---|---|
| `user_chapter_progress` | `LEARNT CHAPTER` |
| `quiz_skip_log` | `SKIP` |
| `quiz_answer_log` | `ANSWER` |
| `lesson_revision_rounds` | `ROUND CREATED (R{n} {status})` |

Each row carries: `event_time`, `action`, `book_id`, `lesson_index`, `lesson_title`, `chapter_id`, `answer_result` (correct/wrong/—), `recall_rate` (forgetting_rate or —).

### New page: `/dashboard`

A protected React page rendering the activity log as a table. Linked from the `/slides` page via a nav link.

---

## Current Implementation Analysis

### What Exists (keep as-is)

| Component | File | Status |
|---|---|---|
| Quiz skip logging | `backend/src/crud/crud_slides.py` | Keep — `log_quiz_skip()` unchanged |
| Learning progress CRUD | `backend/src/crud/crud_learning_progress.py` | Keep — no changes |
| Revision scheduling CRUD | `backend/src/crud/crud_revision.py` | Keep — no changes |
| `QuizSkipLog` model | `backend/src/models/slide_management.py` | Keep — new model added alongside |
| `slides.py` API | `backend/src/api/slides.py` | Update — write to `quiz_answer_log` on answer |
| `App.js` router | `frontend/src/App.js` | Update — add `/dashboard` route |
| `api.js` service | `frontend/src/services/api.js` | Update — add `getActivityLog()` |
| `SlidePage.jsx` | `frontend/src/pages/SlidePage.jsx` | Update — add nav link to `/dashboard` |

### What Changes

| Component | Current | Proposed |
|---|---|---|
| Answer events | No timestamp; only in `user_quiz_recall` | Logged to `quiz_answer_log` with `answered_at` |
| Activity visibility | No endpoint or UI | `GET /api/dashboard/activity-log` + `/dashboard` page |
| Navigation | Only `/slides` and `/login` | Add `/dashboard` as protected route with link from slides |

---

## Implementation Plan

### Key Workflow

#### Answer event write path (updated)

```
POST /api/slides/quizzes/{quiz_id}/respond
  └─ QuizGrader.grade()             (unchanged)
  └─ RevisionService.record_quiz_response()   (unchanged)
  └─ crud_dashboard.log_quiz_answer()         ← NEW: write to quiz_answer_log
  └─ return feedback to frontend              (unchanged)
```

#### Dashboard read path (new)

```
GET /api/dashboard/activity-log
  └─ authenticate via session cookie
  └─ crud_dashboard.get_activity_log(db, username)
       ├─ UNION user_chapter_progress   → LEARNT CHAPTER rows
       ├─ UNION quiz_skip_log           → SKIP rows
       ├─ UNION quiz_answer_log         → ANSWER rows (+ recall_rate from user_quiz_recall)
       └─ UNION lesson_revision_rounds  → ROUND CREATED rows
  └─ return sorted list (event_time ASC)
```

#### To Delete
None.

#### To Update
- `backend/src/api/slides.py` — in `respond_to_quiz()`, after `RevisionService.record_quiz_response()`, call `crud_dashboard.log_quiz_answer()` when `is_correct is not None`.

#### To Add New
- `scripts/sql/005_quiz_answer_log.sql` — migration
- `backend/src/models/slide_management.py` — `QuizAnswerLog` model (added alongside `QuizSkipLog`)
- `backend/src/crud/crud_dashboard.py` — `log_quiz_answer()` and `get_activity_log()`
- `backend/src/api/dashboard.py` — `GET /api/dashboard/activity-log` endpoint
- `backend/src/api/api_router.py` — include dashboard router
- `frontend/src/pages/DashboardPage.jsx` — activity log table page
- `frontend/src/services/api.js` — `getActivityLog()` method
- `frontend/src/App.js` — `/dashboard` protected route
- `frontend/src/pages/SlidePage.jsx` — nav link to `/dashboard`

---

### Database Schema

#### To Delete
None.

#### To Update
None.

#### To Add New

**Migration file**: `scripts/sql/005_quiz_answer_log.sql`

```sql
-- Migration: Quiz Answer Log
-- Records each quiz answer event with a timestamp for dashboard display

CREATE TABLE IF NOT EXISTS quiz_answer_log (
    id SERIAL PRIMARY KEY,
    username VARCHAR NOT NULL REFERENCES users(username),
    quiz_id INTEGER NOT NULL REFERENCES chapter_quizzes(id),
    lesson_id INTEGER NOT NULL REFERENCES lessons(id),
    round_num INTEGER NOT NULL,
    is_correct BOOLEAN NOT NULL,
    answered_at TIMESTAMP NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_qal_user ON quiz_answer_log(username, answered_at);
```

**ORM model**: `QuizAnswerLog` in `backend/src/models/slide_management.py`

```python
class QuizAnswerLog(Base):
    __tablename__ = "quiz_answer_log"
    id = Column(Integer, primary_key=True)
    username = Column(String, ForeignKey("users.username"), nullable=False)
    quiz_id = Column(Integer, ForeignKey("chapter_quizzes.id"), nullable=False)
    lesson_id = Column(Integer, ForeignKey("lessons.id"), nullable=False)
    round_num = Column(Integer, nullable=False)
    is_correct = Column(Boolean, nullable=False)
    answered_at = Column(DateTime, server_default=func.now(), nullable=False)
```

---

### CRUD

#### To Delete
None.

#### To Update
None.

#### To Add New

**File**: `backend/src/crud/crud_dashboard.py`

```python
def log_quiz_answer(
    db: Session,
    username: str,
    quiz_id: int,
    lesson_id: int,
    round_num: int,
    is_correct: bool,
) -> None:
    """Append one row to quiz_answer_log."""

def get_activity_log(db: Session, username: str) -> list[dict]:
    """
    Return all interaction events for the user, sorted by event_time ASC.
    Each dict has keys:
      event_time, action, book_id, lesson_index, lesson_title,
      chapter_id, answer_result, recall_rate
    Built from UNION of:
      user_chapter_progress, quiz_skip_log, quiz_answer_log,
      lesson_revision_rounds
    For ANSWER rows, LEFT JOIN user_quiz_recall to get forgetting_rate.
    """
```

---

### Services

#### To Delete
None.

#### To Update

**File**: `backend/src/api/slides.py` — `respond_to_quiz()` endpoint

After `RevisionService.record_quiz_response(...)`, add:

```python
if body.is_correct is not None:
    crud_dashboard.log_quiz_answer(
        db,
        username=user.username,
        quiz_id=quiz_id,
        lesson_id=quiz.lesson_id,   # resolved from quiz → chapter → lesson
        round_num=body.round_num,
        is_correct=body.is_correct,
    )
```

#### To Add New
None (no new service class — logic is in CRUD and the existing `slides.py` endpoint).

---

### API Endpoints

#### To Delete
None.

#### To Update
None.

#### To Add New

**File**: `backend/src/api/dashboard.py`

```
GET /api/dashboard/activity-log
Auth: session cookie (ProtectedRoute)
Response 200:
[
  {
    "event_time": "2026-03-31T11:30:52",
    "action": "LEARNT CHAPTER",
    "book_id": "themitmonk",
    "lesson_index": 1,
    "lesson_title": "20 Quantum Cheat Codes...",
    "chapter_id": 1,
    "answer_result": null,
    "recall_rate": null
  },
  {
    "event_time": "2026-03-31T11:31:35",
    "action": "ANSWER",
    "book_id": "themitmonk",
    "lesson_index": 1,
    "lesson_title": "20 Quantum Cheat Codes...",
    "chapter_id": 1,
    "answer_result": "wrong",
    "recall_rate": 1.2
  },
  ...
]
```

**File**: `backend/src/api/api_router.py` — include dashboard router:

```python
from src.api.dashboard import router as dashboard_router
api_router.include_router(dashboard_router, prefix="/api", tags=["dashboard"])
```

---

### Testing

#### To Delete
None.

#### To Update
None.

#### To Add New

**File**: `backend/tests/test_dashboard_api.py`

Unit / integration tests:
- `test_activity_log_empty` — authenticated user with no activity returns `[]`
- `test_activity_log_learnt_chapter` — after marking chapter learnt, LEARNT CHAPTER row appears
- `test_activity_log_skip` — after skipping quiz, SKIP row appears with `answer_result=null`, `recall_rate=null`
- `test_activity_log_answer_wrong` — after wrong answer, ANSWER row has `answer_result="wrong"` and `recall_rate=1.2`
- `test_activity_log_answer_correct` — after correct answer, ANSWER row has `answer_result="correct"` and `recall_rate < 1.0`
- `test_activity_log_round_created` — revision round rows appear
- `test_activity_log_ordered` — all rows sorted by `event_time` ascending
- `test_activity_log_unauthenticated` — returns 401

**Pre-commit loop**:
1. Run `source venv/bin/activate && pre-commit run --all-files`.
2. Fix any issues (lint, line count violations).
3. Re-run — Prettier may reformat frontend files over 300 lines; extract components if needed.
4. Repeat until clean.

---

### Frontend

#### To Delete
None.

#### To Update

**`frontend/src/App.js`** — add protected `/dashboard` route:
```jsx
<Route path="/dashboard" element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />
```

**`frontend/src/services/api.js`** — add:
```js
getActivityLog: () => api.get('/api/dashboard/activity-log'),
```

**`frontend/src/pages/SlidePage.jsx`** — add a "Dashboard" nav link in the top bar.

#### To Add New

**`frontend/src/pages/DashboardPage.jsx`**

- Fetches `GET /api/dashboard/activity-log` on mount
- Renders a scrollable table with columns: `#`, `Time`, `Action`, `book_id`, `lesson_index`, `lesson_title`, `chapter_id`, `answer_result`, `recall_rate`
- Empty state: "No activity yet. Start learning on the Slides page." with link to `/slides`
- Loading state: spinner while fetching
- Action column styling:
  - `LEARNT CHAPTER` — bold, green text
  - `SKIP` — grey text
  - `ANSWER` — blue text
  - `ROUND CREATED` — italic, muted text
- `answer_result` column: "correct" in green, "wrong" in red, "—" in grey
- `recall_rate` column: numeric value (2 decimal places) or "—"
- `chapter_id` column: numeric or "—" for round events

---

### Documentation

#### Abstract (`docs/abstract/`)

**New file**: `docs/abstract/dashboard.md`
- Sections: Problem, Solution, User Flow, Scope, Acceptance Criteria
- Explains the dashboard as a way for users to review their own learning history
- User flow: navigate to `/dashboard` → see chronological table of all interactions

#### Technical (`docs/technical/`)

**New file**: `docs/technical/dashboard.md`
- Architecture: UNION query across 4 tables, new `quiz_answer_log` table, new API endpoint
- Data Model: `quiz_answer_log` schema, `ActivityLogEntry` response schema
- API Layer: `GET /api/dashboard/activity-log` — auth, response shape
- CRUD Layer: `log_quiz_answer()`, `get_activity_log()`
- Frontend: `DashboardPage.jsx`, route, api.js method

**Update**: `docs/technical/slide_stack.md`
- API Endpoints section: note that `POST /api/slides/quizzes/{id}/respond` now also writes to `quiz_answer_log`

**Update**: `docs/technical/index.md`
- Add entry: Dashboard — Activity log page showing interaction history

**Update**: `docs/abstract/index.md`
- Add entry: Dashboard — Review learning history

---

### Chrome Claude Extension Execution

After implementation is complete, execute `docs/chrome_test/dashboard.md`.

---

## Dependencies

- `users` table — username FK
- `chapter_quizzes`, `chapters`, `lessons`, `books` — content hierarchy for JOIN
- `user_chapter_progress` — LEARNT CHAPTER events
- `quiz_skip_log` — SKIP events
- `user_quiz_recall` — `forgetting_rate` for recall_rate column
- `lesson_revision_rounds` — ROUND CREATED events
- Authentication (session cookie) — all dashboard endpoints are protected

## Open Questions

None.

---

## Change Request — 2026-03-31

**Request**: R0 completes (and R1 is created) only when BOTH conditions are met:
1. More than 50% of total lesson quizzes have been answered by the user.
2. All chapters in the lesson have been marked as learnt.

**Why**: Without the second condition, R0 could complete while the user is still reading chapters, causing quizzes from unlearnt chapters to be routed to R1 (not due) instead of R0 (immediately available). This left chapters 2–4 quizzes inaccessible.

**What Changes:**

| Layer | Change |
|---|---|
| `crud_learning_progress.py` | Add `all_lesson_chapters_learnt(db, username, lesson_id)` |
| `revision_service.py` | `threshold_met` now requires both 50% answered AND all chapters learnt |
| `test_revision_service.py` | Update completion tests; add negative test for partial-chapters case |
| `docs/technical/revision_scheduling.md` | Update Round Completion Threshold algorithm and pipeline |
| `docs/chrome_test/dashboard.md` | Update ROUND CREATED label from "R0 done" to "R0" |
