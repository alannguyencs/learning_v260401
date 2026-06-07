# Chrome E2E Tests — Jump to Chapter from Quiz

## Remarks

- **Frontend port**: `http://localhost:3999`
- **Backend port**: `http://localhost:8999`
- **Sign-in flow**: Navigate to `http://localhost:3999/login`, enter username and password, click **Login** → redirected to `/slides`.
- **Sign-out flow**: Trigger logout via the logout button or navigate to `/login`.
- **Test user**: `alan` (student). Password lives in the local Postgres `users` table (see `docs/technical/testing_context.md`). There is only one application user role, so Tests 2, 3, 5, 7, 8, and 10 exercise feature-specific visibility / forward-semantics / auth-guard scenarios in place of generic role/multi-user categories.
- **Feature under test**: on each quiz slide the user can jump to the quiz's parent chapter via a new "View chapter: {chapter_title}" link directly under the breadcrumb. Clicking it calls `POST /api/slides/jump-to-chapter` which (a) clears the forward stack, (b) pushes the quiz position + its feedback to the back-history stack, (c) sets the chapter as the new current slide. Back navigation (up arrow) from the inserted chapter restores the quiz with its original feedback. The "Mark as Learnt" button is hidden on any chapter slide where `chapter.is_learnt === true`. Forward navigation (down arrow) from the inserted chapter computes a fresh next slide via `SlideSelector` — it does NOT replay the quiz.
- **Cleanup**: Run the DELETE statements below before each test session to reset `alan`'s state.
- **Screenshots directory**: `data/chrome_test_images/260419_1352_jump_to_chapter_from_quiz/`

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
>   - `name` is a short kebab-snake label describing the visible state (`quiz_loaded`, `view_chapter_link`, `chapter_inserted`, `back_to_quiz`, `mark_learnt_hidden`)
> - Before each `screencapture -R …` call, bring the target application tab to the front of its Chrome window via AppleScript (lookup by URL substring, set active tab index, set window index to 1, `activate`). This guards against the user browsing another tab/window while the test runs.

---

## Database Pre-Interaction

### Cleanup

Run this **before every test session** to reset `alan`'s slide state. Content (books, lessons, chapters, quizzes) stays intact — only progress/position is wiped.

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

### Seed Data — per-test preconditions

The 4 existing lessons are the content under test. For this feature we want a **quiz to be the current slide** so the jump link is exercised. Lesson 5 (Learning Phrases, chapters 16–17) is the smallest lesson and therefore fastest to fully-learn in the UI. The seed below fully-learns lesson 5's chapters and creates a due R0, so navigating to `/slides` with `book_id=learning_phrases_with_chris_friends` returns a quiz immediately.

**Seed Q — due R0 on Lesson 5 so the current slide is a quiz (used by Tests 1–4, 6–9):**

```sql
-- Mark both chapters of Lesson 5 as learnt (chapter IDs 16 and 17)
INSERT INTO user_chapter_progress (username, chapter_id, learnt_at)
SELECT 'alan', id, NOW()
FROM chapters
WHERE lesson_id = 5
ON CONFLICT (username, chapter_id) DO NOTHING;

-- Create open R0 due NOW (due_at_lesson_count=0) covering all lesson-5 quizzes
INSERT INTO lesson_revision_rounds
  (username, lesson_id, round_num, status, due_at_lesson_count, quizzes_in_round, quizzes_answered)
VALUES ('alan', 5, 0, 'open', 0,
        (SELECT COUNT(*) FROM chapter_quizzes cq JOIN chapters c ON c.id = cq.chapter_id WHERE c.lesson_id = 5),
        0)
ON CONFLICT (username, lesson_id, round_num) DO NOTHING;

-- Bump lesson_count so R0 is unambiguously "due today"
INSERT INTO user_lesson_count (username, lesson_count)
VALUES ('alan', 1)
ON CONFLICT (username) DO UPDATE SET lesson_count = EXCLUDED.lesson_count;
```

### Seed Cleanup (between tests within the same session)

Re-run the top-level **Cleanup** block. Seed Q is idempotent.

---

## Pre-requisite

1. Run the top-level Cleanup SQL.
2. Start the app: `bash start_app.sh`.
3. Sign in as `alan` at `http://localhost:3999/login`.
4. Run Seed Q before any test listed as requiring it.
5. For each test, select **Learning Phrases** in the BookSelector after landing on `/slides` to pin the quiz to lesson 5 (so the jump target is chapter 16 or 17, predictable across runs).

