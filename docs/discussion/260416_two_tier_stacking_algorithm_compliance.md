# 2-Tier Stacking Algorithm — Compliance Review

**Date:** 2026-04-16
**Question:** Does the current codebase implement the 2-Tier Stacking Algorithm rules?

---

## Summary

The codebase implements most of the algorithm, but has **three gaps** versus the spec:

| Rule | Status |
|------|--------|
| R0 created on first chapter learnt | ✅ Implemented |
| Round completion: >50% answered AND all chapters learnt | ✅ Implemented |
| Next-round intervals: `2^(round_num+1)` | ✅ Implemented |
| Due condition: `due_at_lesson_count <= lesson_count` | ✅ Implemented |
| Group A: weakest-recall-first via m(t) | ✅ Implemented |
| Group A blocks Tier 2 | ✅ Implemented |
| Pooling across all due lessons (no per-lesson isolation) | ✅ Implemented |
| Skipped quizzes ordered oldest-first | ✅ Implemented |
| Tier 2: book filter or random pick | ✅ Implemented |
| **Activation gate**: quizzes only surface when ALL chapters in lesson are learnt | ❌ Not implemented |
| **Group B does NOT block Tier 2** | ❌ Not implemented — Group B blocks Tier 2 |
| **lesson_count increments only after R0 complete** | ❌ Not implemented (known, spec acknowledges this) |

---

## Gap 1 — Activation Gate (not implemented)

**Spec rule:** Before pooling a lesson's quizzes into Tier 1, check: are ALL chapters in this lesson marked as learnt? If not → skip this lesson entirely.

**Current behaviour:** `SlideSelector.get_next_slide` (`backend/src/service/slide_selector.py:92`) calls `get_due_rounds` then `get_eligible_quiz_ids_for_round` for each round. Neither function checks whether all chapters in the lesson are learnt.

`get_eligible_quiz_ids_for_round` (`backend/src/crud/crud_slides.py:40`) filters quizzes to those whose chapters are in `learnt_chapter_ids` — so it only returns quizzes from *already-learnt* chapters. But "quizzes from chapters I've learnt so far" is not the same as "lesson's quizzes unlocked only after the last chapter is learnt."

**Effect:** A user who has learnt chapters 1–3 of a 5-chapter lesson will see R0 quizzes for those 3 chapters while still working through chapters 4 and 5. The spec intends for Tier 1 quizzes to start only after the whole lesson is done.

**Where the fix belongs:** In `SlideSelector.get_next_slide`, before calling `get_eligible_quiz_ids_for_round`, add a check:

```python
from src.crud import crud_learning_progress
if not crud_learning_progress.all_lesson_chapters_learnt(db, username, round_row.lesson_id):
    continue  # skip this lesson's round — activation gate
```

---

## Gap 2 — Group B blocks Tier 2 (spec says it should not)

**Spec rule:** Group B (skipped quizzes) sits in a back-of-queue and **does not block Tier 2**. Tier 2 fires when Group A is empty.

**Current behaviour:** `slide_selector.py:118-121`:

```python
if group_b:
    best_quiz_id, best_round_num, best_lesson_id = group_b[0]
    quiz_dict = _build_quiz_dict(db, best_quiz_id, best_round_num, best_lesson_id)
    return SlideResult(slide_type="quiz", chapter=None, quiz=quiz_dict)

# Tier 2: next unlearnt chapter  ← Group B prevents this from being reached
```

Group B is checked before Tier 2, so a user with any skipped quizzes will never see new chapters until every skipped quiz is cleared. The spec intends the opposite: new chapters advance in parallel with Group B quizzes, and Group B quizzes resurface as a background retry.

**Note:** The technical documentation (`docs/technical/slide_stack.md`, pipeline diagram) also documents the current (non-spec-compliant) behaviour: `Group B → return first as QuizSlide → done`. So the docs are in sync with the code but out of sync with the spec.

**Effect:** If a user skips a quiz, they are blocked from new chapters until that quiz is answered.

**Where the fix belongs:** In `SlideSelector.get_next_slide`, Group B should only be surfaced after both Group A AND Tier 2 are exhausted — or, per spec, only appended as a secondary queue that is served concurrently with Tier 2. The exact interleaving policy needs clarification.

---

## Gap 3 — lesson_count increments without waiting for R0 completion (known)

**Spec rule:** A lesson is "learnt" (and `lesson_count` increments) when: (1) all chapters are marked as learnt AND (2) R0 is complete (>50% quizzes answered).

**Current behaviour:** `LearningProgressService.mark_chapter_learnt` (`backend/src/service/learning_progress_service.py:50-51`) increments `lesson_count` as soon as all chapters are learnt, without waiting for R0 to complete:

```python
if lesson_fully_learnt:
    lesson_count = crud_learning_progress.increment_lesson_count(db, username)
```

**The spec itself acknowledges this:** "Remark: condition (2) is not yet implemented — currently `lesson_count` increments immediately when the last chapter is marked learnt, without waiting for R0 completion."

**Effect:** The lesson clock advances before the user has engaged with R0 quizzes. This means next-round `due_at` values are calculated from a slightly earlier `lesson_count` than intended.

---

## What IS Working Correctly

### Revision round scheduling (`revision_service.py`)
- R0 created on first chapter learnt with `due_at = lesson_count` (immediately due). ✅
- R0 incremented as more chapters in the lesson are learnt. ✅
- Round completion check: `quizzes_answered / total_lesson_quizzes > 0.50 AND all_chapters_done`. ✅ (`revision_service.py:125-126`)
- Next round interval: `2^(round_num + 1)` (`revision_service.py:138`). ✅
- Skips (`is_correct=None`) don't increment `quizzes_answered`. ✅

### Group A recall scoring (`slide_selector.py`)
- `m(t) = exp(-forgetting_rate * lessons_elapsed / 10)` via `RevisionService.compute_recall`. ✅
- New quizzes with no recall history get `m_t = 1.0` (treated as strongest recall, served last). ✅
- Group A sorted ascending by m(t) (weakest first). ✅

### Skip log (`crud_slides.py`)
- `log_quiz_skip` upserts with fresh `skipped_at` — re-skipping pushes a quiz to the back of Group B. ✅
- `remove_quiz_skip` called on answer — clears the skip record. ✅
- Group B ordered by `skipped_at ASC` (oldest first). ✅

### Tier 2
- Book filter → `get_next_chapter_in_book` (ordered by lesson_index, chapter_index). ✅
- No book → `get_next_chapters_all_books` → `random.choice`. ✅

---

## Next Steps

The two unacknowledged gaps are actionable:

1. **Activation gate** — add an `all_lesson_chapters_learnt` check in `SlideSelector.get_next_slide` before queueing a lesson's quizzes into Group A/B. Straightforward fix.

2. **Group B / Tier 2 ordering** — requires a design decision: should Group B be completely non-blocking (Tier 2 always fires when Group A is empty), or should Group B be served concurrently with Tier 2 in some interleaved manner? Once the policy is clear, the fix in `slide_selector.py` is simple.

Use `/feature-update` once you decide on the policy for Gap 2.
