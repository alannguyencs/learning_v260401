# Group B Above Tier 2 — Skipped Quizzes Resurface Before New Chapters

**Feature**: Promote Group B (skipped revision quizzes) above Tier 2 (new chapter) in the slide-selection algorithm, so skipped quizzes resurface before new chapters are served.
**Plan Created:** 2026-04-18
**Status:** Plan
**Reference**:
- [Discussion — 2-Tier Stacking Algorithm Compliance](../discussion/260416_two_tier_stacking_algorithm_compliance.md)
- [Abstract — Slide Stack](../abstract/slide_stack.md)
- [Technical — Slide Stack](../technical/slide_stack.md)
- [Technical — System Pipelines](../technical/system_pipelines.md)
- [Spec — Slide Stack (slides_stack.md)](../slides_stack.md)
- [Testing Context](../technical/testing_context.md)

---

## Problem Statement

The current slide-selection algorithm in `SlideSelector.get_next_slide` (`backend/src/service/slide_selector.py:78-141`) serves slides in the order:

1. **Group A** — non-skipped due revision quizzes (weakest recall first)
2. **Tier 2** — next unlearnt chapter
3. **Group B** — skipped due revision quizzes (oldest skip first)

This means a quiz the user skipped today only resurfaces after every remaining unlearnt chapter across all books is exhausted. In practice, skipped quizzes rarely come back at all, because new chapters keep appearing. The user's intent when skipping a quiz is "show me this again later" — not "bury this forever until I run out of content." The current ordering makes the Skip action effectively a soft-delete for the current revision session.

The desired priority is:

1. **Group A** — non-skipped due revision quizzes (weakest recall first)
2. **Group B** — skipped due revision quizzes (oldest skip first)
3. **Tier 2** — next unlearnt chapter

Under the new priority, the user always clears the full due-quiz backlog (both unskipped and skipped) before the system serves a new chapter. Skipped quizzes are re-presented in round-robin fashion until each is either answered or re-skipped to the back of the queue.

This plan **supersedes Fix 2** of [260416_srs_algorithm_fixes.md](./260416_srs_algorithm_fixes.md) (the retry-cycle proposal), which was never implemented. The simpler reorder replaces the retry cycle entirely — no skip-log clearing, no round-completion edge-case handling in the selector.

---

## Proposed Solution

**Pure backend re-ordering in `SlideSelector.get_next_slide`.** No database migrations, no new CRUD functions, no frontend changes, no API schema changes. Group B becomes the middle priority tier instead of the trailing fallback.

### Algorithm change

```
BEFORE                               AFTER
------------------------------       --------------------------------
1. Group A → QuizSlide               1. Group A → QuizSlide
2. Tier 2  → ChapterSlide            2. Group B → QuizSlide   ← moved up
3. Group B → QuizSlide               3. Tier 2  → ChapterSlide
4. All caught up                     4. All caught up
```

### Code shape

Inside `SlideSelector.get_next_slide`, the three sequential `if` blocks after the Pass-1 loop are swapped. Group B is checked immediately after Group A; Tier 2 is now the last content-returning branch before `slide_type='none'`.

```python
# After Pass 1 builds group_a and group_b:

if group_a:
    group_a.sort(key=lambda x: x[0])
    _, qid, r, l = group_a[0]
    return SlideResult(slide_type="quiz", chapter=None, quiz=_build_quiz_dict(db, qid, r, l))

# NEW POSITION — Group B served before Tier 2
if group_b:
    qid, r, l = group_b[0]
    return SlideResult(slide_type="quiz", chapter=None, quiz=_build_quiz_dict(db, qid, r, l))

# Tier 2: next unlearnt chapter (now only fires when BOTH Group A and Group B are empty)
...
```

Group B ordering (`oldest skip first`) and Group A ordering (`weakest recall first`) are unchanged — only the position of the Group B branch moves.

### Why this is correct

