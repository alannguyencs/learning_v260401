# Likeable Lesson Slides

**Feature**: Extend the existing quiz-like affordance to chapter (lesson) slides; liked chapters appear in the `/favorite` tab alongside liked quizzes in a single interleaved carousel, newest liked first. Chapter likes are bookmark-only and do not affect slide selection.
**Plan Created:** 2026-04-19
**Status:** Plan
**Reference**:
- [Abstract — Slide Stack](../abstract/slide_stack.md)
- [Technical — Slide Stack](../technical/slide_stack.md)
- [Technical — Testing Context](../technical/testing_context.md)

---

## Problem Statement

1. The Like affordance only exists for quiz slides (`SlidePage.jsx:134`). A user reading a chapter they want to revisit later has no way to flag it — the heart FAB does not render on chapter slides.
2. The `user_slide_like` table is quiz-only (`UniqueConstraint(username, quiz_id)`, non-null FK `quiz_id → chapter_quizzes.id`). There is no storage path for liking a chapter.
3. The `/favorite` tab (`FavoriteView.jsx`) only fetches liked **quizzes** via `GET /api/slides/liked-quizzes`. Even if a chapter could be liked, there is no UI surface where a user would see it.
4. The product decision in `docs/abstract/slide_stack.md` explicitly carves out "Liking chapters (a future bookmark feature)" from the current scope. That carve-out is the feature requested here.

---

## Proposed Solution

Make `user_slide_like` **polymorphic over the two slide types** by adding a nullable `chapter_id` column alongside the existing nullable-ified `quiz_id`, with a DB-level CHECK that exactly one of the two is set. Reuse the existing `LikeButton` FAB on chapter slides — same position, same filled/outline states. Extend `/favorite` to render an **interleaved, newest-first carousel** whose card component branches on item type (existing `FavoriteQuizCard` vs a new `FavoriteChapterCard`).

```
user_slide_like
  (id, username, quiz_id?, chapter_id?, liked_at)
  CHECK ((quiz_id IS NOT NULL) <> (chapter_id IS NOT NULL))   -- exactly one
  UNIQUE (username, quiz_id)      ← multiple-NULL-allowed; quiz dedupe
  UNIQUE (username, chapter_id)   ← multiple-NULL-allowed; chapter dedupe

SlidePage
  chapter slide  → <LikeButton chapterId={slide.chapter.id} />
  quiz slide     → <LikeButton quizId={slide.quiz.id} />       (unchanged)

/favorite
  GET /api/slides/liked-items → [{ type: "quiz" | "chapter", ...data, liked_at }]
      ordered by liked_at DESC, id DESC
  FavoriteView renders FavoriteQuizCard or FavoriteChapterCard per item
```

### Key design decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Schema | Nullable `quiz_id` + new nullable `chapter_id` on `user_slide_like` with CHECK constraint | Preserves proper FKs to both parent tables; avoids an untyped `target_id` column; PG UNIQUE with NULLs naturally de-dupes each leg |
| Slide-selection impact | None for chapter likes | Chapters are served once until marked learnt; "resurface a liked chapter" would need a new tier and is out of scope |
| Favorite UI | Single interleaved carousel, newest first | Matches current up/down arrow UX; `FavoriteView` only needs a card-dispatcher; no sub-tabs to introduce |
| Like button placement | Same FAB (`bottom-40 left-[calc(50%+240px)]`) on chapter slides | Reuse existing component, single visual convention; shown on `slide_type` in `{quiz, chapter}` |
| New hook name | Rename `useLikedQuizzes` → `useLikedSlides`; expose `{likedQuizIds, likedChapterIds, isLiked(kind, id), toggleLike(kind, id)}` | Keeps one source of truth for both like sets; backward-compatible callers are updated in the same PR |
| Existing `/likes` response | Extend `LikeListResponse` to `{quiz_ids, chapter_ids}` | One round-trip for both sets on mount; old callers (`useLikedQuizzes`) are migrated in this PR anyway |

---

## Current Implementation Analysis

### What Exists (keep as-is)

