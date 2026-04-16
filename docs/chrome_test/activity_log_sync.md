# Chrome E2E Test — Activity Log Sync

## Remarks

- Frontend: `http://localhost:3999`
- Backend: `http://localhost:8999`
- Single-user app — sign in as `alan`
- Tests verify that the activity log table persists slide history across db-compress/db-load cycles

## Database Pre-Interaction

Ensure at least one lesson is uploaded with chapters and quizzes:

```sql
-- Verify data exists
SELECT COUNT(*) FROM chapters;       -- should be > 0
SELECT COUNT(*) FROM chapter_quizzes; -- should be > 0
```

### Cleanup

```sql
-- Clear activity data from prior test runs
DELETE FROM quiz_answer_log WHERE username = 'alan';
DELETE FROM quiz_skip_log WHERE username = 'alan';
DELETE FROM user_chapter_progress WHERE username = 'alan';
DELETE FROM lesson_revision_rounds WHERE username = 'alan';
DELETE FROM user_quiz_recall WHERE username = 'alan';
DELETE FROM user_lesson_count WHERE username = 'alan';
DELETE FROM slide_history WHERE username = 'alan';
```

## Pre-requisite

Sign in as `alan` at `http://localhost:3999/login`.

---

## Test 1: Activity log shows events after slide interactions

**User:** alan

- [ ] Navigate to `http://localhost:3999/slides`
- [ ] Complete a chapter slide (click "Mark as learnt")
- [ ] Answer a quiz slide (submit any answer)
- [ ] Navigate to `http://localhost:3999/dashboard`
- [ ] Verify the Activity Log table shows at least 2 rows
- [ ] Verify LEARNT CHAPTER event appears with correct book/lesson/chapter info
- [ ] Verify ANSWER event appears with correct/wrong result

**Report:** `IN QUEUE`
- Findings:
- Improvement Proposals:

---

## Test 2: Activity log persists across db-compress and db-load

**User:** alan

- [ ] After Test 1, note the number of rows and their order in the Activity Log
- [ ] Run `python3 .claude/skills/db-compress/compress.py --project-root .` in terminal
- [ ] Verify `data/db/slide_history.sql` file is created and has INSERT statements
- [ ] Run `python3 .claude/skills/db-compress/restore.py --project-root . --schema` in terminal
- [ ] Verify restore output shows `slide_history` table with correct row count
- [ ] Refresh `http://localhost:3999/dashboard`
- [ ] Verify the Activity Log shows the same rows in the same order as before the export/restore

**Report:** `IN QUEUE`
- Findings:
- Improvement Proposals:

---

## Test 3: Empty state when no activity exists

**User:** alan

- [ ] Clear all activity: run cleanup SQL from Database Pre-Interaction section
- [ ] Navigate to `http://localhost:3999/dashboard`
- [ ] Verify "No activity yet." message is displayed
- [ ] Verify "Start learning on the Slides page" link is present and navigates to `/slides`

**Report:** `IN QUEUE`
- Findings:
- Improvement Proposals:

---

## Test 4: Activity log ordering matches slide interaction order

**User:** alan

- [ ] Navigate to `http://localhost:3999/slides`
- [ ] Complete 3 interactions in sequence (e.g., learn chapter, answer quiz, skip quiz)
- [ ] Navigate to `http://localhost:3999/dashboard`
- [ ] Verify rows appear in chronological order (oldest first)
- [ ] Verify each row's Date/Time matches the interaction sequence

**Report:** `IN QUEUE`
- Findings:
- Improvement Proposals:

---

## Test 5: Slide history table included in db-compress export

**User:** alan (terminal)

- [ ] Ensure there is activity in the database (run Test 1 first if needed)
- [ ] Run `python3 .claude/skills/db-compress/compress.py --project-root .`
- [ ] Verify output includes `slide_history` with row count > 0
- [ ] Verify `data/db/slide_history.sql` contains valid INSERT statements
- [ ] Run `python3 .claude/skills/db-compress/restore.py --project-root .`
- [ ] Verify restore output shows `slide_history` with matching row count

**Report:** `IN QUEUE`
- Findings:
- Improvement Proposals:
