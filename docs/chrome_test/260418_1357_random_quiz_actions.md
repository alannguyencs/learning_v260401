# Chrome E2E Tests — Random Quiz Actions on /slides

## Remarks

- **Frontend port**: `http://localhost:3999`
- **Backend port**: `http://localhost:8999`
- **Sign-in flow**: Navigate to `http://localhost:3999/login`, enter username `alan` and password (from `.env`), click **Login** → redirected to `/slides`.
- **Sign-out flow**: Trigger logout via the logout control or navigate directly to `/login`.
- **Test approach**: After landing on `/slides`, drive a **random sequence of 8 quiz interactions**, where each interaction is uniformly chosen from `{answer correctly, answer wrongly, skip}`. The randomness is deterministic per run via a seed printed to the console at Action 03 of Tests 1 and 6 (so the run is reproducible). Chapter slides encountered along the way are auto-marked-learnt to keep the stream flowing into quizzes (the activation gate must be satisfied for Tier 1 quizzes to surface).
- **Cleanup**: Run the DELETE statements below before each test session to reset all user progress. Content (books, lessons, chapters, quizzes) is preserved.
- **Screenshots directory**: `data/chrome_test_images/260418_1357_random_quiz_actions/`

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
>   - `NN` is a two-digit action sequence number within the test (`01`, `02`, …); sub-actions may use a letter suffix (`06b`, `06c`) or the next sequential number
>   - `name` is a short kebab-snake label describing the visible state (`list_empty`, `quiz_loaded`, `answer_correct`, `feedback_passed`)
> - Before each `screencapture -R …` call, bring the target application tab to the front of its Chrome window via AppleScript (lookup by URL substring, set active tab index, set window index to 1, `activate`). This guards against the user browsing another tab/window while the test runs.

---

## Database Pre-Interaction

### Cleanup

Run **before every test session** to reset all user progress for `alan`. Content rows are untouched.

```sql
DELETE FROM quiz_answer_log         WHERE username = 'alan';
DELETE FROM quiz_skip_log           WHERE username = 'alan';
DELETE FROM user_quiz_recall        WHERE username = 'alan';
DELETE FROM lesson_revision_rounds  WHERE username = 'alan';
DELETE FROM user_chapter_progress   WHERE username = 'alan';
DELETE FROM user_lesson_count       WHERE username = 'alan';
DELETE FROM slide_history           WHERE username = 'alan';
DELETE FROM slide_position          WHERE username = 'alan';
DELETE FROM slide_chat_messages     WHERE username = 'alan';
```

### Seed data

No additional seed data required. Tests rely on the 4 lessons already present:

| Book              | Lesson ID | Lesson                       | Chapters       | Quizzes |
|-------------------|-----------|------------------------------|----------------|---------|
| coach             | 3         | Time-Framed Learning         | 5 (IDs 7–11)   | 45      |
| themitmonk        | 2         | 20 Quantum Cheat Codes       | 5 (IDs 2–6)    | 44      |
| themitmonk        | 4         | From Homeless to MIT Grad    | 4 (IDs 12–15)  | 36      |
| Learning Phrases  | 5         | English Cartoons: My Room    | 2 (IDs 16–17)  | 42      |

---

## Pre-requisite

1. Apply the cleanup SQL above: `psql -U alan learning_v2604 -f cleanup.sql`
2. Start the application: `bash start_app.sh`
3. Sign in as `alan` at `http://localhost:3999/login` per the procedure in `docs/technical/testing_context.md`.

---

## Test 1 — Random quiz action sequence on /slides (Desktop)

**User:** `alan` (student)
**Goal:** From a clean slate, navigate to `/slides`, satisfy the activation gate by marking chapters learnt, then perform a **random sequence of 8 quiz interactions** uniformly drawn from `{correct, wrong, skip}`. Verify each interaction's resulting UI state matches the chosen action.

- [ ] **Action 01 — set desktop viewport:** call `mcp__claude-in-chrome__resize_window` with `width: 1440, height: 900`. Verify `window.innerWidth === 1440` via `javascript_tool`. **Screenshot:** `test1_{HMMSS}_01_desktop_viewport_set.png`

