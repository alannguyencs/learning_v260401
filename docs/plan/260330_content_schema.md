# Content Schema — Books, Lessons, Chapters, Quizzes

**Feature**: DB schema and upload API for books, lessons, chapters, and chapter quizzes
**Plan Created:** 2026-03-30
**Status:** Plan
**Reference**:
- [Abstract — Content Upload](../abstract/content_upload.md)
- [Technical — Content Upload](../technical/content_upload.md)
- [Source spec](../learning_strategy.md#7-dynamic-lesson-quiz-stacking-proposal)

---

## Problem Statement

1. The app has no content data model. There is no way to store or retrieve books, lessons, chapters, or quizzes.
2. A local agent (e.g., the `lesson-upload` skill) needs to upload structured content via API using a Bearer token — without direct database access.
3. The frontend needs to list available books and show a book's structure (lessons → chapters) to support book selection.

---

## Proposed Solution

Create four tables that form the content hierarchy: `books → lessons → chapters → chapter_quizzes`. Provide authenticated upload endpoints (Bearer token) for the local agent and read endpoints (session cookie) for the frontend. All quiz types (free recall, teach-back, cloze, multiple choice) are stored in one unified table using a `quiz_type` column.

**Content hierarchy:**
```
Book  →  Lesson (ordered by lesson_index)
              └─  Chapter (ordered by chapter_index)
                      └─  ChapterQuiz (one or more per chapter)
```

---

## Current Implementation Analysis

### What Exists (keep as-is)

| Component | File | Status |
|-----------|------|--------|
| Users model | `backend/src/models/user.py` | Keep — auth |
| Auth middleware | `backend/src/auth.py` | Keep — provides `get_current_user` |
| API router | `backend/src/api/api_router.py` | Keep — will add new router |
| Models init | `backend/src/models/__init__.py` | Keep — will add new model imports |

### What Changes

| Component | Current | Proposed |
|-----------|---------|----------|
| `backend/src/models/__init__.py` | Imports `Users` only | Also import `Book`, `Lesson`, `Chapter`, `ChapterQuiz` |
| `backend/src/api/api_router.py` | Auth/login/root only | Also register `content` router |
| `backend/src/configs.py` | No `webapp_access_token` | Add `webapp_access_token: str` field for Bearer auth |

---

## Implementation Plan

### Key Workflow

```
Local agent (lesson-upload skill)
  │
  ▼
POST /api/content/books  (Bearer token)
  │
  ▼
POST /api/content/lessons  (Bearer token)
  │
  ▼
POST /api/content/chapters  (Bearer token)
  │
  ▼
POST /api/content/quizzes  (Bearer token, batch)
  │
  ▼
Content stored in DB: books → lessons → chapters → chapter_quizzes

Frontend (book selection)
  │
  ▼
GET /api/content/books  (session cookie)
  │
  ▼
GET /api/content/books/{book_id}/structure  (session cookie)
```

### Database Schema

#### To Delete
None.

#### To Update
None.

#### To Add New

Migration file: `scripts/sql/001_content_schema.sql`

```sql
CREATE TABLE IF NOT EXISTS books (
    id SERIAL PRIMARY KEY,
    book_id VARCHAR UNIQUE NOT NULL,
    title VARCHAR NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS lessons (
    id SERIAL PRIMARY KEY,
    book_id VARCHAR NOT NULL REFERENCES books(book_id),
    lesson_index INTEGER NOT NULL,
    title VARCHAR NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(book_id, lesson_index)
);
CREATE INDEX IF NOT EXISTS idx_lessons_book ON lessons(book_id);

CREATE TABLE IF NOT EXISTS chapters (
    id SERIAL PRIMARY KEY,
    lesson_id INTEGER NOT NULL REFERENCES lessons(id),
    chapter_index INTEGER NOT NULL,
    title VARCHAR NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(lesson_id, chapter_index)
);
CREATE INDEX IF NOT EXISTS idx_chapters_lesson ON chapters(lesson_id);

CREATE TABLE IF NOT EXISTS chapter_quizzes (
    id SERIAL PRIMARY KEY,
    chapter_id INTEGER NOT NULL REFERENCES chapters(id),
    quiz_type VARCHAR NOT NULL,
    question TEXT NOT NULL,
    expected_answer TEXT,
    option_a TEXT,
    option_b TEXT,
    option_c TEXT,
    option_d TEXT,
    correct_options JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_cq_chapter ON chapter_quizzes(chapter_id);
```

**Column notes:**
- `quiz_type`: `'free_recall'`, `'teach_back'`, `'cloze'`, or `'multiple_choice'`
- `expected_answer`: populated for `free_recall`, `teach_back`, `cloze`; NULL for `multiple_choice`
- `option_a/b/c/d`, `correct_options`: populated for `multiple_choice` only; NULL for others
- `correct_options`: JSONB list, e.g. `["A"]` or `["A", "C"]`

### CRUD

#### To Delete
None.

#### To Update
None.

#### To Add New

File: `backend/src/crud/crud_content.py`

```python
def get_book(db, book_id: str) -> Book | None
def create_book(db, book_id: str, title: str) -> Book
def list_books(db) -> list[Book]

def get_lesson(db, lesson_id: int) -> Lesson | None
def create_lesson(db, book_id: str, lesson_index: int, title: str) -> Lesson
def list_lessons_in_book(db, book_id: str) -> list[Lesson]
def get_lesson_chapter_count(db, lesson_id: int) -> int

def get_chapter(db, chapter_id: int) -> Chapter | None
def create_chapter(db, lesson_id: int, chapter_index: int, title: str, content: str) -> Chapter
def list_chapters_in_lesson(db, lesson_id: int) -> list[Chapter]

def create_chapter_quiz(db, chapter_id: int, quiz_type: str, question: str,
                         expected_answer: str | None, option_a: str | None,
                         option_b: str | None, option_c: str | None,
                         option_d: str | None, correct_options: list | None) -> ChapterQuiz
def list_quizzes_for_chapter(db, chapter_id: int) -> list[ChapterQuiz]
def list_quizzes_for_lesson(db, lesson_id: int) -> list[ChapterQuiz]
```

### Services

#### To Delete
None.

#### To Update
None.

#### To Add New
None — content operations are pure CRUD; no business logic service needed.

### API Endpoints

#### To Delete
None.

#### To Update
- `backend/src/api/api_router.py`: add `from src.api import content` and `api_router.include_router(content.router, prefix="/api", tags=["content"])`
- `backend/src/models/__init__.py`: import `Book`, `Lesson`, `Chapter`, `ChapterQuiz`
- `backend/src/configs.py`: add `webapp_access_token: str = os.getenv("WEBAPP_ACCESS_TOKEN", "")` to `Settings`

#### To Add New

File: `backend/src/api/content.py`

All write endpoints require `Authorization: Bearer <WEBAPP_ACCESS_TOKEN>` validated by a `verify_agent_token` dependency:
```python
from fastapi import Header, HTTPException
from src.configs import settings

def verify_agent_token(authorization: str = Header(...)) -> None:
    if not authorization.startswith("Bearer ") or authorization[7:] != settings.webapp_access_token:
        raise HTTPException(status_code=401, detail="Invalid or missing Bearer token")
```
All read endpoints require session cookie (via `get_current_user`).

| Method | Path | Auth | Request body | Response |
|--------|------|------|-------------|----------|
| POST | `/api/content/books` | Bearer | `{ book_id, title }` | `BookResponse` |
| POST | `/api/content/lessons` | Bearer | `{ book_id, lesson_index, title }` | `LessonResponse` |
| POST | `/api/content/chapters` | Bearer | `{ lesson_id, chapter_index, title, content }` | `ChapterResponse` |
| POST | `/api/content/quizzes` | Bearer | `{ chapter_id, quizzes: [QuizCreate] }` | `{ inserted: int }` |
| GET | `/api/content/books` | Session | — | `list[BookResponse]` |
| GET | `/api/content/books/{book_id}/structure` | Session | — | `BookStructureResponse` |

`QuizCreate`:
```json
{
  "quiz_type": "free_recall",
  "question": "...",
  "expected_answer": "...",
  "option_a": null,
  "option_b": null,
  "option_c": null,
  "option_d": null,
  "correct_options": null
}
```

`BookStructureResponse`:
```json
{
  "book_id": "ml",
  "title": "Machine Learning",
  "lessons": [
    {
      "id": 1, "lesson_index": 1, "title": "Introduction",
      "chapters": [
        { "id": 1, "chapter_index": 1, "title": "Ch1: ...", "quiz_count": 2 }
      ]
    }
  ]
}
```

File: `backend/src/schemas/content.py` — Pydantic models for all requests/responses above.

### Testing

#### To Delete
None.

#### To Update
None.

#### To Add New

File: `backend/tests/test_content_api.py`

- `test_create_book_bearer_auth` — POST /api/content/books with valid Bearer token → 200
- `test_create_book_unauthorized` — POST without auth → 401
- `test_create_lesson_in_book` — POST /api/content/lessons → 200, lesson_index stored
- `test_create_chapter` — POST /api/content/chapters → 200
- `test_upload_quizzes_mc` — POST /api/content/quizzes with MC type → correct_options stored
- `test_upload_quizzes_open_ended` — POST /api/content/quizzes with free_recall type → expected_answer stored
- `test_list_books` — GET /api/content/books (session auth) → list returned
- `test_book_structure` — GET /api/content/books/{id}/structure → full tree

Pre-commit loop:
1. Run `pre-commit run --all-files`
2. Fix lint errors, unused imports, line count violations
3. Repeat until clean

### Frontend

#### To Delete
None.

#### To Update
None.

#### To Add New
None — frontend for book selection is part of Plan 5 (Frontend Slides).

### Documentation

#### Abstract (`docs/abstract/`)

- **Create** `docs/abstract/content_upload.md`:
  - Status: Plan
  - Problem: no way to load learning content into the system
  - Solution: local agent uploads books/lessons/chapters/quizzes via API
  - User Flow: agent reads markdown files → calls upload endpoints → content stored
  - Scope: books, lessons, chapters, quizzes upload; not manual entry in UI
  - Acceptance Criteria: agent can upload a full book with quizzes via API

- **Update** `docs/abstract/index.md`: add row 2 for Content Upload

#### Technical (`docs/technical/`)

- **Create** `docs/technical/content_upload.md`:
  - Architecture: local agent → POST endpoints → PostgreSQL
  - Data Model: `Book`, `Lesson`, `Chapter`, `ChapterQuiz` with all columns
  - Pipeline: upload sequence diagram
  - API Layer: all endpoints from plan
  - CRUD Layer: all functions from plan
  - Component Checklist

- **Update** `docs/technical/index.md`: add row 3 for Content Upload

### Chrome Claude Extension Execution

After implementation is complete, execute the Chrome E2E tests defined in `docs/chrome_test/slide_stack.md` (created in Plan 5) — no browser tests needed for this backend-only plan.

---

## Dependencies

- `users` table (auth) — `chapter_quizzes` has no user dependency; `users` needed only by subsequent plans.
- `WEBAPP_ACCESS_TOKEN` env var — must be set for Bearer auth on upload endpoints.

## Open Questions

None.
