# Liked Slide Frequency Boost

**Feature**: Add a Like (thumbs-up) button on quiz slides; liking a quiz inflates its `forgetting_rate` so the quiz surfaces sooner in the Tier‑1 weakest‑recall‑first ordering (Option A).
**Plan Created:** 2026-04-18
**Status:** Plan
**Reference**:
- [Discussion — Liked Slide Frequency Boost](../discussion/260417_liked_slide_frequency_boost.md)
- [Abstract — Slide Stack](../abstract/slide_stack.md)
- [Technical — Slide Stack](../technical/slide_stack.md)
- [Technical — Revision Scheduling](../technical/revision_scheduling.md)
- [Testing Context](../technical/testing_context.md)

---

## Problem Statement

1. The slide-selection algorithm has no way for the user to signal "I want to see this quiz more often." All ordering within Tier 1 is driven purely by the spaced-repetition recall score `m(t)`.
2. A user who identifies a quiz as strategically important (or subjectively interesting) must wait for the natural review cadence to surface it again, even though they would benefit from seeing it sooner.
3. There is no per-quiz user-preference storage at all. No lightweight UI affordance (heart/star/bookmark) exists to capture this preference.

---

## Proposed Solution

**Option A — Like as a Forgetting-Rate Boost.**

Liking a quiz inserts a row into a new `user_slide_like` table and simultaneously bumps the quiz's `forgetting_rate` in `user_quiz_recall` to `max(current_rate, 1.0)`. The existing recall formula `m(t) = exp(-forgetting_rate * elapsed_lessons / 10)` then produces a lower (weaker) recall value for the liked quiz, so it ranks earlier in the Tier-1 weakest-recall-first sort. No new tier, no new sort multiplier — the boost lives entirely inside the existing `user_quiz_recall` table.

```
Like quiz 42 → INSERT INTO user_slide_like (alan, 42)
              → UPDATE user_quiz_recall SET forgetting_rate = MAX(rate, 1.0)
                       WHERE (alan, 42)

Next sort of Group A:
  m(t) = exp(-forgetting_rate * elapsed / 10)
       = exp(-1.0 * elapsed / 10)   ← lower (weaker) than if rate had decayed below 1.0
  → quiz 42 surfaces earlier

Answering correctly later: forgetting_rate *= 0.7 → boost naturally decays away.
```

Unlike is a pure toggle for the visual state: `DELETE` removes the row but does **not** restore any prior `forgetting_rate`. This matches Option A's "natural review cycles reduce the boost" semantics and avoids storing a pre-like snapshot.

### Key design decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Boost rule | `forgetting_rate = max(current, 1.0)` | Matches the discussion doc verbatim; resets to "never reviewed" level; safe no-op for fresh quizzes |
| Like persistence | New `user_slide_like` table | Needed to render the filled/outline heart deterministically across refresh |
| Unlike effect on rate | None | Simpler; avoids a snapshot column and reconciliation bugs |
| Scope | Quizzes only (not chapters) | Chapters have no recall row; liking a chapter would be a "bookmark" — a separate feature |
| Like count shown | No | Personal preference, not social |

---

## Current Implementation Analysis

### What Exists (keep as-is)

| Component | File | Status |
|-----------|------|--------|
| `SlideSelector.get_next_slide` (2-tier algorithm) | `backend/src/service/slide_selector.py` | Keep — boost works within existing sort, no algorithm branch needed |
| `RevisionService.compute_recall` (`m(t)` formula) | `backend/src/service/revision_service.py` | Keep — unchanged |
| `RevisionService.record_quiz_response` (0.7× / 1.2× decay) | `backend/src/service/revision_service.py` | Keep — liked rates naturally decay on correct answers |
| `user_quiz_recall` table | `scripts/sql/003_revision_scheduling.sql` | Keep — the `forgetting_rate` column is the boost target |
| `crud_revision.get_quiz_recall` / `upsert_quiz_recall` | `backend/src/crud/crud_revision.py` | Keep — reused by the like endpoint |
| `ChatButton` positioning pattern | `frontend/src/components/ChatButton.jsx` | Keep — the heart button clones its FAB positioning convention |
| `useSlide` hook API shape | `frontend/src/hooks/useSlide.js` | Keep — like state lives in a new hook, not here |