- [ ] **Action 02 — slides page loaded:** navigate to `http://localhost:3999/slides`. Verify the slides page mounts: BookSelector dropdown is visible, a slide is rendered (chapter or "All caught up" — on a fresh slate this is a chapter from Tier 2). **Screenshot:** `test1_{HMMSS}_02_slides_loaded.png`

- [ ] **Action 03 — seed RNG and log plan:** in `javascript_tool`, run `const seed = Date.now() & 0xffff; const rng = (() => { let s = seed; return () => { s = (s * 1103515245 + 12345) & 0x7fffffff; return s; }; })(); const choices = ['correct','wrong','skip']; const plan = Array.from({length:8}, () => choices[rng() % 3]); console.log('[random-quiz-actions] seed=' + seed + ' plan=' + JSON.stringify(plan)); window.__quizPlan = plan;` — confirm the console log includes `[random-quiz-actions] seed=` and an 8-element plan. **Screenshot:** `test1_{HMMSS}_03_plan_logged.png`

- [ ] **Action 04 — open activation gate (mark chapters learnt):** while the current slide is a chapter (DOM contains `Mark as Learnt` button or equivalent), click the down arrow to mark the chapter learnt and advance. Repeat until a quiz slide appears (DOM contains `Submit Answer` button, or `data-testid="quiz-slide"`/`feedback-panel`). Capture one screenshot of the **first quiz** shown. **Screenshot:** `test1_{HMMSS}_04_first_quiz_visible.png`

- [ ] **Action 05 — interaction #1 (planned action #1):** read `window.__quizPlan[0]`. Branch:
  - `correct` → For MC: select the option(s) listed in `quiz.correct_options` (read via `javascript_tool` on the React props or the `correct` server response after Submit). For open-ended: type the `quiz.expected_answer` verbatim. Click **Submit Answer**.
  - `wrong` → For MC: select any option **not** in `quiz.correct_options`. For open-ended: type a clearly off-topic string (`"unrelated nonsense answer"`). Click **Submit Answer**.
  - `skip` → Do **not** submit; click the **down arrow** (skip control) to push the quiz to Group B and advance.
  **Screenshot:** `test1_{HMMSS}_05_interaction_01_{action}.png` (substitute `{action}` with `correct` / `wrong` / `skip`).

- [ ] **Action 05b — verify result of interaction #1:** depending on the chosen action:
  - `correct` → assert `data-testid="feedback-panel"` is visible and contains `✓ PASSED` (green text).
  - `wrong` → assert `data-testid="feedback-panel"` is visible and contains `✗ FAILED` (red text).
  - `skip` → assert no feedback panel rendered; the next slide (chapter or different quiz) is now shown.
  **Screenshot:** `test1_{HMMSS}_05b_result_01_{action}.png`

- [ ] **Action 06 — advance from interaction #1:** if the previous action showed feedback (`correct` or `wrong`), click the down arrow to advance to the next slide. If it was `skip`, the page already advanced — skip this sub-step and capture the current slide. Verify the new slide is either a quiz or a chapter. If it's a chapter, repeat the auto-mark-learnt loop from Action 04 until a quiz appears. **Screenshot:** `test1_{HMMSS}_06_next_quiz_visible.png`

- [ ] **Action 07 — interaction #2 (planned action #2):** repeat Action 05's branching logic using `window.__quizPlan[1]`. **Screenshot:** `test1_{HMMSS}_07_interaction_02_{action}.png`

- [ ] **Action 07b — verify + advance to next quiz:** repeat the assertion + auto-mark-learnt loop from Actions 05b and 06. **Screenshot:** `test1_{HMMSS}_07b_next_quiz_visible.png`

- [ ] **Action 08 — interaction #3 (planned action #3):** repeat Action 05's branching logic using `window.__quizPlan[2]`. **Screenshot:** `test1_{HMMSS}_08_interaction_03_{action}.png`

- [ ] **Action 08b — verify + advance:** repeat assertion + advance loop. **Screenshot:** `test1_{HMMSS}_08b_next_quiz_visible.png`

- [ ] **Action 09 — interaction #4 (planned action #4):** repeat Action 05 with `window.__quizPlan[3]`. **Screenshot:** `test1_{HMMSS}_09_interaction_04_{action}.png`

- [ ] **Action 09b — verify + advance:** repeat assertion + advance loop. **Screenshot:** `test1_{HMMSS}_09b_next_quiz_visible.png`

- [ ] **Action 10 — interaction #5 (planned action #5):** repeat Action 05 with `window.__quizPlan[4]`. **Screenshot:** `test1_{HMMSS}_10_interaction_05_{action}.png`

- [ ] **Action 10b — verify + advance:** repeat assertion + advance loop. **Screenshot:** `test1_{HMMSS}_10b_next_quiz_visible.png`

- [ ] **Action 11 — interaction #6 (planned action #6):** repeat Action 05 with `window.__quizPlan[5]`. **Screenshot:** `test1_{HMMSS}_11_interaction_06_{action}.png`

- [ ] **Action 11b — verify + advance:** repeat assertion + advance loop. **Screenshot:** `test1_{HMMSS}_11b_next_quiz_visible.png`

- [ ] **Action 12 — interaction #7 (planned action #7):** repeat Action 05 with `window.__quizPlan[6]`. **Screenshot:** `test1_{HMMSS}_12_interaction_07_{action}.png`

- [ ] **Action 12b — verify + advance:** repeat assertion + advance loop. **Screenshot:** `test1_{HMMSS}_12b_next_quiz_visible.png`

- [ ] **Action 13 — interaction #8 (planned action #8):** repeat Action 05 with `window.__quizPlan[7]`. **Screenshot:** `test1_{HMMSS}_13_interaction_08_{action}.png`

- [ ] **Action 13b — final verify:** verify the resulting UI state matches the planned action. **Screenshot:** `test1_{HMMSS}_13b_result_08_{action}.png`

- [ ] **Action 14 — DB verification:** in a separate shell, run `psql -U alan learning_v2604 -c "SELECT (SELECT COUNT(*) FROM quiz_answer_log WHERE username='alan' AND is_correct=true) AS correct_count, (SELECT COUNT(*) FROM quiz_answer_log WHERE username='alan' AND is_correct=false) AS wrong_count, (SELECT COUNT(*) FROM quiz_skip_log WHERE username='alan') AS skip_count;"`. Counts must match the tally of `correct` / `wrong` / `skip` entries in `window.__quizPlan` (skip count may be lower if the same quiz was re-skipped — Group B re-skips refresh `skipped_at` rather than insert a new row). **Screenshot:** `test1_{HMMSS}_14_db_counts.png`

**Expected UI states:**
- After Action 02: BookSelector visible; an active slide rendered; `[↓]` ArrowDown visible at viewport bottom; `[↑]` ArrowUp hidden (no history yet).
- After every `correct` action: green `✓ PASSED` badge inside `data-testid="feedback-panel"`; Submit Answer button is hidden.
- After every `wrong` action: red `✗ FAILED` badge; for MC, the user's wrong choice is highlighted red and the correct option is highlighted green; for cloze, the correct answer is shown in a yellow callout.
- After every `skip` action: no feedback panel; URL stays `/slides` but a new slide is rendered (slide identifier in DOM differs from previous quiz).
- Throughout: `[↑]` ArrowUp becomes visible after the first advance and remains visible.

**Report:** `IN QUEUE`
- Findings:
  - _(populate during execution)_
- Improvement Proposals:
  - `+ {priority} - {proposal name} - brief description`

---

## Test 2 — Role-based visibility on /slides (Desktop)

**User:** `alan` (only test user available per `testing_context.md`).
**Goal:** Verify that `/slides` is reachable for the authenticated `alan` user, and that the BookSelector exposes the books `alan` has content for. (This project currently lists only a `student` role in `testing_context.md`, so the role matrix is degenerate; this test documents the single-role baseline so any future multi-role expansion has a concrete starting point.)

- [ ] **Action 01 — slides reachable while signed in:** with viewport still at 1440 × 900 from Test 1, navigate to `http://localhost:3999/slides`. Verify the page loads (no redirect to `/login`). **Screenshot:** `test2_{HMMSS}_01_slides_authed.png`

- [ ] **Action 02 — book selector populated:** open the BookSelector dropdown. Verify the option list contains, at minimum, the seeded books (`coach`, `themitmonk`, `Learning Phrases`) plus an `All Books` option. **Screenshot:** `test2_{HMMSS}_02_book_dropdown.png`

