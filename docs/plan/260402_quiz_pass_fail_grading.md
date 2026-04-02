# Quiz PASSED/FAILED Grading with Good/Bad Points

**Feature**: Replace Correct/Incorrect labels with PASSED/FAILED across all quiz types; open-ended quizzes return itemized good/bad points with a 66% pass threshold
**Plan Created:** 2026-04-02
**Status:** Plan
**Reference**:
- [Abstract — Slide Stack](../abstract/slide_stack.md)
- [Technical — Slide Stack](../technical/slide_stack.md)

---

## Problem Statement

1. The current grading labels "Correct" / "Incorrect" are binary and don't reflect partial understanding.
2. For open-ended quizzes (free_recall, teach_back), the LLM returns a single boolean `is_correct` and a one-sentence feedback string. This doesn't help the user understand which parts of their answer were good and which were missing.
3. There is no partial-credit mechanism — a user who covers 3 out of 4 key points gets the same "Incorrect" as someone who wrote nothing relevant.

---

## Proposed Solution

### 1. Label Change (all quiz types)
Replace "Correct" / "Incorrect" with **"PASSED"** / **"FAILED"** across the entire UI.

### 2. Itemized Grading (open-ended quizzes)
For free_recall, teach_back, and cloze quizzes, the LLM now returns:
- `good_points`: list of things the student got right
- `bad_points`: list of things the student missed or got wrong
- `is_correct`: computed as `len(good_points) / (len(good_points) + len(bad_points)) >= 0.66`

### 3. SRS Impact
PASSED = `is_correct=true` (forgetting rate 0.7x). FAILED = `is_correct=false` (forgetting rate 1.2x). No change to the spaced-repetition algorithm.

### 4. MC Quizzes
MC quizzes keep the same auto-grading logic (no LLM call). Only the label changes to PASSED/FAILED.

---

## Current Implementation Analysis

### What Exists (keep as-is)

| Component | File | Status |
|-----------|------|--------|
| MC auto-grading logic | `backend/src/api/slides.py` | Keep — only label changes |
| SlideSelector | `backend/src/service/slide_selector.py` | Keep — unchanged |
| RevisionService (SRS) | `backend/src/service/revision_service.py` | Keep — PASSED maps to is_correct=true |
| useSlide hook | `frontend/src/hooks/useSlide.js` | Keep — unchanged |
| QuizSlide structure | `frontend/src/components/QuizSlide.jsx` | Keep — modify FeedbackPanel |

### What Changes

| Component | Current | Proposed |
|-----------|---------|----------|
| `GradingOutput` schema | `{ is_correct: bool, feedback: str }` | `{ good_points: [str], bad_points: [str] }` |
| `GradingResult` dataclass | `is_correct: bool, feedback: str` | `is_correct: bool, good_points: [str], bad_points: [str]` |
| `QuizGrader.grade()` | Returns boolean + one sentence | Returns good/bad points; computes is_correct from 66% threshold |
| System prompt | Asks for `{is_correct, feedback}` | Asks for `{good_points, bad_points}` |
| `QuizRespondResponse` | `is_correct: bool, feedback: str` | `is_correct: bool, good_points: [str], bad_points: [str]` |
| API handler | Passes `feedback` string | Passes `good_points` and `bad_points` lists |
| FeedbackPanel | Shows "Correct"/"Incorrect" + feedback sentence | Shows "PASSED"/"FAILED" + good/bad point lists |

---

## Implementation Plan

### Key Workflow

#### To Delete
None.

#### To Update

**Open-ended quiz grading flow (changed):**

```
User submits open-ended answer
  │
  ▼
QuizGrader.grade(question, expected_answer, user_answer, quiz_type)
  │
  ▼
Gemini 2.5 Flash returns:
  { good_points: ["point 1", ...], bad_points: ["missed X", ...] }
  │
  ▼
Compute: is_correct = len(good_points) / max(len(good_points) + len(bad_points), 1) >= 0.66
  │
  ▼
Return GradingResult(is_correct, good_points, bad_points)
  │
  ▼
API returns QuizRespondResponse(is_correct, good_points, bad_points, round_done)
  │
  ▼
Frontend FeedbackPanel:
  ├── Badge: "PASSED" (green) or "FAILED" (red)
  ├── Good points list (green bullets)
  └── Bad points list (red bullets)
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

**`backend/src/service/quiz_grader.py`:**

1. **`GradingOutput`** — change schema:
   ```python
   class GradingOutput(BaseModel):
       good_points: list[str] = Field(description="List of correct points in the student answer")
       bad_points: list[str] = Field(description="List of missing or incorrect points")
   ```

2. **`GradingResult`** — change fields:
   ```python
   @dataclass
   class GradingResult:
       is_correct: bool
       good_points: list[str]
       bad_points: list[str]
   ```

3. **`QuizGrader.grade()`** — compute `is_correct` from threshold:
   ```python
   total = len(parsed.good_points) + len(parsed.bad_points)
   is_correct = (len(parsed.good_points) / max(total, 1)) >= 0.66
   return GradingResult(
       is_correct=is_correct,
       good_points=parsed.good_points,
       bad_points=parsed.bad_points,
   )
   ```

**`backend/resources/prompts/quiz_grader.md`** — update prompt:
```
You are a quiz grader for a spaced-repetition learning app.
You are given a quiz question, the expected answer, and a student's response.