| Component | File | Status |
|-----------|------|--------|
| `LikeButton` (outline/filled heart FAB) | `frontend/src/components/LikeButton.jsx` | Keep — accept either `quizId` or `chapterId` prop (adds a discriminator), otherwise unchanged |
| `ChatButton` FAB positioning pattern | `frontend/src/components/ChatButton.jsx` | Keep — both slide types already show the chat FAB |
| `SlideSelector.get_next_slide` (2-tier algorithm) | `backend/src/service/slide_selector.py` | Keep — chapter likes do **not** affect slide selection |
| `RevisionService.apply_like_boost` | `backend/src/service/revision_service.py` | Keep — still only called for quiz likes |
| `FavoriteQuizCard` render logic | `frontend/src/components/FavoriteView.jsx` | Keep — extracted to its own file and consumed by the dispatcher |
| `BookSelector` | `frontend/src/components/BookSelector.jsx` | Keep — same `book_id` filtering works for chapters |
| `user_slide_like` table (migration 010) | `scripts/sql/010_user_slide_like.sql` | Keep — extended by a new migration 011, not replaced |
| Existing `/likes` / `/liked-quizzes` / `POST /quizzes/{id}/like` endpoints | `backend/src/api/slides.py` | Keep — `/likes` response is extended; quiz endpoints unchanged |

### What Changes

| Component | Current | Proposed |
|-----------|---------|----------|
| `user_slide_like` | `quiz_id INTEGER NOT NULL REFERENCES chapter_quizzes(id)`, `UNIQUE(username, quiz_id)` | `quiz_id` becomes nullable, `chapter_id INTEGER NULL REFERENCES chapters(id)` added, CHECK ((quiz_id IS NOT NULL) <> (chapter_id IS NOT NULL)), two UNIQUE indexes (one per leg) |
| `UserSlideLike` ORM model | `quiz_id` non-null, no chapter | `quiz_id` nullable, new `chapter_id` nullable, new CHECK constraint in `__table_args__` |
| `crud_slide_like.py` | quiz-only `add_like / remove_like / is_liked / get_liked_quiz_ids / get_liked_quizzes_with_context` | Adds chapter-equivalent helpers + one combined `get_liked_items_with_context` returning interleaved rows |
| `LikeResponse` / `LikeListResponse` | `{liked: bool}` / `{quiz_ids: [int]}` | Unchanged `LikeResponse`; `LikeListResponse` gains `chapter_ids: [int]` (old `quiz_ids` preserved) |
| `GET /api/slides/liked-quizzes` | Returns quizzes only | Unchanged (kept for backwards compatibility / until consumers migrate) |
| `slides.py` API surface | 10 endpoints | 13 endpoints (+ `POST /chapters/{id}/like`, `DELETE /chapters/{id}/like`, `GET /liked-items`) |
| `SlidePage` | Renders `LikeButton` when `slide_type === "quiz"` | Renders `LikeButton` when `slide_type in {"quiz", "chapter"}` |
| `useLikedQuizzes` hook | Tracks `Set<number>` of liked quiz IDs | Renamed `useLikedSlides`; tracks `{quizIds, chapterIds}` and exposes `isLiked(kind, id)` / `toggleLike(kind, id)` |
| `FavoriteView` | Fetches `listLikedQuizzesFull()`, renders `FavoriteQuizCard` only | Fetches `listLikedItems()`, renders `FavoriteQuizCard` or `FavoriteChapterCard` based on `item.type` |

---

## Implementation Plan

### Key Workflow

#### To Delete
None.

#### To Update
- `frontend/src/pages/SlidePage.jsx` — render `LikeButton` for both chapter and quiz slides (swap the current `slide_type === "quiz"` guard for `slide_type in {"quiz", "chapter"}`). Pass `chapterId` or `quizId` based on type.

#### To Add New

- **Chapter like flow** (new):

```
[User] viewing chapter slide
  │
  ▼
[LikeButton] reads useLikedSlides().likedChapterIds
  │   isLiked = chapterIds.has(chapter.id)
  │   render: filled thumbs-up (isLiked) | outline thumbs-up (!isLiked)
  │
  ▼
[User] clicks heart
  │
  ├── !isLiked → POST /api/slides/chapters/{id}/like
  │              → crud_slide_like.add_chapter_like(db, user, chapter_id) (idempotent)
  │              → frontend optimistically adds id to chapterIds
  │
  └── isLiked  → DELETE /api/slides/chapters/{id}/like
                 → crud_slide_like.remove_chapter_like(db, user, chapter_id) (idempotent)
                 → frontend optimistically removes id from chapterIds
```

- **Interleaved Favorite flow** (new):

```
/favorite loads
  │
  ▼
GET /api/slides/liked-items
  → crud_slide_like.get_liked_items_with_context(db, user)
       SELECT ... FROM user_slide_like usl
       LEFT JOIN chapter_quizzes cq ON cq.id = usl.quiz_id
       LEFT JOIN chapters c_q ON c_q.id = cq.chapter_id       -- quiz lineage
       LEFT JOIN chapters c_c ON c_c.id = usl.chapter_id      -- chapter lineage
       LEFT JOIN lessons l ON l.id = COALESCE(c_q.lesson_id, c_c.lesson_id)
       LEFT JOIN books b ON b.book_id = l.book_id
       WHERE usl.username = :u
       ORDER BY usl.liked_at DESC, usl.id DESC
  │
  ▼
Build List[FavoriteItem] with item.type ∈ {"quiz", "chapter"} + per-type fields
  │
  ▼
FavoriteView dispatches on item.type
  ├── "quiz"    → <FavoriteQuizCard quiz={item} />
  └── "chapter" → <FavoriteChapterCard chapter={item} />
```

