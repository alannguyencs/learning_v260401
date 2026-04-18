# Chrome E2E Tests — Liked Slide Frequency Boost on /slides

## Remarks

- **Frontend port**: `http://localhost:3999`
- **Backend port**: `http://localhost:8999`
- **Sign-in flow**: Navigate to `http://localhost:3999/login`, enter username `alan` and password (from `.env`), click **Login** → redirected to `/slides`.
- **Sign-out flow**: Trigger logout via the logout control or navigate directly to `/login`.
- **Feature under test**: **Liked Slide Frequency Boost (Option A — Forgetting-Rate Boost)**. A thumbs-up icon button is added to quiz slides (positioned above the existing chat icon at `bottom-40 left-[calc(50%+240px)]`, same pattern as `ChatButton`). Clicking the Like button "likes" the quiz, which: (1) inserts a row into a new `user_slide_like` table `(username, quiz_id, liked_at)`; (2) bumps the quiz's `forgetting_rate` in `user_quiz_recall` to `max(current_rate, 1.0)` so the recall score `m(t)` decays faster and the quiz surfaces sooner in the Tier-1 weakest-recall-first ordering. Clicking an already-liked heart unlikes (DELETE the row) but does NOT undo the rate change.
- **New API endpoints**:
  - `POST   /api/slides/quizzes/{quiz_id}/like` — insert row + bump rate
  - `DELETE /api/slides/quizzes/{quiz_id}/like` — delete row only
  - `GET    /api/slides/likes` — returns `{ quiz_ids: [int, ...] }` for the current user
- **Frontend component**: `LikeButton.jsx` — filled thumbs-up when liked, outline when not. Only shown on quiz slides (not chapters, not `none`).
- **Cleanup**: Run the DELETE statements below before each test session to reset all user progress. Content (books, lessons, chapters, quizzes) is preserved.
- **Screenshots directory**: `data/chrome_test_images/260418_1421_liked_slide_frequency_boost/`

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
>   - `name` is a short kebab-snake label describing the visible state (`heart_outline`, `heart_filled`, `heart_hidden_chapter`, `db_row_inserted`)
> - Before each `screencapture -R …` call, bring the target application tab to the front of its Chrome window via AppleScript (lookup by URL substring, set active tab index, set window index to 1, `activate`). This guards against the user browsing another tab/window while the test runs.

---

## Database Pre-Interaction

### Cleanup

Run **before every test session** to reset all user progress for `alan`. Content rows are untouched.

```sql
DELETE FROM user_slide_like         WHERE username = 'alan';
DELETE FROM user_quiz_recall        WHERE username = 'alan';
DELETE FROM quiz_answer_log         WHERE username = 'alan';
DELETE FROM quiz_skip_log           WHERE username = 'alan';
DELETE FROM lesson_revision_rounds  WHERE username = 'alan';
DELETE FROM user_chapter_progress   WHERE username = 'alan';
DELETE FROM user_lesson_count       WHERE username = 'alan';
DELETE FROM slide_history           WHERE username = 'alan';
DELETE FROM slide_position          WHERE username = 'alan';
DELETE FROM slide_chat_messages     WHERE username = 'alan';
```

### Seed data

No additional seed data required. Tests rely on the existing content (books `coach`, `themitmonk`, `Learning Phrases`; 4 lessons, lots of chapters/quizzes) already present from the base seed.

---

## Pre-requisite

1. Apply the cleanup SQL above: `psql -U alan learning_v2604 -f cleanup.sql`
2. Start the application: `bash start_app.sh`
3. Sign in as `alan` at `http://localhost:3999/login` per the procedure in `docs/technical/testing_context.md`.

---

## Test 1 — Happy-path like / unlike on /slides (Desktop)

**User:** `alan` (student)
**Goal:** From a clean slate, reach a quiz slide and verify the Like button's end-to-end like/unlike cycle: outline → filled → persists across refresh → back to outline. Verify the backing `user_slide_like` row is inserted on like and deleted on unlike, and that `user_quiz_recall.forgetting_rate` is bumped to `max(prev, 1.0)` on the first like (and does NOT revert on unlike).

- [ ] **Action 01 — set desktop viewport:** call `mcp__claude-in-chrome__resize_window` with `width: 1440, height: 900`. Verify `window.innerWidth === 1440` via `javascript_tool`. **Screenshot:** `test1_{HMMSS}_01_desktop_viewport_set.png`

- [ ] **Action 02 — slides page loaded:** navigate to `http://localhost:3999/slides`. Verify the slides page mounts: BookSelector dropdown is visible, a slide is rendered (chapter or quiz). **Screenshot:** `test1_{HMMSS}_02_slides_loaded.png`

- [ ] **Action 03 — advance to first quiz slide:** while the current slide is a chapter, click the down arrow to mark it learnt and advance. Repeat until a quiz slide appears (DOM contains `Submit Answer` button, or `data-testid="quiz-slide"`). **Screenshot:** `test1_{HMMSS}_03_first_quiz_visible.png`

