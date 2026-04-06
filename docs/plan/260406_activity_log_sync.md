# Activity Log Sync

**Feature**: Add a `slide_history` table so the Activity Log dashboard survives db-compress/db-load transfers between computers
**Plan Created:** 2026-04-06
**Status:** Cancelled
**Reference**:
- [Abstract — Dashboard](../abstract/dashboard.md)
- [Technical — Dashboard](../technical/dashboard.md)
- [Technical — Slide Stack](../technical/slide_stack.md)
- [Chrome Test — Activity Log Sync](../chrome_test/activity_log_sync.md)

---

## Problem Statement

1. The Activity Log dashboard (`/dashboard`) builds its view from a UNION of 4 tables: `user_chapter_progress`, `quiz_skip_log`, `quiz_answer_log`, and `lesson_revision_rounds`.
2. When the database is exported via `/db-compress` and restored via `/db-load` on another computer, the dashboard shows "No activity yet" because the exported SQL files only contain data that was present at export time.
3. The current approach works but is fragile — 4 separate tables must all export and import correctly for the dashboard to reconstruct the history.
4. There is no single source of truth for slide interaction history. The chronological order is reconstructed at query time from 4 different timestamp columns.

---

## Proposed Solution

Add a `slide_history` table that acts as a unified append-only event log. Every slide interaction (learn chapter, answer quiz, skip quiz, round created) inserts one row with a sequential ID and timestamp. The dashboard reads from this single table instead of the 4-table UNION query.

Benefits:
- **Single table to export/import** — db-compress handles one table instead of reconstructing from 4
- **Guaranteed ordering** — sequential `id` column preserves exact interaction order
- **Simpler query** — dashboard reads from one table with no UNION/JOIN

The existing 4 tables (`user_chapter_progress`, `quiz_answer_log`, `quiz_skip_log`, `lesson_revision_rounds`) remain unchanged — they serve other purposes (revision scheduling, recall tracking). The `slide_history` table is write-alongside, not a replacement.

---

## Current Implementation Analysis

### What Exists (keep as-is)

| Component | File | Status |
|-----------|------|--------|
| `user_chapter_progress` table | `scripts/sql/002_learning_progress.sql` | Keep — used by learning progress service |
| `quiz_answer_log` table | `scripts/sql/005_quiz_answer_log.sql` | Keep — used by revision service |
| `quiz_skip_log` table | `scripts/sql/004_slide_skips.sql` | Keep — used by revision service |
| `lesson_revision_rounds` table | `scripts/sql/003_revision_scheduling.sql` | Keep — used by revision service |
| `QuizAnswerLog` model | `backend/src/models/slide_management.py` | Keep |
| `QuizSkipLog` model | `backend/src/models/slide_management.py` | Keep |
| `LessonRevisionRound` model | `backend/src/models/revision_scheduling.py` | Keep |
| `UserChapterProgress` model | `backend/src/models/learning_progress.py` | Keep |

### What Changes

| Component | Current | Proposed |
|-----------|---------|----------|
| Dashboard CRUD | 4-table UNION query in `crud_dashboard.py` | Read from `slide_history` table |
| Dashboard API | Returns `List[ActivityLogEntry]` from UNION | Returns `List[ActivityLogEntry]` from `slide_history` |
| Slides API — chapter learnt | No history write | Also inserts into `slide_history` |
| Slides API — quiz respond | Writes to `quiz_answer_log` only | Also inserts into `slide_history` |
| Slides API — quiz skip | Writes to `quiz_skip_log` only | Also inserts into `slide_history` |
| Revision service — round created | Creates `lesson_revision_rounds` row only | Also inserts into `slide_history` |
| db-compress | Exports 12 tables | Exports 13 tables (+ `slide_history`) |

---

## Implementation Plan

### Key Workflow

#### To Delete
None.

#### To Update
- `backend/src/api/slides.py` — after each slide interaction, call `crud_dashboard.log_slide_event()` to insert into `slide_history`

#### To Add New
- Write-alongside pattern: every slide event writes to both the existing table AND `slide_history`

```
POST /slides/chapters/{id}/learnt
  │
  ├── mark_chapter_learnt()          ← existing (user_chapter_progress)
  ├── log_slide_event("LEARNT CHAPTER", ...)  ← NEW (slide_history)
  └── on_chapter_learnt()            ← existing (revision rounds)
        └── log_slide_event("ROUND CREATED", ...)  ← NEW

POST /slides/quizzes/{id}/respond (is_skip=false)
  │
  ├── grade answer                   ← existing
  ├── record_quiz_response()         ← existing (user_quiz_recall)
  ├── log_quiz_answer()              ← existing (quiz_answer_log)
  └── log_slide_event("ANSWER", ...) ← NEW (slide_history)

POST /slides/quizzes/{id}/respond (is_skip=true)
  │
  ├── log_quiz_skip()                ← existing (quiz_skip_log)
  └── log_slide_event("SKIP", ...)   ← NEW (slide_history)
```

### Database Schema

#### To Delete
None.

#### To Update
None.

#### To Add New

**Migration file**: `scripts/sql/008_slide_history.sql`

