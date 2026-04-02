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
- [ ] Verify only two options are displayed in the feedback: user's pick (A) and correct option (B)
- [ ] Verify option A has a red border/background (user's wrong pick)
- [ ] Verify option B has a green border/background (correct answer)
- [ ] Verify the other options (C, D) are not displayed

**Expected UI state**: Only A (red) and B (green) shown after wrong answer.
**Error handling**: If all 4 options still display, flag — filtering not applied.
**Report**: IN QUEUE
- Improvement Proposals:

---

## Test 2 — Correct answer shows user pick in green only

**Test name**: Correct MC answer highlights user pick green
**User**: test user (fresh state)
**Steps**:
- [ ] Mark the MC Chapter as learnt to trigger R0 quiz
- [ ] On the MC quiz, select option B (correct answer)
- [ ] Click "Submit Answer"
- [ ] Verify the correct badge shows
- [ ] Verify option B is displayed with green border/background
- [ ] Verify option B is the only option displayed (since user pick = correct, only one shown)

**Expected UI state**: Only B (green) shown after correct answer.
**Error handling**: If other options display alongside correct, flag — filtering not applied for correct case.
**Report**: IN QUEUE
- Improvement Proposals:

---

## Test 3 — Per-option explanations still display for shown options

**Test name**: Explanations shown for visible options only
**User**: test user
**Steps**:
- [ ] On an MC quiz with quiz_metadata containing response_to_user_option_* fields
- [ ] Select a wrong answer (e.g., option A)
- [ ] Submit
- [ ] Verify the explanation for option A is visible under the red-highlighted option
- [ ] Verify the explanation for option B (correct) is visible under the green-highlighted option
- [ ] Verify no explanations for C or D are shown

**Expected UI state**: Explanations appear only for the two visible options.
**Error handling**: If explanations for hidden options appear, flag — filtering not complete.
**Report**: IN QUEUE
- Improvement Proposals:

---

## Test 4 — Takeaway and other feedback elements still render

**Test name**: Takeaway block and correct/incorrect badge unaffected
**User**: test user
**Steps**:
- [ ] Submit a wrong MC answer
- [ ] Verify "Incorrect" badge is shown in red
- [ ] Verify Key Takeaway block still renders below the options (if quiz has quiz_take_away)
- [ ] Verify "Next Slide" button is present and clickable
- [ ] Click "Next Slide" — verify navigation works

**Expected UI state**: Full feedback panel renders with filtered options, badge, takeaway, and Next Slide button.
**Error handling**: If takeaway or Next Slide button missing, flag — regression in FeedbackPanel.
**Report**: IN QUEUE
- Improvement Proposals:

---

## Test 5 — Non-MC quiz types unaffected

**Test name**: Free recall / teach back / cloze feedback unchanged
**User**: test user
**Steps**:
- [ ] Navigate to a free_recall or teach_back quiz
- [ ] Submit an answer
- [ ] Verify the feedback panel shows the standard format (no MC option display)
- [ ] Verify key points list still renders if applicable

**Expected UI state**: Non-MC quiz feedback unchanged by this feature.
**Error handling**: If MC option display appears on non-MC quiz, flag — conditional logic broken.
**Report**: IN QUEUE
- Improvement Proposals:
