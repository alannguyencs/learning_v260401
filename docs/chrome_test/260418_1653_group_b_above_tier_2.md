# Chrome E2E Tests — Group B Above Tier 2 (Skipped Quizzes Resurface Before New Chapters)

## Remarks

- **Frontend port**: `http://localhost:3999`
- **Backend port**: `http://localhost:8999`
- **Sign-in flow**: Navigate to `http://localhost:3999/login`, enter username and password, click **Login** → redirected to `/slides`.
- **Sign-out flow**: Trigger logout via the logout button or navigate to `/login`.
- **Test user**: `alan` (student). Password lives in the local Postgres `users` table (see `docs/technical/testing_context.md`). There is only one application user role in this project, so Tests 2, 5, 7, and 10 exercise the feature's **ordering semantics** in place of the generic role-based / permission-guard categories.
- **Feature under test**: `SlideSelector.get_next_slide` priority order is now **Group A (non-skipped) → Group B (skipped) → Tier 2 (new chapter)**. Previously it was A → Tier 2 → B.
- **Cleanup**: Run the DELETE statements below before each test session to reset all user progress.
- **Screenshots directory**: `data/chrome_test_images/260418_1653_group_b_above_tier_2/`

> **Screenshot convention:**
> - Capture **one screenshot per Chrome action** — not one per "test step". A checklist bullet like *"Click Approve"* expands into:
>   1. Screenshot the Approve button highlighted/scrolled into view (before click) — `..._XX_approve_button.png`
>   2. Click it.
>   3. Screenshot the confirmation modal that appears (after click, if any) — `..._XX_approve_modal.png` or `..._XXb_approve_modal.png`
>   4. Click the modal's confirm button.
>   5. Screenshot the resulting state (status badge / workflow stage updated) — `..._XX_status_xxx.png`
> - Treat each of these as a distinct Chrome action. If an action yields a new visual state (modal opens, page navigates, status changes, form field appears), that state gets its own file.
> - Filename format: `test{id}_{HMMSS}_{NN}_{name}.png` where:
>   - `id` is the test number (`1`, `2`, `3`, …)
>   - `HMMSS` is the last 5 digits of the system clock `HHMMSS` at the moment of capture (so files sort in chronological order)
>   - `NN` is a two-digit action sequence number within the test (`01`, `02`, …); sub-actions may use a letter suffix (`06b`, `06c`) or the next sequential number — either is fine as long as the order is preserved
>   - `name` is a short kebab-snake label describing the visible state (`group_b_quiz_shown`, `tier_2_chapter`, `skip_button`, `feedback_panel`)
> - Before each `screencapture -R …` call, bring the target application tab to the front of its Chrome window via AppleScript (lookup by URL substring, set active tab index, set window index to 1, `activate`). This guards against the user browsing another tab/window while the test runs.

---

## Database Pre-Interaction

### Cleanup

Run this **before every test session** to reset all user progress. The content (books, lessons, chapters, quizzes) stays intact — only `alan`'s state is wiped.

```sql
DELETE FROM quiz_answer_log        WHERE username = 'alan';
DELETE FROM quiz_skip_log          WHERE username = 'alan';
DELETE FROM user_quiz_recall       WHERE username = 'alan';
DELETE FROM user_slide_like        WHERE username = 'alan';
DELETE FROM lesson_revision_rounds WHERE username = 'alan';
DELETE FROM user_chapter_progress  WHERE username = 'alan';
DELETE FROM user_lesson_count      WHERE username = 'alan';
DELETE FROM slide_history          WHERE username = 'alan';
DELETE FROM slide_position         WHERE username = 'alan';
DELETE FROM slide_chat_messages    WHERE username = 'alan';
```

### Seed Data — per-test preconditions (run before the specific test)

The 4 existing lessons in the database are the content under test:

| Book | Lesson ID | Lesson | Chapters | Quizzes |
|------|-----------|--------|----------|---------|
| coach | 3 | Time-Framed Learning | 5 (IDs 7–11) | 45 |
| themitmonk | 2 | 20 Quantum Cheat Codes | 5 (IDs 2–6) | 44 |
| themitmonk | 4 | From Homeless to MIT Grad | 4 (IDs 12–15) | 36 |
| Learning Phrases | 5 | English Cartoons: My Room | 2 (IDs 16–17) | 42 |

**Purpose of per-test seed:** mark a lesson fully chapter-learnt and create a due R0 so that Tier 1 quizzes are guaranteed to pool, and (where the test requires) pre-populate `quiz_skip_log` so Group B is deterministically populated. Without seeding, the user would have to mark many chapters + answer many quizzes through the UI before the ordering matters.

**Seed A — fully-learnt lesson + due R0 + one skipped quiz (used by Tests 2, 3, 7, 8):**

```sql
-- Mark all 2 chapters of Lesson 5 (English Cartoons: My Room) as learnt
INSERT INTO user_chapter_progress (username, chapter_id, learnt_at)
SELECT 'alan', id, NOW()
FROM chapters
WHERE lesson_id = 5
ON CONFLICT (username, chapter_id) DO NOTHING;

-- Create open R0 due NOW (due_at_lesson_count=0) with all lesson 5 quizzes counted
INSERT INTO lesson_revision_rounds
  (username, lesson_id, round_num, status, due_at_lesson_count, quizzes_in_round, quizzes_answered)
VALUES ('alan', 5, 0, 'open', 0,
        (SELECT COUNT(*) FROM chapter_quizzes cq JOIN chapters c ON c.id = cq.chapter_id WHERE c.lesson_id = 5),
        0)
ON CONFLICT (username, lesson_id, round_num) DO NOTHING;

-- Pre-skip one quiz from lesson 5 so Group B has exactly 1 member at test start
INSERT INTO quiz_skip_log (username, quiz_id, lesson_id, round_num, skipped_at)
SELECT 'alan', cq.id, 5, 0, NOW() - INTERVAL '5 minutes'
FROM chapter_quizzes cq
JOIN chapters c ON c.id = cq.chapter_id
WHERE c.lesson_id = 5
ORDER BY cq.id
LIMIT 1
ON CONFLICT DO NOTHING;
```

**Seed B — two skipped quizzes with different `skipped_at` (used by Tests 3, 8 for oldest-first / re-skip ordering):**

```sql
-- Requires Seed A to be applied first. Adds a second skipped quiz with a NEWER skipped_at.
INSERT INTO quiz_skip_log (username, quiz_id, lesson_id, round_num, skipped_at)
SELECT 'alan', cq.id, 5, 0, NOW()
FROM chapter_quizzes cq
JOIN chapters c ON c.id = cq.chapter_id
WHERE c.lesson_id = 5
ORDER BY cq.id
OFFSET 1 LIMIT 1
ON CONFLICT DO NOTHING;
```

**Seed C — all non-skipped due quizzes pre-answered (used by Tests 5, 10):**

```sql
-- Requires Seed A (or equivalent). Answers every unskipped lesson-5 quiz so Group A is empty
-- but R0 is not yet >50%-complete AND chapters-done (we set quizzes_answered manually to stay just under threshold).
INSERT INTO quiz_answer_log (username, quiz_id, lesson_id, round_num, is_correct, answered_at)
SELECT 'alan', cq.id, 5, 0, TRUE, NOW()
FROM chapter_quizzes cq
JOIN chapters c ON c.id = cq.chapter_id
LEFT JOIN quiz_skip_log qsl ON qsl.username = 'alan' AND qsl.quiz_id = cq.id
WHERE c.lesson_id = 5 AND qsl.quiz_id IS NULL
ON CONFLICT DO NOTHING;

UPDATE lesson_revision_rounds
SET quizzes_answered = (
  SELECT COUNT(*) FROM quiz_answer_log
  WHERE username = 'alan' AND lesson_id = 5 AND round_num = 0
)
WHERE username = 'alan' AND lesson_id = 5 AND round_num = 0;
```

### Seed Cleanup (between tests within the same session)