- **Skip semantics**: A skip is a deferral, not a dismissal. Under the new ordering the deferral is bounded to "until Group A is empty" rather than "until all new content is exhausted."
- **Round completion still works**: Group B quizzes count toward `quizzes_answered` once answered via `record_quiz_response`. `remove_quiz_skip` already clears the skip log when a quiz is answered (`crud_slides.py:100`). Re-skipping refreshes `skipped_at`, pushing the quiz back to the end of Group B (`crud_slides.py:77`). No changes to these flows.
- **Activation gate preserved**: The existing `all_lesson_chapters_learnt` check in Pass 1 still filters both Group A and Group B contributions from each lesson.
- **Like boost still works**: Liked quizzes boost `forgetting_rate` and therefore appear earlier in Group A's weakest-first ordering. If a liked quiz is skipped, it goes to Group B — and now resurfaces before new chapters, which is actually more aligned with the Like feature's intent (liked quizzes come back sooner).

### Design pattern

This fits the **P3 Single-Track Workflow** pattern (status progression within the slide selector) combined with a **P6 Read-Only Aggregation View** (pooling due quizzes from multiple lessons). The change is a priority re-ordering inside the aggregation step — no new pattern elements.

---

## Current Implementation Analysis

### What Exists (keep as-is)

| Component | File | Status |
|-----------|------|--------|
| `get_due_rounds` | `backend/src/crud/crud_revision.py` | Keep — still queries due open rounds |
| `get_eligible_quiz_ids_for_round` | `backend/src/crud/crud_slides.py:40` | Keep — still returns `(non_skipped, skipped)` |
| `log_quiz_skip` / `remove_quiz_skip` | `backend/src/crud/crud_slides.py:77,100` | Keep — skip lifecycle unchanged |
| `all_lesson_chapters_learnt` activation gate | `backend/src/service/slide_selector.py:98-101` | Keep — still filters Pass 1 |
| `RevisionService.compute_recall` / `apply_like_boost` | `backend/src/service/revision_service.py` | Keep |
| `get_next_chapter_in_book` / `get_next_chapters_all_books` | `backend/src/crud/crud_slides.py:14,29` | Keep — Tier 2 chapter picker unchanged |
| `SlideResult` dataclass | `backend/src/service/slide_selector.py:21` | Keep — no new fields |
| `_build_quiz_dict` / `_build_chapter_dict` | `backend/src/service/slide_selector.py:32,49` | Keep |
| All API endpoints | `backend/src/api/slides.py` | Keep — no schema or handler changes |
| All frontend components, hooks, services | `frontend/src/` | Keep — no UI change |
| All SQL migrations | `scripts/sql/` | Keep — no schema change |

### What Changes

| Component | Current | Proposed |
|-----------|---------|----------|
| Group B branch position in `SlideSelector.get_next_slide` | Below Tier 2 (lines 136-139) | Between Group A check and Tier 2 (directly after line 122) |
| Effective slide priority | A → Tier 2 → B → none | A → B → Tier 2 → none |
| `docs/slides_stack.md` spec text | "Group B does NOT block Tier 2 — retry cycle" | "Group B blocks Tier 2 — all due quizzes clear before new chapters" |
| `docs/technical/slide_stack.md` pipeline diagram | Group B after Tier 2 | Group B before Tier 2 |
| `docs/technical/system_pipelines.md` Slide Selection Pipeline | "Tier 3: skipped quizzes" (after Tier 2) | "Tier 2: skipped quizzes"; chapters become Tier 3 |
| `docs/abstract/slide_stack.md` Solution / Acceptance Criteria | Implies skipped quizzes are last | Skipped quizzes precede new chapters |

---

## Implementation Plan

### Key Workflow

#### Current flow (inside `SlideSelector.get_next_slide`)

```
lesson_count = get_lesson_count(db, username)
due_rounds = get_due_rounds(db, username, lesson_count)

# Pass 1: build Group A + Group B with activation gate
for round_row in due_rounds:
    if NOT all_lesson_chapters_learnt(username, lesson_id): continue
    non_skipped, skipped = get_eligible_quiz_ids_for_round(...)
    group_a += [(m_t, qid, round_num, lesson_id) for qid in non_skipped]
    group_b += [(qid, round_num, lesson_id) for qid in skipped]

if group_a: return weakest Group A quiz
if book_id: chapter = get_next_chapter_in_book(...)
else:       chapter = random.choice(get_next_chapters_all_books(...))
if chapter: return chapter                ← Tier 2 fires before Group B
if group_b: return oldest Group B quiz    ← Group B only if no chapters left
return slide_type='none'
```

#### Proposed flow

