# Content Upload — Technical Design

[< Prev: Authentication](./authentication.md) | [Parent](./index.md)

## Related Docs
- Abstract: [abstract/content_upload.md](../abstract/content_upload.md)

## Architecture

```
+-------------------+     +-------------+     +----------+
|  Local Agent      | --> |   Backend   | --> | Database |
|  (lesson-upload)  |     |  (FastAPI)  |     | (Postgres)|
+-------------------+     +-------------+     +----------+
  Bearer token              content.py          books
                            crud_content.py     lessons
                                                chapters
                                                chapter_quizzes
```

Write endpoints use a static Bearer token (`WEBAPP_ACCESS_TOKEN`) validated by `verify_agent_token`.
Read endpoints use the session cookie via `authenticate_user_from_request`.

## Data Model

**`books`**

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | Integer | PK |
| `book_id` | String | UNIQUE, NOT NULL |
| `title` | String | NOT NULL |
| `created_at` | Timestamp | DEFAULT NOW() |

**`lessons`**

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | Integer | PK |
| `book_id` | String | FK → books.book_id, NOT NULL |
| `lesson_index` | Integer | NOT NULL |
| `title` | String | NOT NULL |
| `created_at` | Timestamp | DEFAULT NOW() |
| — | — | UNIQUE(book_id, lesson_index) |

**`chapters`**

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | Integer | PK |
| `lesson_id` | Integer | FK → lessons.id, NOT NULL |
| `chapter_index` | Integer | NOT NULL |
| `title` | String | NOT NULL |
| `content` | Text | NOT NULL |
| `created_at` | Timestamp | DEFAULT NOW() |
| — | — | UNIQUE(lesson_id, chapter_index) |

**`chapter_quizzes`**

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | Integer | PK |
| `chapter_id` | Integer | FK → chapters.id, NOT NULL |
| `quiz_type` | String | NOT NULL — `free_recall`, `teach_back`, `cloze`, `multiple_choice` |
| `question` | Text | NOT NULL |
| `expected_answer` | Text | nullable — populated for open-ended types |
| `option_a/b/c/d` | Text | nullable — populated for `multiple_choice` only |
| `correct_options` | JSONB | nullable — e.g. `["A"]` or `["A","C"]` |
| `created_at` | Timestamp | DEFAULT NOW() |

## Pipeline

### Upload Sequence

```
Local agent
  │
  ├── POST /api/content/books { book_id, title }
  │         verify_agent_token → crud_content.create_book
  │
  ├── POST /api/content/lessons { book_id, lesson_index, title }
  │         verify_agent_token → crud_content.create_lesson
  │
  ├── POST /api/content/chapters { lesson_id, chapter_index, title, content }
  │         verify_agent_token → crud_content.create_chapter
  │
  └── POST /api/content/quizzes { chapter_id, quizzes: [...] }
            verify_agent_token → crud_content.create_chapter_quiz × N
```

### Frontend Read Sequence

```
Frontend (session cookie)
  │
  ├── GET /api/content/books
  │         authenticate_user_from_request → crud_content.list_books
  │
  └── GET /api/content/books/{book_id}/structure
            authenticate_user_from_request → crud_content.list_lessons_in_book
              → for each lesson: list_chapters_in_lesson → len(list_quizzes_for_chapter)
```

## Backend — API Layer

| Method | Path | Auth | Request | Response |
|--------|------|------|---------|----------|
| POST | `/api/content/books` | Bearer | `{book_id, title}` | `BookResponse` |
| POST | `/api/content/lessons` | Bearer | `{book_id, lesson_index, title}` | `LessonResponse` |
| POST | `/api/content/chapters` | Bearer | `{lesson_id, chapter_index, title, content}` | `ChapterResponse` |
| POST | `/api/content/quizzes` | Bearer | `{chapter_id, quizzes: [QuizCreate]}` | `{inserted: int}` |
| GET | `/api/content/books` | Session | — | `list[BookResponse]` |
| GET | `/api/content/books/{book_id}/structure` | Session | — | `BookStructureResponse` |

Bearer auth: `Authorization: Bearer <WEBAPP_ACCESS_TOKEN>` validated by `verify_agent_token` dependency in `content.py`.

## Backend — CRUD Layer

**`crud_content.py`:**

| Function | Description |
|----------|-------------|
| `get_book(book_id)` | Query by book_id |
| `create_book(book_id, title)` | Insert new book |
| `list_books()` | All books ordered by book_id |
| `get_lesson(lesson_id)` | Query by PK |
| `create_lesson(book_id, lesson_index, title)` | Insert new lesson |
| `list_lessons_in_book(book_id)` | Lessons ordered by lesson_index |
| `get_lesson_chapter_count(lesson_id)` | Count chapters in lesson |
| `get_chapter(chapter_id)` | Query by PK |
| `create_chapter(lesson_id, chapter_index, title, content)` | Insert new chapter |
| `list_chapters_in_lesson(lesson_id)` | Chapters ordered by chapter_index |
| `create_chapter_quiz(chapter_id, ...)` | Insert one quiz |
| `list_quizzes_for_chapter(chapter_id)` | All quizzes for a chapter |
| `list_quizzes_for_lesson(lesson_id)` | All quizzes in all chapters of a lesson |

## Configuration

| Setting | Source | Default |
|---------|--------|---------|
| `webapp_access_token` | `WEBAPP_ACCESS_TOKEN` env var | `""` |

Set `WEBAPP_ACCESS_TOKEN` in `.env` before running the agent upload workflow.

## Component Checklist

- [ ] Migration — `scripts/sql/001_content_schema.sql`
- [ ] Model — `backend/src/models/content.py` (`Book`, `Lesson`, `Chapter`, `ChapterQuiz`)
- [ ] CRUD — `backend/src/crud/crud_content.py`
- [ ] Schemas — `backend/src/schemas/content.py`
- [ ] API — `backend/src/api/content.py` (6 endpoints + `verify_agent_token`)
- [ ] Config — `backend/src/configs.py` (`webapp_access_token`)
- [ ] Router — registered in `backend/src/api/api_router.py`
- [ ] Tests — `backend/tests/test_content_api.py`

---

[< Prev: Authentication](./authentication.md) | [Parent](./index.md)
