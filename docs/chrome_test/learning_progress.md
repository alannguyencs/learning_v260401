# Chrome E2E Tests — Learning Progress Tab

## Remarks

- **Frontend**: http://localhost:3999
- **Backend**: http://localhost:8999
- **Test user**: `alan` / `sunny`
- **Sign-in flow**: Navigate to `/login` → enter username + password → submit → redirected to `/slides`
- **Sign-out flow**: Click logout button on `/slides` page
- **Cleanup**: Run the SQL in the Cleanup section before each test session to reset progress tables

---

## Database Pre-Interaction

### Seed Data

The learning progress tab requires existing books, lessons, chapters, quizzes, and user progress data.

**Table**: `user_chapter_progress`
```sql
-- Ensure at least one chapter is marked learnt
INSERT INTO user_chapter_progress (username, chapter_id, learnt_at)
VALUES ('alan', (SELECT id FROM chapters WHERE lesson_id = (SELECT id FROM lessons LIMIT 1) LIMIT 1), NOW() - INTERVAL '1 hour')
ON CONFLICT DO NOTHING;
```
**Purpose**: Creates a learnt chapter so chapter progress metric is non-zero.

**Table**: `quiz_answer_log`
```sql
INSERT INTO quiz_answer_log (username, quiz_id, lesson_id, round_num, is_correct, answered_at)
VALUES
  ('alan', (SELECT id FROM chapter_quizzes LIMIT 1), (SELECT id FROM lessons LIMIT 1), 0, true, NOW() - INTERVAL '30 minutes'),
  ('alan', (SELECT id FROM chapter_quizzes OFFSET 1 LIMIT 1), (SELECT id FROM lessons LIMIT 1), 0, false, NOW() - INTERVAL '25 minutes')
ON CONFLICT DO NOTHING;
```
**Purpose**: One correct + one wrong answer so accuracy metric shows non-trivial data.

**Table**: `lesson_revision_rounds`
```sql
INSERT INTO lesson_revision_rounds (username, lesson_id, round_num, status, due_at_lesson_count, quizzes_in_round, quizzes_answered)
VALUES ('alan', (SELECT id FROM lessons LIMIT 1), 0, 'open', 0, 9, 2)
ON CONFLICT DO NOTHING;
```
**Purpose**: An open R0 round so revision status is visible.

**Table**: `user_quiz_recall`
```sql
INSERT INTO user_quiz_recall (username, quiz_id, forgetting_rate, last_reviewed_lesson_count, review_count)
VALUES
  ('alan', (SELECT id FROM chapter_quizzes LIMIT 1), 0.7, 0, 1),
  ('alan', (SELECT id FROM chapter_quizzes OFFSET 1 LIMIT 1), 1.2, 0, 1)
ON CONFLICT DO NOTHING;
```
**Purpose**: Recall values so average recall metric is visible.

### Cleanup

```sql
DELETE FROM quiz_answer_log WHERE username = 'alan';
DELETE FROM quiz_skip_log WHERE username = 'alan';
DELETE FROM user_quiz_recall WHERE username = 'alan';
DELETE FROM lesson_revision_rounds WHERE username = 'alan';
DELETE FROM user_chapter_progress WHERE username = 'alan';
DELETE FROM user_lesson_count WHERE username = 'alan';
```

---

## Pre-requisite

Sign in as `alan` (password: `sunny`) before running any test. Navigate to http://localhost:3999/login, enter credentials, and confirm redirect to `/slides`.

---

## Tests

### Test 1 — Tab switcher renders and defaults to Activity Log

- [ ] Sign in as `alan`
- [ ] Navigate to http://localhost:3999/dashboard
- [ ] Verify two tabs are visible: "Activity Log" and "Learning Progress"
- [ ] Verify "Activity Log" is the active/selected tab by default
- [ ] Verify the activity log table is shown (existing behavior unchanged)

**Expected UI state**: Dashboard page with tab switcher at top. Activity Log tab selected, table visible below.

**Report**: IN QUEUE
- Findings: --
- Improvement Proposals:
  + good to have - URL hash support — `/dashboard#progress` to deep-link to the Learning Progress tab

---

### Test 2 — Switching to Learning Progress tab shows lesson cards

- [ ] Sign in as `alan`
- [ ] Navigate to http://localhost:3999/dashboard
- [ ] Click the "Learning Progress" tab
- [ ] Verify the activity log table disappears
- [ ] Verify at least one book section heading is visible (e.g., "theMITmonk")
- [ ] Verify at least one lesson card is visible with the lesson title
- [ ] Verify the lesson card shows: Chapters progress, Revision status, Accuracy, Recall metrics

**Expected UI state**: Card-based layout grouped by book. Each lesson card shows 4 metrics.

**Report**: IN QUEUE
- Findings: --
- Improvement Proposals:
  + good to have - Expand/collapse book sections for users with many books

---

### Test 3 — Lesson card metrics display correct values

- [ ] Ensure seed data is applied (Cleanup + re-insert)
- [ ] Sign in as `alan` and navigate to `/dashboard`
- [ ] Click "Learning Progress" tab
- [ ] Find the lesson card for the seeded lesson
- [ ] Verify Chapters shows a progress bar with correct fraction (e.g., "1/5")
- [ ] Verify Revision shows "R0 open" with answered count
- [ ] Verify Accuracy shows correct/total with percentage
- [ ] Verify Recall shows an average forgetting rate value

**Expected UI state**: All 4 metrics populated with data matching the seed data.

**Report**: IN QUEUE
- Findings: --
- Improvement Proposals:
  + good to have - Colour-coded recall value — green for strong, red for weak

---

### Test 4 — Empty state when no progress exists

- [ ] Run cleanup SQL to empty all progress tables
- [ ] Sign in as `alan` and navigate to `/dashboard`
- [ ] Click "Learning Progress" tab
- [ ] Verify an empty-state message is displayed (e.g., "No progress yet")
- [ ] Verify a link to `/slides` is present

**Expected UI state**: No lesson cards shown. Empty-state message with link to start learning.

**Report**: IN QUEUE
- Findings: --
- Improvement Proposals:
  + good to have - Show total available lessons count in empty state

---

### Test 5 — Unauthenticated access redirects to login

- [ ] Ensure user is signed out
- [ ] Navigate directly to http://localhost:3999/dashboard
- [ ] Verify redirect to `/login` page
- [ ] Verify dashboard content is not visible

**Expected UI state**: Login page shown. No dashboard data exposed.

**Report**: IN QUEUE
- Findings: --
- Improvement Proposals: --