```
lesson_count = get_lesson_count(db, username)
due_rounds = get_due_rounds(db, username, lesson_count)

# Pass 1: build Group A + Group B with activation gate (UNCHANGED)
for round_row in due_rounds:
    if NOT all_lesson_chapters_learnt(username, lesson_id): continue
    non_skipped, skipped = get_eligible_quiz_ids_for_round(...)
    group_a += [(m_t, qid, round_num, lesson_id) for qid in non_skipped]
    group_b += [(qid, round_num, lesson_id) for qid in skipped]

if group_a: return weakest Group A quiz
if group_b: return oldest Group B quiz    ← NEW POSITION — before Tier 2

if book_id: chapter = get_next_chapter_in_book(...)
else:       chapter = random.choice(get_next_chapters_all_books(...))
if chapter: return chapter                ← Tier 2 now fires only after B empty
return slide_type='none'
```

#### To Delete
None.

#### To Update
The three return branches inside `get_next_slide` are reordered. Only three contiguous if-blocks move; no logic inside any branch changes.

#### To Add New
None.

### Database Schema

#### To Delete
None.

#### To Update
None.

#### To Add New
None — no schema changes, no new SQL migrations.

### CRUD

#### To Delete
None.

#### To Update
None.

#### To Add New
None — `get_eligible_quiz_ids_for_round`, `log_quiz_skip`, `remove_quiz_skip`, and `get_skipped_quizzes` in `backend/src/crud/crud_slides.py` already supply everything the new ordering needs.

### Services

#### To Delete
None.

#### To Update

**`backend/src/service/slide_selector.py`** — reorder three branches in `SlideSelector.get_next_slide`:

1. Keep lines 87-115 (lesson_count read, due_rounds loop with activation gate, Group A / Group B build) exactly as-is.
2. Keep lines 117-122 (Group A serve) as-is.
3. **Move** the Group B block (currently lines 135-139) to sit immediately after line 122. It becomes the new Tier 2.
4. **Shift** the Tier 2 chapter block (currently lines 124-133) to sit after the Group B block. It becomes the new Tier 3.
5. The trailing `return SlideResult(slide_type="none", ...)` at line 141 stays at the bottom.
6. Update the class docstring at line 76 and the method docstring at line 80 to reflect the new priority.

Final method structure:

```python
class SlideSelector:
    """Implements the slide-selection algorithm:
       Group A (non-skipped due quizzes, weakest recall first)
       → Group B (skipped due quizzes, oldest skip first)
       → Tier 2 (next unlearnt chapter).
    """

    @staticmethod
    def get_next_slide(db, username, book_id=None) -> SlideResult:
        """
        Return the next slide for the user.

        Priority:
        1. Due revision quizzes — Group A (non-skipped, weakest recall first)
        2. Due revision quizzes — Group B (skipped, oldest skip first)
        3. Next unlearnt chapter
        """
        lesson_count = crud_learning_progress.get_lesson_count(db, username)
        due_rounds = get_due_rounds(db, username, lesson_count)
        group_a, group_b = [], []

        for round_row in due_rounds:
            if not crud_learning_progress.all_lesson_chapters_learnt(
                db, username, round_row.lesson_id
            ):
                continue
            non_skipped, skipped = get_eligible_quiz_ids_for_round(
                db, username, round_row.lesson_id, round_row.round_num
            )
            for qid in non_skipped:
                recall = get_quiz_recall(db, username, qid)
                if recall is not None:
                    elapsed = lesson_count - (recall.last_reviewed_lesson_count or 0)
                    m_t = RevisionService.compute_recall(recall.forgetting_rate, elapsed)
                else:
                    m_t = 1.0
                group_a.append((m_t, qid, round_row.round_num, round_row.lesson_id))
            for qid in skipped:
                group_b.append((qid, round_row.round_num, round_row.lesson_id))

        # 1. Group A — weakest recall first
        if group_a:
            group_a.sort(key=lambda x: x[0])
            _, qid, r, l = group_a[0]
            return SlideResult(slide_type="quiz", chapter=None,
                               quiz=_build_quiz_dict(db, qid, r, l))

        # 2. Group B — oldest skip first (now blocks Tier 2)
        if group_b:
            qid, r, l = group_b[0]
            return SlideResult(slide_type="quiz", chapter=None,
                               quiz=_build_quiz_dict(db, qid, r, l))

        # 3. Tier 2 — next unlearnt chapter
        if book_id:
            chapter = get_next_chapter_in_book(db, username, book_id)
        else:
            chapters = get_next_chapters_all_books(db, username)
            chapter = random.choice(chapters) if chapters else None
        if chapter:
            return SlideResult(slide_type="chapter",
                               chapter=_build_chapter_dict(db, chapter), quiz=None)

        return SlideResult(slide_type="none", chapter=None, quiz=None)
```

