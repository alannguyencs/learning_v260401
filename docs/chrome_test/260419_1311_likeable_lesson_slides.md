# Chrome E2E Tests — Likeable Lesson Slides (Chapter Like + Interleaved Favorites)

## Remarks

- **Frontend port**: `http://localhost:3999`
- **Backend port**: `http://localhost:8999`
- **Sign-in flow**: Navigate to `http://localhost:3999/login`, enter username and password, click **Login** → redirected to `/slides`.
- **Sign-out flow**: Trigger logout via the logout button or navigate to `/login`.
- **Test user**: `alan` (student). Password lives in the local Postgres `users` table (see `docs/technical/testing_context.md`). There is only one application user role in this project, so Tests 2, 5, 7, and 10 exercise the feature's **visibility / guard semantics** in place of the generic role-based / permission-guard categories.
- **Feature under test**: chapter (lesson) slides are now likeable. Liking uses the same `LikeButton` FAB rendered on both chapter and quiz slides. The `user_slide_like` table is polymorphic (nullable `quiz_id` + new nullable `chapter_id` with a CHECK that exactly one is set). The `/favorite` page renders **one interleaved carousel** ordered newest-liked first; each card is a quiz card or a chapter card depending on the item's type. Chapter likes are **bookmark-only** — they never affect `SlideSelector` or the revision queue.
- **Cleanup**: Run the DELETE statements below before each test session to reset the user's like state.
- **Screenshots directory**: `data/chrome_test_images/260419_1311_likeable_lesson_slides/`

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
>   - `name` is a short kebab-snake label describing the visible state (`heart_outline`, `heart_filled`, `chapter_card`, `quiz_card`, `favorite_empty`)
> - Before each `screencapture -R …` call, bring the target application tab to the front of its Chrome window via AppleScript (lookup by URL substring, set active tab index, set window index to 1, `activate`). This guards against the user browsing another tab/window while the test runs.

---

## Database Pre-Interaction

### Cleanup

Run this **before every test session** to reset `alan`'s like state. Other user progress is left intact so chapters remain available to study.

```sql
DELETE FROM user_slide_like        WHERE username = 'alan';
DELETE FROM slide_history          WHERE username = 'alan';
DELETE FROM slide_position         WHERE username = 'alan';
DELETE FROM slide_chat_messages    WHERE username = 'alan';
```

> If you want a fully clean slate (useful for Tests 2 / 7 that rely on untouched chapters), also run the wider wipe used in other specs:
>
> ```sql
> DELETE FROM quiz_answer_log        WHERE username = 'alan';
> DELETE FROM quiz_skip_log          WHERE username = 'alan';
> DELETE FROM user_quiz_recall       WHERE username = 'alan';
> DELETE FROM lesson_revision_rounds WHERE username = 'alan';
> DELETE FROM user_chapter_progress  WHERE username = 'alan';
> DELETE FROM user_lesson_count      WHERE username = 'alan';
> ```

### Seed Data — per-test preconditions

The 4 existing lessons in the database are the content under test (see `docs/chrome_test/260418_1653_group_b_above_tier_2.md` for the full table). For this feature the useful anchors are:

| Book             | Lesson ID | Lesson                       | Chapter IDs |
|------------------|-----------|------------------------------|-------------|
| Learning Phrases | 5         | English Cartoons: My Room    | 16, 17      |
| themitmonk       | 2         | 20 Quantum Cheat Codes       | 2, 3, 4, 5, 6 |
| coach            | 3         | Time-Framed Learning         | 7, 8, 9, 10, 11 |

**Seed L — pre-like one chapter + one quiz (used by Tests 3, 8 to verify interleaving order):**

```sql
-- Pre-like chapter 16 (Learning Phrases, first chapter of lesson 5) 5 min ago
INSERT INTO user_slide_like (username, chapter_id, liked_at)
VALUES ('alan', 16, NOW() - INTERVAL '5 minutes')
ON CONFLICT DO NOTHING;

-- Pre-like one quiz from lesson 5 (most recently liked → rendered first)
INSERT INTO user_slide_like (username, quiz_id, liked_at)
SELECT 'alan', cq.id, NOW()
FROM chapter_quizzes cq
JOIN chapters c ON c.id = cq.chapter_id
WHERE c.lesson_id = 5
ORDER BY cq.id
LIMIT 1
ON CONFLICT DO NOTHING;
```

### Seed Cleanup (between tests within the same session)

Re-run the top-level **Cleanup** block. Seed L is idempotent except for the `INTERVAL '5 minutes'` timestamp — re-running Seed L resets it.

---

## Pre-requisite

1. Run the top-level Cleanup SQL.
2. Start the app: `bash start_app.sh`.
3. Sign in as `alan` at `http://localhost:3999/login`.
4. For each test, run the Seed SQL listed in the test header before performing the Chrome actions.

---

## Test 1 — Desktop — Happy-path: like a chapter on `/slides`, see it in `/favorite`

**User:** `alan`
**Viewport:** 1440 × 900 (set in Action 01; inherited by Tests 2–5)
**Seed:** none (start from clean user state).
**Goal:** Verify the new heart FAB appears on a chapter slide, persists across refresh, and the liked chapter shows up on `/favorite` as a chapter card.

- [ ] **Action 01 — set desktop viewport:** call `mcp__claude-in-chrome__resize_window` with `width: 1440, height: 900`. Verify `window.innerWidth === 1440` via `javascript_tool`. **Screenshot:** `test1_{HMMSS}_01_desktop_viewport_set.png`
- [ ] **Action 02 — slides page loaded:** navigate to `http://localhost:3999/slides`. Verify a chapter slide renders (chapter title, markdown body, **Mark as Learnt**). **Screenshot:** `test1_{HMMSS}_02_chapter_slide_loaded.png`
- [ ] **Action 03 — heart outline visible on chapter slide:** scroll/focus the Like FAB at `bottom-40 left-[calc(50%+240px)]`. Verify `data-testid="like-button"` is present and the SVG is an outline thumbs-up (`text-gray-400`). **Screenshot:** `test1_{HMMSS}_03_chapter_heart_outline.png`
- [ ] **Action 04 — click heart (chapter liked):** click the heart. Verify it flips to filled (`text-blue-500`) and `POST /api/slides/chapters/{id}/like` fires (check `read_network_requests`; expect 200 `{ "liked": true }`). **Screenshot:** `test1_{HMMSS}_04_chapter_heart_filled.png`
- [ ] **Action 05 — refresh persists liked state:** reload the page. Verify the heart remains filled and `GET /api/slides/likes` returns `chapter_ids` containing the current chapter id. **Screenshot:** `test1_{HMMSS}_05_chapter_heart_filled_after_refresh.png`
- [ ] **Action 06 — navigate to /favorite:** click the Favorite tab in the BottomNavBar (or navigate to `http://localhost:3999/favorite`). **Screenshot:** `test1_{HMMSS}_06_favorite_page_loaded.png`
- [ ] **Action 07 — chapter card rendered:** verify the first (and only) card is a **chapter card** — shows book/lesson breadcrumb, chapter title, and markdown content (not MC options / expected-answer block). Assert the card is distinct from `FavoriteQuizCard`. **Screenshot:** `test1_{HMMSS}_07_chapter_card.png`
- [ ] **Action 08 — unlike from slide:** navigate back to `/slides`, find the same chapter slide, click the filled heart. Verify it reverts to outline and `DELETE /api/slides/chapters/{id}/like` fires (200 `{ "liked": false }`). **Screenshot:** `test1_{HMMSS}_08_chapter_heart_unliked.png`
- [ ] **Action 09 — favorite empty after unlike:** return to `/favorite`. Verify the empty-state message appears (`No favorites yet.`). **Screenshot:** `test1_{HMMSS}_09_favorite_empty.png`

**Expected:** heart toggles on a chapter slide exactly like it does on a quiz slide; persists across refresh; liked chapter appears as a chapter card in `/favorite`; unliking removes it.

### Report

IN QUEUE

**Findings:** _(placeholder — to be filled after execution)_

**Improvement Proposals:**
+ _(placeholder — to be filled after execution)_

---

## Test 2 — Desktop — Heart visibility across slide types

**User:** `alan`
**Viewport:** 1440 × 900 (inherited from Test 1)
**Seed:** none (Cleanup only).
**Goal:** Verify the heart is present on both chapter slides and quiz slides, and hidden on the All-Caught-Up state. Chapter likes must not affect slide selection.

- [ ] **Action 01 — /slides loaded (chapter):** navigate to `http://localhost:3999/slides`. Verify a chapter slide renders and the Like FAB is visible. **Screenshot:** `test2_{HMMSS}_01_chapter_with_heart.png`
- [ ] **Action 02 — like the chapter:** click the heart. Verify filled state. **Screenshot:** `test2_{HMMSS}_02_chapter_liked.png`
- [ ] **Action 03 — advance to quiz slide (same session):** mark chapter 16 learnt, then chapter 17. Wait for lesson 5 R0 to activate and a quiz to appear. Verify the Like FAB is still visible on the quiz slide. **Screenshot:** `test2_{HMMSS}_03_quiz_with_heart.png`
- [ ] **Action 04 — advance ordering sanity:** answer several lesson-5 quizzes through the Slide UI. Verify the liked chapter (id 16) **never reappears** as a slide — chapter likes are bookmark-only and must not resurface in Tier 2 or any tier. **Screenshot:** `test2_{HMMSS}_04_ordering_no_resurface.png`
- [ ] **Action 05 — drain all content, reach All Caught Up:** navigate `All Books` in BookSelector and keep advancing until `AllCaughtUp` renders (or seed all chapters learnt if this takes too long). Verify **no Like FAB** is visible on the All-Caught-Up state. **Screenshot:** `test2_{HMMSS}_05_all_caught_up_no_heart.png`
- [ ] **Action 06 — liked chapter still in /favorite:** navigate to `/favorite`. Verify the chapter liked in Action 02 is still present as a chapter card even after the Slide session is "caught up." **Screenshot:** `test2_{HMMSS}_06_favorite_still_has_chapter.png`

**Expected:** the heart renders on any slide where `slide_type !== "none"`. Liked chapters never resurface on `/slides`, but persist in `/favorite`.

### Report

IN QUEUE

**Findings:** _(placeholder — to be filled after execution)_

**Improvement Proposals:**
+ _(placeholder — to be filled after execution)_

---

## Test 3 — Desktop — Interleaved carousel: chapter + quiz in one list, newest-first

**User:** `alan`
**Viewport:** 1440 × 900
**Seed:** run **Cleanup** then **Seed L** (chapter 16 liked 5 min ago; one lesson-5 quiz liked now).
**Goal:** Verify the Favorite tab shows a single interleaved carousel ordered by `liked_at DESC`; card component branches on item type (quiz vs chapter); up/down arrows paginate across both types.