```sql
CREATE TABLE IF NOT EXISTS slide_history (
    id SERIAL PRIMARY KEY,
    username VARCHAR NOT NULL REFERENCES users(username),
    action VARCHAR NOT NULL,
    book_id VARCHAR,
    lesson_id INTEGER REFERENCES lessons(id),
    lesson_title VARCHAR,
    chapter_id INTEGER,
    quiz_id INTEGER,
    round_num INTEGER,
    answer_result VARCHAR,
    recall_rate FLOAT,
    event_time TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sh_user_time ON slide_history(username, event_time);
```

**Columns:**

| Column | Type | Description |
|--------|------|-------------|
| `id` | SERIAL PK | Sequential — preserves exact interaction order |
| `username` | VARCHAR FK | Which user |
| `action` | VARCHAR | `LEARNT CHAPTER`, `ANSWER`, `SKIP`, `ROUND CREATED (Rn)` |
| `book_id` | VARCHAR | Book identifier |
| `lesson_id` | INTEGER FK | Lesson reference |
| `lesson_title` | VARCHAR | Denormalized for fast reads |
| `chapter_id` | INTEGER | Chapter reference (null for ROUND CREATED) |
| `quiz_id` | INTEGER | Quiz reference (null for LEARNT CHAPTER, ROUND CREATED) |
| `round_num` | INTEGER | Revision round number (null for LEARNT CHAPTER) |
| `answer_result` | VARCHAR | `correct`, `wrong`, or null |
| `recall_rate` | FLOAT | Forgetting rate at time of answer, or null |
| `event_time` | TIMESTAMP | When the event occurred |

**ORM model**: `backend/src/models/slide_management.py`

```python
class SlideHistory(Base):
    __tablename__ = "slide_history"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, ForeignKey("users.username"), nullable=False)
    action = Column(String, nullable=False)
    book_id = Column(String)
    lesson_id = Column(Integer, ForeignKey("lessons.id"))
    lesson_title = Column(String)
    chapter_id = Column(Integer)
    quiz_id = Column(Integer)
    round_num = Column(Integer)
    answer_result = Column(String)
    recall_rate = Column(Float)
    event_time = Column(DateTime, server_default=func.now(), nullable=False)
```

### CRUD

#### To Delete
None.

#### To Update
- `backend/src/crud/crud_dashboard.py` — replace `get_activity_log()` UNION query with a simple `SELECT * FROM slide_history WHERE username = :username ORDER BY event_time ASC`

#### To Add New
- `backend/src/crud/crud_dashboard.py` — add `log_slide_event(db, username, action, book_id, lesson_id, lesson_title, chapter_id, quiz_id, round_num, answer_result, recall_rate)` that inserts one row into `slide_history`

### Services

#### To Delete
None.

#### To Update
- `backend/src/service/revision_service.py` — when `create_round()` is called, also call `log_slide_event()` with action `ROUND CREATED (Rn)`. Pass `db` and the round context through.

#### To Add New
None.

### API Endpoints

#### To Delete
None.

#### To Update
- `backend/src/api/slides.py` — `mark_chapter_learnt()`: after existing logic, call `log_slide_event("LEARNT CHAPTER", ...)`
- `backend/src/api/slides.py` — `respond_to_quiz()`: after existing logic, call `log_slide_event("ANSWER", ...)` or `log_slide_event("SKIP", ...)`

#### To Add New
None. The existing `GET /api/dashboard/activity-log` endpoint stays the same — only the underlying query changes.

### Testing

#### To Delete
None.

#### To Update
- `backend/tests/test_dashboard_api.py` — existing tests should still pass since the API response schema is unchanged. May need to adjust setup to ensure `slide_history` is populated.

#### To Add New
- Test that `log_slide_event()` creates a row in `slide_history`
- Test that `get_activity_log()` returns rows from `slide_history` in correct order
- Test round-trip: insert events → compress → restore → verify same rows

Final step: run pre-commit in a loop until clean.

### Frontend

#### To Delete
None.

#### To Update
None. `DashboardPage.jsx` already renders `ActivityLogEntry` — the API response shape is unchanged.

#### To Add New
None.

### Documentation

#### Abstract (`docs/abstract/`)

- **Update** `docs/abstract/dashboard.md`:
  - **Solution** section: add that events are stored in a dedicated `slide_history` table for cross-machine portability
  - **Scope** section: add that activity survives db-compress/db-load transfers

#### Technical (`docs/technical/`)

- **Update** `docs/technical/dashboard.md`:
  - **Architecture** section: replace UNION diagram with `SELECT * FROM slide_history`
  - **Data Model** section: add `slide_history` table schema
  - **CRUD Layer** section: update `get_activity_log()` description, add `log_slide_event()`
- **Update** `docs/technical/slide_stack.md`:
  - **Pipeline** section: add `log_slide_event()` call in both the chapter-learnt and quiz-respond pipelines

### db-compress / db-load Updates

#### To Update
- `compress.py` — add `"slide_history"` to `TABLES` list
- `restore.py` — add `"slide_history"` to `TABLES` list, add `("slide_history", "id", "slide_history_id_seq")` to `seq_map`

### Chrome Claude Extension Execution

After implementation, execute tests in `docs/chrome_test/activity_log_sync.md`.

---

## Dependencies

- `users` table (FK on username)
- `lessons` table (FK on lesson_id)
- Backend server running for API tests
- db-compress/db-load scripts for portability tests

## Open Questions

None — the approach is straightforward: add a single event log table alongside existing tables.