### What Changes

| Component | Current | Proposed |
|-----------|---------|----------|
| `user_quiz_recall.forgetting_rate` (for liked quizzes) | Only updated by `record_quiz_response` | Also updated by `RevisionService.apply_like_boost` at like time |
| Quiz slide layout | One FAB (chat) fixed at `bottom-24 left-[calc(50%+240px)]` | Two stacked FABs: heart at `bottom-40`, chat at `bottom-24` (same `left` anchor) |
| Slide API surface | 7 endpoints | 10 endpoints (+ `POST /like`, `DELETE /like`, `GET /likes`) |
| `SlidePage` | Renders `ChatButton` when `slide_type !== "none"` | Also renders `LikeButton` when `slide_type === "quiz"` |
| `useSlide` / client state | No knowledge of likes | A sibling `useLikedQuizzes` hook exposes the liked set; `LikeButton` reads/writes through it |

---

## Implementation Plan

### Key Workflow

#### To Delete
None.

#### To Update
- `frontend/src/pages/SlidePage.jsx` — add `<LikeButton />` sibling to `<ChatButton />`, rendered only when `slide.slide_type === "quiz"` (chapters never get a heart per the scope decision).

#### To Add New
- **Like flow** (new):

```
[User] viewing quiz slide
  │
  ▼
[LikeButton] reads liked_ids from useLikedQuizzes
  │   isLiked = liked_ids.has(quiz.id)
  │   render: filled heart (isLiked) | outline heart (!isLiked)
  │
  ▼
[User] clicks heart
  │
  ├── !isLiked → POST /api/slides/quizzes/{id}/like
  │              → crud_slide_like.add_like(db, username, quiz_id) (idempotent)
  │              → RevisionService.apply_like_boost(db, username, quiz_id)
  │                   → upsert_quiz_recall with forgetting_rate = max(current, 1.0)
  │              → frontend optimistically adds quiz_id to liked set
  │
  └── isLiked  → DELETE /api/slides/quizzes/{id}/like
                 → crud_slide_like.remove_like(db, username, quiz_id) (idempotent)
                 → frontend optimistically removes quiz_id from liked set
```

- **Boost effect on next sort** (inside existing Tier-1 loop, no code change required):

```
SlideSelector.get_next_slide
  │
  ▼
For each due round:
  For each non-skipped quiz:
    recall = get_quiz_recall(db, user, qid)
    m_t    = compute_recall(recall.forgetting_rate, elapsed)
    # If this quiz was recently liked, forgetting_rate was bumped
    # to ≥ 1.0 → m_t is lower → quiz sorts earlier.
```

---

### Database Schema

#### To Delete
None.

#### To Update
None — `user_quiz_recall` schema unchanged; only the value of `forgetting_rate` changes for liked quizzes at write time.

#### To Add New

New migration file: `scripts/sql/010_user_slide_like.sql`

```sql
-- Migration: User Slide Like
-- Persists per-user quiz likes (drives the filled/outline heart UI)
-- DDL only; idempotent

CREATE TABLE IF NOT EXISTS user_slide_like (
    id SERIAL PRIMARY KEY,
    username VARCHAR NOT NULL REFERENCES users(username),
    quiz_id INTEGER NOT NULL REFERENCES chapter_quizzes(id),
    liked_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(username, quiz_id)
);
CREATE INDEX IF NOT EXISTS idx_usl_user ON user_slide_like(username);
```

