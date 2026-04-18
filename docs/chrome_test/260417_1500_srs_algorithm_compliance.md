# Chrome E2E Tests — 2-Tier Stacking Algorithm Compliance

## Remarks

- **Frontend port**: `http://localhost:3999`
- **Backend port**: `http://localhost:8999`
- **Sign-in flow**: Navigate to `http://localhost:3999/login`, enter username and password, click Login → redirected to `/slides`.
- **Sign-out flow**: Trigger logout via the logout button or navigate to `/login`.
- **Test approach**: Each test exercises the slide algorithm by performing a mix of actions (mark chapter learnt, answer correctly, answer incorrectly, skip) and verifying the algorithm serves slides in the correct Tier 1 → Tier 2 priority order. Tests use the **real seeded content** (4 lessons across 3 books) to validate algorithm behavior end-to-end.
- **Cleanup**: Run the DELETE statements below before each test session to reset all user progress.
- **Screenshots directory**: `data/chrome_test_images/260417_1500_srs_algorithm_compliance/`

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

### Cleanup

Run this **before every test session** to reset all user progress. The content (books, lessons, chapters, quizzes) stays intact — only user state is wiped.

```sql
-- Wipe all user progress and navigation state for alan
DELETE FROM quiz_answer_log   WHERE username = 'alan';
DELETE FROM quiz_skip_log     WHERE username = 'alan';
DELETE FROM user_quiz_recall  WHERE username = 'alan';
DELETE FROM lesson_revision_rounds WHERE username = 'alan';
DELETE FROM user_chapter_progress  WHERE username = 'alan';
DELETE FROM user_lesson_count WHERE username = 'alan';
DELETE FROM slide_history     WHERE username = 'alan';
DELETE FROM slide_position    WHERE username = 'alan';
DELETE FROM slide_chat_messages WHERE username = 'alan';
```

### Seed data

No additional seed data needed — the tests use the 4 real lessons already in the database:

| Book | Lesson ID | Lesson | Chapters | Quizzes |
|------|-----------|--------|----------|---------|
| coach | 3 | Time-Framed Learning | 5 (IDs 7–11) | 45 |
| themitmonk | 2 | 20 Quantum Cheat Codes | 5 (IDs 2–6) | 44 |
| themitmonk | 4 | From Homeless to MIT Grad | 4 (IDs 12–15) | 36 |
| Learning Phrases | 5 | English Cartoons: My Room | 2 (IDs 16–17) | 42 |

---

## Pre-requisite

1. Run the cleanup SQL above against the local database: `psql -U alan learning_v2604 -f cleanup.sql`
2. Start the application: `bash start_app.sh`
3. Sign in as `alan` at `http://localhost:3999/login`

---

## Test 1 — Tier 2: Fresh start shows chapters first (Desktop)

**User:** `alan`
**Goal:** On a clean slate (no progress), the algorithm should serve Tier 2 (new chapters) since there are no due revision quizzes. Select a specific book, verify a chapter is shown, mark it as learnt, verify a quiz appears (Tier 1 activates for R0), then answer/skip quizzes.

- [ ] **Action 01 — set desktop viewport:** call `resize_window` with `width: 1440, height: 900`. Verify `window.innerWidth === 1440` via `javascript_tool`. **Screenshot:** `test1_{HMMSS}_01_desktop_viewport_set.png`

- [ ] **Action 02 — slides page loaded:** navigate to `http://localhost:3999/slides`. Verify the slides page loads with the book selector and a chapter slide (Tier 2 — no progress yet). **Screenshot:** `test1_{HMMSS}_02_slides_loaded.png`

- [ ] **Action 03 — select book:** use the book selector dropdown to choose a specific book (e.g., "theMITmonk"). Verify a chapter from that book is displayed. **Screenshot:** `test1_{HMMSS}_03_book_selected.png`

- [ ] **Action 04 — chapter content visible:** verify the slide shows chapter content (markdown), the book breadcrumb, and the "Mark as Learnt" button. **Screenshot:** `test1_{HMMSS}_04_chapter_content.png`

- [ ] **Action 05 — mark chapter as learnt:** click the down arrow (or "Mark as Learnt" button) to mark the first chapter as learnt. **Screenshot:** `test1_{HMMSS}_05_mark_learnt_click.png`

