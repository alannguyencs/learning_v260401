# Slide Chat — Contextual AI Q&A on Slides

**Feature**: Floating chat icon on each slide enabling contextual AI Q&A with lesson/chapter/quiz context
**Plan Created:** 2026-04-02
**Status:** Plan
**Reference**:
- [Abstract — Slide Stack](../abstract/slide_stack.md)
- [Technical — Slide Stack](../technical/slide_stack.md)
- [Technical — Content Upload](../technical/content_upload.md)

---

## Problem Statement

1. Users studying chapter content or reviewing quiz questions often have follow-up questions — e.g., "Why is this concept important?", "Can you explain this differently?", "How does this relate to the previous chapter?"
2. There is no in-context way to ask questions while studying. The user would need to leave the app and use an external tool, losing context.
3. The raw lesson data (full paper text or YouTube transcript) is stored only in local JSON files (`data/metadata/`), not in PostgreSQL. This rich source material cannot be leveraged at runtime.
4. There is no conversation storage — even if a chat were added, previous questions would be lost on refresh.

---

## Proposed Solution

Add a floating chat icon at the bottom-right of every slide (chapter and quiz). Clicking it opens a chat panel where the user can type questions. The backend receives the question and assembles rich context:

1. **Current slide content** — chapter markdown or quiz question/expected answer
2. **Parent chapter content** — for quiz slides, the chapter the quiz belongs to
3. **Lesson raw data** — the full transcript/paper text stored in a new `raw_content` column on the `lessons` table
4. **Recent conversation history** — last N messages for this user on this slide (from a new `slide_chat_messages` table)

This context + the user's question is sent to Gemini 2.5 Flash, which returns a contextual answer. Both the question and answer are persisted so the user can revisit them.

```
User clicks chat icon on slide
  │
  ▼
Chat panel opens (loads recent messages from DB)
  │
  ▼
User types question → POST /api/slides/chat
  │
  ▼
Backend loads context:
  ├── slide content (chapter.content or quiz fields)
  ├── chapter content (for quiz slides: parent chapter)
  ├── lesson raw_content (from lessons table)
  └── recent chat messages (last 10 for this slide)
  │
  ▼
Gemini 2.5 Flash generates answer
  │
  ▼
Save user message + AI response to slide_chat_messages
  │
  ▼
Return AI response to frontend → display in chat panel
```

---

## Current Implementation Analysis

### What Exists (keep as-is)

| Component | File | Status |
|-----------|------|--------|
| Slide API (next, learnt, respond) | `backend/src/api/slides.py` | Keep — add new chat endpoint alongside existing ones |
| SlideSelector service | `backend/src/service/slide_selector.py` | Keep — unchanged |
| QuizGrader (Gemini) | `backend/src/service/quiz_grader.py` | Keep — reference pattern for Gemini calls |
| Lesson model | `backend/src/models/content.py` | Keep — extend with `raw_content` column |
| SlidePage | `frontend/src/pages/SlidePage.jsx` | Keep — add ChatButton overlay |
| ChapterSlide / QuizSlide | `frontend/src/components/` | Keep — unchanged |
| useSlide hook | `frontend/src/hooks/useSlide.js` | Keep — unchanged |
| api.js | `frontend/src/services/api.js` | Keep — add chat methods |
| configs.py | `backend/src/configs.py` | Keep — already has `gemini_api_key` |

### What Changes

| Component | Current | Proposed |
|-----------|---------|----------|
| `lessons` table | No raw content column | Add `raw_content TEXT` column |
| `Lesson` model | No `raw_content` field | Add `raw_content = Column(Text)` |
| Upload pipeline | Does not store raw content | Reads `content` or `transcript` from metadata JSON and sends to API |
| `POST /api/content/lessons` | Accepts `book_id, lesson_index, title` | Also accepts optional `raw_content` field |
| `SlidePage.jsx` | Renders slides only | Adds floating chat button + chat panel overlay |
| `api.js` | No chat endpoints | Adds `sendChatMessage()` and `getChatHistory()` |

---

## Implementation Plan

### Key Workflow

#### To Delete
None.

#### To Update
None.

#### To Add New

**Chat request pipeline:**

