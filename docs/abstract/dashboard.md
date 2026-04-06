# Dashboard — Abstract

[Parent](./index.md)

## Problem

Users have no way to review their past interactions with the learning system. There is no visibility into which chapters were studied, which quizzes were answered or skipped, or whether the spaced-repetition system is behaving as expected.

Additionally, quiz answer events previously had no timestamp, making it impossible to reconstruct a chronological history of a learning session.

Users also lack a high-level summary of their learning progress — there is no view showing how far they are through each lesson, which revision round they are on, their quiz accuracy, or how well they are retaining material.

## Solution

A `/dashboard` page with two tabs:

1. **Activity Log** — the user's full interaction history as a chronological table. Every event is captured: chapters marked learnt, quizzes answered (with correct/wrong result), quizzes skipped, and revision rounds created by the system.

2. **Learning Progress** — per-lesson progress cards grouped by book. Each lesson card shows four metrics: chapter completion (progress bar), current revision round status, quiz accuracy (correct/total), and average recall strength.

## User Flow

1. User navigates to `/dashboard` (or clicks "Dashboard" from the Slides page).
2. The page loads with the "Activity Log" tab active by default.
3. The Activity Log tab shows a table of all past interactions, sorted oldest to newest.
4. Each row shows: when it happened, what type of event it was, which book/lesson/chapter it belongs to, and — for quiz answers — whether the answer was correct and the current recall rate.
5. User clicks the "Learning Progress" tab.
6. The page shows lesson cards grouped by book, each with chapter progress, revision status, accuracy, and recall metrics.
7. Lessons with no activity show a muted "Not started" state.
8. If there is no activity yet, an empty state message is shown with a link to `/slides`.

## Scope

- Read-only view — the dashboard does not allow editing or deleting history.
- Scoped to the authenticated user — users only see their own activity.
- Activity Log: all four event types are covered: LEARNT CHAPTER, SKIP, ANSWER, ROUND CREATED.
- Learning Progress: per-lesson metrics (chapters, revision, accuracy, recall) grouped by book.

## Acceptance Criteria

- [ ] `/dashboard` requires authentication; unauthenticated users are redirected to `/login`.
- [ ] Tab switcher shows "Activity Log" and "Learning Progress" tabs.
- [ ] Activity Log tab is active by default.
- [ ] All four event types appear with correct column values in Activity Log.
- [ ] Rows are ordered by event time ascending in Activity Log.
- [ ] ANSWER rows show `correct` or `wrong` and a `forgetting_rate` value.
- [ ] SKIP and non-quiz rows show `—` for `answer_result` and `forgetting_rate`.
- [ ] Learning Progress tab shows lesson cards grouped by book.
- [ ] Each lesson card shows chapters progress bar, revision status, accuracy, and recall.
- [ ] Lessons with no progress show "Not started".
- [ ] Empty state is shown when the user has no activity.
- [ ] "Dashboard" link is accessible from the Slides page.
