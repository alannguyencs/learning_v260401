# Chrome E2E Tests — MC Feedback Highlight

## Remarks

- **Frontend port**: `http://localhost:3999`
- **Backend port**: `http://localhost:8999`
- **Sign-in flow**: Navigate to `http://localhost:3999/login`, enter username and password, click Login → redirected to `/slides`.
- **Seed data**: Tests require at least one book with a lesson containing a chapter with an MC quiz (4 options, one correct). See Database Pre-Interaction below.
- **Cleanup**: Run the DELETE statements below before each test session.

---

## Database Pre-Interaction

### Seed data

```sql
INSERT INTO books (book_id, title) VALUES ('test_mc', 'MC Test Book')
ON CONFLICT DO NOTHING;

INSERT INTO lessons (book_id, lesson_index, title)
VALUES ('test_mc', 1, 'MC Test Lesson')
ON CONFLICT DO NOTHING;

INSERT INTO chapters (lesson_id, chapter_index, title, content)
VALUES (
  (SELECT id FROM lessons WHERE book_id='test_mc' AND lesson_index=1),
  1, 'MC Chapter', '# MC Chapter\n\nContent for MC quiz testing.'
) ON CONFLICT DO NOTHING;

INSERT INTO chapter_quizzes (chapter_id, quiz_type, question, option_a, option_b, option_c, option_d, correct_options, quiz_metadata)
VALUES (
  (SELECT id FROM chapters WHERE lesson_id=(SELECT id FROM lessons WHERE book_id='test_mc' AND lesson_index=1) AND chapter_index=1),
  'multiple_choice',
  'What is 2 + 2?',
  'Three', 'Four', 'Five', 'Six',
  '["B"]',
  '{"response_to_user_option_a": "3 is incorrect.", "response_to_user_option_b": "Correct! 2+2=4.", "response_to_user_option_c": "5 is incorrect.", "response_to_user_option_d": "6 is incorrect."}'
) ON CONFLICT DO NOTHING;
```

### Cleanup

```sql
DELETE FROM slide_chat_messages WHERE username = '<test_user>';
DELETE FROM quiz_answer_log WHERE username = '<test_user>';
DELETE FROM user_quiz_recall WHERE username = '<test_user>';
DELETE FROM quiz_skip_log WHERE username = '<test_user>';
DELETE FROM lesson_revision_rounds WHERE username = '<test_user>';
DELETE FROM user_lesson_count WHERE username = '<test_user>';
DELETE FROM user_chapter_progress WHERE username = '<test_user>';
```

---

## Pre-requisite

Sign in as the test user. Navigate to `http://localhost:3999/login`, enter credentials, verify redirect to `/slides`.

---

## Test 1 — Wrong answer shows user pick in red and correct in green

**Test name**: Incorrect MC answer highlights user pick red, correct option green
**User**: test user
**Steps**:
- [ ] Mark the MC Chapter as learnt to trigger R0 quiz
- [ ] On the MC quiz, select option A (wrong answer)
- [ ] Click "Submit Answer"
- [x] Verify all 4 options are displayed in the feedback
- [x] Verify option A has a red border/background (user's wrong pick)
- [x] Verify option B has a green border/background (correct answer)
- [x] Verify options C and D have gray border/background (not picked, not correct)

**Expected UI state**: All 4 options shown: A (red), B (green), C (gray), D (gray).
**Error handling**: If user pick is not red or correct is not green, flag.
**Report**: PASS
- Improvement Proposals:

---

## Test 2 — Correct answer shows user pick in green only

**Test name**: Correct MC answer highlights user pick green
**User**: test user (fresh state)
**Steps**:
- [x] Mark the MC Chapter as learnt to trigger R0 quiz
- [x] On the MC quiz, select option B (correct answer)
- [x] Click "Submit Answer"
- [x] Verify the correct badge shows ("Correct")
- [x] Verify option B is displayed with green border/background
- [x] Verify all options displayed: correct options green, others gray

**Expected UI state**: All options shown. Correct options green, others gray. Badge "Correct".
**Error handling**: If correct option not green, flag.
**Report**: PASS
- Improvement Proposals:

---

## Test 3 — Per-option explanations still display for shown options

**Test name**: Explanations shown for visible options only
**User**: test user
**Steps**:
- [x] On an MC quiz with quiz_metadata containing response_to_user_option_* fields
- [x] Select a wrong answer (e.g., option A)
- [x] Submit
- [x] Verify the explanation for option A is visible under the red-highlighted option
- [x] Verify the explanation for option B (correct) is visible under the green-highlighted option
- [x] Verify explanations for all options are shown under each option

**Expected UI state**: All options shown with their explanations. Colors: wrong pick red, correct green, others gray.
**Error handling**: If explanations missing, flag.
**Report**: PASS
- Improvement Proposals:

---

## Test 4 — Takeaway and other feedback elements still render

**Test name**: Takeaway block and correct/incorrect badge unaffected
**User**: test user
**Steps**:
- [x] Submit a wrong MC answer
- [x] Verify "Incorrect" badge is shown in red
- [x] Verify Key Takeaway block still renders below the options
- [x] Verify "Next Slide" button is present and clickable
- [x] Click "Next Slide" — navigation works

**Expected UI state**: Full feedback panel renders with all options, badge, takeaway, and Next Slide button.
**Error handling**: If takeaway or Next Slide button missing, flag — regression in FeedbackPanel.
**Report**: PASS
- Improvement Proposals:

---

## Test 5 — Non-MC quiz types unaffected

**Test name**: Free recall / teach back / cloze feedback unchanged
**User**: test user
**Steps**:
- [x] Navigated through free_recall and cloze quizzes during skip phase
- [x] Non-MC quizzes show standard feedback (textarea, no MC options)
- [x] MC option highlighting does not appear on non-MC types

**Expected UI state**: Non-MC quiz feedback unchanged by this feature.
**Error handling**: If MC option display appears on non-MC quiz, flag — conditional logic broken.
**Report**: PASS
- Improvement Proposals:
