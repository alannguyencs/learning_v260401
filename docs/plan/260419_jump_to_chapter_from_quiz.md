# Jump to Chapter from Quiz

**Feature**: On every quiz slide, render a "View chapter: {chapter_title}" link under the breadcrumb. Clicking it inserts the quiz's parent chapter as the new current slide (via `POST /api/slides/jump-to-chapter`) while pushing the quiz position + its feedback onto the back-history stack. The up arrow from the inserted chapter restores the original quiz with its feedback panel intact.
**Plan Created:** 2026-04-19
**Status:** Plan
**Reference**:
- [Abstract — Slide Stack](../abstract/slide_stack.md)
- [Technical — Slide Stack](../technical/slide_stack.md)
- [Technical — Testing Context](../technical/testing_context.md)

---

## Problem Statement

1. When a user answers a revision quiz and realises they don't remember the underlying material, they have no in-slide way to review the source chapter. They must leave the slide stream, find the chapter through some other navigation (there is none today), and then get back to the quiz.
2. Even if the chapter could be reached, there is no machinery to **come back to the quiz** at its post-answer state. Back/forward navigation today only replays slides the user has already visited through the natural Tier 1/Tier 2 stream.
3. The `ChapterSlide.jsx` component unconditionally renders "Mark as Learnt" — safe today because Tier 2 selection only surfaces unlearnt chapters — but the moment we allow a **learnt** chapter to appear on the slide page, that button becomes a footgun (it would either create a duplicate learnt row or trigger `on_chapter_learnt` a second time and duplicate quiz distribution).

---

## Proposed Solution

Add a dedicated navigation action "jump to this quiz's parent chapter" that reuses the existing back-history machinery:

1. **New endpoint `POST /api/slides/jump-to-chapter { chapter_id }`** —
   - Validates the chapter exists (404 otherwise).
   - Calls `clear_forward` — the jump is a user-initiated "new action", same as marking a chapter learnt.
   - Calls `save_position("chapter", chapter_id, ...)` — which **already** pushes the current position (the quiz) plus its `feedback_json` onto the back-history stack.
   - Returns a `SlideResult` for the chapter.

2. **`ChapterSlide` payload gains `is_learnt: bool`** — driven by `crud_learning_progress.is_chapter_learnt(db, username, chapter_id)`. Any chapter fetched from the jump path has `is_learnt=true`; Tier-2 chapters stay `is_learnt=false`. The frontend hides "Mark as Learnt" when `chapter.is_learnt === true`.

3. **`QuizSlide` payload gains `chapter_title: str`** — so the link can render the actual title without an extra round-trip.

4. **Frontend link** — `frontend/src/components/QuizSlide.jsx` adds a small text link under the existing `Revision Rn · Lesson · Book` breadcrumb. Clicking it calls a new `useSlide.jumpToChapter(chapterId)` which POSTs the endpoint and swaps local state via the existing `_applySlideData` helper. Back arrow (`goPrevious`) already restores feedback via `feedback_json`.

```
[Quiz slide]                                   [Chapter slide — inserted]
 Revision R0 · Lesson · Book                    Book · Lesson · Chapter 1
 View chapter: {chapter_title}      ←[clicked]
 {question}                                     {markdown body}
 {feedback panel after submit}                  (Mark as Learnt HIDDEN)

 ↓ clicking the link →
  POST /api/slides/jump-to-chapter { chapter_id }
    ├── clear_forward(user)
    └── save_position("chapter", chapter_id, ...)
          └── pushes (quiz, feedback_json) to back-history
  SlideResult { slide_type="chapter", chapter: { …, is_learnt: true } }

 ↑ clicking ArrowUp on the inserted chapter →
  POST /api/slides/back  (existing)
    └── go_back — pops back-history, restores feedback_json
  SlideResult { slide_type="quiz", quiz, feedback: … }
```