New ORM model: `backend/src/models/slide_like.py` → `UserSlideLike` mapping to table `user_slide_like`. Columns mirror the migration. Include it in `backend/src/database.py` / `backend/src/models/__init__.py` if they enumerate models.

**Column descriptions**

| Column | Type | Constraint | Purpose |
|--------|------|-----------|---------|
| `id` | Integer | PK | Surrogate key |
| `username` | String | FK → `users.username`, NOT NULL | Who liked the quiz |
| `quiz_id` | Integer | FK → `chapter_quizzes.id`, NOT NULL | Which quiz |
| `liked_at` | Timestamp | NOT NULL, DEFAULT NOW() | When; useful for future analytics |
| — | — | UNIQUE(`username`, `quiz_id`) | Prevents duplicate likes |

Index `idx_usl_user` supports `GET /likes` listing by user.

---

### CRUD

#### To Delete
None.

#### To Update
None — `crud_revision.upsert_quiz_recall` already supports both insert and update and is reused verbatim.

#### To Add New

New file: `backend/src/crud/crud_slide_like.py`

| Function | Signature | Description |
|----------|-----------|-------------|
| `add_like` | `add_like(db: Session, username: str, quiz_id: int) -> None` | `INSERT ... ON CONFLICT (username, quiz_id) DO NOTHING` so repeat clicks are idempotent. Commits. |
| `remove_like` | `remove_like(db: Session, username: str, quiz_id: int) -> None` | `DELETE FROM user_slide_like WHERE username = :u AND quiz_id = :q`. Idempotent (no error if absent). Commits. |
| `is_liked` | `is_liked(db: Session, username: str, quiz_id: int) -> bool` | `SELECT 1 FROM user_slide_like WHERE (u, q) LIMIT 1`. Used by tests / future features. |
| `get_liked_quiz_ids` | `get_liked_quiz_ids(db: Session, username: str) -> list[int]` | `SELECT quiz_id FROM user_slide_like WHERE username = :u ORDER BY liked_at DESC`. Backs `GET /likes`. |

---

### Services

#### To Delete
None.

#### To Update

`backend/src/service/revision_service.py` — add a new `@staticmethod` on `RevisionService`:

```python
@staticmethod
def apply_like_boost(
    db: Session,
    username: str,
    quiz_id: int,
    lesson_count: int,
) -> None:
    """Bump forgetting_rate to max(current, 1.0) for a liked quiz.

    No change to last_reviewed_lesson_count — the boost alone is enough
    to lower m(t) on the next sort, and preserving the review cadence
    avoids double-counting the "like" as a review.
    """
    existing = crud_revision.get_quiz_recall(db, username, quiz_id)
    current_rate = existing.forgetting_rate if existing else 1.0
    new_rate = max(current_rate, 1.0)
    last_reviewed = (
        existing.last_reviewed_lesson_count
        if existing and existing.last_reviewed_lesson_count is not None
        else lesson_count
    )
    crud_revision.upsert_quiz_recall(db, username, quiz_id, new_rate, last_reviewed)
```

Notes:
- For a never-reviewed quiz, `upsert_quiz_recall` will create a row with rate 1.0 and `last_reviewed_lesson_count = lesson_count` (the current position). That is a correct baseline — it means "as weak as a brand-new quiz."
- `upsert_quiz_recall` currently bumps `review_count`. That increment is acceptable (a like counts as an "interaction"); if the user later finds this misleading, a dedicated non-bumping helper can be split out.

#### To Add New
None beyond the method above.

---

### API Endpoints

#### To Delete
None.

#### To Update
None.

#### To Add New

Three new endpoints in `backend/src/api/slides.py`:

| Method | Path | Auth | Handler | Response |
|--------|------|------|---------|----------|
| POST   | `/api/slides/quizzes/{quiz_id}/like` | Session | `like_quiz` | `{"liked": true}` |
| DELETE | `/api/slides/quizzes/{quiz_id}/like` | Session | `unlike_quiz` | `{"liked": false}` |
| GET    | `/api/slides/likes` | Session | `list_likes` | `{"quiz_ids": [int, ...]}` |

