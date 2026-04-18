# Discussion: Liked Slide Frequency Boost

## Context

The user wants to add a **like button** above the chat icon on each slide. Liked slides should appear **more frequently** than others in the stacking algorithm.

---

## What Exists Today

The slide stacking algorithm (`backend/src/service/slide_selector.py`) decides slide order using:

1. **Tier 1 — Revision quizzes** (due rounds, weakest-recall-first via forgetting curve `m(t)`)
2. **Tier 2 — New chapters** (next unlearnt, optionally book-filtered)

The recall score that orders quizzes is:

```
m(t) = exp(-forgetting_rate * elapsed_lessons / 10)
```

- `forgetting_rate` starts at 1.0, decays to 0.7 on correct, grows to 1.2 on wrong (capped at 1.5)
- Lower m(t) = weaker recall = served first
- Stored per (user, quiz) in `user_quiz_recall` table

Revision rounds are scheduled at exponentially increasing intervals: R0 complete -> R1 in +2, R1 -> R2 in +4, etc. (`due_at = completed_at + 2^(round+1)`)

---

## Design Options

### Option A: Like as a Forgetting-Rate Boost (Recommended)

**Idea:** Liking a quiz artificially inflates its `forgetting_rate`, making `m(t)` decay faster and the quiz surface sooner in the weakest-recall-first ordering.

**How it works:**
- User likes quiz 42 -> set `forgetting_rate = max(current_rate, 1.0)` (reset to "never reviewed" level)
- The next time the algorithm sorts Group A, quiz 42's m(t) will be lower (weaker recall), so it surfaces earlier
- Natural review cycles still apply — once the user answers it correctly again, the rate decays back down
- Liking repeatedly keeps the rate elevated

**Pros:**
- No new tier or algorithm branch — works within existing m(t) sorting
- Self-correcting: correct answers naturally reduce the boost over time
- Minimal code change: one CRUD operation + one API endpoint

**Cons:**
- Only affects quizzes, not chapters (chapters have no recall score)
- The boost is indirect — the user might not perceive "more frequent" if many other quizzes also have high rates

### Option B: Like as a Separate Priority Multiplier

**Idea:** Add a `like_weight` multiplier to the m(t) formula: `effective_m(t) = m(t) * like_multiplier` where liked quizzes get `like_multiplier = 0.5` (halves the score, making them appear weaker/sooner).

```
effective_m(t) = m(t) * (0.5 if liked else 1.0)
```

**How it works:**
- New table `user_slide_like` with (username, quiz_id, liked_at)
- In `SlideSelector.get_next_slide()`, after computing m(t) for each quiz, multiply by 0.5 if the quiz is liked
- Liked quizzes consistently rank higher in the priority queue

**Pros:**
- Predictable and permanent boost until unliked
- Clean separation between recall state and user preference
- Can extend to chapters later (e.g., re-surface liked chapters as review material)

**Cons:**
- Requires a new table and join in the hot path
- Liked quizzes could dominate the queue if the user likes many

### Option C: Liked Slides Get Extra Revision Rounds

**Idea:** When a quiz is liked, the system schedules an additional "bonus" revision round with a shorter interval.

**How it works:**
- Liking a quiz in lesson X creates a bonus `LessonRevisionRound` with `due_at = current_lesson_count + 1` (surfaces next lesson)
- Uses existing round infrastructure — no algorithm changes needed

**Pros:**
- Uses existing scheduling infrastructure entirely
- Works at the lesson level (all quizzes in the liked lesson get reviewed)

**Cons:**
- Coarse granularity: affects all quizzes in the lesson, not just the liked one
- Complexity in managing "bonus" vs "natural" rounds

---

## Recommendation: Option B (Priority Multiplier)

Option B is the best balance of simplicity, predictability, and clean architecture:

### Data Model

```sql
CREATE TABLE user_slide_like (
    id SERIAL PRIMARY KEY,
    username VARCHAR NOT NULL REFERENCES users(username),
    quiz_id INTEGER NOT NULL REFERENCES chapter_quizzes(id),
    liked_at TIMESTAMP NOT NULL DEFAULT now(),
    UNIQUE(username, quiz_id)
);
CREATE INDEX idx_usl_user ON user_slide_like(username);
```

### Algorithm Change (slide_selector.py)

```python
# In the Group A loop, after computing m_t:
liked_quiz_ids = get_liked_quiz_ids(db, username)  # Set[int]
like_multiplier = 0.5 if qid in liked_quiz_ids else 1.0
effective_m_t = m_t * like_multiplier
group_a.append((effective_m_t, qid, round_row.round_num, round_row.lesson_id))
```

### API

```
POST /api/slides/quizzes/{quiz_id}/like     -> toggle like on
DELETE /api/slides/quizzes/{quiz_id}/like    -> toggle like off
GET /api/slides/likes                        -> list liked quiz IDs for user
```

### Frontend

- Heart icon above the chat icon, same positioning pattern
- Filled when liked, outline when not
- Toggle on click with optimistic UI update

### Flow

```
[User] Sees quiz slide
  |
  v
[User] Clicks heart icon (like)
  |
  |   POST /api/slides/quizzes/{id}/like
  |   -> INSERT INTO user_slide_like
  |
  v
[Algorithm] Next time quiz is eligible:
  |   m(t) = exp(-rate * elapsed / 10)
  |   effective_m(t) = m(t) * 0.5  <-- liked boost
  |   -> quiz ranks higher in Group A
  |
  v
[User] Sees liked quiz sooner than unlocked ones
```

---

## Scope Decisions

| Question | Suggested Answer |
|----------|-----------------|
| Like chapters too? | Start with quizzes only — chapters are one-time reads, liking them to "review" is a different feature (bookmarks) |
| Like multiplier value? | 0.5 (halves m(t), effectively doubling priority). Configurable later |
| Unlike? | Yes — DELETE endpoint removes the row, multiplier goes back to 1.0 |
| Persist across rounds? | Yes — like is independent of revision rounds. Stays until user unlikes |
| Show like count? | No — this is personal preference, not social. Just a filled/unfilled heart |

---

## Next Steps

- `/webapp-dev:feature-plan` — to generate the full implementation plan with migration SQL, backend endpoints, frontend components, and test spec
- The implementation is small (~4 files changed, 1 new table, 1 new CRUD file) and can be done in a single session
