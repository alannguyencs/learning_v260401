# SRS Algorithm Fixes — Activation Gate, Retry Cycle, lesson_count Timing

**Feature**: Fix three gaps between the 2-tier stacking algorithm spec and the current implementation
**Plan Created:** 2026-04-16
**Status:** Plan
**Reference**:
- [Discussion — 2-Tier Stacking Algorithm Compliance](../discussion/260416_two_tier_stacking_algorithm_compliance.md)
- [Abstract — Slide Stack](../abstract/slide_stack.md)
- [Technical — Slide Stack](../technical/slide_stack.md)
- [Technical — Revision Scheduling](../technical/revision_scheduling.md)
- [Technical — Learning Progress](../technical/learning_progress.md)

---

## Problem Statement

Three gaps between the spec and the current implementation:

1. **Activation gate missing** (`slide_selector.py`): The spec requires that a lesson's quizzes only pool into Tier 1 once **all chapters** in that lesson are marked as learnt. Currently, `SlideSelector.get_next_slide` pools quizzes from *already-learnt chapters* even while the lesson is still in progress. A user who has learnt 3 of 5 chapters sees R0 quizzes for those 3 chapters before finishing the lesson.

2. **Group B blocks Tier 2; retry cycle not implemented** (`slide_selector.py`): The spec says skipped quizzes (Group B) do not block Tier 2 (new chapters). When Group A is empty:
   - If round is done (>50% answered AND all chapters learnt) → Tier 2 fires.
   - If round is not done → retry cycle: clear skip log so skipped quizzes rejoin Group A and are re-served.
   Currently, Group B is served directly before Tier 2, permanently blocking new chapters until every skipped quiz is answered. The retry cycle is never run.

3. **`lesson_count` increments too early** (`learning_progress_service.py`): The spec defines a lesson as "fully learnt" only when both (a) all chapters are marked learnt AND (b) the first revision round R0 is completed. Currently, `lesson_count` increments the moment the last chapter is marked learnt, without waiting for R0. The spec itself acknowledges this as a known deferred gap.

---

## Proposed Solution

All three fixes are **pure backend service/CRUD changes**. No database schema changes and no frontend changes are required.

### Fix 1 — Activation Gate

In `SlideSelector.get_next_slide`, add a guard before pooling each round's quizzes:

```python
for round_row in due_rounds:
    if not crud_learning_progress.all_lesson_chapters_learnt(db, username, round_row.lesson_id):
        continue  # activation gate: lesson not fully covered yet
    non_skipped, skipped = get_eligible_quiz_ids_for_round(...)
```

This ensures Tier 1 quizzes only surface for lessons where every chapter is done.

### Fix 2 — Retry Cycle (replaces direct Group B serving)

After Group A is exhausted, instead of serving Group B directly, run the retry cycle for each due round that has skipped quizzes:

```
For each due round (activation gate passed):
  threshold_met = (quizzes_answered / total_lesson_quizzes > 0.50)?

  If threshold_met:
    Round is complete (or should have been completed already).
    Call RevisionService.complete_round_if_ready(...) to handle
    the edge case where record_quiz_response missed completion
    because chapters weren't all done at answer time.
  Else:
    Clear skip log for this round → skipped quizzes rejoin Group A.

Rebuild Group A from the refreshed eligible quizzes.
Serve from new Group A (weakest first).
Only if Group A still empty → Tier 2.
```

New CRUD helper `clear_skip_log_for_round(db, username, lesson_id, round_num)` deletes all `QuizSkipLog` rows for a specific round.

New `RevisionService.complete_round_if_ready(db, username, round_row, lesson_count)` extracts the round-completion logic (currently inlined in `record_quiz_response`) into a reusable helper callable from both `record_quiz_response` and the selector's retry cycle. Returns `True` if the round was completed.

### Fix 3 — lesson_count Increment Timing

Move `increment_lesson_count` from `mark_chapter_learnt` (fires on last chapter learnt) to `complete_round_if_ready` (fires when `round_num == 0` completes).

```
Before: all chapters learnt → lesson_count++
After:  R0 complete (>50% answered AND all chapters done) → lesson_count++
```

Effect on scheduling: R0 is created with `due_at = lesson_count` (immediately due, unchanged). R1 is scheduled with `due_at = lesson_count_at_R0_completion + 2`, where `lesson_count_at_R0_completion` is the value **before** the increment that R0 completion triggers. This is consistent and correct: the first tick of the lesson clock happens when the lesson is truly "learnt."

`QuizRespondResponse` gains an optional `lesson_count: Optional[int]` field — populated when R0 completes (so the caller knows the new clock value), `None` otherwise.

