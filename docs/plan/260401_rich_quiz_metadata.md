# Rich Quiz Metadata — DB Extension + Upload Pipeline

**Feature**: Store rich quiz metadata in the DB and fix the upload pipeline so lessons and quizzes can actually be uploaded
**Plan Created:** 2026-04-01
**Status:** Plan
**Reference**:
- [Discussion — Lesson & Quiz Upload Sufficiency](../discussion/260401_lesson_quiz_upload_sufficiency.md)
- [Abstract — Content Upload](../abstract/content_upload.md)
- [Technical — Content Upload](../technical/content_upload.md)
- [Technical — Slide Stack](../technical/slide_stack.md)

---

## Problem Statement

1. The `chapter_quizzes` table stores only 9 fields (`quiz_type`, `question`, `expected_answer`, `option_a/b/c/d`, `correct_options`). The `lesson-quiz-generate` skill produces richer JSON with per-format metadata — `key_points`, `blanks`, `context_hint`, `quiz_take_away`, `response_to_user_option_*`, section labels — all of which are silently dropped on upload.
2. The upload script (`upload.py`) sends the **wrong payload** to every endpoint:
   - Lesson upload sends `{topic, topic_name, title, published_date, content}` but the API expects `{book_id, lesson_index, title}`
   - No book is created first, causing FK violation
   - No chapters are created, so `chapter_id` is never available for quiz upload
   - Quiz upload injects `lesson_id` (not `chapter_id`) and sends individual objects instead of a `{chapter_id, quizzes: [...]}` batch
3. The `QuizSlide` response schema does not expose the rich fields, so even if they were stored the frontend could not display them.
4. The frontend `QuizSlide` component renders every quiz format identically — a plain open-ended text field — with no format-specific UI for cloze blanks, key-point checklists, or per-option MC explanations.

---

## Proposed Solution

### DB: four new nullable columns on `chapter_quizzes`

| Column | Type | Purpose |
|--------|------|---------|
| `section_index` | INTEGER | Maps lesson section (1–5) to chapter; enables section-aware filtering |
| `section_name` | VARCHAR | Human-readable section label (e.g., "Summary") |
| `quiz_take_away` | TEXT | One-sentence lesson to display after every answered quiz |
| `quiz_metadata` | JSONB | Format-specific data (blanks, key_points, per-option explanations) |

`quiz_metadata` structure per format:

```
free_recall:     {"key_points": ["...", "..."]}
teach_back:      {"key_elements": ["...", "..."]}
cloze:           {"blanks": ["term"], "context_hint": "..."}
multiple_choice: {
                   "quiz_type_cognitive": "recall|understanding|application|analysis",
                   "quiz_learnt": "...",
                   "response_to_user_option_a": "...",
                   "response_to_user_option_b": "...",
                   "response_to_user_option_c": "...",
                   "response_to_user_option_d": "..."
                 }
```

### Upload pipeline: full rewrite of `upload.py`

```
upload.py (new flow)
  │
  ├── POST /api/content/books { book_id=channel_slug, title=channel_name }
  │         idempotent — ignore 409 Conflict
  │
  ├── POST /api/content/lessons { book_id, lesson_index=YYYYMMDD, title }
  │         lesson_index derived from published_date: int("2025-02-18".replace("-","")) = 20250218
  │
  ├── For each section in lesson markdown (skip "Material"):
  │     POST /api/content/chapters { lesson_id, chapter_index=N, title=section_name, content=section_text }
  │
  └── For each chapter:
        POST /api/content/quizzes {
          chapter_id,
          quizzes: [mapped QuizCreate per quiz in that section]
        }
        Mapping:
          quiz_format "cloze_deletion" → quiz_type "cloze"
          sentence   → question        (cloze only)
          model_answer/blanks joined  → expected_answer (open-ended/cloze)
          section    → section_index
          section_name → section_name
          quiz_take_away → quiz_take_away
          format-specific fields → quiz_metadata JSONB
```

### API: extend `QuizCreate` and `QuizSlide`

`QuizCreate` accepts the four new optional fields so the upload batch can carry them.
`QuizSlide` exposes `section_name`, `quiz_take_away`, and `quiz_metadata` so the frontend can render them.

### Frontend: format-specific quiz UI