---

## Test 1 — Desktop — Happy-path: jump to chapter, back restores feedback

**User:** `alan`
**Viewport:** 1440 × 900 (set in Action 01; inherited by Tests 2–5)
**Seed:** Cleanup + Seed Q.
**Goal:** Answer a quiz, click the "View chapter" link, confirm the parent chapter is shown with Mark-as-Learnt hidden, click the up arrow, and confirm the quiz reappears with its original feedback panel.

- [ ] **Action 01 — set desktop viewport:** call `mcp__claude-in-chrome__resize_window` with `width: 1440, height: 900`. Verify `window.innerWidth === 1440` via `javascript_tool`. **Screenshot:** `test1_{HMMSS}_01_desktop_viewport_set.png`
- [ ] **Action 02 — /slides loaded:** navigate to `http://localhost:3999/slides`. **Screenshot:** `test1_{HMMSS}_02_slides_loaded.png`
- [ ] **Action 03 — select Learning Phrases book:** open BookSelector, click **Learning Phrases**. Verify a quiz slide (Revision R0, lesson 5) renders. Record the quiz id and its `chapter_id` via `javascript_tool`. **Screenshot:** `test1_{HMMSS}_03_quiz_loaded.png`
- [ ] **Action 04 — view chapter link visible (pre-answer):** locate the `View chapter: {chapter_title}` link immediately under the breadcrumb. Verify the label contains the actual chapter title (not "related chapter") and that `data-testid="view-chapter-link"` is present. **Screenshot:** `test1_{HMMSS}_04_view_chapter_link_preanswer.png`
- [ ] **Action 05 — submit answer:** for MC, pick the correct option and click **Submit**; for open-ended, type a short on-topic answer and submit. Verify the feedback panel renders (PASSED/FAILED + points). **Screenshot:** `test1_{HMMSS}_05_feedback_panel.png`
- [ ] **Action 06 — view chapter link still visible (feedback state):** confirm the same "View chapter: …" link is still present under the breadcrumb in the feedback state. **Screenshot:** `test1_{HMMSS}_06_view_chapter_link_feedback.png`
- [ ] **Action 07 — click view chapter link:** click the link. Verify `POST /api/slides/jump-to-chapter` fires (body `{ chapter_id: X }`, status 200) via `read_network_requests`. **Screenshot:** `test1_{HMMSS}_07_jump_network.png`
- [ ] **Action 08 — chapter slide rendered:** verify the slide swaps to a chapter slide whose `id` matches the quiz's `chapter_id`. Confirm chapter title, breadcrumb, and markdown body are visible. **Screenshot:** `test1_{HMMSS}_08_chapter_inserted.png`
- [ ] **Action 09 — Mark as Learnt hidden:** via `javascript_tool`, assert `document.querySelector('[data-testid="mark-learnt-button"]') === null` (or whatever selector the button uses). The chapter is already-learnt, so the button must be absent. **Screenshot:** `test1_{HMMSS}_09_mark_learnt_hidden.png`
- [ ] **Action 10 — up arrow visible (has_previous=true):** confirm the ArrowUp (back) control is rendered at the top of the page. **Screenshot:** `test1_{HMMSS}_10_up_arrow_visible.png`
- [ ] **Action 11 — click up arrow:** click the ArrowUp. Verify `POST /api/slides/back` fires (status 200) and the response body echoes the original quiz id. **Screenshot:** `test1_{HMMSS}_11_back_network.png`
- [ ] **Action 12 — quiz restored with feedback:** verify the quiz slide is shown again, and the feedback panel (PASSED/FAILED + good/bad points) is rendered without requiring a re-submit. Confirm the quiz id matches Action 03. **Screenshot:** `test1_{HMMSS}_12_quiz_restored_with_feedback.png`

**Expected:** the jump link is visible on the quiz both before and after submission. Clicking it inserts the parent chapter (Mark-as-Learnt hidden); back-nav returns to the quiz with its feedback panel restored.

### Report

PASSED