Re-run the top-level **Cleanup** block. Seed blocks A/B/C are idempotent except for the `INTERVAL '5 minutes'` timestamp — re-running Seed A will reset it.

---

## Pre-requisite

1. Run the top-level Cleanup SQL.
2. Start the app: `bash start_app.sh`.
3. Sign in as `alan` at `http://localhost:3999/login`.
4. For each test, run the Seed SQL listed in the test header before performing the Chrome actions.

---

## Test 1 — Desktop — Happy-path: Group A served first after chapters learnt

**User:** `alan`
**Viewport:** 1440 × 900 (set in Action 01; inherited by Tests 2–5)
**Seed:** none (start from clean user state).
**Goal:** Verify the baseline: once all chapters of a lesson are marked learnt, due revision quizzes (Group A) appear before any new chapter. This locks in the prerequisite for every later test — Group A always wins over Tier 2 content.

- [ ] **Action 01 — set desktop viewport:** call `mcp__claude-in-chrome__resize_window` with `width: 1440, height: 900`. Verify `window.innerWidth === 1440` via `javascript_tool`. **Screenshot:** `test1_{HMMSS}_01_desktop_viewport_set.png`
- [ ] **Action 02 — slides page loaded:** navigate to `http://localhost:3999/slides`. Verify the BookSelector and a chapter slide render. **Screenshot:** `test1_{HMMSS}_02_slides_loaded.png`
- [ ] **Action 03 — select "Learning Phrases" book:** open the book dropdown, click **Learning Phrases**. Verify a chapter slide from lesson 5 (English Cartoons: My Room) appears. **Screenshot:** `test1_{HMMSS}_03_book_selected.png`
- [ ] **Action 04 — mark chapter 1 learnt:** click **Mark as Learnt** (or press the down arrow). Verify the next slide appears. **Screenshot:** `test1_{HMMSS}_04_chapter_1_learnt.png`
- [ ] **Action 05 — mark chapter 2 learnt:** if the next slide is chapter 2, click **Mark as Learnt** again. **Screenshot:** `test1_{HMMSS}_05_chapter_2_learnt.png`
- [ ] **Action 06 — quiz slide appears (Tier 1 activated):** verify the next slide is a quiz from lesson 5 — the R0 activation gate has opened. Confirm the quiz question, round badge `Revision R0`, and book breadcrumb **Learning Phrases** are visible. **Screenshot:** `test1_{HMMSS}_06_group_a_quiz.png`
- [ ] **Action 07 — answer the quiz correctly:** for MC, select the correct option(s) and click **Submit**; for open-ended, type a short on-topic answer and submit. Verify the feedback panel appears. **Screenshot:** `test1_{HMMSS}_07_feedback_panel.png`
- [ ] **Action 08 — advance to next slide:** click the down arrow. Verify the next slide is another Group A quiz from lesson 5 (not a chapter from another book, because due quizzes block Tier 2). **Screenshot:** `test1_{HMMSS}_08_next_group_a_quiz.png`

**Expected:** Group A is non-empty after lesson 5 is fully chapter-learnt; the selector returns a lesson-5 quiz slide, not a chapter from a different book.

### Report

IN QUEUE

**Findings:** _(placeholder — to be filled after execution)_

**Improvement Proposals:**
+ _(placeholder — to be filled after execution)_

---

## Test 2 — Desktop — Core change: Group B resurfaces before Tier 2

**User:** `alan`
**Viewport:** 1440 × 900 (inherited from Test 1)
**Seed:** run **Cleanup** then **Seed A** (lesson 5 chapters learnt, R0 due, 1 skipped quiz in Group B).
**Goal:** Exhaust Group A (lesson 5 unskipped quizzes), then verify the **skipped quiz** reappears before any chapter from another book. This is the specific behavior this feature introduces.