### Key design decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Link placement | Directly below the breadcrumb, both pre-answer and feedback states | User confirmed — always-visible placement; avoids hiding the affordance behind submit |
| Link label | "View chapter: {chapter_title}" | User confirmed — actual title gives context; requires one extra field in QuizSlide |
| Backend shape | Dedicated `POST /api/slides/jump-to-chapter` | User confirmed — avoids overloading `/forward`; validation + forward-stack clearing are explicit |
| Forward-stack behavior on jump | Clear | Consistent with `mark_chapter_id` path in `go_next` — a jump is "new action" semantics |
| Mark-as-Learnt on inserted chapter | Hidden via `is_learnt` flag | User confirmed — prevents duplicate learnt-writes; clean UX since the chapter IS already learnt |
| Down-arrow from inserted chapter | Computes a fresh next slide (forward stack empty) | Avoids the confusing round-trip "down also returns to the quiz"; user's intent after viewing the chapter is to continue |
| Feedback preservation | Reuses existing `feedback_json` in `UserSlidePosition` + `SlideHistory` | Zero new state — `save_position` already pushes `feedback_json`; `go_back` already restores it |
| Validation: must the chapter_id match quiz.chapter_id? | No | The frontend always sends the quiz's own chapter_id; server-side `chapter_id` match is unnecessary ceremony and would only reject off-by-one bugs in callers the team owns |

---

## Current Implementation Analysis

### What Exists (keep as-is)

| Component | File | Status |
|-----------|------|--------|
| `UserSlidePosition` + `SlideHistory` schema | `scripts/sql/008_slide_position.sql`, `009_slide_history.sql` | Keep — no schema change |
| `save_position` (auto-pushes old position + feedback to back-history) | `backend/src/crud/crud_slide_position.py` | Keep — reused verbatim |
| `clear_forward` | `backend/src/crud/crud_slide_position.py` | Keep — called at the start of every jump |
| `go_back` / `go_previous` (restores feedback_json) | `backend/src/crud/crud_slide_position.py`, `backend/src/service/slide_navigation.py` | Keep — back from the inserted chapter falls through unchanged |
| `SlideSelector.get_next_slide` | `backend/src/service/slide_selector.py` | Keep — still produces the fresh next slide when ArrowDown fires |
| `crud_learning_progress.is_chapter_learnt` | `backend/src/crud/crud_learning_progress.py` | Keep — reused to populate `is_learnt` on chapter payloads |
| `useSlide._applySlideData` / `goPrevious` / `feedback` state | `frontend/src/hooks/useSlide.js` | Keep — back navigation already rehydrates feedback |
| `ChapterSlide` layout | `frontend/src/components/ChapterSlide.jsx` | Keep except for conditional Mark-as-Learnt render |

### What Changes

| Component | Current | Proposed |
|-----------|---------|----------|
| `QuizSlide` payload (`_build_quiz_dict`) | No `chapter_title` | Adds `chapter_title: str` |
| `ChapterSlide` payload (`_build_chapter_dict`) | No `is_learnt` | Adds `is_learnt: bool` from `crud_learning_progress.is_chapter_learnt` |
| `schemas.slides.QuizSlide` | Missing `chapter_title` | Adds `chapter_title: Optional[str]` |
| `schemas.slides.ChapterSlide` | Missing `is_learnt` | Adds `is_learnt: bool = False` |
| Slide API surface | 13 endpoints | 14 endpoints (+ `POST /jump-to-chapter`) |
| `slide_navigation` | `go_next` / `go_back` / `get_current_slide` | Adds `jump_to_chapter` function |
| `QuizSlide.jsx` | No jump link | Renders `data-testid="view-chapter-link"` under breadcrumb |
| `ChapterSlide.jsx` | Always renders "Mark as Learnt" | Hides the button when `chapter.is_learnt === true` |
| `useSlide` hook | No jump method | Exposes `jumpToChapter(chapterId)` |
| `api.js` | No jump method | Exposes `jumpToChapter(chapterId)` |
| `SlidePage.jsx` | QuizSlide gets `{ quiz, feedback, submitting, onSubmit }` | Also passes `onJumpToChapter` |

