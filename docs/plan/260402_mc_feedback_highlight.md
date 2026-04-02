# MC Quiz Feedback — Show Only User Pick & Correct Option

**Feature**: After submitting an MC quiz, show only the user's selected option and the correct option (red for wrong pick, green for correct)
**Plan Created:** 2026-04-02
**Status:** Plan
**Reference**:
- [Abstract — Slide Stack](../abstract/slide_stack.md)
- [Technical — Slide Stack](../technical/slide_stack.md)

---

## Problem Statement

1. Currently, after submitting an MC quiz answer, **all 4 options** are displayed in the feedback panel — the correct option has a green border, the rest have gray borders.
2. The user cannot quickly see which option they picked. Their selection is not visually distinguished from the other wrong options.
3. Showing all 4 options with explanations creates visual clutter. The user only needs to see: what they chose and what the correct answer is.

---

## Proposed Solution

After submitting an MC quiz answer, show **only** the relevant options:
- **Wrong answer**: Show the user's pick (red border/text) and the correct option (green border/text). Hide other options.
- **Correct answer**: Show only the user's pick (green border/text). No other options needed.

Per-option explanations still render for the visible options.

This is a **frontend-only** change. The `answer` state already holds the user's selection in `QuizSlide` — it just needs to be passed through to `FeedbackPanel` → `McOptionExplanations`.

---

## Current Implementation Analysis

### What Exists (keep as-is)

| Component | File | Status |
|-----------|------|--------|
| Backend quiz respond API | `backend/src/api/slides.py` | Keep — no backend changes |
| QuizRespondResponse schema | `backend/src/schemas/slides.py` | Keep — no schema changes |
| useSlide hook | `frontend/src/hooks/useSlide.js` | Keep — unchanged |
| FeedbackPanel (structure) | `frontend/src/components/QuizSlide.jsx` | Keep — modify McOptionExplanations only |
| QuizSlide (answer state) | `frontend/src/components/QuizSlide.jsx` | Keep — pass answer to FeedbackPanel |

### What Changes

| Component | Current | Proposed |
|-----------|---------|----------|
| `McOptionExplanations` | Shows all 4 options; correct = green border, rest = gray | Filter to show only user's pick + correct option; user wrong pick = red, correct = green |
| `FeedbackPanel` | No `userAnswer` prop | Receives `userAnswer` prop to pass to `McOptionExplanations` |
| `QuizSlide` | `answer` state not passed to `FeedbackPanel` | Passes `answer` to `FeedbackPanel` as `userAnswer` |

---

## Implementation Plan

### Key Workflow

#### To Delete
None.

#### To Update

**After MC submission — feedback rendering flow:**

```
QuizSlide (answer = "A")
  │
  ▼
FeedbackPanel receives userAnswer="A"
  │
  ▼
McOptionExplanations receives userAnswer="A", correctOptions=["B"]
  │
  ▼
Filter: show only options where opt === userAnswer OR opt in correctOptions
  │
  ├── opt "A" (userAnswer, not correct) → red border + red text
  ├── opt "B" (correct) → green border + green text
  ├── opt "C" → hidden
  └── opt "D" → hidden
```

#### To Add New
None.

### Database Schema

#### To Delete
None.

#### To Update
None.

#### To Add New
None.

### CRUD

#### To Delete
None.

#### To Update
None.

#### To Add New
None.

### Services

#### To Delete
None.

#### To Update
None.

#### To Add New
None.

### API Endpoints

#### To Delete
None.

#### To Update
None.

#### To Add New
None.

### Testing

#### To Delete
None.

#### To Update

**`frontend/src/__tests__/components/QuizSlide.test.js`:**
- Update existing MC feedback tests to verify only user's pick + correct option render
- Add test: wrong answer → user pick shown red, correct shown green, others hidden
- Add test: correct answer → only user pick shown green

#### To Add New
None.

**Pre-commit loop:**
1. Run `source venv/bin/activate && pre-commit run --all-files`.
2. Fix any issues (e.g., lint errors, line count violations).
3. Re-run pre-commit again — Prettier may reformat the fixes and push files back over the line limit (max 300 lines per frontend file). If so, fix again (e.g., extract components to separate files to reduce line count durably).
4. Repeat until pre-commit passes cleanly on a full re-run with no new failures.

### Frontend

#### To Delete
None.

#### To Update

**`frontend/src/components/QuizSlide.jsx`:**

1. **`McOptionExplanations`** — add `userAnswer` prop, filter and restyle:
   - Add `userAnswer` to destructured props
   - Filter: `MC_OPTIONS.filter((opt) => optionMap[opt] && (opt === userAnswer || correct.includes(opt)))`
   - Style logic per option:
     - `opt === userAnswer && correct.includes(opt)` → green border + green text (user picked correctly)
     - `correct.includes(opt)` → green border + green text (correct answer)
     - `opt === userAnswer` → red border + red text (user's wrong pick)

2. **`FeedbackPanel`** — add `userAnswer` prop, pass to `McOptionExplanations`:
   - Add `userAnswer` to destructured props
   - Pass `userAnswer={userAnswer}` to `McOptionExplanations`

3. **`QuizSlide`** — pass `answer` to `FeedbackPanel`:
   - Change `<FeedbackPanel feedback={feedback} quiz={quiz} onNext={onNext} />`
   - To `<FeedbackPanel feedback={feedback} quiz={quiz} onNext={onNext} userAnswer={answer} />`

**Specific style changes in `McOptionExplanations`:**

```jsx
// Current
const isCorrect = correct.includes(opt);
className={`p-2 rounded text-sm border ${
  isCorrect ? "border-green-600 bg-green-900/20" : "border-gray-600 bg-gray-800/40"
}`}
className={`font-semibold ${isCorrect ? "text-green-400" : "text-gray-400"}`}

// Proposed
const isCorrect = correct.includes(opt);
const isUserPick = opt === userAnswer;
const isWrongPick = isUserPick && !isCorrect;
className={`p-2 rounded text-sm border ${
  isCorrect ? "border-green-600 bg-green-900/20"
  : isWrongPick ? "border-red-600 bg-red-900/20"
  : "border-gray-600 bg-gray-800/40"
}`}
className={`font-semibold ${
  isCorrect ? "text-green-400"
  : isWrongPick ? "text-red-400"
  : "text-gray-400"
}`}
```

#### To Add New
None.

### Documentation

#### Abstract (`docs/abstract/`)

**Update `docs/abstract/slide_stack.md`:**
- **User Flow** — Quiz slide branch: add note that MC feedback shows only user pick + correct option with color coding

#### Technical (`docs/technical/`)

**Update `docs/technical/slide_stack.md`:**
- **Frontend — Components** — `QuizSlide` row: note that `McOptionExplanations` filters to user pick + correct, with red/green styling

### Chrome Claude Extension Execution

After implementation is complete, execute the Chrome Claude Extension E2E tests defined in `docs/chrome_test/mc_feedback_highlight.md`.

---

## Dependencies

- Existing MC quiz data with `correct_options` field populated
- `quiz_metadata` with `response_to_user_option_*` fields for per-option explanations (optional — feature works without them)

## Open Questions

None — all requirements clear from user screenshot and description.