- [ ] **Action 01 — /favorite loaded:** navigate to `http://localhost:3999/favorite`. Verify `1 / 2` counter and "Newest liked first" label at the top. **Screenshot:** `test3_{HMMSS}_01_favorite_loaded.png`
- [ ] **Action 02 — first card is the quiz (newest like):** verify the current card is the lesson-5 quiz card (MC options or expected-answer block; book/lesson breadcrumb). **Screenshot:** `test3_{HMMSS}_02_quiz_card_first.png`
- [ ] **Action 03 — down arrow paginates to chapter card:** click the down arrow. Verify the card swaps to a chapter card (chapter title, markdown body, no MC options). Counter reads `2 / 2`. **Screenshot:** `test3_{HMMSS}_03_chapter_card_second.png`
- [ ] **Action 04 — up arrow returns to quiz card:** click the up arrow. Verify the quiz card is shown again and counter reads `1 / 2`. **Screenshot:** `test3_{HMMSS}_04_up_arrow_returns_quiz.png`
- [ ] **Action 05 — like a new chapter from /slides:** navigate to `/slides`, open another chapter (e.g. themitmonk chapter 2), click the heart. Return to `/favorite`. Verify the new chapter card is now at position 1 / 3 (newest). **Screenshot:** `test3_{HMMSS}_05_new_chapter_on_top.png`
- [ ] **Action 06 — BookSelector filter excludes non-matching items:** open the BookSelector, pick **Learning Phrases**. Verify only lesson-5 items remain (the themitmonk chapter card disappears from the carousel and counter updates to `2 / 2`). **Screenshot:** `test3_{HMMSS}_06_book_filter_applied.png`
- [ ] **Action 07 — switch back to All Books:** pick **All Books**. Verify all 3 items return. **Screenshot:** `test3_{HMMSS}_07_all_books_restored.png`

**Expected:** `/favorite` is a single list interleaving quizzes and chapters by `liked_at DESC`; the card component is chosen per-item; BookSelector filters both types by `book_id`.

### Report

IN QUEUE

**Findings:** _(placeholder — to be filled after execution)_

**Improvement Proposals:**
+ _(placeholder — to be filled after execution)_

---

## Test 4 — Desktop — Validation & edge cases: idempotent like, 404, polymorphic CHECK

**User:** `alan`
**Viewport:** 1440 × 900
**Seed:** Cleanup only.
**Goal:** Exercise API-level edge cases via `javascript_tool` + network inspection: double-like, double-unlike, 404 on unknown chapter, and the polymorphic CHECK constraint rejecting rows with neither FK set.

- [ ] **Action 01 — /slides loaded:** navigate. Land on a chapter slide. **Screenshot:** `test4_{HMMSS}_01_slides_loaded.png`
- [ ] **Action 02 — double-like idempotency:** click the heart twice in quick succession. Verify only one row is inserted (check `GET /api/slides/likes` returns a single `chapter_id` match). **Screenshot:** `test4_{HMMSS}_02_double_like_single_row.png`
- [ ] **Action 03 — double-unlike idempotency:** click the filled heart twice. Verify final state is outline and no server error appears in `read_console_messages`. **Screenshot:** `test4_{HMMSS}_03_double_unlike_clean.png`
- [ ] **Action 04 — 404 on unknown chapter:** via `javascript_tool`, run `fetch('/api/slides/chapters/999999/like', { method: 'POST', credentials: 'include' }).then(r => r.status)`. Verify the status is `404`. **Screenshot:** `test4_{HMMSS}_04_chapter_404.png`
- [ ] **Action 05 — 404 on unknown quiz (regression):** run the same probe against `/api/slides/quizzes/999999/like`. Verify `404` — existing quiz-like behavior unchanged. **Screenshot:** `test4_{HMMSS}_05_quiz_404.png`
- [ ] **Action 06 — /favorite empty state:** navigate to `/favorite`. Verify empty-state copy renders and the link `Like a quiz or chapter from the Slides page…` is present (copy updated for this feature). **Screenshot:** `test4_{HMMSS}_06_favorite_empty_copy.png`

**Expected:** POST/DELETE on both endpoints are idempotent and return 404 for unknown IDs; the CHECK constraint prevents orphan rows at the DB layer; `/favorite` empty copy mentions both quizzes and chapters.

### Report

IN QUEUE

**Findings:** _(placeholder — to be filled after execution)_

**Improvement Proposals:**
+ _(placeholder — to be filled after execution)_

---

## Test 5 — Desktop — Permission guard: unauthenticated access blocked

**User:** (none — signed out)
**Viewport:** 1440 × 900
**Seed:** none.
**Goal:** Confirm chapter-like endpoints and `/favorite` require an authenticated session.

