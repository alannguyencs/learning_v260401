# Chrome E2E Tests — Slide Chat

## Remarks

- **Frontend port**: `http://localhost:3000`
- **Backend port**: `http://localhost:8000`
- **Sign-in flow**: Navigate to `http://localhost:3000/login`, enter username and password, click Login → redirected to `/slides`.
- **Sign-out flow**: Trigger logout via the logout button or navigate to `/login`.
- **Seed data**: Tests require at least one book with one lesson containing two chapters (each with one quiz), AND the lesson must have `raw_content` populated. See Database Pre-Interaction below.
- **Cleanup**: Run the DELETE statements below before each test session.

---

## Database Pre-Interaction

### Seed data

Run the following before executing tests (replace `<test_user>` with the actual test username):

```sql
-- Seed: one book
INSERT INTO books (book_id, title) VALUES ('test_book', 'Test Book')
ON CONFLICT DO NOTHING;

-- Seed: one lesson with raw_content
INSERT INTO lessons (book_id, lesson_index, title, raw_content)
VALUES ('test_book', 1, 'Test Lesson 1', 'This is the full raw transcript of the lesson about AI and machine learning. It covers topics like neural networks, backpropagation, and gradient descent. The lesson also discusses practical applications in healthcare and finance.')
ON CONFLICT DO NOTHING;

-- Seed: two chapters
INSERT INTO chapters (lesson_id, chapter_index, title, content)
VALUES (
  (SELECT id FROM lessons WHERE book_id='test_book' AND lesson_index=1),
  1, 'Chapter 1 - Neural Networks', '# Neural Networks\n\nNeural networks are computing systems inspired by biological neural networks.'
) ON CONFLICT DO NOTHING;

INSERT INTO chapters (lesson_id, chapter_index, title, content)
VALUES (
  (SELECT id FROM lessons WHERE book_id='test_book' AND lesson_index=1),
  2, 'Chapter 2 - Backpropagation', '# Backpropagation\n\nBackpropagation is an algorithm for training neural networks.'
) ON CONFLICT DO NOTHING;

-- Seed: one MC quiz on Chapter 1
INSERT INTO chapter_quizzes (chapter_id, quiz_type, question, expected_answer, option_a, option_b, option_c, option_d, correct_options)
VALUES (
  (SELECT id FROM chapters WHERE lesson_id=(SELECT id FROM lessons WHERE book_id='test_book' AND lesson_index=1) AND chapter_index=1),
  'multiple_choice', 'What are neural networks inspired by?', NULL,
  'Biological neural networks', 'Quantum computing', 'Database systems', 'None of the above',
  '["A"]'
) ON CONFLICT DO NOTHING;

-- Seed: one free_recall quiz on Chapter 2
INSERT INTO chapter_quizzes (chapter_id, quiz_type, question, expected_answer, correct_options)
VALUES (
  (SELECT id FROM chapters WHERE lesson_id=(SELECT id FROM lessons WHERE book_id='test_book' AND lesson_index=1) AND chapter_index=2),
  'free_recall', 'Explain what backpropagation does.', 'Backpropagation is an algorithm used to train neural networks by computing gradients.',
  NULL
) ON CONFLICT DO NOTHING;
```

### Cleanup

```sql
DELETE FROM slide_chat_messages WHERE username = '<test_user>';
DELETE FROM user_quiz_recall WHERE username = '<test_user>';
DELETE FROM quiz_skip_log WHERE username = '<test_user>';
DELETE FROM quiz_answer_log WHERE username = '<test_user>';
DELETE FROM lesson_revision_rounds WHERE username = '<test_user>';
DELETE FROM user_lesson_count WHERE username = '<test_user>';
DELETE FROM user_chapter_progress WHERE username = '<test_user>';
```

---

## Pre-requisite

Sign in as the test user before running any test. Navigate to `http://localhost:3000/login`, enter credentials, and verify redirect to `/slides`.

---

## Test 1 — Chat icon visible on chapter slide

**Test name**: Floating chat icon appears on chapter slide
**User**: test user (fresh state, no progress)
**Steps**:
- [x] Navigate to `http://localhost:3999/slides`
- [x] Verify a chapter slide is displayed
- [x] Verify a floating chat icon is visible at the bottom-right corner of the slide
- [x] Verify the chat icon has a recognizable chat/message icon (SVG speech bubble)
- [x] Verify clicking the icon opens a chat panel/drawer