---

## Implementation Plan

### Key Workflow

#### To Delete
None.

#### To Update
- `frontend/src/components/ChapterSlide.jsx` — wrap the `<Mark as Learnt>` button in `{!chapter.is_learnt && …}`.
- `frontend/src/components/QuizSlide.jsx` — render a small link under the breadcrumb block when `quiz.chapter_title` is set. Click calls `onJumpToChapter(quiz.chapter_id)`.
- `frontend/src/pages/SlidePage.jsx` — wire `useSlide.jumpToChapter` into the `QuizSlide` `onJumpToChapter` prop.

#### To Add New

- **Jump flow** (new):

```
[User] on quiz slide (pre-answer or post-feedback)
  │
  ▼
Clicks "View chapter: {chapter_title}" link
  │
  ▼
useSlide.jumpToChapter(chapter_id)
  │  apiService.jumpToChapter(chapter_id)
  ▼
POST /api/slides/jump-to-chapter { chapter_id }
  │
  ├── get_chapter(db, chapter_id) → 404 if None
  ├── slide_navigation.jump_to_chapter(db, username, chapter_id)
  │     ├── clear_forward(db, username)
  │     ├── save_position(db, username, "chapter", chapter_id, None, None)
  │     │     └── pushes old quiz + feedback_json to back-history
  │     └── rebuild SlideResult for the chapter with is_learnt=True
  │
  └── returns SlideResult → _applySlideData in the hook
```

- **Back navigation** (unchanged, no new code): `go_previous` pops the quiz off back-history, including its `feedback_json`, and `useSlide._applySlideData` rehydrates `feedback` for the UI.

---

### Database Schema

#### To Delete
None.

#### To Update
None.

#### To Add New
None — this feature is pure code; no new tables, columns, or indexes.

---

### CRUD

#### To Delete
None.

#### To Update

- `backend/src/service/slide_selector.py::_build_chapter_dict` — add `"is_learnt": crud_learning_progress.is_chapter_learnt(db, username, chapter.id)` to the returned dict. This function is called from both the selector and `slide_navigation._rebuild_slide`, so a single change covers all paths. The function signature changes to accept `username: str` (currently it may only take `db, chapter`). Update all call sites accordingly.

- `backend/src/service/slide_selector.py::_build_quiz_dict` — add `"chapter_title": chapter.title` (fetched via `get_chapter(db, quiz.chapter_id)`). One extra query per quiz render, negligible.

#### To Add New

None at CRUD layer — all changes are in the service helpers above.

---

### Services

#### To Delete
None.

#### To Update

- `backend/src/service/slide_navigation.py::_rebuild_slide` — propagate `username` through so `_build_chapter_dict` can consult `is_chapter_learnt`. Current signature: `_rebuild_slide(db, slide_type, slide_id, lesson_id, round_num)`. Proposed: add `username` argument. Update all call sites in `get_current_slide`, `go_next`, `go_previous`.

#### To Add New

- `backend/src/service/slide_navigation.py::jump_to_chapter` (new):

```python
def jump_to_chapter(db: Session, username: str, chapter_id: int) -> SlideResult:
    """Insert a chapter as the new current slide; push the prior quiz+feedback to back-history."""
    chapter = get_chapter(db, chapter_id)
    if chapter is None:
        raise ValueError("Chapter not found")  # API layer converts to 404

    # Clear any forward-stack entries — this is a new user-initiated action.
    clear_forward(db, username)

    # save_position auto-pushes the old position (the quiz + its feedback_json) to back-history.
    save_position(db, username, "chapter", chapter_id, None, None)

    rebuilt = _rebuild_slide(db, username, "chapter", chapter_id, None, None)
    if rebuilt is None:
        return SlideResult(slide_type="none", chapter=None, quiz=None, has_previous=False)
    rebuilt.has_previous = get_history_depth(db, username) > 0
    rebuilt.feedback = None
    return rebuilt
```