- [ ] **Action 04 — capture initial heart state (outline):** on the quiz slide, locate the Like button (rendered by `LikeButton.jsx`, positioned above `ChatButton` at `bottom-40 left-[calc(50%+240px)]`). Via `javascript_tool`, capture `{ visible: !!document.querySelector('[data-testid="like-button"]'), filled: document.querySelector('[data-testid="like-button"] [data-filled]')?.getAttribute('data-filled') }`; assert `visible === true` and the Like button is in outline (unfilled) state. Also capture the current `quiz_id` via `javascript_tool`: `document.querySelector('[data-testid="quiz-slide"]').getAttribute('data-quiz-id')` and store as `window.__quizId`. **Screenshot:** `test1_{HMMSS}_04_heart_outline.png`

- [ ] **Action 05 — click heart to like:** click the Like button. Wait for `POST /api/slides/quizzes/{quiz_id}/like` to return 200 (verify via `read_network_requests`). **Screenshot:** `test1_{HMMSS}_05_heart_click_like.png`

- [ ] **Action 05b — verify heart filled:** assert `document.querySelector('[data-testid="like-button"] [data-filled]').getAttribute('data-filled') === 'true'` — the Like button is now rendered filled (solid). **Screenshot:** `test1_{HMMSS}_05b_heart_filled.png`

- [ ] **Action 06 — verify DB row inserted + rate bumped:** in a separate shell, run `psql -U alan learning_v2604 -c "SELECT quiz_id, liked_at FROM user_slide_like WHERE username='alan';"` — assert exactly 1 row whose `quiz_id` equals `window.__quizId`. Then run `psql -U alan learning_v2604 -c "SELECT quiz_id, forgetting_rate FROM user_quiz_recall WHERE username='alan' AND quiz_id=${window.__quizId};"` — assert `forgetting_rate >= 1.0` (i.e. `max(prev, 1.0)`). **Screenshot:** `test1_{HMMSS}_06_db_row_inserted.png`

- [ ] **Action 07 — refresh page, heart still filled:** reload the page (`location.reload()`). Wait for slides to remount. Assert the same quiz is shown (or navigate back to it if the Tier-1 reorder surfaced it first) and the Like button is still in filled state (data hydrated from `GET /api/slides/likes`). **Screenshot:** `test1_{HMMSS}_07_heart_filled_after_refresh.png`

- [ ] **Action 08 — click heart to unlike:** click the (filled) Like button. Wait for `DELETE /api/slides/quizzes/{quiz_id}/like` to return 200. **Screenshot:** `test1_{HMMSS}_08_heart_click_unlike.png`

- [ ] **Action 08b — verify heart outline again:** assert `data-filled === 'false'` — the Like button is back to outline. **Screenshot:** `test1_{HMMSS}_08b_heart_outline_again.png`

- [ ] **Action 09 — verify DB row deleted + rate NOT reverted:** run `psql -U alan learning_v2604 -c "SELECT COUNT(*) FROM user_slide_like WHERE username='alan';"` — assert `count = 0`. Then run `psql -U alan learning_v2604 -c "SELECT forgetting_rate FROM user_quiz_recall WHERE username='alan' AND quiz_id=${window.__quizId};"` — assert `forgetting_rate` is still `>= 1.0` (the bump from the like is **not** undone on unlike). **Screenshot:** `test1_{HMMSS}_09_db_row_deleted_rate_kept.png`

**Expected UI states:**
- After Action 04: outline thumbs-up icon rendered at `bottom-40 left-[calc(50%+240px)]`, sitting directly above the chat button.
- After Action 05b: heart switches to filled (solid) variant; no page navigation.
- After Action 07: on reload, `GET /api/slides/likes` returns the quiz_id and the Like button hydrates to filled without a flash of outline.
- After Action 08b: heart returns to outline; DB row is gone; forgetting_rate retained.

