# Revision Scheduling — R0/Rn Rounds & Quiz Recall Tracking

**Feature**: Create and advance spaced-repetition revision rounds per lesson; track per-quiz recall rates
**Plan Created:** 2026-03-30
**Status:** Plan
**Reference**:
- [Source spec](../learning_strategy.md#73-revision-schedule)
- [Technical — Revision Scheduling](../technical/revision_scheduling.md)
- [Depends on: Plan 1](./260330_content_schema.md)
- [Depends on: Plan 2](./260330_learning_progress.md)

---

## Problem Statement

1. After a user learns chapters, there is no system to schedule when to review them again.
2. The spec defines a revision schedule using exponential intervals (`2^n` lessons fully learnt). This requires tracking which round each lesson is on, when each round becomes due, and when it completes.
3. Quiz selection within a revision round must prioritise the weakest quizzes first (lowest recall rate). There is no mechanism to track per-user, per-quiz recall.

---

## Proposed Solution

Add two tables:
- `lesson_revision_rounds`: one row per (user, lesson, round number). Tracks status (`open`/`done`), when due, quiz counts.
- `user_quiz_recall`: one row per (user, quiz). Tracks MEMORIZE-style forgetting rate for ordering quizzes by weakest-first within a round.

A `RevisionSchedulingService` handles:
1. **on_chapter_learnt** — when a chapter is learnt, distribute its quizzes into the correct round pool (R0 if open, else next open round).
2. **record_quiz_response** — when a quiz is answered, update recall, increment answered count, and check if round completes; if so, create the next round.

**Interval formula:** `due_at_lesson_count = lesson_count_when_round_completed + 2^(round_num + 1)`

**Round completion threshold:** `quizzes_answered / quizzes_in_round > 0.50`

**MEMORIZE recall update:**
- Correct: `forgetting_rate *= 0.7`
- Incorrect: `forgetting_rate = min(forgetting_rate * 1.2, 1.5)`
- Recall score: `m(t) = exp(-forgetting_rate * lessons_elapsed / 10)` where `lessons_elapsed = current_lesson_count - last_reviewed_lesson_count`

---

## Current Implementation Analysis

### What Exists (keep as-is)

| Component | File | Status |
|-----------|------|--------|
| `chapter_quizzes` table | Plan 1 | Keep — quizzes referenced |
| `lessons` table | Plan 1 | Keep — lesson_id FK |
| `user_lesson_count` | Plan 2 | Keep — lesson_count used for intervals |
| `LearningProgressService` | Plan 2 | Keep — `on_chapter_learnt` is triggered by its result |

### What Changes

| Component | Current | Proposed |
|-----------|---------|----------|
| `backend/src/models/__init__.py` | Plans 1+2 imports | Also import `LessonRevisionRound`, `UserQuizRecall` |

---

## Implementation Plan

### Key Workflow

#### On chapter learnt (called from Plan 4 after LearningProgressService)

```
ChapterLearntResult { lesson_id, lesson_fully_learnt, lesson_count, chapter_quiz_ids }
  │
  ▼
RevisionSchedulingService.on_chapter_learnt(db, username, result)
  │
  ├── Find open R0 for (username, lesson_id)
  │
  ├── Case A: No R0 exists yet
  │     └── CREATE R0: due_at_lesson_count=result.lesson_count, quizzes_in_round=len(chapter_quiz_ids)
  │
  ├── Case B: R0 is open
  │     └── UPDATE R0: quizzes_in_round += len(chapter_quiz_ids)
  │
  └── Case C: R0 is done
        └── Find/create R1, UPDATE: quizzes_in_round += len(chapter_quiz_ids)
```

#### On quiz response (called from Plan 4's respond endpoint)

```
quiz_id, lesson_id, round_num, is_correct (bool or None=skip), lesson_count
  │
  ▼
RevisionSchedulingService.record_quiz_response(...)
  │
  ├── Update user_quiz_recall (MEMORIZE)
  │     ├── Correct:   forgetting_rate *= 0.7
  │     └── Incorrect: forgetting_rate = min(n * 1.2, 1.5)
  │     (Skip: no recall update)
  │
  ├── If not a skip: increment round.quizzes_answered
  │
  ├── Check completion: quizzes_answered / quizzes_in_round > 0.50?
  │     └── If YES:
  │           UPDATE round: status='done', completed_at_lesson_count=lesson_count
  │           CREATE next round Rn+1:
  │             round_num = round_num + 1
  │             due_at_lesson_count = lesson_count + 2^(round_num + 1)
  │             quizzes_in_round = total quizzes in lesson (all chapters)
  │             status = 'open'
  │
  └── Return { round_done: bool, next_round_due_at: int | None }
```

### Database Schema

#### To Delete
None.

#### To Update
None.

#### To Add New

Migration file: `scripts/sql/003_revision_scheduling.sql`

```sql
CREATE TABLE IF NOT EXISTS lesson_revision_rounds (
    id SERIAL PRIMARY KEY,
    username VARCHAR NOT NULL REFERENCES users(username),
    lesson_id INTEGER NOT NULL REFERENCES lessons(id),
    round_num INTEGER NOT NULL DEFAULT 0,
    status VARCHAR NOT NULL DEFAULT 'open',
    due_at_lesson_count INTEGER NOT NULL DEFAULT 0,
    completed_at_lesson_count INTEGER,
    quizzes_in_round INTEGER NOT NULL DEFAULT 0,
    quizzes_answered INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(username, lesson_id, round_num)
);
CREATE INDEX IF NOT EXISTS idx_lrr_user_status ON lesson_revision_rounds(username, status);
CREATE INDEX IF NOT EXISTS idx_lrr_user_lesson ON lesson_revision_rounds(username, lesson_id);

CREATE TABLE IF NOT EXISTS user_quiz_recall (
    id SERIAL PRIMARY KEY,
    username VARCHAR NOT NULL REFERENCES users(username),
    quiz_id INTEGER NOT NULL REFERENCES chapter_quizzes(id),
    forgetting_rate FLOAT NOT NULL DEFAULT 1.0,
    last_reviewed_lesson_count INTEGER,
    review_count INTEGER NOT NULL DEFAULT 0,
    UNIQUE(username, quiz_id)
);
CREATE INDEX IF NOT EXISTS idx_uqr_user ON user_quiz_recall(username);
```

**Column notes:**
- `lesson_revision_rounds.round_num`: 0 = R0, 1 = R1, etc.
- `lesson_revision_rounds.status`: `'open'` = active; `'done'` = completed
- `lesson_revision_rounds.due_at_lesson_count`: round becomes eligible once user's `total_lessons_learnt >= due_at_lesson_count`
- `lesson_revision_rounds.quizzes_in_round`: how many distinct quizzes are eligible for this round
- `lesson_revision_rounds.quizzes_answered`: how many have been answered (skips not counted)
- `user_quiz_recall.forgetting_rate`: MEMORIZE `n` value; starts at 1.0
- `user_quiz_recall.last_reviewed_lesson_count`: lesson_count at time of last response (for m(t) calc)

### CRUD

#### To Delete
None.

#### To Update
None.

#### To Add New

File: `backend/src/crud/crud_revision.py`

```python
def get_open_round(db, username: str, lesson_id: int, round_num: int) -> LessonRevisionRound | None
    """SELECT open round for (username, lesson_id, round_num)."""

def get_latest_round(db, username: str, lesson_id: int) -> LessonRevisionRound | None
    """SELECT round with highest round_num for (username, lesson_id)."""

def create_round(db, username: str, lesson_id: int, round_num: int,
                 due_at_lesson_count: int, quizzes_in_round: int) -> LessonRevisionRound

def increment_round_quiz_count(db, round_id: int, delta: int) -> None
    """UPDATE quizzes_in_round += delta."""

def increment_round_answered(db, round_id: int) -> LessonRevisionRound
    """UPDATE quizzes_answered += 1. Return updated row."""

def complete_round(db, round_id: int, completed_at_lesson_count: int) -> None
    """UPDATE status='done', completed_at_lesson_count=?."""

def get_due_rounds(db, username: str, lesson_count: int) -> list[LessonRevisionRound]
    """SELECT all open rounds where due_at_lesson_count <= lesson_count."""

def get_answered_quiz_ids_in_round(db, username: str, lesson_id: int, round_num: int) -> set[int]
    """SELECT quiz_ids already answered or skipped in a given round (from user_quiz_recall + round)."""

def upsert_quiz_recall(db, username: str, quiz_id: int,
                       forgetting_rate: float, lesson_count: int) -> UserQuizRecall
    """INSERT ... ON CONFLICT DO UPDATE forgetting_rate, last_reviewed_lesson_count, review_count."""

def get_quiz_recall(db, username: str, quiz_id: int) -> UserQuizRecall | None

def get_quiz_recalls_for_lesson(db, username: str, lesson_id: int) -> list[UserQuizRecall]
    """Used for ordering quizzes weakest-first within a round."""
```

### Services

#### To Delete
None.

#### To Update
None.

#### To Add New

File: `backend/src/service/revision_service.py`

```python
from dataclasses import dataclass
import math

MEMORIZE_DIVISOR = 10
MAX_FORGETTING_RATE = 1.5

@dataclass
class QuizResponseResult:
    round_done: bool
    next_round_num: int | None
    next_round_due_at: int | None

class RevisionService:
    @staticmethod
    def on_chapter_learnt(db, username: str, lesson_id: int,
                          chapter_quiz_ids: list[int], lesson_count: int) -> None:
        """
        Distribute new chapter quizzes into the correct revision round.
        - If no R0 exists: create R0 (due immediately at lesson_count).
        - If R0 is open: increment quizzes_in_round.
        - If R0 is done: find/create R1 and increment its quizzes_in_round.
        """

    @staticmethod
    def record_quiz_response(db, username: str, quiz_id: int, lesson_id: int,
                             round_num: int, is_correct: bool | None,
                             lesson_count: int) -> QuizResponseResult:
        """
        is_correct=None means skip (no recall update, no count increment).
        1. Update user_quiz_recall (MEMORIZE).
        2. If not skip: increment quizzes_answered on round.
        3. Check completion (>50%). If done: create next round with interval 2^(round_num+1).
        """

    @staticmethod
    def compute_recall(forgetting_rate: float, lessons_elapsed: int) -> float:
        """m(t) = exp(-forgetting_rate * lessons_elapsed / MEMORIZE_DIVISOR)."""
        return math.exp(-forgetting_rate * max(lessons_elapsed, 0) / MEMORIZE_DIVISOR)
```

### API Endpoints

#### To Delete
None.

#### To Update
None.

#### To Add New
None — this service has no standalone API endpoint. It is called from Plan 4's slide endpoints.

### Testing

#### To Delete
None.

#### To Update
None.

#### To Add New

File: `backend/tests/test_revision_service.py`

- `test_r0_created_on_first_chapter_learnt` — R0 row created with due_at=lesson_count
- `test_r0_quiz_count_grows_as_chapters_added` — second chapter learnt increments quizzes_in_round
- `test_quiz_answer_increments_answered_count` — record_quiz_response increments counter
- `test_skip_does_not_increment_answered` — skip leaves quizzes_answered unchanged
- `test_round_completes_at_50_percent` — answering >50% flips status to done
- `test_next_round_created_after_completion` — R1 created with correct due_at (lesson_count + 2^1 = +2)
- `test_memorize_correct_reduces_forgetting_rate` — rate * 0.7 after correct
- `test_memorize_incorrect_increases_forgetting_rate` — rate * 1.2 after incorrect
- `test_memorize_forgetting_rate_capped` — rate never exceeds 1.5
- `test_recall_score_formula` — compute_recall returns exp(-n * elapsed / 10)
- `test_quizzes_added_to_r1_when_r0_done` — late chapters go into R1 quizzes_in_round

Pre-commit loop:
1. Run `pre-commit run --all-files`
2. Fix lint errors
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
No standalone abstract doc — revision scheduling is an internal mechanism.
The user-facing behaviour is documented in `docs/abstract/slide_stack.md` (Plan 5).

#### Technical (`docs/technical/`)

- **Create** `docs/technical/revision_scheduling.md`:
  - Architecture: RevisionService + two DB tables
  - Data Model: `LessonRevisionRound`, `UserQuizRecall`
  - Algorithms: on_chapter_learnt distribution, round completion threshold, MEMORIZE update, recall formula
  - Pipeline: on_chapter_learnt flow, record_quiz_response flow
  - Service Layer: all methods with signatures
  - CRUD Layer: all functions listed above
  - Constraints & Edge Cases: R0 due immediately; skips don't count; quizzes added mid-round go to next round if R0 done
  - Component Checklist

### Chrome Claude Extension Execution

No browser tests for this backend-only plan.

---

## Dependencies

- Plan 1 (`260330_content_schema.md`) — `lessons`, `chapter_quizzes` tables must exist.
- Plan 2 (`260330_learning_progress.md`) — `user_lesson_count` for interval calculations; `LearningProgressService` triggers this service.

## Open Questions

None.
