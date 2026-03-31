# Chrome E2E Tests — Dashboard Activity Log

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

**Table**: `user_chapter_progress`
```sql
INSERT INTO user_chapter_progress (username, chapter_id, learnt_at)
VALUES ('alan', 1, NOW() - INTERVAL '10 minutes')
ON CONFLICT DO NOTHING;
```
**Purpose**: Simulate a learnt chapter so LEARNT CHAPTER event appears in the log.

**Table**: `quiz_skip_log`
```sql
INSERT INTO quiz_skip_log (username, quiz_id, lesson_id, round_num, skipped_at)
VALUES
  ('alan', 2, 1, 0, NOW() - INTERVAL '8 minutes'),
  ('alan', 3, 1, 0, NOW() - INTERVAL '7 minutes')
ON CONFLICT DO NOTHING;
```
**Purpose**: Two skip events to verify SKIP rows appear in the dashboard table.

**Table**: `quiz_answer_log`
```sql
INSERT INTO quiz_answer_log (username, quiz_id, lesson_id, round_num, is_correct, answered_at)
VALUES
  ('alan', 1, 1, 0, false, NOW() - INTERVAL '6 minutes'),
  ('alan', 4, 1, 0, true,  NOW() - INTERVAL '5 minutes')
ON CONFLICT DO NOTHING;
```
**Purpose**: One wrong and one correct answer to verify answer_result and recall_rate columns.

**Table**: `lesson_revision_rounds`
```sql
INSERT INTO lesson_revision_rounds (username, lesson_id, round_num, status, due_at_lesson_count, quizzes_in_round, quizzes_answered)
VALUES ('alan', 1, 0, 'done', 0, 5, 3)
ON CONFLICT DO NOTHING;
```
**Purpose**: A completed R0 round to verify ROUND CREATED row appears.

### Cleanup

```sql
TRUNCATE user_chapter_progress, user_lesson_count, user_quiz_recall, quiz_skip_log, quiz_answer_log, lesson_revision_rounds;
```

---

## Pre-requisite

Sign in as `alan` (password: `sunny`) before running any test. Navigate to http://localhost:3999/login, enter credentials, and confirm redirect to `/slides`.

---

## Tests

### Test 1 — Dashboard loads with activity log table

- [ ] Sign in as `alan`
- [ ] Navigate to http://localhost:3999/dashboard
- [ ] Verify page title or heading shows "Dashboard" or "Activity Log"
- [ ] Verify the table renders with columns: `#`, `Time`, `Action`, `book_id`, `lesson_index`, `lesson_title`, `chapter_id`, `answer_result`, `recall_rate`
- [ ] Verify at least one row exists in the table

**Expected UI state**: Table visible with headers and at least one row. No spinner or error state.

**Report**: IN QUEUE
- Findings: —
- Improvement Proposals:
  + good to have - Column sorting — allow clicking column headers to sort rows

---

### Test 2 — All action types appear with correct values

- [ ] Ensure seed data is applied (Cleanup + re-insert)
- [ ] Sign in as `alan` and navigate to `/dashboard`
- [ ] Verify a row with Action = `LEARNT CHAPTER` exists with `chapter_id = 1`
- [ ] Verify rows with Action = `SKIP` exist with `answer_result = —` and `recall_rate = —`
- [ ] Verify a row with Action = `ANSWER` and `answer_result = wrong` and `recall_rate = 1.2`
- [ ] Verify a row with Action = `ANSWER` and `answer_result = correct` and `recall_rate` < 1.0
- [ ] Verify a row with Action = `ROUND CREATED (R0 done)` exists

**Expected UI state**: Each action type has its own row with correct column values; `—` shown for non-applicable cells.

**Report**: IN QUEUE
- Findings: —
- Improvement Proposals:
  + must have - Colour-code action types — LEARNT in green, SKIP in grey, ANSWER in blue, ROUND CREATED in italic

---

### Test 3 — Rows are ordered chronologically

- [ ] Sign in as `alan` and navigate to `/dashboard`
- [ ] Read the `Time` column for all rows
- [ ] Verify each row's time is equal to or later than the previous row (ascending order)

**Expected UI state**: First row is the earliest event; last row is the most recent.

**Report**: IN QUEUE
- Findings: —
- Improvement Proposals:
  + good to have - Newest-first toggle — option to reverse sort order

---

### Test 4 — Empty state when no activity exists

- [ ] Run cleanup SQL to empty all progress tables
- [ ] Sign in as `alan` and navigate to `/dashboard`
- [ ] Verify no table rows are shown
- [ ] Verify an empty-state message is displayed (e.g., "No activity yet. Start learning on the Slides page.")

**Expected UI state**: Table headers visible but no data rows; empty-state message present.

**Report**: IN QUEUE
- Findings: —
- Improvement Proposals:
  + good to have - Link in empty state — "Go to Slides" button that navigates to `/slides`

---

### Test 5 — Unauthenticated access is blocked

- [ ] Ensure user is signed out (clear session or open incognito)
- [ ] Navigate directly to http://localhost:3999/dashboard
- [ ] Verify redirect to `/login` page
- [ ] Verify `/dashboard` content is not visible

**Expected UI state**: Login page shown. No dashboard data exposed.

**Report**: IN QUEUE
- Findings: —
- Improvement Proposals:
  + must have - Preserve redirect — after login, redirect back to `/dashboard` instead of `/slides`