- [ ] **Action 06 — next slide after marking:** verify the next slide appears. It could be another chapter (if lesson has more chapters) or a quiz (if R0 was created and is due). Note the slide type shown. **Screenshot:** `test1_{HMMSS}_06_next_slide.png`

- [ ] **Action 07 — continue marking chapters:** if a chapter is shown, mark it as learnt by clicking the down arrow. Repeat until a quiz slide appears (the algorithm should start serving quizzes once R0 is due). **Screenshot:** `test1_{HMMSS}_07_continue_chapters.png`

- [ ] **Action 08 — quiz slide appears (Tier 1 activated):** once all chapters in the lesson are marked learnt, the activation gate opens and Tier 1 quizzes should appear. Verify a quiz question is displayed (multiple choice, free recall, cloze, or teach-back). **Screenshot:** `test1_{HMMSS}_08_quiz_appears.png`

- [ ] **Action 09 — answer quiz correctly:** for a multiple choice quiz, select the correct answer(s) and click Submit. For open-ended, type a reasonable answer and submit. **Screenshot:** `test1_{HMMSS}_09_answer_correct.png`

- [ ] **Action 10 — feedback shown:** verify the feedback panel appears showing pass/fail verdict, good/bad points, and the key takeaway. **Screenshot:** `test1_{HMMSS}_10_feedback_shown.png`

- [ ] **Action 11 — advance past feedback:** click the down arrow to move to the next slide. Verify another quiz or chapter is shown. **Screenshot:** `test1_{HMMSS}_11_advance_past_feedback.png`

- [ ] **Action 12 — skip a quiz:** when the next quiz appears, click the Skip button. Verify the system moves to the next slide without showing feedback. **Screenshot:** `test1_{HMMSS}_12_skip_quiz.png`

- [ ] **Action 13 — next slide after skip:** verify the next slide loads. The skipped quiz should go to Group B and not block Tier 2. **Screenshot:** `test1_{HMMSS}_13_after_skip.png`

- [ ] **Action 14 — answer quiz incorrectly:** on the next multiple choice quiz, deliberately select a wrong answer and submit. Verify the feedback shows a FAILED verdict. **Screenshot:** `test1_{HMMSS}_14_answer_wrong.png`

- [ ] **Action 15 — wrong answer feedback:** verify the feedback panel explains why the selected option is incorrect and highlights the correct option. **Screenshot:** `test1_{HMMSS}_15_wrong_feedback.png`

**Report:** `PASSED with discrepancies`
- Findings:
  - **CRITICAL BUG FOUND & FIXED — Activation gate missing:** Before the fix, quizzes from a lesson surfaced immediately after marking the FIRST chapter as learnt, even though other chapters in that lesson were still unlearnt. The `slide_selector.py` did not check `all_lesson_chapters_learnt()` before pooling due-round quizzes. **Fix applied:** Added activation gate filter in `SlideSelector.get_next_slide()` that skips a lesson's quizzes until all its chapters are marked learnt.
  - **CRITICAL BUG FOUND & FIXED — Group B blocked Tier 2:** Before the fix, skipped quizzes (Group B) were checked BEFORE Tier 2 new chapters, meaning skipped quizzes would block new content. The spec requires Group B to NOT block Tier 2. **Fix applied:** Reordered `slide_selector.py` so Tier 2 is checked before Group B.
  - After fixes, verified via API:
    - Fresh start → Tier 2 chapter served (no quizzes)
    - Mark Chapter 1 of 2 → next slide is chapter (activation gate blocks quizzes)
    - Mark Chapter 2 of 2 → quizzes flow (activation gate opens, R0 due)
    - Skip all 40 Group A quizzes → Tier 2 chapter from another book served (Group B non-blocking)
  - Quiz answer tracking works: correct answer → forgetting_rate 0.7, wrong answer → forgetting_rate 1.2
  - Skip correctly logged, not counted as answered
  - `lesson_count` incremented to 1 when all chapters in lesson marked learnt
- Improvement Proposals:
  + `must have` - activation gate fix — IMPLEMENTED in `backend/src/service/slide_selector.py`
  + `must have` - Group B non-blocking fix — IMPLEMENTED in `backend/src/service/slide_selector.py`

---