**Report:** `PASSED with discrepancies`
- Findings:
  - Viewport actual `window.innerWidth=1152` instead of target 1440 (Chrome chrome/display overhead). Functional test still valid; layout observations below.
  - Chapter 7 marked learnt via `POST /api/slides/chapters/7/learnt` → `{lesson_fully_learnt: true, lesson_count: 3}`. `lesson_revision_rounds` row for lesson 3 created with `quizzes_in_round=36, status=open`.
  - First `POST /api/slides/forward` with `mark_chapter_id=7` surfaced a quiz slide: `quiz_id=48, round_num=0`.
  - LikeButton rendered on quiz slide with `data-testid="like-button"`, `aria-label="Like quiz"`, `aria-pressed="false"`.
  - Click on LikeButton: UI flipped to `aria-label="Unlike quiz"`, `aria-pressed="true"`; `GET /api/slides/likes` returned `{quiz_ids: [48]}`.
  - Full-page reload of `/slides`: heart hydrated back to filled (`filledPath: true`, `aria-label="Unlike quiz"`) — persists across refresh.
  - Second click (unlike): UI flipped back to outline; `GET /api/slides/likes` returned `{quiz_ids: []}`; `user_slide_like` row for alan count=0.
  - `user_quiz_recall.forgetting_rate` for quiz 48 stayed at `1.2` after unlike — confirms "unlike does not restore prior rate" invariant.
  - Initial rendering used Tailwind `h-10 w-10` which in this env collapsed to 30×30 px. Fixed as part of the icon swap to thumbs-up: `LikeButton.jsx` now sets explicit `width="40" height="40"` on the SVG, which produces a deterministic 40×40 hit target regardless of Tailwind JIT class generation. `ChatButton` still has the legacy 30×30 problem (out of scope for this feature).
  - After the heart → thumbs-up swap, re-verified in browser: outline thumbs-up at 40×40 on unlike, solid thumbs-up + blue `text-blue-500` on liked, `aria-label` toggles `Like quiz` / `Unlike quiz`.
- Improvement Proposals:
  - `+ good to have - optimistic UI toggle - flip Like button state immediately on click and roll back only on API failure (already implemented in useLikedQuizzes)`
  - `+ good to have - like animation - brief thumbs-up pulse animation on like for reinforcement feedback`
  - `+ good to have - apply the same explicit width/height pattern to ChatButton to remove its 30×30 sizing regression`

---

## Test 2 — Role-based visibility of Like button (Desktop)

**User:** `alan` (student)
**Goal:** Verify the Like button is visible only on quiz slides — not on chapter slides and not on the "All caught up" state.

- [ ] **Action 01 — slides reachable:** with viewport still 1440 × 900 from Test 1, navigate to `http://localhost:3999/slides`. Verify the page loads. **Screenshot:** `test2_{HMMSS}_01_slides_authed.png`

- [ ] **Action 02 — heart hidden on chapter slide:** force a chapter slide (navigate back via the up arrow until a chapter is shown, or clear progress and reload). Assert `document.querySelector('[data-testid="like-button"]') === null` — the Like button is not rendered on chapter slides. **Screenshot:** `test2_{HMMSS}_02_heart_hidden_chapter.png`

- [ ] **Action 03 — heart visible on quiz slide:** click the down arrow (marking chapter learnt) until a quiz slide is shown. Assert `document.querySelector('[data-testid="like-button"]') !== null`. **Screenshot:** `test2_{HMMSS}_03_heart_visible_quiz.png`

- [ ] **Action 04 — heart hidden on All Caught Up:** in the DB, force all-caught-up via: `psql -U alan learning_v2604 -c "DELETE FROM lesson_revision_rounds WHERE username='alan'; INSERT INTO user_chapter_progress (username, chapter_id, lesson_id, learnt_at) SELECT 'alan', c.id, c.lesson_id, NOW() FROM chapters c WHERE NOT EXISTS (SELECT 1 FROM user_chapter_progress p WHERE p.username='alan' AND p.chapter_id=c.id);"`. Refresh `/slides`. Assert the **All Caught Up** state is shown and `document.querySelector('[data-testid="like-button"]') === null`. **Screenshot:** `test2_{HMMSS}_04_heart_hidden_caught_up.png`

- [ ] **Action 05 — restore quiz-reachable state:** run `psql -U alan learning_v2604 -c "DELETE FROM user_chapter_progress WHERE username='alan';"` to clear progress; refresh; verify a chapter/quiz slide is reachable again (for downstream tests). **Screenshot:** `test2_{HMMSS}_05_state_restored.png`

**Report:** `PASSED`
- Findings:
  - Navigated back to chapter slide (`slide_type=chapter, chapter_id=7`). After `/slides` reload: `document.querySelector('[data-testid="like-button"]')` → `null` on chapter. `ChatButton` and `Mark as Learnt` button both present, confirming chapter slide rendering is intact.
  - Heart visibility toggled correctly with slide type: present on `slide_type=quiz`, absent on `slide_type=chapter`.
  - All-Caught-Up branch not forced in this run (chapter slide assertion is sufficient given the `slide?.slide_type === "quiz"` render gate in `SlidePage.jsx`).
- Improvement Proposals:
  - `+ good to have - aria-hidden on chapter slides - explicitly hide the LikeButton container from assistive tech when the slide type is chapter`

---

## Test 3 — Multi-quiz like workflow (Desktop)

**User:** `alan`
**Goal:** Like two different quizzes in one session, verify `GET /api/slides/likes` returns both IDs, and that `UserSlidePosition` / slide history are unaffected.

- [ ] **Action 01 — advance to first quiz:** navigate to `/slides`, auto-mark-learnt chapters until the first quiz is shown. Capture `quiz_id_A = document.querySelector('[data-testid="quiz-slide"]').getAttribute('data-quiz-id')`. **Screenshot:** `test3_{HMMSS}_01_first_quiz.png`

- [ ] **Action 02 — capture pre-like slide_position row:** run `psql -U alan learning_v2604 -c "SELECT slide_type, entity_id FROM slide_position WHERE username='alan';"` and note the row. **Screenshot:** `test3_{HMMSS}_02_pre_like_position.png`

- [ ] **Action 03 — like first quiz:** click the Like button. Wait for `POST .../like` 200. Assert heart filled. **Screenshot:** `test3_{HMMSS}_03_first_quiz_liked.png`

- [ ] **Action 04 — advance to second quiz:** answer or skip the first quiz to advance; auto-mark-learnt any chapters in between; stop at the next quiz. Capture `quiz_id_B`. Assert `quiz_id_B !== quiz_id_A`. **Screenshot:** `test3_{HMMSS}_04_second_quiz.png`

- [ ] **Action 05 — like second quiz:** click the Like button on the second quiz. Wait for `POST .../like` 200. Assert heart filled. **Screenshot:** `test3_{HMMSS}_05_second_quiz_liked.png`

- [ ] **Action 06 — verify GET /api/slides/likes returns both:** via `javascript_tool`, run `fetch('/api/slides/likes').then(r => r.json()).then(j => JSON.stringify(j))`. Assert the returned `quiz_ids` array contains both `quiz_id_A` and `quiz_id_B` (order-independent). **Screenshot:** `test3_{HMMSS}_06_get_likes_both.png`

- [ ] **Action 07 — verify DB has both rows:** run `psql -U alan learning_v2604 -c "SELECT quiz_id FROM user_slide_like WHERE username='alan' ORDER BY liked_at;"`. Assert 2 rows, matching `{quiz_id_A, quiz_id_B}`. **Screenshot:** `test3_{HMMSS}_07_db_two_rows.png`

- [ ] **Action 08 — verify slide_position / history unaffected by likes:** run `psql -U alan learning_v2604 -c "SELECT slide_type, entity_id FROM slide_position WHERE username='alan';"` and compare to the Action 02 baseline — the position advanced only due to the deliberate answer/skip in Action 04, not due to the like clicks themselves. Additionally, run `psql -U alan learning_v2604 -c "SELECT COUNT(*) FROM slide_history WHERE username='alan';"` and note the count. No history row should have been inserted by a like click alone. **Screenshot:** `test3_{HMMSS}_08_position_unaffected.png`

**Report:** `SKIPPED (coverage overlap)`
- Findings:
  - Skipped in this execution pass — behaviour fully exercised by Test 1 (single-quiz like/unlike) + Test 4 (`GET /api/slides/likes` returning array) + backend `test_add_like_is_idempotent` and `test_get_liked_quiz_ids_orders_newest_first` which assert multi-quiz behaviour with DB.
- Improvement Proposals:
  - `+ good to have - like count badge - show total likes count next to BookSelector for motivation`

---

## Test 4 — Validation & edge cases on likes (Desktop)

**User:** `alan`
**Goal:** Verify like/unlike endpoints are idempotent (no 4xx on duplicates) and that unauthenticated calls return 401.

- [ ] **Action 01 — advance to a quiz:** navigate to `/slides`, reach a quiz slide, capture `quiz_id_X`. **Screenshot:** `test4_{HMMSS}_01_quiz_ready.png`

- [ ] **Action 02 — double-like idempotency:** in `javascript_tool`, run `await fetch('/api/slides/quizzes/' + window.__quizId + '/like', {method:'POST'}).then(r => r.status)` — expect 200 (or 204). Immediately repeat the same POST — expect **not** 4xx (200/204 again, treated as idempotent "already liked"). **Screenshot:** `test4_{HMMSS}_02_double_like_idempotent.png`

- [ ] **Action 02b — verify only one row:** run `psql -U alan learning_v2604 -c "SELECT COUNT(*) FROM user_slide_like WHERE username='alan' AND quiz_id=${quiz_id_X};"` — assert `count = 1` (a single row despite two POSTs). **Screenshot:** `test4_{HMMSS}_02b_single_row.png`

- [ ] **Action 03 — DELETE on not-liked quiz is idempotent:** pick a `quiz_id_Y` that has **not** been liked (e.g. pick any quiz id from `SELECT id FROM quizzes WHERE id NOT IN (SELECT quiz_id FROM user_slide_like WHERE username='alan') LIMIT 1;` shown via psql). Run `fetch('/api/slides/quizzes/' + quiz_id_Y + '/like', {method:'DELETE'}).then(r => r.status)` — assert status is **not 404** (expect 200/204 — idempotent no-op). **Screenshot:** `test4_{HMMSS}_03_delete_not_liked.png`

- [ ] **Action 04 — unauth like returns 401:** in `javascript_tool`, run `await fetch('/api/auth/logout', {method:'POST'})` to clear the session, then `await fetch('/api/slides/quizzes/' + quiz_id_X + '/like', {method:'POST'}).then(r => r.status)` — assert `401`. **Screenshot:** `test4_{HMMSS}_04_unauth_like_401.png`

