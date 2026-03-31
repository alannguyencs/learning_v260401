# Revision Scheduling — Technical Design

[< Prev: Learning Progress](./learning_progress.md) | [Parent](./index.md)

## Architecture

```
ChapterLearntResult (from LearningProgressService)
        |
        v
RevisionService.on_chapter_learnt(db, username, lesson_id, chapter_quiz_ids, lesson_count)
        |
        v
crud_revision  →  lesson_revision_rounds table
               →  user_quiz_recall table

POST /api/slides/chapters/{id}/respond  (Plan 4 endpoint)
        |
        v
RevisionService.record_quiz_response(db, username, quiz_id, lesson_id, round_num, is_correct, lesson_count)
```

No standalone API in this plan — the service is called by Plan 4's slide endpoints.

## Data Model

**`lesson_revision_rounds`**

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | Integer | PK |
| `username` | String | FK → users.username, NOT NULL |
| `lesson_id` | Integer | FK → lessons.id, NOT NULL |
| `round_num` | Integer | NOT NULL, DEFAULT 0 |
| `status` | String | NOT NULL, DEFAULT 'open' |
| `due_at_lesson_count` | Integer | NOT NULL, DEFAULT 0 |
| `completed_at_lesson_count` | Integer | nullable |
| `quizzes_in_round` | Integer | NOT NULL, DEFAULT 0 |
| `quizzes_answered` | Integer | NOT NULL, DEFAULT 0 |
| `created_at` | Timestamp | DEFAULT NOW() |
| — | — | UNIQUE(username, lesson_id, round_num) |

**`user_quiz_recall`**

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | Integer | PK |
| `username` | String | FK → users.username, NOT NULL |
| `quiz_id` | Integer | FK → chapter_quizzes.id, NOT NULL |
| `forgetting_rate` | Float | NOT NULL, DEFAULT 1.0 |
| `last_reviewed_lesson_count` | Integer | nullable |
| `review_count` | Integer | NOT NULL, DEFAULT 0 |
| — | — | UNIQUE(username, quiz_id) |

## Algorithms

### on_chapter_learnt Distribution

```
chapter_quiz_ids → delta = len(chapter_quiz_ids)

Case A: No R0 exists
  → CREATE R0 (due_at = lesson_count, quizzes_in_round = delta)

Case B: R0 is open
  → UPDATE R0: quizzes_in_round += delta

Case C: R0 is done
  → Find/create next open round Rk
  → UPDATE Rk: quizzes_in_round += delta
```

### Round Completion Threshold

Both conditions must be true simultaneously:

1. `quizzes_answered / total_lesson_quizzes > 0.50`
2. All chapters in the lesson are marked as learnt by the user

`total_lesson_quizzes` is the count of all quizzes across every chapter in the lesson (not just the chapters learnt so far). This prevents R0 from completing while the user is still progressing through chapters.

### Next Round Interval

`due_at_lesson_count = lesson_count_when_completed + 2^(round_num + 1)`

| Round completed | Next round | Interval |
|----------------|------------|----------|
| R0 | R1 | +2 lessons |
| R1 | R2 | +4 lessons |
| R2 | R3 | +8 lessons |

### MEMORIZE Recall Update

- Correct: `forgetting_rate *= 0.7`
- Incorrect: `forgetting_rate = min(forgetting_rate * 1.2, 1.5)`
- Skip: no update

### Recall Score Formula

`m(t) = exp(-forgetting_rate * lessons_elapsed / 10)`

where `lessons_elapsed = current_lesson_count - last_reviewed_lesson_count`

## Pipeline

### on_chapter_learnt

```
RevisionService.on_chapter_learnt(db, username, lesson_id, chapter_quiz_ids, lesson_count)
  │
  ├── If no quizzes → return (no-op)
  │
  ├── crud_revision.get_open_round(db, username, lesson_id, 0) → r0
  │
  ├── If r0 open → increment_round_quiz_count(r0.id, delta)
  │
  ├── Else: get_latest_round(db, username, lesson_id) → latest
  │
  ├── If no latest → create_round(R0, due_at=lesson_count, quizzes=delta)
  │
  └── If latest done → find/create next open round Rk, increment/create with delta
```

### record_quiz_response

