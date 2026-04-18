# Slide Stack — Next-Slide Selection Algorithm

**Report date:** 2026-04-18

---

## 0. Concepts

- `lesson_count`: running count of how many lessons the user has touched so far; acts as the clock for spacing decisions.
- `revision_round`: a per-(user, lesson) spaced-repetition batch, numbered R0, R1, R2, …; the user answers the lesson's quizzes inside the round, and completing it schedules the next round at an exponentially longer interval (R0 → R1 in +2 lessons, R1 → R2 in +4, etc.).
- `status`: lifecycle flag on a revision round; `'open'` means the round still has quizzes to serve, `'done'` means every quiz in it has been answered and a later round has been scheduled. Note: there is no "scheduled-but-not-yet-due" status — when a round completes, the next round is created with `status='open'` and a future `due_at_lesson_count`. Status and due-ness are orthogonal:
  - `status='open'` AND `due_at_lesson_count > lesson_count` → **dormant** (exists, will surface later)
  - `status='open'` AND `due_at_lesson_count <= lesson_count` → **active** (returned by `get_due_rounds`, feeds Group A)
  - `status='done'` → terminal (already completed)
- `due_at_lesson_count`: the `lesson_count` value at which a revision round becomes eligible; the round stays dormant until `lesson_count` reaches this threshold.
- `due_rounds`: the set of revision rounds currently eligible for Tier 1 consideration — essentially a list of `(Lᵢ, Rⱼ)` pairs (lesson id, round number) for the current user. A pair qualifies iff its row has `status='open'` AND `due_at_lesson_count <= lesson_count`.
- `user_chapter_progress`: per-(user, chapter) record marking which chapters the user has already learnt; drives the activation gate.
- `quiz_skip_log`: per-(user, quiz) skip marker; splits eligible quizzes into Group A (non-skipped) vs Group B (skipped).
- `user_quiz_recall`: per-(user, quiz) memory state, holding `forgetting_rate` and `last_reviewed_lesson_count`; feeds the recall score `m(t)`.
- `user_slide_like`: per-(user, quiz) like row (added 260418); does not change the sort key directly but raises `forgetting_rate` at like time, which then lowers `m(t)`.
- `book_id`: optional request parameter that narrows Tier 2 to chapters from a specific book.

---

## 1. What the algorithm decides

Every call to `GET /api/slides/current` (or `POST /api/slides/forward`) eventually lands in `SlideSelector.get_next_slide(db, username, book_id)` and returns a `SlideResult` with one of three shapes:

- `slide_type = "quiz"` + a `quiz` dict (a due revision quiz)
- `slide_type = "chapter"` + a `chapter` dict (a new unlearnt chapter)
- `slide_type = "none"` (nothing left to serve)

The selection favours **memory maintenance over progression**: if anything is due for revision, it is served before any new chapter.

---

## 2. Inputs

| Input | Source | Used for |
|-------|--------|----------|
| `lesson_count` | `user_lesson_count` (per user) | Clock for spacing decisions — see `RevisionService.compute_recall` |
| `due_rounds` | `lesson_revision_rounds WHERE status='open' AND due_at_lesson_count <= lesson_count` | Which `(lesson, round_num)` groups are eligible for Tier 1 |
| `user_chapter_progress` | one row per (user, chapter) that has been learnt | Activation gate (all chapters of a lesson must be learnt before its round-quizzes surface) |
| `quiz_skip_log` | per-(user, quiz) skip markers | Split eligible quizzes into Group A (non-skipped) vs Group B (skipped) |
| `user_quiz_recall` | per-(user, quiz) `forgetting_rate` + `last_reviewed_lesson_count` | Compute `m(t)` per quiz in Group A for weakest-first sorting |
| `user_slide_like` | per-(user, quiz) like row (new in 260418) | Does **not** change sort key directly — influences `forgetting_rate` at like time, which then flows into `m(t)` |
| `book_id` (optional) | Request parameter | Narrows Tier 2 to chapters from a specific book |

---

## 3. Two-tier priority overview

```
                get_next_slide(username, book_id?)
                        │
                        ▼
            lesson_count ← user_lesson_count
                        │
                        ▼
            due_rounds ← open rounds where due_at <= lesson_count
                        │
        ┌───────────────┴────────────────┐
        │                                │
        ▼                                ▼
   TIER 1: revisions             (iterate due_rounds, split
   (Group A and Group B)          each round's eligible quizzes
                                  into non-skipped / skipped via
                                  quiz_skip_log)
        │
        ▼
   Group A non-empty?  ─── yes ──► return weakest-m(t) quiz  ✱ TERMINAL ✱
        │
        no
        ▼
   Group B non-empty?  ─── yes ──► return oldest-skip quiz   ✱ TERMINAL ✱
        │
        no
        ▼
   TIER 2: new chapter
   (book_id filter optional)
        │
        ▼
   chapter available? ─── yes ──► return that chapter        ✱ TERMINAL ✱
        │
        no
        ▼
   SlideResult(slide_type="none")
```