```
POST /api/slides/chat
Body: { slide_type, chapter_id?, quiz_id?, message }
  │
  ▼
authenticate user (session cookie)
  │
  ▼
Load slide context:
  ├── If slide_type == "chapter":
  │     chapter = get_chapter(chapter_id)
  │     lesson = get_lesson(chapter.lesson_id)
  │     slide_context = chapter.content
  │     slide_identifier = "chapter:{chapter_id}"
  │
  └── If slide_type == "quiz":
        quiz = get_chapter_quiz(quiz_id)
        chapter = get_chapter(quiz.chapter_id)
        lesson = get_lesson_by_chapter(quiz.chapter_id)
        slide_context = quiz question + expected_answer + chapter.content
        slide_identifier = "quiz:{quiz_id}"
  │
  ▼
raw_content = lesson.raw_content (may be NULL)
  │
  ▼
recent_messages = get_recent_chat_messages(username, slide_identifier, limit=10)
  │
  ▼
SlideChatService.answer(slide_context, raw_content, recent_messages, user_message)
  → Gemini 2.5 Flash → response text
  │
  ▼
save_chat_message(username, slide_identifier, role="user", content=user_message)
save_chat_message(username, slide_identifier, role="assistant", content=response)
  │
  ▼
Return { response: "..." }
```

**Chat history retrieval:**

```
GET /api/slides/chat?slide_type=chapter&chapter_id=5
  │
  ▼
authenticate user → build slide_identifier
  │
  ▼
get_chat_messages(username, slide_identifier)
  │
  ▼
Return [ { role, content, created_at }, ... ]
```

### Database Schema

#### To Delete
None.

#### To Update

**Migration `scripts/sql/007_slide_chat.sql`:**

```sql
-- Add raw_content column to lessons table
ALTER TABLE lessons ADD COLUMN IF NOT EXISTS raw_content TEXT;

-- Create slide chat messages table
CREATE TABLE IF NOT EXISTS slide_chat_messages (
    id SERIAL PRIMARY KEY,
    username VARCHAR NOT NULL REFERENCES users(username),
    slide_identifier VARCHAR NOT NULL,
    role VARCHAR NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_slide_chat_messages_lookup
    ON slide_chat_messages (username, slide_identifier, created_at);
```

**`slide_identifier`** is a string like `"chapter:42"` or `"quiz:17"` — a composite key that ties messages to a specific slide without separate FK columns.

**Column descriptions:**

| Column | Type | Description |
|--------|------|-------------|
| `id` | Serial PK | Auto-increment primary key |
| `username` | VARCHAR FK | The user who sent/received the message |
| `slide_identifier` | VARCHAR | Slide key: `"chapter:{id}"` or `"quiz:{id}"` |
| `role` | VARCHAR | `"user"` or `"assistant"` |
| `content` | TEXT | Message text |
| `created_at` | TIMESTAMP | When the message was created |

**ORM model:** `backend/src/models/slide_chat.py`

#### To Add New

**`backend/src/models/slide_chat.py`** — `SlideChatMessage` SQLAlchemy model.

**Update `backend/src/models/content.py`** — Add `raw_content = Column(Text)` to `Lesson` class.

### CRUD

#### To Delete
None.

#### To Update

**`backend/src/crud/crud_content.py`:**
- Update `create_lesson()` to accept optional `raw_content` parameter and store it.
- Add `get_lesson_by_chapter_id(db, chapter_id)` — join chapters → lessons to get lesson for a quiz's chapter.

#### To Add New

**`backend/src/crud/crud_slide_chat.py`:**

| Function | Signature | Description |
|----------|-----------|-------------|
| `get_chat_messages` | `(db, username, slide_identifier) → list[SlideChatMessage]` | All messages for a user+slide, ordered by created_at ASC |
| `get_recent_chat_messages` | `(db, username, slide_identifier, limit=10) → list[SlideChatMessage]` | Last N messages for context window |
| `save_chat_message` | `(db, username, slide_identifier, role, content) → SlideChatMessage` | Insert one message row |

### Services

#### To Delete
None.

#### To Update
None.

#### To Add New

**`backend/src/service/slide_chat_service.py`** — `SlideChatService`:

| Method | Signature | Description |
|--------|-----------|-------------|
| `answer` | `(slide_context: str, raw_content: str|None, recent_messages: list, user_message: str) → str` | Builds prompt, calls Gemini, returns response text |

**Prompt structure:**

```
+----------------------------------------------------------+
|  SYSTEM PROMPT                                           |
|  (resources/prompts/slide_chat.md)                       |
|  - You are a learning assistant                          |
|  - Answer based on the provided lesson context           |
|  - Be concise but thorough                               |
|  - If the answer is not in the context, say so           |
+----------------------------------------------------------+
|                                                          |
+----------------------------------------------------------+
|  USER PROMPT  (built by SlideChatService.answer)         |
|                                                          |
|  +----------------------------------------------------+  |
|  | LESSON CONTEXT (raw_content, truncated to ~8000ch) |  |
|  +----------------------------------------------------+  |
|  | SLIDE CONTEXT (chapter content or quiz fields)     |  |
|  +----------------------------------------------------+  |
|  | RECENT CONVERSATION (last 10 messages)             |  |
|  +----------------------------------------------------+  |
|  | USER QUESTION                                      |  |
|  +----------------------------------------------------+  |
|                                                          |
+----------------------------------------------------------+
```

