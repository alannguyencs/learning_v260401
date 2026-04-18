# Slide Stack — Technical Design

[< Prev: Revision Scheduling](./revision_scheduling.md) | [Parent](./index.md)

## Architecture

```
GET  /api/slides/current        → slide_navigation.get_current_slide(db, username, book_id)
POST /api/slides/forward        → slide_navigation.go_next(db, username, book_id, mark_chapter_id?)
POST /api/slides/back           → slide_navigation.go_previous(db, username)
POST /api/slides/chapters/{id}/learnt
                                → LearningProgressService.mark_chapter_learnt
                                → RevisionService.on_chapter_learnt
POST /api/slides/quizzes/{id}/respond
                                → auto-grade (MC) or QuizGrader.grade (open-ended)
                                → RevisionService.record_quiz_response
                                → crud_slide_position.save_feedback (persists feedback for history replay)
POST /api/slides/chat           → SlideChatService.answer (Gemini 2.5 Flash)
GET  /api/slides/chat           → get_chat_messages(username, slide_identifier)
POST   /api/slides/quizzes/{id}/like
                                → crud_slide_like.add_like
                                → RevisionService.apply_like_boost
DELETE /api/slides/quizzes/{id}/like
                                → crud_slide_like.remove_like
GET    /api/slides/likes        → crud_slide_like.get_liked_quiz_ids
```

## Data Model

**`UserSlidePosition`** (`slide_position`) — one row per user, stores current slide

| Column | Type | Constraints |
|--------|------|-------------|
| `username` | String | PK, FK → users.username |
| `slide_type` | String | NOT NULL — `'chapter'` or `'quiz'` |
| `slide_id` | Integer | NOT NULL |
| `lesson_id` | Integer | nullable |
| `round_num` | Integer | nullable |
| `feedback_json` | JSON | nullable — stored quiz feedback for history replay |
| `updated_at` | Timestamp | NOT NULL, DEFAULT NOW() |

**`SlideHistory`** (`slide_history`) — ordered stack of back/forward history

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | Integer | PK |
| `username` | String | FK → users.username, NOT NULL |
| `position` | Integer | NOT NULL — ordering index |
| `slide_type` | String | NOT NULL |
| `slide_id` | Integer | NOT NULL |
| `lesson_id` | Integer | nullable |
| `round_num` | Integer | nullable |
| `feedback_json` | JSON | nullable |
| `direction` | String | NOT NULL, DEFAULT `'back'` — `'back'` or `'forward'` |
| `created_at` | Timestamp | NOT NULL, DEFAULT NOW() |

Index: `(username, position)`

**`SlideChatMessage`** (`slide_chat_messages`)

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | Integer | PK |
| `username` | String | FK → users.username, NOT NULL |
| `slide_identifier` | String | NOT NULL — `"chapter:{id}"` or `"quiz:{id}"` |
| `role` | String | NOT NULL — `"user"` or `"assistant"` |
| `content` | Text | NOT NULL |
| `created_at` | Timestamp | NOT NULL, DEFAULT NOW() |

Index: `(username, slide_identifier, created_at)`

**`Lesson`** — added column:

| Column | Type | Constraints |
|--------|------|-------------|
| `raw_content` | Text | nullable — full paper text or YouTube transcript |

**`UserSlideLike`** (`user_slide_like`) — per-user quiz likes; drives the filled/outline Like-button UI and is the signal that triggers the forgetting-rate boost

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | Integer | PK |
| `username` | String | FK → users.username, NOT NULL |
| `quiz_id` | Integer | FK → chapter_quizzes.id, NOT NULL |
| `liked_at` | Timestamp | NOT NULL, DEFAULT NOW() |
| — | — | UNIQUE(`username`, `quiz_id`) |

Index: `idx_usl_user` on `(username)`.

**`quiz_skip_log`** — tracks skipped quizzes for back-of-queue ordering within tier 1

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | Integer | PK |
| `username` | String | FK → users.username, NOT NULL |
| `quiz_id` | Integer | FK → chapter_quizzes.id, NOT NULL |
| `lesson_id` | Integer | FK → lessons.id, NOT NULL |
| `round_num` | Integer | NOT NULL |
| `skipped_at` | Timestamp | NOT NULL, DEFAULT NOW() — updated on re-skip to push to back of queue |

## Pipeline

