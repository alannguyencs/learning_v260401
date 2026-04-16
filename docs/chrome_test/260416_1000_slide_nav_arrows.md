# Chrome E2E Tests — Slide Navigation Arrows (Coach UI)

## Remarks

- **Frontend port**: `http://localhost:3000`
- **Backend port**: `http://localhost:8000`
- **Sign-in flow**: Navigate to `http://localhost:3000/login`, enter username and password, click Login → redirected to `/slides`.
- **Sign-out flow**: Trigger logout via the logout button or navigate to `/login`.
- **Seed data**: Tests require at least one book with one lesson containing two chapters, each with at least one quiz. See Database Pre-Interaction below.
- **Cleanup**: Run the DELETE statements below before each test session.
- **Screenshots directory**: `data/chrome_test_images/260416_1000_slide_nav_arrows/`

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
>   - `HMMSS` is the last 5 digits of the system clock `HHMMSS` at the moment of capture
>   - `NN` is a two-digit action sequence number within the test (`01`, `02`, …)
>   - `name` is a short kebab-snake label describing the visible state
> - Before each `screencapture` call, bring the target application tab to the front of its Chrome window via AppleScript.

---

## Database Pre-Interaction

### Seed data

Run the following before executing tests (replace `<test_user>` with the actual test username):

```sql
-- Seed: one book
INSERT INTO books (book_id, title) VALUES ('nav_test_book', 'Nav Test Book')
ON CONFLICT DO NOTHING;

-- Seed: one lesson
INSERT INTO lessons (book_id, lesson_index, title)
VALUES ('nav_test_book', 1, 'Nav Test Lesson')
ON CONFLICT DO NOTHING;

-- Seed: two chapters
INSERT INTO chapters (lesson_id, chapter_index, title, content)
VALUES (
  (SELECT id FROM lessons WHERE book_id='nav_test_book' AND lesson_index=1),
  1, 'Chapter 1 - Navigation Test', '# Navigation Test\n\nThis chapter tests the down-arrow navigation.'
) ON CONFLICT DO NOTHING;

INSERT INTO chapters (lesson_id, chapter_index, title, content)
VALUES (
  (SELECT id FROM lessons WHERE book_id='nav_test_book' AND lesson_index=1),
  2, 'Chapter 2 - Second Chapter', '# Second Chapter\n\nThis is the second chapter content.'
) ON CONFLICT DO NOTHING;

-- Seed: one MC quiz on Chapter 1
INSERT INTO chapter_quizzes (chapter_id, quiz_type, question, expected_answer, option_a, option_b, option_c, option_d, correct_options)
VALUES (
  (SELECT id FROM chapters WHERE lesson_id=(SELECT id FROM lessons WHERE book_id='nav_test_book' AND lesson_index=1) AND chapter_index=1),
  'multiple_choice', 'What does this chapter test?', NULL,
  'Navigation', 'Authentication', 'Database', 'None of the above',
  '["A"]'
) ON CONFLICT DO NOTHING;

-- Seed: one free_recall quiz on Chapter 2
INSERT INTO chapter_quizzes (chapter_id, quiz_type, question, expected_answer, correct_options)
VALUES (
  (SELECT id FROM chapters WHERE lesson_id=(SELECT id FROM lessons WHERE book_id='nav_test_book' AND lesson_index=1) AND chapter_index=2),
  'free_recall', 'Describe the second chapter content.', 'The second chapter covers navigation test content.',
  NULL
) ON CONFLICT DO NOTHING;
```

### Cleanup

```sql
DELETE FROM slide_history WHERE username = '<test_user>';
DELETE FROM slide_position WHERE username = '<test_user>';
DELETE FROM quiz_skip_log WHERE username = '<test_user>';
DELETE FROM quiz_answer_log WHERE username = '<test_user>';
DELETE FROM lesson_revision_rounds WHERE username = '<test_user>';
DELETE FROM user_lesson_count WHERE username = '<test_user>';
DELETE FROM user_chapter_progress WHERE username = '<test_user>';
```