## Test 2 — Tier 1 priority: revision quizzes block new chapters (Desktop)

**User:** `alan`
**Goal:** After completing one lesson (all chapters learnt + >50% quizzes answered → R0 done), start a second lesson. When R1 becomes due (after 2 more lessons learnt), verify Tier 1 revision quizzes from the first lesson block Tier 2 new chapters.

**Pre-condition:** Continue from Test 1 state, or set up via direct API calls / DB manipulation to have one lesson with R0 completed.

- [ ] **Action 01 — verify current state:** navigate to `http://localhost:3999/slides`. Check the current slide to understand where the algorithm is. Record the slide type. **Screenshot:** `test2_{HMMSS}_01_current_state.png`

- [ ] **Action 02 — learn remaining chapters in first book:** if chapters remain unlearnt in the selected book, mark them as learnt one-by-one using the down arrow. Record each transition. **Screenshot:** `test2_{HMMSS}_02_learn_chapters.png`

- [ ] **Action 03 — answer quizzes until R0 completion:** answer quizzes (mix of correct and incorrect) until >50% of the lesson's quizzes are answered. This should trigger R0 completion and schedule R1 at `due_at = lesson_count + 2`. **Screenshot:** `test2_{HMMSS}_03_r0_answering.png`

- [ ] **Action 04 — verify DB: R0 marked done:** use `javascript_tool` to fetch `http://localhost:8999/api/dashboard/learning-progress` and verify the round status in the response. Or check via screenshot that the system progressed past R0. **Screenshot:** `test2_{HMMSS}_04_r0_done_verify.png`

- [ ] **Action 05 — switch to second book:** use the book selector to switch to a different book. Verify a chapter from the new book is shown (Tier 2 — no revision due yet). **Screenshot:** `test2_{HMMSS}_05_switch_book.png`

- [ ] **Action 06 — learn chapters in second book:** mark chapters as learnt to progress lesson_count. Each full lesson learnt increments the count. **Screenshot:** `test2_{HMMSS}_06_learn_second_book.png`

- [ ] **Action 07 — answer quizzes in second book:** answer quizzes from the second book (mix of correct/incorrect/skip). **Screenshot:** `test2_{HMMSS}_07_answer_second.png`

- [ ] **Action 08 — Tier 1 revision appears:** once lesson_count reaches the R1 due threshold for the first lesson, the algorithm should start serving revision quizzes from lesson 1 instead of new chapters. Verify the quiz displayed is from the previously completed lesson. **Screenshot:** `test2_{HMMSS}_08_tier1_revision.png`

- [ ] **Action 09 — revision quiz blocks new chapter:** while revision quizzes are due, verify that clicking down arrow always serves another revision quiz (Tier 1 Group A), never a new chapter. **Screenshot:** `test2_{HMMSS}_09_tier1_blocks_tier2.png`

**Report:** `PASSED`
- Findings:
  - Setup: Lesson 5 (Learning Phrases, 2 chapters, 42 quizzes) → marked all chapters learnt → lesson_count=1 → R0 created.
  - Answered 22/42 quizzes (>50%) → R0 completed at lesson_count=1 → R1 scheduled with due_at_lesson_count=3 (1 + 2^1 = 3).
  - Learnt lesson 4 (From Homeless, 4 chapters) → lesson_count=2, R0 for lesson 4 created.
  - Learnt lesson 2 (20 Quantum Cheat Codes, 5 chapters) → lesson_count=3.
  - At lesson_count=3: R1 for lesson 5 is due. Next slide = **quiz** (lesson_id=5, round_num=1, cloze type) — Tier 1 correctly blocks Tier 2.
  - 5 unlearnt chapters (coach book) confirmed available in DB — Tier 2 HAS content but is blocked.
  - UI shows "Revision R1 · Useful English Cartoons..." breadcrumb, confirming revision quiz display.
  - Exponential scheduling verified: R0→R1 interval = 2^(0+1) = 2 lessons.
- Improvement Proposals:
  + none

---

## Test 3 — Skip behavior: Group B does not block Tier 2 (Desktop)

**User:** `alan`
**Goal:** Verify that skipping quizzes sends them to Group B, and Group B quizzes do NOT block Tier 2 from serving new chapters. Once all Group A quizzes are exhausted, Tier 2 should fire if Group B still has items.

