# Frontend Slides — Slide View UI

**Feature**: Slide view page with chapter and quiz slide components, book selector, and session state
**Plan Created:** 2026-03-30
**Status:** Plan
**Reference**:
- [Source spec](../learning_strategy.md#75-user-interactions)
- [Abstract — Slide Stack](../abstract/slide_stack.md)
- [Technical — Slide Stack](../technical/slide_stack.md)
- [Depends on: Plan 4](./260330_slide_selection_api.md)

---

## Problem Statement

1. After authentication, the user lands on a blank page. There is no slide view or learning interface.
2. The backend slide API (Plan 4) is fully implemented but has no frontend consumer.
3. Users need to select books, view chapter content, answer quizzes, and see AI feedback — all in one continuous flow.

---

## Proposed Solution

Build a single `/slides` page (`SlidePage`) that fetches and displays one slide at a time. Two sub-components handle chapter slides (`ChapterSlide`) and quiz slides (`QuizSlide`). A `BookSelector` component lets the user filter to a specific book or study all books. A `useSlide` custom hook manages all state and API calls.

**User-facing flow:**
```
User logs in → redirected to /slides
  │
  ▼
BookSelector: All Books | Select a book
  │
  ▼
SlidePage polls GET /api/slides/next
  │
  ├── Chapter slide:
  │     Display markdown content
  │     Buttons: [Mark as Learnt]  [Skip]
  │
  └── Quiz slide:
        Display question (+ options for MC)
        Input: text area (open-ended) or radio buttons (MC)
        Buttons: [Submit Answer]  [Skip]
        After submission: show is_correct + AI feedback
        Button: [Next Slide]
```

---

## Current Implementation Analysis

### What Exists (keep as-is)

| Component | File | Status |
|-----------|------|--------|
| Login page | `frontend/src/pages/Login.jsx` | Keep — auth |
| AuthContext | `frontend/src/contexts/AuthContext.js` | Keep — auth |
| ProtectedRoute | `frontend/src/components/ProtectedRoute.jsx` | Keep — auth |
| Auth API methods | `frontend/src/services/api.js` | Keep — will add slide methods |
| App.js | `frontend/src/App.js` | Keep — will add `/slides` route |

### What Changes

| Component | Current | Proposed |
|-----------|---------|----------|
| `frontend/src/App.js` | `/login` + `/` redirect | Also add `/slides` route; redirect `/` to `/slides` after login |
| `frontend/src/services/api.js` | Auth methods only | Also add `getNextSlide`, `markChapterLearnt`, `respondToQuiz`, `listBooks` |

---

## Implementation Plan

### Key Workflow

```
SlidePage mounts → useSlide.fetchNextSlide()
  │
  ▼
GET /api/slides/next?book_id=optional
  │
  ├── slide_type=chapter → render ChapterSlide
  │     [Mark as Learnt] → POST /api/slides/chapters/{id}/learnt
  │                          → useSlide.fetchNextSlide()
  │     [Skip] → useSlide.fetchNextSlide() (chapter skipped, no API call needed)
  │
  ├── slide_type=quiz → render QuizSlide
  │     User fills answer
  │     [Submit Answer] → POST /api/slides/quizzes/{id}/respond
  │                          → Show feedback panel (is_correct + feedback text)
  │                          → [Next Slide] → useSlide.fetchNextSlide()
  │     [Skip] → POST /api/slides/quizzes/{id}/respond { is_skip: true }
  │                → useSlide.fetchNextSlide()
  │
  └── slide_type=none → render AllCaughtUp message
```

### Database Schema

#### To Delete
None.

#### To Update
None.

#### To Add New
None — all DB changes were in Plans 1–4.

### CRUD

#### To Delete
None.

#### To Update
None.

#### To Add New
None — all CRUD is in Plans 1–4.

### Services

#### To Delete
None.

#### To Update
None.

#### To Add New
None — all backend services are in Plans 1–4.

### API Endpoints

#### To Delete
None.

#### To Update
None.

#### To Add New
None — all endpoints are in Plan 4.

### Testing

#### To Delete
None.

#### To Update
None.

#### To Add New

File: `frontend/src/__tests__/components/ChapterSlide.test.js`
- `renders chapter title and content` — markdown rendered
- `calls markLearnt on button click` — API call triggered
- `shows skip button` — skip available

File: `frontend/src/__tests__/components/QuizSlide.test.js`
- `renders MC options as radio buttons`
- `renders text area for free_recall type`
- `shows feedback panel after submit`
- `Next Slide button appears after feedback shown`
- `skip triggers quiz respond with is_skip=true`

File: `frontend/src/__tests__/hooks/useSlide.test.js`
- `fetchNextSlide sets chapter slide state`
- `fetchNextSlide sets quiz slide state`
- `fetchNextSlide sets allCaughtUp=true on none`
- `after markLearnt, fetchNextSlide is called`

Pre-commit loop:
1. Run `pre-commit run --all-files`
2. Fix lint/Prettier issues; if any component exceeds 300 lines, extract sub-components
3. Repeat until clean

### Frontend

#### To Delete
None.

#### To Update

- `frontend/src/App.js`:
  - Import `SlidePage`
  - Add route: `<Route path="/slides" element={<ProtectedRoute><SlidePage /></ProtectedRoute>} />`
  - Change `/` redirect from `/login` to `/slides`

- `frontend/src/services/api.js`:
  - Add `listBooks()` → GET `/api/content/books`
  - Add `getNextSlide(bookId)` → GET `/api/slides/next?book_id=bookId`
  - Add `markChapterLearnt(chapterId)` → POST `/api/slides/chapters/{id}/learnt`
  - Add `respondToQuiz(quizId, body)` → POST `/api/slides/quizzes/{id}/respond`

#### To Add New

**`frontend/src/hooks/useSlide.js`**

State managed: `{ slide, loading, error, feedback, bookId }`

```
useSlide()
  → fetchNextSlide(bookId)    calls getNextSlide, updates slide state
  → markLearnt(chapterId)     calls markChapterLearnt, then fetchNextSlide
  → submitAnswer(quizId, body) calls respondToQuiz, stores feedback, waits for Next
  → skipItem(quizId, body)    calls respondToQuiz with is_skip=true, then fetchNextSlide
  → selectBook(bookId)        sets bookId, calls fetchNextSlide
```

**`frontend/src/pages/SlidePage.jsx`**

Layout:
```
┌─────────────────────────────────────────┐
│  [BookSelector]              All Books  │
├─────────────────────────────────────────┤
│                                         │
│   [ChapterSlide] or [QuizSlide]         │
│                                         │
│   [AllCaughtUp message if none]         │
│                                         │
└─────────────────────────────────────────┘
```

**`frontend/src/components/BookSelector.jsx`**

A dropdown that fetches books on mount (GET `/api/content/books`) and renders:
- "All Books" (default)
- One option per book (book_id → title)

On change: calls `useSlide.selectBook(bookId)`

**`frontend/src/components/ChapterSlide.jsx`**

Displays:
- Breadcrumb: `{book_title} › {lesson_title} › Chapter {chapter_index}`
- Markdown content rendered with `react-markdown` (already available or add as dependency)
- Footer: `[Skip Chapter]`  `[Mark as Learnt]`

**`frontend/src/components/QuizSlide.jsx`**

Displays:
- Header: `Revision R{round_num} · {lesson_title} · {book_title}`
- Question text
- Input area (conditional on `quiz_type`):
  - `multiple_choice`: 4 radio buttons (A/B/C/D)
  - `free_recall`, `teach_back`, `cloze`: textarea for typed answer
- Before submission: `[Skip]`  `[Submit Answer]`
- After submission:
  - Result badge: ✓ Correct (green) or ✗ Incorrect (red)
  - AI feedback text (italic)
  - `[Next Slide]` button

**`frontend/src/components/AllCaughtUp.jsx`**

Shown when `slide_type === 'none'`. Displays a congratulations message and encourages the user to check back later.

### Documentation

#### Abstract (`docs/abstract/`)

- **Create** `docs/abstract/slide_stack.md`:
  - Status: Plan
  - Problem: no learning interface; users can't consume content or get tested
  - Solution: continuous slide stream combining chapter study + spaced-repetition quizzes
  - User Flow: full walkthrough from book selection to quiz feedback
  - Scope: included/not included
  - Acceptance Criteria: all 7.5 user interactions from the spec

- **Update** `docs/abstract/index.md`:
  - Add row 2: Slide Stack (after Authentication)

#### Technical (`docs/technical/`)

- **Update** `docs/technical/slide_stack.md` (created in Plan 4):
  - Add `Frontend — Pages & Routes` section: `SlidePage` at `/slides`
  - Add `Frontend — Components` section: all 5 components with responsibilities
  - Add `Frontend — Services & Hooks` section: `useSlide`, `api.js` additions
  - Complete the Component Checklist with all frontend items

- **Update** `docs/technical/system_pipelines.md`:
  - Add `Slide Selection Pipeline` section
  - Add `Chapter Learnt Pipeline` section
  - Add `Quiz Response Pipeline` section

- **Update** `docs/technical/index.md`:
  - Already updated in Plan 4 for `slide_stack.md`; no further change needed

### Chrome Claude Extension Execution

After implementation is complete, execute the Chrome Claude Extension E2E tests defined in `docs/chrome_test/slide_stack.md`.

---

## Dependencies

- Plan 4 (`260330_slide_selection_api.md`) — all three API endpoints must be live.
- `react-markdown` npm package — for rendering chapter content.

## Open Questions

None.