---

## Current Implementation Analysis

### What Exists (keep as-is)

| Component | File | Status |
|-----------|------|--------|
| `get_due_rounds` | `backend/src/crud/crud_revision.py:103` | Keep — queries open rounds where `due_at <= lesson_count` |
| `get_eligible_quiz_ids_for_round` | `backend/src/crud/crud_slides.py:40` | Keep — returns `(non_skipped, skipped)` |
| `log_quiz_skip` / `remove_quiz_skip` | `backend/src/crud/crud_slides.py:77,100` | Keep |
| `RevisionService.compute_recall` | `backend/src/service/revision_service.py:157` | Keep |
| `all_lesson_chapters_learnt` | `backend/src/crud/crud_learning_progress.py:76` | Keep — already exists, used by retry cycle |
| `increment_round_answered` / `complete_round` / `create_round` | `backend/src/crud/crud_revision.py` | Keep |
| Tier 2 chapter selection | `backend/src/service/slide_selector.py:123` | Keep |
| All frontend components and hooks | `frontend/src/` | Keep — no UI changes |
| All database migrations | `scripts/sql/` | Keep — no schema changes |

### What Changes

| Component | Current | Proposed |
|-----------|---------|----------|
| Tier 1 quiz pooling | Pools quizzes from learnt chapters only | Activation gate: skips entire lesson if not all chapters done |
| Group B serving | Served directly before Tier 2 | Never served directly; retry cycle clears skip log or completes round |
| Round completion logic | Inlined in `record_quiz_response` | Extracted to `complete_round_if_ready`; also called from selector |
| `lesson_count` increment | Fires in `mark_chapter_learnt` when last chapter learnt | Fires in `complete_round_if_ready` when R0 completes |
| `QuizRespondResponse` | `{is_correct, good_points, bad_points, round_done}` | + `lesson_count: Optional[int]` |

---

## Implementation Plan

### Key Workflow

#### Current Tier 1 flow

```
due_rounds = get_due_rounds(db, username, lesson_count)

for round_row in due_rounds:
    non_skipped, skipped = get_eligible_quiz_ids_for_round(...)
    group_a += non_skipped (with recall score)
    group_b += skipped

if group_a: serve weakest → DONE
if group_b: serve oldest → DONE   ← WRONG: blocks Tier 2
# Tier 2
```

#### Proposed Tier 1 flow

```
due_rounds = get_due_rounds(db, username, lesson_count)

# Pass 1: build Group A (activation gate applied)
for round_row in due_rounds:
    if NOT all_lesson_chapters_learnt(username, lesson_id): continue  ← GAP 1 FIX
    non_skipped, skipped = get_eligible_quiz_ids_for_round(...)
    group_a += non_skipped (with recall score)
    if skipped: rounds_needing_retry.append(round_row)

if group_a: serve weakest → DONE

# Retry cycle (GAP 2 FIX)
for round_row in rounds_needing_retry:
    total = get_lesson_quiz_count(lesson_id)
    threshold_met = (quizzes_answered / total > 0.50)
    if threshold_met:
        complete_round_if_ready(...)   ← handles edge case; round may already be done
    else:
        clear_skip_log_for_round(...)  ← skipped quizzes rejoin Group A

# Pass 2: rebuild Group A with cleared skip logs
group_a_retry = []
for round_row in due_rounds (activation gate applied):
    non_skipped, _ = get_eligible_quiz_ids_for_round(...)
    group_a_retry += non_skipped (with recall score)

if group_a_retry: serve weakest → DONE

# Tier 2
chapter = get_next_chapter(...)
if chapter: return ChapterSlide → DONE

return 'none'
```

#### lesson_count increment flow (GAP 3 FIX)

```
OLD:
  mark_chapter_learnt → all chapters done? → increment_lesson_count

NEW:
  mark_chapter_learnt → all chapters done? → just get_lesson_count (no increment)
  complete_round_if_ready(round_num=0) → threshold met → increment_lesson_count
                                                        → schedule R1 with due_at = new_lesson_count + 2
```

### Database Schema

#### To Delete
None.

#### To Update
None — no schema changes required.

#### To Add New
None — no new SQL migrations.

### CRUD

#### To Delete
None.

#### To Update
None.

#### To Add New

**`backend/src/crud/crud_slides.py`** — add one function:

```python
def clear_skip_log_for_round(
    db: Session, username: str, lesson_id: int, round_num: int
) -> None:
    """Clear all skip log entries for a specific round (retry cycle)."""
    db.query(QuizSkipLog).filter(
        QuizSkipLog.username == username,
        QuizSkipLog.lesson_id == lesson_id,
        QuizSkipLog.round_num == round_num,
    ).delete()
    db.commit()
```

### Services

#### To Delete
None.

#### To Update

**`backend/src/service/revision_service.py`**:

1. Extract inline round-completion block from `record_quiz_response` into a new `complete_round_if_ready` static method:

   ```python
   @staticmethod
   def complete_round_if_ready(
       db: Session,
       username: str,
       round_row: LessonRevisionRound,
       lesson_count: int,
   ) -> bool:
       """
       Check completion conditions and, if met, mark the round done and schedule the next.
       Also increments lesson_count when round_num == 0 (lesson fully learnt).
       Returns True if the round was completed, False otherwise.
       """
       total_quizzes = get_lesson_quiz_count(db, round_row.lesson_id)
       quizzes_ans = round_row.quizzes_answered
       all_chapters_done = crud_learning_progress.all_lesson_chapters_learnt(
           db, username, round_row.lesson_id
       )
       threshold_met = (
           total_quizzes > 0
           and (quizzes_ans / total_quizzes) > 0.50
           and all_chapters_done
       )
       if not threshold_met:
           return False

       crud_revision.complete_round(db, round_row.id, lesson_count)

       next_round_num = round_row.round_num + 1
       interval = 2 ** (round_row.round_num + 1)
       next_due_at = lesson_count + interval
       total_quizzes = get_lesson_quiz_count(db, round_row.lesson_id)
       crud_revision.create_round(
           db, username, round_row.lesson_id,
           next_round_num, next_due_at, total_quizzes,
       )

       # GAP 3 FIX: lesson is now fully learnt — advance the SRS clock
       if round_row.round_num == 0:
           crud_learning_progress.increment_lesson_count(db, username)

       return True
   ```

2. Update `record_quiz_response` to call `complete_round_if_ready` instead of the inlined block. Also update return type:

   - Replace inline completion block with: `completed = RevisionService.complete_round_if_ready(db, username, round_row, lesson_count)`
   - If `completed` and `round_row.round_num == 0`: fetch the new `lesson_count` from DB and populate `QuizResponseResult.lesson_count`
   - Signature of `QuizResponseResult` gains `lesson_count: Optional[int]` field

3. Update `QuizResponseResult` dataclass:

   ```python
   @dataclass
   class QuizResponseResult:
       round_done: bool
       next_round_num: Optional[int]
       next_round_due_at: Optional[int]
       lesson_count: Optional[int] = None  # new: populated when R0 completes
   ```

**`backend/src/service/learning_progress_service.py`**:

Remove `increment_lesson_count` call. The method always reads (never writes) `lesson_count`:

```python
# BEFORE:
if lesson_fully_learnt:
    lesson_count = crud_learning_progress.increment_lesson_count(db, username)
else:
    lesson_count = crud_learning_progress.get_lesson_count(db, username)

# AFTER:
lesson_count = crud_learning_progress.get_lesson_count(db, username)
```

`lesson_fully_learnt` in `ChapterLearntResult` keeps its meaning ("all chapters done") but no longer implies `lesson_count` was incremented.

**`backend/src/service/slide_selector.py`**:

Full rewrite of `get_next_slide` to implement the activation gate, retry cycle, and removal of direct Group B serving. Key changes:

1. Add import: `from src.crud.crud_slides import clear_skip_log_for_round`
2. Add import: `from src.crud.crud_content import get_lesson_quiz_count`
3. Pass 1 loop: add `all_lesson_chapters_learnt` activation gate check
4. Track rounds that have skipped quizzes → `rounds_needing_retry` list
5. After Group A check: retry cycle loop over `rounds_needing_retry`
6. Pass 2: rebuild Group A after skip log cleared
7. Remove lines 118-121 (Group B direct serving)

#### To Add New
None (new logic lives in updated files).

### API Endpoints

#### To Delete
None.

#### To Update

**`backend/src/schemas/slides.py`** — `QuizRespondResponse`:

```python
class QuizRespondResponse(BaseModel):
    is_correct: Optional[bool] = None
    good_points: Optional[List[str]] = None
    bad_points: Optional[List[str]] = None
    round_done: bool
    lesson_count: Optional[int] = None  # new: populated when R0 completes
```

**`backend/src/api/slides.py`** — `respond_to_quiz` handler: pass `result.lesson_count` into `QuizRespondResponse`.

#### To Add New
None.

### Testing

#### To Delete
None.

#### To Update