- [ ] **Action 01 — sign out:** click logout or navigate to `/login`. Verify login form renders. **Screenshot:** `test5_{HMMSS}_01_logged_out.png`
- [ ] **Action 02 — /favorite redirects:** navigate to `http://localhost:3999/favorite`. Verify redirect to `/login` (or explicit unauthenticated state). **Screenshot:** `test5_{HMMSS}_02_favorite_redirect.png`
- [ ] **Action 03 — POST /chapters/{id}/like returns 401:** via `javascript_tool`, run `fetch('/api/slides/chapters/16/like', { method: 'POST', credentials: 'include' }).then(r => r.status)`. Verify `401`. **Screenshot:** `test5_{HMMSS}_03_chapter_like_401.png`
- [ ] **Action 04 — GET /liked-items returns 401:** run `fetch('/api/slides/liked-items', { credentials: 'include' }).then(r => r.status)`. Verify `401`. **Screenshot:** `test5_{HMMSS}_04_liked_items_401.png`
- [ ] **Action 05 — sign back in:** submit `alan` credentials. Verify redirect to `/slides`. **Screenshot:** `test5_{HMMSS}_05_signed_in.png`

**Expected:** all new endpoints are gated by the session dependency; `/favorite` route requires auth just like `/slides`.

### Report

IN QUEUE

**Findings:** _(placeholder — to be filled after execution)_

**Improvement Proposals:**
+ _(placeholder — to be filled after execution)_

---

## Test 6 — Mobile — Happy-path replay at 375 × 812

**User:** `alan`
**Viewport:** 375 × 812 (set in Action 01; inherited by Tests 7–10)
**Seed:** Cleanup only.
**Goal:** Replay Test 1 at mobile viewport. Verify the heart FAB is tappable and the `/favorite` chapter card has no horizontal overflow.

- [ ] **Action 01 — set mobile viewport:** call `mcp__claude-in-chrome__resize_window` with `width: 375, height: 812`. Verify `window.innerWidth === 375` via `javascript_tool`. **Screenshot:** `test6_{HMMSS}_01_mobile_viewport_set.png`
- [ ] **Action 02 — /slides loaded (mobile chapter):** navigate. Run the horizontal-overflow JS check; fail if `hasOverflow === true`. Verify the chapter slide renders. **Screenshot:** `test6_{HMMSS}_02_mobile_chapter_slide.png`
- [ ] **Action 03 — heart FAB tap-target:** assert the Like FAB `getBoundingClientRect().height >= 44` and that it is not clipped at the right edge of the viewport (`rect.right <= 375`). **Screenshot:** `test6_{HMMSS}_03_mobile_heart_fab.png`
- [ ] **Action 04 — tap heart (chapter liked):** tap it. Verify filled state and a 200 response from `POST /api/slides/chapters/{id}/like`. **Screenshot:** `test6_{HMMSS}_04_mobile_chapter_liked.png`
- [ ] **Action 05 — refresh persists:** reload. Verify filled state persists. **Screenshot:** `test6_{HMMSS}_05_mobile_refresh_filled.png`
- [ ] **Action 06 — navigate to /favorite via BottomNavBar:** tap the Favorite icon. Run overflow check. **Screenshot:** `test6_{HMMSS}_06_mobile_favorite_loaded.png`
- [ ] **Action 07 — chapter card readable:** verify the chapter markdown body is fully visible (no horizontal scroll; `font-size >= 12px`; no text truncated). Scroll to bottom to confirm breadcrumb + content reachable. **Screenshot:** `test6_{HMMSS}_07_mobile_chapter_card.png`
- [ ] **Action 08 — unlike from mobile slide:** return to `/slides`, tap the filled heart. Verify outline state. **Screenshot:** `test6_{HMMSS}_08_mobile_chapter_unliked.png`
- [ ] **Action 09 — empty /favorite copy:** tap Favorite again. Verify empty-state copy is not truncated at 375 px. **Screenshot:** `test6_{HMMSS}_09_mobile_favorite_empty.png`

**Mobile findings checklist:** no overflow on chapter card or /slides; heart FAB `height >= 44`; markdown body wraps cleanly; empty-state fully visible.