- **Slide-selector unaffected** — chapter likes never flow into `SlideSelector`. A liked chapter that was already marked learnt does **not** re-appear as a slide. The only surface is `/favorite`.

---

### Database Schema

#### To Delete
None.

#### To Update

`user_slide_like` table via a new DDL-only migration (existing migration `010_user_slide_like.sql` is untouched):

- `quiz_id` becomes nullable (`ALTER COLUMN quiz_id DROP NOT NULL`).
- Existing `UNIQUE(username, quiz_id)` **kept** — Postgres treats NULLs as distinct so rows with `quiz_id IS NULL` (chapter-like rows) do not collide with each other.

`UserSlideLike` ORM model (`backend/src/models/slide_like.py`):
- Make `quiz_id` nullable.
- Add `chapter_id` column (`Integer`, nullable, FK → `chapters.id`).
- Add `CheckConstraint` and second `UniqueConstraint` to `__table_args__`.

#### To Add New

New migration file: `scripts/sql/011_polymorphic_slide_like.sql`

```sql
-- Migration: Polymorphic user_slide_like — allow liking chapters in addition to quizzes
-- DDL only, idempotent

-- 1. Relax the NOT NULL on quiz_id so chapter likes can omit it.
ALTER TABLE user_slide_like
    ALTER COLUMN quiz_id DROP NOT NULL;

-- 2. Add nullable chapter_id referencing chapters(id)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'user_slide_like' AND column_name = 'chapter_id'
    ) THEN
        ALTER TABLE user_slide_like
            ADD COLUMN chapter_id INTEGER NULL REFERENCES chapters(id);
    END IF;
END
$$;

-- 3. Enforce exactly-one-of-(quiz_id, chapter_id) at the DB layer
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'usl_exactly_one_target'
    ) THEN
        ALTER TABLE user_slide_like
            ADD CONSTRAINT usl_exactly_one_target
            CHECK ((quiz_id IS NOT NULL) <> (chapter_id IS NOT NULL));
    END IF;
END
$$;

-- 4. Chapter-leg uniqueness. Multiple NULLs are fine for both unique constraints.
CREATE UNIQUE INDEX IF NOT EXISTS idx_usl_user_chapter_unique
    ON user_slide_like (username, chapter_id);

CREATE INDEX IF NOT EXISTS idx_usl_chapter
    ON user_slide_like (chapter_id);
```

**Column additions / changes**

| Column | Type | Constraint | Purpose |
|--------|------|-----------|---------|
| `quiz_id` | Integer | **nullable** (was NOT NULL), FK → `chapter_quizzes.id` | Set when the row is a quiz like |
| `chapter_id` | Integer | nullable (new), FK → `chapters.id` | Set when the row is a chapter like |
| — | — | `CHECK ((quiz_id IS NOT NULL) <> (chapter_id IS NOT NULL))` | Exactly one target per row |
| — | — | `UNIQUE (username, quiz_id)` (existing; multi-NULL allowed) | De-dupe per quiz |
| — | — | `UNIQUE (username, chapter_id)` (new) | De-dupe per chapter |
| — | — | Index `idx_usl_chapter` | Backs `GET /liked-items` chapter-side joins |

---

### CRUD

#### To Delete
None — existing quiz helpers stay.

#### To Update

`backend/src/crud/crud_slide_like.py`:

- `add_like(db, username, quiz_id)` → rename internally to `add_quiz_like`; keep the old name as a thin alias for the already-shipped quiz flow.
- `remove_like(db, username, quiz_id)` → rename to `remove_quiz_like`; keep alias.
- `get_liked_quiz_ids(db, username)` → unchanged (still queries `WHERE quiz_id = ... AND quiz_id IS NOT NULL`).
- `get_liked_quizzes_with_context(db, username)` → add `WHERE UserSlideLike.quiz_id IS NOT NULL` to keep behaviour correct now that `quiz_id` can be NULL.

#### To Add New

`backend/src/crud/crud_slide_like.py`:

| Function | Signature | Description |
|----------|-----------|-------------|
| `add_chapter_like` | `(db, username, chapter_id) -> None` | `INSERT ... (username, chapter_id) VALUES ... ON CONFLICT (username, chapter_id) DO NOTHING`. Commits. |
| `remove_chapter_like` | `(db, username, chapter_id) -> None` | `DELETE FROM user_slide_like WHERE username = :u AND chapter_id = :c`. Idempotent. |
| `is_chapter_liked` | `(db, username, chapter_id) -> bool` | Row lookup. |
| `get_liked_chapter_ids` | `(db, username) -> list[int]` | `SELECT chapter_id FROM user_slide_like WHERE username = :u AND chapter_id IS NOT NULL ORDER BY liked_at DESC, id DESC`. |
| `get_liked_items_with_context` | `(db, username) -> list[LikedItemRow]` | Returns a **type-tagged** list of rows combining both legs via `UNION ALL`, each row carrying `kind ∈ {"quiz", "chapter"}` + per-type fields + book/lesson context, ordered by `liked_at DESC, id DESC`. Backs `GET /liked-items`. |

The `LikedItemRow` dataclass (lives in `crud_slide_like.py`):

```python
@dataclass
class LikedItemRow:
    kind: Literal["quiz", "chapter"]
    like_id: int
    liked_at: datetime
    book_id: str
    book_title: str
    lesson_id: int
    lesson_title: str
    # quiz-only
    quiz: ChapterQuiz | None
    # chapter-only
    chapter: Chapter | None
```

---

### Services

#### To Delete
None.

#### To Update
None — `RevisionService.apply_like_boost` stays quiz-only (chapter likes do not affect recall).

#### To Add New
None — the feature is thin enough to live entirely in CRUD + API layers.

---

### API Endpoints

#### To Delete
None.

#### To Update

`GET /api/slides/likes` response extends from `{quiz_ids: [int]}` to `{quiz_ids: [int], chapter_ids: [int]}`. Old `quiz_ids` key is preserved verbatim so any other consumer continues to work; the frontend `useLikedSlides` hook reads both.

#### To Add New

Three new endpoints in `backend/src/api/slides.py`:

| Method | Path | Auth | Handler | Response |
|--------|------|------|---------|----------|
| POST   | `/api/slides/chapters/{chapter_id}/like` | Session | `like_chapter` | `{"liked": true}` |
| DELETE | `/api/slides/chapters/{chapter_id}/like` | Session | `unlike_chapter` | `{"liked": false}` |
| GET    | `/api/slides/liked-items` | Session | `list_liked_items` | `{"items": [...]}` — see schema below |

Endpoint behaviour:

```python
@router.post("/slides/chapters/{chapter_id}/like", response_model=LikeResponse)
def like_chapter(chapter_id, user=Depends(require_session_user), db=Depends(get_db)):
    if get_chapter(db, chapter_id) is None:
        raise HTTPException(404, "Chapter not found")
    crud_slide_like.add_chapter_like(db, user.username, chapter_id)
    return LikeResponse(liked=True)

@router.delete("/slides/chapters/{chapter_id}/like", response_model=LikeResponse)
def unlike_chapter(chapter_id, user=Depends(require_session_user), db=Depends(get_db)):
    crud_slide_like.remove_chapter_like(db, user.username, chapter_id)
    return LikeResponse(liked=False)

@router.get("/slides/liked-items", response_model=LikedItemsResponse)
def list_liked_items(user=Depends(require_session_user), db=Depends(get_db)):
    rows = crud_slide_like.get_liked_items_with_context(db, user.username)
    return LikedItemsResponse(items=[_row_to_item(r) for r in rows])
```

New / updated Pydantic schemas in `backend/src/schemas/slides.py`:

```python
class LikeListResponse(BaseModel):           # UPDATED
    quiz_ids: List[int]
    chapter_ids: List[int] = []              # new key, default empty for safety

class LikedQuizItem(BaseModel):
    type: Literal["quiz"] = "quiz"
    id: int                                  # like row id
    quiz: FavoriteQuiz                       # reuse existing schema
    liked_at: str

class LikedChapterItem(BaseModel):
    type: Literal["chapter"] = "chapter"
    id: int                                  # like row id
    chapter: FavoriteChapter                 # new schema (below)
    liked_at: str

class FavoriteChapter(BaseModel):
    id: int
    lesson_id: int
    lesson_title: str
    book_id: str
    book_title: str
    lesson_index: int
    chapter_index: int
    title: str
    content: str                             # markdown body

class LikedItemsResponse(BaseModel):
    items: List[LikedQuizItem | LikedChapterItem]
```

JSON examples:

```
POST /api/slides/chapters/16/like       → 200 {"liked": true}
POST (repeat)                            → 200 {"liked": true}     # idempotent
DELETE /api/slides/chapters/16/like     → 200 {"liked": false}
POST /api/slides/chapters/999999/like   → 404 {"detail": "Chapter not found"}
POST (no session)                        → 401 {"detail": "Not authenticated"}

GET /api/slides/likes                    → 200 {"quiz_ids": [42], "chapter_ids": [16]}
GET /api/slides/liked-items              → 200 {
  "items": [
    {"type": "quiz",    "id": 19, "quiz":    { …FavoriteQuiz… },    "liked_at": "2026-04-19T12:00:00"},
    {"type": "chapter", "id": 18, "chapter": { …FavoriteChapter… }, "liked_at": "2026-04-19T11:55:00"}
  ]
}
```

---

### Testing

#### To Delete
None.

#### To Update

- `backend/tests/test_crud_slide_like.py` — update any assertion that reads `quiz_id` to also tolerate NULL rows (chapter likes). Existing quiz-like test cases continue to pass.
- `backend/tests/test_slides_api.py` — the `/likes` test should assert the new `chapter_ids` key is present and empty when no chapter likes exist.

#### To Add New

**Backend tests**

- `backend/tests/test_crud_slide_like.py` *(extend)*
  - `add_chapter_like` inserts a row with non-null `chapter_id` and null `quiz_id`; second call is idempotent.
  - `remove_chapter_like` deletes the row; second call no-op.
  - `is_chapter_liked` / `get_liked_chapter_ids` return correct values.
  - `get_liked_items_with_context` returns a tagged interleaved list ordered by `liked_at DESC, id DESC`.
  - CHECK constraint: attempting to INSERT a row with both `quiz_id IS NULL` AND `chapter_id IS NULL` (or both set) raises an `IntegrityError`.

- `backend/tests/test_slides_api.py` *(extend)*
  - `POST /api/slides/chapters/{id}/like` returns `{"liked": true}`, inserts a row with the right columns, and does **not** touch `user_quiz_recall` (no rate boost).
  - `DELETE /api/slides/chapters/{id}/like` returns `{"liked": false}` and deletes the row.
  - `POST /api/slides/chapters/999999/like` returns 404.
  - `GET /api/slides/likes` returns both `quiz_ids` and `chapter_ids`.
  - `GET /api/slides/liked-items` returns an interleaved list, newest first, with `type` discriminator.
  - All three new endpoints return 401 without a session cookie.

- `backend/tests/test_slide_selector.py` *(extend)*
  - Regression: liking a chapter does **not** change the order returned by `SlideSelector.get_next_slide`; a learnt chapter with a like does not reappear on `/slides`.

**Frontend tests**

- `frontend/src/__tests__/hooks/useLikedSlides.test.js` (renamed from `useLikedQuizzes.test.js`)
  - On mount, fetches `GET /api/slides/likes` and stores both sets.
  - `toggleLike("quiz", id)` and `toggleLike("chapter", id)` call the correct endpoints.
  - Rolls back optimistic state on API error.

- `frontend/src/__tests__/components/LikeButton.test.js` *(extend)*
  - Renders identically whether driven by `quizId` or `chapterId` prop.
  - Clicks call the correct hook method.

- `frontend/src/__tests__/components/FavoriteView.test.js` *(new or extend)*
  - Renders `FavoriteQuizCard` for quiz items and `FavoriteChapterCard` for chapter items based on `item.type`.
  - Respects `liked_at DESC` ordering.
  - BookSelector filter applies to both types via `book_id`.

**Pre-commit loop**

1. Run `source venv/bin/activate && pre-commit run --all-files`.
2. Fix any issues (lint errors, line count violations, Prettier diff).
3. Re-run — Prettier may reformat the fixes and push files over the 300-line frontend limit (`FavoriteView.jsx` is already at ~200 lines; the card dispatcher may push it close). If so, extract `FavoriteQuizCard` and `FavoriteChapterCard` into their own files.
4. Repeat until pre-commit passes cleanly on a full re-run with no new failures.

---

### Frontend

#### To Delete
None.

#### To Update

- `frontend/src/services/api.js` — update existing and add new methods:

```js
// Extended: now returns { quiz_ids, chapter_ids }
listLikedSlides: async () => {
  const response = await api.get("/api/slides/likes");
  return response.data;
},

// New
likeChapter: async (chapterId) => {
  const response = await api.post(`/api/slides/chapters/${chapterId}/like`);
  return response.data;
},

unlikeChapter: async (chapterId) => {
  const response = await api.delete(`/api/slides/chapters/${chapterId}/like`);
  return response.data;
},

// New — interleaved list for /favorite
listLikedItems: async () => {
  const response = await api.get("/api/slides/liked-items");
  return response.data;
},
```

Old `likeQuiz` / `unlikeQuiz` / `listLikedQuizzes` / `listLikedQuizzesFull` remain (still called by the renamed hook).