#### To Add New
None.

### API Endpoints

#### To Delete
None.

#### To Update
None — no request schema, response schema, handler, or route changes. All existing endpoints (`GET /api/slides/current`, `POST /api/slides/forward`, `POST /api/slides/back`, `POST /api/slides/chapters/{id}/learnt`, `POST /api/slides/quizzes/{id}/respond`) continue to produce the same payload shapes; only the ordering of slides returned by repeated calls to `get_next_slide` changes.

#### To Add New
None.

### Testing

#### To Delete
None.

#### To Update

**`backend/tests/test_slide_selector.py`** — update existing tests whose assertions encode the OLD priority:

- `TestSkipQueueWithinTier1.test_skipped_quiz_resurfaces_when_group_a_empty` (line 160): this test already asserts that a skipped quiz surfaces when Group A is empty, but the current setup path completes R0 and advances `lesson_count`, so Tier 2 is also empty in that scenario (no other chapters learnt in another book). Verify the assertion still holds under the new ordering — it should, because Group B now comes before Tier 2, so an earlier return point is hit. Add an explicit assertion that Group B is served **before** any available unlearnt chapter: create an unlearnt chapter in another book, skip a Group A quiz, exhaust the rest of Group A, then assert the next slide is the skipped quiz (not the unlearnt chapter).
- `TestSkipQueueWithinTier1.test_skipped_quiz_deferred_to_group_b` (line 142): still valid — skipped quiz is deferred behind non-skipped Group A quizzes. No change needed.
- `TestTier2NewChapter.test_tier2_new_chapter_after_no_revisions` (line 119): still valid — with no due rounds, Tier 2 fires. No change needed.
- `TestTier2NewChapter.test_tier2_specific_book_filter` (line 129): still valid — with no due rounds, Tier 2 fires with book filter. No change needed.

#### To Add New

**`backend/tests/test_slide_selector.py`** — add tests asserting the new priority:

1. **`test_group_b_served_before_tier_2`** — a skipped quiz exists AND an unlearnt chapter exists. Expect the skipped quiz to be returned, not the chapter.
2. **`test_group_a_still_beats_group_b`** — both Group A and Group B have quizzes. Expect a Group A quiz (sanity; current behavior preserved).
3. **`test_tier_2_fires_only_when_both_groups_empty`** — no due rounds remain (or they fail the activation gate), and an unlearnt chapter exists. Expect the chapter.
4. **`test_group_b_oldest_skip_first`** — two skipped quizzes with different `skipped_at`. Expect the older skip first.
5. **`test_re_skipping_sends_quiz_to_back_of_group_b`** — skip q1, skip q2, then re-skip q1. Expect q2 returned first (oldest remaining skip) on next call.

**Pre-commit loop:**

1. Run `source venv/bin/activate && pre-commit run --all-files`.
2. Fix any issues (lint errors, line-count violations).
3. Re-run — Prettier may re-format frontend files; repeat until pre-commit passes cleanly.

### Frontend

#### To Delete
None.

#### To Update
None.

#### To Add New
None — the frontend receives slide payloads through the same endpoints with the same shape. `QuizSlide`, `ChapterSlide`, `SlidePage`, `useSlide` hook, and all other components are untouched.

### Documentation

#### To Delete
None.

#### To Update

**`docs/abstract/slide_stack.md`**:

- **Solution** paragraph 1: change "skipped quizzes form a back-of-queue and resurface only after all unskipped quizzes are exhausted" to "skipped quizzes form a back-of-queue and resurface after all unskipped quizzes are exhausted but before any new chapter is served."
- **User Flow** (quiz slide branch): update the `[Down arrow]` bullet to note "the skipped quiz rejoins the back of the due-quiz queue and will resurface before new chapters."
- **Acceptance Criteria**: update the existing bullet *"Skipping a quiz via the down arrow puts it at the back of the queue"* to *"Skipping a quiz via the down arrow puts it at the back of the due-quiz queue — the quiz resurfaces before any new chapter is served."*