`QuizSlide.jsx` branches on `quiz_type` to render:
- **cloze** — fill-in-the-blank input, blank replaced by an `<input>` field
- **free_recall / teach_back** — after grading, show `key_points`/`key_elements` as a checklist
- **multiple_choice** — after answering, reveal per-option explanations from `quiz_metadata`
- All formats — show `section_name` badge and `quiz_take_away` after answering

---

## Current Implementation Analysis

### What Exists (keep as-is)

| Component | File | Status |
|-----------|------|--------|
| `chapter_quizzes` table | `scripts/sql/001_content_schema.sql` | Keep — add columns only |
| `ChapterQuiz` ORM model | `backend/src/models/content.py` | Keep — add columns only |
| `crud_content.py` | `backend/src/crud/crud_content.py` | Keep — update `create_chapter_quiz` signature |
| `get_chapter_quiz` | `backend/src/crud/crud_content.py:111` | Keep as-is |
| `content.py` API router | `backend/src/api/content.py` | Keep — update `create_quizzes` to pass new fields |
| `SlideSelector` + `_build_quiz_dict` | `backend/src/service/slide_selector.py` | Keep — add new fields to dict |
| `QuizGrader` | `backend/src/service/quiz_grader.py` | Keep as-is |
| `slides.py` API | `backend/src/api/slides.py` | Keep as-is — response flows through `SlideResponse` schema |
| `QuizSlide.jsx` | `frontend/src/components/QuizSlide.jsx` | Keep — extend to branch on quiz_type |

### What Changes

| Component | Current | Proposed |
|-----------|---------|----------|
| `chapter_quizzes` columns | 9 columns, no section or metadata | +4: `section_index`, `section_name`, `quiz_take_away`, `quiz_metadata` |
| `QuizCreate` schema | 7 fields | +4 optional fields for new columns |
| `QuizSlide` schema | 10 fields | +3: `section_name`, `quiz_take_away`, `quiz_metadata` |
| `create_chapter_quiz` CRUD | 9 params | +4 optional params for new columns |
| `_build_quiz_dict` | 11 keys | +3 keys from new columns |
| `upload.py` | Broken — wrong payloads for all endpoints | Rewritten — correct book/lesson/chapter/quiz hierarchy |
| `QuizSlide.jsx` frontend | Single generic open-ended render | Branches on quiz_type for format-specific UI |

---

## Implementation Plan

### Key Workflow

#### To Delete
None.

#### To Update
None.

#### To Add New

The end-to-end flow after this plan:

```
[Local] python upload.py themitmonk/250218_...
  │
  ├── parse lesson markdown → extract 5 sections (Material skipped)
  │
  ├── POST /api/content/books { book_id="themitmonk", title="theMITmonk" }
  │         → 201 created OR 409 conflict (ignored)
  │
  ├── POST /api/content/lessons { book_id="themitmonk", lesson_index=20250218, title="20 Quantum..." }
  │         → lesson_id=N
  │
  ├── For section_index in [1, 2, 3, 4, 5]:
  │     POST /api/content/chapters { lesson_id=N, chapter_index=section_index, title, content }
  │         → chapter_id=K
  │     POST /api/content/quizzes { chapter_id=K, quizzes: [9 mapped quiz objects] }
  │         → { inserted: 9 }
  │
  └── Print: "Lesson N, 45 quizzes uploaded"

[User] navigates to /slides
  │
  ├── GET /api/slides/next → QuizSlide with section_name, quiz_take_away, quiz_metadata
  │
  └── QuizSlide.jsx renders based on quiz_type:
        cloze        → fill-in-blank input field
        free_recall  → text area; after grading shows key_points checklist
        teach_back   → text area; after grading shows key_elements checklist
        multiple_choice → options; after answering shows per-option explanations
        all formats  → quiz_take_away shown in feedback panel
                     → section_name badge shown in slide header
```

---

### Database Schema

#### To Delete
None.

#### To Update
None.

#### To Add New

**Migration file**: `scripts/sql/006_chapter_quizzes_rich_metadata.sql`

```sql
-- Add rich metadata columns to chapter_quizzes
ALTER TABLE chapter_quizzes
  ADD COLUMN IF NOT EXISTS section_index INTEGER,
  ADD COLUMN IF NOT EXISTS section_name VARCHAR,
  ADD COLUMN IF NOT EXISTS quiz_take_away TEXT,
  ADD COLUMN IF NOT EXISTS quiz_metadata JSONB;

-- Index for section-aware queries
CREATE INDEX IF NOT EXISTS idx_cq_section ON chapter_quizzes(section_index);
```