- [ ] **Action 03 — filter by single book:** select `themitmonk` from the dropdown. Verify the displayed slide's breadcrumb references a `themitmonk` lesson (e.g., `20 Quantum Cheat Codes` or `From Homeless to MIT Grad`). **Screenshot:** `test2_{HMMSS}_03_book_filtered.png`

- [ ] **Action 04 — switch back to All Books:** select `All Books`. Verify a slide loads from any of the seeded books. **Screenshot:** `test2_{HMMSS}_04_all_books.png`

**Report:** `IN QUEUE`
- Findings:
  - _(populate during execution)_
- Improvement Proposals:
  - `+ good to have - seed a second non-student role to make this test non-degenerate`

---

## Test 3 — Multi-user workflow on /slides (Desktop)

**User:** `alan` (single-user environment per `testing_context.md`).
**Goal:** Multi-user flows are not yet representable in this project (only one test user). This test documents the **same-user, multi-session** flow as the closest analogue: sign out, sign back in, verify the saved slide position survives.

- [ ] **Action 01 — capture current slide identifier:** on `/slides`, run `javascript_tool`: `JSON.stringify({type: document.querySelector('[data-testid="quiz-slide"]') ? 'quiz' : 'chapter', text: document.body.innerText.slice(0, 200)})`. Store the result. **Screenshot:** `test3_{HMMSS}_01_pre_logout_slide.png`

- [ ] **Action 02 — sign out:** click the logout control (or navigate to `/login`). Verify the login form is shown. **Screenshot:** `test3_{HMMSS}_02_login_page.png`

- [ ] **Action 03 — sign in again as alan:** enter `alan` + password, click Login. Verify redirect to `/slides`. **Screenshot:** `test3_{HMMSS}_03_signed_in_again.png`

- [ ] **Action 04 — verify slide position persisted:** run the same `javascript_tool` snippet from Action 01. The slide type and content text must match (server-stored `slide_position` row). **Screenshot:** `test3_{HMMSS}_04_post_login_slide.png`

**Report:** `IN QUEUE`
- Findings:
  - _(populate during execution)_
- Improvement Proposals:
  - `+ good to have - add a second test user to enable a true cross-user workflow test`

---

## Test 4 — Validation & edge cases on /slides (Desktop)

**User:** `alan`
**Goal:** Verify the UI handles invalid/empty inputs and the all-caught-up boundary.

- [ ] **Action 01 — submit empty MC answer:** on a quiz slide (force a quiz by repeatedly clicking the down arrow if a chapter is shown), without selecting any option, attempt to click **Submit Answer**. Verify the button is disabled OR the request is rejected client-side (no feedback panel rendered). **Screenshot:** `test4_{HMMSS}_01_empty_submit_blocked.png`

- [ ] **Action 02 — submit empty open-ended answer:** if the current quiz is open-ended (`free_recall`/`teach_back`/`cloze`), leave the textarea/cloze input empty and attempt to submit. Verify submit is blocked. **Screenshot:** `test4_{HMMSS}_02_empty_textarea_submit.png`

- [ ] **Action 03 — submit whitespace-only answer:** enter only spaces in the textarea/cloze input. Verify submit is blocked (`answer.trim()` guard in `QuizSlide.handleSubmit`). **Screenshot:** `test4_{HMMSS}_03_whitespace_blocked.png`

- [ ] **Action 04 — back-arrow at history start:** click the up arrow (back) until it disappears. Verify the up arrow is hidden when `has_previous=false` (no further back navigation possible). **Screenshot:** `test4_{HMMSS}_04_no_back_arrow.png`

- [ ] **Action 05 — all-caught-up state (forced):** in the DB, run `psql -U alan learning_v2604 -c "DELETE FROM lesson_revision_rounds WHERE username='alan'; UPDATE user_chapter_progress SET learnt_at = NOW() WHERE username='alan'; INSERT INTO user_chapter_progress (username, chapter_id, lesson_id, learnt_at) SELECT 'alan', c.id, c.lesson_id, NOW() FROM chapters c WHERE NOT EXISTS (SELECT 1 FROM user_chapter_progress p WHERE p.username='alan' AND p.chapter_id=c.id);"` then refresh `/slides`. Verify the **All Caught Up** message is shown and no down arrow is visible. **Screenshot:** `test4_{HMMSS}_05_all_caught_up.png`