### GET /api/slides/current

```
slide_navigation.get_current_slide(db, username, book_id)
  │
  ├── get_position(db, username) → saved UserSlidePosition?
  │   └── If exists: rebuild SlideResult from saved position → return
  │
  └── No saved position: SlideSelector.get_next_slide(db, username, book_id)
        → save_position(db, username, ...) → return SlideResult
```

`SlideResult` now carries `has_previous` (depth of back-stack > 0) and `feedback` (from `feedback_json` when replaying history).

### POST /api/slides/forward — Advance

```
slide_navigation.go_next(db, username, book_id, mark_chapter_id?)
  │
  ├── is_new_action = mark_chapter_id provided and chapter not already learnt
  │
  ├── If is_new_action:
  │     clear_forward(db, username)   ← discard any forward stack
  │     mark_chapter_learnt + revision setup
  │     SlideSelector.get_next_slide → save_position → return
  │
  └── Not new action:
        fwd = pop_from_forward(db, username)
        If fwd: rebuild from fwd → update position → return (replay)
        Else: SlideSelector.get_next_slide → save_position → return (fresh)
```

### POST /api/slides/back — Go Back

```
slide_navigation.go_previous(db, username)
  │
  ├── crud_slide_position.go_back(db, username)
  │     ├── Check back-history exists (direction='back')
  │     ├── push current position → forward stack (direction='forward')
  │     ├── pop top of back-history (highest position)
  │     └── Update UserSlidePosition to prev_row (single commit)
  │
  └── Rebuild SlideResult from prev_row (including feedback_json)
        → has_previous = get_history_depth(db, username) > 0
```

### GET /api/slides/next — 2-Tier Algorithm (used internally)

```
SlideSelector.get_next_slide(db, username, book_id)
  │
  ├── lesson_count = get_lesson_count(db, username)
  │
  ├── TIER 1: due_rounds = get_due_rounds(db, username, lesson_count)
  │   ├── For each round: get_eligible_quiz_ids_for_round(db, username, lesson_id, round_num)
  │   │   └── Returns (non_skipped, skipped) — two groups of quiz IDs
  │   │
  │   ├── Group A (non-skipped): compute m(t), sort weakest first
  │   │   └── If any → return first as QuizSlide → done
  │   │
  │   └── Group B (skipped): ordered by skipped_at ASC (oldest skip first)
  │       └── If any → return first as QuizSlide → done
  │
  ├── TIER 2: no due revisions
  │   ├── If book_id: get_next_chapter_in_book(db, username, book_id)
  │   ├── Else: get_next_chapters_all_books(db, username) → random pick
  │   └── Return chapter as ChapterSlide → done
  │
  └── Both tiers empty → return 'none'
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
  │     Return { is_correct: null, good_points: null, bad_points: null, round_done }
  │
  ├── If quiz_type == 'multiple_choice':
  │     user_selections = sorted(user_answer.split(","))
  │     is_correct = (user_selections == sorted(correct_options))
  │     feedback = null
  │
  └── Else (open-ended):
        QuizGrader.grade(question, expected_answer, user_answer, quiz_type)
        → { good_points, bad_points }
        → is_correct = good_points / total >= 0.66
  │
  ├── remove_quiz_skip(db, username, quiz_id)
  ├── record_quiz_response(..., is_correct) → QuizResponseResult
  ├── crud_dashboard.log_quiz_answer(db, username, quiz_id, lesson_id, round_num, is_correct)  ← writes to quiz_answer_log
  └── Return { is_correct, good_points, bad_points, round_done }
```

### POST /api/slides/chat — Contextual AI Q&A

```
Body: { slide_type, chapter_id?, quiz_id?, message }
  │
  ▼
Build slide_identifier + load slide context
  ├── chapter: chapter.content
  └── quiz: quiz question + expected_answer + chapter.content
  │
  ▼
Load lesson.raw_content (may be NULL)
  │
  ▼
get_recent_chat_messages(username, slide_identifier, limit=10)
  │
  ▼
SlideChatService.answer(slide_context, raw_content, recent, message)
  → Gemini 2.5 Flash → response text
  │
  ▼
save_chat_message × 2 (user + assistant)
  │
  ▼
Return { response }
```

## API Layer