Endpoint behaviour:

```python
@router.post("/slides/quizzes/{quiz_id}/like", response_model=LikeResponse)
def like_quiz(quiz_id, user=Depends(require_session_user), db=Depends(get_db)):
    if get_chapter_quiz(db, quiz_id) is None:
        raise HTTPException(404, "Quiz not found")
    crud_slide_like.add_like(db, user.username, quiz_id)
    lesson_count = crud_learning_progress.get_lesson_count(db, user.username)
    RevisionService.apply_like_boost(db, user.username, quiz_id, lesson_count)
    return LikeResponse(liked=True)

@router.delete("/slides/quizzes/{quiz_id}/like", response_model=LikeResponse)
def unlike_quiz(quiz_id, user=Depends(require_session_user), db=Depends(get_db)):
    crud_slide_like.remove_like(db, user.username, quiz_id)
    return LikeResponse(liked=False)

@router.get("/slides/likes", response_model=LikeListResponse)
def list_likes(user=Depends(require_session_user), db=Depends(get_db)):
    ids = crud_slide_like.get_liked_quiz_ids(db, user.username)
    return LikeListResponse(quiz_ids=ids)
```

New Pydantic schemas in `backend/src/schemas/slides.py`:

```python
class LikeResponse(BaseModel):
    liked: bool

class LikeListResponse(BaseModel):
    quiz_ids: List[int]
```

JSON examples:

```
POST /api/slides/quizzes/42/like        → 200 {"liked": true}
POST (same, second call)                 → 200 {"liked": true}     # idempotent
DELETE /api/slides/quizzes/42/like      → 200 {"liked": false}
DELETE (same, second call)               → 200 {"liked": false}    # idempotent
GET /api/slides/likes                    → 200 {"quiz_ids": [42, 17, 9]}
POST /api/slides/quizzes/999999/like    → 404 {"detail": "Quiz not found"}
POST (no session cookie)                 → 401 {"detail": "Not authenticated"}
```

---

### Testing

#### To Delete
None.

#### To Update
None.

#### To Add New

**Backend tests**

- `backend/tests/test_crud_slide_like.py`
  - Unit: `add_like` inserts a row; second call is idempotent (still one row).
  - Unit: `remove_like` deletes the row; second call is a no-op (no exception).
  - Unit: `is_liked` / `get_liked_quiz_ids` return correct values before and after like/unlike.

- `backend/tests/test_revision_service.py` *(extend)*
  - Unit: `apply_like_boost` on a quiz with **no** recall row → creates row with `forgetting_rate = 1.0`.
  - Unit: `apply_like_boost` on a quiz with `forgetting_rate = 0.49` → rate becomes `1.0`.
  - Unit: `apply_like_boost` on a quiz with `forgetting_rate = 1.3` → rate stays `1.3` (idempotent boost).
  - Unit: `apply_like_boost` does not decrement `review_count` and does not change `last_reviewed_lesson_count` when a prior value exists.

- `backend/tests/test_slide_selector.py` *(extend)*
  - Integration: two quizzes in the same due round, one with `forgetting_rate = 0.49` (well-remembered), one with `forgetting_rate = 1.0` (freshly liked). Assert the liked one is returned first by `SlideSelector.get_next_slide`.

- `backend/tests/test_slides_api.py` *(extend)*
  - Integration: `POST /like` returns `{"liked": true}`, inserts a row, and bumps `forgetting_rate` as expected.
  - Integration: `DELETE /like` returns `{"liked": false}` and deletes the row but leaves `forgetting_rate` unchanged.
  - Integration: `GET /likes` returns the current liked quiz IDs in `liked_at DESC` order.
  - Integration: `POST /like` on a non-existent quiz returns 404.
  - Integration: all three endpoints return 401 without a session cookie.

