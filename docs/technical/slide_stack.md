# Slide Stack — Technical Design (Backend)

[< Prev: Revision Scheduling](./revision_scheduling.md) | [Parent](./index.md)

## Architecture

```
GET  /api/slides/next           → SlideSelector.get_next_slide(db, username, book_id)
POST /api/slides/chapters/{id}/learnt
                                → LearningProgressService.mark_chapter_learnt
                                → RevisionService.on_chapter_learnt
POST /api/slides/quizzes/{id}/respond
                                → auto-grade (MC) or QuizGrader.grade (open-ended)
                                → RevisionService.record_quiz_response
```

## Data Model

**`quiz_skip_log`**

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | Integer | PK |
| `username` | String | FK → users.username, NOT NULL |
| `quiz_id` | Integer | FK → chapter_quizzes.id, NOT NULL |
| `lesson_id` | Integer | FK → lessons.id, NOT NULL |
| `round_num` | Integer | NOT NULL |
| `skipped_at` | Timestamp | NOT NULL, DEFAULT NOW() |

## Pipeline

### GET /api/slides/next — 3-Tier Algorithm

```
SlideSelector.get_next_slide(db, username, book_id)
  │
  ├── lesson_count = get_lesson_count(db, username)
  │
  ├── TIER 1: due_rounds = get_due_rounds(db, username, lesson_count)
  │   ├── For each round: get_eligible_quiz_ids_for_round(db, username, lesson_id, round_num)
  │   ├── For each quiz: compute m(t) using UserQuizRecall.forgetting_rate
  │   ├── Sort ascending by m(t) (weakest first, lowest m(t) = worst recall)
  │   └── Return first quiz as QuizSlide → done
  │
  ├── TIER 2: no due revisions
  │   ├── If book_id: get_next_chapter_in_book(db, username, book_id)
  │   ├── Else: get_next_chapters_all_books(db, username) → random pick
  │   └── Return chapter as ChapterSlide → done
  │
  └── TIER 3: no unlearnt chapters
      ├── get_skipped_quizzes(db, username) → ordered by skipped_at ASC
      └── Return first as QuizSlide or 'none'
```

### POST /api/slides/chapters/{chapter_id}/learnt

```
LearningProgressService.mark_chapter_learnt(db, username, chapter_id)
  → ChapterLearntResult { lesson_id, lesson_fully_learnt, lesson_count, chapter_quiz_ids }

RevisionService.on_chapter_learnt(db, username, lesson_id, chapter_quiz_ids, lesson_count)

Return { lesson_fully_learnt, lesson_count }
```

### POST /api/slides/quizzes/{quiz_id}/respond

```
Body: { round_num, lesson_id, user_answer, is_skip }
  │
  ├── load quiz (quiz_type, correct_options, expected_answer)
  ├── lesson_count = get_lesson_count(db, username)
  │
  ├── If is_skip=true:
  │     log_quiz_skip(db, username, quiz_id, lesson_id, round_num)
  │     record_quiz_response(..., is_correct=None)
  │     Return { is_correct: null, feedback: null, round_done }
  │
  ├── If quiz_type == 'multiple_choice':
  │     is_correct = (user_answer in correct_options)
  │     feedback = null
  │
  └── Else (open-ended):
        QuizGrader.grade(question, expected_answer, user_answer, quiz_type)
        → { is_correct, feedback }
  │
  ├── remove_quiz_skip(db, username, quiz_id)
  └── record_quiz_response(..., is_correct) → QuizResponseResult
      Return { is_correct, feedback, round_done }
```

## API Layer

| Method | Path | Auth | Handler |
|--------|------|------|---------|
| GET | `/api/slides/next` | Session | `get_next_slide` |
| POST | `/api/slides/chapters/{chapter_id}/learnt` | Session | `mark_chapter_learnt` |
| POST | `/api/slides/quizzes/{quiz_id}/respond` | Session | `respond_to_quiz` |

## Service Layer

**`SlideSelector`** (`backend/src/service/slide_selector.py`):

| Method | Description |
|--------|-------------|
| `get_next_slide(db, username, book_id)` | Returns `SlideResult` using 3-tier algorithm |

**`SlideResult`** dataclass:

| Field | Type | Description |
|-------|------|-------------|
| `slide_type` | str | `'chapter'`, `'quiz'`, or `'none'` |
| `chapter` | dict \| None | Chapter data enriched with book/lesson info |
| `quiz` | dict \| None | Quiz data enriched with round/lesson/book info |

**`QuizGrader`** (`backend/src/service/quiz_grader.py`):

| Method | Description |
|--------|-------------|
| `grade(question, expected_answer, user_answer, quiz_type)` | Calls Claude API, returns `GradingResult` |

**`GradingResult`** dataclass:

| Field | Type | Description |
|-------|------|-------------|
| `is_correct` | bool | Whether answer is correct |
| `feedback` | str | One-sentence explanation |

## LLM Requests Layer

**System prompt:** `backend/resources/prompts/quiz_grader.md`

**Model:** `claude-haiku-4-5-20251001`, temperature: 0.1, max_tokens: 256

**User message structure:**
```
Quiz type: {quiz_type}
Question: {question}
Expected answer: {expected_answer}
Student answer: {user_answer}
```

**Output schema:**
```json
{"is_correct": bool, "feedback": "one sentence explaining the grade"}
```

## CRUD Layer

**`crud_slides.py`:**

| Function | Description |
|----------|-------------|
| `get_next_chapter_in_book(username, book_id)` | First unlearnt chapter in book order |
| `get_next_chapters_all_books(username)` | One unlearnt chapter per book |
| `get_eligible_quiz_ids_for_round(username, lesson_id, round_num)` | Not-answered, not-skipped quiz IDs |
| `log_quiz_skip(username, quiz_id, lesson_id, round_num)` | Insert skip log row (idempotent) |
| `remove_quiz_skip(username, quiz_id)` | Delete skip log row on answer |
| `get_skipped_quizzes(username)` | Skipped quizzes ordered by skipped_at ASC |

## Component Checklist

- [x] Migration — `scripts/sql/004_slide_skips.sql`
- [x] Models — `backend/src/models/slide_management.py` (`QuizSkipLog`)
- [x] CRUD — `backend/src/crud/crud_slides.py`
- [x] Service — `backend/src/service/slide_selector.py`
- [x] Service — `backend/src/service/quiz_grader.py`
- [x] System prompt — `backend/resources/prompts/quiz_grader.md`
- [x] Schemas — `backend/src/schemas/slides.py`
- [x] API — `backend/src/api/slides.py`
- [x] Router registration — `backend/src/api/api_router.py`
- [x] Tests — `backend/tests/test_slide_selector.py`
- [x] Tests — `backend/tests/test_slides_api.py`
- [x] Tests — `backend/tests/test_quiz_grader.py`

---

[< Prev: Revision Scheduling](./revision_scheduling.md) | [Parent](./index.md)