```
RevisionService.record_quiz_response(db, username, quiz_id, lesson_id, round_num, is_correct, lesson_count)
  │
  ├── get_open_round(db, username, lesson_id, round_num) → round_row
  │
  ├── If is_correct is not None (not a skip):
  │     ├── get existing forgetting_rate (default 1.0 if first time)
  │     ├── Update rate: correct → *0.7, incorrect → min(*1.2, 1.5)
  │     ├── upsert_quiz_recall(db, username, quiz_id, new_rate, lesson_count)
  │     └── increment_round_answered(db, round_row.id) → updated round_row
  │
  ├── If quizzes_answered / total_lesson_quizzes > 0.50
  │   AND all_lesson_chapters_learnt(db, username, lesson_id):
  │     ├── complete_round(db, round_row.id, lesson_count)
  │     ├── Create next round (round_num+1, due_at = lesson_count + 2^(round_num+1))
  │     └── Return QuizResponseResult(round_done=True, next_round_num, next_round_due_at)
  │
  └── Else: Return QuizResponseResult(round_done=False, ...)
```

## Service Layer

**`RevisionService`** (`backend/src/service/revision_service.py`):

| Method | Description |
|--------|-------------|
| `on_chapter_learnt(db, username, lesson_id, chapter_quiz_ids, lesson_count)` | Distribute quizzes into correct round |
| `record_quiz_response(db, username, quiz_id, lesson_id, round_num, is_correct, lesson_count)` | Update recall and advance round |
| `compute_recall(forgetting_rate, lessons_elapsed)` | Returns m(t) recall score |

**`QuizResponseResult`** dataclass:

| Field | Type | Description |
|-------|------|-------------|
| `round_done` | bool | True if round completed |
| `next_round_num` | int \| None | Round number of newly created next round |
| `next_round_due_at` | int \| None | lesson_count when next round becomes due |

## CRUD Layer

**`crud_revision.py`:**

| Function | Description |
|----------|-------------|
| `get_open_round(username, lesson_id, round_num)` | SELECT open round |
| `get_latest_round(username, lesson_id)` | SELECT highest round_num |
| `create_round(username, lesson_id, round_num, due_at, quizzes)` | INSERT new round |
| `increment_round_quiz_count(round_id, delta)` | UPDATE quizzes_in_round += delta |
| `increment_round_answered(round_id)` | UPDATE quizzes_answered += 1 |
| `complete_round(round_id, completed_at)` | UPDATE status='done' |
| `get_due_rounds(username, lesson_count)` | SELECT open rounds where due_at <= lesson_count |
| `get_answered_quiz_ids_in_round(username, lesson_id, round_num)` | SET of reviewed quiz_ids |
| `upsert_quiz_recall(username, quiz_id, forgetting_rate, lesson_count)` | INSERT or UPDATE recall |
| `get_quiz_recall(username, quiz_id)` | SELECT recall row |
| `get_quiz_recalls_for_lesson(username, lesson_id)` | SELECT all recall rows for a lesson |

**`crud_learning_progress.py`** (used by `RevisionService`):

| Function | Description |
|----------|-------------|
| `all_lesson_chapters_learnt(username, lesson_id)` | True if every chapter in the lesson has a `user_chapter_progress` row for the user |

## Constraints & Edge Cases

- R0 is due immediately (`due_at_lesson_count = lesson_count` at time of first chapter learnt).
- Skips (`is_correct=None`) do not increment `quizzes_answered` and do not update recall.
- Quizzes added after R0 is done go into the next open round (R1 or higher).
- `quizzes_in_round` for next round after completion is set to total quizzes in the lesson.
- If `total_lesson_quizzes = 0`, the completion threshold is never met (no division by zero).
- If not all chapters are learnt, R0 stays open even when >50% of answered quizzes is reached; completion fires on the next answer once the second condition is satisfied.

## Component Checklist

- [x] Migration — `scripts/sql/003_revision_scheduling.sql`
- [x] Models — `backend/src/models/revision_scheduling.py` (`LessonRevisionRound`, `UserQuizRecall`)
- [x] CRUD — `backend/src/crud/crud_revision.py`
- [x] Service — `backend/src/service/revision_service.py`
- [x] Tests — `backend/tests/test_revision_service.py`

---

[< Prev: Learning Progress](./learning_progress.md) | [Parent](./index.md)
