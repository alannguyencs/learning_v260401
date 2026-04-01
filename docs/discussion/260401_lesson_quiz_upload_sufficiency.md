# Discussion: Is the Current Implementation Sufficient for New Lessons and Quizzes?

**Date:** 2026-04-01
**Topic:** End-to-end sufficiency — lesson generation → quiz generation → upload → slide serving

---

## Summary

The content generation side (lesson template, quiz skill) is in good shape. The delivery side (upload.py → API → DB) has significant gaps. The upload script is misaligned with the actual backend API and the new quiz JSON format is richer than what the DB schema currently stores.

---

## What Works

### Lesson generation
- `lesson-create-youtube` produces well-structured 6-section markdown files (sections 0–5)
- The lesson template is clean and consistent

### Quiz generation
- `lesson-quiz-generate` produces 9 quizzes per section (1 free_recall + 1 teach_back + 2 cloze_deletion + 5 multiple_choice)
- All quiz objects carry `section`, `section_name`, `quiz_format` — enabling section-aware retrieval
- Rich metadata fields (`key_points`, `model_answer`, `blanks`, `quiz_take_away`) provide grading material
- Cloze deletions correctly target terminology (not numbers)
- Multiple choice spans 4 cognitive levels with explained options

### Backend (serving)
- The `chapter_quizzes` DB table, CRUD layer, and slide selector are all working
- `QuizGrader` handles open-ended grading via Claude API for `free_recall` and `teach_back`
- The 3-tier slide selector (revision → new chapter → skipped) is fully implemented and tested

---

## The Gaps

### Gap 1 — upload.py sends the wrong payload to the lesson endpoint

`upload.py` (`.claude/skills/lesson-upload/upload.py:121–131`) currently POSTs:

```json
{ "topic": "...", "topic_name": "...", "title": "...", "published_date": "...", "content": "..." }
```

But `POST /api/content/lessons` (`backend/src/schemas/content.py:28–33`) expects:

```json
{ "book_id": "...", "lesson_index": 1, "title": "..." }
```

These schemas are completely incompatible. **The upload will fail at step 3 (lesson upload).** Additionally, the script never calls `POST /api/content/books` first, so the foreign key constraint on `book_id` will cause a 404 before any lesson is inserted.

### Gap 2 — upload.py skips chapter creation entirely

The DB hierarchy is `books → lessons → chapters → chapter_quizzes`. Quizzes must be attached to a `chapter_id`. The upload script:
- Does not call `POST /api/content/chapters`
- Sends individual quizzes to `POST /api/content/quizzes` with `lesson_id` (not `chapter_id`) added

The actual API (`backend/src/api/content.py:94–117`) expects `{chapter_id, quizzes: [...]}`. Without a chapter, every quiz upload will return 404.

### Gap 3 — The new quiz JSON fields don't map to the DB schema

The new quiz JSON (produced by `lesson-quiz-generate`) has fields the DB cannot store:

| Quiz JSON field | DB `chapter_quizzes` column | Status |
|---|---|---|
| `quiz_format` | `quiz_type` | **rename needed** |
| `question` | `question` | OK |
| `model_answer` | `expected_answer` | **rename needed** |
| `blanks` (array) | — | **not stored** |
| `sentence` (cloze) | `question` | **rename needed** |
| `key_points` (array) | — | **not stored** |
| `key_elements` (array) | — | **not stored** |
| `context_hint` | — | **not stored** |
| `quiz_take_away` | — | **not stored** |
| `quiz_learnt` | — | **not stored** |
| `section` | — | **not stored** |
| `section_name` | — | **not stored** |
| `quiz_type` (cognitive level, MC only) | — | **not stored** |
| `option_a/b/c/d` | `option_a/b/c/d` | OK |
| `correct_options` | `correct_options` | OK |

The rich metadata (key_points, blanks, quiz_take_away) is currently silently dropped on upload — it exists only in the local JSON file.

### Gap 4 — No mapping from lesson sections to chapters

The quiz JSON groups quizzes by `section` (1–5). The DB uses `chapters` as the unit under lessons. There is currently no defined mapping: which chapter does Section 1 (Summary) correspond to? The upload flow needs a rule — most likely **one chapter per lesson section** — but this is not implemented or documented anywhere.

---

## Upload Pipeline: Current State vs. Required State

### Current State

```
[Agent] upload.py
  │
  ├── POST /api/content/lessons { topic, topic_name, title, published_date, content }
  │         ← schema mismatch — API returns 422
  │
  └── POST /api/content/quizzes [{ lesson_id, topic_id, ... }]
            ← missing chapter_id — API returns 404
```

### Required State

```
[Agent] upload.py
  │
  ├── POST /api/content/books { book_id, title }
  │         book_id = topic_id (e.g. "themitmonk")
  │
  ├── POST /api/content/lessons { book_id, lesson_index, title }
  │         lesson_index from metadata
  │
  ├── For each section (1–5) in the lesson markdown:
  │     POST /api/content/chapters { lesson_id, chapter_index, title, content }
  │         chapter_index = section number
  │         title         = section name (e.g. "Summary")
  │         content       = section markdown text
  │
  └── For each chapter:
        POST /api/content/quizzes {
          chapter_id,
          quizzes: [
            {
              quiz_type: quiz["quiz_format"],          ← rename
              question:  quiz["question"]              ← or "sentence" for cloze
                         or quiz["sentence"],
              expected_answer: quiz["model_answer"]    ← or blanks joined for cloze
                               or quiz["blanks"].join(", "),
              option_a/b/c/d,
              correct_options
            }
          ]
        }
```

---

## Decision Point: Should the Rich Metadata Be Stored?

The extra fields — `key_points`, `quiz_take_away`, `blanks`, `context_hint`, `section`, `section_name` — are currently generated but not persisted to the DB. There are two paths:

**Option A — Drop on upload (minimal change)**
Map only the fields the DB already has. The rich metadata is only available in the local JSON file. The quiz UI sees `free_recall` as a plain open-ended question, same as `teach_back`. Cloze is stored as a question with `expected_answer` = the blank term.

**Option B — Extend the DB schema (richer quiz UI)**
Add columns or a JSONB `metadata` column to `chapter_quizzes` to persist the extra fields. This enables:
- Fill-in-the-blank UI for cloze deletion (blanks array)
- Key points checklist for free recall
- Section-aware progress tracking (show "Section 2 quizzes done")
- Quiz takeaway display after answering

Option B requires a migration and schema changes; Option A requires only fixing upload.py.

---

## What Needs to Change (Minimum to Make Upload Work)

1. **Fix upload.py** — rewrite to:
   - POST book first (idempotent — ignore 409 conflict)
   - POST lesson with `{book_id, lesson_index, title}`
   - Parse lesson markdown → extract section content → POST one chapter per section
   - POST quizzes per chapter, mapping `quiz_format → quiz_type`, `sentence → question` (cloze), `model_answer → expected_answer`

2. **Define the book_id / lesson_index mapping** — `book_id` = channel slug (e.g. `themitmonk`), `lesson_index` = numeric order from the metadata (e.g. position in channel video history or a sequence number)

3. **Decide on Option A or B** for the rich metadata

---

## Next Steps

- `/feature-plan` — plan the upload.py rewrite and chapter extraction logic
- `/feature-update` — if extending the DB schema for rich quiz metadata (Option B)
- Check `data/metadata/themitmonk/*.json` to confirm what fields are available for `lesson_index`
