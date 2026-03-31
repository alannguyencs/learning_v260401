# Dashboard — Abstract

[Parent](./index.md)

## Problem

Users have no way to review their past interactions with the learning system. There is no visibility into which chapters were studied, which quizzes were answered or skipped, or whether the spaced-repetition system is behaving as expected.

Additionally, quiz answer events previously had no timestamp, making it impossible to reconstruct a chronological history of a learning session.

## Solution

A `/dashboard` page shows the user's full interaction history as a chronological table. Every event is captured — chapters marked learnt, quizzes answered (with correct/wrong result), quizzes skipped, and revision rounds created by the system.

## User Flow

1. User navigates to `/dashboard` (or clicks "Activity Log" from the Slides page).
2. The page loads a table of all past interactions, sorted oldest to newest.
3. Each row shows: when it happened, what type of event it was, which book/lesson/chapter it belongs to, and — for quiz answers — whether the answer was correct and the current recall rate.
4. If there is no activity yet, an empty state message is shown with a link to `/slides`.

## Scope

- Read-only view — the dashboard does not allow editing or deleting history.
- Scoped to the authenticated user — users only see their own activity.
- All four event types are covered: LEARNT CHAPTER, SKIP, ANSWER, ROUND CREATED.

## Acceptance Criteria

- [ ] `/dashboard` requires authentication; unauthenticated users are redirected to `/login`.
- [ ] All four event types appear with correct column values.
- [ ] Rows are ordered by event time ascending.
- [ ] ANSWER rows show `correct` or `wrong` and a `recall_rate` value.
- [ ] SKIP and non-quiz rows show `—` for `answer_result` and `recall_rate`.
- [ ] Empty state is shown when the user has no activity.
- [ ] "Activity Log" link is accessible from the Slides page.
