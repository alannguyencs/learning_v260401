# Dashboard — Abstract

[Parent](./index.md)

## Problem

Users have no way to review their past interactions with the learning system. There is no visibility into which chapters were studied, which quizzes were answered or skipped, or whether the spaced-repetition system is behaving as expected.

Additionally, quiz answer events previously had no timestamp, making it impossible to reconstruct a chronological history of a learning session.

Users also lack a high-level summary of their learning progress — there is no view showing which revision round each lesson is on, their quiz accuracy, or whether their accuracy is improving over time.

## Solution

A `/dashboard` page with two tabs:

1. **Activity Log** — the user's full interaction history as a chronological table. Every event is captured: chapters marked learnt, quizzes answered (with correct/wrong result), quizzes skipped, and revision rounds created by the system.

2. **Learning Progress** — one card per book. Each card contains:
   - A **lesson table** with columns: Lesson title, Current Revision round, and Accuracy (correct answers / total answers across all rounds, shown as a percentage).
   - An **accuracy trendline** below the table, showing how the user's accuracy for that book has changed over their most recent answers. The trendline uses a sliding window to smooth out noise and reveal the overall direction.

## User Flow

1. User navigates to `/dashboard` (or clicks "Dashboard" from the Slides page).
2. The page loads with the "Activity Log" tab active by default.
3. The Activity Log tab shows a table of all past interactions, sorted oldest to newest.
4. Each row shows: when it happened, what type of event it was, which book/lesson/chapter it belongs to, and — for quiz answers — whether the answer was correct and the current recall rate.
5. User clicks the "Learning Progress" tab.
6. The page shows one card per book.
7. Each book card displays a table of lessons with their revision round and accuracy.
8. Below each table, a trendline chart shows accuracy direction over the most recent 119 answers for that book.
9. If there is no activity yet, an empty state message is shown with a link to `/slides`.

## Scope

- Read-only view — the dashboard does not allow editing or deleting history.
- Scoped to the authenticated user — users only see their own activity.
- Activity Log: all four event types are covered: LEARNT CHAPTER, SKIP, ANSWER, ROUND CREATED.
- Learning Progress: per-book cards with lesson table and accuracy trendline.

## Acceptance Criteria

- [ ] `/dashboard` requires authentication; unauthenticated users are redirected to `/login`.
- [ ] Tab switcher shows "Activity Log" and "Learning Progress" tabs.
- [ ] Activity Log tab is active by default.
- [ ] All four event types appear with correct column values in Activity Log.
- [ ] Rows are ordered by event time ascending in Activity Log.
- [ ] Learning Progress tab shows one card per book.
- [ ] Each book card has a lesson table with Lesson, Revision, and Accuracy columns.
- [ ] Each book card has a trendline chart below the table.
- [ ] Trendline shows 20 data points when the book has 20+ answers; hidden when fewer than 20.
- [ ] Empty state is shown when the user has no activity.
- [ ] "Dashboard" link is accessible from the Slides page.