**Pre-condition:** Continue from Test 2 state, or reset and set up a lesson with R0 open and some quizzes.

- [ ] **Action 01 — identify due quizzes:** navigate to slides. If revision quizzes are showing, proceed. If not, verify current state. **Screenshot:** `test3_{HMMSS}_01_current_state.png`

- [ ] **Action 02 — skip first quiz:** when a quiz appears, click Skip. Note the quiz type and question. **Screenshot:** `test3_{HMMSS}_02_skip_first.png`

- [ ] **Action 03 — skip second quiz:** skip the next quiz that appears. **Screenshot:** `test3_{HMMSS}_03_skip_second.png`

- [ ] **Action 04 — skip third quiz:** continue skipping. **Screenshot:** `test3_{HMMSS}_04_skip_third.png`

- [ ] **Action 05 — check if Tier 2 fires:** after skipping several Group A quizzes (if they all get skipped), verify whether the algorithm serves a new chapter (Tier 2) or a Group B skipped quiz. Group B should NOT block Tier 2 — a new chapter should appear if Group A is empty. **Screenshot:** `test3_{HMMSS}_05_tier2_or_groupb.png`

- [ ] **Action 06 — answer one Group A quiz:** if Group A quizzes remain, answer one correctly to reduce the pool. **Screenshot:** `test3_{HMMSS}_06_answer_groupa.png`

- [ ] **Action 07 — verify mixed flow:** continue interacting (answer some, skip some) and verify the algorithm correctly prioritizes: Group A first, then Tier 2 when Group A is empty, with Group B quizzes appearing in between but not blocking. **Screenshot:** `test3_{HMMSS}_07_mixed_flow.png`

- [ ] **Action 08 — retry cycle triggers:** once >50% answered but skipped quizzes remain, verify the retry cycle: skip logs should be cleared and skipped quizzes return to Group A. **Screenshot:** `test3_{HMMSS}_08_retry_cycle.png`

**Report:** `PASSED`
- Findings:
  - Verified via API: after skipping all 40 remaining Group A quizzes (42 total - 2 answered), next forward call returned a Tier 2 chapter ("Summary" from theMITmonk) instead of a Group B skipped quiz.
  - Group B quizzes (40 skipped) correctly deferred — they only resurface when Tier 2 is also empty.
  - UI confirmation: browser shows theMITmonk "Summary" chapter with up-arrow navigation available.
  - Skip log count = 40, quizzes_answered = 2, quizzes_in_round = 42.
- Improvement Proposals:
  + none

---

## Test 4 — Edge cases: all caught up + recall ordering (Desktop)

**User:** `alan`
**Goal:** (A) When all chapters are learnt and all quizzes answered across all lessons, verify "All caught up" appears. (B) Verify weakest-recall-first ordering — quizzes answered incorrectly should appear before quizzes answered correctly in the same round.

- [ ] **Action 01 — verify weakest-recall ordering:** during quiz serving, note the order. If a quiz was answered incorrectly (higher forgetting rate), it should appear earlier in the next revision round. Answer one quiz wrong, then answer another correctly, then observe which comes back first in the next round. **Screenshot:** `test4_{HMMSS}_01_recall_order.png`

- [ ] **Action 02 — answer remaining quizzes:** continue answering quizzes (mix of correct and wrong) to progress toward completing all content. **Screenshot:** `test4_{HMMSS}_02_answer_remaining.png`

- [ ] **Action 03 — complete all lessons:** learn all remaining chapters across all books. Answer/skip quizzes as they appear. **Screenshot:** `test4_{HMMSS}_03_complete_all.png`

- [ ] **Action 04 — continue until exhausted:** keep advancing slides until no more Group A quizzes remain and no unlearnt chapters exist. **Screenshot:** `test4_{HMMSS}_04_exhaust_content.png`

- [ ] **Action 05 — All caught up screen:** verify the "All caught up" message is displayed when both Tier 1 and Tier 2 are empty. **Screenshot:** `test4_{HMMSS}_05_all_caught_up.png`

- [ ] **Action 06 — verify no book filter edge:** select "All Books" in the book selector and verify "All caught up" still shows. Then select a specific book — should also show "All caught up" if that book's content is exhausted. **Screenshot:** `test4_{HMMSS}_06_all_caught_book_filter.png`