**`docs/technical/slide_stack.md`**:

- **Pipeline — GET /api/slides/next — 2-Tier Algorithm** (lines 150-173): update the ASCII diagram so the sequence is `Group A → Group B → Tier 2 → none`. Replace the current text *"Group B (skipped): ordered by skipped_at ASC (oldest skip first) → If any → return first as QuizSlide → done"* block with a block that sits **before** Tier 2.
- **Architecture** / **Service Layer — `SlideSelector`** (line 271): update the `get_next_slide` description: *"Returns `SlideResult` using algorithm: Group A (non-skipped, weakest recall first) → Group B (skipped, oldest first) → Tier 2 (next unlearnt chapter)."*

**`docs/technical/system_pipelines.md`**:

- **Slide Selection Pipeline** (lines 52-72): renumber the three bullet points so the diagram reads:
  - TIER 1: non-skipped due revision rounds → QuizSlide
  - TIER 2: skipped due revision rounds → QuizSlide (was TIER 3)
  - TIER 3: next unlearnt chapter → ChapterSlide (was TIER 2)

**`docs/slides_stack.md`** (project-level spec):

- **Solution** paragraph (line 47): adjust the `do not block Tier 2` phrasing; replace with "Within revision quizzes, unskipped quizzes are served first (weakest recall); skipped quizzes form a back-of-queue that is served after the unskipped pool but before new chapters."
- **2-Tier Stacking Algorithm** — Tier 1 paragraph (line 132): rewrite the sentence *"Skipped quizzes (Group B) sit in a back-of-queue and do not block Tier 2 — they resurface via a retry cycle once all non-skipped quizzes are exhausted"* to *"Skipped quizzes (Group B) sit in a back-of-queue that is consumed after Group A and before Tier 2. They resurface in oldest-skip-first order; re-skipping refreshes `skipped_at` to push the quiz to the back."*
- **ASCII algorithm diagram** (lines 138-182): delete the "Retry cycle" box. Rewrite the boxes in order: `Group A → (if empty) Group B → (if empty) Tier 2 → All caught up`. Remove "does NOT block Tier 2" annotation from the Group B box.
- **Compliance note**: add a remark below the diagram that this supersedes the retry-cycle approach referenced in `260416_srs_algorithm_fixes.md`.

#### To Add New
None.

#### API Documentation (`docs/api_doc/`)

No changes — no endpoint path, method, request, or response shape changes. Skim `docs/api_doc/` (if it exists) and confirm; if any endpoint doc text mentions ordering, update it to reflect A → B → Tier 2.

### Chrome Claude Extension Execution

After implementation is complete, execute the Chrome Claude Extension E2E tests defined in `docs/chrome_test/260418_{hhmm}_group_b_above_tier_2.md` (generated in Step 1.6 of feature-plan) by invoking the `chrome-test-execute` skill.

`feature-implement-full` invokes it automatically. For a manual run:

```
/webapp-dev:chrome-test-execute docs/chrome_test/260418_{hhmm}_group_b_above_tier_2.md
```

---

## Dependencies

- `get_due_rounds`, `get_eligible_quiz_ids_for_round`, `log_quiz_skip`, `remove_quiz_skip` — all already exist.
- `all_lesson_chapters_learnt` — already exists; continues to gate Pass 1.
- `RevisionService.compute_recall` — already exists; unchanged.
- No new external services, packages, or schema dependencies.

## Open Questions

- **Retry-cycle plan (`260416_srs_algorithm_fixes.md`, Fix 2)**: this plan supersedes Fix 2 with a simpler reorder. Fixes 1 (activation gate) and 3 (`lesson_count` timing) from 260416 are independent and remain valid if the user still wants them. Confirm whether the Fix 2 portion of 260416 should be marked as superseded in `docs/checklist.md`.
- **Order preservation across repeated calls**: re-skipping a Group B quiz updates `skipped_at` to now, pushing it to the back. Confirm this is the intended behavior (it is the existing behavior; no change planned).
