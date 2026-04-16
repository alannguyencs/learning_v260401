# Slide Stack

[Parent](./index.md)

**Status:** Plan

## Related Docs
- Technical: [technical/slide_stack.md](../technical/slide_stack.md)

## Problem

After authentication, users land on a blank page. There is no learning interface — users cannot consume lesson content, take quizzes, or track their revision progress. The backend slide API is fully implemented but has no frontend consumer.

## Solution

A continuous slide stream combining chapter study and spaced-repetition quizzes. The user sees one slide at a time: either a chapter to read or a quiz to answer. The system selects the next slide using a 2-tier priority algorithm (due revisions → new chapters). Within revision quizzes, unskipped quizzes are served first (weakest recall); skipped quizzes form a back-of-queue and resurface only after all unskipped quizzes are exhausted. Open-ended quiz answers are graded by AI. A floating chat icon on each slide lets the user ask contextual questions, answered by AI using the lesson source material, slide content, and conversation history.

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
  │     User answers MC or open-ended (textarea)
  │     Single-correct MC → radio buttons (pick one)
  │     Multi-correct MC  → checkboxes ("Select all that apply")
  │     [Submit Answer] → PASSED/FAILED badge + good/bad points shown
  │     MC feedback: all options shown (wrong pick red, correct green, others gray)
  │     [Next Slide]   → advances to next slide
  │     [Skip]         → quiz goes to back of queue, next unskipped quiz shown
  │
  ├── Chat (on any chapter or quiz slide):
  │     [Chat icon] → opens chat panel
  │     User types question → AI responds using slide + lesson context
  │     Conversation persists per slide across sessions
  │
  └── All caught up:
        Congratulations message shown when no slides remain
```

## Scope

**Included:**
- Chapter reading + mark-as-learnt interaction
- MC and open-ended quiz answering
- AI-graded PASSED/FAILED with itemized good/bad points for open-ended answers
- Book filtering via dropdown
- Spaced-repetition round display (Revision R0, R1, …)
- All-caught-up state
- Contextual AI Q&A chat on chapter and quiz slides

**Not included:**
- User progress dashboard (separate feature)
- Lesson structure browsing
- Manual content creation (agent upload only)

## Acceptance Criteria

- [ ] After login, user is redirected to `/slides`
- [ ] BookSelector dropdown shows all available books and allows filtering
- [ ] Chapter slides display markdown content with book/lesson breadcrumb
- [ ] Clicking "Mark as Learnt" advances to the next slide
- [ ] Single-correct MC quizzes show radio buttons; multi-correct MC quizzes show checkboxes with "Select all that apply" hint

- [ ] Submit button shows "Submitting..." and is disabled while waiting for the backend response
- [ ] Submitting an answer shows the correct/incorrect badge and AI feedback
- [ ] Clicking "Next Slide" after feedback advances to the next slide
- [ ] Skipping a quiz or chapter advances to the next slide
- [ ] When no slides remain, the "All caught up" message is shown
- [ ] Floating chat icon is visible on chapter and quiz slides
- [ ] Clicking chat icon opens a chat panel
- [ ] User can type a question and receive a contextual AI response
- [ ] Chat history persists per slide across page refreshes

---

[Parent](./index.md)
