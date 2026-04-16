# Slide Navigation Arrows — Coach UI

**Feature**: Adopt coach-style arrow UI: ArrowUp above BookSelector, ArrowDown fixed at viewport bottom, smart down-arrow (chapter marks learnt, quiz pre-answer skips, quiz post-feedback advances), remove explicit Skip/Next buttons
**Plan Created:** 2026-04-16
**Status:** Plan
**Reference**:
- [Abstract — Slide Stack](../abstract/slide_stack.md)
- [Technical — Slide Stack](../technical/slide_stack.md)
- [Testing Context](../technical/testing_context.md)

---

## Problem Statement

1. The current navigation arrows are placed inline in a horizontal flex row between BookSelector and slide content. The down arrow is not persistently accessible — it scrolls with the page.
2. The up arrow is beside the down arrow in the same row instead of being visually separated above the BookSelector.
3. The down arrow always calls `fetchNextSlide(bookId)` regardless of slide type, so pressing it on a chapter slide advances without marking the chapter as learnt.
4. Quiz skip requires clicking an explicit "Skip" button inside the quiz card. The coach design removes this button and routes skip through the down arrow (before answer submission).
5. After quiz feedback, the user must click a "Next Slide" button inside the feedback panel. The coach design removes this button and routes advance through the down arrow.
6. `fetchNextSlide` takes `currentBookId` as its argument instead of using internal `bookId` state, which creates an inconsistency (callers must pass the right book id).

---

## Proposed Solution

Adopt the coach app's navigation pattern with no backend changes:

1. **ArrowUp** — a full-width centered row rendered above `<BookSelector>`, shown only when `hasPrevious` is true. Uses a SVG up-chevron (`M5 15l7-7 7 7`).
2. **ArrowDown** — a fixed overlay at `bottom-[76px]` (above bottom nav), horizontally centered via `left-1/2 -translate-x-1/2`, always shown when a slide is active. Uses a SVG down-chevron (`M19 9l-7 7-7-7`).
3. **Smart down arrow** (`handleDownArrow`):
   - Chapter slide → `fetchNextSlide(slide.chapter.id)` → marks chapter learnt + advances
   - Quiz slide (no feedback) → `skipItem(...)` with `is_skip: true` → skip to back of queue
   - Quiz slide (feedback shown) → `fetchNextSlide()` → advance without marking
4. **Remove Skip Chapter** button from `ChapterSlide`.
5. **Remove Skip** button and `onSkip` prop from `QuizSlide`.
6. **Remove Next Slide** button from `FeedbackPanel` inside `QuizSlide`.
7. **`fetchNextSlide` signature** → change from `fetchNextSlide(currentBookId)` to `fetchNextSlide(markChapterId?)`. Always uses internal `bookId` state for the book filter; optionally includes `mark_chapter_id` when a chapter id is passed.

---

## Current Implementation Analysis

### What Exists (keep as-is)

| Component | File | Status |
|-----------|------|--------|
| All backend endpoints | `backend/src/api/slides.py` | Keep — no backend changes |
| `useSlide` state, `markLearnt`, `goPrevious`, `submitAnswer`, `skipItem` | `frontend/src/hooks/useSlide.js` | Keep — only `fetchNextSlide` signature changes |
| `BookSelector` | `frontend/src/components/BookSelector.jsx` | Keep |
| `AllCaughtUp` | `frontend/src/components/AllCaughtUp.jsx` | Keep |
| `ChatButton` / `ChatPanel` | `frontend/src/components/ChatButton.jsx`, `ChatPanel.jsx` | Keep |

### What Changes

| Component | Current | Proposed |
|-----------|---------|----------|
| `SlidePage.jsx` — ArrowUp | Inline flex row (text `↑`) next to ArrowDown | Full-width centered row above BookSelector, SVG chevron, shown only when `hasPrevious` |
| `SlidePage.jsx` — ArrowDown | Inline flex row (text `↓`) | Fixed overlay `bottom-[76px] left-1/2 -translate-x-1/2 z-40`, SVG chevron |
| `SlidePage.jsx` — down arrow handler | `fetchNextSlide(bookId)` always | Smart: chapter → mark learnt; quiz no-feedback → skip; quiz with-feedback → advance |
| `ChapterSlide.jsx` | "Mark as Learnt" + "Skip Chapter" buttons | "Mark as Learnt" only |
| `QuizSlide.jsx` (before feedback) | "Skip" + "Submit Answer" buttons | "Submit Answer" only |
| `FeedbackPanel` (inside QuizSlide) | Shows "Next Slide" button | No "Next Slide" button |
| `useSlide.fetchNextSlide` | `fetchNextSlide(currentBookId)` passes book id via arg | `fetchNextSlide(markChapterId?)` uses internal `bookId`; optional `mark_chapter_id` |