---

### API Endpoints

#### To Delete
None.

#### To Update
None.

#### To Add New

New endpoint in `backend/src/api/slides.py`:

| Method | Path | Auth | Handler | Response |
|--------|------|------|---------|----------|
| POST | `/api/slides/jump-to-chapter` | Session | `jump_to_chapter` | `SlideResponse` |

```python
class JumpToChapterRequest(BaseModel):
    chapter_id: int


@router.post("/slides/jump-to-chapter", response_model=SlideResponse)
def jump_to_chapter_endpoint(
    body: JumpToChapterRequest,
    user=Depends(require_session_user),
    db: Session = Depends(get_db),
):
    """Insert a chapter as the next slide; push current quiz + feedback to back-history."""
    try:
        result = slide_navigation.jump_to_chapter(db, user.username, body.chapter_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return SlideResponse(
        slide_type=result.slide_type,
        chapter=result.chapter,
        quiz=result.quiz,
        has_previous=result.has_previous,
        feedback=result.feedback,
    )
```

New Pydantic schema in `backend/src/schemas/slides.py`:

```python
class JumpToChapterRequest(BaseModel):
    """Request body for POST /api/slides/jump-to-chapter."""
    chapter_id: int
```

Also extend existing schemas:

```python
class ChapterSlide(BaseModel):
    # existing fields …
    is_learnt: bool = False


class QuizSlide(BaseModel):
    # existing fields …
    chapter_title: Optional[str] = None
```

JSON examples:

```
POST /api/slides/jump-to-chapter {"chapter_id": 16}    → 200 SlideResponse (slide_type="chapter", chapter.is_learnt=true, has_previous=true)
POST /api/slides/jump-to-chapter {"chapter_id": 999999} → 404 {"detail": "Chapter not found"}
POST /api/slides/jump-to-chapter {}                     → 422 (FastAPI validation — chapter_id required)
POST (no session)                                       → 401 {"detail": "Not authenticated"}
```

---

### Testing

#### To Delete
None.

#### To Update

- `backend/tests/test_slides_api.py` — existing `SlideResponse`-shape assertions in `TestGetCurrentSlide` and `TestMarkChapterLearnt` need to tolerate the new `is_learnt` / `chapter_title` fields (defaults keep them optional, so likely no change, but verify).

#### To Add New

**Backend tests**

- `backend/tests/test_slide_navigation.py` *(new or extend if it exists)*
  - `jump_to_chapter` with a fresh user (no prior position) writes the position and returns chapter with `is_learnt=true` / `is_learnt=false` depending on progress.
  - `jump_to_chapter` with a prior quiz position pushes that quiz + `feedback_json` onto back-history.
  - `jump_to_chapter` clears any existing forward-stack entries.
  - `jump_to_chapter` on unknown `chapter_id` raises `ValueError`.
  - After `jump_to_chapter`, `go_previous` returns the original quiz with its feedback.
  - After `jump_to_chapter`, `go_next` does NOT return the original quiz (forward stack empty → selector fresh pick).

- `backend/tests/test_slides_api.py` *(extend)*
  - `POST /jump-to-chapter` happy-path: returns `SlideResponse` with `slide_type=="chapter"`, `chapter.is_learnt==true`, `has_previous==true`.
  - `POST /jump-to-chapter` on unknown chapter returns 404.
  - `POST /jump-to-chapter` without session returns 401.
  - `POST /jump-to-chapter` with missing body returns 422.
  - After a jump, `POST /back` returns the original quiz with its feedback object populated.

- `backend/tests/test_slide_selector.py` *(extend)*
  - `_build_quiz_dict` includes `chapter_title`.
  - `_build_chapter_dict` includes `is_learnt` matching `crud_learning_progress.is_chapter_learnt`.

**Frontend tests**