- [ ] **Action 01 — slides page:** navigate to `http://localhost:3999/slides`. Choose **All Books** in the BookSelector (or no book filter) so Tier 2 would, under the OLD ordering, pull chapters from book 2 / book 3. **Screenshot:** `test2_{HMMSS}_01_all_books_selected.png`
- [ ] **Action 02 — first Group A quiz:** verify a lesson-5 quiz (Revision R0) renders. Answer correctly and click **Submit**. **Screenshot:** `test2_{HMMSS}_02_group_a_quiz_1.png`
- [ ] **Action 03 — advance past feedback:** click the down arrow. **Screenshot:** `test2_{HMMSS}_03_after_feedback_1.png`
- [ ] **Action 04 — loop until Group A empty:** repeat answer → advance until the selector serves the pre-skipped quiz (recognizable by quiz id / question text — record the pre-skipped quiz id from Seed A). **Screenshot:** `test2_{HMMSS}_04_group_a_exhausted.png`
- [ ] **Action 05 — assert Group B quiz surfaces before Tier 2:** verify the slide shown is the pre-skipped quiz from lesson 5 — **not** a chapter from books 2 / 3 / coach. Confirm the quiz id matches the Seed A quiz. **Screenshot:** `test2_{HMMSS}_05_group_b_quiz_served.png`
- [ ] **Action 06 — answer the Group B quiz:** submit a correct answer. Verify feedback panel appears. **Screenshot:** `test2_{HMMSS}_06_group_b_feedback.png`
- [ ] **Action 07 — Tier 2 fires only now:** click the down arrow. Verify the next slide is either a chapter from book 2, 3, or coach (Tier 2), OR a later-round quiz — and crucially is NOT the same lesson-5 Group B quiz (skip log was cleared on answer). **Screenshot:** `test2_{HMMSS}_07_tier_2_chapter_after_group_b.png`

**Expected:** the skipped quiz resurfaces between the last Group A quiz and the first Tier 2 chapter. Under the old ordering, a chapter from books 2/3/coach would have appeared at Action 05 and the Group B quiz would only surface at the very end.

### Report

IN QUEUE

**Findings:** _(placeholder — to be filled after execution)_

**Improvement Proposals:**
+ _(placeholder — to be filled after execution)_

---

## Test 3 — Desktop — Re-skip pushes a Group B quiz to the back of the queue

**User:** `alan`
**Viewport:** 1440 × 900
**Seed:** run **Cleanup**, then **Seed A**, then **Seed B** (Group B now has 2 quizzes: `quiz_old` skipped 5 min ago, `quiz_new` skipped just now).
**Goal:** Verify oldest-skip-first ordering in Group B, then verify that re-skipping `quiz_old` refreshes its `skipped_at` and sends it to the back — so `quiz_new` is served next.

- [ ] **Action 01 — slides page:** navigate to `http://localhost:3999/slides`. **Screenshot:** `test3_{HMMSS}_01_slides_loaded.png`
- [ ] **Action 02 — exhaust Group A:** answer all unskipped lesson-5 quizzes (loop: answer → down arrow). Record each quiz id. Stop when the next slide is a Group B quiz. **Screenshot:** `test3_{HMMSS}_02_group_a_exhausted.png`
- [ ] **Action 03 — quiz_old served first:** verify the slide shown is the quiz whose `skipped_at` is 5 minutes ago (the oldest). Record the quiz id as `quiz_old`. **Screenshot:** `test3_{HMMSS}_03_quiz_old_shown.png`
- [ ] **Action 04 — re-skip quiz_old:** click the down arrow **without submitting**. This posts `is_skip=true`; the skip log entry for `quiz_old` is refreshed to NOW. **Screenshot:** `test3_{HMMSS}_04_quiz_old_reskipped.png`
- [ ] **Action 05 — quiz_new served next:** verify the next slide is the other pre-skipped quiz (from Seed B) — `quiz_new`. Confirm it is a different quiz id from Action 03. **Screenshot:** `test3_{HMMSS}_05_quiz_new_shown.png`
- [ ] **Action 06 — answer quiz_new correctly:** submit an answer. **Screenshot:** `test3_{HMMSS}_06_quiz_new_feedback.png`
- [ ] **Action 07 — quiz_old returns (newest skip, served last):** click the down arrow. Verify the slide is `quiz_old` again (now the only remaining Group B member). **Screenshot:** `test3_{HMMSS}_07_quiz_old_returns.png`