Column notes:
- All four columns are nullable — existing rows are unaffected
- `section_index`: integer matching the lesson section number (1 = Summary, 2 = Recommendation, etc.)
- `section_name`: label matching the markdown heading (e.g., "Summary", "One-Liners")
- `quiz_take_away`: one-sentence learning anchor shown after every answered quiz
- `quiz_metadata`: JSONB blob with format-specific keys; shape varies by `quiz_type` (see Proposed Solution)

---

### CRUD

#### To Delete
None.

#### To Update

**`backend/src/crud/crud_content.py`** — `create_chapter_quiz`:

```python
def create_chapter_quiz(
    db: Session,
    chapter_id: int,
    quiz_type: str,
    question: str,
    expected_answer: Optional[str],
    option_a: Optional[str],
    option_b: Optional[str],
    option_c: Optional[str],
    option_d: Optional[str],
    correct_options: Optional[list],
    section_index: Optional[int] = None,
    section_name: Optional[str] = None,
    quiz_take_away: Optional[str] = None,
    quiz_metadata: Optional[dict] = None,
) -> ChapterQuiz:
```

Add the four new params as keyword-only with defaults of `None`. Pass them to `ChapterQuiz(...)`.

#### To Add New
None.

---

### Services

#### To Delete
None.

#### To Update

**`backend/src/service/slide_selector.py`** — `_build_quiz_dict`:

Add the three new fields to the returned dict:

```python
return {
    # ... existing fields ...
    "section_name": quiz.section_name,
    "quiz_take_away": quiz.quiz_take_away,
    "quiz_metadata": quiz.quiz_metadata,
}
```

#### To Add New
None.

---

### API Endpoints

#### To Delete
None.

#### To Update

**`backend/src/schemas/content.py`** — `QuizCreate`:

Add four optional fields:

```python
class QuizCreate(BaseModel):
    quiz_type: str
    question: str
    expected_answer: Optional[str] = None
    option_a: Optional[str] = None
    option_b: Optional[str] = None
    option_c: Optional[str] = None
    option_d: Optional[str] = None
    correct_options: Optional[List[str]] = None
    section_index: Optional[int] = None          # new
    section_name: Optional[str] = None           # new
    quiz_take_away: Optional[str] = None         # new
    quiz_metadata: Optional[dict] = None         # new
```

**`backend/src/api/content.py`** — `create_quizzes` endpoint:

Pass the new fields from `quiz` object to `create_chapter_quiz`:

```python
crud_content.create_chapter_quiz(
    db,
    chapter_id=body.chapter_id,
    quiz_type=quiz.quiz_type,
    question=quiz.question,
    expected_answer=quiz.expected_answer,
    option_a=quiz.option_a,
    option_b=quiz.option_b,
    option_c=quiz.option_c,
    option_d=quiz.option_d,
    correct_options=quiz.correct_options,
    section_index=quiz.section_index,       # new
    section_name=quiz.section_name,         # new
    quiz_take_away=quiz.quiz_take_away,     # new
    quiz_metadata=quiz.quiz_metadata,       # new
)
```

**`backend/src/schemas/slides.py`** — `QuizSlide`:

Add three new optional fields:

```python
class QuizSlide(BaseModel):
    # ... existing fields ...
    section_name: Optional[str] = None
    quiz_take_away: Optional[str] = None
    quiz_metadata: Optional[dict] = None
```

#### To Add New
None.

---

### Testing

#### To Delete
None.

#### To Update

**`backend/tests/test_content_api.py`** — add tests:
- `test_upload_quiz_with_rich_metadata` — POST /api/content/quizzes with `section_index`, `section_name`, `quiz_take_away`, `quiz_metadata` → verify all fields stored in DB
- `test_upload_cloze_quiz_metadata` — POST cloze quiz with `{"blanks": ["H = O/D"]}` in `quiz_metadata` → verify JSONB stored correctly
- `test_upload_mc_quiz_with_option_explanations` — POST MC quiz with full `quiz_metadata` including `response_to_user_option_*` → verify DB round-trips correctly

**`backend/tests/test_slide_selector.py`** — add test:
- `test_quiz_slide_includes_rich_metadata` — verify that `_build_quiz_dict` includes `section_name`, `quiz_take_away`, `quiz_metadata` when the DB row has them
- `test_quiz_slide_null_metadata_safe` — verify `_build_quiz_dict` returns `None` for all three fields when they are NULL in DB (backwards compatibility)