Four things to note:

1. **Group A strictly blocks Tier 2.** If a single weakly-recalled quiz is due, the user will not see a new chapter until they have addressed it.
2. **Group B also blocks Tier 2.** Once Group A is empty, any previously-skipped revision quiz is served before any new chapter — this guarantees skipped quizzes resurface promptly rather than accumulating behind fresh material.
3. **Tier 2 only serves unlearnt chapters**, sourced via `get_next_chapter_in_book(book_id)` when filtered, otherwise `get_next_chapters_all_books(username)` with a random pick across books.
4. **The activation gate** skips an entire round's quizzes until every chapter of that lesson is learnt — an R0 with half-learnt chapters never surfaces; the user always sees chapters first for that lesson.

---

## 4. Tier 1 in detail — Group A (non-skipped revision quizzes)

### 4.1 Eligibility — who joins Group A?

For each `round_row` in `due_rounds`:

```
# activation gate
if not all_lesson_chapters_learnt(username, round_row.lesson_id):
    continue

# eligible quizzes for this round, split by skip state
non_skipped, skipped = get_eligible_quiz_ids_for_round(
    username, round_row.lesson_id, round_row.round_num
)
```

A quiz belongs to `non_skipped` iff:

1. It belongs to a chapter in `round_row.lesson_id`.
2. It has not already been answered in this round (`last_reviewed_lesson_count < round_row.due_at_lesson_count`, equivalently no "current-round answer" row yet).
3. It has no active row in `quiz_skip_log` for this user.

### 4.2 Scoring — how the weakest is chosen

For each eligible quiz `qid` the selector computes the **recall score** `m(t)`:

```
recall = get_quiz_recall(username, qid)
if recall is None:
    m_t = 1.0                                 # fresh quiz: neutral
else:
    last_reviewed = recall.last_reviewed_lesson_count or 0
    elapsed       = lesson_count - last_reviewed
    m_t           = exp(- forgetting_rate * max(elapsed, 0) / 10)
group_a.append((m_t, qid, round_num, lesson_id))
```

Properties of `m(t)` (`RevisionService.compute_recall`):

| Variable | Effect on `m(t)` | Effect on ordering |
|----------|-----------------|--------------------|
| `forgetting_rate` ↑ | `m(t)` ↓ | Quiz sorts **earlier** |
| `elapsed_lessons` ↑ | `m(t)` ↓ | Quiz sorts **earlier** |
| `forgetting_rate` = 0 | `m(t)` = 1.0 | Quiz never weakest |

`forgetting_rate` is updated by `RevisionService.record_quiz_response`:

- Correct answer: `rate = rate * 0.7` (recall strengthens, quiz drifts later)
- Wrong answer: `rate = min(rate * 1.2, 1.5)` (recall weakens, quiz drifts earlier)
- Skip: `rate` unchanged

### 4.3 The Like boost

When the user likes a quiz, the system does **not** tag the quiz as "liked" in the sort — it just **weakens the quiz's memory score on paper** so the existing weakest-recall-first ordering surfaces it sooner. Concretely, the like does three things:

1. **Insert a row** into `user_slide_like(username, quiz_id, liked_at)` — purely for the filled / outline UI state.
2. **Bump `forgetting_rate` to `max(current_rate, 1.0)`** in the `user_quiz_recall` row for that `(username, quiz_id)`. This is the only part that influences ordering.
3. **Preserve `last_reviewed_lesson_count`** when it already exists (so a like is not mistaken for a real review); initialise it to the current `lesson_count` only for never-answered quizzes.

Pseudocode (`RevisionService.apply_like_boost`):

```
existing  = get_quiz_recall(username, quiz_id)
new_rate  = max(existing.forgetting_rate if existing else 1.0, 1.0)
last_reviewed = existing.last_reviewed_lesson_count
                if existing and existing.last_reviewed_lesson_count is not None
                else current_lesson_count
upsert_quiz_recall(username, quiz_id, new_rate, last_reviewed)
```

#### How does this surface the quiz sooner?

Recall from §4.2 that every eligible quiz is scored:

```
m(t) = exp(- forgetting_rate * elapsed_lessons / 10)
```