### Report

IN QUEUE

**Findings:** _(placeholder — to be filled after execution)_

**Improvement Proposals:**
+ _(placeholder — to be filled after execution)_

---

## Test 7 — Mobile — Heart visibility across slide types on mobile

**User:** `alan`
**Viewport:** 375 × 812
**Seed:** Cleanup only.
**Goal:** Replay Test 2 on mobile. Confirm the FAB position does not collide with the down-arrow / chat FAB stack at 375 px.

- [ ] **Action 01 — /slides loaded:** navigate. Run overflow check. **Screenshot:** `test7_{HMMSS}_01_mobile_slides_loaded.png`
- [ ] **Action 02 — FAB stack inspection (chapter):** verify LikeButton at `bottom-40`, ChatButton at `bottom-24`, ArrowDown at `bottom-[76px]` are stacked without overlap. Assert each button's rect does not intersect the others. **Screenshot:** `test7_{HMMSS}_02_mobile_fab_stack_chapter.png`
- [ ] **Action 03 — like chapter + advance:** tap heart → filled. Mark chapter learnt → next slide. Repeat until a quiz slide renders. **Screenshot:** `test7_{HMMSS}_03_mobile_advance_to_quiz.png`
- [ ] **Action 04 — FAB stack inspection (quiz):** repeat the no-overlap assertion on the quiz slide. Verify heart FAB is still at `bottom-40`. **Screenshot:** `test7_{HMMSS}_04_mobile_fab_stack_quiz.png`
- [ ] **Action 05 — All Caught Up hides heart:** advance until `AllCaughtUp` renders. Assert `[data-testid="like-button"]` does not exist in the DOM. **Screenshot:** `test7_{HMMSS}_05_mobile_all_caught_up_no_heart.png`

**Mobile findings checklist:** no FAB overlap at 375 px; heart/chat/down-arrow vertical spacing ≥ 8 px; All-Caught-Up screen has no stray FABs.

### Report

IN QUEUE

**Findings:** _(placeholder — to be filled after execution)_

**Improvement Proposals:**
+ _(placeholder — to be filled after execution)_

---

## Test 8 — Mobile — Interleaved carousel on mobile

**User:** `alan`
**Viewport:** 375 × 812
**Seed:** run **Cleanup** then **Seed L**.
**Goal:** Replay Test 3 on mobile. Verify the interleaved carousel paginates on a small screen and each card type renders without overflow.

- [ ] **Action 01 — /favorite loaded:** navigate. Run overflow check. Verify `1 / 2` counter. **Screenshot:** `test8_{HMMSS}_01_mobile_favorite_loaded.png`
- [ ] **Action 02 — mobile quiz card:** verify the quiz card fits within 375 px — MC options wrap cleanly, expected-answer block has `whitespace-pre-wrap`, no horizontal scrollbar. **Screenshot:** `test8_{HMMSS}_02_mobile_quiz_card.png`
- [ ] **Action 03 — down-arrow tap-target:** assert the down-arrow button `height >= 44 px`. Tap it. **Screenshot:** `test8_{HMMSS}_03_mobile_down_arrow.png`
- [ ] **Action 04 — mobile chapter card:** verify the chapter card renders with full markdown body, no overflow, `font-size >= 12 px`. Scroll to the bottom to confirm the whole chapter text is reachable. **Screenshot:** `test8_{HMMSS}_04_mobile_chapter_card.png`
- [ ] **Action 05 — BookSelector mobile filter:** tap BookSelector, choose **Learning Phrases**. Verify only lesson-5 items remain; counter updates. **Screenshot:** `test8_{HMMSS}_05_mobile_book_filter.png`
- [ ] **Action 06 — empty state on unmatched filter:** pick a book with no liked items (e.g. `coach`). Verify `No favorites in this book yet.` copy is fully visible (no truncation). **Screenshot:** `test8_{HMMSS}_06_mobile_empty_book.png`

