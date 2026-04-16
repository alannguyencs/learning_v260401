# Slide Navigation — Back/Forward History

**Feature**: Back/forward navigation through slide history using up/down arrow buttons on the slides page
**Plan Created:** 2026-04-16
**Status:** Plan
**Reference**:
- [Abstract — Slide Stack](../abstract/slide_stack.md)
- [Technical — Slide Stack](../technical/slide_stack.md)

---

## Problem Statement

1. The current `/slides` page only moves forward — `GET /api/slides/next` computes the next slide and discards the previous one. There is no way to revisit a slide already seen.
2. There is no server-side record of which slide the user is currently on. Every page refresh recomputes a fresh next slide, which can be a different slide than the one the user was looking at.
3. The spec (`docs/slides_stack.md`) and abstract doc both state: *"Users can navigate back and forward through their slide history"* — this is a documented requirement that is not yet implemented.

---

## Proposed Solution

Introduce a **two-stack, server-authoritative** navigation model, ported from the `delta/coach` reference project:

- **`UserSlidePosition`** table — stores the user's current slide (one row per user, upserted on every navigation event).
- **`SlideHistory`** table — an ordered log of past and future slides, with a `direction` column (`'back'` or `'forward'`) distinguishing the two stacks.
- Three new API endpoints replace `GET /api/slides/next`:
  - `GET /api/slides/current` — return saved position or compute next if none exists.
  - `POST /api/slides/forward` — replay forward stack (if navigating forward after going back) or compute a fresh next slide.
  - `POST /api/slides/back` — push current slide to forward stack, pop from back-history.
- All responses include `has_previous: bool` so the frontend can show/hide the up-arrow.
- Quiz feedback (`is_correct`, `good_points`, `bad_points`) is persisted as `feedback_json` on the position row so that replaying a quiz slide from history shows the same feedback the user already received.
- The frontend adds up/down arrow buttons: up arrow visible only when `has_previous=true`, down arrow always visible.

```
Navigation model:

  [slide A] ──mark learnt──> [slide B] ──skip──> [slide C]
                                                      ↑ current

  [Back]: push C to forward, restore B
  back-history: [A, B]  forward-stack: [C]

  [Back again]: push B to forward, restore A
  back-history: [A]     forward-stack: [B, C]

  [Forward]: pop B from forward, save as current
  back-history: [A, B]  forward-stack: [C]

  New action (mark chapter learnt):
    → clear forward stack, compute fresh, save new position
```

---

## Current Implementation Analysis

### What Exists (keep as-is)

| Component | File | Status |
|-----------|------|--------|
| `SlideSelector.get_next_slide` | `backend/src/service/slide_selector.py` | Keep — still used by `go_next` when computing fresh slides |
| `POST /api/slides/chapters/{id}/learnt` | `backend/src/api/slides.py` | Keep — direct chapter-learnt endpoint still valid |
| `POST /api/slides/quizzes/{id}/respond` | `backend/src/api/slides.py` | Keep — quiz grading logic unchanged; add `save_feedback` call |
| `POST /api/slides/chat` / `GET /api/slides/chat` | `backend/src/api/slides.py` | Keep — chat endpoints unchanged |
| `crud_slides.py` | `backend/src/crud/crud_slides.py` | Keep — skip log functions unchanged |
| `crud_slide_chat.py` | `backend/src/crud/crud_slide_chat.py` | Keep — chat persistence unchanged |
| `QuizGrader` | `backend/src/service/quiz_grader.py` | Keep |
| `SlideChatService` | `backend/src/service/slide_chat_service.py` | Keep |
| All existing SQL migrations `001`–`007` | `scripts/sql/` | Keep |

### What Changes

| Component | Current | Proposed |
|-----------|---------|----------|
| `GET /api/slides/next` | Stateless: computes next slide on every call | Remove — replaced by `/current` and `/forward` |
| `SlideResponse` schema | `{ slide_type, chapter, quiz }` | Add `has_previous: bool` and `feedback: Optional[dict]` |
| `useSlide.js` hook | Calls `getNextSlide()` on mount; `markLearnt` = POST learnt + fetch next | Calls `loadCurrent()` on mount; `markLearnt` calls `slideForward(chapterId)`; adds `hasPrevious` state and `goPrevious()` |
| `SlidePage.jsx` | No navigation buttons | Add up/down arrow buttons with `hasPrevious` guard on up arrow |
| `api.js` | `getNextSlide(bookId)` | Remove; add `getCurrentSlide(bookId)`, `slideForward(body)`, `slideBack()` |
| `POST /api/slides/quizzes/{id}/respond` | Returns grading result; does not persist feedback | After grading, call `save_feedback(db, username, feedback_json)` to store feedback on current position |