**Expected:** Group B is served oldest-first (Action 03 = `quiz_old`). Re-skipping refreshes `skipped_at` so `quiz_new` takes the front (Action 05). When `quiz_new` is answered and removed, `quiz_old` returns (Action 07).

### Report

IN QUEUE

**Findings:** _(placeholder — to be filled after execution)_

**Improvement Proposals:**
+ _(placeholder — to be filled after execution)_

---

## Test 4 — Desktop — Validation: Group A always beats Group B (priority sanity)

**User:** `alan`
**Viewport:** 1440 × 900
**Seed:** run **Cleanup** then **Seed A** (lesson 5 fully chapter-learnt, R0 due, 1 skipped quiz).
**Goal:** A skipped quiz exists **and** non-skipped due quizzes exist. Verify the selector always serves a non-skipped Group A quiz first, never the skipped one.

- [ ] **Action 01 — slides page:** navigate to `http://localhost:3999/slides`. **Screenshot:** `test4_{HMMSS}_01_slides_loaded.png`
- [ ] **Action 02 — first slide is Group A:** verify the quiz shown has a quiz id **different** from the pre-skipped quiz id from Seed A. Confirm it is from lesson 5 / Revision R0. **Screenshot:** `test4_{HMMSS}_02_group_a_first.png`
- [ ] **Action 03 — answer correctly:** submit a correct answer. **Screenshot:** `test4_{HMMSS}_03_feedback.png`
- [ ] **Action 04 — second slide still Group A (skipped quiz still back-seated):** click the down arrow. Verify the next slide is another non-skipped lesson-5 quiz, not the pre-skipped one (because Group A is still non-empty). **Screenshot:** `test4_{HMMSS}_04_second_group_a.png`
- [ ] **Action 05 — invalid submit (edge case):** for an MC quiz, click **Submit** with no option selected. Verify either the submit is disabled OR the UI shows a validation error (no silent advance). **Screenshot:** `test4_{HMMSS}_05_invalid_submit.png`
- [ ] **Action 06 — recover and answer:** select a valid option, submit. Verify feedback appears normally. **Screenshot:** `test4_{HMMSS}_06_valid_answer.png`

**Expected:** Group A wins over Group B whenever both are non-empty. Group B only surfaces once Group A is drained.

### Report

IN QUEUE

**Findings:** _(placeholder — to be filled after execution)_

**Improvement Proposals:**
+ _(placeholder — to be filled after execution)_

---

## Test 5 — Desktop — Fallback: Tier 2 fires only when Group A and Group B are both empty

**User:** `alan`
**Viewport:** 1440 × 900
**Seed:** run **Cleanup**, then **Seed A**, then **Seed C** (all unskipped lesson-5 quizzes pre-answered — Group A empty; 1 skipped quiz remaining in Group B).
**Goal:** With Group A empty and Group B non-empty, the selector serves the Group B quiz first; only after Group B is drained does Tier 2 (a new-book chapter) appear.

- [ ] **Action 01 — slides page:** navigate to `http://localhost:3999/slides`. **Screenshot:** `test5_{HMMSS}_01_slides_loaded.png`
- [ ] **Action 02 — Group B quiz served (Group A drained):** verify the first quiz shown is the pre-skipped lesson-5 quiz. **Screenshot:** `test5_{HMMSS}_02_group_b_quiz.png`
- [ ] **Action 03 — answer the Group B quiz:** submit a correct answer. **Screenshot:** `test5_{HMMSS}_03_group_b_feedback.png`
- [ ] **Action 04 — advance:** click the down arrow. **Screenshot:** `test5_{HMMSS}_04_advance.png`
- [ ] **Action 05 — Tier 2 chapter appears:** verify the next slide is a **chapter** from a different book (book 2, 3, or coach) — Tier 2 only fires after both Group A and Group B are empty. Confirm `[Mark as Learnt]` button is visible. **Screenshot:** `test5_{HMMSS}_05_tier_2_chapter.png`