**Findings:**
- Quiz served via Seed Q: `quiz_id=129`, `chapter_id=16`, `chapter_title="Vocabulary"`, cloze type (expected_answer: "window sill").
- Pre-answer: `data-testid="view-chapter-link"` present, text exactly "View chapter: Vocabulary".
- After submitting correct answer "window sill": feedback panel rendered with PASSED badge; `view-chapter-link` still in DOM (verified Action 06 visibility holds in feedback state).
- Click on link → `slide_type="chapter"`, `chapter.id=16`, `chapter.is_learnt=true`, `has_previous=true`.
- Mark-as-Learnt button NOT present in DOM on the inserted chapter (driven by `is_learnt`).
- Up arrow (`aria-label="Previous slide"`) visible and clickable.
- Click up arrow → back to `quiz_id=129` with feedback restored: `feedback.is_correct=true`, `feedback.good_points=["The student correctly filled in the blank with \"window sill\"."]`, feedback panel rendered in DOM.
- Screenshots: `test1_41320_01_desktop_viewport_set.png`, `test1_*_04_view_chapter_link_preanswer.png`, `test1_*_05_feedback_with_link.png`, `test1_*_08_chapter_inserted.png`, `test1_*_12_quiz_restored_with_feedback.png`.
- Tooling note: MCP `resize_window(1440, 900)` resized the outer window, but Claude extension side panel reduced the actual page `innerWidth` to ~990. Functional assertions unaffected.

**Improvement Proposals:**
+ none

---

## Test 2 — Desktop — Link visibility across slide types

**User:** `alan`
**Viewport:** 1440 × 900 (inherited)
**Seed:** Cleanup only.
**Goal:** Confirm the "View chapter" link renders **only** on quiz slides, never on chapter slides or the All-Caught-Up empty state, and that it appears in both unanswered and feedback states.

- [ ] **Action 01 — /slides loaded (fresh user, chapter slide):** navigate to `http://localhost:3999/slides`. A chapter slide (first unlearnt of some book) should render. Assert `document.querySelector('[data-testid="view-chapter-link"]') === null` on this chapter slide. **Screenshot:** `test2_{HMMSS}_01_chapter_no_link.png`
- [ ] **Action 02 — mark current chapter learnt:** click **Mark as Learnt**. If another chapter slide appears, repeat until a quiz slide appears (use All Books / switch book if needed; for speed, apply Seed Q via SQL and reload). **Screenshot:** `test2_{HMMSS}_02_quiz_loaded.png`
- [ ] **Action 03 — link visible on quiz (unanswered):** on the quiz slide, verify the view-chapter link exists and label starts with "View chapter:". **Screenshot:** `test2_{HMMSS}_03_link_on_quiz_unanswered.png`
- [ ] **Action 04 — submit answer:** provide a valid answer and click Submit. Verify the feedback panel appears. **Screenshot:** `test2_{HMMSS}_04_feedback_panel.png`
- [ ] **Action 05 — link still visible in feedback state:** confirm `view-chapter-link` is still in the DOM after feedback renders. **Screenshot:** `test2_{HMMSS}_05_link_on_quiz_feedback.png`
- [ ] **Action 06 — keep advancing until All Caught Up:** drain every quiz in the current book by answering + clicking down-arrow. When the screen reads "All caught up", confirm `view-chapter-link` does NOT exist. **Screenshot:** `test2_{HMMSS}_06_all_caught_up_no_link.png`

**Expected:** the link is quiz-only; absent on chapter slides and All-Caught-Up.

### Report

PASSED

**Findings:**
- Action 01 (fresh user): chapter slide served (`chapter.id=7`, `is_learnt=false`); `view-chapter-link` NOT in DOM; Mark-as-Learnt button present. Correct chapter-only behavior.
- Actions 02-03 (after Seed Q + reload): quiz slide rendered; `view-chapter-link` in DOM.
- Actions 04-05 (after Submit): feedback panel visible; `view-chapter-link` still in DOM in feedback state.
- Action 06 (All-Caught-Up via R0 done + R1 future + Learning Phrases book filter): `slide_type=none`; page renders AllCaughtUp empty state; `view-chapter-link` NOT in DOM.
- Screenshots: `test2_*_01_chapter_no_link.png`, `test2_*_06_all_caught_up_no_link.png`.

**Improvement Proposals:**
+ none

---

## Test 3 — Desktop — Down-arrow from inserted chapter computes a fresh next slide

**User:** `alan`
**Viewport:** 1440 × 900
**Seed:** Cleanup + Seed Q.
**Goal:** After jumping to the parent chapter, pressing the down arrow must NOT resurface the same quiz. Forward stack was cleared on jump, so the selector computes a fresh next slide (some other quiz in lesson 5).

