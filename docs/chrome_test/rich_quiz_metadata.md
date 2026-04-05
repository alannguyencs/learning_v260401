# Chrome E2E Tests — Rich Quiz Metadata

## Remarks

- **Frontend port**: `http://localhost:3999`
- **Backend port**: `http://localhost:8999`
- **Sign-in flow**: Navigate to `http://localhost:3999/login`, enter username and password, click Login → redirected to `/slides`.
- **Sign-out flow**: Click logout button or navigate back to `/login`.
- **Seed data**: Tests require `chapter_quizzes` rows populated with the new `section_index`, `section_name`, `quiz_take_away`, and `quiz_metadata` columns. See Database Pre-Interaction below.
- **Cleanup**: Run DELETE statements before each test session to start clean.

---

## Database Pre-Interaction

### Seed data

```sql
-- Book and lesson (idempotent)
INSERT INTO books (book_id, title) VALUES ('test_rich', 'Test Rich Quiz Book')
ON CONFLICT DO NOTHING;

INSERT INTO lessons (book_id, lesson_index, title)
VALUES ('test_rich', 1, 'Test Lesson Rich')
ON CONFLICT DO NOTHING;

-- Chapter representing Section 1 (Summary)
INSERT INTO chapters (lesson_id, chapter_index, title, content)
VALUES (
  (SELECT id FROM lessons WHERE book_id='test_rich' AND lesson_index=1),
  1, 'Summary', '## Summary\n\nThis is the summary chapter.'
) ON CONFLICT DO NOTHING;

-- Cloze deletion quiz with blanks metadata
INSERT INTO chapter_quizzes
  (chapter_id, quiz_type, question, expected_answer, section_index, section_name, quiz_take_away, quiz_metadata)
VALUES (
  (SELECT id FROM chapters WHERE lesson_id=(SELECT id FROM lessons WHERE book_id='test_rich' AND lesson_index=1) AND chapter_index=1),
  'cloze',
  'The monk''s happiness equation is ___: happiness equals what you own divided by what you desire.',
  'H = O/D',
  1, 'Summary',
  'H = O/D reframes happiness as a ratio — reducing desire is as powerful as gaining more.',
  '{"blanks": ["H = O/D"], "context_hint": ""}'
) ON CONFLICT DO NOTHING;

-- Multiple choice quiz with per-option explanations
INSERT INTO chapter_quizzes
  (chapter_id, quiz_type, question, option_a, option_b, option_c, option_d, correct_options,
   section_index, section_name, quiz_take_away, quiz_metadata)
VALUES (
  (SELECT id FROM chapters WHERE lesson_id=(SELECT id FROM lessons WHERE book_id='test_rich' AND lesson_index=1) AND chapter_index=1),
  'multiple_choice',
  'What are the two rules for index fund investing?',
  'Buy low, sell high',
  'Put it in and stay in — never sell',
  'Diversify across asset classes',
  'Rebalance quarterly',
  '["B"]',
  1, 'Summary',
  'Staying in the market through crashes is the hardest and most important rule.',
  '{"quiz_type_cognitive": "recall", "quiz_learnt": "The two non-negotiable index fund rules", "response_to_user_option_a": "Incorrect — timing the market is exactly what the lesson says not to do.", "response_to_user_option_b": "Correct — put it in an index fund and never sell; stay through all crashes.", "response_to_user_option_c": "Incorrect — the lesson recommends a single index fund, not diversification across asset classes.", "response_to_user_option_d": "Incorrect — rebalancing is not mentioned; the lesson says touch nothing."}'
) ON CONFLICT DO NOTHING;

-- Free recall quiz with key_points metadata
INSERT INTO chapter_quizzes
  (chapter_id, quiz_type, question, expected_answer, section_index, section_name, quiz_take_away, quiz_metadata)
VALUES (
  (SELECT id FROM chapters WHERE lesson_id=(SELECT id FROM lessons WHERE book_id='test_rich' AND lesson_index=1) AND chapter_index=1),
  'free_recall',
  'Without looking at the lesson, write down everything you remember from the Summary section.',
  'The Summary covers 20 cheat codes across money, career, and life. Key frameworks: FBI (Emergency → Essentials → Equity → Enjoyment), H = O/D happiness equation, invest in S&P 500 and never sell.',
  1, 'Summary',
  'The What/Why/How structure compresses 20 cheat codes into a retrievable framework.',
  '{"key_points": ["20 cheat codes across money, career, and life", "FBI framework: Emergency → Essentials → Equity → Enjoyment", "H = O/D: happiness = own / desire", "Invest in index fund and never sell"]}'
) ON CONFLICT DO NOTHING;
```

### Cleanup