| Method | Path | Auth | Handler |
|--------|------|------|---------|
| GET | `/api/slides/current` | Session | `slide_current` |
| POST | `/api/slides/forward` | Session | `slide_forward` — body: `{ book_id, mark_chapter_id? }` |
| POST | `/api/slides/back` | Session | `slide_back` |
| POST | `/api/slides/chapters/{chapter_id}/learnt` | Session | `mark_chapter_learnt` |
| POST | `/api/slides/quizzes/{quiz_id}/respond` | Session | `respond_to_quiz` |
| POST | `/api/slides/chat` | Session | `slide_chat` |
| GET | `/api/slides/chat` | Session | `get_slide_chat_history` |
| POST | `/api/slides/quizzes/{quiz_id}/like` | Session | `like_quiz` — inserts like row + `RevisionService.apply_like_boost` |
| DELETE | `/api/slides/quizzes/{quiz_id}/like` | Session | `unlike_quiz` — deletes like row; does not restore rate |
| GET | `/api/slides/likes` | Session | `list_likes` — returns `{"quiz_ids": [...]}` newest-first |

## Service Layer

**`slide_navigation`** (`backend/src/service/slide_navigation.py`):

| Method | Description |
|--------|-------------|
| `get_current_slide(db, username, book_id)` | Returns saved position or computes fresh; never recomputes if saved |
| `go_next(db, username, book_id, mark_chapter_id)` | Clears forward on new action; replays forward stack or computes fresh |
| `go_previous(db, username)` | Pops back-history, pushes current to forward, rebuilds slide with saved feedback |

**`SlideSelector`** (`backend/src/service/slide_selector.py`):

| Method | Description |
|--------|-------------|
| `get_next_slide(db, username, book_id)` | Returns `SlideResult` using 2-tier algorithm |

**`RevisionService`** (`backend/src/service/revision_service.py`) — see [technical/revision_scheduling.md](./revision_scheduling.md) for full details. New entry:

| Method | Description |
|--------|-------------|
| `apply_like_boost(db, username, quiz_id, lesson_count)` | Sets `forgetting_rate = max(current, 1.0)` for a liked quiz; preserves `last_reviewed_lesson_count` |

**`SlideResult`** dataclass:

| Field | Type | Description |
|-------|------|-------------|
| `slide_type` | str | `'chapter'`, `'quiz'`, or `'none'` |
| `chapter` | dict \| None | Chapter data enriched with book/lesson info |
| `quiz` | dict \| None | Quiz data enriched with round/lesson/book info, including `section_name`, `quiz_take_away`, `quiz_metadata` |
| `has_previous` | bool | Whether back navigation is available (history depth > 0) |
| `feedback` | dict \| None | Stored quiz feedback when replaying history |

**`QuizGrader`** (`backend/src/service/quiz_grader.py`):

| Method | Description |
|--------|-------------|
| `grade(question, expected_answer, user_answer, quiz_type)` | Calls Gemini API with structured output, returns `GradingResult` |

**`GradingResult`** dataclass:

| Field | Type | Description |
|-------|------|-------------|
| `is_correct` | bool | Whether answer passed (good_points/total >= 0.66) |
| `good_points` | list[str] | Points the student got right |
| `bad_points` | list[str] | Points the student missed or got wrong |

**`SlideChatService`** (`backend/src/service/slide_chat_service.py`):

| Method | Description |
|--------|-------------|
| `answer(slide_context, raw_content, recent_messages, user_message)` | Builds prompt with context, calls Gemini, returns free-text response |

## LLM Requests Layer

**System prompt:** `backend/resources/prompts/quiz_grader.md` — concatenated with user message into a single prompt (Gemini does not use a separate system parameter)

**Model:** `gemini-2.5-flash`, temperature: 0.1

**User message structure:**
```
Quiz type: {quiz_type}
Question: {question}
Expected answer: {expected_answer}
Student answer: {user_answer}
```

**Output schema:** `GradingOutput` Pydantic model passed as `response_schema` parameter with `response_mime_type="application/json"` for guaranteed structured output:

```python
class GradingOutput(BaseModel):
    good_points: list[str]
    bad_points: list[str]
```

`is_correct` is computed from the threshold: `len(good_points) / max(total, 1) >= 0.66`.

### Slide Chat — SlideChatService.answer

**System prompt:** `backend/resources/prompts/slide_chat.md`

**Model:** `gemini-2.5-flash`, temperature: 0.3, free-text output