**Report:** `IN QUEUE`
- Findings:
  - _(populate during execution)_
- Improvement Proposals:
  - `+ {priority} - {proposal name} - brief description`

---

## Test 5 — Permission guard on /slides (Desktop)

**User:** unauthenticated visitor
**Goal:** Verify `/slides` requires authentication; an unauthenticated request is redirected to `/login`.

- [ ] **Action 01 — sign out fully:** click the logout control or call `fetch('/api/auth/logout', {method:'POST'})` then navigate to `/login`. Confirm session cookie is cleared. **Screenshot:** `test5_{HMMSS}_01_logged_out.png`

- [ ] **Action 02 — direct visit to /slides while unauth:** navigate to `http://localhost:3999/slides`. Verify the URL redirects to (or replaces with) `/login`, and the login form is shown. **Screenshot:** `test5_{HMMSS}_02_redirected_to_login.png`

- [ ] **Action 03 — direct API call returns 401:** in `javascript_tool`, run `fetch('/api/slides/current').then(r => r.status)` and assert the response status is `401`. **Screenshot:** `test5_{HMMSS}_03_api_401.png`

- [ ] **Action 04 — restore signed-in state for downstream tests:** navigate to `/login`, sign in as `alan`. Verify redirect to `/slides`. **Screenshot:** `test5_{HMMSS}_04_resigned_in.png`

**Report:** `IN QUEUE`
- Findings:
  - _(populate during execution)_
- Improvement Proposals:
  - `+ {priority} - {proposal name} - brief description`

---

## Test 6 — Random quiz action sequence on /slides (Mobile)

**User:** `alan`
**Goal:** Replay Test 1 at mobile viewport (375 × 812). Verify the same random quiz action sequence works on a phone screen, and add per-checkpoint mobile assertions (overflow, tap-target size, readability, scroll reachability).

- [ ] **Action 01 — set mobile viewport:** call `mcp__claude-in-chrome__resize_window` with `width: 375, height: 812`. Verify `window.innerWidth === 375` via `javascript_tool`. **Screenshot:** `test6_{HMMSS}_01_mobile_viewport_set.png`

- [ ] **Action 02 — slides page loaded (mobile):** navigate to `http://localhost:3999/slides`. Verify mobile layout: BookSelector and active slide both render without horizontal scroll. **Screenshot:** `test6_{HMMSS}_02_slides_loaded_mobile.png`

- [ ] **Action 02b — overflow check (slides page):** run the horizontal-overflow JS from `generation-rules.md` §"Per-test mobile assertions". Fail the test if `hasOverflow === true`; record the offending elements in Findings. **Screenshot:** `test6_{HMMSS}_02b_overflow_check_slides.png`

- [ ] **Action 03 — seed RNG (mobile run):** rerun the seed-and-plan JS from Test 1 Action 03 (a fresh seed; mobile run gets its own plan). Confirm the plan logs to console. **Screenshot:** `test6_{HMMSS}_03_plan_logged_mobile.png`

- [ ] **Action 04 — open activation gate (mark chapters learnt) on mobile:** auto-mark-learnt chapters by clicking the down arrow until a quiz appears. Verify the down arrow is reachable (within viewport, not clipped) at mobile width. **Screenshot:** `test6_{HMMSS}_04_first_quiz_mobile.png`

- [ ] **Action 04b — tap-target check (down arrow + Submit Answer):** measure `getBoundingClientRect().height` for the down-arrow control and (when on a quiz) the Submit Answer button via `javascript_tool`. Fail the test if either is `< 44`. **Screenshot:** `test6_{HMMSS}_04b_tap_targets.png`

- [ ] **Action 05 — interaction #1 (mobile, planned action #1):** apply the same branching as Test 1 Action 05 using the mobile run's plan. **Screenshot:** `test6_{HMMSS}_05_interaction_01_{action}_mobile.png`

- [ ] **Action 05b — verify result + readability:** assert the resulting UI state matches the chosen action (Test 1 Action 05b). Then run the text-readability JS: assert `parseFloat(getComputedStyle(document.querySelector('[data-testid="feedback-panel"]') || document.body).fontSize) >= 12`. **Screenshot:** `test6_{HMMSS}_05b_result_readability.png`

- [ ] **Action 06 — interaction #2 (mobile):** repeat Action 05 with plan index 1. **Screenshot:** `test6_{HMMSS}_06_interaction_02_{action}_mobile.png`

- [ ] **Action 07 — interaction #3 (mobile):** repeat with plan index 2. **Screenshot:** `test6_{HMMSS}_07_interaction_03_{action}_mobile.png`

- [ ] **Action 08 — interaction #4 (mobile):** repeat with plan index 3. **Screenshot:** `test6_{HMMSS}_08_interaction_04_{action}_mobile.png`

- [ ] **Action 09 — interaction #5 (mobile):** repeat with plan index 4. **Screenshot:** `test6_{HMMSS}_09_interaction_05_{action}_mobile.png`

- [ ] **Action 10 — interaction #6 (mobile):** repeat with plan index 5. **Screenshot:** `test6_{HMMSS}_10_interaction_06_{action}_mobile.png`

- [ ] **Action 11 — interaction #7 (mobile):** repeat with plan index 6. **Screenshot:** `test6_{HMMSS}_11_interaction_07_{action}_mobile.png`

- [ ] **Action 12 — interaction #8 (mobile):** repeat with plan index 7. **Screenshot:** `test6_{HMMSS}_12_interaction_08_{action}_mobile.png`

- [ ] **Action 12b — overflow check after final interaction:** rerun the horizontal-overflow JS. Fail the test if `hasOverflow === true`. **Screenshot:** `test6_{HMMSS}_12b_overflow_check_final.png`

- [ ] **Action 13 — scroll reachability check:** scroll to the bottom of the page (`window.scrollTo(0, document.body.scrollHeight)`); verify the down arrow / Submit button / feedback panel is still visible and not hidden behind a fixed footer. **Screenshot:** `test6_{HMMSS}_13_scroll_bottom.png`

- [ ] **Action 14 — DB verification (mobile run):** repeat Test 1 Action 14's `psql` count check. Counts must match the mobile-run plan's tally. **Screenshot:** `test6_{HMMSS}_14_db_counts_mobile.png`

**Mobile-specific visual assessment:** when reviewing screenshots, flag any of: horizontal overflow, body text below ~12 px, tap targets below ~44 px, cramped padding, overlapping elements, form inputs narrower than viewport, side-by-side columns too narrow to read, truncated text where wrap is expected, images overflowing, or columns that should be hidden via `hidden sm:table-cell` still rendering.

**Report:** `IN QUEUE`
- Findings:
  - _(populate during execution)_
- Improvement Proposals:
  - `+ {priority} - {proposal name} - brief description`

---

## Test 7 — Role-based visibility on /slides (Mobile)

**User:** `alan`

- [ ] **Action 01 — slides reachable while signed in (mobile):** with viewport still 375 × 812 from Test 6, navigate to `/slides`. **Screenshot:** `test7_{HMMSS}_01_slides_authed_mobile.png`

- [ ] **Action 02 — book selector usable on mobile:** open BookSelector. Verify the dropdown options are full-width and readable at 375 px. **Screenshot:** `test7_{HMMSS}_02_book_dropdown_mobile.png`

- [ ] **Action 02b — overflow check on dropdown open:** run horizontal-overflow JS. **Screenshot:** `test7_{HMMSS}_02b_overflow_dropdown.png`

- [ ] **Action 03 — filter by single book (mobile):** select `themitmonk`. Verify the slide breadcrumb is from `themitmonk`. **Screenshot:** `test7_{HMMSS}_03_book_filtered_mobile.png`

- [ ] **Action 04 — switch back to All Books (mobile):** select `All Books`. Verify a slide renders. **Screenshot:** `test7_{HMMSS}_04_all_books_mobile.png`

- [ ] **Action 04b — readability check on breadcrumb:** assert breadcrumb text font-size ≥ 12 px. **Screenshot:** `test7_{HMMSS}_04b_readability.png`

**Report:** `IN QUEUE`
- Findings:
  - _(populate during execution)_
- Improvement Proposals:
  - `+ {priority} - {proposal name} - brief description`

---

