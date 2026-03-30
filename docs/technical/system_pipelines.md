# System Pipelines

[Parent](./index.md) | [Next: Authentication >](./authentication.md)

## Login Pipeline — [details](./authentication.md)

```
User submits login form
  │
  ▼
POST /api/login (username, password)
  │
  ▼
bcrypt.verify(password, hashed_password)
  │
  ▼
create_access_token(90d expiry, HS256 JWT)
  │
  ▼
Set-Cookie (HttpOnly, access_token)
  │
  ▼
Navigate to /
```

## Session Restore Pipeline — [details](./authentication.md)

```
Page load / refresh
  │
  ▼
AuthContext calls GET /api/me
  │
  ▼
Read access_token cookie → decode JWT
  │
  ▼
get_user(username) from DB
  │
  ▼
Return {authenticated, user} to frontend
  │
  ▼
authenticated? ──No──> Redirect to /login
      │
     Yes
      │
      ▼
Render protected page
```

## Slide Selection Pipeline — [details](./slide_stack.md)

```
User visits /slides
  │
  ▼
useSlide.fetchNextSlide(bookId)
  │
  ▼
GET /api/slides/next?book_id=optional
  │
  ▼
SlideSelector.get_next_slide(db, username, book_id)
  │
  ├── TIER 1: due revision rounds → QuizSlide
  ├── TIER 2: next unlearnt chapter → ChapterSlide
  └── TIER 3: skipped quizzes → QuizSlide (or AllCaughtUp)
  │
  ▼
Render ChapterSlide | QuizSlide | AllCaughtUp
```

## Chapter Learnt Pipeline — [details](./slide_stack.md)

```
User clicks [Mark as Learnt]
  │
  ▼
useSlide.markLearnt(chapterId)
  │
  ▼
POST /api/slides/chapters/{chapter_id}/learnt
  │
  ▼
LearningProgressService.mark_chapter_learnt → ChapterLearntResult
  │
  ▼
RevisionService.on_chapter_learnt → create/update revision round
  │
  ▼
useSlide.fetchNextSlide() → next slide
```

## Quiz Response Pipeline — [details](./slide_stack.md)

```
User submits answer (or skips)
  │
  ▼
useSlide.submitAnswer(quizId, body) | skipItem(quizId, body)
  │
  ▼
POST /api/slides/quizzes/{quiz_id}/respond
  │
  ├── is_skip=true → log_quiz_skip, record_quiz_response(is_correct=None)
  ├── multiple_choice → auto-grade (user_answer in correct_options)
  └── open-ended → QuizGrader.grade (Claude Haiku) → GradingResult
  │
  ▼
RevisionService.record_quiz_response → update recall, check round completion
  │
  ▼
Return { is_correct, feedback, round_done }
  │
  ▼
Show feedback panel → [Next Slide] → fetchNextSlide()
```

---

[Parent](./index.md) | [Next: Authentication >](./authentication.md)