**Frontend tests**

- `frontend/src/__tests__/components/LikeButton.test.js`
  - Renders outline heart when `quizId` is not in `likedIds`.
  - Renders filled heart when `quizId` is in `likedIds`.
  - Clicking an outline heart calls `apiService.likeQuiz(quizId)` and flips to filled (optimistic update).
  - Clicking a filled heart calls `apiService.unlikeQuiz(quizId)` and flips to outline.

- `frontend/src/__tests__/hooks/useLikedQuizzes.test.js`
  - On mount, fetches `GET /api/slides/likes` and stores IDs.
  - `toggleLike(quizId)` calls the correct endpoint based on current state.
  - Rolls back optimistic state on API error.

- `frontend/src/__tests__/pages/SlidePage.test.js` *(extend)*
  - `LikeButton` renders for `slide_type === "quiz"` and does **not** render for `slide_type === "chapter"` or `"none"`.

**Pre-commit loop**

1. Run `source venv/bin/activate && pre-commit run --all-files`.
2. Fix any issues (lint errors, line count violations, Prettier diff).
3. Re-run — Prettier may reformat the fixes and push files over the 300-line frontend limit. If so, fix again (e.g., extract sub-components to separate files).
4. Repeat until pre-commit passes cleanly on a full re-run with no new failures.

---

### Frontend

#### To Delete
None.

#### To Update

- `frontend/src/services/api.js` — add three methods:

```js
likeQuiz: async (quizId) => {
  const response = await api.post(`/api/slides/quizzes/${quizId}/like`);
  return response.data;
},

unlikeQuiz: async (quizId) => {
  const response = await api.delete(`/api/slides/quizzes/${quizId}/like`);
  return response.data;
},

listLikedQuizzes: async () => {
  const response = await api.get("/api/slides/likes");
  return response.data;
},
```

- `frontend/src/pages/SlidePage.jsx` — render `<LikeButton quizId={slide.quiz.id} />` when `slide.slide_type === "quiz"`, alongside the existing `<ChatButton />`.

#### To Add New

- `frontend/src/hooks/useLikedQuizzes.js` — small hook that owns the liked-set state.

  State / methods:
  - `likedIds: Set<number>` — loaded once via `apiService.listLikedQuizzes()` on mount.
  - `isLiked(quizId) -> boolean`.
  - `toggleLike(quizId)` — optimistic: add/remove from the set, then call `likeQuiz` or `unlikeQuiz`. On error, revert.

- `frontend/src/components/LikeButton.jsx` — thumbs-up Like FAB.

  Visual spec:
  - Position: `fixed bottom-40 left-[calc(50%+240px)]` (one FAB-height above `ChatButton`, same horizontal anchor).
  - Size: 40×40 SVG (explicit `width="40" height="40"` attributes on the `<svg>` so sizing is independent of Tailwind JIT class generation).
  - States:
    - Not liked: outline thumbs-up, `text-gray-400 hover:text-blue-400`.
    - Liked: filled thumbs-up, `text-blue-500 hover:text-blue-400`.
  - Accessibility: `aria-label="Like quiz"` when outline; `aria-label="Unlike quiz"` when filled. `aria-pressed` reflects state.
  - Transition: quick color fade (Tailwind `transition-colors duration-150`).

  Props: `{ quizId: number }`. Pulls `likedIds` / `toggleLike` from `useLikedQuizzes`.

  Visual sketch:
  ```
  ┌─────────────────────────────────────────────────────┐
  │ Slide content                                       │
  │                                                     │
  │                                                     │
  │                                               ♥     │ ← LikeButton (bottom-40)
  │                                               💬    │ ← ChatButton (bottom-24)
  │                         [↓]                         │ ← ArrowDown (bottom-[76px])
  └─────────────────────────────────────────────────────┘
  ```

---

### Documentation

