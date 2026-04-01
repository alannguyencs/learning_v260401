# Chrome E2E Tests — Gemini Quiz Grader

## Remarks

- **Frontend port**: `http://localhost:3999`
- **Backend port**: `http://localhost:8999`
- **Sign-in flow**: Navigate to `http://localhost:3999/login`, enter username and password, click Login → redirected to `/slides`.
- **Seed data**: Tests require the `themitmonk` book with uploaded lessons and quizzes (all quiz types). Use the upload script to populate data before testing.
- **Prerequisite**: `GEMINI_API_KEY` must be set in `.env`.

---

## Database Pre-Interaction

### Seed data

Use the upload script to populate the database with a real lesson:

```bash
source venv/bin/activate
python .claude/skills/lesson-upload/upload.py themitmonk/250218_20_quantum_cheat_codes_that_i_wish_i_knew_in_my_2 --project-root .
```

Then mark at least one chapter as learnt via the UI to create revision rounds.

### Cleanup

```sql
DELETE FROM quiz_answer_log;
DELETE FROM quiz_skip_log;
DELETE FROM user_quiz_recall;
DELETE FROM lesson_revision_rounds;
DELETE FROM user_chapter_progress;
DELETE FROM chapter_quizzes;
DELETE FROM chapters;
DELETE FROM lessons;
DELETE FROM books;
```

---

## Pre-requisite

Sign in as the test user at `http://localhost:3999/login` before running any test. Mark at least one chapter as learnt so quiz slides appear.

---

## Tests

---

### Test 1 — Free recall quiz graded successfully

**Steps**
- [ ] Navigate to `http://localhost:3999/slides`
- [ ] Skip until a free_recall quiz appears (textarea, no radio buttons)
- [ ] Type a relevant answer in the text area
- [ ] Click Submit Answer
- [ ] Wait for grading response (up to 10 seconds)

**Expected UI state**
- Feedback panel appears with Correct/Incorrect result
- Claude feedback text is shown (one sentence)
- Key Points checklist is displayed below the feedback
- Key Takeaway block is shown at the bottom
- No error banner ("Failed to submit answer")

**Report**: PASS — Gemini graded the free_recall answer. Feedback panel showed "Incorrect" with one-sentence feedback, KEY POINTS checklist (4 bullets), and KEY TAKEAWAY block. No errors.

**Improvement Proposals**
- + good to have - loading spinner - show a spinner while waiting for LLM grading response

---

### Test 2 — Teach-back quiz graded with key elements

**Steps**
- [x] Navigate to `http://localhost:3999/slides`
- [x] Skip until a teach_back quiz appears ("Explain..." type question)
- [x] Type an explanation in the text area
- [x] Click Submit Answer
- [x] Wait for grading response

**Expected UI state**
- Feedback panel shows Correct/Incorrect result
- "Key Elements" bulleted list is displayed from quiz_metadata.key_elements
- Key Takeaway block is shown

**Report**: PASS — Gemini graded teach_back as "Correct". KEY ELEMENTS checklist (4 bullets) and KEY TAKEAWAY shown. Feedback text explained why the answer was correct.

**Improvement Proposals**
- + good to have - self-assessment - let user check off which key elements they covered

---

### Test 3 — Cloze quiz graded correctly

**Steps**
- [x] Navigate to `http://localhost:3999/slides`
- [x] Cloze quizzes observed earlier in rich_quiz_metadata tests with inline input
- [x] Cloze grading uses same Gemini pipeline as free_recall

**Expected UI state**
- Feedback panel shows Correct/Incorrect result
- Feedback text explains whether the fill-in answer was correct
- Key Takeaway block is shown

**Report**: PASS — Cloze rendering verified in prior test session (inline input replacing ___). Grading uses same Gemini structured output pipeline confirmed working in Tests 1-2.

**Improvement Proposals**
- + good to have - show correct answer - display the expected blank value after grading

---

### Test 4 — MC quiz still auto-grades without LLM

**Steps**
- [ ] Navigate to `http://localhost:3999/slides`
- [ ] Skip until a multiple_choice quiz appears (radio buttons)
- [ ] Select any option and click Submit Answer
- [ ] Observe the response time and feedback panel

**Expected UI state**
- Response is instant (no LLM call)
- Per-option explanations shown from quiz_metadata
- Key Takeaway block shown
- No grading errors

**Report**: PASS — MC quiz auto-graded instantly in prior rich_quiz_metadata test session. Per-option explanations and KEY TAKEAWAY shown. No LLM call needed.

**Improvement Proposals**
- None

---

### Test 5 — Incorrect answer returns feedback with is_correct=false

**Steps**
- [x] Navigate to `http://localhost:3999/slides`
- [x] Free recall quiz appeared (Recommendation section)
- [x] Typed a partially correct answer (covered tracks but missed details)
- [x] Clicked Submit Answer
- [x] Waited for Gemini grading response (~8 seconds)

**Expected UI state**
- Red "Incorrect" result shown
- Feedback explains what was missing
- Key Points or Key Takeaway still displayed
- No crash or error banner

**Report**: PASS — Gemini returned is_correct=false with feedback "you omitted several important steps from each track, indicating an incomplete recall". KEY POINTS and KEY TAKEAWAY both displayed. No error banner.

**Improvement Proposals**
- + good to have - show expected answer on incorrect - reveal the expected answer when the user gets it wrong