---

## Implementation Plan

### Key Workflow

```
User presses down arrow
  │
  ├── slide_type === "chapter"
  │     fetchNextSlide(slide.chapter.id)
  │       → POST /api/slides/forward { book_id: <internal>, mark_chapter_id: chapter.id }
  │       → marks chapter learnt + advances
  │
  ├── slide_type === "quiz" AND no feedback
  │     skipItem(quiz.id, { is_skip: true, round_num, lesson_id, user_answer: "" })
  │       → POST /api/slides/quizzes/{id}/respond { is_skip: true }
  │       → POST /api/slides/forward { book_id: <internal> }
  │       → quiz goes to back of queue, next slide loaded
  │
  └── slide_type === "quiz" AND feedback shown
        fetchNextSlide()
          → POST /api/slides/forward { book_id: <internal> }
          → advances to next slide
```

### Database Schema

#### To Delete
None.

#### To Update
None.

#### To Add New
None — no schema changes.

### CRUD

#### To Delete
None.

#### To Update
None.

#### To Add New
None — no CRUD changes.

### Services

#### To Delete
None.

#### To Update
None.

#### To Add New
None — no service changes.

### API Endpoints

#### To Delete
None.

#### To Update
None.

#### To Add New
None — no API changes.

### Testing

#### To Delete
None.

#### To Update

- **`frontend/src/__tests__/components/ChapterSlide.test.js`**:
  - Remove tests asserting the "Skip Chapter" button renders and calls `onSkip`.
  - Remove the `onSkip` prop from any `render(<ChapterSlide ...>)` calls.
  - Add/keep assertion that only "Mark as Learnt" button is rendered.

- **`frontend/src/__tests__/components/QuizSlide.test.js`**:
  - Remove tests asserting the "Skip" button renders and calls `onSkip`.
  - Remove tests asserting the "Next Slide" button renders in feedback.
  - Remove `onSkip` and `onNext` props from `render(<QuizSlide ...>)` calls.
  - Keep all feedback panel content tests (PASSED/FAILED badge, good/bad points, key points).

- **`frontend/src/__tests__/hooks/useSlide.test.js`**:
  - Update `fetchNextSlide` tests: signature now `fetchNextSlide(markChapterId?)` not `fetchNextSlide(bookId)`.
  - Verify that calling `fetchNextSlide()` sends `{ book_id: <bookId from state>, mark_chapter_id: undefined }`.
  - Verify that calling `fetchNextSlide(42)` sends `{ book_id: <bookId from state>, mark_chapter_id: 42 }`.

#### To Add New
None.

**Pre-commit loop:**
1. Run `source venv/bin/activate && pre-commit run --all-files`.
2. Fix any lint or line-count issues (max 300 lines per frontend file).
3. Re-run; Prettier may push files back over the line limit — extract sub-components if needed.
4. Repeat until pre-commit passes cleanly.

### Frontend

#### To Delete

- `onSkip` prop and "Skip Chapter" `<button>` from `frontend/src/components/ChapterSlide.jsx`.
- `onSkip` prop and "Skip" `<button>` from `frontend/src/components/QuizSlide.jsx`.
- "Next Slide" `<button>` and `onNext` prop from `FeedbackPanel` (inside `frontend/src/components/QuizSlide.jsx`).
- The existing inline flex navigation row (`<div className="flex justify-between items-center mb-4">` containing both arrows) from `frontend/src/pages/SlidePage.jsx`.

#### To Update

**`frontend/src/hooks/useSlide.js`**:
- Change `fetchNextSlide` signature: replace `async (currentBookId)` with `async (markChapterId)`.
- Inside, always use internal `bookId` state: `const body = { book_id: bookId };`
- If `markChapterId` is truthy, add `body.mark_chapter_id = markChapterId`.
- Update `skipItem` to call `fetchNextSlide()` (no arg) instead of `fetchNextSlide(bookId)`.

```js
// Before
const fetchNextSlide = useCallback(async (currentBookId) => {
  const data = await apiService.slideForward({ book_id: currentBookId || null });
  ...
}, []);

// After
const fetchNextSlide = useCallback(
  async (markChapterId) => {
    const body = { book_id: bookId };
    if (markChapterId) body.mark_chapter_id = markChapterId;
    const data = await apiService.slideForward(body);
    ...
  },
  [bookId],
);
```