## Test 8 — Multi-user workflow on /slides (Mobile)

**User:** `alan` (single-user environment — same-user multi-session per Test 3).

- [ ] **Action 01 — capture pre-logout slide (mobile):** run the `javascript_tool` snippet from Test 3 Action 01. **Screenshot:** `test8_{HMMSS}_01_pre_logout_mobile.png`

- [ ] **Action 02 — sign out (mobile):** click logout. Verify the login form renders correctly at 375 px (inputs full-width, button reachable). **Screenshot:** `test8_{HMMSS}_02_login_page_mobile.png`

- [ ] **Action 02b — overflow check on login page:** run horizontal-overflow JS. **Screenshot:** `test8_{HMMSS}_02b_overflow_login.png`

- [ ] **Action 03 — sign in again (mobile):** enter `alan` + password, tap Login. Verify Login button height ≥ 44 px before tapping. Verify redirect to `/slides`. **Screenshot:** `test8_{HMMSS}_03_signed_in_mobile.png`

- [ ] **Action 04 — verify slide position persisted (mobile):** rerun the snippet from Action 01; assert match. **Screenshot:** `test8_{HMMSS}_04_post_login_mobile.png`

**Report:** `IN QUEUE`
- Findings:
  - _(populate during execution)_
- Improvement Proposals:
  - `+ {priority} - {proposal name} - brief description`

---

## Test 9 — Validation & edge cases on /slides (Mobile)

**User:** `alan`

- [ ] **Action 01 — submit empty MC answer (mobile):** on a quiz slide, attempt to tap **Submit Answer** without selecting an option. Assert blocked. **Screenshot:** `test9_{HMMSS}_01_empty_submit_mobile.png`

- [ ] **Action 02 — submit empty open-ended (mobile):** if open-ended, leave textarea empty, tap submit. Assert blocked. **Screenshot:** `test9_{HMMSS}_02_empty_textarea_mobile.png`

- [ ] **Action 02b — tap-target check on Submit Answer:** measure Submit button height; assert ≥ 44 px at 375 × 812. **Screenshot:** `test9_{HMMSS}_02b_submit_tap_target.png`

- [ ] **Action 03 — back-arrow disappears at history start (mobile):** tap up arrow until it disappears. Assert hidden. **Screenshot:** `test9_{HMMSS}_03_no_back_arrow_mobile.png`

- [ ] **Action 04 — all-caught-up state on mobile:** force the all-caught-up state via the Test 4 Action 05 SQL, refresh `/slides`. Verify the empty-state message renders without overflow on 375 px. **Screenshot:** `test9_{HMMSS}_04_all_caught_up_mobile.png`

- [ ] **Action 04b — overflow check on all-caught-up:** run horizontal-overflow JS. **Screenshot:** `test9_{HMMSS}_04b_overflow_caught_up.png`

**Report:** `IN QUEUE`
- Findings:
  - _(populate during execution)_
- Improvement Proposals:
  - `+ {priority} - {proposal name} - brief description`

---

## Test 10 — Permission guard on /slides (Mobile)

**User:** unauthenticated visitor

- [ ] **Action 01 — sign out fully (mobile):** clear session and navigate to `/login`. **Screenshot:** `test10_{HMMSS}_01_logged_out_mobile.png`

- [ ] **Action 02 — direct visit to /slides while unauth (mobile):** navigate to `/slides`. Assert redirect to `/login`. **Screenshot:** `test10_{HMMSS}_02_redirected_mobile.png`

- [ ] **Action 02b — overflow check on login page:** run horizontal-overflow JS. **Screenshot:** `test10_{HMMSS}_02b_overflow_login_mobile.png`

- [ ] **Action 03 — direct API call returns 401 (mobile):** run `fetch('/api/slides/current').then(r => r.status)`; assert `401`. **Screenshot:** `test10_{HMMSS}_03_api_401_mobile.png`

- [ ] **Action 04 — restore signed-in state:** sign in as `alan`. Verify redirect to `/slides`. **Screenshot:** `test10_{HMMSS}_04_resigned_in_mobile.png`

**Report:** `IN QUEUE`
- Findings:
  - _(populate during execution)_
- Improvement Proposals:
  - `+ {priority} - {proposal name} - brief description`