**Mobile findings checklist:** overflow-free on both card types; markdown images/code blocks (if any) wrap or scroll within their container; down-arrow ≥ 44 px.

### Report

IN QUEUE

**Findings:** _(placeholder — to be filled after execution)_

**Improvement Proposals:**
+ _(placeholder — to be filled after execution)_

---

## Test 9 — Mobile — Validation & edge cases at 375 × 812

**User:** `alan`
**Viewport:** 375 × 812
**Seed:** Cleanup only.
**Goal:** Replay Test 4 on mobile. Confirm the API idempotency + 404 probes behave identically and the optimistic UI never flashes a filled state on error.

- [ ] **Action 01 — /slides loaded:** navigate. Overflow check. **Screenshot:** `test9_{HMMSS}_01_mobile_slides_loaded.png`
- [ ] **Action 02 — double-tap heart:** double-tap in under 300 ms. Verify only one `POST /like` is logged in `read_network_requests`. **Screenshot:** `test9_{HMMSS}_02_mobile_double_tap_one_post.png`
- [ ] **Action 03 — 404 probe via devtools:** run `fetch('/api/slides/chapters/999999/like', { method: 'POST', credentials: 'include' }).then(r => r.status)`. Expect `404`. **Screenshot:** `test9_{HMMSS}_03_mobile_chapter_404.png`
- [ ] **Action 04 — simulated error rollback:** in `javascript_tool`, intercept the next `POST /like` with a synthetic 500 (e.g., temporarily install a `fetch` shim). Tap an outline heart. Verify the UI rolls back to outline after the failure (no lingering filled state). **Screenshot:** `test9_{HMMSS}_04_mobile_error_rollback.png`
- [ ] **Action 05 — /favorite empty-state copy:** navigate. Verify empty-state message + link are within 375 px and link is tappable (`height >= 44 px`). **Screenshot:** `test9_{HMMSS}_05_mobile_empty_copy.png`

**Mobile findings checklist:** no double-POST; optimistic UI rolls back cleanly; empty-state link tappable.

### Report

IN QUEUE

**Findings:** _(placeholder — to be filled after execution)_

**Improvement Proposals:**
+ _(placeholder — to be filled after execution)_

---

## Test 10 — Mobile — Permission guard at 375 × 812

**User:** (none — signed out)
**Viewport:** 375 × 812
**Seed:** none.
**Goal:** Replay Test 5 on mobile. Confirm `/favorite`, `POST /chapters/{id}/like`, and `GET /liked-items` are all 4xx without a session.

- [ ] **Action 01 — sign out:** tap logout or navigate to `/login`. **Screenshot:** `test10_{HMMSS}_01_mobile_logged_out.png`
- [ ] **Action 02 — /favorite redirect:** navigate to `http://localhost:3999/favorite`. Verify redirect to `/login` and the login form is full-width with submit ≥ 44 px. **Screenshot:** `test10_{HMMSS}_02_mobile_favorite_redirect.png`
- [ ] **Action 03 — unauth POST /chapter/like → 401:** `fetch('/api/slides/chapters/16/like', { method: 'POST', credentials: 'include' }).then(r => r.status)`. Expect `401`. **Screenshot:** `test10_{HMMSS}_03_mobile_chapter_401.png`
- [ ] **Action 04 — unauth GET /liked-items → 401:** `fetch('/api/slides/liked-items', { credentials: 'include' }).then(r => r.status)`. Expect `401`. **Screenshot:** `test10_{HMMSS}_04_mobile_liked_items_401.png`
- [ ] **Action 05 — sign back in + landed on /slides:** submit credentials. Verify redirect to `/slides` and no overflow on the landed page. **Screenshot:** `test10_{HMMSS}_05_mobile_signed_in.png`

**Mobile findings checklist:** login inputs full-width; submit ≥ 44 px; unauth API returns 4xx; no redirect loop.

### Report

IN QUEUE

**Findings:** _(placeholder — to be filled after execution)_

**Improvement Proposals:**
+ _(placeholder — to be filled after execution)_