#### To Add New

No new test files. All additions go into the two existing files above.

Pre-commit loop:
1. Run `source venv/bin/activate && pre-commit run --all-files`
2. Fix any lint errors, unused imports, line-count violations
3. Repeat until pre-commit passes cleanly on a full re-run with no new failures

---

### Frontend

#### To Delete
None.

#### To Update

**`frontend/src/components/QuizSlide.jsx`**:

1. **Section name badge** — display `quiz.section_name` as a small label in the slide header (e.g., "Section: Summary"). Show only if `section_name` is non-null.

2. **Cloze format** — when `quiz_type === 'cloze'`, render the `question` string with `___` replaced by an `<input>` element. The user types their answer into the blank. `quiz_metadata.blanks[0]` is used as the grading reference (passed as `expected_answer` which already holds the correct term — the blank input feeds `user_answer`).

3. **Feedback panel extension** — after submitting any quiz, show:
   - Existing: `is_correct` result + Claude `feedback` text
   - New: `quiz.quiz_take_away` rendered in a distinct "Key Takeaway" block (show only if non-null)
   - For `multiple_choice`: render each option label with its corresponding `quiz_metadata.response_to_user_option_*` explanation below it; highlight correct options green, incorrect red
   - For `free_recall`: render `quiz_metadata.key_points` as a bulleted checklist titled "Key Points"
   - For `teach_back`: render `quiz_metadata.key_elements` as a bulleted checklist titled "Key Elements"

**`frontend/src/services/api.js`** — no changes needed; `respondToQuiz` already passes through the full response.

**`frontend/src/hooks/useSlide.js`** — no changes needed; quiz object is passed as-is to the component.

#### To Add New
None.

---

### Upload Script

#### To Delete

**`backend/src/api/content.py`** (upload.py, not backend) — the existing upload.py logic for `upload_lesson` and `upload_questions` functions must be replaced entirely.

Actually: `.claude/skills/lesson-upload/upload.py` — delete the `upload_lesson` and `upload_questions` functions. Replace with new functions listed below.

#### To Update

**`.claude/skills/lesson-upload/upload.py`** — full rewrite of the upload pipeline. Keep `load_env`, `find_file`, `read_files`, `tick_to_learn`, `cleanup`, and `main` structure. Replace the core upload logic:

**New function: `parse_lesson_sections(lesson_content: str) -> list[dict]`**

Extracts sections from the markdown. Returns list of `{section_index, title, content}`, skipping the first section ("Material").

```python
def parse_lesson_sections(lesson_content):
    """Split lesson markdown into sections. Skip 'Material' (section 0)."""
    parts = re.split(r'\n---\n', lesson_content)
    sections = []
    index = 0
    for part in parts:
        lines = part.strip().split('\n')
        if not lines:
            continue
        heading_line = next((l for l in lines if l.startswith('## ')), None)
        if not heading_line:
            continue
        title = heading_line[3:].strip()
        if title.lower() == 'material':
            continue
        index += 1
        content = part.strip()
        sections.append({'section_index': index, 'title': title, 'content': content})
    return sections
```

**New function: `upload_book(api_url, token, book_id, book_title) -> None`**

POST `/api/content/books` with `{book_id, title}`. Ignore 409 (already exists).

**Rename `upload_lesson` → `upload_lesson_record`**

POST `/api/content/lessons` with `{book_id, lesson_index, title}` where:
- `book_id` = channel slug from metadata (e.g., `themitmonk`)
- `lesson_index` = `int(metadata["published_date"].replace("-", ""))` (e.g., 20250218)
- `title` = `metadata["title"]`

Returns `lesson_id`.

**New function: `upload_chapter(api_url, token, lesson_id, section) -> chapter_id`**

POST `/api/content/chapters` with `{lesson_id, chapter_index=section["section_index"], title=section["title"], content=section["content"]}`.

**New function: `map_quiz_to_create(q, chapter_id, section_index, section_name) -> dict`**

Maps a quiz JSON object to a `QuizCreate` payload:

```python
def map_quiz_to_create(q, chapter_id, section_index, section_name):
    quiz_format = q.get("quiz_format", "")
    # Normalise cloze_deletion → cloze
    quiz_type = "cloze" if quiz_format == "cloze_deletion" else quiz_format

    # question field
    question = q.get("sentence") if quiz_format == "cloze_deletion" else q.get("question")

    # expected_answer field
    if quiz_format == "cloze_deletion":
        expected_answer = ", ".join(q.get("blanks", []))
    else:
        expected_answer = q.get("model_answer")

    # quiz_metadata — format-specific
    if quiz_format == "free_recall":
        quiz_metadata = {"key_points": q.get("key_points", [])}
    elif quiz_format == "teach_back":
        quiz_metadata = {"key_elements": q.get("key_elements", [])}
    elif quiz_format == "cloze_deletion":
        quiz_metadata = {"blanks": q.get("blanks", []), "context_hint": q.get("context_hint", "")}
    elif quiz_format == "multiple_choice":
        quiz_metadata = {
            "quiz_type_cognitive": q.get("quiz_type", ""),
            "quiz_learnt": q.get("quiz_learnt", ""),
            "response_to_user_option_a": q.get("response_to_user_option_a", ""),
            "response_to_user_option_b": q.get("response_to_user_option_b", ""),
            "response_to_user_option_c": q.get("response_to_user_option_c", ""),
            "response_to_user_option_d": q.get("response_to_user_option_d", ""),
        }
    else:
        quiz_metadata = {}

    return {
        "quiz_type": quiz_type,
        "question": question,
        "expected_answer": expected_answer,
        "option_a": q.get("option_a"),
        "option_b": q.get("option_b"),
        "option_c": q.get("option_c"),
        "option_d": q.get("option_d"),
        "correct_options": q.get("correct_options"),
        "section_index": section_index,
        "section_name": section_name,
        "quiz_take_away": q.get("quiz_take_away"),
        "quiz_metadata": quiz_metadata,
    }
```

**New function: `upload_chapter_quizzes(api_url, token, chapter_id, quiz_batch) -> int`**

POST `/api/content/quizzes` with `{chapter_id, quizzes: quiz_batch}`. Returns count inserted.

**Update `main()`**

New orchestration:

```python
# Step 1: load env, read files
# Step 2: derive book_id = channel slug, lesson_index = int(published_date)
# Step 3: upload book (idempotent)
# Step 4: upload lesson record → lesson_id
# Step 5: parse lesson sections
# Step 6: for each section → upload chapter → chapter_id
#          group quizzes by section_index → upload batch
# Step 7: tick_to_learn, cleanup, print result
```

#### To Add New
None.

---

### Documentation

#### Abstract (`docs/abstract/`)

**Update `docs/abstract/content_upload.md`**:
- **Scope** section: add "rich quiz metadata (section labels, takeaways, format-specific fields)" to Included list
- **Acceptance Criteria**: add `[ ] Quiz slides display section name, takeaway, and format-specific metadata after answering`

#### Technical (`docs/technical/`)

**Update `docs/technical/content_upload.md`**:
- **Data Model**: add 4 new columns to `chapter_quizzes` table
- **Pipeline — Upload Sequence**: update quiz upload step to show new field mapping
- **API Layer**: update `QuizCreate` schema table to include 4 new fields
- **Component Checklist**: mark all items done (or update status)

**Update `docs/technical/slide_stack.md`**:
- **Data Model**: no table changes (new columns are in `chapter_quizzes`, already referenced)
- **Pipeline — POST /api/slides/quizzes/{quiz_id}/respond**: note that `QuizSlide` now includes `section_name`, `quiz_take_away`, `quiz_metadata`
- **Frontend — Components**: update `QuizSlide` component description to document format-specific rendering
- **Component Checklist**: add new checklist items for the QuizSlide format branches

---

### Chrome Claude Extension Execution

After implementation is complete, execute the Chrome E2E tests defined in `docs/chrome_test/rich_quiz_metadata.md`.

---

## Dependencies

- `chapter_quizzes` table (Plan `260330_content_schema`) — migration 006 adds to this table
- `QuizGrader` — no changes needed; grading uses `quiz_type`, `question`, `expected_answer` which are unchanged
- `SlideSelector` — `_build_quiz_dict` change is a pure extension (new keys only)
- `upload.py` script — requires lesson markdown files with `## SectionName` headings and quiz JSON from `lesson-quiz-generate`
- `lesson-quiz-generate` skill — must produce `section`, `section_name`, `quiz_take_away`, format-specific fields as currently implemented

## Open Questions

None — all design decisions resolved in the [discussion file](../discussion/260401_lesson_quiz_upload_sufficiency.md).