**Prompt structure:**
```
+----------------------------------------------------------+
|  SYSTEM PROMPT (slide_chat.md)                           |
|  - Learning assistant role                               |
|  - Answer based on context, be concise and educational   |
+----------------------------------------------------------+
|  USER PROMPT                                             |
|  +----------------------------------------------------+  |
|  | Lesson Source Material (raw_content, max 8000 ch)  |  |
|  +----------------------------------------------------+  |
|  | Current Slide Content (chapter or quiz fields)     |  |
|  +----------------------------------------------------+  |
|  | Recent Conversation (last 10 messages)             |  |
|  +----------------------------------------------------+  |
|  | User Question                                      |  |
|  +----------------------------------------------------+  |
+----------------------------------------------------------+
```

## CRUD Layer

**`crud_slide_position.py`:**

| Function | Description |
|----------|-------------|
| `get_position(db, username)` | Current `UserSlidePosition` row or None |
| `save_position(db, username, slide_type, slide_id, lesson_id, round_num)` | Upsert current; pushes old position to back-history first |
| `save_feedback(db, username, feedback_json)` | Update `feedback_json` on current position |
| `push_to_history(db, username, ..., direction)` | Insert a `SlideHistory` row |
| `get_history_depth(db, username)` | Count of `direction='back'` rows |
| `go_back(db, username)` | Atomic: push current to forward, pop prev from back, update position |
| `push_to_forward(db, username, ...)` | Insert a `direction='forward'` history row |
| `pop_from_forward(db, username)` | Remove and return highest-position forward row |
| `clear_forward(db, username)` | Delete all `direction='forward'` rows for user |

**`crud_slides.py`:**

| Function | Description |
|----------|-------------|
| `get_next_chapter_in_book(username, book_id)` | First unlearnt chapter in book order |
| `get_next_chapters_all_books(username)` | One unlearnt chapter per book |
| `get_eligible_quiz_ids_for_round(username, lesson_id, round_num)` | Not-answered, not-skipped quiz IDs |
| `get_eligible_quiz_ids_for_round(username, lesson_id, round_num)` | Returns (non_skipped, skipped) quiz IDs not yet answered |
| `log_quiz_skip(username, quiz_id, lesson_id, round_num)` | Insert or refresh skip (updates skipped_at to push to back of queue) |
| `remove_quiz_skip(username, quiz_id)` | Delete skip log row when quiz is answered |

**`crud_slide_chat.py`:**

| Function | Description |
|----------|-------------|
| `get_chat_messages(username, slide_identifier)` | All messages for user+slide, ordered ASC |
| `get_recent_chat_messages(username, slide_identifier, limit)` | Last N messages for context |
| `save_chat_message(username, slide_identifier, role, content)` | Insert one message row |

**`crud_slide_like.py`:**

| Function | Description |
|----------|-------------|
| `add_like(username, quiz_id)` | `INSERT ... ON CONFLICT DO NOTHING` — idempotent |
| `remove_like(username, quiz_id)` | `DELETE` the row; no-op if absent |
| `is_liked(username, quiz_id)` | Boolean lookup |
| `get_liked_quiz_ids(username)` | List of liked `quiz_id`s, newest first |

## Frontend — Pages & Routes

| Path | Component | Auth | Description |
|------|-----------|------|-------------|
| `/slides` | `SlidePage` | Required | Main slide view; renders chapter or quiz slide |

## Frontend — Components

| Component | File | Responsibility |
|-----------|------|----------------|
| `SlidePage` | `frontend/src/pages/SlidePage.jsx` | Orchestrates `useSlide`, renders correct sub-component |
| `BookSelector` | `frontend/src/components/BookSelector.jsx` | Fetches book list, dropdown to filter slides by book |
| `ChapterSlide` | `frontend/src/components/ChapterSlide.jsx` | Renders markdown chapter + Mark as Learnt button |
| `QuizSlide` | `frontend/src/components/QuizSlide.jsx` | Renders quiz by format: cloze (fill-in-blank), free_recall/teach_back (text area + key-points checklist), MC single-correct (radio buttons) / MC multi-correct (checkboxes + "Select all that apply"); feedback shows all options: wrong pick = red, correct = green; shows section_name badge and quiz_take_away in feedback; no Skip or Next Slide buttons (navigation handled by down arrow) |
| `AllCaughtUp` | `frontend/src/components/AllCaughtUp.jsx` | Empty-state message when no slides remain |
| `ChatButton` | `frontend/src/components/ChatButton.jsx` | Floating FAB at bottom-right, toggles ChatPanel |
| `ChatPanel` | `frontend/src/components/ChatPanel.jsx` | Chat drawer with message bubbles, input, markdown rendering |
| `LikeButton` | `frontend/src/components/LikeButton.jsx` | Thumbs-up FAB above `ChatButton` on quiz slides; filled (blue) when liked, outline (gray) when not; calls `toggleLike` from `useLikedQuizzes` |