Your task: identify what the student got right and what they missed.

Guidelines:
- For free recall: compare against core concepts in the expected answer.
- For teach-back: check if the student explained each key idea clearly.
- For cloze: check if the fill-in is correct or semantically equivalent.
- Be lenient on wording; strict on correctness of concepts.
- Each good_point or bad_point should be one concise sentence.

Respond ONLY in JSON:
{
  "good_points": ["what the student got right", ...],
  "bad_points": ["what the student missed or got wrong", ...]
}
```

#### To Add New
None.

### API Endpoints

#### To Delete
None.

#### To Update

**`backend/src/schemas/slides.py`** — change `QuizRespondResponse`:
```python
class QuizRespondResponse(BaseModel):
    is_correct: Optional[bool] = None
    good_points: Optional[list[str]] = None
    bad_points: Optional[list[str]] = None
    round_done: bool
```

**`backend/src/api/slides.py`** — update the response construction for open-ended:
- Replace `feedback=grading.feedback` with `good_points=grading.good_points, bad_points=grading.bad_points`
- For MC quizzes: `good_points=None, bad_points=None` (no itemized feedback)
- For skips: `good_points=None, bad_points=None`

#### To Add New
None.

### Testing

#### To Delete
None.

#### To Update

**`backend/tests/test_quiz_grader.py`:**
- Update mock responses to return `GradingOutput(good_points=[...], bad_points=[...])`
- Test threshold: 2 good + 1 bad = 66% → PASSED
- Test threshold: 1 good + 2 bad = 33% → FAILED
- Test edge: 0 good + 0 bad → PASSED (empty answer edge case — treat as 0/0 = PASSED to avoid division issues, or FAILED — choose FAILED)

**`backend/tests/test_slides_api.py`:**
- Update open-ended quiz response assertions: `good_points` and `bad_points` instead of `feedback`

**`frontend/src/__tests__/components/QuizSlide.test.js`:**
- Update feedback mock objects: replace `feedback` string with `good_points` / `bad_points` arrays
- Test PASSED/FAILED labels appear instead of Correct/Incorrect

#### To Add New
None.

**Pre-commit loop:**
1. Run `source venv/bin/activate && pre-commit run --all-files`.
2. Fix any issues.
3. Repeat until clean.

### Frontend

#### To Delete
None.

#### To Update

**`frontend/src/components/QuizSlide.jsx`:**

1. **`FeedbackPanel`** — update badge and feedback display:
   - Change `"✓ Correct"` to `"✓ PASSED"`
   - Change `"✗ Incorrect"` to `"✗ FAILED"`
   - Replace single `feedback.feedback` paragraph with two lists:
     - Good points: green bullet list (reuse `KeyPointsList` pattern with green color)
     - Bad points: red bullet list
   - Show score: `"{good_count}/{total} points"` above the lists

2. **`FeedbackPanel`** — update prop usage:
   - `feedback.feedback` → no longer used
   - `feedback.good_points` → array of strings for green list
   - `feedback.bad_points` → array of strings for red list

**`frontend/src/hooks/useSlide.js`:**
- No changes needed — `feedback` state already stores the full API response object

#### To Add New
None.

### Documentation

#### Abstract (`docs/abstract/`)

**Update `docs/abstract/slide_stack.md`:**
- **User Flow** — Quiz slide branch: update "is_correct badge + AI feedback shown" to "PASSED/FAILED badge + good/bad points shown"
- **Scope — Included**: update "AI feedback display" to "AI-graded PASSED/FAILED with itemized good/bad points"

#### Technical (`docs/technical/`)

**Update `docs/technical/slide_stack.md`:**
- **Service Layer** — `GradingResult`: update fields from `is_correct, feedback` to `is_correct, good_points, bad_points`
- **LLM Requests Layer** — update GradingOutput schema table and prompt description
- **API Layer** — note that `QuizRespondResponse` now returns `good_points` and `bad_points` instead of `feedback`
- **Pipeline** — update POST /api/slides/quizzes respond pipeline to show good/bad points flow

### Chrome Claude Extension Execution

After implementation is complete, execute the Chrome Claude Extension E2E tests defined in `docs/chrome_test/quiz_pass_fail_grading.md`.

---

## Dependencies

- Gemini API key (already configured)
- Existing quiz data with `expected_answer` populated for open-ended types

## Open Questions

None — all questions resolved during planning.
