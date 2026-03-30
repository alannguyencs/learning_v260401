# Learning Progress — Chapter Learnt Tracking & Lesson Count

**Feature**: Track which chapters a user has marked as learnt and maintain a global lessons-learnt counter
**Plan Created:** 2026-03-30
**Status:** Plan
**Reference**:
- [Source spec](../learning_strategy.md#72-constraints)
- [Technical — Learning Progress](../technical/learning_progress.md)
- [Depends on: Plan 1](./260330_content_schema.md)

---

## Problem Statement

1. The app has no record of which chapters a user has studied. There is no way to know whether a user has seen a chapter or not.
2. The revision interval formula `2^n lessons fully learnt` requires a global counter of how many lessons (all chapters complete) the user has finished. This counter doesn't exist.
3. "Lesson fully learnt" — all chapters in the lesson marked as learnt — must be computed and tracked so downstream systems (revision scheduling) can trigger correctly.

---

## Proposed Solution

Add two tables:
- `user_chapter_progress`: one row per (user, chapter) when the user marks a chapter as learnt.
- `user_lesson_count`: one row per user; integer counter incremented each time a lesson becomes fully learnt.

A `LearningProgressService` encapsulates the mark-learnt logic: record the chapter, check if the lesson is now complete, and if so increment the lesson count.

---

## Current Implementation Analysis

### What Exists (keep as-is)

| Component | File | Status |
|-----------|------|--------|
| `chapters` table | Plan 1 | Keep — foreign key target |
| `lessons` table | Plan 1 | Keep — used to count total chapters |
| Users model | `backend/src/models/user.py` | Keep — auth |

### What Changes

| Component | Current | Proposed |
|-----------|---------|----------|
| `backend/src/models/__init__.py` | `Book, Lesson, Chapter, ChapterQuiz` | Also import `UserChapterProgress`, `UserLessonCount` |

---

## Implementation Plan

### Key Workflow

```
POST /api/slides/chapters/{chapter_id}/learnt  (Plan 4's endpoint calls this service)
  │
  ▼
LearningProgressService.mark_chapter_learnt(db, username, chapter_id)
  │
  ├── INSERT INTO user_chapter_progress (ignore if already exists)
  │
  ├── COUNT chapters in lesson (from chapters table)
  ├── COUNT learnt chapters for user in lesson (from user_chapter_progress)
  │
  ├── lesson_fully_learnt = learnt_count == total_count?
  │
  └── If fully learnt:
        UPDATE user_lesson_count SET total_lessons_learnt += 1
        (INSERT if no row yet)
  │
  ▼
Return { lesson_id, lesson_fully_learnt: bool, lesson_count: int }
```

### Database Schema

#### To Delete
None.

#### To Update
None.

#### To Add New

Migration file: `scripts/sql/002_learning_progress.sql`

```sql
CREATE TABLE IF NOT EXISTS user_chapter_progress (
    id SERIAL PRIMARY KEY,
    username VARCHAR NOT NULL REFERENCES users(username),
    chapter_id INTEGER NOT NULL REFERENCES chapters(id),
    learnt_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(username, chapter_id)
);
CREATE INDEX IF NOT EXISTS idx_ucp_user ON user_chapter_progress(username);
CREATE INDEX IF NOT EXISTS idx_ucp_user_chapter ON user_chapter_progress(username, chapter_id);

CREATE TABLE IF NOT EXISTS user_lesson_count (
    username VARCHAR PRIMARY KEY REFERENCES users(username),
    total_lessons_learnt INTEGER NOT NULL DEFAULT 0
);
```

**Column notes:**
- `user_chapter_progress.learnt_at`: timestamp when first marked as learnt
- `user_lesson_count.total_lessons_learnt`: global counter across all books; incremented once per lesson, never decremented

### CRUD

#### To Delete
None.

#### To Update
None.

#### To Add New

File: `backend/src/crud/crud_learning_progress.py`

```python
def mark_chapter_learnt(db, username: str, chapter_id: int) -> None
    """INSERT INTO user_chapter_progress (ignore duplicate via ON CONFLICT DO NOTHING)."""

def is_chapter_learnt(db, username: str, chapter_id: int) -> bool
    """SELECT 1 FROM user_chapter_progress WHERE username=? AND chapter_id=?."""

def count_learnt_chapters_in_lesson(db, username: str, lesson_id: int) -> int
    """COUNT user_chapter_progress rows for all chapters belonging to lesson_id."""

def get_lesson_count(db, username: str) -> int
    """SELECT total_lessons_learnt FROM user_lesson_count WHERE username=?. Return 0 if no row."""

def increment_lesson_count(db, username: str) -> int
    """INSERT ... ON CONFLICT DO UPDATE SET total_lessons_learnt += 1. Return new value."""

def get_learnt_chapter_ids_for_user(db, username: str) -> set[int]
    """SELECT chapter_id FROM user_chapter_progress WHERE username=?. Used by slide selector."""
```

### Services

#### To Delete
None.

#### To Update
None.

#### To Add New

File: `backend/src/service/learning_progress_service.py`

```python
from dataclasses import dataclass

@dataclass
class ChapterLearntResult:
    lesson_id: int
    lesson_fully_learnt: bool
    lesson_count: int
    chapter_quiz_ids: list[int]  # quiz IDs on this chapter (for revision scheduling trigger)

class LearningProgressService:
    @staticmethod
    def mark_chapter_learnt(db, username: str, chapter_id: int) -> ChapterLearntResult:
        """
        1. Mark chapter as learnt (idempotent).
        2. Retrieve chapter's lesson_id and total chapter count in lesson.
        3. Count learnt chapters for this user in the lesson.
        4. If all chapters learnt: increment user_lesson_count.
        5. Return ChapterLearntResult with lesson_id, lesson_fully_learnt, lesson_count,
           and chapter_quiz_ids (so revision scheduling can ingest new quizzes).
        """
```

### API Endpoints

#### To Delete
None.

#### To Update
None.

#### To Add New
None — this service has no standalone API endpoint. It is called by Plan 4's
`POST /api/slides/chapters/{chapter_id}/learnt` endpoint.

### Testing

#### To Delete
None.

#### To Update
None.

#### To Add New

File: `backend/tests/test_learning_progress.py`

- `test_mark_chapter_learnt_first_time` — marking a chapter creates a progress row
- `test_mark_chapter_learnt_idempotent` — marking the same chapter twice doesn't create a duplicate
- `test_lesson_fully_learnt_detected` — after all chapters of a lesson are marked, `lesson_fully_learnt=True`
- `test_lesson_count_increments_on_fully_learnt` — counter goes from 0 to 1 on first fully-learnt lesson
- `test_lesson_count_not_incremented_partial` — partial completion doesn't increment counter
- `test_multiple_lessons_count` — completing 2 lessons yields lesson_count=2

Pre-commit loop:
1. Run `pre-commit run --all-files`
2. Fix any lint errors, unused imports
3. Repeat until clean

### Frontend

#### To Delete
None.

#### To Update
None.

#### To Add New
None — no frontend in this plan.

### Documentation

#### Abstract (`docs/abstract/`)
No standalone abstract doc for this plan — learning progress is an internal mechanism.
The user-facing description is covered in `docs/abstract/slide_stack.md` (Plan 5).

#### Technical (`docs/technical/`)

- **Create** `docs/technical/learning_progress.md`:
  - Architecture: LearningProgressService + two DB tables
  - Data Model: `UserChapterProgress`, `UserLessonCount`
  - Pipeline: mark-chapter-learnt flow
  - Service Layer: `LearningProgressService.mark_chapter_learnt`
  - CRUD Layer: all functions listed above
  - Component Checklist

### Chrome Claude Extension Execution

No browser tests for this backend-only plan.

---

## Dependencies

- Plan 1 (`260330_content_schema.md`) — `chapters`, `lessons` tables must exist.
- `users` table — foreign key in `user_chapter_progress`.

## Open Questions

None.