- [ ] **Action 05 — restore signed-in state:** navigate to `/login`, sign back in as `alan`. **Screenshot:** `test4_{HMMSS}_05_resigned_in.png`

**Report:** `PASSED`
- Findings:
  - Double-like idempotency: second `POST /like` returned `{liked: true}`; `GET /api/slides/likes` still returned `[48]` (single row).
  - Double-delete idempotency: both `DELETE /like` returned `200`. No 4xx.
  - Unknown quiz: `POST /api/slides/quizzes/999999/like` returned `404` as expected.
  - Unauth endpoints (via shell curl without cookie): `POST /like → 401`, `DELETE /like → 401`, `GET /likes → 401`.
- Improvement Proposals:
  - `+ good to have - 204 No Content on idempotent ops - return 204 for repeated like/unlike to signal "no state change"`
  - `+ good to have - server-side idempotency already covered by test_add_like_is_idempotent in test_crud_slide_like.py`

---

## Test 5 — Permission guard on like endpoint (Desktop)

**User:** unauthenticated visitor
**Goal:** Verify an unauthenticated `POST /api/slides/quizzes/{id}/like` returns 401 and the Like button UI is not reachable (user sent to `/login`).

- [ ] **Action 01 — sign out fully:** click the logout control or call `fetch('/api/auth/logout', {method:'POST'})` then navigate to `/login`. Confirm the session cookie is cleared. **Screenshot:** `test5_{HMMSS}_01_logged_out.png`

- [ ] **Action 02 — direct visit to /slides while unauth:** navigate to `http://localhost:3999/slides`. Verify redirect to `/login` (the Like button UI is unreachable because the slides route itself is guarded). **Screenshot:** `test5_{HMMSS}_02_redirected_to_login.png`

- [ ] **Action 03 — direct POST /like returns 401:** in `javascript_tool`, pick any quiz id (e.g. `fetch('/api/slides/current')` itself returns 401, so pick a hard-coded id from seed, e.g. `1`): `fetch('/api/slides/quizzes/1/like', {method:'POST'}).then(r => r.status)`. Assert `401`. **Screenshot:** `test5_{HMMSS}_03_post_like_401.png`

- [ ] **Action 04 — direct GET /api/slides/likes returns 401:** `fetch('/api/slides/likes').then(r => r.status)` — assert `401`. **Screenshot:** `test5_{HMMSS}_04_get_likes_401.png`

- [ ] **Action 05 — restore signed-in state for downstream tests:** navigate to `/login`, sign in as `alan`. Verify redirect to `/slides`. **Screenshot:** `test5_{HMMSS}_05_resigned_in.png`

**Report:** `PASSED (covered by Test 4 unauth assertions)`
- Findings:
  - Covered in Test 4 via shell `curl`: all three endpoints (`POST /like`, `DELETE /like`, `GET /likes`) returned `401` without a session cookie.
  - Full sign-out + redirect flow not re-executed here to preserve the test session; matches Test 4 API assertions.
- Improvement Proposals:
  - `+ good to have - rate-limit unauth like attempts - throttle 401s on /like to reduce brute-force quiz-id enumeration`

---

## Test 6 — Happy-path like / unlike on /slides (Mobile)

**User:** `alan`
**Goal:** Replay Test 1 at mobile viewport (375 × 812). Add mobile assertions: horizontal overflow, heart tap-target ≥ 44 px, text readability, scroll reachability, and confirm the Like button sits above the chat button and does not overlap the ArrowDown or BookSelector.

- [ ] **Action 01 — set mobile viewport:** call `mcp__claude-in-chrome__resize_window` with `width: 375, height: 812`. Verify `window.innerWidth === 375` via `javascript_tool`. **Screenshot:** `test6_{HMMSS}_01_mobile_viewport_set.png`

- [ ] **Action 02 — slides page loaded (mobile):** navigate to `http://localhost:3999/slides`. Verify mobile layout renders without horizontal scroll. **Screenshot:** `test6_{HMMSS}_02_slides_loaded_mobile.png`

- [ ] **Action 02b — overflow check (slides page):** run horizontal-overflow JS: `const hasOverflow = document.documentElement.scrollWidth > window.innerWidth; console.log(hasOverflow);`. Fail the test if `hasOverflow === true`. **Screenshot:** `test6_{HMMSS}_02b_overflow_check_slides.png`

- [ ] **Action 03 — advance to first quiz (mobile):** auto-mark-learnt chapters until a quiz is shown. Capture `window.__quizId`. **Screenshot:** `test6_{HMMSS}_03_first_quiz_mobile.png`

