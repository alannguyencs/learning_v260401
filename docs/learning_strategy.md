# Learning Strategy: Spaced Repetition with Time-Capped Daily Sessions

## Notation

- **Lk** — Learning lesson k (initial study, ~25 min)
- **Rk** — Review round k (scheduled review at increasing intervals)

## 1. Review Schedule

Each lesson follows a doubling-interval review schedule after initial learning:

| Review | Days after learning | Duration |
|--------|-------------------|----------|
| R1 | +1 | 5 min |
| R2 | +2 | 5 min |
| R3 | +4 | 10 min |
| R4 | +8 | 10 min |
| R5 | +16 | 10 min |
| R6 | +32 | 10 min |
| R7 | +64 | 10 min |
| ... | +2^k | 10 min |

Initial learning takes ~25 min per lesson. Reviews never end — intervals keep doubling indefinitely.

## 2. Daily Time Cap

All projections assume a **60 min/day** cap. On any given day:

- A new lesson is learned **only if** current review load + 25 min <= 60 min
- Reviews always take priority over new lessons

## 3. Sustainable Learning Rate

### Formula

On day D, the expected daily review load for a learner at rate r (lessons/day) is:

```
Daily time = 25r + 10r * log2(D)
```

Solving for the max sustainable rate:

```
r <= 60 / (25 + 10 * log2(D))
```

The rate decreases logarithmically over time because every lesson ever learned still demands occasional review.

### Projections

| Time elapsed | Max rate | Lessons/month | Cumulative lessons |
|-------------|----------|---------------|-------------------|
| 1 month | 0.81/day | ~24 | ~28 |
| 6 months | 0.60/day | ~18 | ~125 |
| 1 year | 0.55/day | ~16 | ~230 |
| 2 years | 0.50/day | ~15 | ~420 |
| 5 years | 0.45/day | ~14 | ~900 |
| 10 years | 0.42/day | ~13 | ~1,700 |
| 20 years | 0.39/day | ~12 | ~3,100 |
| 50 years | 0.36/day | ~11 | ~7,000 |

## 4. Two-Phase Learning Pattern

### Phase 1: Ramp-up (first ~2 weeks)

Reviews are light (only R1 and R2 active), so 1 new lesson/day is feasible:

| Day | Activity | Duration |
|-----|----------|----------|
| 0 | **L1** | 25 min |
| 1 | **L2**, R1(L1) | 30 min |
| 2 | **L3**, R1(L2) | 30 min |
| 3 | **L4**, R2(L1), R1(L3) | 35 min |
| 4 | **L5**, R2(L2), R1(L4) | 35 min |
| 5 | **L6**, R2(L3), R1(L5) | 35 min |
| 6 | **L7**, R2(L4), R1(L6) | 35 min |
| 7 | **L8**, R3(L1), R2(L5), R1(L7) | 45 min |
| 8 | **L9**, R3(L2), R2(L6), R1(L8) | 45 min |
| 9 | **L10**, R3(L3), R2(L7), R1(L9) | 45 min |
| 10 | **L11**, R3(L4), R2(L8), R1(L10) | 45 min |
| 11 | **L12**, R3(L5), R2(L9), R1(L11) | 45 min |
| 12 | **L13**, R3(L6), R2(L10), R1(L12) | 45 min |
| 13 | **L14**, R3(L7), R2(L11), R1(L13) | 45 min |

### Phase 2: Steady state (day 14+)

R3 and R4 reviews begin stacking. New lessons are learned only on days when review load allows it — roughly every other day:

| Day | Activity | Duration |
|-----|----------|----------|
| 14 | R4(L1), R3(L8), R2(L12), R1(L14) | 30 min |
| 15 | R4(L2), R3(L9), R2(L13) | 25 min |
| 16 | R4(L3), R3(L10), R2(L14) | 25 min |
| 17 | **L15**, R4(L4), R3(L11) | 45 min |
| 18 | R4(L5), R3(L12), R1(L15) | 25 min |
| 19 | **L16**, R4(L6), R3(L13) | 45 min |
| 20 | R4(L7), R3(L14), R2(L15), R1(L16) | 30 min |
| 21 | **L17**, R4(L8) | 35 min |
| 22 | **L18**, R4(L9), R2(L16), R1(L17) | 45 min |
| 23 | **L19**, R4(L10), R1(L18) | 40 min |
| 24 | R4(L11), R3(L15), R2(L17), R1(L19) | 30 min |
| 25 | **L20**, R4(L12), R2(L18) | 40 min |
| 26 | R4(L13), R3(L16), R2(L19), R1(L20) | 30 min |
| 27 | **L21**, R4(L14) | 35 min |
| 28 | R5(L1), R3(L17), R2(L20), R1(L21) | 30 min |
| 29 | **L22**, R5(L2), R3(L18) | 45 min |
| 30 | R5(L3), R3(L19), R2(L21), R1(L22) | 30 min |

## 5. Impact of Daily Time Cap

| Time | 45 min/day cumulative | 60 min/day cumulative | Gain |
|------|----------------------|----------------------|------|
| 1 year | ~160 | ~230 | +44% |
| 5 years | ~600 | ~900 | +50% |
| 10 years | ~1,100 | ~1,700 | +55% |
| 50 years | ~5,000 | ~7,000 | +40% |

Adding 15 min/day (~33% more time) yields roughly 40-55% more lessons — a better-than-linear return because the extra minutes absorb more review load, keeping the learning rate higher.

## 6. Key Takeaways

1. **No hard limit on total lessons.** Cumulative lessons grow as D/log(D), which goes to infinity. You can always learn more.
2. **The rate must gradually slow.** Because reviews never end (doubling intervals), every lesson ever learned still demands occasional review time. This creates a slowly growing review burden (~logarithmic).
3. **Reviews always come first.** Skipping reviews defeats the purpose of SRS. New lessons are only added when the daily cap allows it.
4. **Front-load aggressively.** The first 2 weeks support 1 lesson/day since long-interval reviews haven't kicked in yet. Use this window.
5. **Steady state is ~13 lessons/month** (at 60 min/day after 10 years). This is still substantial — one deeply retained lesson every 2-3 days, indefinitely.

## 7. Dynamic Lesson-Quiz Stacking Proposal

### 7.1 Definitions

| Concept | Description |
|---------|-------------|
| **Book** | A curated collection of lessons on a related topic |
| **Lesson** | A thematic unit within a book, composed of ordered chapters |
| **Chapter** | An atomic learning unit within a lesson; the smallest content block |
| **Quiz** | A retrieval exercise attached to a chapter |
| **Slide** | The frontend display unit — either a chapter view or a quiz |

**Quiz types** (see [§2.2 Retrieval Practice](data/lesson/coach/260324_time_framed_learning.md)):

| Type | Description |
|------|-------------|
| Free recall | User writes everything they remember, unprompted |
| Teach-back / Feynman | User explains the concept as if teaching someone else |
| Cloze deletion | Fill-in-the-blank with a key term removed |
| Multiple choice | Select the correct answer from options |

### 7.2 Constraints

**Learning order**
- A chapter must be fully learnt before any of its quizzes are presented.
- The order of chapters within a book is pre-defined; slides always follow that fixed order.
- All chapters of a lesson must be marked as learnt before the next lesson in the same book can begin — this applies both during initial learning and during revision sessions.

### 7.3 Revision Schedule

Following [§2.1 Spaced Repetition Systems](data/lesson/coach/260324_time_framed_learning.md), reviews use exponential decay measured in **number of lessons fully learnt** (not days).

**Definitions:**
- **Lesson fully learnt** — all chapters in the lesson have been marked as learnt.
- **Lesson fully revised** — the user has responded to (not skipped) more than 50% of the lesson's quizzes (scoped across all chapters in the lesson).

**All rounds are tracked at the lesson level.** As each chapter is marked as learnt, its quizzes become eligible for the lesson's current open round:
- If the lesson's R0 is not yet complete, the quizzes enter the **R0** pool — immediately eligible, no interval wait.
- If R0 is already complete, the quizzes are added to the **R1** pool instead, becoming due when R1 is triggered.

**Interval formula:** The interval between rounds is `2^n` lessons fully learnt since the previous round completed:

| Round | Trigger | Interval |
|-------|---------|----------|
| R0 | First chapter of the lesson marked as learnt | Immediate — no wait |
| R1 | R0 completed | 2^1 = 2 lessons fully learnt |
| R2 | R1 completed | 2^2 = 4 lessons fully learnt |
| R3 | R2 completed | 2^3 = 8 lessons fully learnt |
| Rn | R(n-1) completed | 2^n lessons fully learnt |

**Completion threshold:** A round is marked done when the user has responded to (not skipped) more than 50% of the lesson's quizzes. This applies to all rounds including R0.

### 7.4 Stacking Algorithm

The system always shows one slide at a time. **Due revisions take priority over new lesson chapters.** When all due revisions are cleared, the next new chapter is presented.

**Slide selection rules:**

| Context | Selection rule |
|---------|---------------|
| Due revision slides | Randomly selected from all due revision quizzes across all books (interleaved — see [§2.3 Interleaved Practice](data/lesson/coach/260324_time_framed_learning.md)); within a lesson's round, quizzes are ordered by ascending recall rate — weakest first (see MEMORIZE algorithm in [docs/technical/quiz.md](docs/technical/quiz.md)) |
| New chapter — specific book selected | Next chapter in the book's pre-defined order |
| New chapter — all books selected | Randomly selected from all available next chapters across books |

