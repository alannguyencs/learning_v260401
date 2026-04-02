# Chrome E2E Tests — Quiz PASSED/FAILED Grading

## Remarks

- **Frontend port**: `http://localhost:3999`
- **Backend port**: `http://localhost:8999`
- **Sign-in flow**: Navigate to `http://localhost:3999/login`, enter username and password, click Login.
- **Seed data**: Tests require a book with lessons containing both MC and open-ended quizzes. Use existing "theMITmonk" book data.
- **Cleanup**: Run the DELETE statements below before each test session.

---

## Database Pre-Interaction

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

## Test 1 — MC correct answer shows PASSED label

**Test name**: MC quiz correct answer displays PASSED instead of Correct
**User**: test user
**Steps**:
- [ ] Navigate to an MC quiz and select the correct answer
- [ ] Click "Submit Answer"
- [ ] Verify the feedback badge shows "PASSED" in green (not "Correct")

**Expected UI state**: Green "PASSED" badge instead of "Correct".
**Error handling**: If "Correct" still shows, flag — label not updated.
**Report**: IN QUEUE

---

## Test 2 — MC wrong answer shows FAILED label

**Test name**: MC quiz wrong answer displays FAILED instead of Incorrect
**User**: test user
**Steps**:
- [ ] On an MC quiz, select a wrong answer
- [ ] Click "Submit Answer"
- [ ] Verify the feedback badge shows "FAILED" in red (not "Incorrect")

**Expected UI state**: Red "FAILED" badge instead of "Incorrect".
**Error handling**: If "Incorrect" still shows, flag — label not updated.
**Report**: IN QUEUE

---

## Test 3 — Open-ended quiz shows good/bad points with PASSED

**Test name**: Free recall quiz with good answer shows good points, bad points, and PASSED
**User**: test user
**Steps**:
- [ ] Navigate to a free_recall or teach_back quiz
- [ ] Type a reasonably good answer covering most key points
- [ ] Click "Submit Answer"
- [ ] Verify feedback shows a list of good points (green) and bad points (red)
- [ ] Verify a score indicator shows (e.g., "3/4 points")
- [ ] Verify badge shows "PASSED" if good points >= 66%

**Expected UI state**: Good points in green, bad points in red, PASSED badge, score visible.
**Error handling**: If only a single feedback sentence shows (old format), flag — LLM schema not updated.
**Report**: IN QUEUE

---

## Test 4 — Open-ended quiz with poor answer shows FAILED

**Test name**: Free recall quiz with incomplete answer shows FAILED
**User**: test user
**Steps**:
- [ ] On a free_recall quiz, type a vague or mostly wrong answer
- [ ] Click "Submit Answer"
- [ ] Verify feedback shows good points and bad points
- [ ] Verify badge shows "FAILED" if good points < 66%

**Expected UI state**: FAILED badge in red, good/bad points listed.
**Error handling**: If PASSED shows for a clearly wrong answer, flag — threshold logic broken.
**Report**: IN QUEUE

---

## Test 5 — Cloze quiz uses PASSED/FAILED labels

**Test name**: Cloze quiz uses PASSED/FAILED instead of Correct/Incorrect
**User**: test user
**Steps**:
- [ ] Navigate to a cloze quiz
- [ ] Fill in the blank with the correct answer
- [ ] Submit and verify "PASSED" badge shows
- [ ] Navigate to another cloze quiz, fill in a wrong answer
- [ ] Submit and verify "FAILED" badge shows

**Expected UI state**: PASSED/FAILED labels on cloze quizzes.
**Error handling**: If old Correct/Incorrect labels show, flag.
**Report**: IN QUEUE