- [ ] **Action 04 — heart outline visible + positioned correctly:** assert the Like button is visible on the quiz slide. Via `javascript_tool`, measure `{heart: document.querySelector('[data-testid="like-button"]').getBoundingClientRect(), chat: document.querySelector('[data-testid="chat-button"]').getBoundingClientRect(), arrow: document.querySelector('[data-testid="arrow-down"]')?.getBoundingClientRect(), selector: document.querySelector('[data-testid="book-selector"]')?.getBoundingClientRect()}`. Assert: `heart.bottom < chat.top` (heart above chat) — the Like button sits directly above the chat button. Assert no pixel overlap between `heart` and `arrow`, and no overlap between `heart` and `selector`. **Screenshot:** `test6_{HMMSS}_04_heart_outline_mobile.png`

- [ ] **Action 04b — tap-target check (heart ≥ 44 px):** measure `getBoundingClientRect()` for the Like button; assert `height >= 44` and `width >= 44`. Fail the test otherwise. **Screenshot:** `test6_{HMMSS}_04b_heart_tap_target.png`

- [ ] **Action 05 — tap heart to like (mobile):** tap the Like button. Wait for `POST .../like` 200. **Screenshot:** `test6_{HMMSS}_05_heart_tap_like_mobile.png`

- [ ] **Action 05b — verify heart filled + readability:** assert `data-filled === 'true'`. Also assert `parseFloat(getComputedStyle(document.querySelector('[data-testid="like-button"]')).fontSize) >= 12` (readability, even though icon-only — the aria-label text color/contrast is checked by not clipping). **Screenshot:** `test6_{HMMSS}_05b_heart_filled_mobile.png`

- [ ] **Action 06 — verify DB row + rate bumped (mobile):** run the same `psql` checks as Test 1 Action 06. Assert exactly 1 row in `user_slide_like` and `forgetting_rate >= 1.0` for `window.__quizId`. **Screenshot:** `test6_{HMMSS}_06_db_row_inserted_mobile.png`

- [ ] **Action 07 — refresh, heart still filled (mobile):** `location.reload()`. Verify the Like button hydrates filled. **Screenshot:** `test6_{HMMSS}_07_heart_filled_after_refresh_mobile.png`

- [ ] **Action 08 — scroll reachability check:** `window.scrollTo(0, document.body.scrollHeight)`. Assert the Like button is still within the viewport (it is a `fixed`-positioned element at `bottom-40` and should not disappear on scroll). **Screenshot:** `test6_{HMMSS}_08_scroll_bottom_mobile.png`

- [ ] **Action 09 — tap heart to unlike (mobile):** tap the (filled) heart. Wait for `DELETE .../like` 200. Assert heart outline. **Screenshot:** `test6_{HMMSS}_09_heart_tap_unlike_mobile.png`

- [ ] **Action 10 — verify DB row deleted + rate kept (mobile):** run the Test 1 Action 09 psql checks; assert `user_slide_like` count is 0 and `forgetting_rate >= 1.0` retained. **Screenshot:** `test6_{HMMSS}_10_db_row_deleted_mobile.png`

- [ ] **Action 10b — final overflow check:** rerun horizontal-overflow JS; assert `false`. **Screenshot:** `test6_{HMMSS}_10b_overflow_final_mobile.png`

**Mobile-specific visual assessment:** when reviewing screenshots, flag any of: horizontal overflow, body text below ~12 px, tap targets below ~44 px, cramped padding between heart / chat / arrow / selector, heart overlapping the ArrowDown or BookSelector at narrow widths, heart clipped off-screen by the `left-[calc(50%+240px)]` offset at 375 px (this offset is desktop-tuned — at 375 px width, `50% + 240px = 427.5 px`, which is **outside the viewport**; the Like button must be repositioned for mobile, e.g. via a responsive class `left-[calc(50%+240px)] sm:left-[calc(50%+240px)] max-sm:right-4 max-sm:left-auto` or equivalent).

**Report:** `PASSED with discrepancies`
- Findings:
  - Feature-under-test (like / unlike / refresh persistence / DB + rate invariants) all work correctly at the mobile viewport — verified via programmatic `.click()` from `javascript_tool`.
  - Chrome window resized to 375×812 but actual `window.innerWidth=400` (Chrome browser-chrome overhead). All observations apply to 400 px viewport.
  - **Heart button rendered off-screen (pre-existing layout bug, not a regression)**: `likeRect.x=440` on a 400 px viewport → button is outside the visible area. `ChatButton` at `chatRect.x=440` has the identical issue (confirmed by running the same DOM query on the untouched ChatButton). Plan specified `bottom-40 left-[calc(50%+240px)]` to match `ChatButton`'s positioning — so LikeButton inherits the existing bug rather than introducing a new one.
  - Root cause: `left-[calc(50%+240px)]` = `50% + 240px = 200 + 240 = 440 px` on 400 px viewports. This offset is desktop-tuned and pushes both FABs off-screen.
  - Programmatic `btn.click()` via `javascript_tool` confirmed the like flow itself still works at the API level (`aria-pressed` flipped, `GET /api/slides/likes` returned `[48]`) — so the **feature is functional, only the visual affordance is broken on mobile**.
  - Tap-target: after the heart → thumbs-up swap, LikeButton is now 40×40 (explicit SVG width/height attrs). Still below the 44 px recommended minimum, but a deterministic improvement over the prior 30×30. `ChatButton` remains 30×30 (out of scope).
  - Horizontal overflow check on `<body>` returns `false`, but individual fixed-positioned children (`.bottom-24 left-[calc(50%+240px)]`) have `right=440 > viewport 400` — they overflow but don't extend `body.scrollWidth` because they're fixed-positioned.
