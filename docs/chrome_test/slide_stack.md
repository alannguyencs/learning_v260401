# Chrome E2E Tests — Slide Stack (Dynamic Lesson-Quiz Stacking)

## Remarks

- **Frontend port**: `http://localhost:3000`
- **Backend port**: `http://localhost:8000`
- **Sign-in flow**: Navigate to `http://localhost:3000/login`, enter username and password, click Login → redirected to `/slides`.
- **Sign-out flow**: Trigger logout via the logout button or navigate to `/login`.
- **Seed data**: All tests require at least one book with at least one lesson containing two chapters, each with at least one quiz. See Database Pre-Interaction below.
- **Cleanup**: Run the DELETE statements below before each test session.

---

## Database Pre-Interaction

### Seed data

Run the following before executing tests (replace `<test_user>` with the actual test username):

```sql
-- Seed: one book
INSERT INTO books (book_id, title) VALUES ('test_book', 'Test Book')
ON CONFLICT DO NOTHING;

-- Seed: one lesson with lesson_index=1
INSERT INTO lessons (book_id, lesson_index, title) VALUES ('test_book', 1, 'Test Lesson 1')
ON CONFLICT DO NOTHING;

-- Seed: two chapters
INSERT INTO chapters (lesson_id, chapter_index, title, content)
VALUES (
  (SELECT id FROM lessons WHERE book_id='test_book' AND lesson_index=1),
  1, 'Chapter 1', '# Chapter 1\n\nThis is the first chapter content.'
) ON CONFLICT DO NOTHING;

INSERT INTO chapters (lesson_id, chapter_index, title, content)
VALUES (
  (SELECT id FROM lessons WHERE book_id='test_book' AND lesson_index=1),
  2, 'Chapter 2', '# Chapter 2\n\nThis is the second chapter content.'
) ON CONFLICT DO NOTHING;

-- Seed: one single-correct MC quiz on Chapter 1
INSERT INTO chapter_quizzes (chapter_id, quiz_type, question, expected_answer, option_a, option_b, option_c, option_d, correct_options)
VALUES (
  (SELECT id FROM chapters WHERE lesson_id=(SELECT id FROM lessons WHERE book_id='test_book' AND lesson_index=1) AND chapter_index=1),
  'multiple_choice', 'What is the topic of Chapter 1?', NULL,
  'Chapter 1 topic', 'Chapter 2 topic', 'Chapter 3 topic', 'None of the above',
  '["A"]'
) ON CONFLICT DO NOTHING;

-- Seed: one multi-correct MC quiz on Chapter 1
INSERT INTO chapter_quizzes (chapter_id, quiz_type, question, expected_answer, option_a, option_b, option_c, option_d, correct_options)
VALUES (
  (SELECT id FROM chapters WHERE lesson_id=(SELECT id FROM lessons WHERE book_id='test_book' AND lesson_index=1) AND chapter_index=1),
  'multiple_choice', 'Which topics are covered in Chapter 1? (select all)', NULL,
  'Topic A', 'Topic B', 'Topic C', 'Topic D',
  '["A","B"]'
) ON CONFLICT DO NOTHING;

-- Seed: one free_recall quiz on Chapter 2
INSERT INTO chapter_quizzes (chapter_id, quiz_type, question, expected_answer, correct_options)
VALUES (
  (SELECT id FROM chapters WHERE lesson_id=(SELECT id FROM lessons WHERE book_id='test_book' AND lesson_index=1) AND chapter_index=2),
  'free_recall', 'Describe the content of Chapter 2.', 'Chapter 2 covers the second chapter content.',
  NULL
) ON CONFLICT DO NOTHING;
```

### Cleanup

```sql
DELETE FROM user_quiz_recall WHERE username = '<test_user>';
DELETE FROM quiz_skip_log WHERE username = '<test_user>';
DELETE FROM lesson_revision_rounds WHERE username = '<test_user>';
DELETE FROM user_lesson_count WHERE username = '<test_user>';
DELETE FROM user_chapter_progress WHERE username = '<test_user>';
```

---

## Pre-requisite

Sign in as the test user before running any test. Navigate to `http://localhost:3000/login`, enter credentials, and verify redirect to `/slides`.

---

## Test 1 — Chapter slide loads on fresh start

**Test name**: First slide is a chapter when no history exists
**User**: test user (fresh state, no progress)
**Steps**:
- [ ] Navigate to `http://localhost:3000/slides`
- [ ] Verify a chapter slide is displayed (not a quiz slide)
- [ ] Verify chapter title and markdown content are visible
- [ ] Verify "Mark as Learnt" button is present
- [ ] Verify "Skip Chapter" button is present

**Expected UI state**: Chapter 1 content displayed; no quiz visible.
**Error handling**: If a quiz slide appears instead of a chapter, flag immediately — Tier 1 incorrectly triggered on empty state.
**Report**: IN QUEUE
- Improvement Proposals:
  + good to have - progress indicator - show how many chapters and revisions remain

---

## Test 2 — Mark chapter as learnt triggers R0 quiz

**Test name**: Marking Chapter 1 as learnt immediately shows R0 quiz
**User**: test user
**Steps**:
- [ ] On the Chapter 1 slide, click "Mark as Learnt"
- [ ] Verify the slide transitions to a quiz slide
- [ ] Verify the quiz is from the MC quiz on Chapter 1 (round label shows "R0")
- [ ] Verify MC radio buttons A/B/C/D are displayed (single-correct quiz)
- [ ] Select option A (correct answer)
- [ ] Click "Submit Answer"
- [ ] Verify result shows "Correct" (green indicator)
- [ ] Verify "Next Slide" button appears
- [ ] Click "Next Slide"
- [ ] Verify next slide is Chapter 2 (Tier 2: no more due revisions, next chapter shown)

**Expected UI state**: Correct result shown; then Chapter 2 displayed.
**Error handling**: If incorrect result shown for correct MC answer, flag immediately — MC auto-grading broken.
**Report**: IN QUEUE
- Improvement Proposals:
  + good to have - round badge color - color-code R0/R1/R2 badges differently

---

## Test 3 — Free recall quiz with AI grading

**Test name**: Open-ended quiz submission triggers AI feedback
**User**: test user (Chapter 1 already learnt from Test 2)
**Steps**:
- [ ] Mark Chapter 2 as learnt
- [ ] Verify a quiz slide appears (free_recall type)
- [ ] Verify a textarea input is shown (not radio buttons)
- [ ] Type a reasonable answer in the textarea: "Chapter 2 covers the second chapter content"
- [ ] Click "Submit Answer"
- [ ] Verify the app shows a loading indicator (AI grading in progress)
- [ ] Verify a result (Correct or Incorrect) appears after grading
- [ ] Verify a feedback text paragraph is shown below the result
- [ ] Click "Next Slide"

**Expected UI state**: AI feedback text visible; result badge shown.
**Error handling**: If the submit button stays disabled or the grading never returns, flag immediately — LLM call failed or API error.
**Report**: IN QUEUE
- Improvement Proposals:
  + must have - timeout handling - show error message if AI grading takes more than 10 seconds
  + good to have - answer preview - show student's answer alongside expected answer in feedback panel

---

## Test 4 — Skip chapter and quiz

**Test name**: Skipped chapter and quiz are properly deferred
**User**: test user (fresh state)
**Steps**:
- [ ] On Chapter 1 slide, click "Skip Chapter"
- [ ] Verify slide transitions (no chapter marked as learnt)
- [ ] If only one book exists, verify the same chapter is shown again (no other books to interleave)
- [ ] Mark Chapter 1 as learnt
- [ ] On the R0 quiz slide, click "Skip"
- [ ] Verify the slide transitions without showing feedback panel
- [ ] If more chapters remain: verify a chapter slide appears next
- [ ] If more quizzes remain in the round: verify the next unskipped quiz appears (not the one just skipped)
- [ ] If all non-skipped quizzes are exhausted: verify skipped quizzes resurface (oldest skip first)

**Expected UI state**: Skipped quiz goes to back of queue; next unskipped quiz shown. No feedback shown on skip.
**Error handling**: If the same skipped quiz reappears immediately, flag — skip queue ordering broken.
**Report**: IN QUEUE
- Improvement Proposals:
  + good to have - skip counter - show "(3 skipped)" label somewhere in the UI

---

## Test 5 — All caught up state

**Test name**: "All caught up" message shown when no slides remain
**User**: test user (after completing all chapters and quizzes with no pending revisions)
**Steps**:
- [ ] Complete all chapters in Test Book (mark Chapter 1 and Chapter 2 as learnt)
- [ ] Answer all R0 quizzes (both MC and free_recall)
- [ ] Verify all R0 rounds are completed
- [ ] Verify that GET /api/slides/next returns slide_type=none (check via network tab or observe UI)
- [ ] Verify the "All Caught Up" message is displayed on the slide page
- [ ] Verify no error or blank screen appears

**Expected UI state**: Encouraging "All caught up" message displayed with no error.
**Error handling**: If a blank screen appears instead of the caught-up message, flag immediately.
**Report**: IN QUEUE
- Improvement Proposals:
  + good to have - next due date - show when the next R1 revision will become due
  + good to have - session summary - show a summary of quizzes answered and accuracy

---

## Test 6 — Multi-correct MC quiz uses checkboxes

**Test name**: Multi-correct MC quiz renders checkboxes and allows multiple selections
**User**: test user (fresh state)
**Steps**:
- [ ] Seed the multi-correct MC quiz (see Database Pre-Interaction)
- [ ] Mark Chapter 1 as learnt
- [ ] Navigate to the multi-correct MC quiz slide
- [ ] Verify "Select all that apply" hint is displayed
- [ ] Verify checkboxes are displayed instead of radio buttons
- [ ] Click option A checkbox — verify it becomes checked
- [ ] Click option B checkbox — verify it becomes checked AND option A remains checked
- [ ] Click "Submit Answer"
- [ ] Verify result shows "PASSED" (both correct options selected)
- [ ] Verify feedback shows option A and B highlighted green

**Expected UI state**: Both options remain selected; correct result shown.
**Error handling**: If selecting B deselects A, the multi-select toggle logic is broken.
**Report**: IN QUEUE