## Frontend — Services & Hooks

**`useSlide`** (`frontend/src/hooks/useSlide.js`):

| Method / State | Description |
|----------------|-------------|
| `hasPrevious` | Boolean state — true when back navigation is available |
| `loadCurrent(bookId)` | GET `/api/slides/current`; called on mount |
| `fetchNextSlide(markChapterId?)` | POST `/api/slides/forward`; uses internal `bookId` state; optional `mark_chapter_id` when chapter id passed |
| `markLearnt(chapterId)` | POST `/api/slides/forward` with `mark_chapter_id`; records progress and advances |
| `goPrevious()` | POST `/api/slides/back`; restores previous slide with saved feedback |
| `submitAnswer(quizId, body)` | POST respond; sets `submitting=true` during request, stores `feedback` state (no advance) |
| `skipItem(quizId, body)` | POST respond with `is_skip=true`; calls `fetchNextSlide` after |
| `selectBook(bookId)` | Sets `bookId`; calls `loadCurrent` |

**`api.js`** additions (`frontend/src/services/api.js`):

| Method | Endpoint |
|--------|----------|
| `listBooks()` | GET `/api/content/books` |
| `getCurrentSlide(bookId)` | GET `/api/slides/current?book_id=bookId` |
| `slideForward(body)` | POST `/api/slides/forward` — body: `{ book_id, mark_chapter_id? }` |
| `slideBack()` | POST `/api/slides/back` |
| `markChapterLearnt(chapterId)` | POST `/api/slides/chapters/{id}/learnt` |
| `respondToQuiz(quizId, body)` | POST `/api/slides/quizzes/{id}/respond` |
| `sendChatMessage(body)` | POST `/api/slides/chat` |
| `getChatHistory(slideType, chapterId, quizId)` | GET `/api/slides/chat` |
| `likeQuiz(quizId)` | POST `/api/slides/quizzes/{id}/like` |
| `unlikeQuiz(quizId)` | DELETE `/api/slides/quizzes/{id}/like` |
| `listLikedQuizzes()` | GET `/api/slides/likes` |

**`useSlideChat`** (`frontend/src/hooks/useSlideChat.js`):

| Method | Description |
|--------|-------------|
| `messages` | Array of `{ role, content, created_at }` |
| `loading` | Boolean — true while waiting for AI response |
| `sendMessage(text)` | POST chat, append user msg + AI response to state |

**`useLikedQuizzes`** (`frontend/src/hooks/useLikedQuizzes.js`):

| Method / State | Description |
|----------------|-------------|
| `likedIds` | `Set<number>` of quizzes the current user has liked |
| `loading` | Boolean — true until initial `GET /api/slides/likes` resolves |
| `isLiked(quizId)` | Returns whether the quiz is in `likedIds` |
| `toggleLike(quizId)` | Optimistic flip of the like set; calls `likeQuiz`/`unlikeQuiz`; rolls back on error |

## Component Checklist