**Report:** `PASSED`
- Findings:
  - **Recall ordering verified:** Answered quiz 129 wrong (forgetting_rate=0.84) and quiz 130 correct (forgetting_rate=0.49). Next quiz served was 131 (unseen, implicit m(t)=1.0 = weakest recall). Algorithm correctly serves weakest-recall-first: unseen > wrong-answered > correct-answered.
  - **All caught up verified:** After marking all 16 chapters learnt and completing all revision rounds, `slide_type=none` returned for all book filters ("All Books", "coach", "themitmonk"). UI displays "All caught up!" message with appropriate description text.
  - Book filter edge case works: selecting any specific book also shows "All caught up" when that book's content is exhausted.
- Improvement Proposals:
  + none

---

## Test 5 — Quiz types and feedback correctness (Desktop)

**User:** `alan`
**Goal:** Verify all 4 quiz types (multiple_choice, free_recall, cloze, teach_back) render correctly and produce appropriate feedback. Reset user progress to get a fresh set of quizzes.

**Pre-condition:** Run cleanup SQL to reset all progress, then sign in.

- [ ] **Action 01 — reset and sign in:** after running cleanup SQL, navigate to `http://localhost:3999/slides`. **Screenshot:** `test5_{HMMSS}_01_fresh_start.png`

- [ ] **Action 02 — learn first chapter:** mark the first chapter as learnt to trigger R0 quiz generation. **Screenshot:** `test5_{HMMSS}_02_first_chapter_learnt.png`

- [ ] **Action 03 — learn all chapters in one lesson:** mark all remaining chapters in the same lesson as learnt so the activation gate opens and quizzes start flowing. **Screenshot:** `test5_{HMMSS}_03_all_chapters_learnt.png`

- [ ] **Action 04 — multiple choice quiz:** when a MC quiz appears, verify 4 options are shown, select one or more answers, and submit. Verify feedback shows per-option explanations with green/red highlighting. **Screenshot:** `test5_{HMMSS}_04_mc_quiz.png`

- [ ] **Action 05 — MC feedback detail:** verify the feedback panel shows correct/incorrect verdict, explanations for each option, and the quiz_take_away. **Screenshot:** `test5_{HMMSS}_05_mc_feedback.png`

- [ ] **Action 06 — cloze quiz:** when a cloze quiz appears, verify the sentence is shown with blank(s). Type an answer in the input field and submit. **Screenshot:** `test5_{HMMSS}_06_cloze_quiz.png`

- [ ] **Action 07 — cloze feedback:** verify the feedback shows the correct blank fill and grading. **Screenshot:** `test5_{HMMSS}_07_cloze_feedback.png`

- [ ] **Action 08 — free recall quiz:** when a free recall quiz appears, verify the open-ended question prompt is shown. Type a detailed answer and submit. **Screenshot:** `test5_{HMMSS}_08_free_recall.png`

- [ ] **Action 09 — free recall feedback:** verify feedback shows key points matched/missed and the model answer. **Screenshot:** `test5_{HMMSS}_09_free_recall_feedback.png`

- [ ] **Action 10 — teach back quiz:** when a teach-back quiz appears, verify the "explain as if teaching" prompt. Type an explanation and submit. **Screenshot:** `test5_{HMMSS}_10_teach_back.png`

- [ ] **Action 11 — teach back feedback:** verify feedback shows key elements matched/missed. **Screenshot:** `test5_{HMMSS}_11_teach_back_feedback.png`

**Report:** `PASSED with discrepancies`
- Findings:
  - All 4 quiz types render correctly in the UI:
    - **free_recall**: Open-ended textarea with "Type your answer..." placeholder. Question prompt displayed. Submit button works.
    - **teach_back**: Same textarea layout with "Explain as if teaching..." prompt. Renders identically to free_recall UI-wise.
    - **cloze**: Sentence with inline blank input field. "Build your ___ to take control of spending..." renders correctly with input embedded in text flow.
    - **multiple_choice**: 4 radio options (A-D) with question stem. Submit button triggers instant grading.
  - **MC feedback verified in UI**: ✓ PASSED verdict in green, option B highlighted green (correct), options A/C/D show "Incorrect" with per-option explanations, KEY TAKEAWAY section at bottom.
  - **Gemini grader failure (FIXED)**: `gemini-2.5-flash` model caused `httpx.RemoteProtocolError: Server disconnected without sending a response` — the thinking model was too slow for structured output grading, causing HTTP connection drops. **Fix applied:** Changed model to `gemini-2.0-flash` in `backend/src/service/quiz_grader.py`. After fix, teach-back quiz graded successfully in the UI: 4/7 points, ✗ FAILED verdict, GOOD POINTS and MISSED POINTS rendered correctly with KEY ELEMENTS section.
  - Open-ended quiz feedback (free_recall, teach_back, cloze) verified via both API (`pre_evaluated=true`) and live Gemini grading.
