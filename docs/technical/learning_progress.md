# Learning Progress — Technical Design

[< Prev: Content Upload](./content_upload.md) | [Parent](./index.md)

## Architecture

```
POST /api/slides/chapters/{id}/learnt  (Plan 4 endpoint)
        |
        v
LearningProgressService.mark_chapter_learnt(db, username, chapter_id)
        |
        v
crud_learning_progress  →  user_chapter_progress table
                        →  user_lesson_count table
```

No standalone API in this plan — the service is called by Plan 4's slide endpoint.

## Data Model

**`user_chapter_progress`**

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | Integer | PK |
| `username` | String | FK → users.username, NOT NULL |
| `chapter_id` | Integer | FK → chapters.id, NOT NULL |
| `learnt_at` | Timestamp | NOT NULL, DEFAULT NOW() |
| — | — | UNIQUE(username, chapter_id) |

**`user_lesson_count`**

| Column | Type | Constraints |
|--------|------|-------------|
| `username` | String | PK, FK → users.username |
| `total_lessons_learnt` | Integer | NOT NULL, DEFAULT 0 |

`total_lessons_learnt` is a global counter across all books. It is incremented once per fully-learnt lesson and never decremented.

## Pipeline

### Mark Chapter Learnt

```
LearningProgressService.mark_chapter_learnt(db, username, chapter_id)
  │
  ├── crud_learning_progress.mark_chapter_learnt(db, username, chapter_id)
  │         INSERT INTO user_chapter_progress (idempotent — skip if duplicate)
  │
  ├── get_chapter(db, chapter_id) → lesson_id
  ├── get_lesson_chapter_count(db, lesson_id) → total_chapters
  ├── count_learnt_chapters_in_lesson(db, username, lesson_id) → learnt_chapters
  │
  ├── lesson_fully_learnt = (learnt_chapters == total_chapters)
  │
  ├── If lesson_fully_learnt:
  │       increment_lesson_count(db, username) → lesson_count
  │   Else:
  │       get_lesson_count(db, username) → lesson_count
  │
  ├── list_quizzes_for_chapter(db, chapter_id) → chapter_quiz_ids
  │
  └── Return ChapterLearntResult(
            lesson_id, lesson_fully_learnt, lesson_count, chapter_quiz_ids
        )
```

## Service Layer

**`LearningProgressService`** (`backend/src/service/learning_progress_service.py`):

| Method | Description |
|--------|-------------|
| `mark_chapter_learnt(db, username, chapter_id)` | Full mark-learnt flow; returns `ChapterLearntResult` |

**`ChapterLearntResult`** dataclass:

| Field | Type | Description |
|-------|------|-------------|
| `lesson_id` | int | The lesson this chapter belongs to |
| `lesson_fully_learnt` | bool | True if all chapters in the lesson are now learnt |
| `lesson_count` | int | User's total fully-learnt lesson count after this operation |
| `chapter_quiz_ids` | list[int] | Quiz IDs on this chapter (passed to RevisionService) |

## CRUD Layer

**`crud_learning_progress.py`:**

| Function | Description |
|----------|-------------|
| `mark_chapter_learnt(username, chapter_id)` | INSERT into user_chapter_progress; skip if duplicate |
| `is_chapter_learnt(username, chapter_id)` | True if progress row exists |
| `count_learnt_chapters_in_lesson(username, lesson_id)` | COUNT via JOIN with chapters |
| `get_lesson_count(username)` | SELECT total_lessons_learnt; returns 0 if no row |
| `increment_lesson_count(username)` | UPSERT with += 1; returns new value |
| `get_learnt_chapter_ids_for_user(username)` | All chapter_ids the user has learnt (used by SlideSelector) |

## Component Checklist

- [ ] Migration — `scripts/sql/002_learning_progress.sql`
- [ ] Models — `backend/src/models/learning_progress.py` (`UserChapterProgress`, `UserLessonCount`)
- [ ] CRUD — `backend/src/crud/crud_learning_progress.py`
- [ ] Service — `backend/src/service/learning_progress_service.py`
- [ ] Tests — `backend/tests/test_learning_progress.py`

---

[< Prev: Content Upload](./content_upload.md) | [Parent](./index.md)
