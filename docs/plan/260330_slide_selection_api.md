# Slide Selection API — Stacking Algorithm, AI Grading & REST Endpoints

**Feature**: Implement the slide selection algorithm, AI quiz grader, and the three slide endpoints
**Plan Created:** 2026-03-30
**Status:** Plan
**Reference**:
- [Source spec](../learning_strategy.md#74-stacking-algorithm)
- [Technical — Slide Stack](../technical/slide_stack.md)
- [Depends on: Plan 1](./260330_content_schema.md)
- [Depends on: Plan 2](./260330_learning_progress.md)
- [Depends on: Plan 3](./260330_revision_scheduling.md)

---

## Problem Statement

1. There is no API endpoint that implements the slide selection priority logic (revision → new chapter → skipped).
2. Open-ended quiz types (free recall, teach-back, cloze) need AI grading — no LLM integration exists.
3. The three slide interactions (mark chapter as learnt, submit quiz answer, get next slide) have no API surface.

---

## Proposed Solution

Implement a `SlideSelector` service that encodes the three-tier priority algorithm from spec §7.4, three REST endpoints, and a `QuizGrader` service that uses the Claude API to grade open-ended answers. Multiple-choice answers are auto-graded.

**Priority tiers:**
```
1. Due revision quizzes  (rounds where due_at_lesson_count <= lesson_count, status='open')
   → order by ascending recall score m(t) (weakest first)
   → randomly interleaved across books
2. Next unlearnt chapter
   → if book_id specified: next in book's lesson/chapter order
   → if all books: random from each book's next chapter
3. Skipped items
   → quizzes answered with is_correct=NULL, oldest first
```

---

## Current Implementation Analysis

### What Exists (keep as-is)

| Component | File | Status |
|-----------|------|--------|
| Auth middleware | `backend/src/auth.py` | Keep — `get_current_user` |
| API router | `backend/src/api/api_router.py` | Keep — will register slides router |
| `LearningProgressService` | Plan 2 | Keep — called from mark-learnt endpoint |
| `RevisionService` | Plan 3 | Keep — called from both endpoints |

### What Changes

| Component | Current | Proposed |
|-----------|---------|----------|
| `backend/src/api/api_router.py` | content + auth routers | Also register `slides` router |
| `backend/src/main.py` | no `resources/` path | May need `resources/prompts/` path for grader system prompt |

---

## Implementation Plan

### Key Workflow

#### GET /api/slides/next

```
GET /api/slides/next?book_id=optional
  │
  ▼
SlideSelector.get_next_slide(db, username, book_id)
  │
  ├── lesson_count = crud_learning_progress.get_lesson_count(db, username)
  │
  ├── TIER 1: due_rounds = crud_revision.get_due_rounds(db, username, lesson_count)
  │   ├── For each round: get eligible quiz_ids (not yet answered in this round)
  │   ├── For each quiz: compute m(t) = exp(-n * (lesson_count - last_reviewed) / 10)
  │   ├── Sort all due quizzes ascending by m(t)  (weakest = lowest m(t) first)
  │   └── Return first quiz as QuizSlide → done
  │
  ├── TIER 2: no due revisions
  │   ├── learnt_chapter_ids = crud_learning_progress.get_learnt_chapter_ids_for_user(db, username)
  │   ├── If book_id specified: next chapter in book order not in learnt_ids
  │   ├── If no book_id: for each book, find first unlearnt chapter; pick randomly
  │   └── Return chapter as ChapterSlide → done
  │
  └── TIER 3: no unlearnt chapters
      ├── Find all quiz responses with is_correct=NULL for this user (oldest first)
      └── Return first as QuizSlide (skipped resurface) → done or return NoSlide
```

#### POST /api/slides/chapters/{chapter_id}/learnt

```
POST /api/slides/chapters/{chapter_id}/learnt
  │
  ▼
LearningProgressService.mark_chapter_learnt(db, username, chapter_id)
  → { lesson_id, lesson_fully_learnt, lesson_count, chapter_quiz_ids }
  │
  ▼
RevisionService.on_chapter_learnt(db, username, lesson_id, chapter_quiz_ids, lesson_count)
  │
  ▼
Return { lesson_fully_learnt: bool, lesson_count: int }
```

#### POST /api/slides/quizzes/{quiz_id}/respond

```
POST /api/slides/quizzes/{quiz_id}/respond
Body: { round_num, lesson_id, user_answer: str, is_skip: bool }
  │
  ├── Load quiz from DB (quiz_type, expected_answer, correct_options)
  │
  ├── If is_skip=true:
  │     RevisionService.record_quiz_response(..., is_correct=None)
  │     Return { is_correct: null, feedback: null }
  │
  ├── If quiz_type == 'multiple_choice':
  │     is_correct = (user_answer in correct_options)
  │     feedback = null
  │
  └── Else (open-ended):
        QuizGrader.grade(question, expected_answer, user_answer, quiz_type)
        → { is_correct: bool, feedback: str }
  │
  ▼
RevisionService.record_quiz_response(db, username, quiz_id, lesson_id,
                                      round_num, is_correct, lesson_count)
  │
  ▼
Return { is_correct: bool | null, feedback: str | null, round_done: bool }
```

### Database Schema

#### To Delete
None.

#### To Update
None.

#### To Add New

Migration file: `scripts/sql/004_slide_skips.sql`

```sql
CREATE TABLE IF NOT EXISTS quiz_skip_log (
    id SERIAL PRIMARY KEY,
    username VARCHAR NOT NULL REFERENCES users(username),
    quiz_id INTEGER NOT NULL REFERENCES chapter_quizzes(id),
    lesson_id INTEGER NOT NULL REFERENCES lessons(id),
    round_num INTEGER NOT NULL,
    skipped_at TIMESTAMP NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_qsl_user ON quiz_skip_log(username, skipped_at);
```

**Purpose:** Tracks skipped quizzes for Tier 3 (skipped items resurface oldest first).
When the user skips a quiz, a row is inserted. When the quiz is later answered, the row is deleted.

### CRUD

#### To Delete
None.

#### To Update
None.

#### To Add New

File: `backend/src/crud/crud_slides.py`

```python
def get_next_chapter_in_book(db, username: str, book_id: str) -> Chapter | None
    """Find first chapter in book order not yet learnt by user."""

def get_next_chapters_all_books(db, username: str) -> list[Chapter]
    """For each book, find first unlearnt chapter. Return one per book."""

def get_eligible_quiz_ids_for_round(db, username: str,
                                     lesson_id: int, round_num: int) -> list[int]
    """Quiz IDs for the lesson not yet answered or skipped in this round."""

def log_quiz_skip(db, username: str, quiz_id: int,
                  lesson_id: int, round_num: int) -> None

def remove_quiz_skip(db, username: str, quiz_id: int) -> None
    """Called when a previously skipped quiz is answered."""

def get_skipped_quizzes(db, username: str) -> list[dict]
    """Return skipped quizzes ordered by skipped_at ASC (oldest first)."""
```

### Services

#### To Delete
None.

#### To Update
None.

#### To Add New

**File: `backend/src/service/slide_selector.py`**

```python
from dataclasses import dataclass

@dataclass
class SlideResult:
    slide_type: str   # 'chapter', 'quiz', or 'none'
    chapter: dict | None
    quiz: dict | None

class SlideSelector:
    @staticmethod
    def get_next_slide(db, username: str, book_id: str | None) -> SlideResult:
        """Implements the 3-tier priority algorithm described in spec §7.4."""
```

**File: `backend/src/service/quiz_grader.py`**

Uses the Anthropic Python SDK (`anthropic` package) to grade open-ended answers.

```python
from dataclasses import dataclass

@dataclass
class GradingResult:
    is_correct: bool
    feedback: str

class QuizGrader:
    @staticmethod
    def grade(question: str, expected_answer: str,
              user_answer: str, quiz_type: str) -> GradingResult:
        """
        Call Claude API with structured grading prompt.
        Model: claude-haiku-4-5-20251001 (fast, cost-effective for grading).
        Returns structured JSON { is_correct, feedback }.
        """
```

System prompt file: `resources/prompts/quiz_grader.md`

```
You are a quiz grader for a spaced-repetition learning app.
You are given a quiz question, the expected answer, and a student's response.
Your task: determine whether the student demonstrated sufficient understanding.

Guidelines:
- For free recall: accept answers that cover the core concepts, even if worded differently.
- For teach-back: accept if the student explained the idea clearly and correctly.
- For cloze: accept exact or semantically equivalent answers.
- Be lenient on wording; strict on correctness of concepts.

Respond ONLY in JSON: {"is_correct": bool, "feedback": "one sentence explaining the grade"}
```

LLM call structure:
```
System: resources/prompts/quiz_grader.md
User:   Quiz type: {quiz_type}
        Question: {question}
        Expected answer: {expected_answer}
        Student answer: {user_answer}
```

Output schema (`GradingResult`):

| Field | Type | Description |
|-------|------|-------------|
| `is_correct` | bool | Whether the answer demonstrates sufficient understanding |
| `feedback` | str | One sentence explaining why correct or incorrect |

Model: `claude-haiku-4-5-20251001`, temperature: 0.1, output: structured JSON.

### API Endpoints

#### To Delete
None.

#### To Update
- `backend/src/api/api_router.py`: add `from src.api import slides` and register `slides.router`

#### To Add New

File: `backend/src/api/slides.py`
File: `backend/src/schemas/slides.py`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/slides/next` | Session | Get the next slide to show |
| POST | `/api/slides/chapters/{chapter_id}/learnt` | Session | Mark chapter as learnt |
| POST | `/api/slides/quizzes/{quiz_id}/respond` | Session | Submit quiz answer or skip |

**GET /api/slides/next** query params: `book_id` (optional string)

Response:
```json
{
  "slide_type": "chapter",
  "chapter": {
    "id": 1,
    "lesson_id": 2,
    "book_id": "ml",
    "book_title": "Machine Learning",
    "lesson_title": "Introduction",
    "lesson_index": 1,
    "chapter_index": 1,
    "title": "Chapter 1: ...",
    "content": "# markdown..."
  },
  "quiz": null
}
```

```json
{
  "slide_type": "quiz",
  "chapter": null,
  "quiz": {
    "id": 5,
    "chapter_id": 1,
    "quiz_type": "multiple_choice",
    "question": "...",
    "option_a": "...",
    "option_b": "...",
    "option_c": "...",
    "option_d": "...",
    "expected_answer": null,
    "round_num": 0,
    "lesson_id": 2,
    "lesson_title": "Introduction",
    "book_title": "Machine Learning"
  }
}
```

```json
{ "slide_type": "none", "chapter": null, "quiz": null }
```

**POST /api/slides/chapters/{chapter_id}/learnt** response:
```json
{ "lesson_fully_learnt": true, "lesson_count": 1 }
```

**POST /api/slides/quizzes/{quiz_id}/respond** request body:
```json
{ "round_num": 0, "lesson_id": 2, "user_answer": "...", "is_skip": false }
```
Response:
```json
{ "is_correct": true, "feedback": "Good explanation of the core concept.", "round_done": false }
```

### Testing

#### To Delete
None.

#### To Update
None.

#### To Add New

File: `backend/tests/test_slide_selector.py`

- `test_tier1_due_revision_returned_first` — when a revision is due, quiz slide returned
- `test_tier1_weakest_recall_first` — quiz with lower m(t) returned before higher
- `test_tier2_new_chapter_after_no_revisions` — chapter slide returned when no revisions due
- `test_tier2_specific_book_filter` — book_id filter returns chapter from correct book only
- `test_tier3_skipped_resurfaces` — skipped quiz appears when no new chapters
- `test_none_when_all_done` — slide_type=none when all caught up

File: `backend/tests/test_slides_api.py`

- `test_mark_chapter_learnt` — POST mark-learnt returns lesson_fully_learnt + lesson_count
- `test_respond_mc_correct` — MC with right answer → is_correct=true
- `test_respond_mc_incorrect` — MC with wrong answer → is_correct=false
- `test_respond_skip` — is_skip=true → is_correct=null, no recall update
- `test_get_next_slide_chapter` — fresh user gets chapter slide
- `test_get_next_slide_quiz_after_chapter` — after marking chapter learnt, quiz slide returned

File: `backend/tests/test_quiz_grader.py` (unit, mocked LLM)

- `test_grader_returns_is_correct_true` — mocked LLM → GradingResult.is_correct=True
- `test_grader_returns_feedback_string` — feedback populated from LLM response
- `test_mc_auto_graded_no_llm` — MC type never calls LLM

Pre-commit loop:
1. Run `pre-commit run --all-files`
2. Fix issues
3. Repeat until clean

### Frontend

#### To Delete
None.

#### To Update
None.

#### To Add New
None — frontend is Plan 5.

### Documentation

#### Abstract (`docs/abstract/`)
No standalone abstract doc for this plan — covered in `docs/abstract/slide_stack.md` (Plan 5).

#### Technical (`docs/technical/`)

- **Create** `docs/technical/slide_stack.md` (partial — backend only):
  - Architecture, Data Model, Pipeline diagrams for all 3 endpoints
  - API Layer table
  - Service Layer: SlideSelector (3-tier algorithm), QuizGrader (LLM)
  - LLM Requests Layer: QuizGrader prompt diagram and output schema
  - CRUD Layer
  - Component Checklist (backend items only; frontend items added in Plan 5)

- **Update** `docs/technical/index.md`: add row for Slide Stack

### Chrome Claude Extension Execution

No browser tests for this backend-only plan. Browser tests run in Plan 5.

---

## Dependencies

- Plan 1 — `books`, `chapters`, `chapter_quizzes` tables
- Plan 2 — `user_chapter_progress`, `user_lesson_count`, `LearningProgressService`
- Plan 3 — `lesson_revision_rounds`, `user_quiz_recall`, `RevisionService`
- `anthropic` Python package — must be in `backend/requirements.txt`

## Open Questions

None.