---

## Pre-requisite

Sign in as the test user before running any test. Navigate to `http://localhost:3000/login`, enter credentials, and verify redirect to `/slides`.

---

## Test 1 — Down arrow on chapter marks as learnt and advances (Desktop)

**Test name**: Chapter slide down arrow marks chapter as learnt
**Viewport**: 1440 × 900 (desktop)
**User**: `<test_user>` (fresh state, no progress)

- [ ] **Action 01 — set desktop viewport:** call `mcp__claude-in-chrome__resize_window` with `width: 1440, height: 900`. Verify `window.innerWidth === 1440` via `javascript_tool`. **Screenshot:** `test1_{HMMSS}_01_desktop_viewport_set.png`
- [ ] **Action 02 — slides page loaded:** navigate to `http://localhost:3000/slides`. Verify a chapter slide is displayed (not a quiz). **Screenshot:** `test1_{HMMSS}_02_chapter_slide_loaded.png`
- [ ] **Action 03 — verify no Skip Chapter button:** confirm no "Skip Chapter" button is visible inside the chapter card. **Screenshot:** `test1_{HMMSS}_03_no_skip_button.png`
- [ ] **Action 04 — verify ArrowUp absent:** confirm the up-arrow is NOT visible (no history yet, `hasPrevious` is false). **Screenshot:** `test1_{HMMSS}_04_no_arrow_up.png`
- [ ] **Action 05 — verify fixed ArrowDown visible:** confirm the down-arrow chevron button is visible and fixed at the bottom of the viewport (not inline with the slide card content). **Screenshot:** `test1_{HMMSS}_05_arrow_down_fixed.png`
- [ ] **Action 06 — click down arrow:** click the fixed down-arrow button. **Screenshot:** `test1_{HMMSS}_06_down_arrow_clicked.png`
- [ ] **Action 07 — chapter advance confirmed:** verify the page has advanced. The slide should now show either a quiz (if chapter 1's quizzes are now due) or chapter 2. Verify the previous chapter (Chapter 1) is no longer shown. **Screenshot:** `test1_{HMMSS}_07_slide_advanced.png`
- [ ] **Action 08 — verify ArrowUp now visible:** confirm the up-arrow is now visible above the BookSelector (has_previous = true after advancing). **Screenshot:** `test1_{HMMSS}_08_arrow_up_visible.png`

**Expected UI state**: Down arrow on chapter advances and records chapter as learnt. No "Skip Chapter" button in the chapter card. ArrowDown is fixed at the bottom of viewport. ArrowUp appears after first advance.
**Error handling**: If "Skip Chapter" button is still visible, flag — component not updated. If down arrow is not fixed at bottom, flag — layout not updated.
**Report**: IN QUEUE
- Findings: _none yet_
- Improvement Proposals:
  + good to have - arrow animation - subtle bounce on the down arrow to invite interaction

---

## Test 2 — Down arrow on quiz (no feedback) skips quiz (Desktop)

**Test name**: Down arrow skips a quiz before submission
**Viewport**: 1440 × 900 (inherited from Test 1)
**User**: `<test_user>`

- [ ] **Action 01 — ensure on quiz slide:** navigate to `/slides` and verify a quiz slide is shown. If a chapter is shown first, click "Mark as Learnt" to advance to a quiz. **Screenshot:** `test2_{HMMSS}_01_quiz_slide_loaded.png`
- [ ] **Action 02 — verify no explicit Skip button:** confirm no "Skip" button is visible inside the quiz card (before submitting). **Screenshot:** `test2_{HMMSS}_02_no_skip_button_in_quiz.png`
- [ ] **Action 03 — note quiz question:** screenshot the quiz question text so we can verify it reappears at the back of the queue later. **Screenshot:** `test2_{HMMSS}_03_quiz_question_noted.png`
- [ ] **Action 04 — click down arrow (skip via arrow):** click the fixed down-arrow button without submitting an answer. **Screenshot:** `test2_{HMMSS}_04_down_arrow_skip.png`
- [ ] **Action 05 — slide advanced (quiz skipped):** verify the page has moved to the next slide. The skipped quiz should go to the back of the queue and not immediately reappear. **Screenshot:** `test2_{HMMSS}_05_after_skip_next_slide.png`

**Expected UI state**: No "Skip" button inside the quiz card. The fixed down arrow acts as the skip mechanism before feedback. After clicking, the next slide is shown.
**Error handling**: If a "Skip" button is still visible inside the quiz card, flag — component not updated. If clicking the down arrow does not advance the slide, flag — handler not wired.
**Report**: IN QUEUE
- Findings: _none yet_
- Improvement Proposals:
  + good to have - skip confirmation - brief visual indicator (e.g. swipe animation) when a quiz is skipped via arrow

---

## Test 3 — Down arrow after quiz feedback advances to next slide (Desktop)

**Test name**: Down arrow advances after feedback is shown (no Next Slide button)
**Viewport**: 1440 × 900 (inherited from Test 1)
**User**: `<test_user>`

- [ ] **Action 01 — on quiz slide:** navigate to `/slides`, ensure a quiz slide is shown. **Screenshot:** `test3_{HMMSS}_01_quiz_slide.png`
- [ ] **Action 02 — submit an answer:** type or select an answer and click "Submit Answer". **Screenshot:** `test3_{HMMSS}_02_answer_submitted.png`
- [ ] **Action 03 — feedback shown:** verify PASSED/FAILED badge and feedback panel appear. **Screenshot:** `test3_{HMMSS}_03_feedback_shown.png`
- [ ] **Action 04 — verify no Next Slide button:** confirm no "Next Slide" button is visible inside the feedback panel. **Screenshot:** `test3_{HMMSS}_04_no_next_slide_button.png`
- [ ] **Action 05 — verify down arrow still visible:** confirm the fixed down arrow is still visible at the bottom. **Screenshot:** `test3_{HMMSS}_05_down_arrow_with_feedback.png`
- [ ] **Action 06 — click down arrow to advance:** click the fixed down arrow. **Screenshot:** `test3_{HMMSS}_06_down_arrow_clicked.png`
- [ ] **Action 07 — next slide shown:** verify the page has advanced past the quiz with feedback to the next slide. **Screenshot:** `test3_{HMMSS}_07_next_slide_loaded.png`

**Expected UI state**: After feedback is shown, "Next Slide" button is absent. The fixed down arrow is the only way to advance. Clicking it loads the next slide.
**Error handling**: If a "Next Slide" button appears in the feedback panel, flag — component not updated. If the down arrow does not advance after feedback, flag — handler condition not working.
**Report**: IN QUEUE
- Findings: _none yet_
- Improvement Proposals:
  + good to have - down arrow pulse - brief highlight on the down arrow after feedback appears to draw attention to it

---

## Test 4 — Up arrow navigation (back through history) (Desktop)

**Test name**: ArrowUp returns to previous slide with feedback preserved
**Viewport**: 1440 × 900 (inherited from Test 1)
**User**: `<test_user>`

- [ ] **Action 01 — start on chapter slide:** navigate to `/slides`. Verify chapter is shown. Note chapter title. **Screenshot:** `test4_{HMMSS}_01_chapter_slide.png`
- [ ] **Action 02 — verify ArrowUp position:** confirm ArrowUp is positioned ABOVE the BookSelector dropdown (not beside the ArrowDown). **Screenshot:** `test4_{HMMSS}_02_arrow_up_above_selector.png`
- [ ] **Action 03 — advance via down arrow:** click the fixed down arrow on the chapter slide. **Screenshot:** `test4_{HMMSS}_03_advanced_slide.png`
- [ ] **Action 04 — verify ArrowUp visible:** confirm the up-arrow is visible above the BookSelector. **Screenshot:** `test4_{HMMSS}_04_arrow_up_visible.png`
- [ ] **Action 05 — click ArrowUp:** click the up-arrow above the BookSelector. **Screenshot:** `test4_{HMMSS}_05_up_arrow_clicked.png`
- [ ] **Action 06 — previous slide restored:** verify the previous chapter slide is shown again (same title as noted in Action 01). **Screenshot:** `test4_{HMMSS}_06_previous_slide_shown.png`
- [ ] **Action 07 — verify ArrowUp hidden again:** after going back to the first slide, confirm ArrowUp is no longer visible (no further history). **Screenshot:** `test4_{HMMSS}_07_arrow_up_hidden.png`

**Expected UI state**: ArrowUp sits above the BookSelector as a full-width centered row. It only appears when `hasPrevious` is true. Clicking it restores the previous slide.
**Error handling**: If ArrowUp is positioned beside ArrowDown (inline row) rather than above BookSelector, flag — layout not updated. If ArrowUp appears when on the first slide, flag — hasPrevious logic error.
**Report**: IN QUEUE
- Findings: _none yet_
- Improvement Proposals:
  + good to have - swipe gesture - swipe up/down to navigate in addition to clicking arrows

---

## Test 5 — Unauthenticated access redirects to login (Desktop)

**Test name**: /slides requires authentication
**Viewport**: 1440 × 900 (inherited from Test 1)
**User**: none (logged out)

- [ ] **Action 01 — log out:** navigate to `http://localhost:3000/login` to clear session (or use logout flow). **Screenshot:** `test5_{HMMSS}_01_logged_out.png`
- [ ] **Action 02 — attempt /slides unauthenticated:** navigate directly to `http://localhost:3000/slides`. **Screenshot:** `test5_{HMMSS}_02_navigate_to_slides.png`
- [ ] **Action 03 — redirected to login:** verify the page redirects to `/login` and shows the login form (not the slide interface). **Screenshot:** `test5_{HMMSS}_03_redirected_to_login.png`

**Expected UI state**: Unauthenticated users cannot access `/slides`. They are redirected to `/login`.
**Error handling**: If the slides page renders without authentication, flag — ProtectedRoute not working.
**Report**: IN QUEUE
- Findings: _none yet_
- Improvement Proposals:
  + good to have - redirect back - after login, redirect to originally requested URL

---

## Test 6 — Down arrow on chapter marks as learnt and advances (Mobile)

**Test name**: Chapter slide down arrow marks chapter as learnt (mobile)
**Viewport**: 375 × 812 (mobile)
**User**: `<test_user>` (fresh state)

- [ ] **Action 01 — set mobile viewport:** call `mcp__claude-in-chrome__resize_window` with `width: 375, height: 812`. Verify `window.innerWidth === 375` via `javascript_tool`. **Screenshot:** `test6_{HMMSS}_01_mobile_viewport_set.png`
- [ ] **Action 02 — navigate to slides:** navigate to `http://localhost:3000/slides`. Verify chapter slide loaded on mobile. **Screenshot:** `test6_{HMMSS}_02_mobile_chapter_loaded.png`
- [ ] **Action 03 — horizontal overflow check:** run the overflow JS snippet. Verify `hasOverflow === false`. **Screenshot:** `test6_{HMMSS}_03_mobile_overflow_check.png`
- [ ] **Action 04 — verify no Skip Chapter button:** confirm "Skip Chapter" button absent inside chapter card. **Screenshot:** `test6_{HMMSS}_04_mobile_no_skip.png`
- [ ] **Action 05 — tap target check on down arrow:** verify the fixed down-arrow button has `getBoundingClientRect().height >= 44`. **Screenshot:** `test6_{HMMSS}_05_mobile_down_arrow_tap_target.png`
- [ ] **Action 06 — click down arrow:** click the fixed down arrow. **Screenshot:** `test6_{HMMSS}_06_mobile_down_arrow_clicked.png`
- [ ] **Action 07 — slide advanced on mobile:** verify next slide shown. Verify ArrowUp appears above BookSelector. **Screenshot:** `test6_{HMMSS}_07_mobile_advanced.png`
- [ ] **Action 08 — scroll reachability check:** scroll to bottom of page. Verify no content hidden behind fixed footer. **Screenshot:** `test6_{HMMSS}_08_mobile_scroll_bottom.png`

**Expected UI state**: Same behavior as Test 1 but on mobile. No overflow. Down arrow is at least 44 px tall. No "Skip Chapter" button.
**Error handling**: Horizontal overflow or button height < 44 px → flag immediately.
**Report**: IN QUEUE
- Findings: _none yet_
- Improvement Proposals:
  + good to have - mobile swipe - swipe gestures for navigation on touch devices

---

## Test 7 — Down arrow skips quiz before submission (Mobile)

**Test name**: Down arrow skips quiz (mobile)
**Viewport**: 375 × 812 (inherited from Test 6)
**User**: `<test_user>`

- [ ] **Action 01 — on quiz slide (mobile):** verify a quiz slide is displayed at mobile viewport. **Screenshot:** `test7_{HMMSS}_01_mobile_quiz_loaded.png`
- [ ] **Action 02 — overflow check on quiz:** run overflow JS. Verify `hasOverflow === false`. **Screenshot:** `test7_{HMMSS}_02_mobile_quiz_overflow.png`
- [ ] **Action 03 — verify no Skip button (mobile):** confirm "Skip" button absent inside quiz card. **Screenshot:** `test7_{HMMSS}_03_mobile_no_skip_button.png`
- [ ] **Action 04 — tap target check on down arrow:** verify `getBoundingClientRect().height >= 44` for the fixed arrow button. **Screenshot:** `test7_{HMMSS}_04_mobile_arrow_tap_target.png`
- [ ] **Action 05 — click down arrow to skip:** click the fixed down arrow without submitting. **Screenshot:** `test7_{HMMSS}_05_mobile_skip_via_arrow.png`
- [ ] **Action 06 — next slide shown on mobile:** verify slide advanced. **Screenshot:** `test7_{HMMSS}_06_mobile_after_skip.png`

**Expected UI state**: Mobile quiz skip via arrow works. No explicit Skip button visible.
**Error handling**: Overflow → flag. Tap target < 44 px → flag. Skip button still visible → flag.
**Report**: IN QUEUE
- Findings: _none yet_
- Improvement Proposals:
  + good to have - swipe left to skip - swipe gesture instead of arrow tap

---

## Test 8 — Down arrow after feedback advances (Mobile)

**Test name**: Down arrow advances after feedback, no Next Slide button (mobile)
**Viewport**: 375 × 812 (inherited from Test 6)
**User**: `<test_user>`

- [ ] **Action 01 — on quiz slide (mobile):** verify quiz slide shown. **Screenshot:** `test8_{HMMSS}_01_mobile_quiz_slide.png`
- [ ] **Action 02 — submit answer:** type or select an answer, click "Submit Answer". **Screenshot:** `test8_{HMMSS}_02_mobile_answer_submitted.png`
- [ ] **Action 03 — feedback shown (mobile):** verify PASSED/FAILED badge appears. **Screenshot:** `test8_{HMMSS}_03_mobile_feedback_shown.png`
- [ ] **Action 04 — overflow check with feedback:** run overflow JS. Verify `hasOverflow === false`. **Screenshot:** `test8_{HMMSS}_04_mobile_feedback_overflow.png`
- [ ] **Action 05 — verify no Next Slide button (mobile):** confirm "Next Slide" button absent in feedback panel. **Screenshot:** `test8_{HMMSS}_05_mobile_no_next_slide.png`
- [ ] **Action 06 — text readability check:** verify feedback text `fontSize >= 12px` via `getComputedStyle`. **Screenshot:** `test8_{HMMSS}_06_mobile_text_readability.png`
- [ ] **Action 07 — click down arrow to advance:** click the fixed down arrow. **Screenshot:** `test8_{HMMSS}_07_mobile_down_arrow_advance.png`
- [ ] **Action 08 — next slide shown (mobile):** verify next slide loaded on mobile. **Screenshot:** `test8_{HMMSS}_08_mobile_next_loaded.png`

**Expected UI state**: No Next Slide button in feedback. Down arrow advances. Feedback text readable. No overflow.
**Error handling**: Next Slide button visible → flag. Overflow → flag. Text < 12 px → flag.
**Report**: IN QUEUE
- Findings: _none yet_
- Improvement Proposals:
  + good to have - larger feedback text on mobile - increase font size for key points list

---

## Test 9 — Up arrow navigation (Mobile)

**Test name**: ArrowUp position and navigation on mobile
**Viewport**: 375 × 812 (inherited from Test 6)
**User**: `<test_user>`

- [ ] **Action 01 — chapter slide (mobile):** navigate to `/slides`. Chapter slide shown. **Screenshot:** `test9_{HMMSS}_01_mobile_chapter.png`
- [ ] **Action 02 — ArrowUp position check:** verify ArrowUp (if visible) is above BookSelector, not beside ArrowDown. If not visible (first slide), verify it's absent. **Screenshot:** `test9_{HMMSS}_02_mobile_arrow_up_position.png`
- [ ] **Action 03 — advance via down arrow:** click down arrow to advance. **Screenshot:** `test9_{HMMSS}_03_mobile_advanced.png`
- [ ] **Action 04 — ArrowUp tap target:** verify ArrowUp button has `getBoundingClientRect().height >= 44`. **Screenshot:** `test9_{HMMSS}_04_mobile_up_arrow_tap_target.png`
- [ ] **Action 05 — click ArrowUp:** click up arrow to go back. **Screenshot:** `test9_{HMMSS}_05_mobile_up_arrow_clicked.png`
- [ ] **Action 06 — previous slide restored (mobile):** verify previous chapter is shown again. **Screenshot:** `test9_{HMMSS}_06_mobile_prev_slide_restored.png`
- [ ] **Action 07 — overflow check after navigation:** run overflow JS. `hasOverflow === false`. **Screenshot:** `test9_{HMMSS}_07_mobile_nav_overflow.png`

**Expected UI state**: ArrowUp is above BookSelector on mobile. Tap target >= 44 px. Navigation works. No overflow.
**Error handling**: ArrowUp tap target < 44 px → flag. Overflow after navigation → flag.
**Report**: IN QUEUE
- Findings: _none yet_
- Improvement Proposals:
  + good to have - haptic feedback - vibration on skip/advance on mobile

---

## Test 10 — Unauthenticated access redirects to login (Mobile)

**Test name**: /slides protected on mobile
**Viewport**: 375 × 812 (inherited from Test 6)
**User**: none (logged out)

- [ ] **Action 01 — log out (mobile):** navigate to `/login` to clear session. **Screenshot:** `test10_{HMMSS}_01_mobile_logged_out.png`
- [ ] **Action 02 — attempt /slides (mobile):** navigate to `http://localhost:3000/slides`. **Screenshot:** `test10_{HMMSS}_02_mobile_navigate_slides.png`
- [ ] **Action 03 — redirected to login (mobile):** verify redirect to `/login`, login form visible. **Screenshot:** `test10_{HMMSS}_03_mobile_login_redirect.png`
- [ ] **Action 04 — overflow check on login page (mobile):** run overflow JS. `hasOverflow === false`. **Screenshot:** `test10_{HMMSS}_04_mobile_login_overflow.png`
- [ ] **Action 05 — tap target on Login button:** verify Login button `getBoundingClientRect().height >= 44`. **Screenshot:** `test10_{HMMSS}_05_mobile_login_tap_target.png`

**Expected UI state**: Redirect to login works on mobile. Login page has no horizontal overflow. Login button is tappable (>= 44 px).
**Error handling**: Overflow on login page → flag. Login button < 44 px → flag.
**Report**: IN QUEUE
- Findings: _none yet_
- Improvement Proposals:
  + good to have - auto-focus - auto-focus the username field on mobile login