---

## Implementation Plan

### Key Workflow

#### To Delete
- `GET /api/slides/next` endpoint in `backend/src/api/slides.py`
- `apiService.getNextSlide` in `frontend/src/services/api.js`

#### To Update
- `SlideResponse` schema — add `has_previous` and `feedback` fields
- `respond_to_quiz` handler — call `save_feedback` after grading (not skip)
- `useSlide.js` — replace `fetchNextSlide` on mount with `loadCurrent`; change `markLearnt` to `slideForward`; add `hasPrevious`, `goPrevious`
- `SlidePage.jsx` — add arrow navigation UI

#### To Add New
```
POST /api/slides/forward  (mark_chapter_id?)
  │
  ├── Is new action? (mark_chapter_id provided AND not already learnt)
  │   Yes → clear forward stack
  │       → LearningProgressService.mark_chapter_learnt
  │       → RevisionService.on_chapter_learnt
  │       → SlideSelector.get_next_slide → save position
  │
  ├── No new action → check forward stack
  │   Forward stack has entries?
  │   Yes → pop from forward, save as current position
  │   No  → SlideSelector.get_next_slide → clear forward → save position
  │
  └── Return SlideResponse { slide_type, chapter/quiz, feedback, has_previous }

POST /api/slides/back
  │
  ├── Push current position to forward stack
  ├── Pop from back-history into current position
  └── Return SlideResponse { slide_type, chapter/quiz, feedback, has_previous }

GET /api/slides/current
  │
  ├── get_position(username) → row exists?
  │   No  → SlideSelector.get_next_slide → save_position → return
  │   Yes → _rebuild_slide(pos) → return with has_previous = get_history_depth > 0
  └── Return SlideResponse
```

---

### Database Schema

#### To Delete
None.

#### To Update
None.

#### To Add New

**Migration `008_slide_position.sql`** (`scripts/sql/008_slide_position.sql`):

