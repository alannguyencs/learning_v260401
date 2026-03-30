# Slide Stack

[Parent](./index.md)

**Status:** Plan

## Related Docs
- Technical: [technical/slide_stack.md](../technical/slide_stack.md)

## Problem

After authentication, users land on a blank page. There is no learning interface — users cannot consume lesson content, take quizzes, or track their revision progress. The backend slide API is fully implemented but has no frontend consumer.

## Solution

A continuous slide stream combining chapter study and spaced-repetition quizzes. The user sees one slide at a time: either a chapter to read or a quiz to answer. The system selects the next slide using a 3-tier priority algorithm (due revisions → new chapters → skipped items). Open-ended quiz answers are graded by AI.

## User Flow

```
User logs in → redirected to /slides
  │
  ▼
BookSelector: All Books | select a specific book
  │
  ▼
SlidePage fetches GET /api/slides/next
  │
  ├── Chapter slide:
  │     User reads markdown content
  │     [Mark as Learnt] → records progress, triggers revision round setup
  │     [Skip Chapter]   → moves to next slide
  │
  ├── Quiz slide (revision round):
  │     User answers MC (radio buttons) or open-ended (textarea)
  │     [Submit Answer] → is_correct badge + AI feedback shown
  │     [Next Slide]   → advances to next slide
  │     [Skip]         → logs skip, advances to next slide
  │
  └── All caught up:
        Congratulations message shown when no slides remain
```

## Scope

**Included:**
- Chapter reading + mark-as-learnt interaction
- MC and open-ended quiz answering
- AI feedback display for open-ended answers
- Book filtering via dropdown
- Spaced-repetition round display (Revision R0, R1, …)
- All-caught-up state

**Not included:**
- User progress dashboard (separate feature)
- Lesson structure browsing
- Manual content creation (agent upload only)

## Acceptance Criteria

- [ ] After login, user is redirected to `/slides`
- [ ] BookSelector dropdown shows all available books and allows filtering
- [ ] Chapter slides display markdown content with book/lesson breadcrumb
- [ ] Clicking "Mark as Learnt" advances to the next slide
- [ ] Quiz slides show MC options as radio buttons or a textarea for open-ended types
- [ ] Submitting an answer shows the correct/incorrect badge and AI feedback
- [ ] Clicking "Next Slide" after feedback advances to the next slide
- [ ] Skipping a quiz or chapter advances to the next slide
- [ ] When no slides remain, the "All caught up" message is shown

---

[Parent](./index.md)