- `frontend/src/__tests__/components/QuizSlide.test.js` *(extend)*
  - Renders `view-chapter-link` when `quiz.chapter_title` is set.
  - Clicking it calls `onJumpToChapter` with `quiz.chapter_id`.
  - Link is present in both pre-answer and feedback states.

- `frontend/src/__tests__/components/ChapterSlide.test.js` *(extend)*
  - Renders "Mark as Learnt" when `chapter.is_learnt === false`.
  - Hides "Mark as Learnt" when `chapter.is_learnt === true`.

- `frontend/src/__tests__/hooks/useSlide.test.js` *(extend)*
  - `jumpToChapter(id)` calls `apiService.jumpToChapter(id)` and applies the returned slide + resets feedback.

**Pre-commit loop**

1. Run `source venv/bin/activate && pre-commit run --all-files`.
2. Fix any issues (lint errors, line count violations, Prettier diff).
3. Re-run — Prettier may reformat and push files over the 300-line frontend limit. If so, fix durably (extract components).
4. Repeat until pre-commit passes cleanly on a full re-run.

---

### Frontend

#### To Delete
None.

#### To Update

- `frontend/src/services/api.js` — add:

```js
jumpToChapter: async (chapterId) => {
  const response = await api.post("/api/slides/jump-to-chapter", {
    chapter_id: chapterId,
  });
  return response.data;
},
```

- `frontend/src/hooks/useSlide.js` — add a `jumpToChapter` method that mirrors `goPrevious`/`fetchNextSlide`:

```js
const jumpToChapter = async (chapterId) => {
  setLoading(true);
  setError(null);
  try {
    const data = await apiService.jumpToChapter(chapterId);
    _applySlideData(data);
  } catch {
    setError("Failed to open chapter.");
  } finally {
    setLoading(false);
  }
};
```

Return it from the hook alongside `goPrevious` / `fetchNextSlide`.

- `frontend/src/components/QuizSlide.jsx` — accept a new `onJumpToChapter` prop and render:

```jsx
<div className="text-sm text-gray-400 mb-2">
  Revision R{quiz.round_num} · {quiz.lesson_title} · {quiz.book_title}
</div>
{quiz.chapter_id && quiz.chapter_title && (
  <button
    type="button"
    onClick={() => onJumpToChapter(quiz.chapter_id)}
    data-testid="view-chapter-link"
    className="text-sm text-blue-400 hover:text-blue-300 underline
               underline-offset-2 mb-4 inline-block text-left"
  >
    View chapter: {quiz.chapter_title}
  </button>
)}
```

Styled so tap-target height is ≥ 44 px on mobile (padded via vertical spacing on parent, or `py-2` on the button itself — finalise during implementation).

- `frontend/src/components/ChapterSlide.jsx` — conditional button:

```jsx
{!chapter.is_learnt && (
  <div className="flex gap-3 justify-end">
    <button
      onClick={onMarkLearnt}
      data-testid="mark-learnt-button"
      className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
    >
      Mark as Learnt
    </button>
  </div>
)}
```

- `frontend/src/pages/SlidePage.jsx` — wire the new handler:

```jsx
const { …, jumpToChapter } = useSlide();

// inside QuizSlide render
<QuizSlide
  quiz={slide.quiz}
  feedback={feedback}
  submitting={submitting}
  onSubmit={…}
  onJumpToChapter={jumpToChapter}
/>
```

#### To Add New

None new beyond the methods/props above — no new components or hooks.

---

### Documentation

#### Abstract (`docs/abstract/`)

**Update** `docs/abstract/slide_stack.md`:

- **Solution** paragraph — append: "On any quiz slide the user can jump to the quiz's parent chapter via a 'View chapter' link. The chapter is inserted as the next slide with the quiz pushed to back-history, so the up arrow returns to the quiz with its feedback preserved."
- **User Flow** — under the Quiz slide bullet, add:

  ```
  ├── View chapter link (on every quiz slide, pre-answer and feedback states):
  │     [View chapter: {chapter_title}] → POST /api/slides/jump-to-chapter
  │                                     → parent chapter becomes current slide
  │                                     → quiz is pushed to back-history with feedback
  │     ArrowUp from the inserted chapter → restores the original quiz with feedback
  │     ArrowDown from the inserted chapter → fresh next slide (forward stack was cleared)
  │     "Mark as Learnt" button is HIDDEN on chapters whose is_learnt is true
  ```
- **Scope — Included** — add: "Jump-to-chapter link on every quiz slide; back arrow restores the quiz with its feedback; Mark-as-Learnt is hidden on already-learnt chapters."
- **Acceptance Criteria** — add:
  - `- [ ] Quiz slides render a "View chapter: {chapter_title}" link immediately under the breadcrumb, visible in both pre-answer and feedback states.`
  - `- [ ] Clicking the link inserts the parent chapter as the current slide; quiz position + feedback are pushed to back-history.`
  - `- [ ] From the inserted chapter, clicking the up arrow restores the original quiz with its feedback panel.`
  - `- [ ] From the inserted chapter, clicking the down arrow advances to a fresh next slide (not the original quiz).`
  - `- [ ] "Mark as Learnt" is hidden on any chapter slide where chapter.is_learnt is true.`

#### Technical (`docs/technical/`)

**Update** `docs/technical/slide_stack.md`:

- **Architecture** — append to the API block:

  ```
  POST /api/slides/jump-to-chapter
                                  → slide_navigation.jump_to_chapter
                                  → clear_forward + save_position (pushes quiz + feedback to back-history)
  ```

- **API Layer** — add a row:

  | Method | Path | Auth | Handler |
  |--------|------|------|---------|
  | POST | `/api/slides/jump-to-chapter` | Session | `jump_to_chapter_endpoint` — body `{ chapter_id }` |

- **Schemas** (`backend/src/schemas/slides.py`) — note additions:
  - `QuizSlide.chapter_title: Optional[str]` (new).
  - `ChapterSlide.is_learnt: bool` (new, default False).
  - `JumpToChapterRequest` (new).

- **Service Layer → slide_navigation** — add a row:

  | Method | Description |
  |--------|-------------|
  | `jump_to_chapter(db, username, chapter_id)` | Clears forward; saves chapter as current (pushes quiz+feedback to back-history); returns SlideResult with `has_previous=True` |

- **Frontend — Components** — update:
  - `QuizSlide` row: "… renders a 'View chapter: {chapter_title}' link under the breadcrumb; clicking calls `onJumpToChapter(chapter_id)` …"
  - `ChapterSlide` row: "… hides 'Mark as Learnt' when `chapter.is_learnt === true` …"

- **Frontend — Services & Hooks** — add:
  - `useSlide.jumpToChapter(chapterId)` — POSTs the new endpoint and rehydrates slide state.
  - `apiService.jumpToChapter(chapterId)` — client for the new endpoint.

- **Component Checklist** — append (all unchecked initially):
  - `- [ ] API — backend/src/api/slides.py (POST /jump-to-chapter)`
  - `- [ ] Schemas — backend/src/schemas/slides.py (JumpToChapterRequest; QuizSlide.chapter_title; ChapterSlide.is_learnt)`
  - `- [ ] Service — backend/src/service/slide_navigation.py (jump_to_chapter)`
  - `- [ ] Service update — backend/src/service/slide_selector.py (_build_quiz_dict adds chapter_title; _build_chapter_dict adds is_learnt; accepts username)`
  - `- [ ] Tests — backend/tests/test_slide_navigation.py (jump_to_chapter unit cases)`
  - `- [ ] Tests — backend/tests/test_slides_api.py (jump-to-chapter API)`
  - `- [ ] Tests — backend/tests/test_slide_selector.py (is_learnt / chapter_title dict fields)`
  - `- [ ] API client — frontend/src/services/api.js (jumpToChapter)`
  - `- [ ] Hook — frontend/src/hooks/useSlide.js (jumpToChapter)`
  - `- [ ] Component — frontend/src/components/QuizSlide.jsx (view-chapter link)`
  - `- [ ] Component — frontend/src/components/ChapterSlide.jsx (conditional Mark-as-Learnt)`
  - `- [ ] Page — frontend/src/pages/SlidePage.jsx (wire onJumpToChapter)`
  - `- [ ] Tests — frontend/src/__tests__/components/QuizSlide.test.js (link rendering)`
  - `- [ ] Tests — frontend/src/__tests__/components/ChapterSlide.test.js (is_learnt hides button)`
  - `- [ ] Tests — frontend/src/__tests__/hooks/useSlide.test.js (jumpToChapter)`

#### API Documentation (`docs/api_doc/`)

No changes needed — the project has no `docs/api_doc/` directory. API endpoint reference lives inside `docs/technical/slide_stack.md`, which is updated above.

---

### Chrome Claude Extension Execution

After implementation is complete, execute the Chrome Claude Extension E2E tests defined in `docs/chrome_test/260419_1352_jump_to_chapter_from_quiz.md` by invoking the `chrome-test-execute` skill.

`feature-implement-full` invokes it automatically as part of its post-implementation flow; if the plan is executed manually, run `/webapp-dev:chrome-test-execute docs/chrome_test/260419_1352_jump_to_chapter_from_quiz.md` yourself. Full execution rules live in that skill's `references/execution-rules.md`.

Test coverage at a glance (10 tests, both viewports):

| # | Viewport | Test |
|---|----------|------|
| 1 | 1440×900 | Happy-path: answer quiz → click link → chapter inserted + Mark-as-Learnt hidden → up-arrow restores quiz with feedback |
| 2 | 1440×900 | Link visibility: present on quiz (pre-answer + feedback), absent on chapter and All-Caught-Up |
| 3 | 1440×900 | Forward semantics: down-arrow from inserted chapter → fresh next slide (not the same quiz) |
| 4 | 1440×900 | Validation: 404 on unknown chapter_id; 422 on missing body; current slide unchanged after failures |
| 5 | 1440×900 | Auth guard: POST /jump-to-chapter returns 401 without session; /slides redirects to /login |
| 6 | 375×812  | Mobile happy-path with overflow/tap-target/scroll-reachability assertions |
| 7 | 375×812  | Mobile link visibility |
| 8 | 375×812  | Mobile forward semantics |
| 9 | 375×812  | Mobile validation + synthetic-500 rollback |
| 10| 375×812  | Mobile permission guard |

---

## Dependencies

- `chapters` table (migration `001_content_schema.sql`) — FK target for chapter lookup and `is_chapter_learnt`.
- `UserSlidePosition` + `SlideHistory` (migrations `008`/`009`) — back/forward stack machinery reused verbatim.
- `crud_slide_position.save_position` — the workhorse that pushes old position + `feedback_json` onto back-history.
- `crud_learning_progress.is_chapter_learnt` — drives the new `chapter.is_learnt` flag.
- `SlideSelector._build_quiz_dict` / `_build_chapter_dict` — extended with two new fields.

## Open Questions

1. **Should the link also show the chapter number (e.g. "Chapter 1: {title}")?** Current plan: title alone. Easy to extend later if the chapter context feels ambiguous.
2. **Should we also clear the chat panel state on jump?** The chat is keyed by `slide_identifier` so the inserted chapter shows its own chat history, not the quiz's. Likely fine; flag if users conflate the two panels.
3. **Should the "View chapter" link be visible during the submit-in-flight state (`submitting=true`)?** Current plan: yes (same visibility as breadcrumb). A disabled state during submit would reduce accidental jumps, but complicates the markup for minimal benefit.
4. **Should `jump_to_chapter` be blocked if `chapter_id` is not the quiz's parent chapter?** Current plan: no server-side guard. Reconsider if we start letting users jump from one quiz to a different lesson's chapter.
