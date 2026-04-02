# Slide Stack — Technical Design

[< Prev: Revision Scheduling](./revision_scheduling.md) | [Parent](./index.md)

## Architecture

```
GET  /api/slides/next           → SlideSelector.get_next_slide(db, username, book_id)
POST /api/slides/chapters/{id}/learnt
                                → LearningProgressService.mark_chapter_learnt
                                → RevisionService.on_chapter_learnt
POST /api/slides/quizzes/{id}/respond
                                → auto-grade (MC) or QuizGrader.grade (open-ended)
                                → RevisionService.record_quiz_response
POST /api/slides/chat           → SlideChatService.answer (Gemini 2.5 Flash)
GET  /api/slides/chat           → get_chat_messages(username, slide_identifier)
```

## Data Model

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

**`quiz_skip_log`**

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | Integer | PK |
| `username` | String | FK → users.username, NOT NULL |
| `quiz_id` | Integer | FK → chapter_quizzes.id, NOT NULL |
| `lesson_id` | Integer | FK → lessons.id, NOT NULL |
| `round_num` | Integer | NOT NULL |
| `skipped_at` | Timestamp | NOT NULL, DEFAULT NOW() |

## Pipeline

### GET /api/slides/next — 3-Tier Algorithm

```
SlideSelector.get_next_slide(db, username, book_id)
  │
  ├── lesson_count = get_lesson_count(db, username)
  │
  ├── TIER 1: due_rounds = get_due_rounds(db, username, lesson_count)
  │   ├── For each round: get_eligible_quiz_ids_for_round(db, username, lesson_id, round_num)
  │   ├── For each quiz: compute m(t) using UserQuizRecall.forgetting_rate
  │   ├── Sort ascending by m(t) (weakest first, lowest m(t) = worst recall)
  │   └── Return first quiz as QuizSlide → done
  │
  ├── TIER 2: no due revisions
  │   ├── If book_id: get_next_chapter_in_book(db, username, book_id)
  │   ├── Else: get_next_chapters_all_books(db, username) → random pick
  │   └── Return chapter as ChapterSlide → done
  │
  └── TIER 3: no unlearnt chapters
      ├── get_skipped_quizzes(db, username) → ordered by skipped_at ASC
      └── Return first as QuizSlide or 'none'
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
  │     Return { is_correct: null, feedback: null, round_done }
  │
  ├── If quiz_type == 'multiple_choice':
  │     is_correct = (user_answer in correct_options)
  │     feedback = null
  │
  └── Else (open-ended):
        QuizGrader.grade(question, expected_answer, user_answer, quiz_type)
        → { is_correct, feedback }
  │
  ├── remove_quiz_skip(db, username, quiz_id)
  ├── record_quiz_response(..., is_correct) → QuizResponseResult
  ├── crud_dashboard.log_quiz_answer(db, username, quiz_id, lesson_id, round_num, is_correct)  ← writes to quiz_answer_log
  └── Return { is_correct, feedback, round_done }
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
| GET | `/api/slides/next` | Session | `get_next_slide` |
| POST | `/api/slides/chapters/{chapter_id}/learnt` | Session | `mark_chapter_learnt` |
| POST | `/api/slides/quizzes/{quiz_id}/respond` | Session | `respond_to_quiz` |
| POST | `/api/slides/chat` | Session | `slide_chat` |
| GET | `/api/slides/chat` | Session | `get_slide_chat_history` |

## Service Layer

**`SlideSelector`** (`backend/src/service/slide_selector.py`):

| Method | Description |
|--------|-------------|
| `get_next_slide(db, username, book_id)` | Returns `SlideResult` using 3-tier algorithm |

**`SlideResult`** dataclass:

| Field | Type | Description |
|-------|------|-------------|
| `slide_type` | str | `'chapter'`, `'quiz'`, or `'none'` |
| `chapter` | dict \| None | Chapter data enriched with book/lesson info |
| `quiz` | dict \| None | Quiz data enriched with round/lesson/book info, including `section_name`, `quiz_take_away`, `quiz_metadata` |

**`QuizGrader`** (`backend/src/service/quiz_grader.py`):

| Method | Description |
|--------|-------------|
| `grade(question, expected_answer, user_answer, quiz_type)` | Calls Gemini API with structured output, returns `GradingResult` |

**`GradingResult`** dataclass:

| Field | Type | Description |
|-------|------|-------------|
| `is_correct` | bool | Whether answer is correct |
| `feedback` | str | One-sentence explanation |

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
    is_correct: bool
    feedback: str
```

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

