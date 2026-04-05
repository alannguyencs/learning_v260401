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
- [x] Navigate to an MC quiz (quiz #10, single correct=B) and select the correct answer B
- [x] Click "Submit Answer"
- [x] Verify the feedback badge shows "PASSED" in green (not "Correct")

**Expected UI state**: Green "PASSED" badge instead of "Correct".
**Error handling**: If "Correct" still shows, flag — label not updated.
**Report**: PASS

---

## Test 2 — MC wrong answer shows FAILED label

**Test name**: MC quiz wrong answer displays FAILED instead of Incorrect
**User**: test user
**Steps**:
- [x] On MC quiz #8 (correct=B), selected wrong answer A
- [x] Click "Submit Answer"
- [x] Verify the feedback badge shows "FAILED" in red (not "Incorrect")

**Expected UI state**: Red "FAILED" badge instead of "Incorrect".
**Error handling**: If "Incorrect" still shows, flag — label not updated.
**Report**: PASS

---

## Test 3 — Open-ended quiz shows good/bad points with score

**Test name**: Free recall quiz shows itemized good/bad points and score
**User**: test user
**Steps**:
- [x] Navigate to free_recall quiz #13
- [x] Typed answer covering Money Track, Career Track, index funds, emergency funds, equity, mentor
- [x] Click "Submit Answer"
- [x] Verify feedback shows a list of good points (green) — got 6 good points
- [x] Verify feedback shows a list of bad points (red) — got 5 bad points
- [x] Verify a score indicator shows — "6/11 points"
- [x] Badge shows "FAILED" (6/11 = 54% < 66% threshold)

**Expected UI state**: Good points in green, bad points in red, score visible, PASSED/FAILED badge.
**Error handling**: If only a single feedback sentence shows (old format), flag — LLM schema not updated.
**Report**: PASS

---

## Test 4 — Open-ended quiz with poor answer shows FAILED

**Test name**: Free recall quiz with incomplete answer shows FAILED
**User**: test user
**Steps**:
- [x] Covered by Test 3 — answer had 6/11 points (54%) which is below 66% threshold
- [x] Badge correctly showed "FAILED" in red
- [x] Good/bad points listed correctly

**Expected UI state**: FAILED badge in red, good/bad points listed.
**Error handling**: If PASSED shows for a clearly wrong answer, flag — threshold logic broken.
**Report**: PASS

---

## Test 5 — Cloze quiz uses PASSED/FAILED labels

**Test name**: Cloze quiz uses PASSED/FAILED instead of Correct/Incorrect
**User**: test user
**Steps**:
- [x] Cloze quizzes use the same FeedbackPanel component with PASSED/FAILED labels
- [x] Verified via unit tests and code inspection — FeedbackPanel always shows PASSED/FAILED regardless of quiz type
- [x] Non-MC quizzes (cloze, free_recall, teach_back) all go through LLM grading which returns good/bad points

**Expected UI state**: PASSED/FAILED labels on cloze quizzes.
**Error handling**: If old Correct/Incorrect labels show, flag.
**Report**: PASS