and the quiz with the **lowest** `m(t)` wins. A well-recalled quiz typically has `forgetting_rate` in the 0.49…0.7 range (from two or three correct answers). Liking it resets the rate to 1.0 — higher rate → steeper decay curve → lower `m(t)` at the same `elapsed_lessons`. So on the next call, the liked quiz ranks earlier than an equally-due quiz that was not liked.

**Worked example.** Two quizzes `q1` and `q2` are both due; `elapsed_lessons = 4` for both:

| Quiz | `forgetting_rate` before | `m(t)` before | After liking `q2` | `m(t)` after |
|------|--------------------------|---------------|-------------------|--------------|
| `q1` | 0.7 | `exp(-0.7*4/10) = 0.76` | unchanged: 0.7 | 0.76 |
| `q2` | 0.7 | `exp(-0.7*4/10) = 0.76` | bumped to 1.0 | `exp(-1.0*4/10) = 0.67` |

Before the like, Python's stable sort kept `q1` first (insertion order with equal `m(t)`). After the like, `q2`'s `m(t)` drops to 0.67 < 0.76 and **`q2` is served next**.

#### What the like does *not* do

- It does **not** add an `is_liked` column to the sort key. The selector has no knowledge of likes at all.
- It does **not** apply a multiplier on top of `m(t)`. The effect is fully absorbed into the existing recall formula.
- It does **not** persist a "pre-like rate snapshot". Once raised, the rate can only come down through the natural correct-answer decay (`rate *= 0.7` per correct answer).
- It does **not** affect quizzes whose `forgetting_rate` is already ≥ 1.0 (e.g. after a wrong answer). The `max(current, 1.0)` floor is a no-op in that case.

#### Natural decay

Liking is a **one-shot boost**, not a permanent state. The next time the user answers the quiz correctly, the rate multiplies by 0.7 and `m(t)` recovers. After two or three correct answers the boost is effectively gone and the quiz returns to its usual slot. A user who wants the quiz to keep surfacing must re-like it (or keep getting it wrong, which naturally elevates the rate).

#### Unlike

Clicking an already-liked heart deletes the row from `user_slide_like` (so the icon returns to outline) but leaves `forgetting_rate` untouched. This is intentional: restoring the prior rate would require storing a pre-like snapshot and reconciling it with any reviews that happened in between. Instead, the boost is allowed to decay through natural answering.

### 4.4 Winner selection

```
group_a.sort(key=lambda x: x[0])      # ascending m(t)
_, best_quiz_id, best_round_num, best_lesson_id = group_a[0]
return SlideResult(slide_type="quiz", ...)
```

Ties (identical `m(t)`) are broken by Python's stable sort, i.e. the insertion order into `group_a`, which follows `due_rounds` order (arbitrary but deterministic given the DB state).

---

## 5. Tier 1 — Group B (skipped quizzes)

Group B is the **secondary revision queue**. A quiz enters Group B when the user clicks the down-arrow on a quiz slide without submitting an answer, inserting / refreshing a row in `quiz_skip_log`:

```
log_quiz_skip(username, quiz_id, lesson_id, round_num)
  # ON CONFLICT (username, quiz_id) DO UPDATE skipped_at = NOW()
```

Ordering within Group B is **oldest-skip-first** (`ORDER BY skipped_at ASC`), implemented inside `get_eligible_quiz_ids_for_round`. Re-skipping a quiz updates `skipped_at`, pushing it back to the back of the queue.

Group B is consulted **immediately after Group A is empty, before Tier 2**:

```
if group_a: ...return                  # weakest-m(t) revision
if group_b:
    best_quiz_id, best_round_num, best_lesson_id = group_b[0]
    return SlideResult(slide_type="quiz", ...)
# Tier 2 (new chapter) only runs if both Group A and Group B are empty
```

This ordering (revisions — skipped or not — always beat new chapters) ensures skipped quizzes resurface promptly rather than accumulating behind Tier 2 progression.

---

## 6. Tier 2 — new unlearnt chapters

Only reached when **both Group A and Group B are empty** (no due revisions of any kind).

```
if book_id:
    chapter = get_next_chapter_in_book(username, book_id)
else:
    chapters = get_next_chapters_all_books(username)
    chapter  = random.choice(chapters) if chapters else None
```

- `get_next_chapter_in_book(username, book_id)`: first chapter in that book (by `lesson.lesson_index`, then `chapter.chapter_index`) that has **no** `user_chapter_progress` row for the user.
- `get_next_chapters_all_books(username)`: one such "next unlearnt chapter" per book, from which `random.choice` picks one. This keeps progression interleaved across books rather than exhausting book 1 before starting book 2.

The randomness is per-call — repeated calls without state changes can return different chapters from different books.