**`frontend/src/pages/SlidePage.jsx`**:
- Replace the `ArrowUp`/`ArrowDown` component definitions with SVG-chevron versions:
  ```jsx
  const ArrowUp = ({ onClick }) => (
    <button
      onClick={onClick}
      className="w-full flex justify-center py-1 text-gray-400 hover:text-blue-600 transition-colors"
      aria-label="Previous slide"
    >
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24"
           stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M5 15l7-7 7 7" />
      </svg>
    </button>
  );

  const ArrowDown = ({ onClick }) => (
    <button
      onClick={onClick}
      className="flex items-center gap-1 px-3 py-1 text-gray-400 hover:text-blue-600 transition-colors"
      aria-label="Next slide"
    >
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24"
           stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
      </svg>
    </button>
  );
  ```
- Add `handleDownArrow`:
  ```js
  const handleDownArrow = () => {
    if (!slide) return;
    if (slide.slide_type === "chapter") {
      fetchNextSlide(slide.chapter.id);
    } else if (slide.slide_type === "quiz" && !feedback) {
      skipItem(slide.quiz.id, {
        round_num: slide.quiz.round_num,
        lesson_id: slide.quiz.lesson_id,
        user_answer: "",
        is_skip: true,
      });
    } else {
      fetchNextSlide();
    }
  };
  ```
- Move `ArrowUp` render to above `<BookSelector>` (conditional on `isActive && hasPrevious`).
- Move `ArrowDown` render to a fixed overlay (conditional on `isActive`):
  ```jsx
  <div className="fixed bottom-[76px] left-1/2 -translate-x-1/2 z-40">
    <ArrowDown onClick={handleDownArrow} />
  </div>
  ```
- Remove `onSkip` from `<ChapterSlide>` usage.
- Remove `onSkip` and `onNext` from `<QuizSlide>` usage.

**`frontend/src/components/ChapterSlide.jsx`**:
- Remove `onSkip` from props destructuring.
- Remove "Skip Chapter" button element.

**`frontend/src/components/QuizSlide.jsx`**:
- Remove `onSkip` from `QuizSlide` props.
- Remove "Skip" button element.
- Remove `onNext` from `FeedbackPanel` props.
- Remove "Next Slide" button from `FeedbackPanel`.

#### To Add New
None.

### Documentation

#### Abstract (`docs/abstract/`)

**`docs/abstract/slide_stack.md`** — update:

- **User Flow** section: revise the navigation block and slide-type sections:
  - Arrow descriptions: "ArrowUp — full-width row above BookSelector, only shown when has_previous; ArrowDown — fixed at viewport bottom, always shown on active slides"
  - Chapter slide: remove "[Skip Chapter]" line
  - Quiz slide: remove "[Skip]" button line; remove "[Next Slide]" button line
  - Down arrow: clarify smart behavior — chapter → marks learnt + advances; quiz (no feedback) → skips; quiz (with feedback) → advances
- **Acceptance Criteria** section:
  - Replace "Down arrow is always visible on chapter and quiz slides; clicking it advances to next slide" with:
    - `- [ ] Down arrow on a chapter slide marks the chapter as learnt and advances`
    - `- [ ] Down arrow on a quiz slide (before submitting) skips the quiz to the back of the queue`
    - `- [ ] Down arrow on a quiz slide (after feedback) advances to the next slide`
  - Remove "Clicking 'Next Slide' after feedback advances to the next slide"
  - Replace "Skipping a quiz or chapter advances to the next slide" with "Skipping a quiz via the down arrow puts it at the back of the queue"

#### Technical (`docs/technical/`)

**`docs/technical/slide_stack.md`** — update:

- **Frontend — Components** table:
  - `ChapterSlide`: update description — remove "Skip" button mention
  - `QuizSlide`: update description — remove "Skip" button and "Next Slide" button mentions
- **Frontend — Services & Hooks** `useSlide` table:
  - `fetchNextSlide`: update signature to `fetchNextSlide(markChapterId?)` — uses internal bookId; optional chapter mark

#### API Documentation (`docs/api_doc/`)

No changes needed — no API endpoint changes.

### Chrome Claude Extension Execution

After implementation is complete, execute the E2E tests defined in `docs/chrome_test/260416_1000_slide_nav_arrows.md` by invoking:

```
/webapp-dev:chrome-test-execute docs/chrome_test/260416_1000_slide_nav_arrows.md
```

`feature-implement-full` will invoke this automatically. If running manually, execute that command after all frontend changes are complete and the dev server is running.

---

## Dependencies

- Slide Stack feature (all backend endpoints, `useSlide` hook, `SlidePage`, `ChapterSlide`, `QuizSlide`) — all complete and being modified.

## Open Questions

None.