**`backend/tests/test_revision_service.py`**:
- Tests that called `mark_chapter_learnt` and asserted `lesson_count` increased must be updated: `lesson_count` no longer increments on chapter-learnt; it increments when R0 completes.
- Tests for `record_quiz_response` that check `QuizResponseResult` must add `lesson_count` assertion.

**`backend/tests/test_learning_progress.py`** and **`backend/tests/test_learning_progress_api.py`**:
- Remove assertions that `lesson_count` increments after the last chapter is marked learnt.
- `lesson_fully_learnt=True` should still be asserted, but `lesson_count` should remain unchanged.

**`backend/tests/test_slide_selector.py`**:
- Add test: when not all chapters in a lesson are learnt, that lesson's quizzes do NOT appear even if the round is due (activation gate).
- Add test: when all chapters are learnt and R0 is due, quizzes appear (gate open).
- Add test: skipping a quiz and exhausting Group A triggers retry cycle — skip log is cleared and the skipped quiz reappears in Group A.
- Add test: when >50% answered and Group A empty, retry cycle completes the round and Tier 2 fires (new chapter returned instead of quiz).

**`backend/tests/test_slides_api.py`**:
- Update quiz respond response assertions to include `lesson_count` field (None unless R0 just completed).

#### To Add New

None — all tests are updates to existing test files.

**Pre-commit loop:**

1. Run `source venv/bin/activate && pre-commit run --all-files`.
2. Fix any issues (lint errors, line count violations).
3. Re-run — repeat until clean.

### Frontend

#### To Delete
None.

#### To Update
None.

#### To Add New
None.

No user-visible UI changes. The `lesson_count` field in `QuizRespondResponse` is informational; the frontend currently ignores `lesson_count` from quiz responses, so no component changes are needed.

### Documentation

#### To Delete
None.

#### To Update

**`docs/abstract/slide_stack.md`**:
- **Solution** section: clarify that revision quizzes for a lesson only appear after all chapters in that lesson are marked as learnt (activation gate). Add note that skipping a quiz no longer blocks new chapters.
- **Acceptance Criteria**: add `- [ ] Revision quizzes for a lesson only appear after all chapters in that lesson are marked as learnt`.

**`docs/technical/slide_stack.md`**:
- **Pipeline — GET /api/slides/next — 2-Tier Algorithm**: update the ASCII diagram to show (a) activation gate in the Tier 1 loop, (b) retry cycle block replacing Group B direct serving.
- **Service Layer — `SlideSelector`**: update `get_next_slide` description.
- **CRUD — `crud_slides.py`**: add `clear_skip_log_for_round` row to the function table.

**`docs/technical/revision_scheduling.md`**:
- **Service Layer — `RevisionService`**: add `complete_round_if_ready` method row.
- **Service Layer — `QuizResponseResult`**: add `lesson_count` field row.
- **Pipeline — record_quiz_response**: update diagram to show `complete_round_if_ready` call replacing inline block; add `increment_lesson_count` step when `round_num == 0`.
- **Constraints & Edge Cases**: add note about selector-triggered round completion (edge case where chapters weren't all done at answer time).

**`docs/technical/learning_progress.md`**:
- **Pipeline — Mark Chapter Learnt**: remove `increment_lesson_count` from the "if lesson_fully_learnt" branch; always `get_lesson_count`.
- **Service Layer — `ChapterLearntResult`**: update `lesson_count` description: "User's current lesson count — not yet incremented (increment happens on R0 completion)".

#### To Add New
None.

#### API Documentation (`docs/api_doc/`)

No new endpoints. If `docs/api_doc/` contains a slides module, update the `POST /api/slides/quizzes/{id}/respond` response schema to include `lesson_count: int | null`.

### Chrome Claude Extension Execution

After implementation, execute: `docs/chrome_test/260416_srs_algorithm_fixes.md` (generated by the `chrome-test-generate` sub-skill).

If executing manually: `/webapp-dev:chrome-test-execute docs/chrome_test/260416_srs_algorithm_fixes.md`

---

## Dependencies

- `all_lesson_chapters_learnt` (`crud_learning_progress.py`) — already exists; used by the activation gate.
- `get_lesson_quiz_count` (`crud_content.py`) — already exists; used by the retry cycle threshold check.
- `get_due_rounds` — already exists; used by both Pass 1 and the retry cycle.
- No new external dependencies.

## Open Questions

None — all design decisions resolved:
- **Group B policy**: retry cycle clears skip log for incomplete rounds; Group B never served directly.
- **lesson_count timing**: moves to R0 completion (`complete_round_if_ready`).