- `frontend/src/hooks/useLikedQuizzes.js` → rename file to `useLikedSlides.js`; update the hook:

```js
const useLikedSlides = () => {
  const [quizIds, setQuizIds]       = useState(() => new Set());
  const [chapterIds, setChapterIds] = useState(() => new Set());

  useEffect(() => { /* fetch listLikedSlides → setQuizIds + setChapterIds */ }, []);

  const isLiked = (kind, id) =>
    kind === "quiz"    ? quizIds.has(id)
  : kind === "chapter" ? chapterIds.has(id)
  : false;

  const toggleLike = async (kind, id) => {
    const setter = kind === "quiz" ? setQuizIds : setChapterIds;
    const was = kind === "quiz" ? quizIds.has(id) : chapterIds.has(id);
    setter(prev => { const n = new Set(prev); was ? n.delete(id) : n.add(id); return n; });
    try {
      if (kind === "quiz")    await (was ? apiService.unlikeQuiz(id)    : apiService.likeQuiz(id));
      else                     await (was ? apiService.unlikeChapter(id): apiService.likeChapter(id));
    } catch {
      setter(prev => { const n = new Set(prev); was ? n.add(id) : n.delete(id); return n; });
    }
  };

  return { quizIds, chapterIds, isLiked, toggleLike };
};
```

- `frontend/src/components/LikeButton.jsx` — accept a discriminated prop shape:

```jsx
const LikeButton = ({ kind, id, isLiked, onToggle }) => {
  // kind ∈ {"quiz", "chapter"} — identical visual; aria-label branches on kind
  ...
};
```

Positioning and SVGs unchanged.

- `frontend/src/pages/SlidePage.jsx` — render the FAB for both slide types:

```jsx
{!loading && !error && slide?.slide_type === "chapter" && slide.chapter && (
  <LikeButton
    kind="chapter"
    id={slide.chapter.id}
    isLiked={isLiked("chapter", slide.chapter.id)}
    onToggle={() => toggleLike("chapter", slide.chapter.id)}
  />
)}
{!loading && !error && slide?.slide_type === "quiz" && slide.quiz && (
  <LikeButton
    kind="quiz"
    id={slide.quiz.id}
    isLiked={isLiked("quiz", slide.quiz.id)}
    onToggle={() => toggleLike("quiz", slide.quiz.id)}
  />
)}
```

- `frontend/src/components/FavoriteView.jsx` — replace `listLikedQuizzesFull()` call with `listLikedItems()`; iterate over `data.items` and dispatch per `item.type`. The existing up/down-arrow carousel, BookSelector filter, and counter are preserved verbatim.

#### To Add New

- `frontend/src/components/FavoriteQuizCard.jsx` — extract the existing `FavoriteQuizCard` sub-component from `FavoriteView.jsx` into its own file, unchanged. (Needed to keep `FavoriteView.jsx` under the 300-line limit once the chapter card is added.)

- `frontend/src/components/FavoriteChapterCard.jsx` — new card that mirrors the chapter-slide layout:

  Visual spec:
  - Book/lesson breadcrumb (same `text-sm text-gray-400 mb-3` as the quiz card).
  - Chapter title — `text-lg text-white font-medium`.
  - Markdown body rendered with the same renderer already in `ChapterSlide.jsx` (import it — no new dep needed).
  - No interactive controls (card is read-only in `/favorite`; unlike still happens from the slide page).

  Visual sketch:
  ```
  ┌──────────────────────────────────────────────┐
  │ Learning Phrases · English Cartoons · Ch 1   │
  │ "My Room"                                    │
  │                                              │
  │ # Chapter markdown                           │
  │ Paragraph…                                   │
  │ * bullet                                     │
  └──────────────────────────────────────────────┘
  ```

- `/favorite` empty-state copy update — from:
  > "Like a quiz from the Slides page to add it here"
  to:
  > "Like a quiz or chapter from the Slides page to add it here"

---

### Documentation

#### Abstract (`docs/abstract/`)

**Update** `docs/abstract/slide_stack.md`:
- **Solution** paragraph — append a sentence: "Users can also like chapter slides; liked chapters appear in the Favorite tab alongside liked quizzes in a single newest-first list. Chapter likes are bookmarks only and do not affect the slide selection algorithm."
- **User Flow** — add a branch under the Chapter slide bullet:

  ```
  ├── Like (on any chapter slide):
  │     [Like button (thumbs-up)] → toggles like/unlike
  │     Liked chapters are bookmarked and visible in the Favorite tab;
  │     they do NOT resurface on the slide stream.
  ```