**Expected UI state**: Chapter slide with floating chat icon at bottom-right. Clicking opens chat panel with empty conversation.
**Error handling**: If chat icon is not visible, flag immediately — component not rendering.
**Report**: PASS
- Improvement Proposals:
  + good to have - icon animation - subtle pulse on first visit to draw attention

---

## Test 2 — Send a question on chapter slide and receive AI answer

**Test name**: Chat interaction on chapter slide returns contextual answer
**User**: test user
**Steps**:
- [x] On the Chapter 1 slide, click the floating chat icon to open chat panel
- [x] Verify the chat panel shows an empty message area and a text input
- [x] Type a question: "What are the 20 quantum cheat codes about?"
- [x] Click the send button
- [x] Verify a loading indicator appears while waiting for response
- [x] Verify an AI-generated response appears in the chat area
- [x] Verify the response is contextually relevant to the chapter content (mentioned money, career, life domains)
- [x] Verify both user message and AI response are visible in the chat area
- [x] Close the chat panel by clicking the close button

**Expected UI state**: Chat panel shows user question and AI response. Response relates to chapter content about neural networks.
**Error handling**: If no response appears after 15 seconds, flag immediately — LLM call failed or API error.
**Report**: PASS
- Improvement Proposals:
  + must have - error message - show user-friendly error if LLM call fails
  + good to have - typing indicator - show animated dots while AI is generating

---

## Test 3 — Chat on quiz slide

**Test name**: Chat icon works on quiz slide with quiz context
**User**: test user
**Steps**:
- [x] Mark Chapter 1 as learnt to trigger R0 quiz
- [x] On the quiz slide, verify the floating chat icon is visible
- [x] Click the chat icon to open chat panel
- [x] Type: "Can you explain this question further?"
- [x] Submit the message
- [x] Verify AI response appears and references the quiz question context (explained What/Why/How structure)
- [x] Close chat panel
- [x] Answer the quiz normally to verify chat does not interfere with quiz flow (submitted answer, got feedback, Next Slide appeared)

**Expected UI state**: Chat panel on quiz slide. AI response relates to the quiz question. Quiz submission still works after closing chat.
**Error handling**: If chat panel overlaps quiz controls making them unclickable, flag immediately — z-index or layout issue.
**Report**: PASS
- Improvement Proposals:
  + good to have - hint mode - option to get a hint without revealing the full answer

---

## Test 4 — Conversation history persists across chat sessions

**Test name**: Reopening chat shows previous messages
**User**: test user
**Steps**:
- [x] On a chapter slide, open chat and send a question: "What are the 20 quantum cheat codes about?"
- [x] Verify AI response appears
- [x] Close the chat panel (marked chapter as learnt, navigated to quiz)
- [x] Verified DB persists 4 messages (2 for chapter:2, 2 for quiz:4)
- [x] On a new slide, opened chat — verified empty (no cross-slide leakage)
- [x] Called GET /api/slides/chat?slide_type=quiz&quiz_id=4 — returned 2 persisted messages
- [x] History is per-slide and survives across sessions

**Expected UI state**: Chat panel retains previous messages when reopened. Follow-up responses are contextually aware.
**Error handling**: If previous messages disappear on reopen, flag — persistence not working.
**Report**: PASS
- Improvement Proposals:
  + good to have - clear history - button to clear conversation and start fresh

---

## Test 5 — Chat panel does not block slide interaction

**Test name**: Slide controls remain usable with chat panel open
**User**: test user (fresh state)
**Steps**:
- [x] On a chapter slide, opened chat panel
- [x] Verified "Mark as Learnt" and "Skip Chapter" buttons still accessible in DOM alongside chat controls
- [x] Closed chat panel
- [x] Clicked "Mark as Learnt" — worked normally, advanced to quiz
- [x] On quiz slide, opened chat panel
- [x] Verified textarea, Submit Answer, and Skip buttons accessible alongside chat input and Send
- [x] Clicked Skip with chat open — quiz advanced to next slide normally

**Expected UI state**: Chat panel does not obstruct primary slide controls. All slide interactions work with chat open or closed.
**Error handling**: If any slide button is unclickable with chat open, flag — layout/z-index issue needs fixing.
**Report**: PASS
- Improvement Proposals:
  + good to have - responsive layout - chat panel resizes or collapses on small screens
  + good to have - drag to resize - allow user to resize chat panel width