**Expected:** only after Group B is exhausted does the selector fall through to Tier 2 (new chapter).

### Report

IN QUEUE

**Findings:** _(placeholder — to be filled after execution)_

**Improvement Proposals:**
+ _(placeholder — to be filled after execution)_

---

## Test 6 — Mobile — Happy-path replay at 375 × 812

**User:** `alan`
**Viewport:** 375 × 812 (set in Action 01; inherited by Tests 7–10)
**Seed:** none (run **Cleanup** to restore clean state).
**Goal:** Replay Test 1 at mobile viewport. Verify Group A quizzes still surface first and the mobile layout has no overflow, small tap-targets, or cramped text.

- [ ] **Action 01 — set mobile viewport:** call `mcp__claude-in-chrome__resize_window` with `width: 375, height: 812`. Verify `window.innerWidth === 375` via `javascript_tool`. **Screenshot:** `test6_{HMMSS}_01_mobile_viewport_set.png`
- [ ] **Action 02 — slides page loaded:** navigate to `http://localhost:3999/slides`. Run the horizontal-overflow JS check; fail if `hasOverflow === true`. **Screenshot:** `test6_{HMMSS}_02_mobile_slides_loaded.png`
- [ ] **Action 03 — select "Learning Phrases" book:** open the mobile BookSelector, tap **Learning Phrases**. Confirm the dropdown is fully visible within 375 px (no right-edge clipping). **Screenshot:** `test6_{HMMSS}_03_mobile_book_selected.png`
- [ ] **Action 04 — mark chapter 1 learnt:** tap **Mark as Learnt** or the down arrow. Assert the down-arrow button has `height >= 44 px` via `getBoundingClientRect()`. **Screenshot:** `test6_{HMMSS}_04_mobile_chapter_1_learnt.png`
- [ ] **Action 05 — mark chapter 2 learnt:** tap **Mark as Learnt** again on chapter 2. **Screenshot:** `test6_{HMMSS}_05_mobile_chapter_2_learnt.png`
- [ ] **Action 06 — Group A quiz appears:** verify a lesson-5 quiz renders. Run the overflow check again; assert the quiz question text `font-size >= 12 px`. **Screenshot:** `test6_{HMMSS}_06_mobile_group_a_quiz.png`
- [ ] **Action 07 — answer correctly:** tap the correct option (or type open-ended answer) and tap **Submit**. Assert the **Submit** button has `height >= 44 px`. **Screenshot:** `test6_{HMMSS}_07_mobile_feedback.png`
- [ ] **Action 08 — scroll to bottom:** scroll the page to the bottom; verify all feedback content is reachable (no content hidden behind a fixed footer). **Screenshot:** `test6_{HMMSS}_08_mobile_scroll_bottom.png`
- [ ] **Action 09 — advance:** tap the down arrow. Verify the next slide is another Group A quiz. **Screenshot:** `test6_{HMMSS}_09_mobile_next_group_a.png`

**Mobile findings checklist:** horizontal overflow (none expected), tap-target ≥ 44 px, body text ≥ 12 px, all content reachable via scroll, no cramped padding.

### Report

IN QUEUE

**Findings:** _(placeholder — to be filled after execution)_

**Improvement Proposals:**
+ _(placeholder — to be filled after execution)_

---

## Test 7 — Mobile — Core change replay: Group B before Tier 2 at 375 × 812

**User:** `alan`
**Viewport:** 375 × 812
**Seed:** run **Cleanup** then **Seed A**.
**Goal:** Replay Test 2 at mobile viewport. Verify the skipped quiz still surfaces before any new-book chapter, AND that the Group-B quiz slide lays out cleanly on mobile.