- Replace the existing quiz-only Like bullet with one that explicitly distinguishes the two:
  - Quiz slide Like: weakens recall → resurfaces sooner (unchanged behaviour).
  - Chapter slide Like: bookmark only.
- **Scope — Included** — add: "Per-chapter like/unlike with the same thumbs-up FAB as quizzes; liked chapters appear in the Favorite tab."
- **Scope — Not included** — remove the "Liking chapters (a future bookmark feature)" line (now implemented). Keep the "social like counts" exclusion.
- **Acceptance Criteria** — add:
  - `- [ ] Like button (thumbs-up) is visible on every chapter slide and hidden on the All-Caught-Up state.`
  - `- [ ] Liking a chapter persists across page refresh and does NOT change the next slide served.`
  - `- [ ] The Favorite tab shows liked chapters and liked quizzes in a single carousel ordered newest-liked first.`
  - `- [ ] A liked chapter appears as a chapter card (breadcrumb + title + markdown body), distinct from the quiz card layout.`
  - `- [ ] BookSelector on the Favorite tab filters both quiz and chapter items by book.`

No new abstract file — the feature lives inside the existing Slide Stack scope (the Favorite tab is already a user-facing surface of Slide Stack, even though it currently lacks its own abstract doc).

#### Technical (`docs/technical/`)

**Update** `docs/technical/slide_stack.md`:

- **Architecture** — append three routes to the API block:
  ```
  POST   /api/slides/chapters/{id}/like  → crud_slide_like.add_chapter_like
  DELETE /api/slides/chapters/{id}/like  → crud_slide_like.remove_chapter_like
  GET    /api/slides/liked-items         → crud_slide_like.get_liked_items_with_context
  ```

- **Data Model → `UserSlideLike`** — replace the current table definition with the polymorphic version:

  | Column | Type | Constraints |
  |--------|------|-------------|
  | `id` | Integer | PK |
  | `username` | String | FK → users.username, NOT NULL |
  | `quiz_id` | Integer | nullable, FK → chapter_quizzes.id |
  | `chapter_id` | Integer | nullable, FK → chapters.id |
  | `liked_at` | Timestamp | NOT NULL, DEFAULT NOW() |
  | — | — | CHECK (`(quiz_id IS NOT NULL) <> (chapter_id IS NOT NULL)`) |
  | — | — | UNIQUE(`username`, `quiz_id`), UNIQUE(`username`, `chapter_id`) |

  Indexes: `idx_usl_user` (existing), `idx_usl_chapter` (new).

- **API Layer** — add three rows for the new endpoints.

- **CRUD Layer → `crud_slide_like.py`** — add rows for `add_chapter_like`, `remove_chapter_like`, `is_chapter_liked`, `get_liked_chapter_ids`, `get_liked_items_with_context`. Note that `add_like` / `remove_like` are aliases for the quiz variants.

- **Frontend — Components** — add a row:

  `FavoriteChapterCard | frontend/src/components/FavoriteChapterCard.jsx | Read-only card rendering a liked chapter in /favorite (breadcrumb, title, markdown body)`

  Update the `LikeButton` row to mention both slide types (`Thumbs-up FAB on chapter and quiz slides …`).
  Replace the existing `FavoriteQuizCard` mention in `FavoriteView.jsx` with a new `FavoriteQuizCard` row pointing at `frontend/src/components/FavoriteQuizCard.jsx`.

- **Frontend — Services & Hooks** —
  - Rename the `useLikedQuizzes` row to `useLikedSlides` and update the method table to list `{quizIds, chapterIds, isLiked(kind, id), toggleLike(kind, id)}`.
  - Update the `api.js` additions table to include `likeChapter`, `unlikeChapter`, `listLikedItems`, and note that `listLikedQuizzes` now returns `{quiz_ids, chapter_ids}`.