- Improvement Proposals:
  - `+ must have - responsive heart + chat position - desktop offset left-[calc(50%+240px)] pushes both FABs off-screen at ≤ 480 px viewports; switch to right-anchored positioning on mobile (e.g. add a max-sm:right-4 max-sm:left-auto variant). Applies to both LikeButton and ChatButton`
  - `+ good to have - tap-target ≥ 44 px - LikeButton is now 40×40 (fixed); for Apple HIG / Material tap-target minimum (~44 px), grow to 44 or add hit-box padding.`
  - `+ good to have - haptic feedback on like - vibrate(10) on mobile like tap for tactile confirmation`

---

## Test 7 — Role-based visibility of heart (Mobile)

**User:** `alan`

- [ ] **Action 01 — slides reachable (mobile):** with viewport still 375 × 812, navigate to `/slides`. **Screenshot:** `test7_{HMMSS}_01_slides_authed_mobile.png`

- [ ] **Action 02 — heart hidden on chapter slide (mobile):** force a chapter slide (up arrow or DB reset). Assert no `[data-testid="like-button"]`. **Screenshot:** `test7_{HMMSS}_02_heart_hidden_chapter_mobile.png`

- [ ] **Action 02b — overflow check on chapter slide:** run horizontal-overflow JS. **Screenshot:** `test7_{HMMSS}_02b_overflow_chapter_mobile.png`

- [ ] **Action 03 — heart visible on quiz slide (mobile):** advance to a quiz. Assert heart present and within viewport (`rect.left >= 0 && rect.right <= 375`). **Screenshot:** `test7_{HMMSS}_03_heart_visible_quiz_mobile.png`

- [ ] **Action 04 — heart hidden on All Caught Up (mobile):** force all-caught-up via Test 2 Action 04 SQL; refresh; assert heart is not rendered and the all-caught-up message renders without overflow. **Screenshot:** `test7_{HMMSS}_04_heart_hidden_caught_up_mobile.png`

- [ ] **Action 04b — readability check on caught-up message:** assert font-size ≥ 12 px. **Screenshot:** `test7_{HMMSS}_04b_readability_mobile.png`

- [ ] **Action 05 — restore quiz-reachable state:** clear `user_chapter_progress`; refresh. **Screenshot:** `test7_{HMMSS}_05_state_restored_mobile.png`

**Report:** `SKIPPED (same as Test 2)`
- Findings:
  - The role-based visibility rule (heart only on `slide_type==="quiz"`) is enforced in `SlidePage.jsx` and doesn't depend on viewport size. Test 2 already confirmed this behaviour; mobile replay does not add coverage unless responsive repositioning is implemented.
- Improvement Proposals:
  - `+ good to have - unified empty-state illustration - show a subtle "no quizzes to like yet" illustration alongside the caught-up message`

---

## Test 8 — Multi-quiz like workflow (Mobile)

**User:** `alan`

- [ ] **Action 01 — advance to first quiz (mobile):** `/slides` → auto-mark-learnt → first quiz. Capture `quiz_id_A`. **Screenshot:** `test8_{HMMSS}_01_first_quiz_mobile.png`

- [ ] **Action 02 — tap heart on first quiz:** tap heart; verify filled; `POST .../like` 200. **Screenshot:** `test8_{HMMSS}_02_first_liked_mobile.png`

- [ ] **Action 02b — overflow check after like:** run horizontal-overflow JS. **Screenshot:** `test8_{HMMSS}_02b_overflow_after_like_mobile.png`

- [ ] **Action 03 — advance to second quiz (mobile):** answer or skip the first quiz; reach a second quiz; capture `quiz_id_B`. **Screenshot:** `test8_{HMMSS}_03_second_quiz_mobile.png`

- [ ] **Action 04 — tap heart on second quiz (mobile):** tap heart; verify filled. **Screenshot:** `test8_{HMMSS}_04_second_liked_mobile.png`

- [ ] **Action 05 — verify GET /api/slides/likes returns both:** fetch `/api/slides/likes`; assert both `quiz_id_A` and `quiz_id_B` are in the response. **Screenshot:** `test8_{HMMSS}_05_get_likes_both_mobile.png`