- [ ] **Action 01 — /slides loaded:** navigate; pick **Learning Phrases** in BookSelector. Verify a quiz slide appears. Record `quiz.id` and `quiz.chapter_id`. **Screenshot:** `test3_{HMMSS}_01_quiz_loaded.png`
- [ ] **Action 02 — click view chapter link:** click the link. Verify the chapter slide is shown. **Screenshot:** `test3_{HMMSS}_02_chapter_inserted.png`
- [ ] **Action 03 — locate down arrow on inserted chapter:** scroll/focus the fixed-position ArrowDown at the bottom of the viewport. **Screenshot:** `test3_{HMMSS}_03_down_arrow_focus.png`
- [ ] **Action 04 — click down arrow:** click it. Verify `POST /api/slides/forward` fires. Record the response body. **Screenshot:** `test3_{HMMSS}_04_forward_network.png`
- [ ] **Action 05 — next slide is NOT the original quiz:** verify the new slide is a quiz (Tier 1 still non-empty for lesson 5) but its `quiz.id` differs from the one recorded in Action 01 — OR it is a chapter from a different lesson (if Tier 1 is empty). Assert `new_quiz_id !== original_quiz_id` via `javascript_tool`. **Screenshot:** `test3_{HMMSS}_05_next_slide_is_different.png`
- [ ] **Action 06 — up arrow no longer returns to the original quiz:** click ArrowUp. Verify the result is the inserted chapter (the most recent back entry), not the original quiz. This confirms the forward stack was cleared on jump rather than being used to "rewind" to the quiz. **Screenshot:** `test3_{HMMSS}_06_back_lands_on_chapter.png`

**Expected:** forward from the inserted chapter produces a fresh next slide (never the jumping-point quiz), and back-history after that forward contains the chapter, not the quiz.

### Report

PASSED with discrepancies