#### Abstract (`docs/abstract/`)

**Update** `docs/abstract/slide_stack.md`:
- **Solution** section — add one sentence: "Users can mark quizzes they want to see more often by tapping a heart icon on the quiz slide; liked quizzes resurface sooner in the revision queue."
- **User Flow** — add a branch under the Quiz slide bullet: "Heart icon: toggle like/unlike — liked quizzes appear more frequently in the spaced-repetition ordering."
- **Scope — Included** — add: "Per-quiz like/unlike with a heart icon; liked quizzes are boosted in the ordering."
- **Scope — Not included** — add: "Liking chapters (a future bookmark feature); showing social like counts."
- **Acceptance Criteria** — add:
  - `- [ ] Heart icon is visible on every quiz slide and hidden on chapter slides and the All-Caught-Up state.`
  - `- [ ] Clicking the heart toggles filled/outline and persists across page refresh.`
  - `- [ ] Liking a quiz causes it to appear sooner in subsequent Tier-1 ordering.`

#### Technical (`docs/technical/`)

**Update** `docs/technical/slide_stack.md`:
- **Architecture** — append three routes to the API block:
  ```
  POST   /api/slides/quizzes/{id}/like   → crud_slide_like.add_like
                                          → RevisionService.apply_like_boost
  DELETE /api/slides/quizzes/{id}/like   → crud_slide_like.remove_like
  GET    /api/slides/likes               → crud_slide_like.get_liked_quiz_ids
  ```
- **Data Model** — add a new `**UserSlideLike**` sub-section with columns `id / username / quiz_id / liked_at`, UNIQUE(`username`, `quiz_id`), index `idx_usl_user`.
- **API Layer** — add three rows (POST/DELETE/GET) to the endpoint table.
- **Service Layer** — in the `RevisionService` method table, add one row: `apply_like_boost(db, username, quiz_id, lesson_count)` — "Sets `forgetting_rate = max(current, 1.0)` for a liked quiz; preserves `last_reviewed_lesson_count`."
- **CRUD Layer** — add a new `**crud_slide_like.py**` sub-block listing `add_like / remove_like / is_liked / get_liked_quiz_ids`.
- **Frontend — Components** — add a row: `LikeButton | frontend/src/components/LikeButton.jsx | Heart FAB above ChatButton on quiz slides; toggles via useLikedQuizzes`.
- **Frontend — Services & Hooks** — add a row: `useLikedQuizzes | frontend/src/hooks/useLikedQuizzes.js | Loads liked quiz IDs, exposes isLiked + toggleLike with optimistic updates`.
- **Component Checklist** — append (all unchecked initially):
  - `- [ ] Migration — scripts/sql/010_user_slide_like.sql`
  - `- [ ] Model — backend/src/models/slide_like.py (UserSlideLike)`
  - `- [ ] CRUD — backend/src/crud/crud_slide_like.py`
  - `- [ ] Service — backend/src/service/revision_service.py (apply_like_boost)`
  - `- [ ] API — backend/src/api/slides.py (POST/DELETE /like, GET /likes)`
  - `- [ ] Schemas — backend/src/schemas/slides.py (LikeResponse, LikeListResponse)`
  - `- [ ] Tests — backend/tests/test_crud_slide_like.py`
  - `- [ ] Tests — backend/tests/test_revision_service.py (apply_like_boost)`
  - `- [ ] Tests — backend/tests/test_slide_selector.py (liked quiz surfaces first)`
  - `- [ ] Tests — backend/tests/test_slides_api.py (like endpoints)`
  - `- [ ] Hook — frontend/src/hooks/useLikedQuizzes.js`
  - `- [ ] Component — frontend/src/components/LikeButton.jsx`
  - `- [ ] Page update — frontend/src/pages/SlidePage.jsx (LikeButton on quiz slides)`
  - `- [ ] API methods — frontend/src/services/api.js (likeQuiz / unlikeQuiz / listLikedQuizzes)`
  - `- [ ] Tests — frontend/src/__tests__/components/LikeButton.test.js`
  - `- [ ] Tests — frontend/src/__tests__/hooks/useLikedQuizzes.test.js`