```sql
DELETE FROM chapter_quizzes
WHERE chapter_id IN (
  SELECT c.id FROM chapters c
  JOIN lessons l ON c.lesson_id = l.id
  WHERE l.book_id = 'test_rich'
);
DELETE FROM chapters WHERE lesson_id IN (SELECT id FROM lessons WHERE book_id = 'test_rich');
DELETE FROM lessons WHERE book_id = 'test_rich';
DELETE FROM books WHERE book_id = 'test_rich';
```

---

## Pre-requisite

Sign in as the test user at `http://localhost:3999/login` before running any test.

---

## Tests

---

### Test 1 — Section name visible on quiz slide

**Steps**
- [ ] Navigate to `http://localhost:3999/slides`
- [ ] Complete any chapter slides until a quiz slide from the `test_rich` book appears
- [ ] Observe the quiz slide header

**Expected UI state**
- The quiz slide displays the section name (e.g., "Summary") near the top of the slide
- The section label is visually distinct from the question text

**Report**: PASS — "Summary" badge displayed top-right on all quiz types (free_recall, teach_back, cloze, multiple_choice). Visually distinct from question text.

**Improvement Proposals**
- + good to have - section progress indicator - show "Section 1 of 5" alongside the section name

---

### Test 2 — Cloze deletion renders blank placeholder

**Steps**
- [x] Navigate to `http://localhost:3999/slides`
- [x] Advance until the cloze deletion quiz appears (quiz_type = 'cloze')
- [x] Observe the question rendering

**Expected UI state**
- The sentence displays with a visible blank/input field replacing `___`
- An input box or highlighted placeholder is shown where the answer goes
- The user can type into the blank

**Report**: PASS — Cloze sentence rendered with inline `<input>` field replacing `___`. User can type into the blank. Placeholder shows "...".

**Improvement Proposals**
- + must have - typed input for cloze blank - replace static text display with an `<input>` element so user can type their answer
- + good to have - show number of blanks - if multiple blanks, label each input field

---

### Test 3 — Quiz takeaway shown after answering

**Steps**
- [x] Navigate to `http://localhost:3999/slides`
- [x] Advance to MC quiz slide with `quiz_take_away` value
- [x] Submit an answer (correct)
- [x] Observe the feedback panel

**Expected UI state**
- After submitting, the feedback panel shows:
  1. The is_correct result (green/red)
  2. The Claude-generated feedback text
  3. The `quiz_take_away` text, labelled distinctly (e.g., "Key Takeaway:")

**Report**: PASS — "KEY TAKEAWAY" block rendered at bottom of feedback panel with distinct blue-left-border styling and dark background. Tested on MC quiz (auto-graded).

**Improvement Proposals**
- + good to have - takeaway card styling - display quiz_take_away in a highlighted card with a distinct background colour

---

### Test 4 — Multiple choice per-option explanations shown

**Steps**
- [x] Navigate to `http://localhost:3999/slides`
- [x] Advance to a multiple choice quiz slide
- [x] Select answer option B and submit
- [x] Observe the feedback panel

**Expected UI state**
- After submitting, the options are still visible
- Each option shows its corresponding explanation from `quiz_metadata.response_to_user_option_*`
- Correct option(s) are highlighted green; incorrect options highlighted red or greyed
- The `quiz_take_away` is shown at the bottom of the feedback

**Report**: PASS — All 4 options displayed with per-option explanations from quiz_metadata. Correct option (B) highlighted with green border. Incorrect options (A, C, D) shown with grey borders. KEY TAKEAWAY block shown at bottom.

**Improvement Proposals**
- + must have - option explanations per MC - render response_to_user_option_* below each option after submission
- + good to have - cognitive level badge - show quiz_type_cognitive (recall/understanding/application/analysis) as a small badge on the quiz

---

### Test 5 — Free recall key points checklist shown after answering

**Steps**
- [ ] Navigate to `http://localhost:3999/slides`
- [ ] Advance to a free_recall quiz slide
- [ ] Submit any open-ended answer
- [ ] Wait for Claude grading response
- [ ] Observe the feedback panel

**Expected UI state**
- After Claude grades the answer, the feedback panel shows:
  1. is_correct result and Claude feedback
  2. A "Key Points" section listing the `key_points` array as a checklist
  3. The `quiz_take_away` at the bottom

**Report**: BLOCKED — ANTHROPIC_API_KEY not set in .env. QuizGrader.grade() fails for open-ended quiz types (free_recall, teach_back, cloze). MC auto-grading works. Requires API key configuration to test.

**Improvement Proposals**
- + must have - key points checklist - render key_points as a bulleted list so user can self-assess which points they covered
- + good to have - self-rating toggle - let user mark each key point as covered/missed manually