- **Component Checklist** — append (all unchecked initially):
  - `- [ ] Migration — scripts/sql/011_polymorphic_slide_like.sql`
  - `- [ ] Model update — backend/src/models/slide_like.py (nullable quiz_id; new chapter_id; CHECK)`
  - `- [ ] CRUD — backend/src/crud/crud_slide_like.py (add_chapter_like, remove_chapter_like, is_chapter_liked, get_liked_chapter_ids, get_liked_items_with_context)`
  - `- [ ] API — backend/src/api/slides.py (POST/DELETE /chapters/{id}/like, GET /liked-items)`
  - `- [ ] Schemas — backend/src/schemas/slides.py (FavoriteChapter, LikedQuizItem, LikedChapterItem, LikedItemsResponse; LikeListResponse.chapter_ids)`
  - `- [ ] Tests — backend/tests/test_crud_slide_like.py (chapter helpers + CHECK + interleaving)`
  - `- [ ] Tests — backend/tests/test_slides_api.py (chapter-like endpoints, /liked-items, /likes extended)`
  - `- [ ] Tests — backend/tests/test_slide_selector.py (regression: chapter like never resurfaces)`
  - `- [ ] Hook — frontend/src/hooks/useLikedSlides.js (renamed from useLikedQuizzes)`
  - `- [ ] Component — frontend/src/components/LikeButton.jsx (kind/id prop)`
  - `- [ ] Component — frontend/src/components/FavoriteQuizCard.jsx (extract)`
  - `- [ ] Component — frontend/src/components/FavoriteChapterCard.jsx`
  - `- [ ] Page update — frontend/src/pages/SlidePage.jsx (LikeButton on chapter slides too)`
  - `- [ ] Page update — frontend/src/components/FavoriteView.jsx (interleaved dispatcher, updated empty copy)`
  - `- [ ] API methods — frontend/src/services/api.js (likeChapter / unlikeChapter / listLikedItems; likes response extended)`
  - `- [ ] Tests — frontend/src/__tests__/hooks/useLikedSlides.test.js`
  - `- [ ] Tests — frontend/src/__tests__/components/LikeButton.test.js (chapter prop shape)`
  - `- [ ] Tests — frontend/src/__tests__/components/FavoriteView.test.js (interleaved rendering)`

No update to `docs/technical/revision_scheduling.md` — chapter likes do not interact with recall or rounds.

#### API Documentation (`docs/api_doc/`)

No changes needed — the project has no `docs/api_doc/` directory (verified in Step 1). API endpoint reference lives inside `docs/technical/slide_stack.md`, which is updated above.

---

### Chrome Claude Extension Execution

After implementation is complete, execute the Chrome Claude Extension E2E tests defined in `docs/chrome_test/260419_1311_likeable_lesson_slides.md` by invoking the `chrome-test-execute` skill.

`feature-implement-full` invokes it automatically as part of its post-implementation flow; if the plan is executed manually, run `/webapp-dev:chrome-test-execute docs/chrome_test/260419_1311_likeable_lesson_slides.md` yourself. Full execution rules live in that skill's `references/execution-rules.md`.

Test coverage at a glance (10 tests, both viewports):

| # | Viewport | Test |
|---|----------|------|
| 1 | 1440×900 | Happy-path like-chapter: click heart → persists refresh → appears in /favorite as chapter card; unlike removes it |
| 2 | 1440×900 | Heart visibility on chapter / quiz / All-Caught-Up; regression — chapter like does not resurface on /slides |
| 3 | 1440×900 | Interleaved /favorite carousel: chapter + quiz in one list, newest-first; BookSelector filters both |
| 4 | 1440×900 | Idempotent like/unlike, 404 on unknown chapter, polymorphic CHECK, empty-state copy |
| 5 | 1440×900 | Unauth /favorite redirect; 401 on new chapter endpoints and /liked-items |
| 6 | 375×812  | Mobile happy-path; heart FAB ≥ 44 px, chapter card no overflow |
| 7 | 375×812  | Mobile FAB stack no overlap on both slide types |
| 8 | 375×812  | Mobile interleaved carousel — card overflow and tap-target checks |
| 9 | 375×812  | Mobile validation — double-tap idempotency + optimistic rollback on synthetic 500 |
| 10| 375×812  | Mobile permission guard |

---

## Dependencies

- `chapters` table (migration `001_content_schema.sql`) — FK target for the new `chapter_id` column.
- `chapter_quizzes` table (migration `001_content_schema.sql`) — existing FK target for `quiz_id`.
- `user_slide_like` table (migration `010_user_slide_like.sql`) — extended by migration 011.
- `users` table — FK target for `username`.
- `ChapterSlide` markdown renderer (`frontend/src/components/ChapterSlide.jsx`) — reused by `FavoriteChapterCard`.
- `LikeButton`, `ChatButton` FAB positioning convention — reused verbatim on chapter slides.

## Open Questions

1. **Unlike from `/favorite`?** Current plan: no — unlike happens only on the slide page (matches the current quiz flow). A "remove" button on each favorite card could be added later if users ask.
2. **Should the chapter card render the full markdown or a truncated preview?** Current plan: full markdown, same as the slide page (with the same renderer). If cards become too tall, we can cap to N lines with a "read more" expansion in a follow-up.
3. **Should liking a chapter also jump the user to `/favorite`?** No — this would be surprising. The heart is a passive bookmark action.
4. **Should `listLikedQuizzesFull` / `GET /liked-quizzes` be deprecated?** Not in this plan — it remains for backwards compatibility. A follow-up can remove it once no consumer is left.