Interleaving revisions across books (rather than completing one book's revisions before another's) exploits *discriminative contrast* — the brain is forced to distinguish between concepts from different topics, building more flexible, transfer-ready knowledge.

**Priority order:**

```
┌──────────────────────────────────────────┐
│  1. Due revision quizzes (all books)     │  ← highest priority
│     selected randomly (interleaved)      │
├──────────────────────────────────────────┤
│  2. New chapter slide                    │  ← only after all revisions done
│     next in order (specific book)        │
│     or random (all books)                │
├──────────────────────────────────────────┤
│  3. Skipped items                        │  ← lowest priority
│     resurface after new chapters         │
└──────────────────────────────────────────┘
```

### 7.5 User Interactions

1. **Book selection** — The user may choose to learn all books or a single specific book.
2. **Slide interaction** — For each slide, the user has two options:

| Slide type | Skip | Activate |
|------------|------|----------|
| Chapter | Chapter deferred. The lesson cannot advance — the system picks a chapter from another book instead. The skipped chapter resurfaces as the next slide once no other books have available chapters. | **Mark as Learnt** button |
| Quiz | Quiz deferred; does not count toward the 50% completion threshold. Resurfaces after all due revisions and new chapters (tier 3). | Submit an answer |

### 7.6 Example: Slide Stack Walkthrough

**Setup:**
- Book A: Lesson 1 → Ch1-Le1-A (Q1, Q2), Ch2-Le1-A (Q3) — 3 quizzes total for Le1-A
- Book B: Lesson 1 → Ch1-Le1-B (Q1, Q2) — 2 quizzes total for Le1-B
- User selects: **All books** | Lesson count: **0**

Naming: `ChN-LeM-X` = Chapter N of Lesson M in Book X. R0 threshold: >50% of lesson quizzes answered.

```
Slide 1:  [ Chapter: Ch1-Le1-A · Book A ]         ← fresh start; no revisions due
          → Mark as Learnt
            Q1, Q2 enter R0 pool for Le1-A (2 eligible; threshold: 2+ of 3)

Slide 2:  [ Quiz R0 · Le1-A · Q1 ]                ← due revision; takes priority over next chapter
          → Submit answer  (1/3 = 33%, R0 not done)

Slide 3:  [ Quiz R0 · Le1-A · Q2 ]
          → Submit answer  (2/3 = 67% > 50%) → R0 for Le1-A DONE
            R1 for Le1-A scheduled: due at lesson count 2

Slide 4:  [ Chapter: Ch2-Le1-A · Book A ]         ← no more eligible R0 quizzes; next chapter
          → Mark as Learnt
            Le1-A fully learnt → lesson count = 1
            Q3 eligible; R0 already done → Q3 added to R1 pool for Le1-A

Slide 5:  [ Chapter: Ch1-Le1-B · Book B ]         ← no revisions due; random next chapter
          → Mark as Learnt
            Le1-B fully learnt → lesson count = 2
            Q1, Q2 enter R0 pool for Le1-B
            R1 for Le1-A now due (lesson count reached 2)

Slide 6:  [ Quiz R0 · Le1-B · Q1 ]                ← R0 Le1-B and R1 Le1-A both due; random interleave
          → Submit answer  (1/2 = 50%, R0 for Le1-B not done)

Slide 7:  [ Quiz R1 · Le1-A · Q1 ]                ← shown first: lowest recall rate among R1 pool
          → Submit answer

Slide 8:  [ Quiz R1 · Le1-A · Q2 ]                ← shown second: higher recall rate than Q1
          → Submit answer  (2/3 = 67% > 50%) → R1 for Le1-A DONE
            R2 for Le1-A scheduled: due at lesson count 6

Slide 9:  [ Quiz R0 · Le1-B · Q2 ]
          → Skip  (1/2 = 50%, R0 not done; skipped, goes to bottom)

No more due revisions. No unlearnt chapters.

Slide 10: [ Quiz R0 · Le1-B · Q2 ]                ← skipped item resurfaces
          → Submit answer  (2/2 = 100% > 50%) → R0 for Le1-B DONE
            R1 for Le1-B scheduled: due at lesson count 4
```

**Key behaviours illustrated:**
- Stack always starts with a chapter slide when no revisions are due
- Rounds are per lesson — R0 for Le1-A tracks quizzes across all its chapters
- Quizzes become eligible for R0 as each chapter is learnt; Q3 enters R1 because R0 was already done when Ch2-Le1-A was marked as learnt (Slide 4)
- R0 completion is lesson-scoped: 2/3 > 50% marks R0 done, even before all chapters are learnt
- Revisions from Book A and Book B interleave randomly (Slides 6–9)
- Skipped quizzes sink to the bottom — below new chapters (Slide 9 → resurfaces at Slide 10)
- R1/R2 intervals are measured from lesson count at time of previous round completion