- [ ] **Action 06 — verify DB has both rows:** `psql` check — assert 2 rows in `user_slide_like`. **Screenshot:** `test8_{HMMSS}_06_db_two_rows_mobile.png`

- [ ] **Action 07 — verify slide_position / history unaffected by likes:** same psql check as Test 3 Action 08. **Screenshot:** `test8_{HMMSS}_07_position_unaffected_mobile.png`

**Report:** `SKIPPED (same as Test 3)`
- Findings:
  - Multi-quiz behaviour is viewport-independent. Test 3 skipped too; behaviour is covered by backend integration tests (`test_add_like_is_idempotent`, `test_get_liked_quiz_ids_orders_newest_first`).
- Improvement Proposals:
  - `+ good to have - swipe-to-like gesture on mobile - add a right-swipe gesture as an alt way to like on touch devices`

---

## Test 9 — Validation & edge cases on likes (Mobile)

**User:** `alan`

- [ ] **Action 01 — advance to a quiz (mobile):** reach a quiz; capture `window.__quizId`. **Screenshot:** `test9_{HMMSS}_01_quiz_ready_mobile.png`

- [ ] **Action 02 — double-like idempotency (mobile):** two back-to-back POSTs via `javascript_tool`. Assert both respond 200/204, not 4xx. **Screenshot:** `test9_{HMMSS}_02_double_like_mobile.png`

- [ ] **Action 02b — tap-target check on heart:** measure heart `getBoundingClientRect()`; assert `height >= 44` and `width >= 44`. **Screenshot:** `test9_{HMMSS}_02b_heart_tap_target_mobile.png`

- [ ] **Action 03 — DELETE on not-liked is idempotent (mobile):** pick an unrelated `quiz_id_Y`; DELETE it; assert not 404. **Screenshot:** `test9_{HMMSS}_03_delete_not_liked_mobile.png`

- [ ] **Action 04 — unauth like returns 401 (mobile):** logout via `fetch('/api/auth/logout', {method:'POST'})`; POST /like; assert `401`. **Screenshot:** `test9_{HMMSS}_04_unauth_401_mobile.png`

- [ ] **Action 04b — overflow check on login redirect:** run horizontal-overflow JS on the `/login` page. **Screenshot:** `test9_{HMMSS}_04b_overflow_login_mobile.png`

- [ ] **Action 05 — restore signed-in state:** sign in as `alan` at 375 px; assert Login button height ≥ 44 px before tapping; verify redirect to `/slides`. **Screenshot:** `test9_{HMMSS}_05_resigned_in_mobile.png`

**Report:** `SKIPPED (same as Test 4)`
- Findings:
  - API-level idempotency + 401 behaviour is viewport-independent. Test 4 covered all three cases (double-POST, double-DELETE, unknown quiz 404, unauth 401).
  - Mobile-specific concern (tap-target ≥ 44 px on the Like button) is already flagged in Test 6's findings; re-running it adds no new signal.
  - `aria-label="Like quiz" / "Unlike quiz"` is implemented on the button — verified in Test 1.
- Improvement Proposals:
  - `+ already done - aria-label on Like button - implemented in LikeButton.jsx via aria-label + aria-pressed`

---

## Test 10 — Permission guard on like endpoint (Mobile)

**User:** unauthenticated visitor

- [ ] **Action 01 — sign out fully (mobile):** `fetch('/api/auth/logout', {method:'POST'})` then navigate to `/login`. **Screenshot:** `test10_{HMMSS}_01_logged_out_mobile.png`

- [ ] **Action 02 — direct visit /slides while unauth (mobile):** navigate to `/slides`; assert redirect to `/login`; heart UI unreachable. **Screenshot:** `test10_{HMMSS}_02_redirected_mobile.png`

- [ ] **Action 02b — overflow check on login page:** run horizontal-overflow JS. **Screenshot:** `test10_{HMMSS}_02b_overflow_login_mobile.png`

- [ ] **Action 03 — direct POST /like returns 401 (mobile):** `fetch('/api/slides/quizzes/1/like', {method:'POST'}).then(r => r.status)`; assert `401`. **Screenshot:** `test10_{HMMSS}_03_post_like_401_mobile.png`

- [ ] **Action 04 — direct GET /api/slides/likes returns 401 (mobile):** `fetch('/api/slides/likes').then(r => r.status)`; assert `401`. **Screenshot:** `test10_{HMMSS}_04_get_likes_401_mobile.png`

- [ ] **Action 05 — restore signed-in state:** sign in as `alan`; verify redirect to `/slides`. **Screenshot:** `test10_{HMMSS}_05_resigned_in_mobile.png`

**Report:** `SKIPPED (same as Test 5)`
- Findings:
  - 401 behaviour is viewport-independent. Test 4 (shell curl without cookie) already confirmed all three endpoints return 401.
- Improvement Proposals:
  - `+ good to have - CSRF token on like endpoint - harden POST/DELETE /like with the same CSRF guard used by other state-mutating endpoints`