- [ ] **Action 01 — slides page:** navigate to `http://localhost:3999/slides`. Run overflow check. **Screenshot:** `test7_{HMMSS}_01_mobile_slides_loaded.png`
- [ ] **Action 02 — first Group A quiz:** verify a lesson-5 quiz renders. Answer correctly and tap **Submit**. **Screenshot:** `test7_{HMMSS}_02_mobile_group_a_quiz.png`
- [ ] **Action 03 — loop answer + down arrow:** advance past feedback and answer each unskipped lesson-5 quiz. Record quiz ids. Stop when the pre-skipped quiz appears. **Screenshot:** `test7_{HMMSS}_03_mobile_group_a_exhausted.png`
- [ ] **Action 04 — Group B quiz appears:** confirm the slide is the pre-skipped quiz id from Seed A — not a chapter from another book. Run overflow check. **Screenshot:** `test7_{HMMSS}_04_mobile_group_b_quiz.png`
- [ ] **Action 05 — mobile tap-target assertion:** assert **Submit**, **down arrow**, and **Like** buttons each have `height >= 44 px`. **Screenshot:** `test7_{HMMSS}_05_mobile_tap_targets.png`
- [ ] **Action 06 — answer Group B quiz:** submit a correct answer. Verify feedback panel; scroll to bottom to confirm the good/bad points list is fully visible. **Screenshot:** `test7_{HMMSS}_06_mobile_group_b_feedback.png`
- [ ] **Action 07 — Tier 2 after Group B drained:** tap the down arrow. Verify the next slide is a chapter from a different book (Tier 2 now fires). **Screenshot:** `test7_{HMMSS}_07_mobile_tier_2_chapter.png`

**Mobile findings checklist:** no overflow on quiz slide or feedback panel; submit/down-arrow ≥ 44 px; feedback content readable without horizontal scroll.

### Report

IN QUEUE

**Findings:** _(placeholder — to be filled after execution)_

**Improvement Proposals:**
+ _(placeholder — to be filled after execution)_

---

## Test 8 — Mobile — Re-skip ordering at 375 × 812

**User:** `alan`
**Viewport:** 375 × 812
**Seed:** run **Cleanup** → **Seed A** → **Seed B**.
**Goal:** Replay Test 3 on mobile. Verify oldest-skip-first ordering holds and the re-skip (down arrow on a quiz without submitting) behaves the same on mobile.

- [ ] **Action 01 — slides page:** navigate to `http://localhost:3999/slides`. Run overflow check. **Screenshot:** `test8_{HMMSS}_01_mobile_slides_loaded.png`
- [ ] **Action 02 — exhaust Group A:** answer all unskipped lesson-5 quizzes. **Screenshot:** `test8_{HMMSS}_02_mobile_group_a_exhausted.png`
- [ ] **Action 03 — quiz_old served first:** confirm the slide is the older pre-skipped quiz. Record its id. **Screenshot:** `test8_{HMMSS}_03_mobile_quiz_old.png`
- [ ] **Action 04 — re-skip via down arrow (no submit):** tap the down arrow. Assert the down-arrow is `height >= 44 px`. Confirm no submit was fired (no feedback panel flashes). **Screenshot:** `test8_{HMMSS}_04_mobile_reskip_down_arrow.png`
- [ ] **Action 05 — quiz_new served next:** verify the slide is the other pre-skipped quiz (different id from Action 03). **Screenshot:** `test8_{HMMSS}_05_mobile_quiz_new.png`
- [ ] **Action 06 — answer quiz_new:** submit a correct answer. Scroll to bottom to confirm feedback content is reachable. **Screenshot:** `test8_{HMMSS}_06_mobile_quiz_new_feedback.png`
- [ ] **Action 07 — quiz_old returns:** tap the down arrow. Verify the slide is `quiz_old` again (newest skip after re-skip). **Screenshot:** `test8_{HMMSS}_07_mobile_quiz_old_returns.png`

**Mobile findings checklist:** down-arrow tap-target ≥ 44 px; no accidental submit on mobile touch; overflow check clean after each state change.

### Report

IN QUEUE

**Findings:** _(placeholder — to be filled after execution)_

**Improvement Proposals:**
+ _(placeholder — to be filled after execution)_

---

## Test 9 — Mobile — Edge cases & validation at 375 × 812