**Update** `docs/technical/revision_scheduling.md`:
- **Algorithms** — add a new `### Like Boost` sub-heading:
  - On like: `forgetting_rate = max(current_rate, 1.0)` for `(username, quiz_id)`.
  - `last_reviewed_lesson_count` unchanged if set; otherwise initialised to current `lesson_count`.
  - Unlike does not restore the prior rate.
- **Service Layer → RevisionService** — add a row for `apply_like_boost(db, username, quiz_id, lesson_count)`.

#### API Documentation (`docs/api_doc/`)

No changes needed — the project has no `docs/api_doc/` directory (verified in Step 1). API endpoint reference lives inside `docs/technical/slide_stack.md`, which is updated above.

---

### Chrome Claude Extension Execution

After implementation is complete, execute the Chrome Claude Extension E2E tests defined in `docs/chrome_test/260418_1421_liked_slide_frequency_boost.md` by invoking the `chrome-test-execute` skill.

`feature-implement-full` invokes it automatically as part of its post-implementation flow; if the plan is executed manually, run `/webapp-dev:chrome-test-execute docs/chrome_test/260418_1421_liked_slide_frequency_boost.md` yourself. Full execution rules live in that skill's `references/execution-rules.md`.

Test coverage at a glance (10 tests, both viewports):

| # | Viewport | Test |
|---|----------|------|
| 1 | 1440×900 | Happy-path like → refresh → persisted → unlike; DB row in/out; rate = max(prev, 1.0) |
| 2 | 1440×900 | Role-based visibility — heart shown on quiz, hidden on chapter, hidden on All-Caught-Up |
| 3 | 1440×900 | Multi-quiz — like two quizzes; `GET /likes` returns both; position/history unaffected |
| 4 | 1440×900 | Validation — double-like and double-unlike are idempotent; 404 on unknown quiz |
| 5 | 1440×900 | Permission guard — unauth POST/DELETE/GET → 401; `/slides` redirects to `/login` |
| 6 | 375×812  | Mobile happy-path — same like/unlike + overflow / ≥44 px tap target / scroll reachability |
| 7 | 375×812  | Mobile role-based visibility |
| 8 | 375×812  | Mobile multi-quiz |
| 9 | 375×812  | Mobile validation |
| 10| 375×812  | Mobile permission guard |

---

## Dependencies

- `user_quiz_recall` table (migration `003_revision_scheduling.sql`) — the boost lives in its `forgetting_rate` column.
- `chapter_quizzes` table (migration `001_content_schema.sql`) — FK target.
- `users` table — FK target.
- `SlideSelector.get_next_slide` (existing) — consumes the boosted `forgetting_rate` without modification.
- `ChatButton` positioning convention — reused for `LikeButton` to guarantee both FABs stay aligned on the same anchor.

## Open Questions

1. **Should a like also "rewind" `last_reviewed_lesson_count` to increase `elapsed_lessons`?** This would make the boost more dramatic (m(t) decays faster _and_ elapsed is larger), but risks double-counting the like as a real review. Current plan: leave `last_reviewed_lesson_count` alone. Revisit if users report the boost is too subtle.
2. **Should likes count toward `review_count`?** Current plan: yes, because `upsert_quiz_recall` increments it and splitting out a non-bumping helper adds branches. Flag if this muddies the dashboard `review_count` meaning.
3. **Should there be a per-user cap on the number of liked quizzes?** Not in this plan. Can be added later as a simple check in `add_like` if spam/abuse becomes a concern.
4. **Should likes be visible in the Dashboard activity log?** Not in this plan. The dashboard currently logs answers and skips, not engagement clicks.