**Model:** Gemini 2.5 Flash, temperature: 0.3, free-text output (not structured JSON).

**System prompt file:** `backend/resources/prompts/slide_chat.md`

```
You are a helpful learning assistant embedded in a study app.
The user is studying a lesson and has a question about the current slide.

You are given:
1. The full lesson transcript/source material (if available)
2. The current slide content (chapter text or quiz question)
3. Recent conversation history on this slide

Answer the user's question based on the provided context.
Be concise, accurate, and educational.
If the answer cannot be found in the provided context, say so honestly.
Do not make up information.
Use markdown formatting for clarity when helpful.
```

### API Endpoints

#### To Delete
None.

#### To Update
None.

#### To Add New

**`backend/src/api/slides.py`** — add two endpoints:

| Method | Path | Auth | Request | Response |
|--------|------|------|---------|----------|
| POST | `/api/slides/chat` | Session | `SlideChatRequest` | `SlideChatResponse` |
| GET | `/api/slides/chat` | Session | query: `slide_type`, `chapter_id` or `quiz_id` | `list[ChatMessageResponse]` |

**Schemas in `backend/src/schemas/slides.py`:**

```python
class SlideChatRequest(BaseModel):
    slide_type: str          # "chapter" or "quiz"
    chapter_id: int | None = None
    quiz_id: int | None = None
    message: str

class SlideChatResponse(BaseModel):
    response: str

class ChatMessageResponse(BaseModel):
    role: str                # "user" or "assistant"
    content: str
    created_at: str          # ISO timestamp
```

**Example POST request:**
```json
{
  "slide_type": "chapter",
  "chapter_id": 42,
  "quiz_id": null,
  "message": "What are neural networks?"
}
```

**Example POST response:**
```json
{
  "response": "Neural networks are computing systems inspired by biological neural networks..."
}
```

**Example GET response:**
```json
[
  { "role": "user", "content": "What are neural networks?", "created_at": "2026-04-02T10:30:00" },
  { "role": "assistant", "content": "Neural networks are...", "created_at": "2026-04-02T10:30:02" }
]
```

### Testing

#### To Delete
None.

#### To Update
None.

#### To Add New

**`backend/tests/test_slide_chat_api.py`:**
- Test POST `/api/slides/chat` with chapter slide — verify 200, response contains text
- Test POST `/api/slides/chat` with quiz slide — verify 200
- Test POST `/api/slides/chat` without auth — verify 401
- Test POST `/api/slides/chat` with invalid slide_type — verify 400
- Test POST `/api/slides/chat` with missing chapter_id for chapter type — verify 400
- Test GET `/api/slides/chat` returns message history ordered by created_at
- Test GET `/api/slides/chat` returns empty list for slide with no history

**`backend/tests/test_slide_chat_service.py`:**
- Test `SlideChatService.answer()` builds correct prompt with all context sections
- Test `SlideChatService.answer()` handles NULL raw_content gracefully
- Test `SlideChatService.answer()` truncates raw_content when too long

**`backend/tests/test_crud_slide_chat.py`:**
- Test `save_chat_message` inserts correctly
- Test `get_chat_messages` returns all messages ordered ASC
- Test `get_recent_chat_messages` returns only last N messages

**`frontend/src/__tests__/components/SlideChat.test.js`:**
- Test ChatButton renders on chapter slide
- Test ChatButton renders on quiz slide
- Test clicking ChatButton opens ChatPanel
- Test ChatPanel displays message history
- Test sending message calls API and displays response
- Test closing panel hides it

**`frontend/src/__tests__/hooks/useSlideChat.test.js`:**
- Test `sendMessage` calls API and updates messages state
- Test `loadHistory` fetches and sets messages
- Test loading state during API call

**Pre-commit loop:**
1. Run `source venv/bin/activate && pre-commit run --all-files`.
2. Fix any issues (e.g., lint errors, line count violations).
3. Re-run pre-commit again — Prettier may reformat the fixes and push files back over the line limit (max 300 lines per frontend file). If so, fix again (e.g., extract components to separate files to reduce line count durably).
4. Repeat until pre-commit passes cleanly on a full re-run with no new failures.

### Frontend

#### To Delete
None.

#### To Update

**`frontend/src/pages/SlidePage.jsx`:**
- Import and render `ChatButton` as an overlay on the slide area
- Pass `slideType`, `chapterId`, and `quizId` from the current `slide` state to `ChatButton`

**`frontend/src/services/api.js`:**
- Add `sendChatMessage(body)` → POST `/api/slides/chat`
- Add `getChatHistory(slideType, chapterId, quizId)` → GET `/api/slides/chat?slide_type=...&chapter_id=...`

#### To Add New

**`frontend/src/components/ChatButton.jsx`** — Floating action button:
- Fixed position bottom-right (`fixed bottom-6 right-6`)
- Circular button with chat icon (SVG speech bubble)
- `bg-blue-600 hover:bg-blue-700` styling, matching existing button palette
- Click toggles `ChatPanel` visibility
- Shows unread indicator dot if chat has history (optional)

**`frontend/src/components/ChatPanel.jsx`** — Chat drawer/panel:
- Fixed position, anchored bottom-right, above the ChatButton
- Width: `w-96`, max-height: `max-h-[70vh]`
- `bg-gray-800 border border-gray-600 rounded-lg shadow-xl`
- Header: "Chat" title + close (X) button
- Message area: scrollable div, messages styled as bubbles
  - User messages: `bg-blue-600 text-white` aligned right
  - Assistant messages: `bg-gray-700 text-gray-200` aligned left, rendered with `ReactMarkdown`
- Input area: text input + send button at bottom
- Loading state: show "..." typing indicator while waiting for response
- On mount: calls `loadHistory` to fetch previous messages from DB

**`frontend/src/hooks/useSlideChat.js`** — Chat state management:

| Method | Description |
|--------|-------------|
| `messages` | Array of `{ role, content, created_at }` |
| `loading` | Boolean — true while waiting for AI response |
| `sendMessage(text)` | POST to API, append user msg + AI response to state |
| `loadHistory(slideType, chapterId, quizId)` | GET history from API, set messages |

The hook reloads history when `slideType`/`chapterId`/`quizId` changes (i.e., when the user navigates to a different slide).

### Documentation

#### Abstract (`docs/abstract/`)

**Update `docs/abstract/slide_stack.md`:**
- **Solution** section: Add sentence about contextual AI chat on slides
- **User Flow**: Add chat branch to the existing flow diagram (chat icon → ask question → receive answer)
- **Scope — Included**: Add "Contextual AI Q&A chat on chapter and quiz slides"
- **Acceptance Criteria**: Add criteria for chat icon visibility, sending questions, receiving responses, and history persistence

#### Technical (`docs/technical/`)

**Update `docs/technical/slide_stack.md`:**
- **Architecture**: Add chat endpoint diagram
- **Data Model**: Add `SlideChatMessage` table and `raw_content` column on `Lesson`
- **Pipeline**: Add new "Slide Chat Pipeline" section
- **API Layer**: Add POST/GET `/api/slides/chat` rows
- **Service Layer**: Add `SlideChatService` documentation
- **LLM Requests Layer**: Add `SlideChatService.answer` prompt structure and output description
- **CRUD Layer**: Add `crud_slide_chat.py` functions
- **Frontend — Components**: Add `ChatButton` and `ChatPanel`
- **Frontend — Services & Hooks**: Add `useSlideChat` hook and `api.js` additions
- **Component Checklist**: Add all new components

**Update `docs/technical/content_upload.md`:**
- **Data Model**: Add `raw_content` column to `lessons` table schema
- **Pipeline — Upload Sequence**: Note that `POST /api/content/lessons` now accepts optional `raw_content`
- **API Layer**: Update `POST /api/content/lessons` request to include `raw_content`
- **CRUD Layer**: Note `create_lesson` accepts `raw_content`

**Update `docs/technical/system_pipelines.md`:**
- Add new "Slide Chat Pipeline" diagram linking to `slide_stack.md`

### Chrome Claude Extension Execution

After implementation is complete, execute the Chrome Claude Extension E2E tests defined in `docs/chrome_test/slide_chat.md`. See [chrome-test-execution.md](../chrome_test/slide_chat.md) for test details.

---

## Dependencies

- **Gemini API key** — already configured in `backend/src/configs.py` via `GEMINI_API_KEY` env var
- **Content upload tables** — `books`, `lessons`, `chapters`, `chapter_quizzes` must exist (migration 001+006)
- **Authentication** — session cookie auth must be working
- **Upload pipeline update** — the `raw_content` column is only useful once the upload script sends raw content. This can be done incrementally (existing lessons will have `NULL` raw_content, chat still works with chapter content alone)

## Open Questions

None — all questions resolved during planning.