- [x] Migration — `scripts/sql/008_slide_position.sql`
- [x] Migration — `scripts/sql/009_slide_history.sql`
- [x] Models — `backend/src/models/slide_position.py` (`UserSlidePosition`, `SlideHistory`)
- [x] CRUD — `backend/src/crud/crud_slide_position.py`
- [x] Service — `backend/src/service/slide_navigation.py`
- [x] API endpoints — `backend/src/api/slides.py` (GET /current, POST /forward, POST /back)
- [x] Schemas — `backend/src/schemas/slides.py` (`SlideResponse.has_previous`, `SlideResponse.feedback`, `SlideForwardRequest`)
- [x] Tests — `backend/tests/test_crud_slide_position.py`
- [x] Tests — `backend/tests/test_slide_navigation.py`
- [x] Hook — `frontend/src/hooks/useSlide.js` (`hasPrevious`, `loadCurrent`, `goPrevious`)
- [x] Page — `frontend/src/pages/SlidePage.jsx` (up/down navigation arrows)
- [x] API methods — `frontend/src/services/api.js` (`getCurrentSlide`, `slideForward`, `slideBack`)
- [x] Tests — `frontend/src/__tests__/hooks/useSlide.test.js`
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
- [x] Hook — `frontend/src/hooks/useSlide.js`
- [x] Page — `frontend/src/pages/SlidePage.jsx`
- [x] Component — `frontend/src/components/BookSelector.jsx`
- [x] Component — `frontend/src/components/ChapterSlide.jsx`
- [x] Component — `frontend/src/components/QuizSlide.jsx` (format-specific UI: cloze, free_recall, teach_back, MC)
- [x] Component — `frontend/src/components/AllCaughtUp.jsx`
- [x] Route — `frontend/src/App.js` (`/slides` → `SlidePage`)
- [x] API methods — `frontend/src/services/api.js`
- [x] Tests — `frontend/src/__tests__/components/ChapterSlide.test.js`
- [x] Tests — `frontend/src/__tests__/components/QuizSlide.test.js`
- [x] Tests — `frontend/src/__tests__/hooks/useSlide.test.js`
- [x] Migration — `scripts/sql/007_slide_chat.sql`
- [x] Model — `backend/src/models/slide_chat.py` (`SlideChatMessage`)
- [x] Model update — `backend/src/models/content.py` (`Lesson.raw_content`)
- [x] CRUD — `backend/src/crud/crud_slide_chat.py`
- [x] Service — `backend/src/service/slide_chat_service.py`
- [x] System prompt — `backend/resources/prompts/slide_chat.md`
- [x] Schemas — `backend/src/schemas/slides.py` (chat request/response)
- [x] API — `backend/src/api/slides.py` (POST/GET `/slides/chat`)
- [x] Tests — `backend/tests/test_slide_chat_api.py`
- [x] Tests — `backend/tests/test_slide_chat_service.py`
- [x] Tests — `backend/tests/test_crud_slide_chat.py`
- [x] Hook — `frontend/src/hooks/useSlideChat.js`
- [x] Component — `frontend/src/components/ChatButton.jsx`
- [x] Component — `frontend/src/components/ChatPanel.jsx`
- [x] Page update — `frontend/src/pages/SlidePage.jsx` (ChatButton overlay)
- [x] API methods — `frontend/src/services/api.js` (chat methods)
- [x] Tests — `frontend/src/__tests__/components/SlideChat.test.js`
- [x] Tests — `frontend/src/__tests__/hooks/useSlideChat.test.js`
- [x] Migration — `scripts/sql/010_user_slide_like.sql`
- [x] Model — `backend/src/models/slide_like.py` (`UserSlideLike`)
- [x] CRUD — `backend/src/crud/crud_slide_like.py`
- [x] Service — `backend/src/service/revision_service.py` (`apply_like_boost`)
- [x] API — `backend/src/api/slides.py` (POST/DELETE `/like`, GET `/likes`)
- [x] Schemas — `backend/src/schemas/slides.py` (`LikeResponse`, `LikeListResponse`)
- [x] Tests — `backend/tests/test_crud_slide_like.py`
- [x] Tests — `backend/tests/test_revision_service.py` (`apply_like_boost`)
- [x] Tests — `backend/tests/test_slide_selector.py` (liked quiz surfaces first)
- [x] Tests — `backend/tests/test_slides_api.py` (like endpoints)
- [x] Hook — `frontend/src/hooks/useLikedQuizzes.js`
- [x] Component — `frontend/src/components/LikeButton.jsx`
- [x] Page update — `frontend/src/pages/SlidePage.jsx` (`LikeButton` on quiz slides)
- [x] API methods — `frontend/src/services/api.js` (`likeQuiz` / `unlikeQuiz` / `listLikedQuizzes`)
- [x] Tests — `frontend/src/__tests__/components/LikeButton.test.js`
- [x] Tests — `frontend/src/__tests__/hooks/useLikedQuizzes.test.js`

---

[< Prev: Revision Scheduling](./revision_scheduling.md) | [Parent](./index.md)