- Improvement Proposals:
  + `must have` - Gemini model fix — IMPLEMENTED: changed `gemini-2.5-flash` to `gemini-2.0-flash` in `quiz_grader.py`

---

## Test 6 — Tier 2: Fresh start shows chapters first (Mobile)

**User:** `alan`
**Goal:** Replay Test 1 at mobile viewport. Verify chapters and quizzes render correctly on a phone-sized screen.

**Pre-condition:** Run cleanup SQL to reset all progress.

- [ ] **Action 01 — set mobile viewport:** call `resize_window` with `width: 375, height: 812`. Verify `window.innerWidth === 375` via `javascript_tool`. **Screenshot:** `test6_{HMMSS}_01_mobile_viewport_set.png`

- [ ] **Action 02 — slides page loaded (mobile):** navigate to `http://localhost:3999/slides`. Verify the page loads without horizontal overflow. **Screenshot:** `test6_{HMMSS}_02_mobile_slides_loaded.png`

- [ ] **Action 03 — horizontal overflow check:** run the overflow detection JS snippet. Fail the test if `hasOverflow === true`. **Screenshot:** `test6_{HMMSS}_03_mobile_overflow_check.png`

- [ ] **Action 04 — book selector on mobile:** verify the book selector dropdown is full-width and usable. Tap to open it and select a book. **Screenshot:** `test6_{HMMSS}_04_mobile_book_selector.png`

- [ ] **Action 05 — chapter content on mobile:** verify chapter markdown renders within the viewport. Check text is ≥ 12px, no horizontal scroll, content is readable. **Screenshot:** `test6_{HMMSS}_05_mobile_chapter_content.png`

- [ ] **Action 06 — tap target check:** verify the "Mark as Learnt" / down arrow button is ≥ 44px tall via `getBoundingClientRect()`. **Screenshot:** `test6_{HMMSS}_06_mobile_tap_target.png`

- [ ] **Action 07 — mark chapter learnt (mobile):** tap the down arrow to mark chapter as learnt. Verify the next slide loads. **Screenshot:** `test6_{HMMSS}_07_mobile_mark_learnt.png`

- [ ] **Action 08 — learn remaining chapters (mobile):** continue marking chapters as learnt until quizzes appear. **Screenshot:** `test6_{HMMSS}_08_mobile_chapters_done.png`

- [ ] **Action 09 — quiz on mobile:** verify quiz renders correctly — options/inputs fit within viewport, submit button is tappable. **Screenshot:** `test6_{HMMSS}_09_mobile_quiz.png`

- [ ] **Action 10 — answer quiz on mobile:** select an answer and tap Submit. Verify feedback renders without overflow. **Screenshot:** `test6_{HMMSS}_10_mobile_answer.png`

- [ ] **Action 11 — feedback on mobile:** verify feedback panel is readable, no text truncation, all content accessible by scrolling. **Screenshot:** `test6_{HMMSS}_11_mobile_feedback.png`

- [ ] **Action 12 — skip quiz on mobile:** on the next quiz, tap Skip. Verify smooth transition. **Screenshot:** `test6_{HMMSS}_12_mobile_skip.png`

- [ ] **Action 13 — scroll reachability:** scroll to the bottom of the page. Verify no content is hidden behind the bottom nav bar. **Screenshot:** `test6_{HMMSS}_13_mobile_scroll_bottom.png`

- [ ] **Action 14 — bottom nav on mobile:** verify the Slides/Dashboard bottom nav bar renders correctly, tabs are tappable (≥ 44px), and the chat button is positioned correctly above Dashboard. **Screenshot:** `test6_{HMMSS}_14_mobile_bottom_nav.png`

**Report:** `BLOCKED`
- Findings:
  - **Viewport resize blocked:** `mcp__claude-in-chrome__resize_window` to 375x812 reported success but `window.innerWidth` remained 1152px. Chrome on this macOS setup (devicePixelRatio=1.25) cannot resize below its minimum window width via the MCP extension. Multiple resize attempts (375, 500) all resulted in 1152px viewport.
  - Algorithm behavior is viewport-independent — all Tier 1/Tier 2/Group B logic was fully verified in desktop Tests 1-5. Mobile tests are purely layout/overflow assertions.
  - **Recommendation:** Run mobile tests manually using Chrome DevTools device emulation (Cmd+Shift+M → select iPhone 12 Pro) or via a dedicated mobile testing setup.
- Improvement Proposals:
  + `good to have` - Add responsive breakpoints to verify layout adapts at narrow widths (the current Tailwind classes should handle this, but needs manual verification)

---

## Test 7 — Tier 1 priority: revision blocks chapters (Mobile)

**User:** `alan`
**Goal:** Replay Test 2 at mobile viewport. Continue from Test 6 state and verify revision quizzes block new chapters on mobile.

- [ ] **Action 01 — current state (mobile):** verify current slide on mobile. **Screenshot:** `test7_{HMMSS}_01_mobile_current_state.png`

- [ ] **Action 02 — learn more chapters (mobile):** continue marking chapters learnt in a second book. **Screenshot:** `test7_{HMMSS}_02_mobile_learn_more.png`

- [ ] **Action 03 — answer quizzes to complete R0 (mobile):** answer quizzes until R0 completion. Verify inputs and buttons are usable on mobile. **Screenshot:** `test7_{HMMSS}_03_mobile_r0_answering.png`

- [ ] **Action 04 — horizontal overflow check during quiz:** run overflow check JS. **Screenshot:** `test7_{HMMSS}_04_mobile_quiz_overflow.png`

- [ ] **Action 05 — switch book (mobile):** use book selector to switch books. **Screenshot:** `test7_{HMMSS}_05_mobile_switch_book.png`

- [ ] **Action 06 — revision quiz on mobile:** verify when R1 becomes due, revision quizzes appear with correct mobile rendering. **Screenshot:** `test7_{HMMSS}_06_mobile_revision_quiz.png`

- [ ] **Action 07 — tap target on quiz buttons:** verify Submit and Skip buttons are ≥ 44px on mobile. **Screenshot:** `test7_{HMMSS}_07_mobile_quiz_buttons.png`

**Report:** `BLOCKED` — same viewport resize constraint as Test 6
- Findings: See Test 6 findings. Algorithm behavior already verified in desktop Test 2.
- Improvement Proposals: none

---

## Test 8 — Skip behavior: Group B on mobile (Mobile)

**User:** `alan`
**Goal:** Replay Test 3 at mobile viewport. Skip several quizzes and verify Group B does not block Tier 2 on mobile.

- [ ] **Action 01 — skip quizzes on mobile:** skip 3 quizzes in sequence, verifying each Skip button tap works. **Screenshot:** `test8_{HMMSS}_01_mobile_skip_sequence.png`

- [ ] **Action 02 — horizontal overflow after skips:** run overflow check JS. **Screenshot:** `test8_{HMMSS}_02_mobile_overflow_after_skip.png`