```sql
CREATE TABLE IF NOT EXISTS slide_position (
    username VARCHAR PRIMARY KEY REFERENCES users(username),
    slide_type VARCHAR NOT NULL,
    slide_id INTEGER NOT NULL,
    lesson_id INTEGER,
    round_num INTEGER,
    feedback_json JSONB,
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

**Migration `009_slide_history.sql`** (`scripts/sql/009_slide_history.sql`):

```sql
CREATE TABLE IF NOT EXISTS slide_history (
    id SERIAL PRIMARY KEY,
    username VARCHAR NOT NULL REFERENCES users(username),
    position INTEGER NOT NULL,
    slide_type VARCHAR NOT NULL,
    slide_id INTEGER NOT NULL,
    lesson_id INTEGER,
    round_num INTEGER,
    feedback_json JSONB,
    direction VARCHAR NOT NULL DEFAULT 'back',
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_slide_history_user_pos
    ON slide_history(username, position);
```

**ORM model file:** `backend/src/models/slide_position.py`

`UserSlidePosition` — maps to `slide_position`:

| Column | Type | Constraints |
|--------|------|-------------|
| `username` | String | PK, FK → users.username |
| `slide_type` | String | NOT NULL |
| `slide_id` | Integer | NOT NULL |
| `lesson_id` | Integer | nullable |
| `round_num` | Integer | nullable |
| `feedback_json` | JSON | nullable |
| `updated_at` | Timestamp | NOT NULL, DEFAULT NOW() |

`SlideHistory` — maps to `slide_history`:

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | Integer | PK |
| `username` | String | NOT NULL, FK → users.username |
| `position` | Integer | NOT NULL |
| `slide_type` | String | NOT NULL |
| `slide_id` | Integer | NOT NULL |
| `lesson_id` | Integer | nullable |
| `round_num` | Integer | nullable |
| `feedback_json` | JSON | nullable |
| `direction` | String | NOT NULL, DEFAULT `'back'` — `'back'` or `'forward'` |
| `created_at` | Timestamp | NOT NULL, DEFAULT NOW() |

Index: `(username, position)` on `slide_history`.

---

### CRUD

#### To Delete
None.

#### To Update
None.

#### To Add New

**File:** `backend/src/crud/crud_slide_position.py`

| Function | Signature | Description |
|----------|-----------|-------------|
| `get_position` | `(db, username) -> UserSlidePosition \| None` | Fetch current position row |
| `save_position` | `(db, username, slide_type, slide_id, lesson_id, round_num, feedback_json=None) -> None` | Upsert current position; first push the old current (if any) to the back-history stack |
| `save_feedback` | `(db, username, feedback_json: dict) -> None` | Update `feedback_json` on the current position (called after quiz grading) |
| `push_to_history` | `(db, username, slide_type, slide_id, lesson_id, round_num, feedback_json, direction) -> None` | Insert a row into `slide_history` with `position = max + 1` for that direction |
| `pop_from_history` | `(db, username, direction) -> SlideHistory \| None` | Fetch the highest-position row for `direction`, delete it, return it |
| `get_history_depth` | `(db, username) -> int` | Count `direction='back'` rows for the user |
| `push_to_forward` | `(db, username, ...) -> None` | `push_to_history(..., direction='forward')` |
| `pop_from_forward` | `(db, username) -> SlideHistory \| None` | `pop_from_history(username, direction='forward')` |
| `clear_forward` | `(db, username) -> None` | Delete all `direction='forward'` rows for user |
| `go_back` | `(db, username) -> SlideHistory \| None` | Atomically: push current to forward, pop from back-history, return popped row |

---

### Services

#### To Delete
None.

#### To Update
None.

#### To Add New

**File:** `backend/src/service/slide_navigation.py`

| Function | Signature | Description |
|----------|-----------|-------------|
| `get_current_slide` | `(db, username, book_id) -> SlideResult` | Return saved position or compute fresh next if none |
| `go_next` | `(db, username, book_id, mark_chapter_id=None) -> SlideResult` | Replay forward stack or compute fresh; handle chapter-learnt if `mark_chapter_id` provided |
| `go_previous` | `(db, username) -> SlideResult` | Pop back-history into current, push current to forward |
| `_rebuild_slide` | `(db, pos) -> dict` | Reconstruct a chapter or quiz slide dict from `(slide_type, slide_id, lesson_id, round_num)` stored in position |

**`go_next` detail:**
- If `mark_chapter_id` is provided AND `chapter_learnt_at IS NULL` on that chapter:
  - Clear forward stack (new branching action)
  - Call `LearningProgressService.mark_chapter_learnt` + `RevisionService.on_chapter_learnt`
  - Compute fresh slide via `SlideSelector.get_next_slide`
- Else: check forward stack → pop if available; else compute fresh + clear forward
- Call `save_position` (which auto-pushes old current to back-history)
- Return `SlideResult` with `has_previous = get_history_depth(db, username) > 0`

**`SlideResult` additions:** Add `has_previous: bool = False` and `feedback: Optional[dict] = None` to the dataclass in `slide_selector.py`.

---

### API Endpoints

#### To Delete
- `GET /api/slides/next` — remove from `backend/src/api/slides.py`

#### To Update
- `POST /api/slides/quizzes/{quiz_id}/respond` — after grading (not skip), call `crud_slide_position.save_feedback(db, username, { "is_correct": ..., "good_points": ..., "bad_points": ... })`

#### To Add New

**File:** `backend/src/api/slides.py` (add three handlers)

| Method | Path | Handler | Body | Response |
|--------|------|---------|------|----------|
| GET | `/api/slides/current` | `slide_current` | `?book_id=` | `SlideResponse` |
| POST | `/api/slides/forward` | `slide_forward` | `SlideForwardRequest` | `SlideResponse` |
| POST | `/api/slides/back` | `slide_back` | — | `SlideResponse` |

**New schema:** `SlideForwardRequest`
```python
class SlideForwardRequest(BaseModel):
    book_id: Optional[str] = None
    mark_chapter_id: Optional[int] = None
```

**Updated `SlideResponse`:**
```python
class SlideResponse(BaseModel):
    slide_type: str
    chapter: Optional[ChapterSlide] = None
    quiz: Optional[QuizSlide] = None
    has_previous: bool = False
    feedback: Optional[dict] = None
```

**Response examples:**

`GET /api/slides/current` (chapter slide, no history):
```json
{
  "slide_type": "chapter",
  "chapter": { "id": 5, "title": "...", ... },
  "quiz": null,
  "has_previous": false,
  "feedback": null
}
```

`POST /api/slides/back` (quiz slide with prior feedback):
```json
{
  "slide_type": "quiz",
  "chapter": null,
  "quiz": { "id": 12, "question": "...", ... },
  "has_previous": true,
  "feedback": {
    "is_correct": true,
    "good_points": ["Mentioned X", "Explained Y"],
    "bad_points": []
  }
}
```

---

### Testing

#### To Delete
- Tests that call `GET /api/slides/next` — update to use `GET /api/slides/current` or `POST /api/slides/forward`.

#### To Update
- `backend/tests/test_slides_api.py` — remove `test_get_next_slide`; update any helper that uses the old endpoint.

#### To Add New

**Backend:**

`backend/tests/test_slide_navigation.py`
- `test_get_current_slide_no_history` — first call returns a slide and `has_previous=false`
- `test_go_next_computes_fresh` — forward from known position returns next slide
- `test_go_next_replays_forward_stack` — after back+forward, replays from stack
- `test_go_previous_restores_slide` — back returns previous slide with `has_previous` flag
- `test_go_previous_no_history` — returns error/none when at start
- `test_mark_chapter_clears_forward` — new action after back clears forward stack
- `test_feedback_persisted` — after quiz respond, `go_back` + `go_next` returns same slide with `feedback` populated

`backend/tests/test_crud_slide_position.py`
- `test_save_and_get_position`
- `test_save_position_pushes_to_history`
- `test_go_back_pops_history`
- `test_clear_forward`
- `test_push_pop_forward_stack`
- `test_get_history_depth`

**Frontend:**

`frontend/src/__tests__/hooks/useSlide.test.js` — update to mock new API methods (`getCurrentSlide`, `slideForward`, `slideBack`); add tests for `hasPrevious` state and `goPrevious()`.

**Pre-commit loop:**
1. Run `source venv/bin/activate && pre-commit run --all-files`.
2. Fix any issues (lint errors, line count violations — max 300 lines per frontend file).
3. Re-run pre-commit — Prettier may reformat fixes and push files back over limit.
4. Repeat until pre-commit passes cleanly with no new failures.

**Chrome test spec:** `docs/technical/testing_context.md` must be created before Chrome E2E tests can be generated. Once it exists, run `/webapp-dev:chrome-test-generate slide_navigation` to generate the spec, then execute via `/webapp-dev:chrome-test-execute docs/chrome_test/{yymmdd}_{hhmm}_slide_navigation.md`.

---

### Frontend

#### To Delete
- `apiService.getNextSlide` in `frontend/src/services/api.js`
- `fetchNextSlide` export from `useSlide.js` (internal use only; replace public usage with `goPrevious` / `markLearnt` / `skipItem`)

#### To Update

**`frontend/src/services/api.js`:**
- Remove `getNextSlide`
- Add `getCurrentSlide(bookId)` → `GET /api/slides/current?book_id=`
- Add `slideForward(body)` → `POST /api/slides/forward` with `{ book_id, mark_chapter_id? }`
- Add `slideBack()` → `POST /api/slides/back`

**`frontend/src/hooks/useSlide.js`:**
- Add `hasPrevious` state (default `false`)
- Replace `useEffect → fetchNextSlide(null)` with `loadCurrent()` on mount
- `loadCurrent()`: call `apiService.getCurrentSlide(bookId)`, set `slide`, set `hasPrevious` from `data.has_previous`, set `feedback` from `data.feedback`
- `markLearnt(chapterId)`: call `apiService.slideForward({ book_id: bookId, mark_chapter_id: chapterId })` (no longer calls separate `markChapterLearnt`); update `slide`, `hasPrevious`, clear `feedback`
- `fetchNextSlide(currentBookId)`: call `apiService.slideForward({ book_id: currentBookId })`; update `slide`, `hasPrevious`, clear `feedback`
- Add `goPrevious()`: call `apiService.slideBack()`; update `slide`, `hasPrevious`, set `feedback` from `data.feedback`
- `skipItem`: unchanged (still calls `respondToQuiz` then `fetchNextSlide`)

**`frontend/src/pages/SlidePage.jsx`:**
- Destructure `hasPrevious` and `goPrevious` from `useSlide()`
- Add navigation arrows below `BookSelector`:
  ```
  {hasPrevious && (
    <button onClick={goPrevious} aria-label="Previous slide">
      ↑ (ChevronUp icon)
    </button>
  )}
  <button onClick={() => fetchNextSlide(bookId)} aria-label="Next slide">
    ↓ (ChevronDown icon)
  </button>
  ```
- Down arrow: disabled while `loading` or `submitting`; not shown on `slide_type === 'none'`
- Up arrow: only shown when `hasPrevious === true`
- When a quiz slide is replayed from history and `feedback` is present, pass `feedback` prop to `QuizSlide` so the already-graded state is shown immediately (no re-submit needed)

#### To Add New
None beyond what is listed in "To Update."

---

### Documentation

#### To Delete
None.

#### To Update

**`docs/abstract/slide_stack.md`:**
- **Status:** change `Plan` → `In Progress`
- **Solution:** add sentence: *"Users can navigate back and forward through their slide history using arrow buttons."*
- **User Flow:** add navigation block:
  ```
  [Up arrow]   → go to previous slide in history (shown only if history exists)
  [Down arrow] → go to next slide (replays forward history first, then computes new)
  ```
- **Scope / Included:** add *"Back/forward navigation through slide history"*
- **Acceptance Criteria:** add:
  - `- [ ] Up arrow is only visible when there is prior history`
  - `- [ ] Down arrow is always visible (except on All Caught Up state)`
  - `- [ ] Navigating back restores the previous slide with its feedback`
  - `- [ ] After going back, navigating forward replays the forward stack before computing new slides`
  - `- [ ] Marking a chapter as learnt clears the forward stack`

**`docs/technical/slide_stack.md`:**
- **Architecture block:** replace `GET /api/slides/next` with three new endpoints; add `slide_navigation.py` to service list
- **Data Model:** add `UserSlidePosition` and `SlideHistory` table docs
- **Pipeline:** add Forward/Back algorithm section (mirror the Pipeline section above)
- **API Layer table:** remove `GET /api/slides/next`; add `GET /api/slides/current`, `POST /api/slides/forward`, `POST /api/slides/back`
- **Service Layer:** add `slide_navigation.py` functions table
- **CRUD Layer:** add `crud_slide_position.py` functions table
- **Frontend — Services & Hooks:** update `useSlide` method table; add `hasPrevious`, `loadCurrent`, `goPrevious`
- **Frontend — Pages:** update `SlidePage.jsx` description to mention arrow navigation
- **Component Checklist:** add:
  - `- [ ] Migration — scripts/sql/008_slide_position.sql`
  - `- [ ] Migration — scripts/sql/009_slide_history.sql`
  - `- [ ] Model — backend/src/models/slide_position.py`
  - `- [ ] CRUD — backend/src/crud/crud_slide_position.py`
  - `- [ ] Service — backend/src/service/slide_navigation.py`
  - `- [ ] API — updated backend/src/api/slides.py (current/forward/back)`
  - `- [ ] Schema — updated backend/src/schemas/slides.py`
  - `- [ ] Tests — backend/tests/test_slide_navigation.py`
  - `- [ ] Tests — backend/tests/test_crud_slide_position.py`
  - `- [ ] Hook — updated frontend/src/hooks/useSlide.js`
  - `- [ ] Page — updated frontend/src/pages/SlidePage.jsx`
  - `- [ ] API methods — updated frontend/src/services/api.js`

#### API Documentation (`docs/api_doc/`)

No `docs/api_doc/` directory currently exists in this project. No changes needed.

### Chrome Claude Extension Execution

`docs/technical/testing_context.md` must be created first (it does not exist). Once created, run:

```
/webapp-dev:chrome-test-generate slide_navigation
```

to generate `docs/chrome_test/260416_{hhmm}_slide_navigation.md`. Then execute via:

```
/webapp-dev:chrome-test-execute docs/chrome_test/260416_{hhmm}_slide_navigation.md
```

`feature-implement-full` will invoke this automatically as part of its post-implementation flow.

---

## Dependencies

- `slide_selector.py` — `SlideSelector.get_next_slide` is called internally by `slide_navigation.py`
- `learning_progress_service.py` — `mark_chapter_learnt` is called by `go_next` when `mark_chapter_id` is provided
- `revision_service.py` — `on_chapter_learnt` is called by `go_next`
- `users` table — `slide_position.username` and `slide_history.username` FK to `users`

## Open Questions

None — the implementation follows the delta/coach reference exactly.
