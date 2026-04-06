# Learning Progress Tab — Discussion

## Context

The `/dashboard` page currently has one view: **Activity Log** — a raw chronological table of every interaction (LEARNT CHAPTER, SKIP, ANSWER, ROUND CREATED). It's useful for debugging and replay, but it doesn't answer the natural question: "How am I doing?"

The user wants a second tab — **Learning Progress** — alongside Activity Log. This document proposes what that tab could look like, grounded in the data already available.

## What Data Exists Today

All of this is already in the database and requires **no new tables**:

| Data Point | Source Table | What It Tells Us |
|---|---|---|
| Chapters learnt per lesson | `user_chapter_progress` JOIN `chapters` | How far through each lesson |
| Total chapters per lesson | `chapters` | Denominator for completion % |
| Lessons fully completed | `user_lesson_count` | Global counter |
| Revision rounds per lesson | `lesson_revision_rounds` | Which round (R0, R1, ...) and status (open/done) |
| Quiz accuracy | `quiz_answer_log` | correct vs wrong counts |
| Recall strength per quiz | `user_quiz_recall` | `forgetting_rate` (lower = stronger memory) |
| Total quizzes per lesson | `chapter_quizzes` JOIN `chapters` | How many quizzes exist |
| Books/lessons metadata | `books`, `lessons` | Names, titles, ordering |

## Suggested Design: Per-Lesson Progress Cards

Instead of another data table (Activity Log already covers that), the Learning Progress tab should be a **card-based view grouped by book**, showing at-a-glance progress for each lesson.

### Layout

```
/dashboard
  [Activity Log]   [Learning Progress]    ← tab switcher
                        ^active

  ┌─────────────────────────────────────────────────────┐
  │  BOOK: theMITmonk                                   │
  ├─────────────────────────────────────────────────────┤
  │                                                     │
  │  ┌───────────────────────────────────────────────┐  │
  │  │ Lesson 1: 20 Quantum Cheat Codes...           │  │
  │  │                                               │  │
  │  │ Chapters:  ████████░░  1/5  (20%)             │  │
  │  │ Revision:  R0 open · 8/9 answered             │  │
  │  │ Accuracy:  ●●●●○○○○  4/8 correct (50%)       │  │
  │  │ Recall:    ▓▓▓▒▒░░  avg 0.87                  │  │
  │  └───────────────────────────────────────────────┘  │
  │                                                     │
  │  ┌───────────────────────────────────────────────┐  │
  │  │ Lesson 2: ...                                 │  │
  │  │  (Not started)                                │  │
  │  └───────────────────────────────────────────────┘  │
  │                                                     │
  └─────────────────────────────────────────────────────┘
```

### Card Metrics (per lesson)

Each lesson card shows 4 metrics:

1. **Chapters progress bar** — `learnt_chapters / total_chapters`
   - Green fill proportional to completion
   - Source: `user_chapter_progress` COUNT vs `chapters` COUNT for this lesson

2. **Revision round status** — current round label + how many quizzes answered in it
   - e.g. "R0 open · 8/9 answered" or "R1 due in 2 lessons" or "R2 done"
   - Source: `lesson_revision_rounds` (latest round for this user+lesson)

3. **Quiz accuracy** — correct answers / total answers attempted
   - e.g. "4/8 correct (50%)"
   - Source: `quiz_answer_log` aggregated per lesson

4. **Average recall strength** — mean of all `forgetting_rate` values for quizzes in this lesson
   - Lower forgetting_rate = stronger recall
   - Display as a colour-coded bar or number (green < 0.5, yellow 0.5-1.0, red > 1.0)
   - Source: `user_quiz_recall` JOIN `chapter_quizzes` JOIN `chapters`

### States

- **Not started** — no `user_chapter_progress` rows for any chapter in this lesson → grey card, "Not started"
- **In progress** — some chapters learnt, revision rounds may exist → active card with metrics
- **Fully completed** — all chapters learnt + latest revision round done → green border/badge

### Book-Level Summary (optional header)

At the top of each book section, a one-line summary:

```
theMITmonk — 1 lesson · 1/5 chapters · R0 in progress
```

## Alternative Ideas Considered

### Option B: Heatmap Calendar
Like GitHub's contribution graph — each day is a cell colored by how many slides were completed. Good for streaks/motivation but requires date-based aggregation and doesn't show per-lesson detail.

**Verdict:** Could be a nice addition later but not the primary view. The card view is more actionable.

### Option C: Leaderboard / Streaks
Show consecutive days of activity, total quizzes this week, etc. Gamification layer.

**Verdict:** Fun but secondary. The per-lesson progress view answers the core question first.

### Option D: Recall Decay Chart
A line chart per lesson showing how recall scores decay over time and get refreshed by revision rounds.

**Verdict:** Very cool for advanced users but complex to implement (needs charting library + time-series data). Better as a drill-down from a lesson card later.

## Implementation Notes

- **No new tables needed.** All data is already captured.
- **One new API endpoint:** `GET /api/dashboard/learning-progress` returning a structured response grouped by book → lessons → metrics.
- **Frontend:** A tab switcher component on `DashboardPage.jsx`, with the existing table under "Activity Log" and a new card grid under "Learning Progress".
- **The query** joins `lessons`, `chapters`, `user_chapter_progress`, `lesson_revision_rounds`, `quiz_answer_log`, and `user_quiz_recall` — aggregated per lesson.

## Next Steps

- `/feature-plan` — to create a detailed implementation plan for the Learning Progress tab
- `/feature-update` — if you want to tweak the existing Activity Log tab at the same time (e.g. add the tab switcher)