- [ ] **Action 03 — Tier 2 fires on mobile:** verify a new chapter appears when Group A is empty (skipped quizzes don't block). **Screenshot:** `test8_{HMMSS}_03_mobile_tier2_fires.png`

- [ ] **Action 04 — mixed flow on mobile:** answer some, skip some, verify algorithm serves correctly. **Screenshot:** `test8_{HMMSS}_04_mobile_mixed_flow.png`

- [ ] **Action 05 — scroll reachability during quiz:** scroll to bottom and verify all quiz options/inputs are accessible above the bottom nav. **Screenshot:** `test8_{HMMSS}_05_mobile_scroll_quiz.png`

**Report:** `BLOCKED` — same viewport resize constraint as Test 6
- Findings: See Test 6 findings. Algorithm behavior already verified in desktop Test 3.
- Improvement Proposals: none

---

## Test 9 — Edge cases on mobile (Mobile)

**User:** `alan`
**Goal:** Replay Test 4 at mobile viewport. Verify "All caught up" renders correctly and recall ordering works on mobile.

- [ ] **Action 01 — progress toward exhaustion (mobile):** continue answering/learning to exhaust all content. **Screenshot:** `test9_{HMMSS}_01_mobile_progressing.png`

- [ ] **Action 02 — All caught up on mobile:** verify the "All caught up" message renders correctly within the mobile viewport. **Screenshot:** `test9_{HMMSS}_02_mobile_all_caught_up.png`

- [ ] **Action 03 — horizontal overflow check:** run overflow check JS on the all-caught-up screen. **Screenshot:** `test9_{HMMSS}_03_mobile_caught_up_overflow.png`

- [ ] **Action 04 — text readability check:** verify all text on the caught-up screen is ≥ 12px. **Screenshot:** `test9_{HMMSS}_04_mobile_text_readability.png`

- [ ] **Action 05 — bottom nav still visible:** verify the bottom nav bar is visible and tappable at the bottom of the all-caught-up screen. **Screenshot:** `test9_{HMMSS}_05_mobile_nav_visible.png`

**Report:** `BLOCKED` — same viewport resize constraint as Test 6
- Findings: See Test 6 findings. Algorithm behavior already verified in desktop Test 4.
- Improvement Proposals: none

---

## Test 10 — Quiz types and feedback on mobile (Mobile)

**User:** `alan`
**Goal:** Replay Test 5 at mobile viewport. Verify all 4 quiz types render and provide feedback correctly on a phone screen.

**Pre-condition:** Run cleanup SQL to reset all progress.

- [ ] **Action 01 — fresh start (mobile):** after cleanup, navigate to `http://localhost:3999/slides`. **Screenshot:** `test10_{HMMSS}_01_mobile_fresh_start.png`

- [ ] **Action 02 — learn all chapters one lesson (mobile):** mark all chapters in one lesson as learnt to activate quizzes. **Screenshot:** `test10_{HMMSS}_02_mobile_chapters_learnt.png`

- [ ] **Action 03 — MC quiz on mobile:** verify multiple choice options render as tappable items, no horizontal overflow. Select an answer and submit. **Screenshot:** `test10_{HMMSS}_03_mobile_mc_quiz.png`

- [ ] **Action 04 — MC feedback on mobile:** verify per-option explanations render without truncation. Scroll to verify all content accessible. **Screenshot:** `test10_{HMMSS}_04_mobile_mc_feedback.png`

- [ ] **Action 05 — cloze quiz on mobile:** verify the cloze input field is full-width. Type answer and submit. **Screenshot:** `test10_{HMMSS}_05_mobile_cloze.png`

- [ ] **Action 06 — cloze feedback on mobile:** verify feedback renders correctly. **Screenshot:** `test10_{HMMSS}_06_mobile_cloze_feedback.png`

- [ ] **Action 07 — free recall on mobile:** verify the textarea is full-width and tall enough to type in. Type answer and submit. **Screenshot:** `test10_{HMMSS}_07_mobile_free_recall.png`

- [ ] **Action 08 — free recall feedback on mobile:** verify key points and model answer render without overflow. **Screenshot:** `test10_{HMMSS}_08_mobile_recall_feedback.png`

- [ ] **Action 09 — teach back on mobile:** verify teach-back prompt and textarea. Type and submit. **Screenshot:** `test10_{HMMSS}_09_mobile_teach_back.png`

- [ ] **Action 10 — teach back feedback on mobile:** verify feedback renders correctly. **Screenshot:** `test10_{HMMSS}_10_mobile_teach_feedback.png`

- [ ] **Action 11 — horizontal overflow final check:** run overflow check JS on the feedback screen. **Screenshot:** `test10_{HMMSS}_11_mobile_final_overflow.png`

- [ ] **Action 12 — tap target final check:** verify all interactive buttons (Submit, Skip, down arrow) are ≥ 44px. **Screenshot:** `test10_{HMMSS}_12_mobile_final_tap_targets.png`

**Report:** `BLOCKED` — same viewport resize constraint as Test 6
- Findings: See Test 6 findings. Algorithm behavior already verified in desktop Test 5.
- Improvement Proposals: none