**User:** `alan`
**Viewport:** 375 × 812
**Seed:** run **Cleanup** then **Seed A**.
**Goal:** Exercise empty-state and validation paths on mobile: an MC quiz with no selection, an open-ended quiz with an empty answer, and the "All caught up" empty state (after answering everything including Group B).

- [ ] **Action 01 — slides page:** navigate. Run overflow check. **Screenshot:** `test9_{HMMSS}_01_mobile_slides_loaded.png`
- [ ] **Action 02 — MC submit with no option:** when an MC quiz appears, tap **Submit** without selecting any option. Verify either the submit is disabled OR a validation message is shown; assert no network POST fires via `read_network_requests`. **Screenshot:** `test9_{HMMSS}_02_mobile_mc_no_selection.png`
- [ ] **Action 03 — MC valid submit:** select an option and submit. Verify feedback panel. **Screenshot:** `test9_{HMMSS}_03_mobile_mc_valid.png`
- [ ] **Action 04 — advance to open-ended quiz:** tap down arrow until an open-ended quiz appears (free_recall / teach_back / cloze). **Screenshot:** `test9_{HMMSS}_04_mobile_open_ended.png`
- [ ] **Action 05 — empty open-ended submit:** tap **Submit** with an empty textarea. Verify validation behavior (disabled or error). **Screenshot:** `test9_{HMMSS}_05_mobile_open_empty.png`
- [ ] **Action 06 — drain everything:** type a valid answer, submit. Continue: answer each unskipped quiz, then the Group B quiz. **Screenshot:** `test9_{HMMSS}_06_mobile_everything_drained.png`
- [ ] **Action 07 — Tier 2 appears:** verify next slide is a chapter from book 2 / 3 / coach. Learn through it quickly and return to `/slides` with `All Books` filter. **Screenshot:** `test9_{HMMSS}_07_mobile_tier_2_chapter.png`

**Mobile findings checklist:** validation messages readable within 375 px; empty-state messages not truncated; open-ended textarea fills width without overflowing.

### Report

IN QUEUE

**Findings:** _(placeholder — to be filled after execution)_

**Improvement Proposals:**
+ _(placeholder — to be filled after execution)_

---

## Test 10 — Mobile — Guard: unauthenticated access at 375 × 812

**User:** (none — signed out)
**Viewport:** 375 × 812
**Seed:** none.
**Goal:** Confirm slide endpoints are auth-gated. This is the closest analogue to a "permission guard" test for a single-role app: anonymous users must not reach `/slides` and must not be able to skew the ordering via unauthenticated API calls.

- [ ] **Action 01 — sign out:** click the logout button (or navigate to `http://localhost:3999/login`). Verify the login form is shown. **Screenshot:** `test10_{HMMSS}_01_mobile_logged_out.png`
- [ ] **Action 02 — direct /slides access denied:** navigate to `http://localhost:3999/slides`. Verify the user is redirected to `/login` (or the page renders an unauthenticated state). **Screenshot:** `test10_{HMMSS}_02_mobile_slides_redirect.png`
- [ ] **Action 03 — unauthenticated API probe:** from the devtools / `javascript_tool`, run `fetch('/api/slides/current').then(r => r.status)`. Verify the status is 401/403. **Screenshot:** `test10_{HMMSS}_03_mobile_api_probe.png`
- [ ] **Action 04 — sign back in:** at `/login`, submit username `alan` + password. Verify redirect to `/slides`. Run overflow check on the landed page. **Screenshot:** `test10_{HMMSS}_04_mobile_signed_in.png`
- [ ] **Action 05 — verify ordering intact for authenticated user:** confirm the logged-in view still shows a quiz or chapter slide (no data leak from the auth boundary disturbed the selector). **Screenshot:** `test10_{HMMSS}_05_mobile_authenticated_slide.png`

**Mobile findings checklist:** login form inputs full-width, submit tap-target ≥ 44 px, redirect loops absent, unauthenticated API returns 4xx.

### Report

IN QUEUE

**Findings:** _(placeholder — to be filled after execution)_

**Improvement Proposals:**
+ _(placeholder — to be filled after execution)_
