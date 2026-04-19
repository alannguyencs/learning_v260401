# Slide Stack

[Parent](./index.md)

**Status:** Implemented

## Related Docs
- Technical: [technical/slide_stack.md](../technical/slide_stack.md)

## Problem

After authentication, users land on a blank page. There is no learning interface — users cannot consume lesson content, take quizzes, or track their revision progress. The backend slide API is fully implemented but has no frontend consumer.

## Solution

A continuous slide stream combining chapter study and spaced-repetition quizzes. The user sees one slide at a time: either a chapter to read or a quiz to answer. The system selects the next slide using a 2-tier priority algorithm (due revisions → new chapters). Within revision quizzes, unskipped quizzes are served first (weakest recall); skipped quizzes form a back-of-queue and resurface only after all unskipped quizzes are exhausted. Open-ended quiz answers are graded by AI. A floating chat icon on each slide lets the user ask contextual questions, answered by AI using the lesson source material, slide content, and conversation history.

Users can mark quizzes they want to see more often by tapping a thumbs-up Like button on the quiz slide; liked quizzes have their recall weakened so they resurface sooner in the revision queue. Chapters can also be liked from their slide; liked chapters appear in the Favorite tab alongside liked quizzes in a single newest-first list. Chapter likes are bookmarks only and do not affect the slide selection algorithm.

On any quiz slide, a "View chapter" link lets the user jump to the quiz's parent chapter. The chapter is inserted as the current slide and the quiz (with its feedback) is pushed onto the back-history stack, so the up arrow returns to the quiz in its original state. "Mark as Learnt" is hidden on any chapter slide that has already been learnt.

Navigation arrows allow the user to move backward through their slide history (up arrow) or forward again (down arrow). Each user's current position and full history are stored server-side so the state survives page refreshes. Quiz answers viewed while replaying history show the original feedback.

## User Flow

```
User logs in → redirected to /slides
  │
  ▼
BookSelector: All Books | select a specific book
  │
  ▼
SlidePage loads GET /api/slides/current (saved position or fresh pick)
  │
  ├── Navigation arrows (shown on all slides except "none"):
  │     [↑] ArrowUp — full-width row above BookSelector, only shown when has_previous=true
  │                 → POST /api/slides/back
  │     [↓] ArrowDown — fixed at viewport bottom, always shown on active slides
  │                   → chapter: marks learnt + advances
  │                   → quiz (no feedback): skips quiz to back of queue
  │                   → quiz (with feedback): advances to next slide
  │
  ├── Chapter slide:
  │     User reads markdown content
  │     [Mark as Learnt] → POST /api/slides/forward with mark_chapter_id
  │                      → records progress, triggers revision round setup, advances
  │
  ├── Quiz slide (revision round):
  │     User answers MC or open-ended (textarea)
  │     Single-correct MC → radio buttons (pick one)
  │     Multi-correct MC  → checkboxes ("Select all that apply")
  │     [Submit Answer] → PASSED/FAILED badge + good/bad points shown
  │     MC feedback: all options shown (wrong pick red, correct green, others gray)
  │
  ├── View chapter link (on every quiz slide, pre-answer and feedback states):
  │     [View chapter: {chapter_title}] → POST /api/slides/jump-to-chapter
  │         → parent chapter becomes current slide
  │         → quiz + feedback pushed to back-history
  │     Up arrow from inserted chapter → restores quiz with feedback
  │     Down arrow from inserted chapter → fresh next slide (forward stack cleared)
  │     "Mark as Learnt" is hidden on chapters whose is_learnt is true
  │
  ├── Like (on quiz slides):
  │     [Like button (thumbs-up) above chat icon] → toggles like/unlike
  │     Liked quizzes have their recall weakened so they appear
  │     more frequently in the spaced-repetition ordering
  │
  ├── Like (on chapter slides):
  │     [Like button (thumbs-up) above chat icon] → toggles like/unlike
  │     Liked chapters are bookmarked and visible in the Favorite tab;
  │     they do NOT resurface on the slide stream
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
- Back/forward navigation through slide history (up/down arrows)
- Per-quiz like/unlike via a thumbs-up Like button; liked quizzes resurface sooner in the revision queue
- Per-chapter like/unlike via the same thumbs-up Like button; liked chapters appear in the Favorite tab
- Favorite tab showing liked quizzes and liked chapters interleaved, newest-liked first, filterable by book
- Jump-to-chapter link on every quiz slide; back arrow restores the quiz with its feedback; Mark-as-Learnt is hidden on already-learnt chapters

**Not included:**
- User progress dashboard (separate feature)
- Lesson structure browsing
- Manual content creation (agent upload only)
- Showing social like counts

## Acceptance Criteria

- [ ] After login, user is redirected to `/slides`
- [ ] BookSelector dropdown shows all available books and allows filtering
- [ ] Chapter slides display markdown content with book/lesson breadcrumb
- [ ] Clicking "Mark as Learnt" advances to the next slide
- [ ] Single-correct MC quizzes show radio buttons; multi-correct MC quizzes show checkboxes with "Select all that apply" hint

- [ ] Submit button shows "Submitting..." and is disabled while waiting for the backend response
- [ ] Submitting an answer shows the correct/incorrect badge and AI feedback
- [ ] When no slides remain, the "All caught up" message is shown
- [ ] Down arrow on a chapter slide marks the chapter as learnt and advances
- [ ] Down arrow on a quiz slide (before submitting) skips the quiz to the back of the queue
- [ ] Down arrow on a quiz slide (after feedback) advances to the next slide
- [ ] Skipping a quiz via the down arrow puts it at the back of the queue
- [ ] Up arrow is visible only when there is previous history; clicking it returns to the previous slide
- [ ] Navigating back to a quiz that was answered shows the original feedback
- [ ] Floating chat icon is visible on chapter and quiz slides
- [ ] Clicking chat icon opens a chat panel
- [ ] User can type a question and receive a contextual AI response
- [ ] Chat history persists per slide across page refreshes
- [ ] Like button (thumbs-up) is visible on every quiz slide and chapter slide and hidden on the All-Caught-Up state
- [ ] Clicking the Like button toggles filled/outline and persists across page refresh
- [ ] Liking a quiz causes it to appear sooner in subsequent Tier-1 ordering
- [ ] Liking a chapter does NOT resurface it on the slide stream (bookmark only)
- [ ] The Favorite tab shows liked quizzes and liked chapters interleaved, newest-liked first
- [ ] A liked chapter renders as a chapter card (breadcrumb + title + markdown body) distinct from the quiz card layout
- [ ] BookSelector on the Favorite tab filters both quiz and chapter items by book
- [ ] Quiz slides render a "View chapter: {chapter_title}" link immediately under the breadcrumb, visible in both pre-answer and feedback states
- [ ] Clicking the link inserts the parent chapter as the current slide; quiz position + feedback are pushed to back-history
- [ ] From the inserted chapter, clicking the up arrow restores the original quiz with its feedback panel
- [ ] From the inserted chapter, clicking the down arrow advances to a fresh next slide (not the original quiz)
- [ ] "Mark as Learnt" is hidden on any chapter slide where `chapter.is_learnt` is true

---

[Parent](./index.md)