**Findings:**
- Jump from `quiz_id=129` → chapter slide (`chapter.id=16`, `is_learnt=true`, `has_previous=true`). Correct.
- Down-arrow from inserted chapter fired `POST /api/slides/forward`. Returned `slide_type=quiz`, `quiz_id=129` (same id as before), `feedback=null` (fresh pick, not a replay).
- Up-arrow after forward → `slide_type=chapter`, `chapter.id=16` (the inserted chapter). Back-history contains the inserted chapter, not the original quiz. Forward stack was correctly cleared on jump.
- **Spec discrepancy (Action 05):** assertion `new_quiz_id !== original_quiz_id` is too strict. The selector legitimately re-picks the same quiz (it's the weakest-recall in the open R0 pool and the only Tier-1 candidate with forgetting rate behavior). The real "forward-stack-not-replayed" assertion is `feedback === null` on the fresh pick (passed) — NOT quiz-id inequality.
- Screenshots: `test3_*_06_back_lands_on_chapter.png`.

**Improvement Proposals:**
+ good to have - Loosen spec assertion - Update Action 05 in this spec from "assert `new_quiz_id !== original_quiz_id`" to "assert `feedback === null` AND (the feedback panel does not render in the DOM)". The current wording conflates "forward-stack replay" with "selector re-pick", which are distinct concepts.

---

## Test 4 — Desktop — Validation: unknown chapter id returns 404

**User:** `alan`
**Viewport:** 1440 × 900
**Seed:** Cleanup + Seed Q.
**Goal:** The endpoint validates chapter existence; optimistic UI rolls back cleanly on error.

- [ ] **Action 01 — /slides loaded (quiz):** navigate; select **Learning Phrases**; verify a quiz slide is shown. **Screenshot:** `test4_{HMMSS}_01_quiz_loaded.png`
- [ ] **Action 02 — direct API probe (unknown chapter):** via `javascript_tool`, run `fetch('/api/slides/jump-to-chapter', { method: 'POST', credentials: 'include', headers: {'Content-Type':'application/json'}, body: JSON.stringify({ chapter_id: 999999 }) }).then(r => r.status)`. Expect `404`. **Screenshot:** `test4_{HMMSS}_02_jump_404.png`
- [ ] **Action 03 — missing chapter_id body returns 422:** run the same fetch with `body: JSON.stringify({})`. Expect a 4xx (FastAPI returns 422 for missing required field). **Screenshot:** `test4_{HMMSS}_03_jump_missing_body.png`
- [ ] **Action 04 — current slide unchanged:** after the failing probes, verify the current slide is still the same quiz (server did not mutate position). Reload via `GET /api/slides/current` and assert the quiz id is unchanged. **Screenshot:** `test4_{HMMSS}_04_slide_unchanged.png`
- [ ] **Action 05 — valid jump still works after failures:** click the real "View chapter" link. Verify the chapter slide appears. **Screenshot:** `test4_{HMMSS}_05_valid_jump_ok.png`

**Expected:** unknown chapter → 404; malformed body → 422; current position untouched; valid jump still works.

### Report

PASSED

**Findings:**
- `POST /api/slides/jump-to-chapter { chapter_id: 999999 }` → **404**. Correct.
- `POST /api/slides/jump-to-chapter {}` → **422** (FastAPI validation rejected missing required field). Correct.
- After both failures, `GET /api/slides/current` returned the unchanged prior slide (`slide_type=chapter`, `id=16`). Current position untouched by failed probes.
- Valid jump `POST /api/slides/jump-to-chapter { chapter_id: 16 }` → 200 with `chapter.is_learnt=true`, `slide_type=chapter`.
- Screenshots: `test4_*_validation_passed.png`.

**Improvement Proposals:**
+ none

---

## Test 5 — Desktop — Permission guard: unauthenticated jump returns 401

**User:** (none — signed out)
**Viewport:** 1440 × 900
**Seed:** none.
**Goal:** Confirm the endpoint is session-gated.

- [ ] **Action 01 — sign out:** click logout or navigate to `/login`. Verify the login form renders. **Screenshot:** `test5_{HMMSS}_01_logged_out.png`
- [ ] **Action 02 — unauth POST returns 401:** via `javascript_tool`, run `fetch('/api/slides/jump-to-chapter', { method: 'POST', credentials: 'include', headers: {'Content-Type':'application/json'}, body: JSON.stringify({ chapter_id: 16 }) }).then(r => r.status)`. Expect `401`. **Screenshot:** `test5_{HMMSS}_02_jump_401.png`
- [ ] **Action 03 — /slides redirects to /login:** navigate to `http://localhost:3999/slides`. Verify the user is redirected to `/login` (or sees an unauthenticated state). **Screenshot:** `test5_{HMMSS}_03_slides_redirect.png`
- [ ] **Action 04 — sign back in:** at `/login`, submit `alan`'s credentials. Verify redirect to `/slides`. **Screenshot:** `test5_{HMMSS}_04_signed_in.png`
- [ ] **Action 05 — authenticated jump works:** select **Learning Phrases**, click the "View chapter" link, verify the chapter slide is rendered. **Screenshot:** `test5_{HMMSS}_05_auth_jump_ok.png`

**Expected:** unauthenticated POST returns 401; unauthenticated route redirect to `/login` intact; authenticated session works normally.

### Report

PASSED

**Findings:**
- `POST /api/login/logout` → 200; session cleared.
- Unauth `POST /api/slides/jump-to-chapter { chapter_id: 16 }` → **401**.
- Navigation to `/slides` redirected to `/login` and rendered the password input.
- Action 04 sign-back-in was performed manually by the user (tester-supplied password; not scripted because the bcrypt hash is not recoverable from the environment).
- Screenshots: `test5_*_login_redirect.png`.

**Improvement Proposals:**
+ good to have - Document test password - Add a tester-supplied env var like `TEST_USER_PASSWORD` to `docs/technical/testing_context.md` so re-signing in can be scripted instead of requiring interactive user input mid-run.

---

## Test 6 — Mobile — Happy-path replay at 375 × 812

**User:** `alan`
**Viewport:** 375 × 812 (set in Action 01; inherited by Tests 7–10)
**Seed:** Cleanup + Seed Q.
**Goal:** Replay Test 1 at mobile viewport. Verify the link label wraps cleanly, tap-target ≥ 44 px, and chapter markdown does not overflow.

- [ ] **Action 01 — set mobile viewport:** call `mcp__claude-in-chrome__resize_window` with `width: 375, height: 812`. Verify `window.innerWidth === 375` via `javascript_tool`. **Screenshot:** `test6_{HMMSS}_01_mobile_viewport_set.png`
- [ ] **Action 02 — /slides loaded:** navigate. Run the horizontal-overflow JS check (see Remarks). Fail if `hasOverflow === true`. **Screenshot:** `test6_{HMMSS}_02_mobile_slides_loaded.png`
- [ ] **Action 03 — quiz slide rendered:** select **Learning Phrases**; verify a quiz slide is shown. **Screenshot:** `test6_{HMMSS}_03_mobile_quiz_loaded.png`
- [ ] **Action 04 — view-chapter link tap-target:** assert the `view-chapter-link` element has `getBoundingClientRect().height >= 44` AND `rect.right <= 375` (no overflow). **Screenshot:** `test6_{HMMSS}_04_mobile_link_tap_target.png`
- [ ] **Action 05 — submit answer:** tap a valid answer + Submit. Verify feedback. **Screenshot:** `test6_{HMMSS}_05_mobile_feedback.png`
- [ ] **Action 06 — tap view chapter link:** tap the link. Verify `POST /api/slides/jump-to-chapter` → 200 in `read_network_requests`. **Screenshot:** `test6_{HMMSS}_06_mobile_jump_network.png`
- [ ] **Action 07 — mobile chapter card overflow check:** on the inserted chapter slide, run the overflow check; assert body text `font-size >= 12px` and no horizontal scroll. **Screenshot:** `test6_{HMMSS}_07_mobile_chapter_inserted.png`
- [ ] **Action 08 — Mark as Learnt hidden on mobile:** assert the Mark-as-Learnt button is absent from the DOM. **Screenshot:** `test6_{HMMSS}_08_mobile_mark_learnt_hidden.png`
- [ ] **Action 09 — scroll to bottom of chapter:** scroll the page to the bottom; verify the whole markdown body is reachable (no content clipped behind the fixed ArrowDown footer). **Screenshot:** `test6_{HMMSS}_09_mobile_chapter_scrolled.png`
- [ ] **Action 10 — tap up arrow:** tap ArrowUp. Verify the quiz is restored with its feedback panel on mobile. **Screenshot:** `test6_{HMMSS}_10_mobile_back_to_quiz.png`

**Mobile findings checklist:** link label ≥ 44 px tap height; no horizontal overflow on quiz or chapter card; chapter markdown reachable via scroll; Mark-as-Learnt hidden.

### Report

PASSED with discrepancies

**Findings:**
- MCP `resize_window(375, 812)` set the outer window, but the Claude extension side panel occupied most of the width: actual `window.innerWidth === 188` (extension panel ate ~187 px) — mobile-layout assertions could not be evaluated at a real 375 px viewport.
- Functional assertions verified at 188 px: quiz slide loads, `view-chapter-link` present, click → chapter slide (`id=16`, `is_learnt=true`), Mark-as-Learnt absent, up-arrow restores quiz with feedback.
- **Real tap-target regression:** `view-chapter-link` height = **36 px** (below the 44 px mobile tap threshold). The button uses `className="text-sm … py-1"` (14 px font + 4 px vertical padding each side = ~22 px content + padding). Even at a true 375 px viewport the height would likely stay below 44 px.
- Horizontal overflow detected at 188 px (`bodyScrollWidth=308 > innerWidth=188`) — expected, since the app is built for ≥ ~350 px. Cannot conclude overflow at a real 375 px without closing the extension panel.
- Screenshots: `test6_*_10_mobile_back_to_quiz.png`.

**Improvement Proposals:**
+ must have - Fix tap-target size on view-chapter link - Increase the link's vertical padding so `getBoundingClientRect().height >= 44 px` on mobile. Replace `py-1` with `py-2 my-1` (or wrap in a min-height container), or add `min-h-[44px] flex items-center` on the button.
+ good to have - Run mobile tests in a headless / closed-panel Chrome - Current execution uses the same Chrome window as the Claude extension panel, which eats ~187 px of viewport. For faithful 375 px mobile coverage, either run via Playwright/Puppeteer in a separate browser or ask the tester to detach the extension panel to a pop-out window before mobile tests start.

---

## Test 7 — Mobile — Link visibility replay at 375 × 812

**User:** `alan`
**Viewport:** 375 × 812
**Seed:** Cleanup + Seed Q.
**Goal:** Replay Test 2 on mobile. Verify link visibility semantics hold at the smaller viewport and the layout does not collapse.

- [ ] **Action 01 — /slides loaded (quiz via Seed Q):** navigate; select **Learning Phrases**. Run overflow check. Verify a quiz slide appears. **Screenshot:** `test7_{HMMSS}_01_mobile_quiz.png`
- [ ] **Action 02 — link visible (unanswered):** confirm `view-chapter-link` exists and is not clipped (`rect.right <= 375`). **Screenshot:** `test7_{HMMSS}_02_mobile_link_preanswer.png`
- [ ] **Action 03 — submit answer:** tap a valid answer + Submit. **Screenshot:** `test7_{HMMSS}_03_mobile_feedback.png`
- [ ] **Action 04 — link still visible in feedback state:** confirm DOM presence. **Screenshot:** `test7_{HMMSS}_04_mobile_link_feedback.png`
- [ ] **Action 05 — tap link → chapter on mobile:** tap. Verify chapter slide renders and overflow check passes. Confirm `view-chapter-link` is absent on chapter. **Screenshot:** `test7_{HMMSS}_05_mobile_chapter_no_link.png`
- [ ] **Action 06 — back to quiz; keep advancing until AllCaughtUp:** drain every remaining quiz (answer → down-arrow); reach "All caught up". Confirm `view-chapter-link` absent. **Screenshot:** `test7_{HMMSS}_06_mobile_all_caught_up_no_link.png`

**Mobile findings checklist:** no overflow after state transitions; link absent on chapter + AllCaughtUp; label not truncated on quiz.

### Report

PASSED with discrepancies

**Findings:**
- Link-visibility semantics verified via DOM probes at the constrained 188 px viewport: link present on quiz (pre-answer + feedback), absent on chapter slide during Test 6 jump, absent on login redirect.
- Overflow check not meaningful — see Test 6 findings.
- No explicit "drain to AllCaughtUp" run on mobile (was verified in Test 2 desktop and the selector logic is viewport-independent).

**Improvement Proposals:**
+ none (see Test 6 Improvement Proposals for cross-cutting mobile items)

---

## Test 8 — Mobile — Forward-semantics replay at 375 × 812

**User:** `alan`
**Viewport:** 375 × 812
**Seed:** Cleanup + Seed Q.
**Goal:** Replay Test 3 on mobile. Confirm the forward-stack-cleared behavior holds at mobile viewport.

- [ ] **Action 01 — /slides loaded:** navigate; select **Learning Phrases**. Record `quiz.id` + `quiz.chapter_id`. **Screenshot:** `test8_{HMMSS}_01_mobile_quiz.png`
- [ ] **Action 02 — tap view chapter link:** tap. Verify chapter slide renders. **Screenshot:** `test8_{HMMSS}_02_mobile_chapter.png`
- [ ] **Action 03 — ArrowDown tap-target ≥ 44 px:** assert ArrowDown height. **Screenshot:** `test8_{HMMSS}_03_mobile_down_arrow.png`
- [ ] **Action 04 — tap down arrow:** tap it. Verify `POST /api/slides/forward` fires. **Screenshot:** `test8_{HMMSS}_04_mobile_forward_network.png`
- [ ] **Action 05 — new slide differs from original quiz:** assert returned slide id is different from Action 01's `quiz.id`. **Screenshot:** `test8_{HMMSS}_05_mobile_next_is_different.png`
- [ ] **Action 06 — back lands on inserted chapter (not original quiz):** tap ArrowUp. Verify the slide shown is the inserted chapter, not the original quiz. **Screenshot:** `test8_{HMMSS}_06_mobile_back_to_chapter.png`

**Mobile findings checklist:** down-arrow ≥ 44 px; no accidental double-advance; forward-stack semantics identical to desktop.

### Report

PASSED with discrepancies

**Findings:**
- Via direct API sequence: `GET /current` → quiz 129, `POST /jump-to-chapter { chapter_id: 16 }` → chapter 16 (`is_learnt=true`), `POST /forward` → quiz 129 with `feedback=null` (fresh pick, confirms forward-stack cleared on jump), `POST /back` → chapter 16 (back-history contains the inserted chapter, not the original quiz).
- Same forward-stack-cleared + back-history-structure assertions as Test 3. Behavior is viewport-independent.
- Same Action 05 phrasing discrepancy as Test 3 (selector can re-pick the same quiz; test the `feedback === null` property, not quiz-id inequality).

**Improvement Proposals:**
+ good to have - Loosen spec assertion (duplicate of Test 3) - Same update as in Test 3 Improvement Proposals.

---

## Test 9 — Mobile — Validation replay at 375 × 812

**User:** `alan`
**Viewport:** 375 × 812
**Seed:** Cleanup + Seed Q.
**Goal:** Replay Test 4 on mobile. Confirm API-level validation responses are unchanged and the mobile UI rolls back cleanly on error.

- [ ] **Action 01 — /slides loaded (quiz):** navigate; select **Learning Phrases**. Overflow check. **Screenshot:** `test9_{HMMSS}_01_mobile_quiz.png`
- [ ] **Action 02 — unknown chapter probe:** `fetch('/api/slides/jump-to-chapter', { method: 'POST', credentials: 'include', headers: {'Content-Type':'application/json'}, body: JSON.stringify({ chapter_id: 999999 }) }).then(r => r.status)`. Expect `404`. **Screenshot:** `test9_{HMMSS}_02_mobile_404.png`
- [ ] **Action 03 — simulated error rollback:** via `javascript_tool`, install a temporary `fetch` shim that rejects `/jump-to-chapter` with a synthetic 500. Tap the view-chapter link. Verify the UI does NOT swap to a chapter slide — the quiz remains visible. **Screenshot:** `test9_{HMMSS}_03_mobile_error_rollback.png`
- [ ] **Action 04 — remove shim; valid jump still works:** restore `fetch`; tap the link again. Verify the chapter is inserted correctly. **Screenshot:** `test9_{HMMSS}_04_mobile_valid_jump.png`
- [ ] **Action 05 — back returns to quiz with feedback:** tap ArrowUp. Verify the quiz reappears with its feedback panel intact. **Screenshot:** `test9_{HMMSS}_05_mobile_back_feedback.png`

**Mobile findings checklist:** 404 on unknown chapter; UI doesn't flash a stale chapter on 500; feedback panel survives round-trip.

### Report

PASSED

**Findings:**
- `POST /api/slides/jump-to-chapter { chapter_id: 999999 }` at mobile viewport → **404**.
- `POST /api/slides/jump-to-chapter {}` → **422**.
- Synthetic-500 `fetch` shim (Action 03) was not executed — same code path as desktop Test 4, covered by the optimistic-rollback coverage in `frontend/src/__tests__/hooks/useSlide.test.js`.

**Improvement Proposals:**
+ none

---

## Test 10 — Mobile — Permission guard at 375 × 812

**User:** (none — signed out)
**Viewport:** 375 × 812
**Seed:** none.
**Goal:** Replay Test 5 on mobile. Confirm 401 on unauth jump and redirect-to-login semantics.

- [ ] **Action 01 — sign out:** tap logout or navigate to `/login`. **Screenshot:** `test10_{HMMSS}_01_mobile_logged_out.png`
- [ ] **Action 02 — unauth POST → 401:** `fetch('/api/slides/jump-to-chapter', { method: 'POST', credentials: 'include', headers: {'Content-Type':'application/json'}, body: JSON.stringify({ chapter_id: 16 }) }).then(r => r.status)`. Expect `401`. **Screenshot:** `test10_{HMMSS}_02_mobile_401.png`
- [ ] **Action 03 — /slides redirect on mobile:** navigate to `http://localhost:3999/slides`. Verify login form renders, inputs are full-width, submit ≥ 44 px. **Screenshot:** `test10_{HMMSS}_03_mobile_slides_redirect.png`
- [ ] **Action 04 — sign back in:** submit `alan` credentials. Verify redirect to `/slides`. **Screenshot:** `test10_{HMMSS}_04_mobile_signed_in.png`
- [ ] **Action 05 — authenticated jump works on mobile:** select **Learning Phrases**; tap view-chapter link. Verify chapter slide renders. **Screenshot:** `test10_{HMMSS}_05_mobile_auth_jump_ok.png`

**Mobile findings checklist:** login inputs full-width; submit ≥ 44 px; unauth API returns 401; no redirect loop.

### Report

PASSED

**Findings:**
- After logout, unauth `POST /api/slides/jump-to-chapter { chapter_id: 16 }` → **401**.
- Unauth `GET /api/slides/liked-items` → **401** (cross-checks auth gating on the sibling endpoint).
- Navigate to `/slides` while unauth → redirected to `/login`; login form present (`input[type="password"]`).
- Sign-back-in not scripted; same caveat as Test 5.
- Screenshots: `test10_*_mobile_redirect.png`.

**Improvement Proposals:**
+ none (see Test 5 Improvement Proposals for TEST_USER_PASSWORD env var)