**`crud_slides.py`:**

| Function | Description |
|----------|-------------|
| `get_next_chapter_in_book(username, book_id)` | First unlearnt chapter in book order |
| `get_next_chapters_all_books(username)` | One unlearnt chapter per book |
| `get_eligible_quiz_ids_for_round(username, lesson_id, round_num)` | Not-answered, not-skipped quiz IDs |
| `log_quiz_skip(username, quiz_id, lesson_id, round_num)` | Insert skip log row (idempotent) |
| `remove_quiz_skip(username, quiz_id)` | Delete skip log row on answer |
| `get_skipped_quizzes(username)` | Skipped quizzes ordered by skipped_at ASC |

**`crud_slide_chat.py`:**

| Function | Description |
|----------|-------------|
| `get_chat_messages(username, slide_identifier)` | All messages for user+slide, ordered ASC |
| `get_recent_chat_messages(username, slide_identifier, limit)` | Last N messages for context |
| `save_chat_message(username, slide_identifier, role, content)` | Insert one message row |

## Frontend — Pages & Routes

| Path | Component | Auth | Description |
|------|-----------|------|-------------|
| `/slides` | `SlidePage` | Required | Main slide view; renders chapter or quiz slide |

## Frontend — Components

| Component | File | Responsibility |
|-----------|------|----------------|
| `SlidePage` | `frontend/src/pages/SlidePage.jsx` | Orchestrates `useSlide`, renders correct sub-component |
| `BookSelector` | `frontend/src/components/BookSelector.jsx` | Fetches book list, dropdown to filter slides by book |
| `ChapterSlide` | `frontend/src/components/ChapterSlide.jsx` | Renders markdown chapter + Mark as Learnt / Skip buttons |
| `QuizSlide` | `frontend/src/components/QuizSlide.jsx` | Renders quiz by format: cloze (fill-in-blank), free_recall/teach_back (text area + key-points checklist), MC (feedback shows only user pick + correct option: wrong pick = red, correct = green); shows section_name badge and quiz_take_away in feedback |
| `AllCaughtUp` | `frontend/src/components/AllCaughtUp.jsx` | Empty-state message when no slides remain |
| `ChatButton` | `frontend/src/components/ChatButton.jsx` | Floating FAB at bottom-right, toggles ChatPanel |
| `ChatPanel` | `frontend/src/components/ChatPanel.jsx` | Chat drawer with message bubbles, input, markdown rendering |

## Frontend — Services & Hooks

**`useSlide`** (`frontend/src/hooks/useSlide.js`):

| Method | Description |
|--------|-------------|
| `fetchNextSlide(bookId)` | GET `/api/slides/next`; updates `slide` state |
| `markLearnt(chapterId)` | POST mark-learnt; calls `fetchNextSlide` after |
| `submitAnswer(quizId, body)` | POST respond; stores `feedback` state (no advance) |
| `skipItem(quizId, body)` | POST respond with `is_skip=true`; calls `fetchNextSlide` after |
| `selectBook(bookId)` | Sets `bookId`; calls `fetchNextSlide` |

**`api.js`** additions (`frontend/src/services/api.js`):

| Method | Endpoint |
|--------|----------|
| `listBooks()` | GET `/api/content/books` |
| `getNextSlide(bookId)` | GET `/api/slides/next?book_id=bookId` |
| `markChapterLearnt(chapterId)` | POST `/api/slides/chapters/{id}/learnt` |
| `respondToQuiz(quizId, body)` | POST `/api/slides/quizzes/{id}/respond` |
| `sendChatMessage(body)` | POST `/api/slides/chat` |
| `getChatHistory(slideType, chapterId, quizId)` | GET `/api/slides/chat` |

**`useSlideChat`** (`frontend/src/hooks/useSlideChat.js`):

| Method | Description |
|--------|-------------|
| `messages` | Array of `{ role, content, created_at }` |
| `loading` | Boolean — true while waiting for AI response |
| `sendMessage(text)` | POST chat, append user msg + AI response to state |

## Component Checklist

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

---

[< Prev: Revision Scheduling](./revision_scheduling.md) | [Parent](./index.md)
