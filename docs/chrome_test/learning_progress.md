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

The learning progress tab requires existing books, lessons, chapters, quizzes, and user progress data. The production database already has this data seeded.

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
- Improvement Proposals: --

---

### Test 2 — Switching to Learning Progress shows book cards with lesson tables

- [ ] Sign in as `alan`
- [ ] Navigate to http://localhost:3999/dashboard
- [ ] Click the "Learning Progress" tab
- [ ] Verify the activity log table disappears
- [ ] Verify at least one book card is visible with a book title header
- [ ] Verify each book card contains a table with columns: Lesson, Revision, Accuracy
- [ ] Verify at least one lesson row in the table

**Expected UI state**: One card per book. Each card has a lesson table.

**Report**: IN QUEUE
- Findings: --
- Improvement Proposals: --

---

### Test 3 — Accuracy trendline is visible below the lesson table

- [ ] Sign in as `alan` and navigate to `/dashboard`
- [ ] Click "Learning Progress" tab
- [ ] Find a book card that has quiz answer data
- [ ] Verify an SVG trendline chart is visible below the lesson table
- [ ] Verify the trendline has data points (not empty)

**Expected UI state**: SVG line chart below the lesson table showing accuracy trend data points.

**Report**: IN QUEUE
- Findings: --
- Improvement Proposals: --

---

### Test 4 — Empty state when no progress exists

- [ ] Run cleanup SQL to empty all progress tables
- [ ] Sign in as `alan` and navigate to `/dashboard`
- [ ] Click "Learning Progress" tab
- [ ] Verify an empty-state message is displayed
- [ ] Verify a link to `/slides` is present

**Expected UI state**: No book cards shown. Empty-state message with link to start learning.

**Report**: IN QUEUE
- Findings: --
- Improvement Proposals: --

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
